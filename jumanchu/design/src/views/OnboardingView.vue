<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

// ===== Step 0: 섹터 & 보유기간 =====
const sectors = [
  '반도체', '바이오', '금융', 'IT·소프트웨어', '에너지',
  '화학', '자동차', '소비재', '통신', '부동산',
]
const periods = [
  { label: '1개월', value: 1 },
  { label: '3개월', value: 3 },
  { label: '6개월', value: 6 },
  { label: '1년', value: 12 },
  { label: '2년+', value: 24 },
]
const selectedSectors = ref([])
const selectedPeriod = ref(null)

function toggleSector(s) {
  const idx = selectedSectors.value.indexOf(s)
  if (idx === -1) selectedSectors.value.push(s)
  else selectedSectors.value.splice(idx, 1)
}

// ===== Step 1~6: 투자 성향 설문 =====
const questions = [
  {
    id: 'q1',
    label: '투자 목적',
    desc: '"첫인상이 관계의 방향을 결정하듯, 이 기준은 주식 선택의 출발점을 정의합니다."',
    options: [
      { score: 1, title: '안전한 보존', desc: '자산 보존과 생활비 보호가 가장 중요합니다.' },
      { score: 3, title: '합리적 초과수익', desc: '정기예금보다 약간 높은 수준의 안정적 이익을 기대합니다.' },
      { score: 5, title: '높은 자산 증식', desc: '위험을 감수하더라도 높은 자산 성장을 추구합니다.' },
    ],
  },
  {
    id: 'q2',
    label: '투자 경험',
    desc: '지금까지의 투자 여정을 선택해주세요.',
    options: [
      { score: 1, title: '거의 없음', desc: '주식·펀드 투자 경험이 1년 미만입니다.' },
      { score: 3, title: '1~3년', desc: '중간 정도의 투자 경험이 있습니다.' },
      { score: 5, title: '3년 이상', desc: '다양한 금융 상품을 적극적으로 운용해 왔습니다.' },
    ],
  },
  {
    id: 'q3',
    label: '손실 허용 범위',
    desc: '허용 가능한 손실 범위를 선택해주세요.',
    options: [
      { score: 1, title: '10% 미만도 불안함', desc: '원금 손실은 절대 용납하기 어렵습니다.' },
      { score: 3, title: '10~20% 수준', desc: '단기 손실은 수용하나 장기 회복이 필요합니다.' },
      { score: 5, title: '30% 이상 감수 가능', desc: '높은 손실도 감수하고 큰 수익을 추구합니다.' },
    ],
  },
  {
    id: 'q4',
    label: '자금 의존도',
    desc: '이 자금은 \'안정적인 연인\'인가요, \'가능성을 보는 썸\'인가요?',
    options: [
      { score: 1, title: '생활에 꼭 필요한 자금', desc: '이 자금이 없으면 생활이 곤란합니다.' },
      { score: 3, title: '없어도 되는 여유 자금', desc: '없어도 생활에 지장은 없으나 소중한 자금입니다.' },
      { score: 5, title: '완전한 여유 자금', desc: '이 자금을 잃어도 생활에 전혀 지장이 없습니다.' },
    ],
  },
  {
    id: 'q5',
    label: '투자 기간',
    desc: '이 인연을 어느 정도의 시간으로 생각하고 계신가요?',
    weighted: true,
    options: [
      { score: 1, title: '6개월 이내', desc: '단기간 내에 자금이 필요합니다.' },
      { score: 3, title: '1~3년', desc: '중기적으로 운용할 계획입니다.' },
      { score: 5, title: '5년 이상', desc: '장기적으로 안정되게 투자할 수 있습니다.' },
    ],
  },
  {
    id: 'q6',
    label: '시장 하락 반응',
    desc: '관계가 크게 흔들릴 때, 당신은 어떻게 하시겠어요?',
    options: [
      { score: 1, title: '즉시 매도', desc: '추가 손실을 막기 위해 빠르게 결정합니다.' },
      { score: 3, title: '관망 후 결정', desc: '상황을 지켜본 뒤 결정합니다.' },
      { score: 5, title: '추가 매수', desc: '하락은 저가 매수 기회입니다.' },
    ],
  },
]

