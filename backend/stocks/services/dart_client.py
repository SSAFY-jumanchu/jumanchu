"""
DART OpenAPI 클라이언트 (backend 운영용).

dart_test/dart_client.py 와 본질적으로 같지만, backend에서
import 하기 좋게 패키지 안에 둠. KIS 패턴 맞춰 from_env() 추가.

기능 요약
----------
1) corp_code 매핑 다운로드/캐싱
   - DART 고유번호(8자리 corp_code) ↔ 종목코드(6자리 stock_code) ↔ 회사명
   - corpCode.xml.zip 한 번 받아서 로컬 캐싱, 30일 후 자동 갱신
2) 단일회사 주요계정 조회 (fnlttSinglAcnt)
3) 단일회사 전체 재무제표 조회 (fnlttSinglAcntAll)
4) 기업 개황 조회 (company) — ceo_nm, hm_url, induty_code, est_dt 등

환경 변수
----------
- DART_API_KEY (https://opendart.fss.or.kr/ 발급)

API 제약
---------
- 호출 한도: 1일 20,000건 (개인 키 기준)
- corp_code 매핑은 ZIP 파일이라 첫 다운로드만 수 초 소요, 이후 캐시 사용
- 보고서 코드(reprt_code):
    11013 = 1분기 / 11012 = 반기 / 11014 = 3분기 / 11011 = 사업보고서(연간)
- 연결재무제표 여부(fs_div): CFS = 연결, OFS = 별도
"""
from __future__ import annotations

import io
import json
import os
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import requests


DART_BASE_URL = "https://opendart.fss.or.kr/api"

CORP_CODE_CACHE_PATH = Path.home() / ".dart_corp_code_cache.json"
CORP_CODE_TTL_DAYS = 30


@dataclass
class DartConfig:
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "DartConfig":
        return cls(api_key=os.environ["DART_API_KEY"])


class DartClient:
    """DART OpenAPI 래퍼. corp_code 매핑 + 재무/개황 조회."""

    def __init__(self, config: DartConfig):
        self.cfg = config
        self._stock_to_corp: dict[str, str] = {}
        self._corp_meta: dict[str, dict[str, str]] = {}
        self._load_cached_mapping()

    def _load_cached_mapping(self) -> None:
        if not CORP_CODE_CACHE_PATH.exists():
            return
        try:
            data = json.loads(CORP_CODE_CACHE_PATH.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(data["fetched_at"])
            if fetched_at + timedelta(days=CORP_CODE_TTL_DAYS) > datetime.now():
                self._stock_to_corp = data["stock_to_corp"]
                self._corp_meta = data["corp_meta"]
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    def _save_mapping_cache(self) -> None:
        CORP_CODE_CACHE_PATH.write_text(
            json.dumps(
                {
                    "fetched_at": datetime.now().isoformat(),
                    "stock_to_corp": self._stock_to_corp,
                    "corp_meta": self._corp_meta,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _download_corp_code_mapping(self) -> None:
        url = f"{DART_BASE_URL}/corpCode.xml"
        res = requests.get(url, params={"crtfc_key": self.cfg.api_key}, timeout=30)
        res.raise_for_status()

        ctype = res.headers.get("Content-Type", "")
        if "json" in ctype or res.content.startswith(b"{"):
            payload = res.json()
            raise RuntimeError(f"[corp_code] {payload.get('status')} {payload.get('message')}")

        with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
            with zf.open("CORPCODE.xml") as xf:
                tree = ET.parse(xf)
        root = tree.getroot()

        stock_to_corp: dict[str, str] = {}
        corp_meta: dict[str, dict[str, str]] = {}
        for item in root.findall("list"):
            corp_code = (item.findtext("corp_code") or "").strip()
            corp_name = (item.findtext("corp_name") or "").strip()
            stock_code = (item.findtext("stock_code") or "").strip()
            if not corp_code:
                continue
            corp_meta[corp_code] = {"corp_name": corp_name, "stock_code": stock_code}
            if stock_code:
                stock_to_corp[stock_code] = corp_code

        self._stock_to_corp = stock_to_corp
        self._corp_meta = corp_meta
        self._save_mapping_cache()

    def ensure_mapping(self) -> None:
        if not self._stock_to_corp:
            self._download_corp_code_mapping()

    def corp_code_of(self, stock_code: str) -> str:
        """6자리 종목코드 → 8자리 corp_code. 못 찾으면 KeyError."""
        self.ensure_mapping()
        if stock_code not in self._stock_to_corp:
            raise KeyError(f"stock_code {stock_code} 매핑이 DART에 없음 (비상장/상폐 가능성)")
        return self._stock_to_corp[stock_code]

    def info_of(self, corp_code: str) -> dict[str, str]:
        self.ensure_mapping()
        return self._corp_meta.get(corp_code, {})

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{DART_BASE_URL}/{path}"
        params = {**params, "crtfc_key": self.cfg.api_key}
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        status = data.get("status")
        # 000: 정상 / 013: 조회된 데이터 없음 (정상의 일종)
        if status not in ("000", "013"):
            raise RuntimeError(f"[{path}] status={status} message={data.get('message')}")
        return data

    def get_single_account(
        self, corp_code: str, bsns_year: int, reprt_code: str,
    ) -> list[dict[str, Any]]:
        data = self._get_json(
            "fnlttSinglAcnt.json",
            {"corp_code": corp_code, "bsns_year": str(bsns_year), "reprt_code": reprt_code},
        )
        return data.get("list", [])

    def get_single_account_all(
        self, corp_code: str, bsns_year: int, reprt_code: str, fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        data = self._get_json(
            "fnlttSinglAcntAll.json",
            {
                "corp_code": corp_code,
                "bsns_year": str(bsns_year),
                "reprt_code": reprt_code,
                "fs_div": fs_div,
            },
        )
        return data.get("list", [])

    def get_company(self, corp_code: str) -> dict[str, Any]:
        """기업 개황. 응답 최상위에 ceo_nm, hm_url, induty_code, est_dt 등."""
        return self._get_json("company.json", {"corp_code": corp_code})
