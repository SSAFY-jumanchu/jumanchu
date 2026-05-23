"""
DART OpenAPI - 단일회사 재무 조회 클라이언트
=====================================================

기능 요약
----------
1) corp_code 매핑 다운로드/캐싱
   - DART 고유번호(8자리 corp_code) ↔ 종목코드(6자리 stock_code) ↔ 회사명
   - corpCode.xml.zip 한 번 받아서 로컬 캐싱, 30일 후 자동 갱신
2) 단일회사 주요계정 조회 (fnlttSinglAcnt)
   - 매출액 / 영업이익 / 당기순이익 등 13개 주요 계정 (손익계산서)
3) 단일회사 전체 재무제표 조회 (fnlttSinglAcntAll)
   - BS(재무상태표) + IS(손익계산서) 전 계정 (부채/자기자본/유동자산 등 포함)

사용 전 준비
------------
- https://opendart.fss.or.kr/ 에서 API 키 발급
- requirements: requests, python-dotenv (선택)

환경 변수(.env)
----------------
DART_API_KEY=발급받은_키

API 제약
---------
- 호출 한도: 1일 20,000건 (개인 키 기준)
- corp_code 매핑은 ZIP 파일이라 첫 다운로드만 수 초 소요, 이후 캐시 사용
- 보고서 코드(reprt_code):
    11013 = 1분기 / 11012 = 반기 / 11014 = 3분기 / 11011 = 사업보고서(연간)
- 연결재무제표 여부(fs_div): CFS = 연결, OFS = 별도
- 일부 종목은 분기 보고서 미제출(분/반기 보고 면제 기업 등)
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
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

# ---------------------------------------------------------------------------
# 1. 환경/도메인 설정
# ---------------------------------------------------------------------------

DART_BASE_URL = "https://opendart.fss.or.kr/api"

# 매핑 캐시 위치 (홈 디렉토리 아래) — 토큰처럼 사용자별 1개
CORP_CODE_CACHE_PATH = Path.home() / ".dart_corp_code_cache.json"
CORP_CODE_TTL_DAYS = 30


@dataclass
class DartConfig:
    api_key: str = ""


# ---------------------------------------------------------------------------
# 2. 클라이언트 본체
# ---------------------------------------------------------------------------

class DartClient:
    """DART OpenAPI 래퍼. corp_code 매핑 + 재무 조회."""

    def __init__(self, config: DartConfig):
        self.cfg = config
        # stock_code(6자리) -> corp_code(8자리)
        self._stock_to_corp: dict[str, str] = {}
        # corp_code -> {"corp_name": ..., "stock_code": ...}
        self._corp_meta: dict[str, dict[str, str]] = {}
        self._load_cached_mapping()

    # ------------------------------------------------------------------
    # 2-1. corp_code 매핑 다운로드 / 캐싱
    # ------------------------------------------------------------------
    def _load_cached_mapping(self) -> None:
        """디스크 캐시가 30일 이내면 로드. 아니면 무시(다음 호출 시 재다운로드)."""
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
        """corpCode.xml.zip 다운로드 → 압축 해제 → XML 파싱 → 메모리 매핑 + 캐시 저장."""
        url = f"{DART_BASE_URL}/corpCode.xml"
        res = requests.get(url, params={"crtfc_key": self.cfg.api_key}, timeout=30)
        res.raise_for_status()

        # 응답이 ZIP이 아니라 에러 JSON(예: status=010 키 인증 실패)일 수 있어 분기
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
            if stock_code:  # 비상장 회사는 stock_code 비어있음
                stock_to_corp[stock_code] = corp_code

        self._stock_to_corp = stock_to_corp
        self._corp_meta = corp_meta
        self._save_mapping_cache()

    def ensure_mapping(self) -> None:
        """매핑이 비어있으면 다운로드. 외부에서 명시적으로 호출 가능."""
        if not self._stock_to_corp:
            self._download_corp_code_mapping()

    def corp_code_of(self, stock_code: str) -> str:
        """6자리 종목코드 → 8자리 corp_code. 못 찾으면 KeyError."""
        self.ensure_mapping()
        if stock_code not in self._stock_to_corp:
            raise KeyError(f"stock_code {stock_code} 매핑이 DART에 없음 (비상장/상폐 가능성)")
        return self._stock_to_corp[stock_code]

    def info_of(self, corp_code: str) -> dict[str, str]:
        """corp_code → {'corp_name', 'stock_code'}."""
        self.ensure_mapping()
        return self._corp_meta.get(corp_code, {})

    # ------------------------------------------------------------------
    # 2-2. 공통 요청 래퍼
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 3. 재무 조회 API
    # ------------------------------------------------------------------
    def get_single_account(
        self,
        corp_code: str,
        bsns_year: int,
        reprt_code: str,
    ) -> list[dict[str, Any]]:
        """
        단일회사 주요계정 (fnlttSinglAcnt)
        - 손익계산서 중심 13개 주요 계정
        - bsns_year: 사업연도 (YYYY)
        - reprt_code: 11013=Q1 / 11012=반기 / 11014=Q3 / 11011=사업보고서

        반환 list 의 각 원소 주요 필드:
            corp_code, corp_name, stock_code
            sj_div         BS=재무상태표 / IS=손익계산서
            account_nm     계정명 (예: "매출액", "영업이익", "당기순이익")
            thstrm_nm      당기명 (예: "제 56 기 반기")
            thstrm_dt      당기 기간 (예: "2024.01.01 ~ 2024.06.30")
            thstrm_amount  당기 금액
            frmtrm_amount  전기 동기 금액
        """
        data = self._get_json(
            "fnlttSinglAcnt.json",
            {
                "corp_code": corp_code,
                "bsns_year": str(bsns_year),
                "reprt_code": reprt_code,
            },
        )
        return data.get("list", [])

    def get_single_account_all(
        self,
        corp_code: str,
        bsns_year: int,
        reprt_code: str,
        fs_div: str = "CFS",
    ) -> list[dict[str, Any]]:
        """
        단일회사 전체 재무제표 (fnlttSinglAcntAll)
        - BS + IS + CIS + CF + SCE 전 계정 (수십~수백 항목)
        - fs_div: CFS=연결재무제표, OFS=별도재무제표

        반환 list 각 원소 주요 필드는 get_single_account와 동일하나
        account_nm/account_id가 훨씬 다양함.
        부채총계, 자본총계, 유동자산, 유동부채 등 안정성 지표 계산에 사용.
        """
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
        """
        기업 개황 (company)
        반환 주요 필드: corp_name, ceo_nm, induty_code, est_dt, hm_url, ...
        """
        return self._get_json("company.json", {"corp_code": corp_code})


# ---------------------------------------------------------------------------
# 4. 사용 예시 (직접 실행 시 동작)
# ---------------------------------------------------------------------------

def _demo() -> None:
    """삼성전자(005930) 기준 corp_code 매핑 + 회사 개황 + 최근 주요계정 1건 출력."""
    cfg = DartConfig(api_key=os.environ["DART_API_KEY"])
    client = DartClient(cfg)

    # 1) 매핑 (첫 실행은 ZIP 다운로드 → 수 초)
    client.ensure_mapping()
    print(f"[매핑] 상장 종목 corp_code 매핑 {len(client._stock_to_corp):,}건 로드됨")

    # 2) 삼성전자 → corp_code 변환
    samsung_corp = client.corp_code_of("005930")
    print(f"[변환] 005930 (삼성전자) → corp_code {samsung_corp}")

    # 3) 회사 개황
    company = client.get_company(samsung_corp)
    print(f"[개황] {company.get('corp_name')} · CEO {company.get('ceo_nm')} "
          f"· 업종 {company.get('induty_code')} · 설립 {company.get('est_dt')}")

    # 4) 최근 사업보고서(연간) 주요계정
    accounts = client.get_single_account(samsung_corp, bsns_year=2024, reprt_code="11011")
    print(f"[재무] 2024년 사업보고서 주요계정 {len(accounts)}건")
    for row in accounts[:5]:
        print(f"  - {row.get('sj_div'):2} {row.get('account_nm'):8} "
              f"당기={row.get('thstrm_amount')} 전기={row.get('frmtrm_amount')}")


if __name__ == "__main__":
    _demo()
