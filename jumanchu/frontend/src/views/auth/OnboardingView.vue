<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const step = ref(1)
const totalSteps = 3

const goalName = ref('')
const goalAmount = ref('')

const styles = [
  { key: 'aggressive', label: '공격형', emoji: '🚀', desc: '높은 수익을 위해 높은 위험도 감수' },
  { key: 'balanced', label: '균형형', emoji: '⚖️', desc: '수익과 안정성의 균형을 추구' },
  { key: 'conservative', label: '안정형', emoji: '🛡️', desc: '원금 보존을 최우선으로' },
]
const selectedStyle = ref('balanced')

function next() {
  if (step.value < totalSteps) { step.value++; return }
  // TODO: POST /api/v1/auth/onboarding
  router.push('/')
}

function prev() {
  if (step.value > 1) step.value--
}
</script>

<template>
  <div class="auth-shell">
    <div class="onboarding-card panel">
      <div class="onboarding-progress" aria-label="진행 단계">
        <div
          v-for="i in totalSteps"
          :key="i"
          class="progress-dot"
          :class="{ active: i === step, done: i < step }"
        ></div>
      </div>

      <!-- Step 1: 환영 + 투자 목표 이름 -->
      <div v-if="step === 1" class="onboarding-step">
        <div class="step-emoji">🎯</div>
        <h2>환영합니다!</h2>
        <p class="step-desc">주만추와 함께 투자 목표를 정해봐요. 어떤 것을 위해 투자하시나요?</p>
        <label class="field">
          <span>투자 목표</span>
          <input v-model="goalName" type="text" placeholder="예) 경차, 여행 자금, 노후 준비" />
        </label>
      </div>

      <!-- Step 2: 목표 금액 -->
      <div v-else-if="step === 2" class="onboarding-step">
        <div class="step-emoji">💰</div>
        <h2>목표 금액 설정</h2>
        <p class="step-desc">「{{ goalName || '나의 목표' }}」를 위해 얼마가 필요한가요?</p>
        <label class="field">
          <span>목표 금액 (원)</span>
          <input v-model="goalAmount" type="number" placeholder="예) 15000000" min="0" step="100000" />
        </label>
        <p class="fine-print" style="margin-top: 8px;">시작 가상 예수금은 1억원으로 설정됩니다.</p>
      </div>

      <!-- Step 3: 투자 성향 -->
      <div v-else class="onboarding-step">
        <div class="step-emoji">🧠</div>
        <h2>나의 투자 성향</h2>
        <p class="step-desc">어떤 투자 방식이 맞으시나요? 나중에 변경할 수 있어요.</p>
        <div class="style-grid">
          <button
            v-for="s in styles"
            :key="s.key"
            type="button"
            class="style-option"
            :class="{ 'is-selected': selectedStyle === s.key }"
            @click="selectedStyle = s.key"
          >
            <span class="style-emoji">{{ s.emoji }}</span>
            <strong>{{ s.label }}</strong>
            <p>{{ s.desc }}</p>
          </button>
        </div>
      </div>

      <div class="onboarding-nav">
        <button v-if="step > 1" class="back-btn" type="button" @click="prev">← 이전</button>
        <button class="primary-action next-btn" type="button" @click="next">
          {{ step < totalSteps ? '다음 →' : '시작하기 🎉' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.onboarding-card {
  width: 100%;
  max-width: 460px;
  padding: 36px;
}

.onboarding-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 28px;
}

.progress-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(180, 200, 255, 0.5);
  transition: background 0.2s ease, transform 0.2s ease;
}

.progress-dot.active {
  background: var(--accent);
  transform: scale(1.3);
  box-shadow: 0 0 0 3px rgba(49, 93, 255, 0.2);
}

.progress-dot.done {
  background: var(--positive);
}

.onboarding-step {
  display: grid;
  gap: 14px;
  margin-bottom: 24px;
}

.step-emoji {
  font-size: 48px;
  text-align: center;
}

.onboarding-step h2 {
  text-align: center;
  font-size: 24px;
}

.step-desc {
  margin: 0;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.55;
  word-break: keep-all;
}

.style-grid {
  display: grid;
  gap: 10px;
}

.style-option {
  display: grid;
  grid-template-columns: 36px 1fr;
  grid-template-rows: auto auto;
  column-gap: 12px;
  padding: 14px;
  border-radius: var(--radius);
  border: 2px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.48);
  text-align: left;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.style-option.is-selected {
  border-color: var(--accent);
  background: rgba(49, 93, 255, 0.06);
  box-shadow: 0 0 0 1px rgba(49, 93, 255, 0.15);
}

.style-emoji {
  font-size: 24px;
  grid-row: span 2;
  display: flex;
  align-items: center;
}

.style-option strong {
  color: var(--ink);
  font-size: 15px;
  align-self: end;
}

.style-option p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
  word-break: keep-all;
  align-self: start;
}

.onboarding-nav {
  display: flex;
  align-items: center;
  gap: 10px;
}

.back-btn {
  min-height: 44px;
  padding: 0 18px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.52);
  color: var(--muted);
  font-size: 14px;
  font-weight: 900;
  flex-shrink: 0;
  transition: background 0.18s ease, color 0.18s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.72);
  color: var(--ink);
}

.next-btn {
  flex: 1;
  width: auto;
}
</style>
