"""longterm_report 독립 실행 검증 — API 키 없이 동작.
====================================================
가짜(fake) LLM을 주입해 프롬프트 build → parse → to_dict 전 경로를 확인한다.
실제 BE는 fake_llm 자리에 OpenAI 호출을 넣는다.

실행:  python demo_longterm_report.py
"""

from __future__ import annotations

import json

from longterm_report import (
    FinancialMetrics,
    GrowthMetrics,
    LongTermScores,
    StockMeta,
    UserProfile,
    build_longterm_report,
    build_report_prompt,
)


def fake_llm(prompt: str) -> str:
    """프롬프트와 무관하게 형식만 맞춘 JSON 반환 (오프라인 검증용)."""
    return json.dumps(
        {
            "financial": "부채비율이 낮고 영업이익률이 견조해 재무 체력이 안정적입니다. "
                         "단기 유동성도 양호한 편이라 외부 충격에 버틸 여력이 있습니다.",
            "growth": "매출과 영업이익이 전년 대비 크게 늘며 성장세가 뚜렷합니다. "
                      "이익이 함께 성장하고 있어 건강한 성장으로 볼 수 있습니다.",
            "userfit": "공격형 성향과 선호 섹터에 잘 맞는 종목입니다. "
                       "다만 포트폴리오 비중이 높아 분산 관점의 점검이 필요합니다.",
            "final_opinion": "재무와 성장성이 모두 우수해 장기 보유 매력이 높은 종목입니다. "
                             "투자 성향과도 잘 맞습니다. 비중이 높은 점만 주기적으로 살피시면 "
                             "장기 관점에서 핵심 보유 후보로 손색이 없습니다.",
        },
        ensure_ascii=False,
    )


def main() -> None:
    meta = StockMeta(code="000660", name="SK하이닉스", market="KOSPI",
                     sector="반도체", currency="KRW")
    fin = FinancialMetrics(debt_ratio=22.4, current_ratio=198.3,
                           operating_margin=32.1, net_margin=24.5,
                           roe=26.78, roa=14.2, dividend_yield=1.1,
                           fiscal_period="2025Q3")
    grw = GrowthMetrics(revenue_yoy=48.2, operating_profit_yoy=120.5, net_profit_yoy=90.1)
    scores = LongTermScores(financial=78, growth=92, total=86, userfit=87)
    profile = UserProfile(risk_type="공격형", preferred_period_months=12,
                          preferred_sectors=["반도체", "전기전자"], portfolio_weight_pct=38.4)

    print("=" * 70)
    print("[1] 생성된 프롬프트 (LLM에 전달될 문자열)")
    print("=" * 70)
    print(build_report_prompt(meta, fin, grw, scores, profile))

    print("\n" + "=" * 70)
    print("[2] fake LLM 주입 → 리포트 결과 (to_dict)")
    print("=" * 70)
    report = build_longterm_report(meta, fin, grw, scores, profile, llm=fake_llm)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))

    print("\n" + "=" * 70)
    print("[3] 적합도 없는 경우(profile=None) — 재무+성장+종합의견만")
    print("=" * 70)
    report2 = build_longterm_report(meta, fin, grw, scores, None, llm=fake_llm)
    print("userfit:", report2.userfit)
    print("final_opinion:", report2.final_opinion[:40], "...")


if __name__ == "__main__":
    main()
