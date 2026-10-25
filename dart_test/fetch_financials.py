"""
DART 재무 가공 데모 - FinancialSummary 매핑
================================================

DartClient로 받은 원시 재무 데이터를 우리 ERD의
`FINANCIAL_SUMMARY` 테이블 컬럼에 맞춰 가공해 보는 스크립트.

매핑 대상 (FinancialSummary 핵심 필드 — docs/DART_COLUMN.md 참조)
----------------------------------------------------------------
원본:    revenue, operating_profit, net_profit                       (IS, P0)
수익성:  operating_margin = OP / Revenue                              (P0)
         net_margin       = NP / Revenue                              (P0)
성장성:  revenue_yoy, operating_profit_yoy, net_profit_yoy             (P0)
안정성:  debt_ratio       = 부채총계 / 자기자본                       (P0)
         equity_ratio     = 자기자본 / 총자산                          (P1)
         current_ratio    = 유동자산 / 유동부채                        (P1)

가공이 끝나면 그대로 `FinancialSummary.objects.create(...)`에 넘기면 되는 형태.

의존성
------
- 동일 디렉토리의 dart_client.py
- requests
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from dart_client import DartClient, DartConfig

from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")


# ---------------------------------------------------------------------------
# 1. 헬퍼 - DART 응답에서 특정 계정 금액 뽑기
# ---------------------------------------------------------------------------

def _to_int(amount: Optional[str]) -> Optional[int]:
    """DART는 금액이 쉼표 섞인 문자열로 옴. '-'나 '' 은 None."""
    if amount is None:
        return None
    s = amount.replace(",", "").strip()
    if not s or s in ("-", "—"):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _find_account(
    rows: list[dict[str, Any]],
    *,
    sj_div: str,
    names: list[str],
) -> Optional[dict[str, Any]]:
    """주어진 계정명(여러 후보 중 하나) + 재무제표 구분(BS/IS/CIS)으로 한 행 찾기."""
    for row in rows:
        if row.get("sj_div") != sj_div:
            continue
        if row.get("account_nm") in names:
            return row
    return None


def _safe_div(a: Optional[int], b: Optional[int]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return round(a / b, 4)


def _yoy(curr: Optional[int], prev: Optional[int]) -> Optional[float]:
    """전년 동기 대비 성장률. prev가 0이거나 None이면 None."""
    if curr is None or prev is None or prev == 0:
        return None
    return round((curr - prev) / abs(prev), 4)


# ---------------------------------------------------------------------------
# 2. 메인 가공 함수
# ---------------------------------------------------------------------------

def build_financial_summary(
    client: DartClient,
    corp_code: str,
    bsns_year: int,
    reprt_code: str,
    fs_div: str = "CFS",
) -> dict[str, Any]:
    """
    DART 응답 → FinancialSummary 컬럼 dict.
    Django에서는 그대로 FinancialSummary.objects.update_or_create(
        stock=..., fiscal_period=..., defaults=result
    ) 에 사용.
    """
    rows = client.get_single_account_all(
        corp_code=corp_code,
        bsns_year=bsns_year,
        reprt_code=reprt_code,
        fs_div=fs_div,
    )

    if not rows:
        return {
            "fiscal_period": f"{bsns_year}{_PERIOD_SUFFIX[reprt_code]}",
            "data_source": "DART",
            "note": "DART 응답 없음 (분/반기 면제 회사이거나 미공시)",
        }

    # IS (손익계산서)
    revenue_row = _find_account(rows, sj_div="IS", names=["매출액", "수익(매출액)", "영업수익"])
    op_row = _find_account(rows, sj_div="IS", names=["영업이익", "영업이익(손실)"])
    np_row = _find_account(rows, sj_div="IS", names=["당기순이익", "당기순이익(손실)"])

    # BS (재무상태표)
    total_assets_row = _find_account(rows, sj_div="BS", names=["자산총계"])
    total_liab_row = _find_account(rows, sj_div="BS", names=["부채총계"])
    total_equity_row = _find_account(rows, sj_div="BS", names=["자본총계"])
    current_assets_row = _find_account(rows, sj_div="BS", names=["유동자산"])
    current_liab_row = _find_account(rows, sj_div="BS", names=["유동부채"])

    revenue = _to_int(revenue_row and revenue_row.get("thstrm_amount"))
    op = _to_int(op_row and op_row.get("thstrm_amount"))
    np = _to_int(np_row and np_row.get("thstrm_amount"))

    prev_revenue = _to_int(revenue_row and revenue_row.get("frmtrm_amount"))
    prev_op = _to_int(op_row and op_row.get("frmtrm_amount"))
    prev_np = _to_int(np_row and np_row.get("frmtrm_amount"))

    total_assets = _to_int(total_assets_row and total_assets_row.get("thstrm_amount"))
    total_liab = _to_int(total_liab_row and total_liab_row.get("thstrm_amount"))
    total_equity = _to_int(total_equity_row and total_equity_row.get("thstrm_amount"))
    current_assets = _to_int(current_assets_row and current_assets_row.get("thstrm_amount"))
    current_liab = _to_int(current_liab_row and current_liab_row.get("thstrm_amount"))

    return {
        "fiscal_period": f"{bsns_year}{_PERIOD_SUFFIX[reprt_code]}",
        # 원본
        "revenue": revenue,
        "operating_profit": op,
        "net_profit": np,
        # 수익성 (P0)
        "operating_margin": _safe_div(op, revenue),
        "net_margin": _safe_div(np, revenue),
        # 성장성 (P0)
        "revenue_yoy": _yoy(revenue, prev_revenue),
        "operating_profit_yoy": _yoy(op, prev_op),
        "net_profit_yoy": _yoy(np, prev_np),
        # 안정성 (P0/P1)
        "debt_ratio": _safe_div(total_liab, total_equity),
        "equity_ratio": _safe_div(total_equity, total_assets),
        "current_ratio": _safe_div(current_assets, current_liab),
        # 메타
        "data_source": "DART",
    }


_PERIOD_SUFFIX = {
    "11013": "Q1",
    "11012": "H1",
    "11014": "Q3",
    "11011": "FY",
}


# ---------------------------------------------------------------------------
# 3. 데모: 삼성전자 2024 사업보고서 → FinancialSummary 한 건 만들어 보기
# ---------------------------------------------------------------------------

def _demo() -> None:
    cfg = DartConfig(api_key=os.environ["DART_API_KEY"])
    client = DartClient(cfg)

    samsung_corp = client.corp_code_of("005930")
    info = client.info_of(samsung_corp)
    print(f"[대상] {info['corp_name']} (stock={info['stock_code']}, corp={samsung_corp})")

    # 2024년 사업보고서 (연간)
    summary = build_financial_summary(
        client, samsung_corp, bsns_year=2024, reprt_code="11011", fs_div="CFS"
    )
    print("[2024 사업보고서 (연결) → FinancialSummary]")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 2024년 반기보고서로도 한 번 — 일부 회사는 면제, 데이터 없을 수 있음
    summary_h1 = build_financial_summary(
        client, samsung_corp, bsns_year=2024, reprt_code="11012", fs_div="CFS"
    )
    print("\n[2024 반기보고서 (연결) → FinancialSummary]")
    print(json.dumps(summary_h1, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _demo()
