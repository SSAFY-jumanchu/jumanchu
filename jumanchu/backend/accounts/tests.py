from django.test import SimpleTestCase

from accounts.models import InvestmentProfile
from accounts.services import calculate_investment_profile


class InvestmentSurveyScoringTests(SimpleTestCase):
    def test_loss_tolerance_answer_has_double_weight(self):
        result = calculate_investment_profile({
            'q1': 1,
            'q2': 1,
            'q3': 1,
            'q4': 1,
            'q5': 5,
            'q6': 1,
        })

        self.assertEqual(result.score_breakdown['q5'], 10)
        self.assertEqual(result.risk_score, 15)

    def test_conservative_profile_maps_to_13_or_less(self):
        result = calculate_investment_profile({
            'q1': 1,
            'q2': 1,
            'q3': 1,
            'q4': 1,
            'q5': 3,
            'q6': 3,
        })

        self.assertEqual(result.risk_score, 13)
        self.assertEqual(result.risk_type, InvestmentProfile.RiskType.CONSERVATIVE)

    def test_balanced_profile_maps_to_14_through_22(self):
        result = calculate_investment_profile({
            'q1': 3,
            'q2': 3,
            'q3': 3,
            'q4': 3,
            'q5': 3,
            'q6': 3,
        })

        self.assertEqual(result.risk_score, 21)
        self.assertEqual(result.risk_type, InvestmentProfile.RiskType.BALANCED)

    def test_aggressive_profile_maps_to_23_or_more(self):
        result = calculate_investment_profile({
            'q1': 5,
            'q2': 5,
            'q3': 5,
            'q4': 5,
            'q5': 5,
            'q6': 5,
        })

        self.assertEqual(result.risk_score, 35)
        self.assertEqual(result.risk_type, InvestmentProfile.RiskType.AGGRESSIVE)
