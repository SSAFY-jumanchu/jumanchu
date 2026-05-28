<script setup>
import { computed, reactive, ref } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const questions = [
  {
    id: 'q1',
    label: '문항 1',
    title: '투자 목적',
    accent: 'pink',
    options: [
      { score: 1, title: '안전한 보존', detail: '자산 보존과 생활비 보조가 가장 중요해요.' },
      { score: 3, title: '안정적 초과수익', detail: '정기예금보다 조금 높은 수익을 기대해요.' },
      { score: 5, title: '높은 자산 증식', detail: '위험을 감수하고 더 큰 성장성을 추구해요.' },
    ],
  },
  {
    id: 'q2',
    label: '문항 2',
    title: '연령',
    accent: 'blue',
    options: [
      { score: 1, title: '60대 이상', detail: '원금 안정성과 현금 흐름을 우선해요.' },
      { score: 3, title: '40대에서 50대', detail: '안정성과 성장성의 균형이 필요해요.' },
      { score: 5, title: '20대에서 30대', detail: '긴 투자 기간을 활용할 수 있어요.' },
    ],
  },
  {
    id: 'q3',
    label: '문항 3',
    title: '수입 원천',
    accent: 'green',
    options: [
      { score: 1, title: '불안정하거나 없음', detail: '은퇴, 연금, 비정기 수입에 가까워요.' },
      { score: 3, title: '비교적 안정적', detail: '직장인, 전문직처럼 예측 가능한 수입이 있어요.' },
      { score: 5, title: '확장 가능성이 높음', detail: '사업 또는 자산 수입이 성장할 여지가 있어요.' },
    ],
  },
  {
    id: 'q4',
    label: '문항 4',
    title: '금융 지식 및 투자 경험',
    accent: 'purple',
    options: [
      { score: 1, title: '경험 없음', detail: '주식, 파생상품 등 위험자산 경험이 거의 없어요.' },
      { score: 3, title: '기본 구조 이해', detail: '펀드나 주식 투자 경험이 있고 구조를 이해해요.' },
      { score: 5, title: '능동적 대응 가능', detail: '시장 변화에 맞춰 스스로 판단하고 조정할 수 있어요.' },
    ],
  },
  {
    id: 'q5',
    label: '문항 5',
    title: '감내할 수 있는 손실 범위',
    accent: 'red',
    weight: 2,
    options: [
      { score: 1, title: '손실을 원치 않음', detail: '원금 보존이 필수이고 1% 손실도 피하고 싶어요.' },
      { score: 3, title: '10% 미만 감내', detail: '일시적 조정이라면 기다릴 수 있어요.' },
      { score: 5, title: '30% 이상 감내', detail: '높은 수익 가능성이 있다면 큰 변동도 받아들여요.' },
    ],
  },
  {
    id: 'q6',
    label: '문항 6',
    title: '실제 투자 상황 대응',
    caption: '투자한 종목이 단기간에 20% 하락했을 때',
    accent: 'cyan',
    options: [
      { score: 1, title: '전량 매도', detail: '손실 확대를 막기 위해 빠르게 정리해요.' },
      { score: 3, title: '일부 보유', detail: '상황을 지켜보며 비중을 줄여요.' },
      { score: 5, title: '추가 매수', detail: '평균 단가를 낮추며 회복을 기다려요.' },
    ],
  },
]

const sectors = ['반도체', '2차전지', '플랫폼', '바이오', '금융']
const holdingPeriods = [
  { label: '1개월', value: 1 },
  { label: '3개월', value: 3 },
  { label: '6개월', value: 6 },
  { label: '1년', value: 12 },
  { label: '2년', value: 24 },
]

const recommendations = {
  CONSERVATIVE: [
    { name: '삼성전자', code: '005930', match: 86, theme: '대형주', reason: '높은 유동성과 사업 안정성이 안정형 포트폴리오의 중심축에 어울려요.' },
    { name: 'KT&G', code: '033780', match: 82, theme: '배당', reason: '방어적 업종과 배당 매력이 변동성 완화에 도움을 줄 수 있어요.' },
  ],
  BALANCED: [
    { name: 'NAVER', code: '035420', match: 88, theme: '플랫폼 AI', reason: '성장 모멘텀과 대형주 안정성을 함께 보는 중립형 후보예요.' },
    { name: '삼성SDI', code: '006400', match: 84, theme: '2차전지', reason: '산업 성장성과 변동성을 균형 있게 반영할 수 있어요.' },
  ],
  AGGRESSIVE: [
    { name: 'SK하이닉스', code: '000660', match: 94, theme: 'AI 반도체', reason: 'HBM 수요와 업황 민감도가 높아 공격형 성향과 잘 맞아요.' },
    { name: '셀트리온', code: '068270', match: 87, theme: '바이오', reason: '실적 기대와 이벤트 변동성을 감수할 수 있는 투자자에게 맞아요.' },
  ],
}

const answers = reactive({})
const currentStep = ref(0)
const selectedSector = ref('반도체')
const preferredPeriod = ref(12)
const apiStatus = ref('idle')
const apiMessage = ref('')
const savedResponse = ref(null)

