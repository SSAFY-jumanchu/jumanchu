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
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from stocks.models import Stock
from stocks.services.price_dispatch import get_kis_client

logger = logging.getLogger(__name__)

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


def get_indices() -> list[dict]:
    """대표 지수 4개를 KIS에서 조회. 개별 실패는 skip(홈은 P0)."""
    client = get_kis_client()
    out: list[dict] = []
    for code, name, iscd in _KR_INDICES:
        try:
            out.append(_map_kr_index(code, name, client.get_domestic_index(iscd)["output"]))
        except Exception:  # noqa: BLE001 — 지수 1개 실패가 홈 전체를 막지 않도록
            logger.warning("국내지수 조회 실패: %s", code, exc_info=True)
    today = timezone.now().date()
    d_to = today.strftime("%Y%m%d")
    d_from = (today - timedelta(days=10)).strftime("%Y%m%d")  # 휴장 대비
    for code, name, iscd in _US_INDICES:
        try:
            out.append(_map_us_index(code, name, client.get_overseas_index(iscd, d_from, d_to)["output1"]))
        except Exception:  # noqa: BLE001
            logger.warning("해외지수 조회 실패: %s", code, exc_info=True)
    return out


# ----- 랭킹 매퍼 (KIS 순위 응답 → StockSummary) -----
def _map_kr_rank(row: dict) -> dict:
    """국내 등락률/거래량 순위 행. 등락률은 코드 필드명이 둘(fluctuation/volume) 다름."""
    return {
        "code": row.get("stck_shrn_iscd") or row.get("mksc_shrn_iscd") or "",
        "name": row.get("hts_kor_isnm", ""),
        "current": Decimal(row["stck_prpr"]),
        "change": Decimal(row["prdy_vrss"]),
        "change_rate": float(row["prdy_ctrt"]),
    }


def _map_us_rank(row: dict) -> dict:
    """해외 순위 행. diff는 부호 없는 값이라 sign(5=하락)으로 부호 보정. rate는 부호 포함."""
    change = Decimal(row["diff"])
    if row.get("sign") in ("4", "5"):  # 4 하한, 5 하락
        change = -change
    return {
        "code": row.get("symb", ""),
        "name": row.get("name") or row.get("ename", ""),
        "current": Decimal(row["last"]),
        "change": change,
        "change_rate": float(row["rate"]),
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

    gainers = keep(c.get_domestic_fluctuation("0").get("output", []))
    losers = keep(c.get_domestic_fluctuation("1").get("output", []))
    active_rows = keep(c.get_domestic_volume_rank().get("output", []))
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
                    c.get_overseas_volume_rank(_US_EXCD).get("output2", []))
        if m["code"] in active
    ]
    return {
        "top_gainers": sorted(pool, key=lambda r: r["change_rate"], reverse=True)[:_RANK_LIMIT],
        "top_losers": sorted(pool, key=lambda r: r["change_rate"])[:_RANK_LIMIT],
        "most_active": pool[:_RANK_LIMIT],
    }


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
