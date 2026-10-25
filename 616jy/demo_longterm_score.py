"""longterm_score 검증 — 영풍제지(002870) 예시. API 키 불필요, 순수 산출만.

실행:  python demo_longterm_score.py
입력 지표/궁합은 **예시 가정값**(실DB 아님). 궁합은 stock DNA 매칭 트랙 산출분을 가정.
"""
from __future__ import annotations

from longterm_report import FinancialMetrics, GrowthMetrics, StockMeta, grade_of, label_of
from longterm_score import (
    W_FINANCIAL,
    W_GROWTH,
    W_MATCH,
    compute_scores,
    stock_subtotal,
    verdict_line,
)


def _row(label: str, score, note: str = "") -> str:
    g = grade_of(score)
    val = f"{score:5.1f}" if score is not None else "  ─  "
    tail = f"   {note}" if note else ""
    return f"  {label:<6} {val} / 100  ({g}){tail}"


def main() -> None:
    # 영풍제지 — KOSPI 제지. (예시 가정값)
    meta = StockMeta(code="002870", name="영풍제지", market="KOSPI", sector="제지")
    fin = FinancialMetrics(
        debt_ratio=78.5, current_ratio=152.0, operating_margin=7.8,
        net_margin=4.9, roe=6.5, fiscal_period="2025Q3",
    )
    grw = GrowthMetrics(revenue_yoy=4.2, operating_profit_yoy=-11.0, net_profit_yoy=-16.5)
    userfit = 58.0  # 궁합(적합도): DNA 매칭 트랙 산출분(안정형 유저 가정)

    scores = compute_scores(fin, grw, userfit_score=userfit)
    subtotal = stock_subtotal(scores.financial, scores.growth)

    print("=" * 56)
    print(f"  {meta.name} ({meta.code} · {meta.market} · {meta.sector})")
    print("=" * 56)
    print("  ── 장투케어 점수 3종 ──")
    print(_row("재무", scores.financial))
    print(_row("성장", scores.growth))
    print(_row("적합도", scores.userfit, "← 궁합(DNA), 입력값"))
    print("  ── 총평 ──")
    print(_row("종합", scores.total, f"— {label_of(scores.total)}"))
    print(f"\n  {verdict_line(scores)}")
    print(
        f"\n  [산식] 종목소계 {subtotal:.1f}"
        f" = 재무×{W_FINANCIAL} + 성장×{W_GROWTH}\n"
        f"         종합   {scores.total:.1f}"
        f" = 소계×{1 - W_MATCH:.1f} + 궁합×{W_MATCH}"
    )


if __name__ == "__main__":
    main()