const currentQuestion = computed(() => questions[currentStep.value])
const isResultStep = computed(() => currentStep.value >= questions.length)
const answeredCount = computed(() => questions.filter((question) => answers[question.id]).length)
const progressPercent = computed(() => Math.round((answeredCount.value / questions.length) * 100))
const canSubmit = computed(() => answeredCount.value === questions.length)
const selectedAnswer = computed(() => currentQuestion.value ? answers[currentQuestion.value.id] : null)

const weightedBreakdown = computed(() => {
  return questions.reduce((breakdown, question) => {
    const score = Number(answers[question.id] || 0)
    breakdown[question.id] = score * (question.weight || 1)
    return breakdown
  }, {})
})

const totalScore = computed(() => {
  return Object.values(weightedBreakdown.value).reduce((sum, score) => sum + score, 0)
})

const riskProfile = computed(() => {
  const score = totalScore.value

  if (score <= 13) {
    return {
      code: 'CONSERVATIVE',
      label: '안정형',
      english: 'Conservative',
      description: '손실 방어와 꾸준한 현금 흐름을 먼저 확인하는 유형',
      gradient: 'linear-gradient(135deg, #26d39b 0%, #38bdf8 100%)',
      period: '장기 분산',
    }
  }

  if (score <= 22) {
    return {
      code: 'BALANCED',
      label: '중립형',
      english: 'Balanced',
      description: '안정성과 성장성을 함께 비교하며 비중을 조절하는 유형',
      gradient: 'linear-gradient(135deg, #38bdf8 0%, #8b5cf6 100%)',
      period: '균형 성장',
    }
  }

  return {
    code: 'AGGRESSIVE',
    label: '공격형',
    english: 'Aggressive',
    description: '높은 변동성을 감수하고 성장 모멘텀을 적극적으로 찾는 유형',
    gradient: 'linear-gradient(135deg, #ff365f 0%, #ff3d8b 48%, #8b5cf6 100%)',
    period: '고성장 탐색',
  }
})

const activeRecommendations = computed(() => recommendations[riskProfile.value.code])

function chooseOption(questionId, score) {
  answers[questionId] = score
}

function goNext() {
  if (!selectedAnswer.value) return
  if (currentStep.value < questions.length - 1) {
    currentStep.value += 1
    return
  }
  submitSurvey()
}

function goPrevious() {
  if (isResultStep.value) {
    currentStep.value = questions.length - 1
    return
  }
  currentStep.value = Math.max(0, currentStep.value - 1)
}

function restartSurvey() {
  currentStep.value = 0
  apiStatus.value = 'idle'
  apiMessage.value = ''
  savedResponse.value = null
}

async function submitSurvey() {
  if (!canSubmit.value) return

  currentStep.value = questions.length
  apiStatus.value = 'saving'
  apiMessage.value = '성향 결과를 저장하고 있어요.'

  const token = localStorage.getItem('access') || localStorage.getItem('accessToken')
  const payload = {
    survey_answers: Object.fromEntries(
      questions.map((question) => [question.id, Number(answers[question.id])]),
    ),
    investment_style: riskProfile.value.label,
    preferred_period: preferredPeriod.value,
    preferred_sector: selectedSector.value,
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/onboarding/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    savedResponse.value = await response.json()
    apiStatus.value = 'saved'
    apiMessage.value = '성향 결과가 저장됐어요.'
  } catch (error) {
    apiStatus.value = 'local'
    apiMessage.value = '로그인 세션이 없어서 화면에서 먼저 계산했어요.'
  }
}
</script>

