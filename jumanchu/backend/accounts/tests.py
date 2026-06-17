from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import InvestmentProfile, User, UserPreferredSector
from portfolio.models import Account


# TODO(auth): 인증 플로우 단위 테스트 (회원가입/로그인/refresh 회전/logout blacklist/중복 닉네임)


class OnboardingTests(APITestCase):
    url = '/api/v1/auth/onboarding/'

    def setUp(self):
        self.user = User.objects.create_user(
            email='t@test.com', username='t@test.com', nickname='tester',
            birth_year=1995, password='pw12345678',
        )
        self.account = Account.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)

    def _payload(self, **over):
        data = {
            'q1': 5, 'q2': 5, 'q3': 5, 'q4': 5, 'q5': 5, 'q6': 5,
            'preferred_sectors': ['반도체', '바이오'], 'preferred_period': 12,
        }
        data.update(over)
        return data

    def test_creates_profile_and_vectors(self):
        res = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        p = InvestmentProfile.objects.get(user=self.user)
        self.assertEqual(
            (p.risk_tolerance, p.experience, p.loss_aversion, p.investment_term, p.behavior),
            (5, 5, 5, 5, 5),  # (q1 5 + q4 5)//2=5, 나머지 1:1
        )
        self.assertEqual(p.risk_type, InvestmentProfile.RiskType.AGGRESSIVE)  # 총점 35
        self.assertIsNotNone(p.profiled_at)
        self.assertEqual(p.onboarding_answers['q5'], 5)

    def test_preferred_sectors_weighted(self):
        self.client.post(self.url, self._payload(), format='json')
        weights = {x.sector: x.weight for x in UserPreferredSector.objects.filter(user=self.user)}
        self.assertEqual(weights['반도체'], Decimal('1.0'))
        self.assertEqual(weights['바이오'], Decimal('0.6'))

    def test_conservative_grade(self):
        # 전부 1점 → 총점 5 + 1*2 = 7 → 안정형
        self.client.post(self.url, self._payload(q1=1, q2=1, q3=1, q4=1, q5=1, q6=1), format='json')
        p = InvestmentProfile.objects.get(user=self.user)
        self.assertEqual(p.risk_type, InvestmentProfile.RiskType.CONSERVATIVE)

    def test_double_onboarding_returns_409(self):
        self.client.post(self.url, self._payload(), format='json')
        res = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_requires_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
