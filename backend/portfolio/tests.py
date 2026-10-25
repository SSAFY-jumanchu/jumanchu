"""매매 서비스/뷰 테스트 — SCRUM-121.

- ExecuteBuyTests / ExecuteSellTests : 서비스 단위 (성공·검증·멱등·평단·실현손익)
- OrderApiTests                      : view 연결 end-to-end (preview/주문/목록/상세)
- ConcurrencyTests                   : select_for_update 동시성 (잔액 음수 방지)

현재가(KIS)는 _current_price를 patch하여 고정값으로 대체한다.
"""
from datetime import date
from decimal import Decimal
from threading import Thread
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connections
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from portfolio import services
from portfolio.models import Account, Holding, Order
from stocks.models import FinancialSummary, Stock, StockIndicator

User = get_user_model()
PRICE = Decimal("80000")


def _make_user(username):
    return User.objects.create(username=username, nickname=username, birth_year=1995)


def _make_stock(code="A0001"):
    return Stock.objects.create(code=code, name="테스트", market="KOSPI", currency="KRW")


class ExecuteBuyTests(TestCase):
    def setUp(self):
        self.user = _make_user("buyer")
        self.account = Account.objects.create(user=self.user)  # 잔액 1억
        self.stock = _make_stock()

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_buy_success(self, _):
        result = services.execute_buy(self.user, "A0001", 5, "k1")
        order = result["order"]
        self.account.refresh_from_db()
        holding = Holding.objects.get(user=self.user, stock=self.stock)
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.quantity, 5)
        self.assertEqual(order.fee, Decimal("60"))          # 400000 * 0.00015
        self.assertIsNone(order.realized_pnl)
        self.assertEqual(order.status, "FILLED")
        self.assertEqual(self.account.balance, Decimal("99599940"))  # 1억 - 400060
        self.assertEqual(holding.quantity, 5)
        self.assertEqual(holding.average_price, Decimal("80000"))
        # 응답 스냅샷은 트랜잭션 안에서 확정된 값
        self.assertEqual(result["balance_after"], Decimal("99599940"))
        self.assertEqual(result["holding_after"]["quantity"], 5)

    @patch("portfolio.services._current_price")
    def test_buy_weighted_average_rounded_to_won(self, mock_price):
        mock_price.return_value = Decimal("70000")
        services.execute_buy(self.user, "A0001", 10, "k1")
        mock_price.return_value = Decimal("80000")
        services.execute_buy(self.user, "A0001", 5, "k2")
        holding = Holding.objects.get(user=self.user, stock=self.stock)
        self.assertEqual(holding.quantity, 15)
        # (70000*10 + 80000*5)/15 = 73333.33 → 원 단위 73333
        self.assertEqual(holding.average_price, Decimal("73333"))

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_buy_insufficient_balance(self, _):
        with self.assertRaises(services.InsufficientBalance):
            services.execute_buy(self.user, "A0001", 100000, "k1")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("100000000"))  # 변동 없음(롤백)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Holding.objects.exists())

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_buy_idempotent(self, _):
        first = services.execute_buy(self.user, "A0001", 5, "dup")["order"]
        again = services.execute_buy(self.user, "A0001", 5, "dup")["order"]
        self.assertEqual(first.id, again.id)
        self.assertEqual(Order.objects.count(), 1)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("99599940"))  # 한 번만 차감


class ExecuteSellTests(TestCase):
    def setUp(self):
        self.user = _make_user("seller")
        self.account = Account.objects.create(user=self.user)  # 1억
        self.stock = _make_stock()
        Holding.objects.create(
            user=self.user, stock=self.stock, quantity=10, average_price=Decimal("70000")
        )

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_sell_success_realized_pnl(self, _):
        order = services.execute_sell(self.user, "A0001", 4, "s1")["order"]
        self.account.refresh_from_db()
        holding = Holding.objects.get(user=self.user, stock=self.stock)
        # 체결가 80000, 평단 70000 → 실현손익 (80000-70000)*4 = 40000
        self.assertEqual(order.realized_pnl, Decimal("40000"))
        self.assertEqual(order.fee, Decimal("48"))           # 320000 * 0.00015
        # 잔액 = 1억 + (320000 - 48)
        self.assertEqual(self.account.balance, Decimal("100319952"))
        self.assertEqual(holding.quantity, 6)
        self.assertEqual(holding.average_price, Decimal("70000"))  # 평단 불변

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_sell_all_deletes_holding(self, _):
        services.execute_sell(self.user, "A0001", 10, "s1")
        self.assertFalse(Holding.objects.filter(user=self.user, stock=self.stock).exists())

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_sell_insufficient_holding(self, _):
        with self.assertRaises(services.InsufficientHolding):
            services.execute_sell(self.user, "A0001", 11, "s1")
        self.account.refresh_from_db()
        holding = Holding.objects.get(user=self.user, stock=self.stock)
        self.assertEqual(self.account.balance, Decimal("100000000"))  # 변동 없음
        self.assertEqual(holding.quantity, 10)


