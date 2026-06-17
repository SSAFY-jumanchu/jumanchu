"""실 DB 덤프 → 지표 추출 → 점수 산출 → 실 GMS GPT-4o → 재무/성장/궁합/총평 출력. (검증용)

- 지표: stocks_financialsummary + stocks_stockindicator (실 DB, 비율→% ×100)
- 궁합: 온보딩 산출값(rec_type='onboarding')이나 덤프엔 비어있음 → 온보딩 가정값 주입
- 총평: gms_client.make_gms_caller (실제 GMS GPT-4o 1콜/종목)
"""
from __future__ import annotations
import os
from dotenv import load_dotenv

from longterm_report import (
    FinancialMetrics, GrowthMetrics, StockMeta, UserProfile,
    build_longterm_report, grade_of, label_of,
)
from longterm_score import compute_scores, stock_subtotal, W_MATCH
from gms_client import make_gms_caller

DUMP = r"C:\Users\정율\Desktop\jumanchu\jumanchu\616jy\0615jy\jumanchu_db_20260615.sql"
ENV = r"C:\Users\정율\Desktop\jumanchu\jumanchu\616jy\0615jy\.env"

# (stock_id, 위험성향, 선호기간, 선호섹터, 온보딩 궁합 가정값)
CANDIDATES = [
    ("285",  "균형형", 12, ["전기·전자", "반도체"],            78.0),  # 삼성전자
    ("40",   "공격형", 18, ["전기·전자", "반도체"],            81.0),  # SK하이닉스
    ("586",  "균형형", 12, ["IT 서비스", "인터넷"],            70.0),  # NAVER
    ("261",  "안정형", 24, ["운송장비·부품", "자동차"],        66.0),  # 현대차
    ("3591", "공격형", 24, ["IT", "컴퓨터전자장비/기기"],      64.0),  # Apple
    ("6075", "공격형", 12, ["반도체", "반도체 및 반도체장비"], 88.0),  # NVIDIA
]
IDS = {c[0] for c in CANDIDATES}
TABLES = {"stocks_stock": "id", "stocks_financialsummary": "stock_id",
          "stocks_stockindicator": "stock_id"}


def parse(dump):
    out = {t: [] for t in TABLES}
    cur = cols = None
    with open(dump, encoding="utf-8") as f:
        for line in f:
            if cur is None:
                if line.startswith("COPY public."):
                    name = line.split("COPY public.")[1].split(" ")[0]
                    if name in TABLES:
                        cols = line[line.index("(") + 1:line.index(")")].split(", ")
                        cur = name
                continue
            if line.rstrip("\n") == r"\.":
                cur = None
                continue
            row = dict(zip(cols, line.rstrip("\n").split("\t")))
            if row.get(TABLES[cur]) in IDS:
                out[cur].append(row)
    return out


def num(v):
    return None if v in (None, "", r"\N") else float(v)


def pct(v):                       # 비율(fraction) → 퍼센트
    n = num(v)
    return None if n is None else n * 100.0


def f1(v):                        # 출력용 (None 안전)
    return "데이터없음" if v is None else f"{v:.1f}%"


def main():
    load_dotenv(ENV)
    data = parse(DUMP)
    llm = make_gms_caller(force_json=True)

    stock_by_id = {r["id"]: r for r in data["stocks_stock"]}
    fs_by_id, ind_by_id = {}, {}
    for r in data["stocks_financialsummary"]:           # 최신 재무(최근 fetched_at)
        sid = r["stock_id"]
        if sid not in fs_by_id or r["fetched_at"] > fs_by_id[sid]["fetched_at"]:
            fs_by_id[sid] = r
    for r in data["stocks_stockindicator"]:             # roe 있는 최신 지표
        if num(r["roe"]) is None:
            continue
        sid = r["stock_id"]
        if sid not in ind_by_id or r["calculated_date"] > ind_by_id[sid]["calculated_date"]:
            ind_by_id[sid] = r

    for sid, risk, period, sectors, userfit in CANDIDATES:
        s, fs = stock_by_id.get(sid), fs_by_id.get(sid)
        if not s or not fs:
            print(f"[skip] stock_id={sid} — 재무 데이터 없음\n")
            continue
        ind = ind_by_id.get(sid, {})
        meta = StockMeta(s["code"], s["name"], s["market"], s["sector"], s["currency"])
        fin = FinancialMetrics(
            debt_ratio=pct(fs["debt_ratio"]), current_ratio=pct(fs["current_ratio"]),
            operating_margin=pct(fs["operating_margin"]), net_margin=pct(fs["net_margin"]),
            roe=pct(ind.get("roe")), fiscal_period=fs["fiscal_period"])
        grw = GrowthMetrics(pct(fs["revenue_yoy"]), pct(fs["operating_profit_yoy"]),
                            pct(fs["net_profit_yoy"]))
        profile = UserProfile(risk, period, sectors, None)
        scores = compute_scores(fin, grw, userfit_score=userfit)
        subtotal = stock_subtotal(scores.financial, scores.growth)
        d = build_longterm_report(meta, fin, grw, scores, profile, llm=llm).to_dict()

        print("=" * 66)
        print(f"  {meta.name} ({meta.code} · {meta.market} · {meta.sector}) [{fs['fiscal_period']}]")
        print("=" * 66)
        print(f"  부채 {f1(fin.debt_ratio)} · 유동 {f1(fin.current_ratio)} · 영업이익률 {f1(fin.operating_margin)} · "
              f"순이익률 {f1(fin.net_margin)} · ROE {f1(fin.roe)}")
        print(f"  매출YoY {f1(grw.revenue_yoy)} · 영업익YoY {f1(grw.operating_profit_yoy)} · 순익YoY {f1(grw.net_profit_yoy)}")
        print()
        print(f"  재무 [{scores.financial:.0f}/{grade_of(scores.financial)}]  {d['financial']['summary']}")
        print(f"  성장 [{scores.growth:.0f}/{grade_of(scores.growth)}]  {d['growth']['summary']}")
        print(f"  궁합 [{scores.userfit:.0f}/{grade_of(scores.userfit)}]  {d['userfit']['summary']}  ※온보딩 가정값")
        print(f"  ── 총평 [{scores.total:.0f}/{grade_of(scores.total)}] {label_of(scores.total)} "
              f"(소계 {subtotal:.0f}×{1-W_MATCH:.1f} + 궁합×{W_MATCH}) ──")
        print(f"  {d['total']['opinion']}")
        print()


if __name__ == "__main__":
    main()
