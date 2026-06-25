"""
시장 요약(MarketSummaryView)용 서비스 — 전부 KIS 실시간.

- 지수(indices)  : 국내 inquire-index-price / 해외 inquire-daily-chartprice.
- 랭킹(kr / us)  : KIS 순위 API. 한 번 호출로 시장 전체 상위 종목을 받음(종목별 호출 X).
                   KR·US가 응답 필드가 달라 매퍼를 분리.
                   US는 KIS가 전체 미국 시장을 주므로 우리 DB의 is_active 종목만 노출.

지수 코드: 코스피 0001 / 코스닥 1001 (국내) · 나스닥 COMP / S&P500 SPX (해외)
"""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache
from django.db.models import F
from django.utils import timezone

from stocks.models import Stock
from stocks.services.price_dispatch import (
    VOLPOWER_EMPTY, VOLPOWER_TTL, fetch_rank_price, fetch_volume_power,
    get_kis_client, rankprice_key, volpower_key,
)

logger = logging.getLogger(__name__)


def _retry(fn, attempts: int = 3, delay: float = 0.5):
    """KIS 간헐 5xx/timeout 대비 짧은 재시도. 4xx는 재시도 무의미해 즉시 중단, 마지막 실패는 raise."""
    last = None
    for i in range(attempts):
        try:
            return fn()
        except (requests.HTTPError, requests.Timeout, RuntimeError) as exc:
            resp = getattr(exc, "response", None)
            status = getattr(resp, "status_code", None)
            if isinstance(exc, requests.HTTPError) and status is not None and status < 500:
                raise
            last = exc
            if i < attempts - 1:
                time.sleep(delay)
    raise last


# (응답 code, 표시 name, KIS iscd)
_KR_INDICES = [("KOSPI", "코스피", "0001"), ("KOSDAQ", "코스닥", "1001")]
_US_INDICES = [("COMP", "나스닥", "COMP"), ("SPX", "S&P500", "SPX")]
_KR_MARKETS = ["KOSPI", "KOSDAQ"]
_US_MARKETS = ["NASDAQ", "NYSE"]
_US_EXCD = "NAS"          # 미국 순위는 나스닥 기준 (NYSE는 후속)
_RANK_LIMIT = 5
_EMPTY_RANKINGS = {"top_gainers": [], "top_losers": [], "most_active": []}


# ----- 지수 (KIS) -----
def _map_kr_index(code: str, name: str, o: dict) -> dict:
    return {
        "code": code, "name": name,
        "current": float(o["bstp_nmix_prpr"]),
        "change": float(o["bstp_nmix_prdy_vrss"]),
        "change_rate": float(o["bstp_nmix_prdy_ctrt"]),
    }


def _map_us_index(code: str, name: str, o1: dict) -> dict:
    """prdy_ctrt가 null로 올 수 있어 등락률은 현재가·전일종가로 직접 계산."""
    current = float(o1["ovrs_nmix_prpr"])
    prev_close = float(o1["ovrs_nmix_prdy_clpr"])
    change = current - prev_close
    change_rate = (change / prev_close * 100) if prev_close else 0.0
    return {"code": code, "name": name, "current": current,
            "change": change, "change_rate": change_rate}


def _index_placeholder(code: str, name: str) -> dict:
    """지수 조회 실패 시 슬롯 보존용 — FE가 항상 4칸을 고정 순서로 받도록(값은 null)."""
    return {"code": code, "name": name, "current": None, "change": None, "change_rate": None}


def get_indices() -> list[dict]:
    """대표 지수 4개를 KIS에서 조회. 개별 실패해도 슬롯 유지(null 값) → 항상 4개·고정 순서 보장."""
    client = get_kis_client()
    out: list[dict] = []
    for code, name, iscd in _KR_INDICES:
        try:
            out.append(_map_kr_index(code, name, _retry(lambda i=iscd: client.get_domestic_index(i))["output"]))
        except Exception:  # noqa: BLE001 — 지수 1개 실패가 홈 전체를 막지 않도록
            logger.warning("국내지수 조회 실패: %s", code, exc_info=True)
            out.append(_index_placeholder(code, name))
    today = timezone.now().date()
    d_to = today.strftime("%Y%m%d")
    d_from = (today - timedelta(days=10)).strftime("%Y%m%d")  # 휴장 대비
    for code, name, iscd in _US_INDICES:
        try:
            out.append(_map_us_index(code, name, _retry(lambda i=iscd: client.get_overseas_index(i, d_from, d_to))["output1"]))
        except Exception:  # noqa: BLE001
            logger.warning("해외지수 조회 실패: %s", code, exc_info=True)
            out.append(_index_placeholder(code, name))
    return out


