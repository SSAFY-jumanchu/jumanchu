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
    env: str = "prod"

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
            env=os.environ.get("KIS_ENV", "prod"),
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

    def get_domestic_orderbook(self, stock_code: str) -> dict[str, Any]:
        """국내주식 호가/예상체결 (FHKST01010200).

        output1 활용 필드:
          askp1~10 / bidp1~10            매도/매수 호가 1~10단계
          askp_rsqn1~10 / bidp_rsqn1~10  각 호가 잔량
          total_askp_rsqn / total_bidp_rsqn  총 매도/매수 잔량
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            tr_id="FHKST01010200",
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

    def get_overseas_orderbook(self, excd: str, symbol: str) -> dict[str, Any]:
        """해외주식 현재가 10호가 (HHDFS76200100). 실서버 + 해외 실시간 시세 구독 필요.

        excd: NAS/NYS, symbol: ticker (예: AAPL)
        output2 활용 필드:
          pask1~10 / pbid1~10   매도/매수 호가 1~10단계
          vask1~10 / vbid1~10   각 호가 잔량
        (국내와 달리 총잔량 필드는 미제공 → 호출자가 vask/vbid 합산.)
        """
        return self._get(
            path="/uapi/overseas-price/v1/quotations/inquire-asking-price",
            tr_id="HHDFS76200100",
            params={"AUTH": "", "EXCD": excd, "SYMB": symbol},
        )

    def get_overseas_daily_price(self, excd: str, symbol: str, bymd: str,
                                 gubn: str = "0", modp: str = "0") -> dict[str, Any]:
        """해외주식 기간별시세 (HHDFS76240000). 모의/실전 OK. 100행/호출.

        excd: NAS/NYS, symbol: ticker
        gubn: 0=일 / 1=주 / 2=월
        bymd: 조회 기준일자(YYYYMMDD) — 이 날짜부터 과거로 100행
        modp: 0=원주가 / 1=수정주가

        응답 output2(일자별 배열) 활용 필드:
          xymd 일자, open/high/low 시·고·저, clos 종가, tvol 거래량
        """
        return self._get(
            path="/uapi/overseas-price/v1/quotations/dailyprice",
            tr_id="HHDFS76240000",
            params={"AUTH": "", "EXCD": excd, "SYMB": symbol,
                    "GUBN": gubn, "BYMD": bymd, "MODP": modp},
        )

    def get_domestic_daily_price(
        self, stock_code: str, start_yyyymmdd: str, end_yyyymmdd: str,
    ) -> dict[str, Any]:
        """국내주식 기간별 일봉 (FHKST03010100). 모의 환경 OK. 한 번에 ~100행.

        output2 각 행 활용 필드:
          stck_bsop_date  영업일자 (YYYYMMDD)
          stck_clpr       종가
          stck_oprc       시가
          stck_hgpr       고가
          stck_lwpr       저가
          acml_vol        누적 거래량
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            tr_id="FHKST03010100",
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
                "FID_INPUT_DATE_1": start_yyyymmdd,
                "FID_INPUT_DATE_2": end_yyyymmdd,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            },
        )

    def get_domestic_minute_price(
        self, stock_code: str, base_hour: str = "153000",
        past_data_yn: str = "Y",
    ) -> dict[str, Any]:
        """국내주식 당일 분봉 (FHKST03010200). 1분봉만 반환, 한 번에 30행.

        base_hour=HHMMSS — 이 시각부터 과거로 30분치.
        5m/15m/1h는 호출자(price_dispatch)에서 _resample.

        output2 각 행:
          stck_bsop_date  영업일자, stck_cntg_hour  체결시각(HHMMSS)
          stck_oprc/stck_hgpr/stck_lwpr/stck_prpr  시·고·저·종가
          cntg_vol        체결량
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            tr_id="FHKST03010200",
            params={
                "FID_ETC_CLS_CODE": "",
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_code,
                "FID_INPUT_HOUR_1": base_hour,
                "FID_PW_DATA_INCU_YN": past_data_yn,
            },
        )

    def get_overseas_minute_price(
        self, excd: str, symbol: str, nmin: str = "1",
        nrec: str = "120", next_token: str = "", keyb: str = "",
        pinc: str = "1", fill: str = "",
    ) -> dict[str, Any]:
        """해외주식 분봉 (HHDFS76950200). NMIN으로 인터벌 직접 지정.

        한 번에 120행. KIS가 OHLC 합산해서 줌 → 클라이언트 재집계 불필요.
        nmin ∈ {1, 5, 15, 60} (15/60은 작업 시 추가 확인 권장).

        output2 각 행:
          xymd/xhms  현지 일자/시각(YYYYMMDD/HHMMSS)
          kymd/khms  한국시간 환산
          open/high/low/last  시·고·저·종가, evol  거래량, eamt  거래대금
        """
        return self._get(
            path="/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice",
            tr_id="HHDFS76950200",
            params={
                "AUTH": "", "EXCD": excd, "SYMB": symbol,
                "NMIN": nmin, "PINC": pinc, "NEXT": next_token,
                "NREC": nrec, "FILL": fill, "KEYB": keyb,
            },
        )

    # ----- 지수 (시장 요약용) -----
    def get_domestic_index(self, iscd: str) -> dict[str, Any]:
        """국내 시장지수 현재가 (FHPUP02100000). iscd: 0001(코스피) / 1001(코스닥).

        응답 output 활용 필드:
          bstp_nmix_prpr        현재지수
          bstp_nmix_prdy_vrss   전일대비 (부호 포함)
          bstp_nmix_prdy_ctrt   전일대비율(%)
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/inquire-index-price",
            tr_id="FHPUP02100000",
            params={"FID_COND_MRKT_DIV_CODE": "U", "FID_INPUT_ISCD": iscd},
        )

    def get_overseas_index(self, iscd: str, start_yyyymmdd: str,
                           end_yyyymmdd: str) -> dict[str, Any]:
        """해외 지수 일별시세 (FHKST03030100, 시장구분 N=해외지수).
        iscd: COMP(나스닥 종합) / SPX(S&P500) / .DJI(다우) / NDX(나스닥100).

        응답 output1(최신 스냅샷) 활용 필드:
          ovrs_nmix_prpr        현재지수
          ovrs_nmix_prdy_clpr   전일종가
          ovrs_nmix_prdy_vrss   전일대비
        (prdy_ctrt는 null로 올 수 있어 등락률은 호출자가 직접 계산.)
        """
        return self._get(
            path="/uapi/overseas-price/v1/quotations/inquire-daily-chartprice",
            tr_id="FHKST03030100",
            params={
                "FID_COND_MRKT_DIV_CODE": "N", "FID_INPUT_ISCD": iscd,
                "FID_INPUT_DATE_1": start_yyyymmdd, "FID_INPUT_DATE_2": end_yyyymmdd,
                "FID_PERIOD_DIV_CODE": "D",
            },
        )

    # ----- 순위 (시장 요약 랭킹용) -----
    def get_domestic_fluctuation(self, sort_cls: str) -> dict[str, Any]:
        """국내 등락률 순위 (FHPST01700000). sort_cls: '0'(상승)/'1'(하락).

        응답 output(list) 활용 필드:
          stck_shrn_iscd 코드, hts_kor_isnm 이름, stck_prpr 현재가,
          prdy_vrss 전일대비(부호), prdy_ctrt 등락률
        """
        return self._get(
            path="/uapi/domestic-stock/v1/ranking/fluctuation",
            tr_id="FHPST01700000",
            params={
                "fid_cond_mrkt_div_code": "J", "fid_cond_scr_div_code": "20170",
                "fid_input_iscd": "0000", "fid_rank_sort_cls_code": sort_cls,
                "fid_input_cnt_1": "0", "fid_prc_cls_code": "0",
                "fid_input_price_1": "", "fid_input_price_2": "", "fid_vol_cnt": "",
                "fid_trgt_cls_code": "0", "fid_trgt_exls_cls_code": "0",
                "fid_div_cls_code": "0", "fid_rsfl_rate1": "", "fid_rsfl_rate2": "",
            },
        )

    def get_domestic_volume_rank(self) -> dict[str, Any]:
        """국내 거래량 순위 (FHPST01710000).

        응답 output(list): mksc_shrn_iscd 코드, hts_kor_isnm 이름, stck_prpr,
          prdy_vrss, prdy_ctrt, acml_vol 거래량
        """
        return self._get(
            path="/uapi/domestic-stock/v1/quotations/volume-rank",
            tr_id="FHPST01710000",
            params={
                "fid_cond_mrkt_div_code": "J", "fid_cond_scr_div_code": "20171",
                "fid_input_iscd": "0000", "fid_div_cls_code": "0", "fid_blng_cls_code": "0",
                "fid_trgt_cls_code": "111111111", "fid_trgt_exls_cls_code": "0000000000",
                "fid_input_price_1": "", "fid_input_price_2": "", "fid_vol_cnt": "",
                "fid_input_date_1": "",
            },
        )

    def get_overseas_volume_rank(self, excd: str) -> dict[str, Any]:
        """해외 거래량 순위 (HHDFS76310010). excd: NAS/NYS.

        응답 output2(list): symb, name/ename, last, diff, sign, rate, tvol 거래량
        """
        return self._get(
            path="/uapi/overseas-stock/v1/ranking/trade-vol",
            tr_id="HHDFS76310010",
            params={"AUTH": "", "EXCD": excd, "NDAY": "0", "PRC1": "", "PRC2": "",
                    "VOL_RANG": "0", "KEYB": ""},
        )
