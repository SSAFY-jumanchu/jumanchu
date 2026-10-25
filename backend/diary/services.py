"""일기 서비스 — 종목/주문 해석을 모아 작성·수정의 중복을 줄인다.

회고(DiaryReview)는 이번 범위 밖(킵). 단순 CRUD라 트랜잭션/락 없음.
"""
from __future__ import annotations

from diary.models import StockDiary
from portfolio.models import Order
from stocks.models import Stock


class StockNotFound(Exception):
    """종목 코드에 해당하는 (활성) 종목이 없음."""


class OrderNotOwned(Exception):
    """order_id가 주어졌으나 본인 주문이 아님(또는 없음)."""


# 작성/수정에서 그대로 옮겨 담는 필드(종목/주문 제외)
_WRITABLE = [
    "action_type",
    "reason_category",
    "confidence",
    "target_price",
    "stop_loss_price",
    "memo",
]


def _resolve_stock(stock_code: str) -> Stock:
    stock = Stock.objects.filter(code=stock_code, is_active=True).first()
    if stock is None:
        raise StockNotFound(stock_code)
    return stock


def _resolve_order(user, order_id):
    """order_id가 None이면 None(연결 없음). 있으면 본인 주문인지 확인."""
    if order_id is None:
        return None
    order = Order.objects.filter(id=order_id, user=user).first()
    if order is None:
        raise OrderNotOwned(order_id)
    return order


def create_diary(user, data: dict) -> StockDiary:
    stock = _resolve_stock(data["stock_code"])
    order = _resolve_order(user, data.get("order_id"))
    return StockDiary.objects.create(
        user=user,
        stock=stock,
        order=order,
        action_type=data["action_type"],
        reason_category=data.get("reason_category", ""),
        confidence=data["confidence"],
        target_price=data.get("target_price"),
        stop_loss_price=data.get("stop_loss_price"),
        memo=data.get("memo", ""),
    )


def update_diary(diary: StockDiary, user, data: dict) -> StockDiary:
    """부분 수정(partial). data에 들어온 필드만 갱신."""
    if "stock_code" in data:
        diary.stock = _resolve_stock(data["stock_code"])
    if "order_id" in data:
        diary.order = _resolve_order(user, data["order_id"])  # None이면 연결 해제
    for field in _WRITABLE:
        if field in data:
            setattr(diary, field, data[field])
    diary.save()
    return diary
