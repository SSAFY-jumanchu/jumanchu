"""관심종목(워치리스트) 서비스 — UserLikedStock 기반 조회/추가/삭제.

현재가는 stocks의 KIS 경로(fetch_price)로 보강하되, 한 종목 조회가 실패해도
목록 전체를 막지 않고 그 항목의 가격만 None으로 둔다(브라우징 UX 우선).
장투 재검증용 스냅샷 필드(base_pbr/base_match_score/last_review_status)는
이번 범위 밖이라 비워둔다.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import InvalidOperation

import requests
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from accounts.models import UserPreferredSector
from recommend.matching import recommend_for_user
from recommend.models import RecommendationCache, UserLikedStock
from stocks.models import Stock, StockPrice
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


# ───────────────────────── 스와이프 궁합 추천 (SCRUM-25) ─────────────────────────

class OnboardingRequired(Exception):
    """온보딩 미완료 — 추천 불가."""


def _last_prices(stock_ids) -> dict:
    """{stock_id: (current_price, change_rate%)} — StockPrice 최근 2개 종가로 계산."""
    rows = (
        StockPrice.objects.filter(stock_id__in=stock_ids)
        .order_by("stock_id", "-price_date")
        .values_list("stock_id", "close")
    )
    closes: dict = {}
    for sid, close in rows:
        closes.setdefault(sid, []).append(close)
    out = {}
    for sid, cs in closes.items():
        cur = cs[0]
        prev = cs[1] if len(cs) > 1 else None
        rate = None
        if prev not in (None, 0):
            rate = round(float((cur - prev) / prev) * 100, 2)
        out[sid] = (cur, rate)
    return out


def _like_counts(stock_ids) -> dict:
    """{stock_id: 관심 등록 수}."""
    rows = (
        UserLikedStock.objects.filter(stock_id__in=stock_ids, is_active=True)
        .values("stock_id").annotate(n=Count("id"))
    )
    return {r["stock_id"]: r["n"] for r in rows}


def _save_recommendation_cache(user, recs) -> None:
    """온보딩 궁합 추천 결과 저장 (유저별 교체, TTL 1일)."""
    expires = timezone.now() + timedelta(days=1)
    rows = [
        RecommendationCache(
            user=user, stock=r["stock"],
            rec_type=RecommendationCache.RecType.ONBOARDING,
            match_score=r["match_score"], rank=r["rank"],
            reason={"summary": r["reason"], "components": r["components"]},
            expires_at=expires,
        )
        for r in recs
    ]
    with transaction.atomic():
        RecommendationCache.objects.filter(
            user=user, rec_type=RecommendationCache.RecType.ONBOARDING
        ).delete()
        RecommendationCache.objects.bulk_create(rows)


def _dna_scores(dna) -> dict:
    def f(x):
        return None if x is None else float(x)
    return {
        "volatility": f(dna.volatility), "value_score": f(dna.value_score),
        "growth_score": f(dna.growth_score), "stability": f(dna.stability),
    }


def swipe_recommendations(user, limit: int = 30) -> list:
    """오늘의 궁합 추천 카드 — 대형주 궁합 상위 N(담은 종목 제외) + 가격·관심수, 캐시 저장."""
    profile = getattr(user, "investment_profile", None)
    if profile is None or profile.profiled_at is None:
        raise OnboardingRequired()
    sector_weights = {
        p.sector: float(p.weight)
        for p in UserPreferredSector.objects.filter(user=user)
    }
    exclude_ids = set(
        UserLikedStock.objects.filter(user=user, is_active=True).values_list("stock_id", flat=True)
    )
    recs = recommend_for_user(profile, sector_weights, limit=limit, exclude_ids=exclude_ids)
    if not recs:
        return []
    _save_recommendation_cache(user, recs)

    ids = [r["stock"].id for r in recs]
    prices = _last_prices(ids)
    likes = _like_counts(ids)
    cards = []
    for r in recs:
        stock = r["stock"]
        cur, rate = prices.get(stock.id, (None, None))
        cards.append({
            "stock_code": stock.code, "stock_name": stock.name,
            "market": stock.market, "sector": stock.sector,
            "match_score": r["match_score"], "rank": r["rank"],
            "dna": _dna_scores(r["dna"]), "reason": r["reason"],
            "current_price": cur, "change_rate": rate,
            "like_count": likes.get(stock.id, 0),
        })
    return cards
