"""
StockPriceView 호출용 KIS 분기 모듈.

기능
----
- fetch_price(stock)        : KR/US 분기 → StockPriceSerializer 입력 dict 반환
- get_cache_ttl(stock)      : 장중 3s / 장외 60s (KST + ET 평일·시간 판정, 공휴일 미고려)
- get_kis_client()          : 모듈 lazy singleton (.env 로드 후 첫 호출 시 초기화)

매핑
----
KR (FHKST01010100) output:
  stck_prpr/stck_oprc/stck_hgpr/stck_lwpr/stck_sdpr → current/open/high/low/prev_close
  prdy_vrss → change (부호 포함값 그대로),  prdy_ctrt → change_rate
  acml_vol → volume,  acml_tr_pbmn → trading_value
  stck_mxpr/stck_llam → upper_limit/lower_limit
  iscd_stat_cls_code → warnings (00 정상 / 51,58 관리 / 52 거래정지 / 그 외 코드 그대로)

US (HHDFS76200200) output:
  last/open/high/low/base → current/open/high/low/prev_close
  change = current - prev_close, change_rate = 100 * change / prev_close (prev_close>0 guard)
  pvol/pamt → volume/trading_value
  uplp/dnlp → upper_limit/lower_limit  (해외는 0이 일반적)
  warnings → 모두 false (KIS 해외엔 상태 코드 없음)

예외
----
KIS 응답 오류(rt_cd != "0", HTTPError, Timeout)·키 누락·Decimal 파싱 실패는 그대로 raise.
view 단에서 503으로 변환.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from django.utils import timezone

from stocks.models import Stock
from stocks.services.kis_client import KISClient, KISConfig


MARKET_TO_EXCD = {"NASDAQ": "NAS", "NYSE": "NYS"}
DOMESTIC_MARKETS = {"KOSPI", "KOSDAQ"}
US_MARKETS = {"NASDAQ", "NYSE"}

WARNINGS_ALL_FALSE = {
    "is_management": False,
    "is_short_overheated": False,
    "is_trading_halted": False,
    "is_vi_active": False,
    "short_term_overheated": False,
    "investment_caution": False,
}

_KST = ZoneInfo("Asia/Seoul")
_ET = ZoneInfo("America/New_York")

_client: Optional[KISClient] = None


def get_kis_client() -> KISClient:
    """lazy singleton — .env 로드는 호출자 책임 (Django settings에서 이미 로드됨)."""
    global _client
    if _client is None:
        _client = KISClient(KISConfig.from_env())
    return _client


def _parse_kr_warnings(code: str) -> dict:
    code = (code or "").strip()
    if code == "00" or not code:
        return dict(WARNINGS_ALL_FALSE)
    w = dict(WARNINGS_ALL_FALSE)
    if code in ("51", "58"):
        w["is_management"] = True
        w["warning_label"] = "관리종목"
    elif code == "52":
        w["is_trading_halted"] = True
        w["warning_label"] = "거래정지"
    else:
        w["warning_label"] = code
    return w


def _map_kr_price(raw: dict, stock: Stock) -> dict:
    current = Decimal(raw["stck_prpr"])
    prev_close = Decimal(raw["stck_sdpr"])
    return {
        "stock_code": stock.code,
        "current": current,
        "open": Decimal(raw["stck_oprc"]),
        "high": Decimal(raw["stck_hgpr"]),
        "low": Decimal(raw["stck_lwpr"]),
        "prev_close": prev_close,
        "change": Decimal(raw["prdy_vrss"]),
        "change_rate": float(raw["prdy_ctrt"]),
        "volume": int(raw["acml_vol"]),
        "trading_value": Decimal(raw["acml_tr_pbmn"]),
        "upper_limit": Decimal(raw["stck_mxpr"]),
        "lower_limit": Decimal(raw["stck_llam"]),
        "warnings": _parse_kr_warnings(raw.get("iscd_stat_cls_code", "")),
        "fetched_at": timezone.now(),
    }


def _map_us_price(raw: dict, stock: Stock) -> dict:
    current = Decimal(raw["last"])
    prev_close = Decimal(raw["base"])
    change = current - prev_close
    change_rate = float(change / prev_close * 100) if prev_close > 0 else 0.0
    return {
        "stock_code": stock.code,
        "current": current,
        "open": Decimal(raw["open"]),
        "high": Decimal(raw["high"]),
        "low": Decimal(raw["low"]),
        "prev_close": prev_close,
        "change": change,
        "change_rate": change_rate,
        "volume": int(raw["pvol"]),
        "trading_value": Decimal(raw["pamt"]),
        "upper_limit": Decimal(raw.get("uplp", "0") or "0"),
        "lower_limit": Decimal(raw.get("dnlp", "0") or "0"),
        "warnings": dict(WARNINGS_ALL_FALSE),
        "fetched_at": timezone.now(),
    }


def fetch_price(stock: Stock) -> dict:
    client = get_kis_client()
    if stock.market in DOMESTIC_MARKETS:
        raw = client.get_current_price(stock.code)["output"]
        return _map_kr_price(raw, stock)
    if stock.market in US_MARKETS:
        excd = MARKET_TO_EXCD[stock.market]
        raw = client.get_overseas_price_detail(excd, stock.code)["output"]
        return _map_us_price(raw, stock)
    raise ValueError(f"unsupported market: {stock.market!r}")


def _is_market_open(market: str, now: Optional[datetime] = None) -> bool:
    """평일 + 시간대 판정. 공휴일은 미고려 (followup §3.4 후속).

    KR (KOSPI/KOSDAQ): KST Mon~Fri 09:00 ≤ t < 15:30
    US (NASDAQ/NYSE):  ET  Mon~Fri 09:30 ≤ t < 16:00  (DST는 zoneinfo가 처리)
    """
    if market in DOMESTIC_MARKETS:
        tz, open_hm, close_hm = _KST, (9, 0), (15, 30)
    elif market in US_MARKETS:
        tz, open_hm, close_hm = _ET, (9, 30), (16, 0)
    else:
        return False
    local = (now or datetime.now(tz=tz)).astimezone(tz)
    if local.weekday() >= 5:  # 토(5)·일(6)
        return False
    t = (local.hour, local.minute)
    return open_hm <= t < close_hm


def get_cache_ttl(stock: Stock) -> int:
    return 3 if _is_market_open(stock.market) else 60