const answers = ref({})
const step = ref(0) // 0=섹터/기간, 1~6=설문, 7=결과

const currentQuestion = computed(() =>
  step.value >= 1 && step.value <= 6 ? questions[step.value - 1] : null,
)

const accumulatedScore = computed(() => {
  let total = 0
  for (const q of questions) {
    const ans = answers.value[q.id]
    if (ans !== undefined) total += q.weighted ? ans * 2 : ans
  }
  return total
})

const currentAnswer = computed(() => {
  if (!currentQuestion.value) return null
  return answers.value[currentQuestion.value.id] ?? null
})

function selectOption(score) {
  if (!currentQuestion.value) return
  answers.value[currentQuestion.value.id] = score
}

const riskResult = computed(() => {
  const s = accumulatedScore.value
  if (s <= 13) return { label: '안정형', emoji: '🛡️', colorVar: 'var(--positive)', desc: '원금 보존을 최우선으로 하며 안정적인 수익을 추구합니다.' }
  if (s <= 22) return { label: '중립형', emoji: '⚖️', colorVar: 'var(--accent)', desc: '수익과 안정성의 균형을 추구하는 균형형 투자자입니다.' }
  return { label: '공격형', emoji: '🚀', colorVar: 'var(--purple)', desc: '높은 수익을 위해 위험도 기꺼이 감수하는 공격형 투자자입니다.' }
})

const canProceed = computed(() => {
  if (step.value === 0) return selectedSectors.value.length > 0 && selectedPeriod.value !== null
  if (currentQuestion.value) return currentAnswer.value !== null
  return true
})

function next() {
  if (!canProceed.value) return
  step.value = step.value < 6 ? step.value + 1 : 7
}

function prev() {
  if (step.value > 0) step.value--
}

const riskTypeMap = { 안정형: 'CONSERVATIVE', 중립형: 'MODERATE', 공격형: 'AGGRESSIVE' }
const finishing = ref(false)
const finishError = ref('')

async function finish() {
  finishing.value = true
  finishError.value = ''
  try {
    await auth.submitOnboarding({
      risk_type: riskTypeMap[riskResult.value.label],
      preferred_period: selectedPeriod.value,
      preferred_sector: selectedSectors.value[0] ?? '',
    })
    router.push('/')
  } catch (e) {
    finishError.value = e.response?.data?.detail ?? '온보딩 저장에 실패했습니다. 다시 시도해주세요.'
  } finally {
    finishing.value = false
  }
}

function displayScore(q, score) {
  return q.weighted ? score * 2 : score
}
</script>

