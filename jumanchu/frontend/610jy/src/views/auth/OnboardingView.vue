<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ── 온보딩 설문 (백엔드 pages/views.py SURVEY_QUESTIONS / PPT image1·7·11) ──
// 흐름: 사전 설정(관심 섹터·보유 기간) → 6문항 설문(1/3/5점, q5 ×2) → 결과(성향+대표 종목)
// 제출: POST /api/v1/auth/onboarding { survey_answers, preferred_period, preferred_sector }

// 관심 섹터 (복수, PPT image1) · 보유 기간 (단일, 백엔드 HOLDING_PERIODS)
const sectors = ['반도체', '바이오', '금융', 'IT·소프트웨어', '에너지', '화학', '자동차', '소비재', '통신', '부동산']
const periods = [
  { label: '1개월', value: 1 }, { label: '3개월', value: 3 }, { label: '6개월', value: 6 },
  { label: '1년', value: 12 }, { label: '2년+', value: 24 },
]
const selectedSectors = ref([])
const selectedPeriod = ref(null)

function toggleSector(s) {
  const i = selectedSectors.value.indexOf(s)
  if (i >= 0) selectedSectors.value.splice(i, 1)
  else selectedSectors.value.push(s)
}

// 설문 6문항 (백엔드 SURVEY_QUESTIONS 그대로)
const questions = [
  { id: 'q1', title: '투자 목적', caption: '주식 추천의 방향을 정하는 첫 기준입니다.', options: [
    { score: 1, title: '안전한 보존', detail: '자산 보존과 생활비 보조가 가장 중요합니다.' },
    { score: 3, title: '안정적 초과수익', detail: '정기예금보다 약간 높은 수준의 안정적 이익을 기대합니다.' },
    { score: 5, title: '높은 자산 증식', detail: '위험을 감수하더라도 높은 자산 성장을 추구합니다.' },
  ] },
  { id: 'q2', title: '연령', caption: '투자 기간과 변동성 수용 가능성을 함께 봅니다.', options: [
    { score: 1, title: '60대 이상', detail: '원금 안정성과 현금 흐름을 우선합니다.' },
    { score: 3, title: '40대에서 50대', detail: '안정성과 성장성의 균형을 중시합니다.' },
    { score: 5, title: '20대에서 30대', detail: '긴 투자 기간을 활용할 수 있습니다.' },
  ] },
  { id: 'q3', title: '수입 원천', caption: '소득 안정성은 추천 종목의 리스크 기준에 반영됩니다.', options: [
    { score: 1, title: '불안정하거나 없음', detail: '은퇴, 연금, 비정기 수입에 가깝습니다.' },
    { score: 3, title: '비교적 안정적', detail: '직장인, 전문직처럼 예측 가능한 수입이 있습니다.' },
    { score: 5, title: '확장 가능성이 높음', detail: '사업 또는 자산 수입이 성장할 여지가 있습니다.' },
  ] },
  { id: 'q4', title: '금융 지식 및 투자 경험', caption: '시장 변화에 대응할 수 있는 수준을 확인합니다.', options: [
    { score: 1, title: '위험자산 경험 없음', detail: '주식, 파생상품 등 위험자산 투자 경험이 거의 없습니다.' },
    { score: 3, title: '기본 구조 이해', detail: '펀드나 주식 투자 경험이 있고 구조를 어느 정도 이해합니다.' },
    { score: 5, title: '능동적 대응 가능', detail: '전문 지식이 있고 시장 변화에 맞춰 판단할 수 있습니다.' },
  ] },
  { id: 'q5', title: '감내할 수 있는 손실 범위', caption: '핵심 가중치 문항입니다. 이 답변은 2배로 반영됩니다.', weight: 2, options: [
    { score: 1, title: '손실을 원치 않음', detail: '원금 보존이 필수이고 1% 손실도 피하고 싶습니다.' },
    { score: 3, title: '10% 미만 감내', detail: '일시적인 손실이라면 기다릴 수 있습니다.' },
    { score: 5, title: '30% 이상 감내', detail: '높은 수익 가능성이 있다면 큰 변동도 받아들입니다.' },
  ] },
  { id: 'q6', title: '실제 투자 상황 대응', caption: '투자한 종목이 단기간에 20% 하락했을 때의 행동을 고릅니다.', options: [
    { score: 1, title: '전량 매도', detail: '손실을 최소화하기 위해 빠르게 정리합니다.' },
    { score: 3, title: '일부 보유', detail: '상황을 지켜보며 비중을 줄이거나 일부만 보유합니다.' },
    { score: 5, title: '추가 매수', detail: '평균 단가를 낮추며 회복을 기다립니다.' },
  ] },
]
const answers = ref({})

