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

import time
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


# ----- 분봉 (chart API용) -----

_INTERVAL_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}


def _parse_kr_minute_dt(yyyymmdd: str, hhmmss: str) -> datetime:
    """KIS KR 분봉 time stamp → KST timezone-aware datetime."""
    return datetime.strptime(yyyymmdd + hhmmss, "%Y%m%d%H%M%S").replace(tzinfo=_KST)


def _map_kr_minute_1m(raw: dict) -> list[dict]:
    """KR FHKST03010200 output2 → 정규화 list (오래된 것부터)."""
    out = []
    for r in (raw.get("output2") or []):
        try:
            t = _parse_kr_minute_dt(r["stck_bsop_date"], r["stck_cntg_hour"])
            close = Decimal(r["stck_prpr"])
            out.append({
                "time": t,
                "open": Decimal(r["stck_oprc"]),
                "high": Decimal(r["stck_hgpr"]),
                "low": Decimal(r["stck_lwpr"]),
                "close": close,
                "volume": int(r.get("cntg_vol") or 0),
            })
        except (KeyError, ValueError):
            continue
    out.sort(key=lambda x: x["time"])  # KIS는 최신순으로 줌 → 오래된 순으로 뒤집기
    return out


def _map_us_minute(raw: dict) -> list[dict]:
    """US HHDFS76950200 output2 → 정규화 list (KST timezone, 오래된 것부터).
    kymd/khms (KIS가 KST 환산해서 줌) 사용.
    """
    out = []
    for r in (raw.get("output2") or []):
        try:
            t = _parse_kr_minute_dt(r["kymd"], r["khms"])
            close = Decimal(r["last"])
            out.append({
                "time": t,
                "open": Decimal(r["open"]),
                "high": Decimal(r["high"]),
                "low": Decimal(r["low"]),
                "close": close,
                "volume": int(r.get("evol") or 0),
            })
        except (KeyError, ValueError):
            continue
    out.sort(key=lambda x: x["time"])
    return out


def _aggregate(window: list[dict]) -> dict:
    return {
        "time": window[0]["time"],
        "open": window[0]["open"],
        "high": max(r["high"] for r in window),
        "low":  min(r["low"]  for r in window),
        "close": window[-1]["close"],
        "volume": sum(r["volume"] for r in window),
    }


def _resample_1m_to_n(rows_1m: list[dict], n: int) -> list[dict]:
    """1분봉을 n분 윈도우로 OHLC 합산. n=1이면 입력 그대로.

    윈도우 구분: time을 epoch-minutes 기준 n으로 나눈 몫 → 안정적 (시간 경계 가로지름 OK).
    """
    if n == 1 or not rows_1m:
        return rows_1m
    out, buf = [], []
    cur_bucket = None
    for r in rows_1m:
        epoch_min = int(r["time"].timestamp() // 60)
        bucket = epoch_min // n
        if cur_bucket is None or bucket == cur_bucket:
            buf.append(r)
            cur_bucket = bucket
        else:
            out.append(_aggregate(buf))
            buf = [r]
            cur_bucket = bucket
    if buf:
        out.append(_aggregate(buf))
    return out


# KR 분봉 페이징 윈도우 (장 09:00~15:30 = 13개 30분 슬롯)
# KIS FHKST03010200가 30행/콜이라 1일치 1m봉 채우려면 base_hour 13번 호출
_KR_MINUTE_BASE_HOURS = [
    "153000", "150000", "143000", "140000", "133000", "130000", "123000",
    "120000", "113000", "110000", "103000", "100000", "093000",
]


def _kr_minute_rows_full_day(client: KISClient, code: str,
                              sleep_sec: float = 0.3) -> list[dict]:
    """KR 분봉 1일치 페이징 — base_hour 13번 호출(30분 단위 슬라이딩).
    응답은 dedupe된 raw 1m row 리스트 (시간 순서 X — _map_kr_minute_1m이 정렬).
    """
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for base_hour in _KR_MINUTE_BASE_HOURS:
        resp = client.get_domestic_minute_price(code, base_hour=base_hour)
        for r in (resp.get("output2") or []):
            key = (r.get("stck_bsop_date"), r.get("stck_cntg_hour"))
            if not key[0] or not key[1] or key in seen:
                continue
            seen.add(key)
            rows.append(r)
        time.sleep(sleep_sec)
    return rows


def fetch_minute_candles(stock: Stock, interval: str) -> list[dict]:
    """KR/US 분봉 호출 + 정규화. 시장별 정책 분기:
       KR: 1m 13콜 페이징(09:00~15:30 1일치) → _resample_1m_to_n (KIS가 1m만 줌, 30행/콜)
       US: NMIN 직접 전달, 120행/콜로 1일치 커버 (KIS가 합산해서 줌)
    """
    if interval not in _INTERVAL_MINUTES:
        raise ValueError(f"unsupported interval: {interval!r}")
    n_minutes = _INTERVAL_MINUTES[interval]
    client = get_kis_client()

    if stock.market in DOMESTIC_MARKETS:
        rows_raw = _kr_minute_rows_full_day(client, stock.code)
        rows_1m = _map_kr_minute_1m({"output2": rows_raw})
        return _resample_1m_to_n(rows_1m, n_minutes)

    if stock.market in US_MARKETS:
        excd = MARKET_TO_EXCD[stock.market]
        raw = client.get_overseas_minute_price(excd, stock.code, nmin=str(n_minutes))
        return _map_us_minute(raw)

    raise ValueError(f"unsupported market: {stock.market!r}")


def build_today_candle(stock: Stock) -> Optional[dict]:
    """⭐ B 패턴 — 장중일 때 fetch_price 결과로 today 일봉 한 칸 합성.
    fetch_price는 3s 캐시(SCRUM-60) 살아있어 차트 폴링 시 KIS 부담 X.
    """
    if not _is_market_open(stock.market):
        return None
    p = fetch_price(stock)
    return {
        "time": p["fetched_at"],
        "open": p["open"],
        "high": p["high"],
        "low": p["low"],
        "close": p["current"],
        "volume": p["volume"],
    }