# ----- 랭킹 매퍼 (KIS 순위 응답 → StockSummary) -----
def _map_kr_rank(row: dict) -> dict:
    """국내 등락률/거래량 순위 행. 등락률은 코드 필드명이 둘(fluctuation/volume) 다름.
    거래대금(acml_tr_pbmn, 원)·거래량(acml_vol)은 거래량순위 응답에만 있어 .get으로 방어."""
    tr_pbmn = row.get("acml_tr_pbmn")
    vol = row.get("acml_vol")
    return {
        "code": row.get("stck_shrn_iscd") or row.get("mksc_shrn_iscd") or "",
        "name": row.get("hts_kor_isnm", ""),
        "current": Decimal(row["stck_prpr"]),
        "change": Decimal(row["prdy_vrss"]),
        "change_rate": float(row["prdy_ctrt"]),
        "trading_value": Decimal(tr_pbmn) if tr_pbmn not in (None, "") else None,
        "volume": int(vol) if vol not in (None, "") else None,
    }


def _map_us_rank(row: dict) -> dict:
    """해외 순위 행. diff는 부호 없는 값이라 sign(5=하락)으로 부호 보정. rate는 부호 포함."""
    change = Decimal(row["diff"])
    if row.get("sign") in ("4", "5"):  # 4 하한, 5 하락
        change = -change
    tamt = row.get("tamt")
    tvol = row.get("tvol")
    return {
        "code": row.get("symb", ""),
        "name": row.get("name") or row.get("ename", ""),
        "current": Decimal(row["last"]),
        "change": change,
        "change_rate": float(row["rate"]),
        "trading_value": Decimal(tamt) if tamt not in (None, "") else None,  # USD
        "volume": int(tvol) if tvol not in (None, "") else None,
    }


# ----- 랭킹 (KIS 순위 API) -----
def _active_codes(markets: list[str]) -> set[str]:
    """우리 DB의 활성 종목 코드 — KIS 순위를 이걸로 필터(미보유·비활성·ETN 등 클릭 불가 종목 제외)."""
    return set(
        Stock.objects.filter(market__in=markets, is_active=True)
        .values_list("code", flat=True)
    )


def _kr_rankings() -> dict:
    c = get_kis_client()
    active = _active_codes(_KR_MARKETS)

    def keep(rows: list) -> list:
        return [m for m in (_map_kr_rank(r) for r in rows) if m["code"] in active]

    gainers = keep(_retry(lambda: c.get_domestic_fluctuation("0")).get("output", []))
    losers = keep(_retry(lambda: c.get_domestic_fluctuation("1")).get("output", []))
    active_rows = keep(_retry(c.get_domestic_volume_rank).get("output", []))
    # KIS 순위 행 순서가 등락률과 100% 일치하진 않아 직접 정렬(거래량은 KIS 순서 신뢰).
    return {
        "top_gainers": sorted(gainers, key=lambda r: r["change_rate"], reverse=True)[:_RANK_LIMIT],
        "top_losers": sorted(losers, key=lambda r: r["change_rate"])[:_RANK_LIMIT],
        "most_active": active_rows[:_RANK_LIMIT],
    }


def _us_rankings() -> dict:
    """미국은 KIS 전체시장 %순위 상위가 동전주라 우리 대형주가 거의 안 낌.
    그래서 거래량 순위 풀(우리 활성 종목)을 공통 소스로 사용:
    most_active=거래량순, top_gainers/losers=그 풀을 등락률로 재정렬.
    """
    c = get_kis_client()
    active = _active_codes(_US_MARKETS)
    pool = [
        m for m in (_map_us_rank(r) for r in
                    _retry(lambda: c.get_overseas_volume_rank(_US_EXCD)).get("output2", []))
        if m["code"] in active
    ]
    return {
        "top_gainers": sorted(pool, key=lambda r: r["change_rate"], reverse=True)[:_RANK_LIMIT],
        "top_losers": sorted(pool, key=lambda r: r["change_rate"])[:_RANK_LIMIT],
        "most_active": pool[:_RANK_LIMIT],
    }