// 결과: 성향별 대표 종목 (백엔드 RECOMMENDATIONS)
const recommendations = {
  CONSERVATIVE: [
    { name: '삼성전자', code: '005930', match: 86, theme: '대형 반도체', price: '74,200원', reason: '높은 유동성과 사업 안정성이 안정형 포트폴리오의 중심축에 어울립니다.' },
    { name: 'KT&G', code: '033780', match: 82, theme: '방어 배당', price: '94,500원', reason: '방어적 업종과 배당 매력이 변동성 완화에 도움을 줄 수 있습니다.' },
    { name: 'KB금융', code: '105560', match: 79, theme: '금융 지주', price: '78,900원', reason: '이익 체력과 배당 여력이 안정형 투자자에게 맞는 후보입니다.' },
  ],
  BALANCED: [
    { name: 'NAVER', code: '035420', match: 88, theme: '플랫폼 AI', price: '192,500원', reason: '성장 모멘텀과 대형주 안정성을 함께 보는 중립형 후보입니다.' },
    { name: '삼성SDI', code: '006400', match: 84, theme: '배터리 밸류체인', price: '401,000원', reason: '산업 성장성과 변동성을 균형 있게 반영할 수 있습니다.' },
    { name: '카카오', code: '035720', match: 81, theme: '콘텐츠 플랫폼', price: '48,600원', reason: '플랫폼 회복 기대와 리스크를 함께 볼 수 있는 균형형 카드입니다.' },
  ],
  AGGRESSIVE: [
    { name: 'SK하이닉스', code: '000660', match: 94, theme: 'AI 반도체', price: '198,300원', reason: 'HBM 수요와 업황 민감도가 높아 공격형 성향과 잘 맞습니다.' },
    { name: '셀트리온', code: '068270', match: 87, theme: '바이오', price: '168,300원', reason: '실적 기대와 이벤트 변동성을 감수할 수 있는 투자자에게 맞습니다.' },
    { name: 'LG에너지솔루션', code: '373220', match: 85, theme: '2차전지', price: '401,000원', reason: '수요 회복 기대와 높은 변동성을 함께 가져가는 성장 후보입니다.' },
  ],
}
const riskMeta = {
  CONSERVATIVE: { label: '안정형', emoji: '🛡️', desc: '원금 보존과 안정적 수익을 우선하는 유형이에요.' },
  BALANCED: { label: '중립형', emoji: '⚖️', desc: '수익과 안정성의 균형을 추구하는 유형이에요.' },
  AGGRESSIVE: { label: '공격형', emoji: '🚀', desc: '높은 변동성을 감수하고 성장을 추구하는 유형이에요.' },
}

// step: 0 = 사전 설정, 1~6 = 문항, 7 = 결과
const step = ref(0)
const totalQuestions = questions.length
const currentQuestion = computed(() => questions[step.value - 1])

const runningScore = computed(() =>
  questions.reduce((sum, q) => sum + (answers.value[q.id] ? answers.value[q.id] * (q.weight || 1) : 0), 0),
)
const totalScore = computed(() => runningScore.value)
const riskKey = computed(() => (totalScore.value <= 13 ? 'CONSERVATIVE' : totalScore.value <= 22 ? 'BALANCED' : 'AGGRESSIVE'))
const result = computed(() => ({ ...riskMeta[riskKey.value], score: totalScore.value, recs: recommendations[riskKey.value] }))
const topPick = computed(() => result.value.recs[0])

const canProceed = computed(() => {
  if (step.value === 0) return true // 사전 설정은 선택 사항
  if (step.value <= totalQuestions) return answers.value[currentQuestion.value.id] != null
  return true
})

function select(score) { answers.value[currentQuestion.value.id] = score }
function next() {
  if (!canProceed.value) return
  if (step.value < totalQuestions + 1) step.value++
}
function prev() { if (step.value > 0) step.value-- }

function finish() {
  // TODO: POST /api/v1/auth/onboarding
  // { survey_answers: answers, preferred_period: selectedPeriod, preferred_sector: selectedSectors.join(',') }
  router.push('/')
}
</script>

