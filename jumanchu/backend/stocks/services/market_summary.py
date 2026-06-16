"""
시장 요약(MarketSummaryView)용 서비스 — 하이브리드.

- 지수(indices)  : KIS 신규 연동 (국내 inquire-index-price / 해외 inquire-daily-chartprice).
                   국내·해외가 API/필드 스키마가 달라 매퍼를 둘로 나눔.
- 랭킹(rankings) : 우리 DB(StockPrice) 최근 2거래일 비교로 계산 (KR 종목만).

지수 코드 (KIS 실호출 확인):
  코스피 0001 / 코스닥 1001 (국내)  ·  나스닥 COMP / S&P500 SPX (해외)
"""
from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone

from stocks.models import StockPrice
from stocks.services.price_dispatch import get_kis_client

logger = logging.getLogger(__name__)

# (응답 code, 표시 name, KIS iscd)
_KR_INDICES = [("KOSPI", "코스피", "0001"), ("KOSDAQ", "코스닥", "1001")]
_US_INDICES = [("COMP", "나스닥", "COMP"), ("SPX", "S&P500", "SPX")]
_KR_MARKETS = ["KOSPI", "KOSDAQ"]
_RANK_LIMIT = 5


# ----- 지수 (KIS) -----
def _map_kr_index(code: str, name: str, o: dict) -> dict:
    """국내 지수 output → IndexSummary dict. 등락/등락률이 응답에 직접 옴."""
    return {
        "code": code,
        "name": name,
        "current": float(o["bstp_nmix_prpr"]),
        "change": float(o["bstp_nmix_prdy_vrss"]),
        "change_rate": float(o["bstp_nmix_prdy_ctrt"]),
    }


def _map_us_index(code: str, name: str, o1: dict) -> dict:
    """해외 지수 output1 → IndexSummary dict.
    prdy_ctrt가 null로 올 수 있어 등락률은 현재가·전일종가로 직접 계산.
    """
    current = float(o1["ovrs_nmix_prpr"])
    prev_close = float(o1["ovrs_nmix_prdy_clpr"])
    change = current - prev_close
    change_rate = (change / prev_close * 100) if prev_close else 0.0
    return {
        "code": code,
        "name": name,
        "current": current,
        "change": change,
        "change_rate": change_rate,
    }


def get_indices() -> list[dict]:
    """대표 지수 4개를 KIS에서 조회. 개별 실패는 skip(홈은 P0 — 일부 지수 오류로 죽지 않게)."""
    client = get_kis_client()
    out: list[dict] = []

    for code, name, iscd in _KR_INDICES:
        try:
            o = client.get_domestic_index(iscd)["output"]
            out.append(_map_kr_index(code, name, o))
        except Exception:  # noqa: BLE001 — 지수 1개 실패가 홈 전체를 막지 않도록
            logger.warning("국내지수 조회 실패: %s", code, exc_info=True)

    today = timezone.now().date()
    d_to = today.strftime("%Y%m%d")
    d_from = (today - timedelta(days=10)).strftime("%Y%m%d")  # 휴장 대비 여유
    for code, name, iscd in _US_INDICES:
        try:
            o1 = client.get_overseas_index(iscd, d_from, d_to)["output1"]
            out.append(_map_us_index(code, name, o1))
        except Exception:  # noqa: BLE001
            logger.warning("해외지수 조회 실패: %s", code, exc_info=True)

    return out


# ----- 랭킹 (DB) -----
def _ranked_rows() -> list[dict]:
    """KR 종목(활성)을 최근 2거래일 종가로 비교해 랭킹 계산용 row 리스트 생성."""
    dates = list(
        StockPrice.objects.filter(stock__market__in=_KR_MARKETS)
        .values_list("price_date", flat=True)
        .distinct().order_by("-price_date")[:2]
    )
    if not dates:
        return []

    latest = dates[0]
    prev = dates[1] if len(dates) > 1 else None
    prev_map: dict[int, Decimal] = {}
    if prev is not None:
        prev_map = dict(
            StockPrice.objects.filter(price_date=prev, stock__market__in=_KR_MARKETS)
            .values_list("stock_id", "close")
        )

    rows = []
    for sp in (
        StockPrice.objects.filter(
            price_date=latest, stock__market__in=_KR_MARKETS, stock__is_active=True
        ).select_related("stock")
    ):
        pc = prev_map.get(sp.stock_id)
        change = (sp.close - pc) if pc is not None else Decimal("0")
        rate = float(change / pc * 100) if pc else 0.0
        rows.append({
            "code": sp.stock.code,
            "name": sp.stock.name,
            "current": sp.close,
            "change": change,
            "change_rate": rate,
            "volume": sp.volume,
        })
    return rows


# ----- 조립 -----
def market_summary() -> dict:
    """홈 상단 시장 요약 — 지수 4개 + 등락/거래량 랭킹 + 생성 시각."""
    rows = _ranked_rows()
    return {
        "indices": get_indices(),
        "top_gainers": sorted(rows, key=lambda r: r["change_rate"], reverse=True)[:_RANK_LIMIT],
        "top_losers": sorted(rows, key=lambda r: r["change_rate"])[:_RANK_LIMIT],
        "most_active": sorted(rows, key=lambda r: r["volume"], reverse=True)[:_RANK_LIMIT],
        "fetched_at": timezone.now(),
    }