# ----- 인기 종목 랭킹 (StocksView 인기 탭: 전체/국내/해외 × 거래대금/거래량/급상승/급하락) -----
USD_KRW_RATE = settings.USD_KRW_RATE  # USD→KRW 환산(전체 탭 정렬·원화 통일). settings 고정값

_POPULAR_SORT = {
    "value":  (lambda x: x["trading_value_krw"] or Decimal("0"), True),   # 거래대금 ↓
    "volume": (lambda x: x["volume"] or 0, True),                          # 거래량 ↓
    "up":     (lambda x: x["change_rate"] or 0.0, True),                   # 급상승 ↓
    "down":   (lambda x: x["change_rate"] or 0.0, False),                  # 급하락 ↑
}

# 후보 시장: FE와 동일(전체=국내+해외, 국내=KOSPI, 해외=NASDAQ). KOSDAQ/NYSE는 후속 확장.
_POPULAR_CANDIDATE_MARKETS = {
    "all": ["KOSPI", "NASDAQ"], "domestic": ["KOSPI"], "overseas": ["NASDAQ"],
}
_PRICE_FILL_LIMIT = 12  # 시세 캐시 미스 중 요청 경로에서 즉석 채울 최대 개수(워밍 전·드리프트 대응)


def _market_cap_candidates(market: str, size: int) -> list[Stock]:
    """랭킹 후보 = DB 시총상위 (실시간 거래대금·등락률은 시세로 매김). 전체는 시장별 반반."""
    markets = _POPULAR_CANDIDATE_MARKETS.get(market, _POPULAR_CANDIDATE_MARKETS["all"])
    per = size // len(markets) if len(markets) > 1 else size
    stocks: list[Stock] = []
    for m in markets:
        stocks += list(
            Stock.objects.filter(market=m, is_active=True)
            # market_cap NULL은 맨 뒤로 (기본 -market_cap은 Postgres에서 NULL이 앞 → 잡주가 1위 됨)
            .order_by(F("market_cap").desc(nulls_last=True))[:per]
        )
    return stocks[:size]


def _apply_currency(it: dict) -> None:
    """current_krw/currency/trading_value_krw 부착 (US는 ×환율, KR은 그대로)."""
    is_us = it["market"] in _US_MARKETS
    it["currency"] = "USD" if is_us else "KRW"
    cur, tv = it.get("current"), it.get("trading_value")
    it["current_krw"] = cur * USD_KRW_RATE if (cur is not None and is_us) else cur
    it["trading_value_krw"] = tv * USD_KRW_RATE if (tv is not None and is_us) else tv


def _candidates_cached(market: str, size: int) -> list[dict]:
    """시총상위 후보 메타(code/name/market/sector)를 캐시 — DB 쿼리를 요청 hot path에서 제거.
    시총 후보는 거의 불변이라 5분 캐시. (요청마다 Neon 연결 ~0.5s 물던 것 제거)"""
    key = f"markets:candidates:{market}:{size}"
    items = cache.get(key)
    if items is None:
        items = [{"code": s.code, "name": s.name, "market": s.market, "sector": s.sector}
                 for s in _market_cap_candidates(market, size)]
        cache.set(key, items, timeout=300)
    return items


def _attach_prices(items: list[dict]) -> list[dict]:
    """후보 행(dict)에 시세 부착. 랭킹 시세캐시(stock:rankprice:*) 우선, 미스는 ≤N개만 즉석 fetch.
    시세 없는 행은 값 None(=FE '—'), 정렬키 change_rate는 0 처리."""
    keys = [rankprice_key(it["market"], it["code"]) for it in items]
    cached = cache.get_many(keys)
    filled = 0
    for it, k in zip(items, keys):
        if k in cached or filled >= _PRICE_FILL_LIMIT:
            continue
        filled += 1
        # 미스필은 DB 없이(미저장 Stock 인스턴스) fetch — market/code만 있으면 됨
        p = fetch_rank_price(Stock(market=it["market"], code=it["code"]))
        if p is not None:
            cached[k] = p
    for it, k in zip(items, keys):
        p = cached.get(k)
        it["current"] = p["current"] if p else None
        it["change"] = p["change"] if p else None
        it["change_rate"] = p["change_rate"] if p else 0.0
        it["trading_value"] = p["trading_value"] if p else None
        it["volume"] = p["volume"] if p else None
    return items