<template>
  <div class="ob-shell">

    <!-- ===== 결과 화면 ===== -->
    <div v-if="step === 7" class="ob-result-wrap">
      <div class="panel ob-result-card">
        <div class="result-emoji">{{ riskResult.emoji }}</div>
        <p class="eyebrow" style="text-align:center;">투자 성향 분석 완료</p>
        <h2 class="result-title" :style="{ color: riskResult.colorVar }">{{ riskResult.label }}</h2>
        <p class="result-score">종합 점수 <strong>{{ accumulatedScore }}점</strong></p>
        <p class="result-desc">{{ riskResult.desc }}</p>

        <div class="result-profile">
          <div class="result-profile-row">
            <span class="result-profile-key">관심 섹터</span>
            <div class="result-chips">
              <span v-for="s in selectedSectors" :key="s" class="result-chip">{{ s }}</span>
            </div>
          </div>
          <div class="result-profile-row">
            <span class="result-profile-key">선호 보유 기간</span>
            <strong class="result-profile-val">{{ periods.find(p => p.value === selectedPeriod)?.label ?? '-' }}</strong>
          </div>
        </div>

        <p v-if="finishError" style="color: var(--negative, #cf3d3d); font-size: 13px; font-weight: 700; text-align: center;">{{ finishError }}</p>
        <button class="primary-btn" :disabled="finishing" @click="finish">{{ finishing ? '저장 중…' : '주만추 시작하기 🎉' }}</button>
      </div>
    </div>

    <!-- ===== 설문 화면 (step 0~6) ===== -->
    <div v-else class="ob-container">

      <!-- 헤더 -->
      <div class="ob-page-header">
        <p class="eyebrow" style="text-align:center; font-size:13px;">김주만님 만의 주식투자 스타일 알아가기</p>
        <h1 class="ob-page-title">온보딩</h1>
      </div>

      <!-- 진행 바 -->
      <div class="ob-progress-track">
        <div class="ob-progress-fill" :style="{ width: `${(step / 6) * 100}%` }"></div>
      </div>
      <div class="ob-step-indicator">
        <span>{{ step === 0 ? '사전 설정' : `문항 ${step} / 6` }}</span>
        <span v-if="step >= 1" class="ob-score-inline">누적 점수 {{ accumulatedScore }}점</span>
      </div>

      <!-- 카드 -->
      <div class="panel ob-card">

        <!-- Step 0: 섹터 & 기간 -->
        <div v-if="step === 0">
          <div class="ob-card-head">
            <span class="ob-tag">사전 설정</span>
            <h2 class="ob-card-title">관심 섹터 &amp; 선호 보유 기간</h2>
            <p class="ob-card-desc">주만님과 잘 맞는 주식을 추천해드리기 위한 과정이에요. 관심 섹터와 선호 보유기간을 선택해주세요.</p>
          </div>

          <div class="ob-section">
            <p class="ob-section-label">
              관심 섹터
              <span class="ob-hint">복수 선택 가능</span>
            </p>
            <div class="sector-chips">
              <button
                v-for="s in sectors"
                :key="s"
                type="button"
                class="sector-chip"
                :class="{ 'is-selected': selectedSectors.includes(s) }"
                @click="toggleSector(s)"
              >
                {{ s }}
              </button>
            </div>
          </div>

          <div class="ob-section">
            <p class="ob-section-label">
              선호 보유 기간
              <span class="ob-hint">단일 선택</span>
            </p>
            <div class="period-chips">
              <button
                v-for="p in periods"
                :key="p.value"
                type="button"
                class="period-chip"
                :class="{ 'is-selected': selectedPeriod === p.value }"
                @click="selectedPeriod = p.value"
              >
                {{ p.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- Step 1~6: 설문 문항 -->
        <div v-else-if="currentQuestion">
          <div class="ob-card-head">
            <div class="ob-card-head-row">
              <span class="ob-tag">문항 {{ step }}</span>
              <div class="ob-score-badge">
                {{ accumulatedScore }}<small>점</small>
              </div>
            </div>
            <h2 class="ob-card-title">{{ currentQuestion.label }}</h2>
            <p class="ob-card-desc">{{ currentQuestion.desc }}</p>
          </div>

          <div class="ob-options">
            <button
              v-for="opt in currentQuestion.options"
              :key="opt.score"
              type="button"
              class="ob-option"
              :class="{ 'is-selected': currentAnswer === opt.score }"
              @click="selectOption(opt.score)"
            >
              <div class="ob-option-badge">
                {{ displayScore(currentQuestion, opt.score) }}<small>점</small>
              </div>
              <div class="ob-option-body">
                <strong class="ob-option-title">{{ opt.title }}</strong>
                <p class="ob-option-desc">{{ opt.desc }}</p>
              </div>
            </button>
          </div>

          <p v-if="currentQuestion.weighted" class="ob-weighted-note">
            ⚖️ 이 문항은 가중치 2배가 적용됩니다.
          </p>
        </div>
      </div>

      <!-- 네비게이션 -->
      <div class="ob-nav">
        <button v-if="step > 0" class="ob-btn-back" type="button" @click="prev">이전</button>
        <button
          class="ob-btn-next"
          type="button"
          :disabled="!canProceed"
          @click="next"
        >
          {{ step === 6 ? '결과 확인' : '다음' }}
        </button>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* ===== 전체 쉘: 앱 배경 그대로 사용 ===== */
.ob-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px 56px;
}

/* ===== 컨테이너 ===== */
.ob-container {
  width: 100%;
  max-width: 560px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== 페이지 헤더 ===== */
.ob-page-header { text-align: center; }

.ob-page-title {
  font-size: 38px;
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -1.5px;
  margin: 4px 0 0;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ===== 진행 바 ===== */
.ob-progress-track {
  height: 5px;
  background: color-mix(in srgb, var(--line-tint) 45%, transparent);
  border-radius: 999px;
  overflow: hidden;
}

.ob-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--purple));
  border-radius: 999px;
  transition: width 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.ob-step-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 900;
  color: var(--muted);
  padding: 0 2px;
}

