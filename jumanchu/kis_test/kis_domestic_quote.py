"""
KIS(한국투자증권) Open API - 국내주식 시세 조회 클라이언트 (모의투자 환경)
=======================================================================

기능 요약
----------
1) OAuth2 접근 토큰 발급 (토큰 캐싱 포함)
2) 주식 현재가 조회      - TR_ID: FHKST01010100
3) 주식 현재가 호가/예상체결 - TR_ID: FHKST01010200
4) 주식 기간별 시세(일/주/월/년 봉) - TR_ID: FHKST03010100
5) 주식 당일 분봉 조회   - TR_ID: FHKST03010200

사용 전 준비
------------
- 한국투자증권 Open API 사이트에서 모의투자용 App Key / App Secret 발급
  (https://apiportal.koreainvestment.com/)
- 모의투자 계좌 개설(KIS 모의투자 시스템) - 시세 조회만 할 경우 계좌번호는 필수 아님
- requirements: requests, python-dotenv (선택)

환경 변수(.env 권장)
--------------------
KIS_APP_KEY=발급받은_앱키
KIS_APP_SECRET=발급받은_시크릿
KIS_ENV=vts            # vts = 모의투자, prod = 실전투자

주의
----
- 모의투자 도메인: https://openapivts.koreainvestment.com:29443
- 실전투자 도메인: https://openapi.koreainvestment.com:9443
- 국내주식 시세 조회용 TR_ID는 모의/실전 동일하나, 일부 API는 모의에서 미지원.
- 토큰은 보통 24시간 유효하므로 파일로 캐싱하여 재사용합니다.
- 호출 횟수 제한이 있으므로 반복 조회 시 time.sleep을 권장합니다.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import requests

# ---------------------------------------------------------------------------
# 1. 환경/도메인 설정
# ---------------------------------------------------------------------------

DOMAIN_MAP = {
    "vts": "https://openapivts.koreainvestment.com:29443",   # 모의투자
    "prod": "https://openapi.koreainvestment.com:9443",      # 실전투자
}

TOKEN_CACHE_PATH = Path.home() / ".kis_token_cache.json"


@dataclass
class KISConfig:
    app_key: str = ""
    app_secret: str = ""
    env: str = "vts"  # "vts" or "prod"

    @property
    def base_url(self) -> str:
        return DOMAIN_MAP[self.env]


# ---------------------------------------------------------------------------
# 2. 클라이언트 본체
# ---------------------------------------------------------------------------

class KISDomesticQuote:
    """국내주식 시세 조회 전용 KIS API 래퍼 (모의투자 기본)."""

    def __init__(self, config: KISConfig):
        self.cfg = config
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._load_cached_token()

    # ------------------------------------------------------------------
    # 2-1. 토큰 발급 및 캐싱
    # ------------------------------------------------------------------
    def _load_cached_token(self) -> None:
        """디스크에 캐싱된 토큰이 유효하면 메모리에 로드."""
        if not TOKEN_CACHE_PATH.exists():
            return
        try:
            data = json.loads(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
            if data.get("env") != self.cfg.env or data.get("app_key") != self.cfg.app_key:
                return  # 다른 환경/계정의 캐시는 무시
            expires_at = datetime.fromisoformat(data["expires_at"])
            if expires_at > datetime.now() + timedelta(minutes=5):
                self._access_token = data["access_token"]
                self._token_expires_at = expires_at
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    def _save_token_cache(self) -> None:
        if not (self._access_token and self._token_expires_at):
            return
        TOKEN_CACHE_PATH.write_text(
            json.dumps(
                {
                    "env": self.cfg.env,
                    "app_key": self.cfg.app_key,
                    "access_token": self._access_token,
                    "expires_at": self._token_expires_at.isoformat(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _issue_access_token(self) -> str:
        """OAuth2 접근 토큰 신규 발급."""
        url = f"{self.cfg.base_url}/oauth2/tokenP"
        headers = {"Content-Type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.cfg.app_key,
            "appsecret": self.cfg.app_secret,
        }
        res = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
        res.raise_for_status()
        payload = res.json()
        self._access_token = payload["access_token"]
        # 한국투자증권은 expires_in(초)을 내려줍니다. 보수적으로 5분 여유.
        expires_in = int(payload.get("expires_in", 86400))
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        self._save_token_cache()
        return self._access_token

    @property
    def access_token(self) -> str:
        if (
            self._access_token
            and self._token_expires_at
            and self._token_expires_at > datetime.now() + timedelta(minutes=5)
        ):
            return self._access_token
        return self._issue_access_token()

    # ------------------------------------------------------------------
    # 2-2. 공통 헤더/요청 래퍼
    # ------------------------------------------------------------------
    def _headers(self, tr_id: str) -> dict[str, str]:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.cfg.app_key,
            "appsecret": self.cfg.app_secret,
            "tr_id": tr_id,
            "custtype": "P",  # P: 개인, B: 법인
        }

    def _get(self, path: str, tr_id: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.cfg.base_url}{path}"
        res = requests.get(url, headers=self._headers(tr_id), params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("rt_cd") != "0":
            raise RuntimeError(f"[{tr_id}] {data.get('msg_cd')} {data.get('msg1')}")
        return data

    # ------------------------------------------------------------------
    # 3. 시세 조회 API
    # ------------------------------------------------------------------
    def get_current_price(self, stock_code: str) -> dict[str, Any]:
        """
        주식 현재가 조회 (FHKST01010100)
        - stock_code: 6자리 종목코드 (예: '005930' 삼성전자)
        반환 output 주요 필드:
            stck_prpr     현재가
            prdy_vrss     전일대비
            prdy_ctrt     전일대비율
            stck_oprc     시가, stck_hgpr 고가, stck_lwpr 저가
            acml_vol      누적 거래량
            acml_tr_pbmn  누적 거래대금
            hts_avls      시가총액(억)
            per, pbr      재무 지표
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",  # J: KRX, NX: NXT, UN: 통합
                "FID_INPUT_ISCD": stock_code,
            },
        )

    def get_order_book(self, stock_code: str) -> dict[str, Any]:
        """
        주식 현재가 호가/예상체결 조회 (FHKST01010200)
        - 매도/매수 10단계 호가 + 잔량 + 예상체결가 제공
        반환 output1: 호가, output2: 예상체결
        주요 필드:
            askp1 ~ askp10    매도호가 1~10
            bidp1 ~ bidp10    매수호가 1~10
            askp_rsqn1 ~ 10   매도호가 잔량
            bidp_rsqn1 ~ 10   매수호가 잔량
            total_askp_rsqn   총 매도잔량
            total_bidp_rsqn   총 매수잔량
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
            },
        )

    def get_daily_chart(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        period: str = "D",
        adjusted: bool = True,
    ) -> dict[str, Any]:
        """
        주식 기간별 시세 (일/주/월/년 봉) (FHKST03010100)
        - start_date, end_date: YYYYMMDD
        - period: D(일), W(주), M(월), Y(년)
        - adjusted: 수정주가 반영 여부
        - 최대 100건씩 반환되므로 장기간은 반복 호출 필요

        반환 output2 리스트의 각 원소:
            stck_bsop_date 영업일자
            stck_oprc/clpr/hgpr/lwpr 시가/종가/고가/저가
            acml_vol       거래량
            acml_tr_pbmn   거래대금
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": "0" if adjusted else "1",  # 0: 수정주가, 1: 원주가
            },
        )

    def get_minute_chart(
        self,
        stock_code: str,
        end_time_hhmmss: str = "153000",
        include_past_data: bool = True,
    ) -> dict[str, Any]:
        """
        주식 당일 분봉 조회 (FHKST03010200)
        - end_time_hhmmss: 조회 종료 시각 HHMMSS (예: '153000' = 15:30:00)
        - 한 번에 최대 30건 반환. 과거로 더 가져오려면 가장 오래된 시간을
          end_time_hhmmss로 다시 호출하여 페이지네이션.

        반환 output2 리스트의 각 원소:
            stck_bsop_date 영업일자
            stck_cntg_hour 체결시각 HHMMSS
            stck_prpr      현재가(분봉 종가)
            stck_oprc/hgpr/lwpr 시/고/저가
            cntg_vol       체결거래량
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            tr_id="FHKST03010200",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
                "FID_INPUT_HOUR_1": end_time_hhmmss,
                "FID_PW_DATA_INCU_YN": "Y" if include_past_data else "N",
            },
        )


# ---------------------------------------------------------------------------
# 4. 사용 예시 (직접 실행 시 동작)
# ---------------------------------------------------------------------------

def _demo() -> None:
    """사용 예시: 삼성전자(005930) 모의투자 환경에서 시세 조회."""
    # .env 사용 시:
    # from dotenv import load_dotenv; load_dotenv()
    cfg = KISConfig(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        env=os.environ.get("KIS_ENV", "vts"),  # 기본 모의투자
    )
    client = KISDomesticQuote(cfg)
    stock_code = "005930"  # 삼성전자

    # 1) 현재가
    price = client.get_current_price(stock_code)["output"]
    print(f"[현재가] {stock_code}: {price['stck_prpr']}원 "
          f"(전일대비 {price['prdy_vrss']}, {price['prdy_ctrt']}%)")

    time.sleep(0.3)

    # 2) 호가
    book = client.get_order_book(stock_code)
    ob = book["output1"]
    print(f"[호가] 1차 매도 {ob['askp1']}({ob['askp_rsqn1']}) / "
          f"매수 {ob['bidp1']}({ob['bidp_rsqn1']})")

    time.sleep(0.3)

    # 3) 일봉 (최근 30영업일)
    today = datetime.now().strftime("%Y%m%d")
    a_month_ago = (datetime.now() - timedelta(days=45)).strftime("%Y%m%d")
    daily = client.get_daily_chart(stock_code, a_month_ago, today, period="D")
    print(f"[일봉] {len(daily['output2'])}건 수신, 가장 최근일 종가 = "
          f"{daily['output2'][0]['stck_clpr']}")

    time.sleep(0.3)

    # 4) 분봉 (오늘 15:30 기준 과거 30봉)
    minute = client.get_minute_chart(stock_code, end_time_hhmmss="153000")
    print(f"[분봉] {len(minute['output2'])}건 수신, "
          f"마지막 봉 {minute['output2'][0]['stck_cntg_hour']} "
          f"종가={minute['output2'][0]['stck_prpr']}")


if __name__ == "__main__":
    _demo()