def popular_ranking(market: str = "all", sort: str = "value", size: int = 100) -> list[dict]:
    """인기 종목 랭킹 = DB 시총상위 후보를 실시간 시세로 매겨 정렬.
    시세는 랭킹 워밍캐시(stock:rankprice:*) 우선 → 요청당 KIS 라이브 호출 최소화(미스만 ≤N).
    거래대금·현재가는 USD→KRW 환산값(_krw)도 같이 줘 전체/국내 원화통일·해외 토글 지원."""
    items = _attach_prices(_candidates_cached(market, size))
    for it in items:
        _apply_currency(it)
    _attach_volume_power(items)
    key, reverse = _POPULAR_SORT.get(sort, _POPULAR_SORT["value"])
    items.sort(key=key, reverse=reverse)
    return items[:size]


# ----- 체결강도(거래비율) 부착 — 워밍 캐시 우선 + 미스 즉석 채움 -----
_VOLPOWER_FILL_LIMIT = 8  # 캐시 미스(새 진입 종목) 중 요청 경로에서 즉석 채울 최대 개수


def popular_universe_stocks(size: int = 100) -> list[Stock]:
    """워밍 대상 = 모든 탭(all/domestic/overseas) 후보의 합집합.
    domestic=상위 size KOSPI, overseas=상위 size NASDAQ → 합쳐 워밍해야 어느 탭이든 캐시 히트.
    (all 탭은 각 상위 size/2라 이 합집합의 부분집합 → 자동 커버)"""
    return _market_cap_candidates("domestic", size) + _market_cap_candidates("overseas", size)


def popular_universe(size: int = 100) -> list[tuple[str, str]]:
    """체결강도 워밍 대상 (market, code) — 위 합집합."""
    return [(s.market, s.code) for s in popular_universe_stocks(size)]


def _attach_volume_power(items: list[dict]) -> list[dict]:
    """각 행에 volume_power/buy_ratio/sell_ratio 부착.
    워밍 캐시(stock:volpower:*) 우선, 캐시에 없는 행은 상위 N개만 즉석 호출 후 적재(드리프트 대응)."""
    if not items:
        return items
    keys = [volpower_key(it["market"], it["code"]) for it in items]
    cached = cache.get_many(keys)
    filled = 0
    for it, k in zip(items, keys):
        if k in cached or filled >= _VOLPOWER_FILL_LIMIT:
            continue
        filled += 1
        vp = fetch_volume_power(it["market"], it["code"]) or VOLPOWER_EMPTY
        cache.set(k, vp, timeout=VOLPOWER_TTL)   # 음성(None)도 캐시 → 매 요청 라이브 재조회 방지
        cached[k] = vp
    for it, k in zip(items, keys):
        vp = cached.get(k)
        it["volume_power"] = vp["volume_power"] if vp else None
        it["buy_ratio"] = vp["buy_ratio"] if vp else None
        it["sell_ratio"] = vp["sell_ratio"] if vp else None
    return items


# ----- 조립 -----
def market_summary() -> dict:
    """홈 상단 시장 요약 — 지수 4개 + 한국·미국 랭킹 + 생성 시각. 시장별 실패는 빈 랭킹으로."""
    try:
        kr = _kr_rankings()
    except Exception:  # noqa: BLE001
        logger.warning("KR 랭킹 조회 실패", exc_info=True)
        kr = dict(_EMPTY_RANKINGS)
    try:
        us = _us_rankings()
    except Exception:  # noqa: BLE001
        logger.warning("US 랭킹 조회 실패", exc_info=True)
        us = dict(_EMPTY_RANKINGS)
    return {
        "indices": get_indices(),
        "kr": kr,
        "us": us,
        "fetched_at": timezone.now(),
    }
