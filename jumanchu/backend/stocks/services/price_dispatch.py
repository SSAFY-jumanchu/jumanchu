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
from decimal import Decimal, InvalidOperation
from typing import Optional
from zoneinfo import ZoneInfo

import requests
from django.core.cache import cache
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
    """현재가 dict. KIS 결과를 stock:price:raw:* 키로 캐시(장중 3s/장외 60s).

    랭킹·보유·관심·차트·매매가 모두 이 캐시를 공유 → KIS 호출 dedup + 화면 간 가격 일관성.
    StockPriceView는 별도 serialized 캐시(stock:price:*)를 유지 — FE 통합 후 중복 정리 예정.
    """
    key = f"stock:price:raw:{stock.market}:{stock.code}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    client = get_kis_client()
    if stock.market in DOMESTIC_MARKETS:
        raw = client.get_current_price(stock.code)["output"]
        result = _map_kr_price(raw, stock)
    elif stock.market in US_MARKETS:
        excd = MARKET_TO_EXCD[stock.market]
        raw = client.get_overseas_price_detail(excd, stock.code)["output"]
        result = _map_us_price(raw, stock)
    else:
        raise ValueError(f"unsupported market: {stock.market!r}")
    cache.set(key, result, timeout=get_cache_ttl(stock))
    return result


# 시장 운영시간 (공휴일 미고려 — followup §3.4 후속). DST는 zoneinfo가 처리.
_MARKET_HOURS = {
    "kr": {"tz": _KST, "open": (9, 0), "close": (15, 30), "markets": DOMESTIC_MARKETS},   # KOSPI/KOSDAQ
    "us": {"tz": _ET, "open": (9, 30), "close": (16, 0), "markets": US_MARKETS},          # NASDAQ/NYSE
}


def _region_of(market: str) -> Optional[str]:
    return "kr" if market in DOMESTIC_MARKETS else "us" if market in US_MARKETS else None


def _is_market_open(market: str, now: Optional[datetime] = None) -> bool:
    """평일 + 시간대 판정. KR 09:00~15:30 KST / US 09:30~16:00 ET. 공휴일 미고려."""
    region = _region_of(market)
    if region is None:
        return False
    h = _MARKET_HOURS[region]
    local = (now or datetime.now(tz=h["tz"])).astimezone(h["tz"])
    if local.weekday() >= 5:  # 토(5)·일(6)
        return False
    return h["open"] <= (local.hour, local.minute) < h["close"]


def market_status(now: Optional[datetime] = None) -> dict:
    """KR·US 시장 개장/마감 상태 + 운영시간. KIS 호출 없는 순수 시간 로직.
    반환: {kr:{is_open,open_time,close_time,timezone}, us:{...}}."""
    out = {}
    for region, h in _MARKET_HOURS.items():
        rep = next(iter(h["markets"]))  # 지역 대표 시장으로 개장 판정(같은 지역은 동일 시간)
        out[region] = {
            "is_open": _is_market_open(rep, now),
            "open_time": f"{h['open'][0]:02d}:{h['open'][1]:02d}",
            "close_time": f"{h['close'][0]:02d}:{h['close'][1]:02d}",
            "timezone": h["tz"].key,
        }
    return out


def get_cache_ttl(stock: Stock) -> int:
    return 3 if _is_market_open(stock.market) else 60


# ----- 호가창 (orderbook API용) -----


def _orderbook_levels(raw: dict, price_fmt: str, qty_fmt: str) -> list[dict]:
    """raw[price_fmt.format(i)]/[qty_fmt.format(i)] (i=1..10) → [{price, quantity}].

    price>0인 레벨만 1→10(최우선→하위) 순서로. 빈 레벨(0/없음)은 제외 — 10호가
    미만 종목·장전/장외엔 상위 일부만 채워지거나 전부 0이라 빈 배열이 될 수 있다.
    """
    levels: list[dict] = []
    for i in range(1, 11):
        p = raw.get(price_fmt.format(i))
        try:
            price = Decimal(str(p)) if p not in (None, "") else Decimal("0")
        except InvalidOperation:
            continue
        if price <= 0:
            continue
        q = raw.get(qty_fmt.format(i))
        try:
            quantity = int(q) if q not in (None, "") else 0
        except (TypeError, ValueError):
            quantity = 0
        levels.append({"price": price, "quantity": quantity})
    return levels


