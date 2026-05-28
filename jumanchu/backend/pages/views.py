from django.views.generic import TemplateView


SURVEY_QUESTIONS = [
    {
        'id': 'q1',
        'label': '문항 1',
        'title': '투자 목적',
        'caption': '주식 추천의 방향을 정하는 첫 기준입니다.',
        'options': [
            {'score': 1, 'title': '안전한 보존', 'detail': '자산 보존과 생활비 보조가 가장 중요합니다.'},
            {'score': 3, 'title': '안정적 초과수익', 'detail': '정기예금보다 약간 높은 수준의 안정적 이익을 기대합니다.'},
            {'score': 5, 'title': '높은 자산 증식', 'detail': '위험을 감수하더라도 높은 자산 성장을 추구합니다.'},
        ],
    },
    {
        'id': 'q2',
        'label': '문항 2',
        'title': '연령',
        'caption': '투자 기간과 변동성 수용 가능성을 함께 봅니다.',
        'options': [
            {'score': 1, 'title': '60대 이상', 'detail': '원금 안정성과 현금 흐름을 우선합니다.'},
            {'score': 3, 'title': '40대에서 50대', 'detail': '안정성과 성장성의 균형을 중시합니다.'},
            {'score': 5, 'title': '20대에서 30대', 'detail': '긴 투자 기간을 활용할 수 있습니다.'},
        ],
    },
    {
        'id': 'q3',
        'label': '문항 3',
        'title': '수입 원천',
        'caption': '소득 안정성은 추천 종목의 리스크 기준에 반영됩니다.',
        'options': [
            {'score': 1, 'title': '불안정하거나 없음', 'detail': '은퇴, 연금, 비정기 수입에 가깝습니다.'},
            {'score': 3, 'title': '비교적 안정적', 'detail': '직장인, 전문직처럼 예측 가능한 수입이 있습니다.'},
            {'score': 5, 'title': '확장 가능성이 높음', 'detail': '사업 또는 자산 수입이 성장할 여지가 있습니다.'},
        ],
    },
    {
        'id': 'q4',
        'label': '문항 4',
        'title': '금융 지식 및 투자 경험',
        'caption': '시장 변화에 대응할 수 있는 수준을 확인합니다.',
        'options': [
            {'score': 1, 'title': '위험자산 경험 없음', 'detail': '주식, 파생상품 등 위험자산 투자 경험이 거의 없습니다.'},
            {'score': 3, 'title': '기본 구조 이해', 'detail': '펀드나 주식 투자 경험이 있고 구조를 어느 정도 이해합니다.'},
            {'score': 5, 'title': '능동적 대응 가능', 'detail': '전문 지식이 있고 시장 변화에 맞춰 판단할 수 있습니다.'},
        ],
    },
    {
        'id': 'q5',
        'label': '문항 5',
        'title': '감내할 수 있는 손실 범위',
        'caption': '핵심 가중치 문항입니다. 이 답변은 2배로 반영됩니다.',
        'weight': 2,
        'options': [
            {'score': 1, 'title': '손실을 원치 않음', 'detail': '원금 보존이 필수이고 1% 손실도 피하고 싶습니다.'},
            {'score': 3, 'title': '10% 미만 감내', 'detail': '일시적인 손실이라면 기다릴 수 있습니다.'},
            {'score': 5, 'title': '30% 이상 감내', 'detail': '높은 수익 가능성이 있다면 큰 변동도 받아들입니다.'},
        ],
    },
    {
        'id': 'q6',
        'label': '문항 6',
        'title': '실제 투자 상황 대응',
        'caption': '투자한 종목이 단기간에 20% 하락했을 때의 행동을 고릅니다.',
        'options': [
            {'score': 1, 'title': '전량 매도', 'detail': '손실을 최소화하기 위해 빠르게 정리합니다.'},
            {'score': 3, 'title': '일부 보유', 'detail': '상황을 지켜보며 비중을 줄이거나 일부만 보유합니다.'},
            {'score': 5, 'title': '추가 매수', 'detail': '평균 단가를 낮추며 회복을 기다립니다.'},
        ],
    },
]

SECTORS = ['반도체', '2차전지', '플랫폼', '바이오', '금융']

HOLDING_PERIODS = [
    {'label': '1개월', 'value': 1},
    {'label': '3개월', 'value': 3},
    {'label': '6개월', 'value': 6},
    {'label': '1년', 'value': 12},
    {'label': '2년', 'value': 24},
]

