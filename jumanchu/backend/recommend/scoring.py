"""장투 점수 산출 — 재무·성장 → 종목 소계(70% 베이스).

※ 정율(Algo) 도메인 산식(`616jy/longterm_score.py`)을 BE가 포팅. matching.py(궁합)와 동일 패턴.
   여기선 **개인 무관한 종목 소계만** 계산한다(궁합 userfit 30%는 ②랭킹에서 결합).
   근거: recommend.LongTermScore.total_score = "종목 소계 (재무+성장)" / 궁합 30%는 docstring으로 확정.

⚠️ 입력 단위는 **%** (예: operating_margin 10.88). DB는 fraction(0.1088) 저장이므로
   호출부(배치)에서 ×100 환산해 넘긴다 — 이 모듈은 환산을 모른다(순수).
"""
from __future__ import annotations

# --- 가중치 (한 곳에서 조정) ---
# 최종 total = 재무×0.30 + 성장×0.40 + 궁합×0.30  (합 1.0).
# stock_subtotal이 (W_FINANCIAL+W_GROWTH)로 정규화 → 소계는 0~100 유지,
# longterm_total에서 ×(1-W_MATCH)=×0.7 되어 원래 비중(재무0.3·성장0.4)으로 복원된다.
# 따라서 W_FINANCIAL + W_GROWTH = 1 - W_MATCH 를 지켜야 비중이 맞물린다.
W_MATCH = 0.30        # 궁합 30% — 확정 (recommend.LongTermScore docstring). ②랭킹에서 사용
W_FINANCIAL = 0.30    # 재무 30% (전체 기준)
W_GROWTH = 0.40       # 성장 40% (전체 기준)


def _linear(value: float | None, at_zero: float, at_full: float) -> float | None:
    """value를 0~100점으로 선형 환산(밖은 clamp). '낮을수록 좋은' 지표는 at_zero>at_full로 방향 반전."""
    if value is None:
        return None
    score = (value - at_zero) / (at_full - at_zero) * 100.0
    return max(0.0, min(100.0, score))


def _avg(values: list[float | None]) -> float | None:
    """None 제외 평균. 전부 None이면 None(데이터 없음)."""
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def financial_score(*, debt_ratio, current_ratio, operating_margin, net_margin, roe) -> float | None:
    """재무 건전성 0~100. 부채↓·유동↑·마진↑·ROE↑ 일수록 고득점. (입력 %)"""
    return _avg([
        _linear(debt_ratio, 200, 0),        # 부채비율 200%→0, 0%→100
        _linear(current_ratio, 0, 200),     # 유동비율 0%→0, 200%→100
        _linear(operating_margin, 0, 30),   # 영업이익률 0%→0, 30%→100
        _linear(net_margin, 0, 25),         # 순이익률 0%→0, 25%→100
        _linear(roe, 0, 20),                # ROE 0%→0, 20%→100
    ])


def growth_score(*, revenue_yoy, operating_profit_yoy, net_profit_yoy) -> float | None:
    """성장성 0~100. YoY 0%→50점, ±30%에서 0/100점. (입력 %)"""
    return _avg([
        _linear(revenue_yoy, -30, 30),
        _linear(operating_profit_yoy, -30, 30),
        _linear(net_profit_yoy, -30, 30),
    ])


def stock_subtotal(financial: float | None, growth: float | None) -> float | None:
    """종목 소계 = 재무·성장 가중평균(= LongTermScore.total_score). 한쪽만 있으면 그 점수."""
    parts = [(financial, W_FINANCIAL), (growth, W_GROWTH)]
    present = [(s, w) for s, w in parts if s is not None]
    if not present:
        return None
    return sum(s * w for s, w in present) / sum(w for _, w in present)


def longterm_total(subtotal: float | None, userfit: float | None) -> float | None:
    """장투 최종 = 소계×(1-W_MATCH) + 궁합×W_MATCH. ②랭킹에서 종목 소계 + 개인 궁합 결합용."""
    if subtotal is None:
        return userfit
    if userfit is None:
        return subtotal
    return subtotal * (1 - W_MATCH) + userfit * W_MATCH