<template>
  <div class="auth-shell">
    <div class="onboarding-card panel">
      <header class="ob-header">
        <p class="ob-sub">회원가입 후 최초 로그인 시 온보딩 설문 필수 진행</p>
        <h1 class="ob-title">온보딩</h1>
      </header>

      <!-- 진행 바 -->
      <div v-if="step >= 1 && step <= totalQuestions" class="ob-progress-row">
        <span>문항 {{ step }} / {{ totalQuestions }}</span>
        <span class="ob-score">누적 점수 {{ runningScore }}점</span>
      </div>
      <div v-if="step >= 1 && step <= totalQuestions" class="ob-bar">
        <div class="ob-bar-fill" :style="{ width: `${(step / totalQuestions) * 100}%` }"></div>
      </div>

      <!-- Step 0: 사전 설정 -->
      <div v-if="step === 0" class="ob-step">
        <span class="ob-chip">사전 설정</span>
        <h2>관심 섹터 &amp; 선호 보유 기간</h2>
        <p class="ob-caption">투자 추천에 반영될 나의 관심 영역을 선택해주세요.</p>

        <p class="ob-field-label">관심 섹터 <em>복수 선택</em></p>
        <div class="chip-wrap">
          <button
            v-for="s in sectors"
            :key="s"
            type="button"
            class="opt-chip"
            :class="{ 'is-selected': selectedSectors.includes(s) }"
            @click="toggleSector(s)"
          >{{ s }}</button>
        </div>

        <p class="ob-field-label">선호 보유 기간 <em>단일 선택</em></p>
        <div class="chip-wrap">
          <button
            v-for="p in periods"
            :key="p.value"
            type="button"
            class="opt-chip"
            :class="{ 'is-selected': selectedPeriod === p.value }"
            @click="selectedPeriod = p.value"
          >{{ p.label }}</button>
        </div>
      </div>

      <!-- Step 1~6: 설문 문항 -->
      <div v-else-if="step <= totalQuestions" class="ob-step">
        <span class="ob-chip">문항 {{ step }}</span>
        <h2>{{ currentQuestion.title }}</h2>
        <p class="ob-caption">{{ currentQuestion.caption }}</p>
        <div class="opt-list">
          <button
            v-for="o in currentQuestion.options"
            :key="o.score"
            type="button"
            class="opt-row"
            :class="{ 'is-selected': answers[currentQuestion.id] === o.score }"
            @click="select(o.score)"
          >
            <span class="opt-score">{{ o.score }}점</span>
            <span class="opt-text">
              <strong>{{ o.title }}</strong>
              <em>{{ o.detail }}</em>
            </span>
          </button>
        </div>
      </div>

      <!-- Step 7: 결과 -->
      <div v-else class="ob-step ob-result">
        <div class="res-emoji">{{ result.emoji }}</div>
        <p class="res-eyebrow">나의 투자 성향</p>
        <h2 class="res-type">{{ result.label }} <span class="res-score">{{ result.score }}점</span></h2>
        <p class="ob-caption">{{ result.desc }}</p>

        <div class="res-pick">
          <p class="res-pick-label">당신과 가장 잘 맞는 종목</p>
          <div class="res-pick-card">
            <div class="rp-top">
              <strong>{{ topPick.name }}</strong>
              <span class="rp-match">♥ 궁합 {{ topPick.match }}점</span>
            </div>
            <p class="rp-meta">{{ topPick.code }} · {{ topPick.theme }} · {{ topPick.price }}</p>
            <p class="rp-reason">{{ topPick.reason }}</p>
          </div>
        </div>

        <p class="res-more-label">이런 종목도 추천해요</p>
        <div class="res-more">
          <div v-for="r in result.recs.slice(1)" :key="r.code" class="res-more-item">
            <span class="rm-name">{{ r.name }}</span>
            <span class="rm-theme">{{ r.theme }}</span>
            <span class="rm-match">궁합 {{ r.match }}</span>
          </div>
        </div>
      </div>

      <!-- 네비게이션 -->
      <div class="ob-nav">
        <button v-if="step > 0 && step <= totalQuestions + 1" class="back-btn" type="button" @click="prev">← 이전</button>
        <button v-if="step <= totalQuestions" class="primary-action next-btn" type="button" :disabled="!canProceed" @click="next">
          {{ step === totalQuestions ? '결과 확인' : '다음 →' }}
        </button>
        <button v-else class="primary-action next-btn" type="button" @click="finish">주만추 시작하기 🎉</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-shell { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
.onboarding-card { width: 100%; max-width: 520px; padding: 32px; }

.ob-header { text-align: center; margin-bottom: 20px; }
.ob-sub { margin: 0; color: var(--muted); font-size: 12px; font-weight: 900; }
.ob-title {
  margin: 6px 0 0; font-size: 30px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

.ob-progress-row { display: flex; align-items: center; justify-content: space-between; color: var(--muted); font-size: 13px; font-weight: 900; margin-bottom: 8px; }
.ob-score { color: var(--accent); }
.ob-bar { height: 6px; border-radius: 999px; background: rgba(180, 200, 255, 0.4); overflow: hidden; margin-bottom: 20px; }
.ob-bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--purple)); transition: width 0.25s ease; }

