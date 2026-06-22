from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import InvestmentProfile, User, UserPreferredSector
from portfolio.models import Account
from recommend.models import StockDna
from stocks.models import Stock


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
        self.assertEqual(p.investment_style, '성장 동반형')  # 전부 5점 → 공격·장기
        self.assertIsNotNone(p.profiled_at)
        self.assertEqual(p.onboarding_answers['q5'], 5)

    def test_preferred_sectors_weighted(self):
        self.client.post(self.url, self._payload(), format='json')
        weights = {x.sector: x.weight for x in UserPreferredSector.objects.filter(user=self.user)}
        self.assertEqual(weights['반도체'], Decimal('1.0'))
        self.assertEqual(weights['바이오'], Decimal('0.6'))

    def test_cautious_type(self):
        # 전부 1점 → 위험축 1·기간 1 → 안정·단기 = 신중 탐색형
        self.client.post(self.url, self._payload(q1=1, q2=1, q3=1, q4=1, q5=1, q6=1), format='json')
        p = InvestmentProfile.objects.get(user=self.user)
        self.assertEqual(p.investment_style, '신중 탐색형')

    def test_double_onboarding_returns_409(self):
        self.client.post(self.url, self._payload(), format='json')
        res = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_requires_auth(self):
        self.client.force_authenticate(user=None)
        res = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_signature_picks_best_match(self):
        today = date.today()
        s1 = Stock.objects.create(code='000001', name='고변동', market='KOSPI', currency='KRW', sector='반도체', market_cap=5_000_000)
        s2 = Stock.objects.create(code='000002', name='안정주', market='KOSPI', currency='KRW', sector='금융', market_cap=9_000_000)
        StockDna.objects.create(stock=s1, volatility=Decimal('0.95'), value_score=Decimal('0.2'),
                                growth_score=Decimal('0.9'), stability=Decimal('0.1'), sector='반도체', calculated_date=today)
        StockDna.objects.create(stock=s2, volatility=Decimal('0.1'), value_score=Decimal('0.8'),
                                growth_score=Decimal('0.3'), stability=Decimal('0.9'), sector='금융', calculated_date=today)
        # 안정형(전부 1점) + 관심섹터 금융 → 저변동·고안정 종목이 1등이어야
        res = self.client.post(
            self.url, self._payload(q1=1, q2=1, q3=1, q4=1, q5=1, q6=1, preferred_sectors=['금융']),
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        p = InvestmentProfile.objects.get(user=self.user)
        self.assertEqual(p.signature_stock_id, s2.id)
        self.assertEqual(res.data['profile_stock']['code'], '000002')
        self.assertIn('dna', res.data['profile_stock'])
        self.assertEqual(res.data['investor_type']['type'], '신중 탐색형')
