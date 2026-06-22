"""관심종목(워치리스트) API 테스트 — SCRUM-26.

현재가(KIS)는 fetch_price를 patch하여 고정값으로 대체한다.
"""
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import InvestmentProfile, UserPreferredSector
from recommend.models import RecommendationCache, StockDna, UserLikedStock
from stocks.models import Stock, StockPrice

User = get_user_model()
PRICE = {"current": Decimal("80000"), "change_rate": 1.5}


def _make_user(username="watcher"):
    return User.objects.create(username=username, nickname=username, birth_year=1995)


def _make_stock(code="A0001"):
    return Stock.objects.create(code=code, name="테스트", market="KOSPI", currency="KRW")


class WatchlistTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.stock = _make_stock("A0001")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("recommend.services.fetch_price", return_value=PRICE)
    def test_add(self, _):
        resp = self.client.post(reverse("watchlist"), {"stock_code": "A0001"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["stock_code"], "A0001")
        self.assertEqual(Decimal(resp.data["current_price"]), Decimal("80000"))
        self.assertTrue(
            UserLikedStock.objects.filter(user=self.user, stock=self.stock).exists()
        )

    @patch("recommend.services.fetch_price", return_value=PRICE)
    def test_add_is_idempotent(self, _):
        self.client.post(reverse("watchlist"), {"stock_code": "A0001"}, format="json")
        self.client.post(reverse("watchlist"), {"stock_code": "A0001"}, format="json")
        self.assertEqual(UserLikedStock.objects.filter(user=self.user).count(), 1)

    def test_add_invalid_stock_404(self):
        resp = self.client.post(reverse("watchlist"), {"stock_code": "ZZZZ"}, format="json")
        self.assertEqual(resp.status_code, 404)

    @patch("recommend.services.fetch_price", return_value=PRICE)
    def test_list(self, _):
        UserLikedStock.objects.create(user=self.user, stock=self.stock)
        resp = self.client.get(reverse("watchlist"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["items"][0]["stock_code"], "A0001")
        self.assertEqual(Decimal(resp.data["items"][0]["current_price"]), Decimal("80000"))

    @patch("recommend.services.fetch_price", side_effect=RuntimeError("KIS down"))
    def test_list_price_graceful_on_kis_failure(self, _):
        UserLikedStock.objects.create(user=self.user, stock=self.stock)
        resp = self.client.get(reverse("watchlist"))
        self.assertEqual(resp.status_code, 200)  # 목록 자체는 안 막힘
        self.assertIsNone(resp.data["items"][0]["current_price"])  # 가격만 None

    def test_remove(self):
        UserLikedStock.objects.create(user=self.user, stock=self.stock)
        resp = self.client.delete(reverse("watchlist-item", kwargs={"code": "A0001"}))
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(
            UserLikedStock.objects.filter(user=self.user, stock=self.stock).exists()
        )

    def test_remove_not_in_watchlist_404(self):
        resp = self.client.delete(reverse("watchlist-item", kwargs={"code": "A0001"}))
        self.assertEqual(resp.status_code, 404)

    @patch("recommend.services.fetch_price", return_value=PRICE)
    def test_watchlist_is_per_user(self, _):
        other = _make_user("other")
        UserLikedStock.objects.create(user=other, stock=self.stock)  # 남의 관심종목
        resp = self.client.get(reverse("watchlist"))
        self.assertEqual(resp.data["total"], 0)  # 내 것만 보여야 함


class SwipeRecommendTests(TestCase):
    """오늘의 궁합 추천 (스와이프 카드) — SCRUM-25."""

    def setUp(self):
        self.user = _make_user("rec")
        InvestmentProfile.objects.create(
            user=self.user, risk_tolerance=5, investment_term=5, experience=5,
            loss_aversion=1, behavior=5, profiled_at=timezone.now(),
        )
        UserPreferredSector.objects.create(user=self.user, sector="전기·전자", weight=Decimal("1.0"))
        today = date.today()
        yesterday = today - timedelta(days=1)
        # (code, name, sector, (변동성, 가치, 성장, 안정성))
        specs = [
            ("AAA", "고성장주", "전기·전자", (0.95, 0.30, 0.95, 0.10)),  # 공격·장기·숙련에 최적
            ("BBB", "안정주", "금융", (0.10, 0.80, 0.20, 0.90)),
            ("CCC", "이미담음", "전기·전자", (0.90, 0.30, 0.90, 0.20)),
        ]
        self.stocks = {}
        for code, name, sector, (v, val, g, st) in specs:
            stock = Stock.objects.create(code=code, name=name, market="KOSPI", currency="KRW",
                                         sector=sector, market_cap=500_000_000_000)
            self.stocks[code] = stock
            StockDna.objects.create(
                stock=stock, volatility=Decimal(str(v)), value_score=Decimal(str(val)),
                growth_score=Decimal(str(g)), stability=Decimal(str(st)),
                sector=sector, calculated_date=today,
            )
            for d, c in [(yesterday, "9900"), (today, "10000")]:
                StockPrice.objects.create(stock=stock, price_date=d, open=Decimal("9900"),
                                          high=Decimal("10100"), low=Decimal("9800"),
                                          close=Decimal(c), volume=1000)
        UserLikedStock.objects.create(user=self.user, stock=self.stocks["CCC"])  # 이미 담음
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_swipe_ok(self):
        resp = self.client.get(reverse("recommend-swipe"))
        self.assertEqual(resp.status_code, 200)
        codes = [it["stock_code"] for it in resp.data["items"]]
        self.assertNotIn("CCC", codes)              # 이미 담은 종목 제외
        self.assertIn("AAA", codes)
        scores = [it["match_score"] for it in resp.data["items"]]
        self.assertEqual(scores, sorted(scores, reverse=True))  # 점수 내림차순
        top = resp.data["items"][0]
        self.assertEqual(top["stock_code"], "AAA")
        self.assertEqual(top["rank"], 1)
        self.assertIn("volatility", top["dna"])
        self.assertTrue(top["reason"])
        self.assertEqual(Decimal(str(top["current_price"])), Decimal("10000"))
        self.assertAlmostEqual(top["change_rate"], 1.01, places=2)

    def test_cache_saved(self):
        self.client.get(reverse("recommend-swipe"))
        self.assertTrue(RecommendationCache.objects.filter(
            user=self.user, rec_type=RecommendationCache.RecType.ONBOARDING).exists())

    def test_limit(self):
        resp = self.client.get(reverse("recommend-swipe"), {"limit": 1})
        self.assertEqual(len(resp.data["items"]), 1)

    def test_requires_onboarding(self):
        u2 = _make_user("noonb")
        c2 = APIClient()
        c2.force_authenticate(user=u2)
        resp = c2.get(reverse("recommend-swipe"))
        self.assertEqual(resp.status_code, 409)

    def test_requires_auth(self):
        resp = APIClient().get(reverse("recommend-swipe"))
        self.assertEqual(resp.status_code, 401)