.ob-score-inline {
  color: var(--accent);
  font-weight: 900;
}

/* ===== 카드 (panel 재사용) ===== */
.ob-card { padding: 24px; }

.ob-card-head { margin-bottom: 22px; }

.ob-card-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.ob-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  margin-bottom: 10px;
}

.ob-card-head-row .ob-tag { margin-bottom: 0; }

.ob-score-badge {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  border: 2px solid color-mix(in srgb, var(--accent) 25%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 900;
  color: var(--accent);
  line-height: 1;
}

.ob-score-badge small { font-size: 10px; font-weight: 900; margin-left: 1px; }

.ob-card-title {
  font-size: 22px;
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -0.5px;
  margin: 0 0 6px;
}

.ob-card-desc {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
  word-break: keep-all;
}

/* ===== 섹션 (Step 0) ===== */
.ob-section { margin-bottom: 20px; }
.ob-section:last-child { margin-bottom: 0; }

.ob-section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
}

.ob-hint {
  font-size: 11px;
  font-weight: 700;
  color: var(--faint);
}

/* 섹터 칩 */
.sector-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sector-chip {
  padding: 7px 16px;
  border-radius: 999px;
  border: 1.5px solid var(--glass-border-subtle);
  background: color-mix(in srgb, var(--overlay) 52%, transparent);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: border-color 0.18s, background 0.18s, color 0.18s;
  box-shadow: var(--glass-shadow);
}

.sector-chip:hover {
  border-color: color-mix(in srgb, var(--accent) 35%, transparent);
  color: var(--ink);
  background: color-mix(in srgb, var(--overlay) 72%, transparent);
}

.sector-chip.is-selected {
  border-color: color-mix(in srgb, var(--accent) 50%, transparent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  color: var(--accent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 15%, transparent), var(--glass-shadow);
}

/* 기간 칩 */
.period-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.period-chip {
  flex: 1;
  min-width: 58px;
  padding: 10px 8px;
  border-radius: var(--radius);
  border: 1.5px solid var(--glass-border-subtle);
  background: color-mix(in srgb, var(--overlay) 52%, transparent);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.18s, background 0.18s, color 0.18s;
  box-shadow: var(--glass-shadow);
}

.period-chip:hover {
  border-color: color-mix(in srgb, var(--purple) 35%, transparent);
  color: var(--ink);
  background: color-mix(in srgb, var(--overlay) 72%, transparent);
}

.period-chip.is-selected {
  border-color: color-mix(in srgb, var(--purple) 50%, transparent);
  background: color-mix(in srgb, var(--purple) 10%, transparent);
  color: var(--purple);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--purple) 15%, transparent), var(--glass-shadow);
}

/* ===== 설문 옵션 (Step 1~6) ===== */
.ob-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ob-option {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
  padding: 16px;
  border-radius: var(--radius);
  border: 1.5px solid var(--glass-border-subtle);
  background: color-mix(in srgb, var(--overlay) 48%, transparent);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  text-align: left;
  cursor: pointer;
  box-shadow: var(--glass-shadow);
  transition: border-color 0.2s, background 0.2s, transform 0.15s, box-shadow 0.2s;
}