MARKET_INDICES = [
    {'name': 'KOSPI', 'value': '2,785.92', 'change': '+1.39%'},
    {'name': 'KOSDAQ', 'value': '863.37', 'change': '+0.74%'},
    {'name': 'USD/KRW', 'value': '1,514.65', 'change': '+0.40%'},
]

RECOMMENDATIONS = {
    'CONSERVATIVE': [
        {'name': '삼성전자', 'code': '005930', 'match': 86, 'sector': '반도체', 'theme': '대형 반도체', 'price': '74,200원', 'change': '+0.8%', 'reason': '높은 유동성과 사업 안정성이 안정형 포트폴리오의 중심축에 어울립니다.', 'gradient': 'linear-gradient(135deg, #20c997, #38bdf8)'},
        {'name': 'KT&G', 'code': '033780', 'match': 82, 'sector': '금융', 'theme': '방어 배당', 'price': '94,500원', 'change': '+0.3%', 'reason': '방어적 업종과 배당 매력이 변동성 완화에 도움을 줄 수 있습니다.', 'gradient': 'linear-gradient(135deg, #35f7a7, #64748b)'},
        {'name': 'KB금융', 'code': '105560', 'match': 79, 'sector': '금융', 'theme': '금융 지주', 'price': '78,900원', 'change': '+0.5%', 'reason': '이익 체력과 배당 여력이 안정형 투자자에게 맞는 후보입니다.', 'gradient': 'linear-gradient(135deg, #f7c948, #1f9d55)'},
    ],
    'BALANCED': [
        {'name': 'NAVER', 'code': '035420', 'match': 88, 'sector': '플랫폼', 'theme': '플랫폼 AI', 'price': '192,500원', 'change': '+1.4%', 'reason': '성장 모멘텀과 대형주 안정성을 함께 보는 중립형 후보입니다.', 'gradient': 'linear-gradient(135deg, #03c75a, #00bcd4)'},
        {'name': '삼성SDI', 'code': '006400', 'match': 84, 'sector': '2차전지', 'theme': '배터리 밸류체인', 'price': '401,000원', 'change': '+2.2%', 'reason': '산업 성장성과 변동성을 균형 있게 반영할 수 있습니다.', 'gradient': 'linear-gradient(135deg, #2563eb, #8b5cf6)'},
        {'name': '카카오', 'code': '035720', 'match': 81, 'sector': '플랫폼', 'theme': '콘텐츠 플랫폼', 'price': '48,600원', 'change': '+0.9%', 'reason': '플랫폼 회복 기대와 리스크를 함께 볼 수 있는 균형형 카드입니다.', 'gradient': 'linear-gradient(135deg, #facc15, #f97316)'},
    ],
    'AGGRESSIVE': [
        {'name': 'SK하이닉스', 'code': '000660', 'match': 94, 'sector': '반도체', 'theme': 'AI 반도체', 'price': '198,300원', 'change': '+3.1%', 'reason': 'HBM 수요와 업황 민감도가 높아 공격형 성향과 잘 맞습니다.', 'gradient': 'linear-gradient(135deg, #ff365f, #8b5cf6)'},
        {'name': '셀트리온', 'code': '068270', 'match': 87, 'sector': '바이오', 'theme': '바이오', 'price': '168,300원', 'change': '+2.4%', 'reason': '실적 기대와 이벤트 변동성을 감수할 수 있는 투자자에게 맞습니다.', 'gradient': 'linear-gradient(135deg, #0f6bff, #8b5cf6)'},
        {'name': 'LG에너지솔루션', 'code': '373220', 'match': 85, 'sector': '2차전지', 'theme': '2차전지', 'price': '401,000원', 'change': '+2.2%', 'reason': '수요 회복 기대와 높은 변동성을 함께 가져가는 성장 후보입니다.', 'gradient': 'linear-gradient(135deg, #a50034, #ff7a59)'},
    ],
}


class IndexView(TemplateView):
    template_name = 'pages/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'survey_questions': SURVEY_QUESTIONS,
            'sectors': SECTORS,
            'holding_periods': HOLDING_PERIODS,
            'market_indices': MARKET_INDICES,
            'recommendations': RECOMMENDATIONS,
            'onboarding_api_url': '/api/v1/auth/onboarding/',
        })
        return context
