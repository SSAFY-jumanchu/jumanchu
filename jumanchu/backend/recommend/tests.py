"""관심종목(워치리스트) API 테스트 — SCRUM-26.

현재가(KIS)는 fetch_price를 patch하여 고정값으로 대체한다.
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from recommend.models import UserLikedStock
from stocks.models import Stock

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