.ob-option:hover {
  background: color-mix(in srgb, var(--overlay) 68%, transparent);
  border-color: color-mix(in srgb, var(--accent) 30%, transparent);
}

.ob-option.is-selected {
  border-color: color-mix(in srgb, var(--accent) 50%, transparent);
  background: color-mix(in srgb, var(--accent) 7%, transparent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 20%, transparent), var(--glass-shadow), var(--glass-inset);
  transform: translateY(-1px);
}

.ob-option-badge {
  flex-shrink: 0;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--overlay) 65%, transparent);
  border: 1.5px solid var(--glass-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 900;
  color: var(--muted);
  box-shadow: var(--glass-inset);
}

.ob-option.is-selected .ob-option-badge {
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  border-color: color-mix(in srgb, var(--accent) 35%, transparent);
  color: var(--accent);
}

.ob-option-badge small { font-size: 10px; font-weight: 900; margin-left: 1px; }

.ob-option-body { flex: 1; min-width: 0; }

.ob-option-title {
  display: block;
  font-size: 15px;
  font-weight: 900;
  color: var(--ink);
  margin-bottom: 4px;
}

.ob-option-desc {
  margin: 0;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.45;
  word-break: keep-all;
}

.ob-option.is-selected .ob-option-title { color: var(--accent); }
.ob-option.is-selected .ob-option-desc { color: color-mix(in srgb, var(--accent) 65%, transparent); }

.ob-weighted-note {
  margin: 12px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--faint);
  text-align: center;
}

/* ===== 네비게이션 ===== */
.ob-nav {
  display: flex;
  gap: 10px;
  align-items: center;
}

.ob-btn-back {
  min-height: 46px;
  padding: 0 22px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: color-mix(in srgb, var(--overlay) 52%, transparent);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  color: var(--muted);
  font-size: 14px;
  font-weight: 900;
  flex-shrink: 0;
  box-shadow: var(--glass-shadow), var(--glass-inset);
  transition: background 0.18s, color 0.18s;
}

.ob-btn-back:hover {
  background: color-mix(in srgb, var(--overlay) 75%, transparent);
  color: var(--ink);
}

.ob-btn-next {
  flex: 1;
  min-height: 46px;
  border: 0;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 900;
  box-shadow: 0 6px 22px color-mix(in srgb, var(--accent) 35%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transition: transform 0.18s, box-shadow 0.18s, opacity 0.18s;
}

.ob-btn-next:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px color-mix(in srgb, var(--accent) 42%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.ob-btn-next:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

/* ===== 결과 화면 ===== */
.ob-result-wrap {
  width: 100%;
  max-width: 480px;
}

.ob-result-card {
  text-align: center;
  padding: 40px 32px;
}

.result-emoji { font-size: 56px; margin-bottom: 16px; }

.result-title {
  font-size: 36px;
  font-weight: 900;
  letter-spacing: -1.5px;
  margin: 8px 0 6px;
}

.result-score {
  color: var(--muted);
  font-size: 13px;
  margin: 0 0 14px;
}

.result-score strong { color: var(--ink); }

.result-desc {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 24px;
  word-break: keep-all;
}

.result-profile {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius);
  background: color-mix(in srgb, var(--overlay) 42%, transparent);
  border: 1px solid var(--glass-border);
  margin-bottom: 24px;
  text-align: left;
}

.result-profile-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.result-profile-key {
  flex-shrink: 0;
  width: 90px;
  font-size: 12px;
  font-weight: 900;
  color: var(--faint);
  padding-top: 2px;
}

.result-profile-val { color: var(--ink); font-size: 13px; font-weight: 900; }

.result-chips { display: flex; flex-wrap: wrap; gap: 5px; }

.result-chip {
  padding: 3px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
}

.primary-btn {
  width: 100%;
  min-height: 48px;
  border: 0;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 900;
  box-shadow: 0 6px 24px color-mix(in srgb, var(--accent) 35%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  transition: transform 0.18s, box-shadow 0.18s;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 32px color-mix(in srgb, var(--accent) 42%, transparent), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
</style>
