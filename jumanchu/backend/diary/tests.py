"""주식 일기 API 테스트 — SCRUM-26 (회고는 범위 밖)."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from diary.models import StockDiary
from portfolio.models import Account, Order
from stocks.models import Stock

User = get_user_model()


def _make_user(username="diarist"):
    return User.objects.create(username=username, nickname=username, birth_year=1995)


def _make_stock(code="A0001"):
    return Stock.objects.create(code=code, name="테스트", market="KOSPI", currency="KRW")


def _make_order(user, stock, key="o1"):
    account, _ = Account.objects.get_or_create(user=user)
    return Order.objects.create(
        user=user, account=account, stock=stock, side="BUY",
        quantity=10, price=Decimal("70000"), total_amount=Decimal("700000"),
        idempotency_key=key, status="FILLED",
    )


class DiaryTests(TestCase):
    def setUp(self):
        self.user = _make_user()
        self.stock = _make_stock("A0001")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_watch_without_order(self):
        resp = self.client.post(
            reverse("diary-list-create"),
            {"stock_code": "A0001", "action_type": "WATCH", "confidence": 4,
             "reason_category": "UNDERVALUED", "diary_date": "2026-06-14"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["action_type"], "WATCH")
        self.assertIsNone(resp.data["order_id"])
        self.assertEqual(resp.data["stock_code"], "A0001")

    def test_create_buy_with_own_order(self):
        order = _make_order(self.user, self.stock)
        resp = self.client.post(
            reverse("diary-list-create"),
            {"stock_code": "A0001", "order_id": order.id, "action_type": "BUY",
             "confidence": 5, "diary_date": "2026-06-14"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["order_id"], order.id)

    def test_create_invalid_stock_404(self):
        resp = self.client.post(
            reverse("diary-list-create"),
            {"stock_code": "ZZZZ", "action_type": "WATCH", "confidence": 3,
             "diary_date": "2026-06-14"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_create_with_others_order_400(self):
        other = _make_user("other")
        others_order = _make_order(other, self.stock, key="o-other")
        resp = self.client.post(
            reverse("diary-list-create"),
            {"stock_code": "A0001", "order_id": others_order.id, "action_type": "BUY",
             "confidence": 3, "diary_date": "2026-06-14"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["code"], "INVALID_ORDER")

    def test_create_confidence_out_of_range_400(self):
        resp = self.client.post(
            reverse("diary-list-create"),
            {"stock_code": "A0001", "action_type": "WATCH", "confidence": 6,
             "diary_date": "2026-06-14"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_list_filters_by_action_type(self):
        StockDiary.objects.create(
            user=self.user, stock=self.stock, action_type="BUY", confidence=4,
            diary_date="2026-06-14",
        )
        StockDiary.objects.create(
            user=self.user, stock=self.stock, action_type="WATCH", confidence=2,
            diary_date="2026-06-13",
        )
        resp = self.client.get(reverse("diary-list-create"), {"action_type": "BUY"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total"], 1)
        self.assertEqual(resp.data["items"][0]["action_type"], "BUY")

    def test_list_only_own(self):
        other = _make_user("other")
        StockDiary.objects.create(
            user=other, stock=self.stock, action_type="BUY", confidence=3,
            diary_date="2026-06-14",
        )
        resp = self.client.get(reverse("diary-list-create"))
        self.assertEqual(resp.data["total"], 0)

    def test_detail_owned(self):
        diary = StockDiary.objects.create(
            user=self.user, stock=self.stock, action_type="BUY", confidence=4,
            diary_date="2026-06-14",
        )
        resp = self.client.get(reverse("diary-detail", kwargs={"id": diary.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], diary.id)

    def test_detail_others_404(self):
        other = _make_user("other")
        diary = StockDiary.objects.create(
            user=other, stock=self.stock, action_type="BUY", confidence=4,
            diary_date="2026-06-14",
        )
        resp = self.client.get(reverse("diary-detail", kwargs={"id": diary.id}))
        self.assertEqual(resp.status_code, 404)

    def test_update_patch(self):
        diary = StockDiary.objects.create(
            user=self.user, stock=self.stock, action_type="BUY", confidence=4,
            diary_date="2026-06-14",
        )
        resp = self.client.patch(
            reverse("diary-detail", kwargs={"id": diary.id}),
            {"confidence": 2, "reason_category": "NEWS"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        diary.refresh_from_db()
        self.assertEqual(diary.confidence, 2)
        self.assertEqual(diary.reason_category, "NEWS")

    def test_update_others_404(self):
        other = _make_user("other")
        diary = StockDiary.objects.create(
            user=other, stock=self.stock, action_type="BUY", confidence=4,
            diary_date="2026-06-14",
        )
        resp = self.client.patch(
            reverse("diary-detail", kwargs={"id": diary.id}),
            {"confidence": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_delete(self):
        diary = StockDiary.objects.create(
            user=self.user, stock=self.stock, action_type="BUY", confidence=4,
            diary_date="2026-06-14",
        )
        resp = self.client.delete(reverse("diary-detail", kwargs={"id": diary.id}))
        self.assertEqual(resp.status_code, 204)
        self.assertFalse(StockDiary.objects.filter(id=diary.id).exists())
