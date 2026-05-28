from dataclasses import dataclass

from accounts.models import InvestmentProfile


ANSWER_SCORES = (1, 3, 5)
SURVEY_QUESTION_IDS = ("q1", "q2", "q3", "q4", "q5", "q6")
WEIGHTED_QUESTION_IDS = {"q5": 2}


@dataclass(frozen=True)
class InvestmentSurveyResult:
    risk_type: str
    risk_score: int
    risk_label: str
    score_breakdown: dict[str, int]


def calculate_investment_profile(answers: dict[str, int]) -> InvestmentSurveyResult:
    score_breakdown = {
        question_id: int(answers[question_id]) * WEIGHTED_QUESTION_IDS.get(question_id, 1)
        for question_id in SURVEY_QUESTION_IDS
    }
    total_score = sum(score_breakdown.values())

    if total_score <= 13:
        risk_type = InvestmentProfile.RiskType.CONSERVATIVE
        risk_label = "안정형"
    elif total_score <= 22:
        risk_type = InvestmentProfile.RiskType.BALANCED
        risk_label = "중립형"
    else:
        risk_type = InvestmentProfile.RiskType.AGGRESSIVE
        risk_label = "공격형"

    return InvestmentSurveyResult(
        risk_type=risk_type,
        risk_score=total_score,
        risk_label=risk_label,
        score_breakdown=score_breakdown,
    )