.ob-step { display: grid; gap: 12px; margin-bottom: 22px; }
.ob-chip { justify-self: start; padding: 4px 12px; border-radius: 999px; background: rgba(49, 93, 255, 0.1); color: var(--accent); font-size: 12px; font-weight: 900; }
.ob-step h2 { margin: 4px 0 0; font-size: 22px; }
.ob-caption { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.55; word-break: keep-all; }
.ob-field-label { margin: 10px 0 0; color: var(--ink); font-size: 13px; font-weight: 900; }
.ob-field-label em { font-style: normal; color: var(--faint); font-size: 11px; margin-left: 6px; }

.chip-wrap { display: flex; flex-wrap: wrap; gap: 8px; }
.opt-chip {
  padding: 8px 14px; border-radius: 999px;
  border: 2px solid var(--glass-border); background: rgba(255, 255, 255, 0.5);
  color: var(--muted); font-size: 13px; font-weight: 900;
  transition: border-color 0.16s ease, background 0.16s ease, color 0.16s ease;
}
.opt-chip.is-selected { border-color: var(--accent); background: rgba(49, 93, 255, 0.08); color: var(--accent); }

.opt-list { display: grid; gap: 10px; }
.opt-row {
  display: grid; grid-template-columns: 44px 1fr; align-items: center; gap: 14px;
  padding: 14px; border-radius: var(--radius);
  border: 2px solid var(--glass-border); background: rgba(255, 255, 255, 0.48); text-align: left;
  transition: border-color 0.16s ease, background 0.16s ease;
}
.opt-row.is-selected { border-color: var(--accent); background: rgba(49, 93, 255, 0.06); }
.opt-score {
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: rgba(49, 93, 255, 0.1); color: var(--accent); font-size: 13px; font-weight: 900;
}
.opt-row.is-selected .opt-score { background: linear-gradient(135deg, var(--accent), var(--purple)); color: #fff; }
.opt-text { display: flex; flex-direction: column; gap: 3px; }
.opt-text strong { color: var(--ink); font-size: 15px; }
.opt-text em { font-style: normal; color: var(--muted); font-size: 12px; line-height: 1.4; word-break: keep-all; }

/* 결과 */
.ob-result { text-align: center; justify-items: center; }
.res-emoji { font-size: 48px; }
.res-eyebrow { margin: 0; color: var(--muted); font-size: 13px; font-weight: 900; }
.res-type { margin: 2px 0 0; font-size: 26px; }
.res-score { color: var(--accent); font-size: 18px; }
.res-pick { width: 100%; margin-top: 8px; }
.res-pick-label { margin: 0 0 8px; color: var(--ink); font-size: 13px; font-weight: 900; }
.res-pick-card { padding: 16px; border-radius: var(--radius); background: linear-gradient(135deg, rgba(49,93,255,0.08), rgba(125,78,232,0.08)); border: 1px solid rgba(49, 93, 255, 0.2); text-align: left; }
.rp-top { display: flex; align-items: center; justify-content: space-between; }
.rp-top strong { font-size: 18px; color: var(--ink); }
.rp-match { color: var(--negative); font-size: 13px; font-weight: 900; }
.rp-meta { margin: 4px 0 8px; color: var(--muted); font-size: 12px; }
.rp-reason { margin: 0; color: var(--text); font-size: 13px; line-height: 1.55; word-break: keep-all; }
.res-more-label { margin: 8px 0 0; align-self: start; color: var(--muted); font-size: 12px; font-weight: 900; }
.res-more { width: 100%; display: grid; gap: 8px; }
.res-more-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: var(--radius); background: rgba(255, 255, 255, 0.5); border: 1px solid var(--glass-border); }
.rm-name { color: var(--ink); font-size: 14px; font-weight: 900; }
.rm-theme { color: var(--muted); font-size: 12px; }
.rm-match { margin-left: auto; color: var(--accent); font-size: 12px; font-weight: 900; }

.ob-nav { display: flex; align-items: center; gap: 10px; }
.back-btn { min-height: 48px; padding: 0 18px; border-radius: var(--radius); border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.52); color: var(--muted); font-size: 14px; font-weight: 900; flex-shrink: 0; }
.back-btn:hover { background: rgba(255, 255, 255, 0.72); color: var(--ink); }
.next-btn { flex: 1; width: auto; }
.next-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