def _map_kr_orderbook(o1: dict, stock: Stock) -> dict:
    return {
        "stock_code": stock.code,
        "asks": _orderbook_levels(o1, "askp{}", "askp_rsqn{}"),
        "bids": _orderbook_levels(o1, "bidp{}", "bidp_rsqn{}"),
        "total_ask_quantity": int(o1.get("total_askp_rsqn") or 0),
        "total_bid_quantity": int(o1.get("total_bidp_rsqn") or 0),
        "is_market_open": _is_market_open(stock.market),  # 빈 호가가 '장 마감' 때문인지 FE가 구분
        "fetched_at": timezone.now(),
    }


def _map_us_orderbook(o2: dict, stock: Stock) -> dict:
    asks = _orderbook_levels(o2, "pask{}", "vask{}")
    bids = _orderbook_levels(o2, "pbid{}", "vbid{}")
    return {
        "stock_code": stock.code,
        "asks": asks,
        "bids": bids,
        # 해외는 총잔량 필드 미제공 → 10호가 잔량 합산
        "total_ask_quantity": sum(a["quantity"] for a in asks),
        "total_bid_quantity": sum(b["quantity"] for b in bids),
        "is_market_open": _is_market_open(stock.market),  # 빈 호가가 '장 마감' 때문인지 FE가 구분
        "fetched_at": timezone.now(),
    }


def fetch_orderbook(stock: Stock) -> dict:
    """KR/US 분기 → OrderBookSerializer 입력 dict (매도/매수 10호가 + 총잔량)."""
    client = get_kis_client()
    if stock.market in DOMESTIC_MARKETS:
        raw = client.get_domestic_orderbook(stock.code)["output1"]
        return _map_kr_orderbook(raw, stock)
    if stock.market in US_MARKETS:
        excd = MARKET_TO_EXCD[stock.market]
        raw = client.get_overseas_orderbook(excd, stock.code)["output2"]
        return _map_us_orderbook(raw, stock)
    raise ValueError(f"unsupported market: {stock.market!r}")


def get_orderbook_ttl(stock: Stock) -> int:
    """호가 캐시 TTL: 장중 1s / 장외 30s (현재가 3s/60s보다 짧게 — 호가는 체결마다 변동)."""
    return 1 if _is_market_open(stock.market) else 30


# ----- 체결강도(거래비율, volume power) — 인기 랭킹 컬럼용 -----

VOLPOWER_TTL = 60  # 체결강도 캐시 TTL(초). 워밍 배치 주기와 맞춤.


def volpower_key(market: str, code: str) -> str:
    return f"stock:volpower:{market}:{code}"


def fetch_volume_power(market: str, code: str) -> Optional[dict]:
    """체결강도(매수/매도 체결 비율). 실패·데이터 없음이면 None(랭킹 안 죽임).

    KR: 체결 API(FHKST01010300) 최근 틱 tday_rltv(=누적 매수체결/매도체결 ×100).
    US: 호가 API(HHDFS76200100) output1 bvol/avol(매수/매도 체결량) → 직접 계산.
    반환: {volume_power(체결강도), buy_ratio(매수%), sell_ratio(매도%)}.
    """
    client = get_kis_client()
    try:
        if market in DOMESTIC_MARKETS:
            rows = client.get_domestic_ccnl(code).get("output") or []
            if not rows:
                return None
            raw = rows[0].get("tday_rltv")
            r = float(raw) if raw not in (None, "") else None
            if r is None or r < 0:
                return None
            buy = r / (r + 100) * 100  # 체결강도 r=매수/매도×100 → 매수비율=r/(r+100)
            return {"volume_power": round(r, 2),
                    "buy_ratio": round(buy, 1), "sell_ratio": round(100 - buy, 1)}
        if market in US_MARKETS:
            excd = MARKET_TO_EXCD[market]
            o1 = client.get_overseas_orderbook(excd, code).get("output1", {})
            bvol = float(o1.get("bvol") or 0)
            avol = float(o1.get("avol") or 0)
            if bvol + avol <= 0:
                return None  # 장외/데이터 없음
            buy = bvol / (bvol + avol) * 100
            vp = bvol / avol * 100 if avol > 0 else 999.99
            return {"volume_power": round(vp, 2),
                    "buy_ratio": round(buy, 1), "sell_ratio": round(100 - buy, 1)}
    except (requests.HTTPError, requests.Timeout, RuntimeError, KeyError,
            ValueError, InvalidOperation):
        return None
    return None


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
