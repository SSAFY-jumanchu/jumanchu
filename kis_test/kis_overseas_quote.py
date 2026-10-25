"""
KIS Open API - 해외주식 시세/메타 응답 탐색 (검증 스크립트)
=========================================================

목적
----
followup §2.6 미국 종목 enrichment 출처 결정용 탐색.
KIS 해외주식 API가 sector/industry/homepage_url 같은 회사 메타를 주는지,
모의(KIS_ENV=virtual) 환경에서 안정적으로 작동하는지 확인.

테스트 엔드포인트
----------------
1. HHDFS00000300 해외주식 현재가
   - Path: /uapi/overseas-price/v1/quotations/price
   - 시세 위주 (현재가, 전일대비, 거래량)
2. CTPF1702R   해외주식 기본 검색 (search-info)
   - Path: /uapi/overseas-price/v1/quotations/search-info
   - 종목 기본정보 (이름, 통화, 상장일 등 가능성)
3. HHDFS76200200 해외주식 상세 (시도)
   - Path: /uapi/overseas-price/v1/quotations/inquire-asking-price 등 후보

테스트 종목
----------
- AAPL (NAS) — NASDAQ 대형 기술주
- NVDA (NAS) — NASDAQ 대형
- JPM  (NYS) — NYSE 대형 은행
- BRK  (NYS) — NYSE (점/하이픈 ticker; KIS는 BRK 또는 BRK.A 표기 확인 필요)

거래소 코드 (EXCD)
-----------------
- NAS = NASDAQ
- NYS = NYSE
- AMS = AMEX
- HKS = 홍콩, TSE = 도쿄 등

상품유형 코드 (PRDT_TYPE_CD, 가설)
---------------------------------
- 512 = 미국 NASDAQ
- 513 = 미국 NYSE
- 529 = 미국 AMEX

사용
----
    cd kis_test
    python kis_overseas_quote.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# Windows cp949 콘솔에서 한글/유니코드(em dash 등) 출력 깨짐 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# .env는 프로젝트 루트(상위 폴더)
load_dotenv(dotenv_path="../.env")

APP_KEY = os.environ.get("KIS_APP_KEY", "")
APP_SECRET = os.environ.get("KIS_APP_SECRET", "")
KIS_ENV = os.environ.get("KIS_ENV", "vts").lower()

DOMAIN_MAP = {
    "vts": "https://openapivts.koreainvestment.com:29443",
    "virtual": "https://openapivts.koreainvestment.com:29443",
    "prod": "https://openapi.koreainvestment.com:9443",
    "real": "https://openapi.koreainvestment.com:9443",
}
BASE_URL = DOMAIN_MAP.get(KIS_ENV, DOMAIN_MAP["vts"])

# 기존 KISClient의 토큰 캐시 파일 재사용 (재발급 방지)
TOKEN_CACHE_PATH = Path.home() / ".kis_token_cache.json"


_cached_token: str | None = None


def get_access_token(force_new: bool = False) -> str:
    """캐시 토큰 재사용. force_new=True면 새로 발급."""
    global _cached_token
    if _cached_token and not force_new:
        return _cached_token

    if not force_new and TOKEN_CACHE_PATH.exists():
        try:
            data = json.loads(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
            if (
                data.get("env") == KIS_ENV
                and data.get("app_key") == APP_KEY
                and data.get("access_token")
            ):
                _cached_token = data["access_token"]
                return _cached_token
        except (json.JSONDecodeError, KeyError):
            pass

    # 신규 발급
    res = requests.post(
        f"{BASE_URL}/oauth2/tokenP",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
        }),
        timeout=10,
    )
    res.raise_for_status()
    token = res.json()["access_token"]
    # 캐시 갱신
    TOKEN_CACHE_PATH.write_text(json.dumps({
        "env": KIS_ENV,
        "app_key": APP_KEY,
        "access_token": token,
    }, ensure_ascii=False), encoding="utf-8")
    _cached_token = token
    return token


def call_api(path: str, tr_id: str, params: dict[str, Any], retry_on_token: bool = True) -> dict:
    """KIS 해외주식 GET 요청. 토큰 만료 시 자동 재발급 + 호출 간 sleep."""
    def _do(force_new_token: bool = False) -> dict:
        token = get_access_token(force_new=force_new_token)
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": tr_id,
            "custtype": "P",
        }
        try:
            res = requests.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=10)
            return {
                "status_code": res.status_code,
                "body": res.json() if res.text else {},
            }
        except Exception as e:
            return {"error": str(e)}

    result = _do(force_new_token=False)
    # 토큰 만료 (EGW00123) → 1회 재발급 후 재시도
    msg_cd = (result.get("body") or {}).get("msg_cd")
    if retry_on_token and msg_cd == "EGW00123":
        time.sleep(0.5)
        result = _do(force_new_token=True)
    # 호출 간 sleep (초당 한도 회피, 해외는 한국보다 빡빡할 수 있음)
    time.sleep(0.5)
    return result


def dump_response(label: str, resp: dict, max_chars: int = 2000) -> None:
    """응답 보기 좋게 출력. 너무 길면 자름."""
    print(f"\n--- {label} ---")
    if "error" in resp:
        print(f"  ERROR: {resp['error']}")
        return
    status = resp.get("status_code")
    body = resp.get("body", {})
    print(f"  HTTP: {status}")
    rt_cd = body.get("rt_cd")
    msg_cd = body.get("msg_cd")
    msg = body.get("msg1") or body.get("msg")
    print(f"  rt_cd={rt_cd} msg_cd={msg_cd} msg={msg!r}")

    # output / output1 / output2 등 모든 output 키를 출력
    output_keys = [k for k in body.keys() if k.startswith("output")]
    if not output_keys:
        # 응답 전체 dump
        text = json.dumps(body, indent=2, ensure_ascii=False)
        print(f"  body (raw):\n{text[:max_chars]}{'...(truncated)' if len(text) > max_chars else ''}")
        return

    for ok in output_keys:
        out = body[ok]
        print(f"  [{ok}] type={type(out).__name__}")
        if isinstance(out, list):
            print(f"    length={len(out)}")
            if out:
                # 첫 element만 보여줌
                text = json.dumps(out[0], indent=4, ensure_ascii=False)
                print(f"    [0]:\n{text[:max_chars]}")
        elif isinstance(out, dict):
            text = json.dumps(out, indent=4, ensure_ascii=False)
            print(f"    {text[:max_chars]}{'...(truncated)' if len(text) > max_chars else ''}")
        else:
            print(f"    {out!r}")


# ---------------------------------------------------------------------------
# 엔드포인트 호출 함수들
# ---------------------------------------------------------------------------

def test_current_price(excd: str, symbol: str) -> dict:
    """HHDFS00000300 해외주식 현재가."""
    return call_api(
        "/uapi/overseas-price/v1/quotations/price",
        "HHDFS00000300",
        {"AUTH": "", "EXCD": excd, "SYMB": symbol},
    )


def test_search_info(prdt_type: str, pdno: str) -> dict:
    """CTPF1702R 해외주식 기본정보 (search-info)."""
    return call_api(
        "/uapi/overseas-price/v1/quotations/search-info",
        "CTPF1702R",
        {"PRDT_TYPE_CD": prdt_type, "PDNO": pdno},
    )


def test_inquire_price_detail(excd: str, symbol: str) -> dict:
    """HHDFS76200200 해외주식 상세 시세 (있다면)."""
    return call_api(
        "/uapi/overseas-price/v1/quotations/price-detail",
        "HHDFS76200200",
        {"AUTH": "", "EXCD": excd, "SYMB": symbol},
    )


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not APP_KEY or not APP_SECRET:
        print("ERROR: .env의 KIS_APP_KEY / KIS_APP_SECRET 없음")
        sys.exit(1)

    print(f"[KIS 해외 탐색] env={KIS_ENV} base={BASE_URL}")
    print(f"  app_key: {APP_KEY[:8]}...")

    # 테스트 종목 매트릭스
    # (ticker, excd, prdt_type_cd, 메모)
    targets = [
        ("AAPL",  "NAS", "512", "Apple — NASDAQ"),
        ("NVDA",  "NAS", "512", "NVIDIA — NASDAQ"),
        ("JPM",   "NYS", "513", "JPMorgan — NYSE"),
        ("BRK.B", "NYS", "513", "Berkshire B — 점 ticker"),
        ("BRK-B", "NYS", "513", "Berkshire B — 하이픈 표기"),
        ("BRK",   "NYS", "513", "Berkshire — 짧은 표기"),
    ]

    for ticker, excd, prdt, note in targets:
        print(f"\n\n========== {ticker} (excd={excd}, prdt={prdt}) — {note} ==========")

        print(f"\n[1] HHDFS00000300 현재가 (price)")
        r1 = test_current_price(excd, ticker)
        dump_response(f"{ticker} current-price", r1)

        print(f"\n[2] CTPF1702R 기본정보 (search-info)")
        r2 = test_search_info(prdt, ticker)
        dump_response(f"{ticker} search-info", r2)

        print(f"\n[3] HHDFS76200200 상세 (price-detail, 추측)")
        r3 = test_inquire_price_detail(excd, ticker)
        dump_response(f"{ticker} price-detail", r3)

    print("\n[KIS 해외 탐색] 완료")
