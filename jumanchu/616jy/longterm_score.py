"""장투 점수 산출기 (Long-Term Score) — 순수 Algo 로직 (정율 → BE)
========================================================================
재무·성장 지표 → 종목소계, 거기에 개인 궁합을 결합해 **장투 최종 total**을 낸다.
`longterm_report`(LLM 문장)의 입력으로 쓰는 `LongTermScores`를 만들어 준다.

근거 (진실의 원천 = backend/recommend 모델):
  - `recommend.LongTermScore.total_score` help_text = "종목 소계 (재무+성장)"  ← per-stock
  - `recommend.LongTermScore` docstring   = "개인 궁합 30%는 RecommendationCache서 결합"
  - `recommend.StockDna`                  = 종목 성격(궁합 계산 입력), 궁합은 별도 트랙 산출
  ⇒  장투 최종 total = 종목소계 × (1 - W_MATCH) + 궁합 × W_MATCH,  W_MATCH = 0.30 (확정)

가중치 메모:
  - **궁합 30%만 BE 모델로 확정** (W_MATCH).
  - 재무↔성장 비중(W_FINANCIAL/W_GROWTH), 각 지표 점수화 기준선은 **잠정값** —
    팀(Algo/BE) 합의로 조정 가능하도록 전부 상수/함수로 분리했다.
  - 궁합 점수(userfit) 자체는 stock DNA 매칭 트랙이 산출 → 여기선 **입력으로 받는다**.
"""
from __future__ import annotations

from typing import Optional

from longterm_report import (
    FinancialMetrics,
    GrowthMetrics,
    LongTermScores,
    grade_of,
    label_of,
)

# ============================================================================ #
# 가중치 상수 (한 곳에서 조정)
# ============================================================================ #
W_MATCH = 0.30        # 궁합(적합도) 비중 — 확정 (recommend.LongTermScore docstring)
W_FINANCIAL = 0.30    # 재무 30% (전체 기준) — 팀 합의 (2026-06-22). BE recommend/scoring.py와 동일
W_GROWTH = 0.40       # 성장 40% (전체 기준) — 합: 재무0.3+성장0.4+궁합0.3 = 1.0


# ============================================================================ #
# 점수화 헬퍼 — 지표값을 0~100 점으로 선형 환산 (기준선 밖은 clamp)
# ============================================================================ #
def _linear(value: Optional[float], at_zero: float, at_full: float) -> Optional[float]:
    """value를 0~100으로. at_zero에서 0점, at_full에서 100점(그 사이 선형, 밖은 clamp).

    부채비율처럼 '낮을수록 좋은' 지표는 at_zero > at_full 로 넣으면 방향이 뒤집힌다.
    """
    if value is None:
        return None
    score = (value - at_zero) / (at_full - at_zero) * 100.0
    return max(0.0, min(100.0, score))


def _avg(values: list[Optional[float]]) -> Optional[float]:
    """None은 빼고 평균. 전부 None이면 None (데이터 없음)."""
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


# ============================================================================ #
# 재무 점수 / 성장 점수 (지표 → 0~100). 기준선은 잠정.
# ============================================================================ #
def financial_score(fin: FinancialMetrics) -> Optional[float]:
    """재무 건전성 점수. 부채↓·유동↑·마진↑·ROE↑ 일수록 고득점."""
    subs = [
        _linear(fin.debt_ratio, 200, 0),       # 부채비율: 200%→0, 0%→100
        _linear(fin.current_ratio, 0, 200),    # 유동비율: 0%→0, 200%→100
        _linear(fin.operating_margin, 0, 30),  # 영업이익률: 0%→0, 30%→100
        _linear(fin.net_margin, 0, 25),        # 순이익률: 0%→0, 25%→100
        _linear(fin.roe, 0, 20),               # ROE: 0%→0, 20%→100
    ]
    return _avg(subs)


def growth_score(grw: GrowthMetrics) -> Optional[float]:
    """성장성 점수. YoY 0%를 50점 기준, ±30%에서 0/100점."""
    subs = [
        _linear(grw.revenue_yoy, -30, 30),
        _linear(grw.operating_profit_yoy, -30, 30),
        _linear(grw.net_profit_yoy, -30, 30),
    ]
    return _avg(subs)


# ============================================================================ #
# 결합 — 종목소계, 장투 최종 total
# ============================================================================ #
def stock_subtotal(financial: Optional[float], growth: Optional[float]) -> Optional[float]:
    """종목 소계 = 재무·성장 가중평균 (= recommend.LongTermScore.total_score). per-stock."""
    parts = [(financial, W_FINANCIAL), (growth, W_GROWTH)]
    present = [(s, w) for s, w in parts if s is not None]
    if not present:
        return None
    wsum = sum(w for _, w in present)
    return sum(s * w for s, w in present) / wsum  # 한쪽만 있으면 그 점수로


def longterm_total(subtotal: Optional[float], userfit: Optional[float]) -> Optional[float]:
    """장투 최종 = 종목소계 × (1-W_MATCH) + 궁합 × W_MATCH. 궁합 없으면 소계만."""
    if subtotal is None:
        return userfit
    if userfit is None:
        return subtotal
    return subtotal * (1 - W_MATCH) + userfit * W_MATCH


def compute_scores(
    fin: FinancialMetrics,
    grw: GrowthMetrics,
    userfit_score: Optional[float] = None,
) -> LongTermScores:
    """지표 + 궁합 → LongTermScores(financial/growth/total/userfit).

    userfit_score: stock DNA 매칭 트랙이 준 궁합 점수(0~100). 없으면 소계가 곧 total.
    """
    fs = financial_score(fin)
    gs = growth_score(grw)
    subtotal = stock_subtotal(fs, gs)
    total = longterm_total(subtotal, userfit_score)
    return LongTermScores(
        financial=fs if fs is not None else 0.0,
        growth=gs if gs is not None else 0.0,
        total=total if total is not None else 0.0,
        userfit=userfit_score,
    )


# ============================================================================ #
# 총평(verdict) — 결정적 한 줄 (LLM 총평의 근거/폴백). 환각 없음.
# ============================================================================ #
def verdict_line(scores: LongTermScores) -> str:
    """점수 패턴 기반 한 줄 총평. (자연어 총평은 longterm_report의 LLM이 담당)"""
    label = label_of(scores.total)
    weak = []
    if scores.financial < 50:
        weak.append("재무")
    if scores.growth < 50:
        weak.append("성장성")
    if scores.userfit is not None and scores.userfit < 50:
        weak.append("적합도")
    if not weak:
        return f"{label} — 재무·성장·적합도 균형이 무난합니다."
    return f"{label} — {'·'.join(weak)}이(가) 약해 장기 보유엔 주의가 필요합니다."
