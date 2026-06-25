"""관심종목(워치리스트) 서비스 — UserLikedStock 기반 조회/추가/삭제.

현재가는 stocks의 KIS 경로(fetch_price)로 보강하되, 한 종목 조회가 실패해도
목록 전체를 막지 않고 그 항목의 가격만 None으로 둔다(브라우징 UX 우선).
장투 재검증(🟢🟡🔴)은 보유(Holding) 기준으로 이동 — portfolio.services.review_holding.
여기 UserLikedStock은 단순 북마크다.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import InvalidOperation

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from accounts.models import UserPreferredSector
from recommend import scoring
from recommend.gms_client import make_gms_caller
from recommend.longterm_report import (
    FinancialMetrics, GrowthMetrics, LongTermScores, StockMeta, UserProfile,
    build_longterm_report,
)
from recommend.matching import _match_components, compute_match_score, recommend_for_user
from recommend.models import LongTermScore, RecommendationCache, StockDna, UserLikedStock
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


def _safe_quote(stock) -> dict:
    """현재가/등락률/거래대금 — 랭킹·리스트용. KIS 실패 시 전부 None(브라우징 막지 않음)."""
    try:
        p = fetch_price(stock)
        tv = p.get("trading_value")
        return {
            "current_price": float(p["current"]),
            "change_rate": p["change_rate"],
            "trading_value": float(tv) if tv is not None else None,
        }
    except (requests.HTTPError, requests.Timeout, RuntimeError, KeyError,
            ValueError, InvalidOperation):
        return {"current_price": None, "change_rate": None, "trading_value": None}


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


def longterm_ranking(user, limit: int | None = None, offset: int = 0) -> list:
    """개인별 전체 종목 장투 랭킹 (on-demand, 저장 안 함).

    종목 소계(LongTermScore.total_score, 70%) + 개인 궁합(compute_match_score, 30%)을
    longterm_total로 결합해 내림차순 정렬. LLM 호출 없음(숫자·등급만).
    → [{rank, stock_code, stock_name, market, sector, longterm_total, subtotal, userfit,
       financial, growth, current_price, change_rate, trading_value}]
    가격 3필드(current_price/change_rate/trading_value)는 반환 페이지만 종목별 KIS 조회(watchlist와 동일 패턴).
    """
    profile = getattr(user, "investment_profile", None)
    if profile is None or profile.profiled_at is None:
        raise OnboardingRequired()
    sector_weights = {
        p.sector: float(p.weight) for p in UserPreferredSector.objects.filter(user=user)
    }
    # 각 배치의 최신 일자 (StockDna=궁합 입력, LongTermScore=70% 소계)
    dna_date = (StockDna.objects.order_by("-calculated_date")
                .values_list("calculated_date", flat=True).first())
    lt_date = (LongTermScore.objects.order_by("-calculated_date")
               .values_list("calculated_date", flat=True).first())
    if dna_date is None or lt_date is None:
        return []  # 배치 미적재

    # 종목 소계(70%): {stock_id: (total_score, financial, growth)}
    lt_map = {
        row[0]: (float(row[1]), row[2], row[3])
        for row in LongTermScore.objects.filter(calculated_date=lt_date)
        .values_list("stock_id", "total_score", "financial_score", "growth_score")
    }
    # 궁합 입력 DNA — LongTermScore 있는 종목만 (양쪽 다 있어야 랭킹 가능)
    qs = (StockDna.objects.filter(calculated_date=dna_date, stock_id__in=lt_map.keys())
          .select_related("stock"))

    scored = []
    for dna in qs:
        subtotal, fin, grw = lt_map[dna.stock_id]
        userfit = compute_match_score(profile, dna, sector_weights)      # 30% (개인)
        total = scoring.longterm_total(subtotal, userfit)               # 소계×0.7 + 궁합×0.3
        scored.append((total, userfit, subtotal, fin, grw, dna.stock))
    scored.sort(key=lambda t: t[0], reverse=True)

    page = scored[offset: offset + limit if limit else None]
    # 페이지 종목 시세를 제한 병렬로 조회 — 순차 N콜 지연을 줄이되 동시성 8로 rate-limit 완화.
    with ThreadPoolExecutor(max_workers=8) as ex:
        quotes = list(ex.map(_safe_quote, [t[5] for t in page]))
    return [
        {
            "rank": offset + i,
            "stock_code": stock.code, "stock_name": stock.name,
            "market": stock.market, "sector": stock.sector,
            "longterm_total": round(total, 1),
            "subtotal": round(subtotal, 1),       # 종목 70% 베이스 (개인 무관)
            "userfit": round(userfit, 1),         # 궁합 30% (개인)
            "financial": float(fin) if fin is not None else None,
            "growth": float(grw) if grw is not None else None,
            **quotes[i - 1],                      # current_price / change_rate / trading_value (KIS, 병렬)
        }
        for i, (total, userfit, subtotal, fin, grw, stock) in enumerate(page, start=1)
    ]


def _metric(obj, attr) -> float | None:
    """obj.attr 를 fraction(0.1088) → %(10.88). obj/값 없으면 None."""
    if obj is None:
        return None
    v = getattr(obj, attr)
    return None if v is None else float(v) * 100


def _portfolio_weight(user, stock) -> float | None:
    """이 종목의 포트폴리오 비중 %(취득원가 기준). 보유 없으면 None."""
    from portfolio.models import Holding
    rows = list(Holding.objects.filter(user=user, quantity__gt=0)
                .values_list("stock_id", "quantity", "average_price"))
    basis = {sid: float(q) * float(p) for sid, q, p in rows}
    total = sum(basis.values())
    if total <= 0 or stock.id not in basis:
        return None
    return basis[stock.id] / total * 100


def longterm_report(user, code, *, llm=None, force: bool = False) -> dict:
    """보유/관심 종목 1개 → 장투 케어 AI 리포트(4문장). rec_type='long_term' 캐시(TTL 1일).

    재무·성장 점수는 LongTermScore(일배치), 궁합(userfit)은 on-demand. LLM 1콜.
    llm 미지정 시 GMS GPT-4o. force=True면 캐시 무시·재생성.
    """
    stock = Stock.objects.filter(code=code, is_active=True).first()
    if stock is None:
        raise StockNotFound()

    # ① 캐시 히트 (rec_type='long_term', 미만료) → LLM 재호출 없이 즉시 반환
    if not force:
        cached = (RecommendationCache.objects
                  .filter(user=user, stock=stock, rec_type=RecommendationCache.RecType.LONG_TERM)
                  .first())
        if cached and cached.reason and cached.expires_at > timezone.now():
            return cached.reason

    # ② 입력 로드 (DB는 fraction 저장 → ×100)
    fs = stock.financials.order_by("-fiscal_period").first()
    ind = stock.indicators.order_by("-calculated_date").first()
    meta = StockMeta(stock.code, stock.name, stock.market, stock.sector, stock.currency)
    fin = FinancialMetrics(
        debt_ratio=_metric(fs, "debt_ratio"), current_ratio=_metric(fs, "current_ratio"),
        operating_margin=_metric(fs, "operating_margin"), net_margin=_metric(fs, "net_margin"),
        roe=_metric(ind, "roe"), roa=_metric(ind, "roa"),
        dividend_yield=_metric(ind, "dividend_yield"), payout_ratio=_metric(fs, "payout_ratio"),
        fiscal_period=fs.fiscal_period if fs else "",
    )
    grw = GrowthMetrics(
        revenue_yoy=_metric(fs, "revenue_yoy"),
        operating_profit_yoy=_metric(fs, "operating_profit_yoy"),
        net_profit_yoy=_metric(fs, "net_profit_yoy"),
    )

    # ③ 점수 — 소계(70%)는 LongTermScore(일배치), 없으면 지표로 즉석 폴백
    lt = LongTermScore.objects.filter(stock=stock).order_by("-calculated_date").first()
    if lt is not None:
        fin_s = float(lt.financial_score) if lt.financial_score is not None else 0.0
        grw_s = float(lt.growth_score) if lt.growth_score is not None else 0.0
        subtotal = float(lt.total_score) if lt.total_score is not None else None
    else:
        fin_s = scoring.financial_score(
            debt_ratio=fin.debt_ratio, current_ratio=fin.current_ratio,
            operating_margin=fin.operating_margin, net_margin=fin.net_margin, roe=fin.roe) or 0.0
        grw_s = scoring.growth_score(
            revenue_yoy=grw.revenue_yoy, operating_profit_yoy=grw.operating_profit_yoy,
            net_profit_yoy=grw.net_profit_yoy) or 0.0
        subtotal = scoring.stock_subtotal(fin_s or None, grw_s or None)

    # 궁합(30%) on-demand — 온보딩 프로필 + 그 종목 DNA가 있어야 적합도 포함
    userfit = None
    report_profile = None
    profile = getattr(user, "investment_profile", None)
    if profile is not None and profile.profiled_at is not None:
        dna = StockDna.objects.filter(stock=stock).order_by("-calculated_date").first()
        if dna is not None:
            prefs = list(UserPreferredSector.objects.filter(user=user))
            userfit = compute_match_score(
                profile, dna, {p.sector: float(p.weight) for p in prefs})
            report_profile = UserProfile(
                risk_type=profile.investment_style,
                preferred_period_months=profile.preferred_period,
                preferred_sectors=[p.sector for p in prefs],
                portfolio_weight_pct=_portfolio_weight(user, stock),
            )

    total = scoring.longterm_total(subtotal, userfit)
    scores = LongTermScores(
        financial=fin_s, growth=grw_s,
        total=total if total is not None else 0.0, userfit=userfit,
    )

    # ④ 리포트 생성 (LLM 1콜) — llm 미지정 시 GMS GPT-4o
    if llm is None:
        llm = make_gms_caller(api_key=settings.GMS_API_KEY)
    payload = build_longterm_report(meta, fin, grw, scores, report_profile, llm=llm).to_dict()

    # ⑤ 캐시 저장 (match_score=종합 total, reason=문장 JSON, TTL 1일)
    RecommendationCache.objects.update_or_create(
        user=user, stock=stock, rec_type=RecommendationCache.RecType.LONG_TERM,
        defaults=dict(match_score=round(scores.total, 2), reason=payload,
                      expires_at=timezone.now() + timedelta(days=1)),
    )
    return payload


def longterm_total_history(user, code, limit: int = 12) -> list[dict]:
    """장투 총점(최종 결과 = 상단 종합 점수) 히스토리.

    총점 = 소계(재무0.3+성장0.4, LongTermScore 일배치)×0.7 + 궁합×0.3 (scoring.longterm_total).
    궁합은 개인화(온보딩+종목 DNA) — 없으면 소계만(상단 점수와 동일 규칙).
    소계 일자별 + 오늘(현재) 점을 함께 반환.
    """
    stock = Stock.objects.filter(code=code, is_active=True).first()
    if stock is None:
        raise StockNotFound()

    # 궁합(개인) — 온보딩 + 종목 DNA 있어야. 없으면 None → 총점은 소계만
    userfit = None
    profile = getattr(user, "investment_profile", None)
    if profile is not None and profile.profiled_at is not None:
        dna = StockDna.objects.filter(stock=stock).order_by("-calculated_date").first()
        if dna is not None:
            sector_weights = {
                p.sector: float(p.weight) for p in UserPreferredSector.objects.filter(user=user)
            }
            userfit = compute_match_score(profile, dna, sector_weights)

    lt_rows = list(
        LongTermScore.objects.filter(stock=stock).order_by("-calculated_date")[:limit]
    )
    lt_rows.reverse()  # 오래된→최신 (FE가 직전 대비 상승 ▲ 비교)

    def _total(lt):
        sub = float(lt.total_score) if lt.total_score is not None else None
        return scoring.longterm_total(sub, userfit)

    out = []
    for lt in lt_rows:
        total = _total(lt)
        if total is None:
            continue
        out.append({
            "date": lt.calculated_date.isoformat(),
            "month": lt.calculated_date.strftime("%y.%m"),
            "score": round(total, 1),
        })
    # 오늘 측정값(현재 장투 총점)도 마지막 점으로 — 최신 소계가 오늘이 아니면 추가
    today = timezone.localdate()
    if lt_rows and lt_rows[-1].calculated_date != today:
        cur = _total(lt_rows[-1])
        if cur is not None:
            out.append({"date": today.isoformat(), "month": "오늘", "score": round(cur, 1)})
    return out


# 궁합 점수 5요소 라벨 (가중치: risk0.35/term0.20/sector0.20/exp0.15/style0.10)
_USERFIT_COMP_LABEL = {
    "risk": "위험성향", "term": "투자기간", "sector": "섹터", "exp": "경험", "style": "스타일",
}


def userfit_components(user, code) -> list[dict] | None:
    """현재 궁합 점수의 5요소 분해 [{label, value(0~100)}] — 위험성향/투자기간/섹터/경험/스타일 매칭.

    재무·성장처럼 궁합 카드에 근거를 보여주기 위함. 온보딩 전이거나 DNA 없으면 None.
    LLM·리포트 캐시와 무관하게 즉석 계산(결정적, 비용 없음).
    """
    stock = Stock.objects.filter(code=code, is_active=True).first()
    if stock is None:
        return None
    profile = getattr(user, "investment_profile", None)
    if profile is None or profile.profiled_at is None:
        return None
    dna = StockDna.objects.filter(stock=stock).order_by("-calculated_date").first()
    if dna is None:
        return None
    sector_weights = {
        p.sector: float(p.weight) for p in UserPreferredSector.objects.filter(user=user)
    }
    comps = _match_components(profile, dna, sector_weights)
    return [
        {"label": f"{_USERFIT_COMP_LABEL[k]} 매칭", "value": round(comps[k] * 100)}
        for k in ("risk", "term", "sector", "exp", "style")
    ]