class OrderApiTests(TestCase):
    def setUp(self):
        self.user = _make_user("apiuser")
        self.account = Account.objects.create(user=self.user)
        self.stock = _make_stock()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_buy_then_list_then_detail(self, _):
        # 매수
        resp = self.client.post(
            reverse("order-list-create"),
            {"stock_code": "A0001", "side": "BUY", "quantity": 5, "idempotency_key": "api1"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["order"]["side"], "BUY")
        self.assertIsNone(resp.data["order"]["realized_pnl"])
        # DRF는 Decimal을 문자열로 직렬화 → 숫자 비교 위해 Decimal로 파싱
        self.assertEqual(Decimal(resp.data["balance_after"]), Decimal("99599940"))
        order_id = resp.data["order"]["id"]

        # 목록
        list_resp = self.client.get(reverse("order-list-create"))
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.data["total"], 1)

        # 상세
        detail = self.client.get(reverse("order-detail", kwargs={"id": order_id}))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["order"]["id"], order_id)
        self.assertIsNone(detail.data["related_diary_id"])

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_order_list_malformed_date_ignored(self, _):
        self.client.post(
            reverse("order-list-create"),
            {"stock_code": "A0001", "side": "BUY", "quantity": 1, "idempotency_key": "d1"},
            format="json",
        )
        # 잘못된 날짜(2024-13-45)로 500 안 나고 200, 필터는 무시
        resp = self.client.get(reverse("order-list-create"), {"from": "2024-13-45"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total"], 1)

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_buy_insufficient_returns_400(self, _):
        resp = self.client.post(
            reverse("order-list-create"),
            {"stock_code": "A0001", "side": "BUY", "quantity": 100000, "idempotency_key": "x"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["code"], "INSUFFICIENT_BALANCE")

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_preview_buy_no_db_write(self, _):
        Holding.objects.create(
            user=self.user, stock=self.stock, quantity=10, average_price=Decimal("70000")
        )
        resp = self.client.post(
            reverse("order-preview"),
            {"stock_code": "A0001", "side": "BUY", "quantity": 5},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["is_valid"])
        # 추가매수 후 평단 73333 (원 단위). 직렬화 문자열 → Decimal 파싱
        self.assertEqual(Decimal(resp.data["preview"]["avg_price_after"]), Decimal("73333"))
        self.assertEqual(Order.objects.count(), 0)  # preview는 DB 변경 없음


class ConcurrencyTests(TransactionTestCase):
    """select_for_update가 동시 매수를 직렬화하는지 검증."""

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_concurrent_buys_never_oversell(self, _):
        user = _make_user("racer")
        # 80000짜리 1주(수수료 포함 80012)만 가능한 잔액
        Account.objects.create(user=user, balance=Decimal("100000"))
        _make_stock("R0001")

        errors = []

        def buy(key):
            try:
                services.execute_buy(user, "R0001", 1, key)
            except services.InsufficientBalance:
                pass
            except Exception as exc:  # 예상 못한 예외 수집
                errors.append(exc)
            finally:
                connections.close_all()

        threads = [Thread(target=buy, args=(f"c{i}",)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        account = Account.objects.get(user=user)
        self.assertGreaterEqual(account.balance, Decimal("0"))           # 음수 절대 안 됨
        self.assertEqual(Order.objects.filter(user=user).count(), 1)     # 딱 1건만 체결
        self.assertEqual(account.balance, Decimal("19988"))              # 100000 - 80012


class PortfolioReadTests(TestCase):
    def setUp(self):
        self.user = _make_user("reader")
        self.account = Account.objects.create(user=self.user, balance=Decimal("50000000"))  # 현금 5천만
        self.stock = _make_stock("A0001")
        self.stock2 = _make_stock("B0002")
        Holding.objects.create(
            user=self.user, stock=self.stock, quantity=10, average_price=Decimal("70000")
        )
        Holding.objects.create(
            user=self.user, stock=self.stock2, quantity=5, average_price=Decimal("100000")
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_summary(self, _):
        resp = self.client.get(reverse("portfolio-summary"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["holdings_count"], 2)
        # 평가액 10*80000 + 5*80000 = 1,200,000 / 투자원금 700000+500000 = 1,200,000 → 손익 0
        self.assertEqual(Decimal(resp.data["total_current_value"]), Decimal("1200000"))
        self.assertEqual(Decimal(resp.data["total_profit_loss"]), Decimal("0"))
        # 총자산 = 현금 5천만 + 주식 120만
        self.assertEqual(Decimal(resp.data["total_assets"]), Decimal("51200000"))

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_holdings_list_sorted_by_value_desc(self, _):
        resp = self.client.get(reverse("portfolio-holdings"), {"sort": "value", "order": "desc"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_count"], 2)
        # 평가액 큰 순: A0001(80만) > B0002(40만)
        self.assertEqual(resp.data["items"][0]["stock"]["code"], "A0001")

    def test_balance(self):
        resp = self.client.get(reverse("portfolio-balance"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Decimal(resp.data["account"]["balance"]), Decimal("50000000"))

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_allocation_cash_and_stocks(self, _):
        resp = self.client.get(reverse("portfolio-allocation"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["by_stock"]), 2)
        # 현금 5천만 / 총자산 5120만 ≈ 97.7%
        self.assertGreater(resp.data["cash_rate"], 95)

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_holding_detail_held(self, _):
        resp = self.client.get(reverse("portfolio-holding-detail", kwargs={"code": "A0001"}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["holding"]["quantity"], 10)

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_holding_detail_not_held_404(self, _):
        _make_stock("Z9999")  # 종목은 있지만 미보유
        resp = self.client.get(reverse("portfolio-holding-detail", kwargs={"code": "Z9999"}))
        self.assertEqual(resp.status_code, 404)


class HoldingReviewTests(TestCase):
    """장투 재검증 — 매수 시점 스냅샷 + 보유 상세의 🟢🟡🔴 판정."""

    def setUp(self):
        self.user = _make_user("careuser")
        self.account = Account.objects.create(user=self.user)
        self.stock = _make_stock("A0001")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _indicator(self, roe, pbr):
        # 비율은 fraction 저장(0.20=20%). pbr은 배수(1.5).
        return StockIndicator.objects.create(
            stock=self.stock, roe=roe, pbr=pbr, calculated_date=date(2026, 6, 20),
        )

    def _financials(self, debt_ratio, net_profit_yoy):
        return FinancialSummary.objects.create(
            stock=self.stock, fiscal_period="2025", debt_ratio=debt_ratio,
            net_profit_yoy=net_profit_yoy, data_source="DART",
        )

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_buy_snapshots_base_pbr(self, _):
        self._indicator(roe=0.20, pbr=1.5)
        services.execute_buy(self.user, "A0001", 1, "k1")
        holding = Holding.objects.get(user=self.user, stock=self.stock)
        self.assertEqual(holding.base_pbr, Decimal("1.5000"))

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_review_green_when_healthy(self, _):
        self._indicator(roe=0.20, pbr=1.5)                      # ROE 20%, PBR 1.5
        self._financials(debt_ratio=1.0, net_profit_yoy=0.15)  # 부채 100%, 순익 +15%
        services.execute_buy(self.user, "A0001", 1, "k1")      # base_pbr=1.5 → 이탈 0
        resp = self.client.get(reverse("portfolio-holding-detail", kwargs={"code": "A0001"}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["review"]["status"], "GREEN")
        self.assertEqual(resp.data["review"]["violations"], [])

    @patch("portfolio.services._current_price", return_value=PRICE)
    def test_review_red_when_weak(self, _):
        # ROE 5%(<10) · 부채 300%(>200) · 순익 -10%(<=0) → 위반 3개
        self._indicator(roe=0.05, pbr=1.5)
        self._financials(debt_ratio=3.0, net_profit_yoy=-0.10)
        services.execute_buy(self.user, "A0001", 1, "k1")
        resp = self.client.get(reverse("portfolio-holding-detail", kwargs={"code": "A0001"}))
        self.assertEqual(resp.data["review"]["status"], "RED")
        self.assertEqual(len(resp.data["review"]["violations"]), 3)