<template>
  <main class="app-screen">
    <div class="laser-field" aria-hidden="true">
      <svg viewBox="0 0 1440 760" preserveAspectRatio="none">
        <path class="laser-glow" d="M-80 560 C 170 330 270 650 470 390 S 820 80 1050 290 S 1320 600 1520 220" />
        <path class="laser-core" d="M-80 560 C 170 330 270 650 470 390 S 820 80 1050 290 S 1320 600 1520 220" />
        <path class="laser-trace" d="M-80 560 C 170 330 270 650 470 390 S 820 80 1050 290 S 1320 600 1520 220" />
      </svg>
    </div>

    <header class="topbar">
      <a class="brand" href="#" aria-label="주만추 홈">주만추</a>
      <nav class="menu" aria-label="주요 메뉴">
        <a href="#survey" class="active">성향 분석</a>
        <a href="#recommend-preview">추천 후보</a>
        <a href="#market-pulse">시장 펄스</a>
      </nav>
      <div class="market-time">
        <span class="live-dot" aria-hidden="true"></span>
        KIS 연결 준비
      </div>
    </header>

    <section class="intro-layout" id="survey">
      <aside class="intro-copy" aria-label="서비스 소개">
        <div class="eyebrow">
          <span class="live-dot" aria-hidden="true"></span>
          투자 성향 기반 종목 매칭
        </div>
        <h1>
          나와 맞는<br />
          주식을 먼저<br />
          걸러냅니다
        </h1>
        <p>
          여섯 개 답변으로 위험 감내도와 행동 패턴을 계산하고, 한국투자증권 시세 데이터와 연결할 추천 기준을 만듭니다.
        </p>

        <div class="profile-grid" aria-label="현재 분석 요약">
          <div class="mini-metric">
            <span>진행률</span>
            <strong>{{ progressPercent }}%</strong>
          </div>
          <div class="mini-metric">
            <span>가중 점수</span>
            <strong>{{ totalScore }}</strong>
          </div>
          <div class="mini-metric wide" :style="{ '--profile-gradient': riskProfile.gradient }">
            <span>예상 성향</span>
            <strong>{{ riskProfile.label }}</strong>
            <small>{{ riskProfile.description }}</small>
          </div>
        </div>

        <div class="market-strip" id="market-pulse" aria-label="시장 요약">
          <div>
            <span>KOSPI</span>
            <strong>2,785.92</strong>
            <em class="up">+1.39%</em>
          </div>
          <div>
            <span>KOSDAQ</span>
            <strong>863.37</strong>
            <em class="up">+0.74%</em>
          </div>
          <div>
            <span>USD/KRW</span>
            <strong>1,514.65</strong>
            <em class="up">+0.40%</em>
          </div>
        </div>
      </aside>

      <section class="survey-panel" aria-label="투자 성향 설문">
        <div class="survey-head">
          <div>
            <span class="step-label">{{ isResultStep ? '결과' : currentQuestion.label }}</span>
            <h2>{{ isResultStep ? '추천 준비 완료' : currentQuestion.title }}</h2>
            <p v-if="!isResultStep && currentQuestion.caption">{{ currentQuestion.caption }}</p>
          </div>
          <div class="score-ring" aria-label="가중 점수">
            <strong>{{ totalScore }}</strong>
            <span>score</span>
          </div>
        </div>

        <div class="progress-track" aria-hidden="true">
          <span :style="{ width: `${progressPercent}%` }"></span>
        </div>

        <template v-if="!isResultStep">
          <div class="option-list" :data-accent="currentQuestion.accent">
            <button
              v-for="option in currentQuestion.options"
              :key="option.score"
              type="button"
              class="answer-option"
              :class="{ selected: answers[currentQuestion.id] === option.score }"
              @click="chooseOption(currentQuestion.id, option.score)"
            >
              <span class="option-score">{{ option.score }}점</span>
              <span class="option-copy">
                <strong>{{ option.title }}</strong>
                <small>{{ option.detail }}</small>
              </span>
            </button>
          </div>

          <div class="preference-row">
            <div>
              <span class="field-label">관심 섹터</span>
              <div class="segmented">
                <button
                  v-for="sector in sectors"
                  :key="sector"
                  type="button"
                  :class="{ active: selectedSector === sector }"
                  @click="selectedSector = sector"
                >
                  {{ sector }}
                </button>
              </div>
            </div>
            <div>
              <span class="field-label">선호 보유 기간</span>
              <div class="segmented compact">
                <button
                  v-for="period in holdingPeriods"
                  :key="period.value"
                  type="button"
                  :class="{ active: preferredPeriod === period.value }"
                  @click="preferredPeriod = period.value"
                >
                  {{ period.label }}
                </button>
              </div>
            </div>
          </div>

          <div class="panel-actions">
            <button type="button" class="ghost-btn" :disabled="currentStep === 0" @click="goPrevious">
              이전
            </button>
            <button type="button" class="primary-btn" :disabled="!selectedAnswer" @click="goNext">
              {{ currentStep === questions.length - 1 ? '결과 보기' : '다음' }}
            </button>
          </div>
        </template>

        <template v-else>
          <div class="result-board" id="recommend-preview">
            <div class="result-card" :style="{ '--result-gradient': riskProfile.gradient }">
              <span>{{ riskProfile.english }}</span>
              <strong>{{ riskProfile.label }}</strong>
              <p>{{ riskProfile.description }}</p>
            </div>

            <div class="score-breakdown" aria-label="문항별 가중 점수">
              <div v-for="question in questions" :key="question.id">
                <span>{{ question.label }}</span>
                <strong>{{ weightedBreakdown[question.id] }}</strong>
              </div>
            </div>

            <div class="recommend-stack">
              <article
                v-for="stock in activeRecommendations"
                :key="stock.code"
                class="stock-card"
              >
                <div>
                  <span class="stock-theme">{{ stock.theme }}</span>
                  <h3>{{ stock.name }}</h3>
                  <p>{{ stock.code }}</p>
                </div>
                <div class="stock-match">
                  <strong>{{ stock.match }}</strong>
                  <span>match</span>
                </div>
                <p class="stock-reason">{{ stock.reason }}</p>
              </article>
            </div>

            <div class="api-note" :class="apiStatus">
              {{ apiMessage }}
            </div>
          </div>

          <div class="panel-actions">
            <button type="button" class="ghost-btn" @click="goPrevious">답변 수정</button>
            <button type="button" class="primary-btn" @click="restartSurvey">처음부터</button>
          </div>
        </template>
      </section>
    </section>
  </main>
</template>
