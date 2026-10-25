"""
당일 1분봉 풀 페이지네이션 로컬 확인 스크립트.

사용:
    python check_minute_chart.py [종목코드]

기본 종목: 005930 (삼성전자)
"""
from __future__ import annotations

import sys
import time
from datetime import datetime

import requests

from kis_domestic_quote import KISConfig, KISDomesticQuote

# Windows PowerShell에서도 한글이 안 깨지도록.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _fetch_with_retry(
    client: KISDomesticQuote,
    stock_code: str,
    end_time: str,
    max_retries: int = 3,
) -> dict:
    """5xx 발생 시 지수 백오프로 재시도."""
    for attempt in range(max_retries):
        try:
            return client.get_minute_chart(stock_code, end_time_hhmmss=end_time)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status < 500 or attempt == max_retries - 1:
                raise
            backoff = 1.0 * (2 ** attempt)
            print(f"  [{end_time}] HTTP {status} — {backoff:.1f}s 후 재시도 ({attempt + 1}/{max_retries})")
            time.sleep(backoff)
    raise RuntimeError("unreachable")


def get_today_1min_full(
    client: KISDomesticQuote,
    stock_code: str,
    sleep_sec: float = 0.5,
) -> list[dict]:
    """당일 09:00~15:30 1분봉을 페이지네이션으로 전부 받아온다."""
    bars: dict[str, dict] = {}
    end_time = "153000"
    page = 0
    base_date: str | None = None  # 첫 응답의 영업일자에 고정
    while True:
        page += 1
        res = _fetch_with_retry(client, stock_code, end_time)
        batch = res.get("output2", []) or []
        if not batch:
            break
        if base_date is None:
            base_date = batch[0].get("stck_bsop_date")
        # 다른 영업일자 봉은 받지 않음 (09:00 이전 요청 시 KIS가 전일 봉을 돌려주는 케이스 차단)
        same_day = [b for b in batch if b.get("stck_bsop_date") == base_date]
        prev_count = len(bars)
        for b in same_day:
            bars[b["stck_cntg_hour"]] = b
        added = len(bars) - prev_count
        oldest = (same_day[-1]["stck_cntg_hour"]
                  if same_day else batch[-1]["stck_cntg_hour"])
        print(f"  page {page}: end={end_time} → {len(batch)}봉(당일 {len(same_day)}) 수신 (~{oldest}), 누적 {len(bars)}봉 (+{added})")
        # 종료 조건: 진전이 없거나 9시 이전으로 내려갔으면 그만.
        if added == 0 or oldest <= "090000" or oldest >= end_time:
            break
        end_time = oldest
        time.sleep(sleep_sec)
    return [bars[k] for k in sorted(bars)]


def main() -> None:
    code = sys.argv[1] if len(sys.argv) > 1 else "005930"
    client = KISDomesticQuote(KISConfig())

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {code} 당일 1분봉 수집 시작...")
    bars = get_today_1min_full(client, code)
    print(f"총 {len(bars)}봉 수집 완료\n")

    if not bars:
        print("수신된 봉이 없습니다. (장 시작 전 / 휴장 / 잘못된 종목코드 가능)")
        return

    print(f"{'시각':>6} {'시가':>9} {'고가':>9} {'저가':>9} {'종가':>9} {'거래량':>12}")
    print("-" * 60)
    for b in bars:
        t = b["stck_cntg_hour"]
        hhmm = f"{t[:2]}:{t[2:4]}"
        print(
            f"{hhmm:>6} "
            f"{b['stck_oprc']:>9} "
            f"{b['stck_hgpr']:>9} "
            f"{b['stck_lwpr']:>9} "
            f"{b['stck_prpr']:>9} "
            f"{b['cntg_vol']:>12}"
        )

    first, last = bars[0], bars[-1]
    print("-" * 60)
    print(
        f"기준일자 {first['stck_bsop_date']} | "
        f"{first['stck_cntg_hour'][:4]} ~ {last['stck_cntg_hour'][:4]} | "
        f"시가 {first['stck_oprc']} → 종가 {last['stck_prpr']}"
    )


if __name__ == "__main__":
    main()
