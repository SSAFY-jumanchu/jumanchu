"""
DART 재무 가공 - FinancialSummary 매핑 (backend 운영용).

dart_test/fetch_financials.py 를 backend로 이전 + roe/roa/payout_ratio 확장.

build_financial_summary() 반환 dict:
  원본:    revenue, operating_profit, net_profit
  수익성:  operating_margin, net_margin
  성장성:  revenue_yoy, operating_profit_yoy, net_profit_yoy
  안정성:  debt_ratio, equity_ratio, current_ratio
  배당:    payout_ratio (배당금의지급 / 순이익)
  메타:    fiscal_period, data_source="DART"
  계산보조: _total_equity, _total_assets, _net_profit (언더스코어 = DB 저장 안 함;
           command에서 roe = net/equity, roa = net/assets 계산 후 pop)

단위: 비율은 모두 배수(소수). 예) operating_margin 0.1088 = 10.88%.
"""
from __future__ import annotations

from typing import Any, Optional

from stocks.services.dart_client import DartClient


_PERIOD_SUFFIX = {
    "11013": "Q1",
    "11012": "H1",
    "11014": "Q3",
    "11011": "FY",
}


def _to_int(amount: Optional[str]) -> Optional[int]:
    """DART는 금액이 쉼표 섞인 문자열로 옴. '-'나 '' 은 None."""
    if amount is None:
        return None
    s = str(amount).replace(",", "").strip()
    if not s or s in ("-", "—"):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _find_account(
    rows: list[dict[str, Any]],
    *,
    sj_div,
    names: list[str],
) -> Optional[dict[str, Any]]:
    """계정명(여러 후보 중 하나) + 재무제표 구분으로 한 행 찾기.

    sj_div는 문자열 또는 리스트. 손익 항목은 회사에 따라 IS(손익계산서) 또는
    CIS(포괄손익계산서)에 들어있어 둘 다 봐야 한다.
    """
    sj_divs = [sj_div] if isinstance(sj_div, str) else list(sj_div)
    for row in rows:
        if row.get("sj_div") not in sj_divs:
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


def build_financial_summary(
    client: DartClient,
    corp_code: str,
    bsns_year: int,
    reprt_code: str,
    fs_div: str = "CFS",
) -> dict[str, Any]:
    """
    DART 응답 → FinancialSummary 컬럼 dict (+ roe/roa 계산용 보조 필드).

    fs_div="CFS"(연결재무)로 먼저 시도하고, revenue를 못 뽑으면
    OFS(별도재무)로 한 번 더 시도한다. 한국 단독회사·소형주는 연결재무를
    제출하지 않아 CFS만 보면 대량 누락되기 때문.

    revenue가 None이면 미공시/면제 회사 → command에서 skip 판정.
    """
    data = _build_one(client, corp_code, bsns_year, reprt_code, fs_div)
    if data.get("revenue") is None and fs_div == "CFS":
        # 연결재무 미제출 → 별도재무(OFS) fallback
        data = _build_one(client, corp_code, bsns_year, reprt_code, "OFS")
    return data


def _build_one(
    client: DartClient,
    corp_code: str,
    bsns_year: int,
    reprt_code: str,
    fs_div: str,
) -> dict[str, Any]:
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
            "revenue": None,
            "_total_equity": None,
            "_total_assets": None,
            "_net_profit": None,
        }

    # 손익 항목: 회사에 따라 IS(손익계산서) 또는 CIS(포괄손익계산서)에 있음
    IS_CIS = ["IS", "CIS"]
    revenue_row = _find_account(rows, sj_div=IS_CIS, names=["매출액", "수익(매출액)", "영업수익", "매출"])
    op_row = _find_account(rows, sj_div=IS_CIS, names=["영업이익", "영업이익(손실)"])
    np_row = _find_account(rows, sj_div=IS_CIS, names=["당기순이익", "당기순이익(손실)"])

    # BS (재무상태표)
    total_assets_row = _find_account(rows, sj_div="BS", names=["자산총계"])
    total_liab_row = _find_account(rows, sj_div="BS", names=["부채총계"])
    total_equity_row = _find_account(rows, sj_div="BS", names=["자본총계"])
    current_assets_row = _find_account(rows, sj_div="BS", names=["유동자산"])
    current_liab_row = _find_account(rows, sj_div="BS", names=["유동부채"])

    # CF (현금흐름표) - 배당금지급
    div_row = _find_account(
        rows, sj_div="CF",
        names=["배당금의지급", "배당금 지급", "현금배당금의 지급", "배당금지급"],
    )

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

    dividend_paid = _to_int(div_row and div_row.get("thstrm_amount"))
    # CF 배당금지급은 현금 유출이라 음수일 수 있음 → abs
    payout_ratio = _safe_div(abs(dividend_paid) if dividend_paid is not None else None, np)

    return {
        "fiscal_period": f"{bsns_year}{_PERIOD_SUFFIX[reprt_code]}",
        # 원본
        "revenue": revenue,
        "operating_profit": op,
        "net_profit": np,
        # 수익성
        "operating_margin": _safe_div(op, revenue),
        "net_margin": _safe_div(np, revenue),
        # 성장성
        "revenue_yoy": _yoy(revenue, prev_revenue),
        "operating_profit_yoy": _yoy(op, prev_op),
        "net_profit_yoy": _yoy(np, prev_np),
        # 안정성
        "debt_ratio": _safe_div(total_liab, total_equity),
        "equity_ratio": _safe_div(total_equity, total_assets),
        "current_ratio": _safe_div(current_assets, current_liab),
        # 배당
        "payout_ratio": payout_ratio,
        # 메타
        "data_source": "DART",
        # 계산 보조 (DB 저장 전 pop)
        "_total_equity": total_equity,
        "_total_assets": total_assets,
        "_net_profit": np,
    }
