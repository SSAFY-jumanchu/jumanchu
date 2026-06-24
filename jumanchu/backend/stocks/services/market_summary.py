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
from django.utils import timezone

from stocks.models import Stock
from stocks.services.price_dispatch import get_kis_client

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
USD_KRW_RATE = Decimal("1500")  # 전체 탭 거래대금 정렬용 환율(USD→KRW). TODO: 라이브 환율로 교체

_POPULAR_SORT = {
    "value":  (lambda x: x["trading_value_krw"] or Decimal("0"), True),   # 거래대금 ↓
    "volume": (lambda x: x["volume"] or 0, True),                          # 거래량 ↓
    "up":     (lambda x: x["change_rate"], True),                          # 급상승 ↓
    "down":   (lambda x: x["change_rate"], False),                         # 급하락 ↑
}


def _popular_pool(markets: list[str], raw_rows: list, mapper) -> list[dict]:
    """KIS 거래량순위 행 → 우리 활성 DB 종목만 + 종목별 market 태깅 + 거래대금 KRW 환산."""
    code_to_market = dict(
        Stock.objects.filter(market__in=markets, is_active=True).values_list("code", "market")
    )
    out = []
    for row in raw_rows:
        m = mapper(row)
        mk = code_to_market.get(m["code"])
        if mk is None:
            continue  # 우리 DB 비활성/미수록 종목 제외(클릭 불가 방지)
        m["market"] = mk
        tv = m.get("trading_value")
        m["trading_value_krw"] = tv * USD_KRW_RATE if (tv is not None and mk in _US_MARKETS) else tv
        out.append(m)
    return out


def popular_ranking(market: str = "all", sort: str = "value", size: int = 30) -> list[dict]:
    """인기 종목 랭킹. 거래량순위 TR(거래대금·거래량·등락률·현재가 포함)을 시장별로 받아
    전체(all)는 합쳐 재정렬한다. 거래대금 정렬은 USD→KRW 환산해 통화를 통일.
    급상승/급하락은 '거래대금 상위 풀 내'에서 등락률 정렬(=활발히 거래되는 종목 중 등락 큰 순)."""
    c = get_kis_client()
    items: list[dict] = []
    if market in ("all", "domestic"):
        rows = _retry(c.get_domestic_volume_rank).get("output", [])
        items += _popular_pool(_KR_MARKETS, rows, _map_kr_rank)
    if market in ("all", "overseas"):
        rows = _retry(lambda: c.get_overseas_volume_rank(_US_EXCD)).get("output2", [])
        items += _popular_pool(_US_MARKETS, rows, _map_us_rank)
    key, reverse = _POPULAR_SORT.get(sort, _POPULAR_SORT["value"])
    items.sort(key=key, reverse=reverse)
    return items[:size]


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
