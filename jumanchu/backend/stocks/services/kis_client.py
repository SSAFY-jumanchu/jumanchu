"""
KIS Open API 클라이언트 (backend 운영용).

kis_test/kis_domestic_quote.py 와 본질적으로 같지만, backend에서
import 하기 좋게 패키지 안에 둠. `.env` 값 `KIS_ENV=virtual`도
받아들이도록 DOMAIN_MAP에 alias 추가.

지원 호출
---------
- get_current_price(stock_code): 종목 현재가
  반환 output 주요 필드:
    stck_prpr        현재가
    prdy_vrss        전일대비
    prdy_ctrt        전일대비율
    bstp_kor_isnm    업종 한글명 ("전기·전자") -- Stock.sector 출처
    hts_avls         시가총액(억)              -- Stock.market_cap 출처
    per, pbr, eps    가치 평가 지표            -- StockIndicator 출처

토큰
----
- OAuth2 client_credentials. 24시간 유효.
- ~/.kis_token_cache.json 에 캐싱 (env + app_key 키로 구분).

호출 제한
---------
- TR_ID 별 분당 호출 수 제한 있음. 반복 호출 시 sleep 권장.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import requests


DOMAIN_MAP = {
    "vts": "https://openapivts.koreainvestment.com:29443",
    "virtual": "https://openapivts.koreainvestment.com:29443",  # .env KIS_ENV=virtual alias
    "prod": "https://openapi.koreainvestment.com:9443",
    "real": "https://openapi.koreainvestment.com:9443",         # .env KIS_ENV=real alias
}

TOKEN_CACHE_PATH = Path.home() / ".kis_token_cache.json"


@dataclass
class KISConfig:
    app_key: str = ""
    app_secret: str = ""
    env: str = "vts"

    @property
    def base_url(self) -> str:
        if self.env not in DOMAIN_MAP:
            raise ValueError(f"KIS_ENV={self.env!r} 지원 안 함. 허용값: {list(DOMAIN_MAP)}")
        return DOMAIN_MAP[self.env]

    @classmethod
    def from_env(cls) -> "KISConfig":
        return cls(
            app_key=os.environ["KIS_APP_KEY"],
            app_secret=os.environ["KIS_APP_SECRET"],
            env=os.environ.get("KIS_ENV", "vts"),
        )


class KISClient:
    """국내주식 시세 조회 (현재가 중심)."""

    def __init__(self, config: KISConfig):
        self.cfg = config
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._load_cached_token()

    # ----- 토큰 -----
    def _load_cached_token(self) -> None:
        if not TOKEN_CACHE_PATH.exists():
            return
        try:
            data = json.loads(TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
            if data.get("env") != self.cfg.env or data.get("app_key") != self.cfg.app_key:
                return
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
        url = f"{self.cfg.base_url}/oauth2/tokenP"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.cfg.app_key,
            "appsecret": self.cfg.app_secret,
        }
        res = requests.post(url, headers={"Content-Type": "application/json"},
                            data=json.dumps(body), timeout=10)
        res.raise_for_status()
        payload = res.json()
        self._access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 86400))
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        self._save_token_cache()
        return self._access_token

    @property
    def access_token(self) -> str:
        if (self._access_token and self._token_expires_at
                and self._token_expires_at > datetime.now() + timedelta(minutes=5)):
            return self._access_token
        return self._issue_access_token()

    # ----- 공통 요청 -----
    def _headers(self, tr_id: str) -> dict[str, str]:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.cfg.app_key,
            "appsecret": self.cfg.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def _get(self, path: str, tr_id: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.cfg.base_url}{path}"
        res = requests.get(url, headers=self._headers(tr_id), params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        if data.get("rt_cd") != "0":
            raise RuntimeError(f"[{tr_id}] {data.get('msg_cd')} {data.get('msg1')}")
        return data

    # ----- 시세 -----
    def get_current_price(self, stock_code: str) -> dict[str, Any]:
        """국내주식 현재가 (FHKST01010100). 응답 output 활용 필드:
        bstp_kor_isnm, hts_avls, per, pbr, eps, stck_prpr, prdy_vrss, prdy_ctrt
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
            },
        )

    def get_overseas_price_detail(self, excd: str, symbol: str) -> dict[str, Any]:
        """해외주식 현재가 상세 (HHDFS76200200). 모의 환경 OK.

        excd: NAS(나스닥) / NYS(뉴욕) / AMS(아멕스) 등
        symbol: ticker (예: AAPL)

        응답 output 활용 필드:
          e_icod  업종 한글명 (예: "컴퓨터전자장비/기기") -> Stock.sector
          tomv    시가총액 (USD)                          -> Stock.market_cap
          perx    PER                                     -> StockIndicator.per
          pbrx    PBR                                     -> StockIndicator.pbr
          epsx    EPS                                     -> StockIndicator.eps
          h52p    52주 최고가                              -> StockIndicator.high_52w
          l52p    52주 최저가                              -> StockIndicator.low_52w
        """
        return self._get(
            path="/uapi/overseas-price/v1/quotations/price-detail",
            tr_id="HHDFS76200200",
            params={"AUTH": "", "EXCD": excd, "SYMB": symbol},
        )
