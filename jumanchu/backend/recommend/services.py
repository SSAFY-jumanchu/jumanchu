"""관심종목(워치리스트) 서비스 — UserLikedStock 기반 조회/추가/삭제.

현재가는 stocks의 KIS 경로(fetch_price)로 보강하되, 한 종목 조회가 실패해도
목록 전체를 막지 않고 그 항목의 가격만 None으로 둔다(브라우징 UX 우선).
장투 재검증용 스냅샷 필드(base_pbr/base_match_score/last_review_status)는
이번 범위 밖이라 비워둔다.
"""
from __future__ import annotations

from decimal import InvalidOperation

import requests

from recommend.models import UserLikedStock
from stocks.models import Stock
from stocks.services.price_dispatch import fetch_price


class StockNotFound(Exception):
    """종목 코드에 해당하는 (활성) 종목이 없음."""


def _safe_price(stock):
    """(current_price, change_rate). KIS 조회 실패 시 (None, None)."""
    try:
        p = fetch_price(stock)
        return p["current"], p["change_rate"]
    except (requests.HTTPError, requests.Timeout, RuntimeError, KeyError,
            ValueError, InvalidOperation):
        return None, None


def _item_dict(liked: UserLikedStock) -> dict:
    """WatchlistItemSerializer 모양 dict (현재가 보강 포함)."""
    stock = liked.stock
    price, rate = _safe_price(stock)
    return {
        "stock_code": stock.code,
        "stock_name": stock.name,
        "market": stock.market,
        "sector": stock.sector,
        "current_price": price,
        "change_rate": rate,
        "liked_at": liked.liked_at,
        "is_active": liked.is_active,
    }


def watchlist_items(user) -> list:
    """유저의 활성 관심종목 목록."""
    likes = (
        UserLikedStock.objects.filter(user=user, is_active=True)
        .select_related("stock")
        .order_by("-liked_at")
    )
    return [_item_dict(liked) for liked in likes]


def add_watchlist(user, stock_code: str) -> dict:
    """관심종목 추가 — 이미 있으면 그대로(멱등), 소프트 삭제 상태면 재활성화."""
    stock = Stock.objects.filter(code=stock_code, is_active=True).first()
    if stock is None:
        raise StockNotFound(stock_code)
    liked, _created = UserLikedStock.objects.get_or_create(user=user, stock=stock)
    if not liked.is_active:
        liked.is_active = True
        liked.save(update_fields=["is_active"])
    return _item_dict(liked)


def remove_watchlist(user, stock_code: str) -> bool:
    """관심종목 제거(하드 삭제). 삭제됐으면 True, 목록에 없었으면 False."""
    deleted, _ = UserLikedStock.objects.filter(
        user=user, stock__code=stock_code
    ).delete()
    return deleted > 0
