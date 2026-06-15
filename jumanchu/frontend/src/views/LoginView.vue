<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const mode = ref('login') // login | signup
const loading = ref(false)
const errorMsg = ref('')

const form = ref({
  email: '',
  password: '',
  password_confirm: '',
  username: '',
  nickname: '',
  birth_year: null,
  agree_terms: false,
})

function submit() {
  // 와이어프레임: 이메일/비밀번호 검증 없이 즉시 로그인 → 온보딩 설문으로 이동
  auth.mockLogin(mode.value === 'signup' ? form.value.nickname || undefined : undefined)
  router.push(auth.hasCompletedOnboarding ? '/' : '/onboarding')
}
</script>

<template>
  <div class="login-shell">
    <div class="panel login-card">
      <strong class="login-brand">주만추</strong>
      <p class="eyebrow" style="text-align:center;">자연스러운 주식과의 만남 추구</p>
      <h2 class="login-title">{{ mode === 'login' ? '로그인' : '회원가입' }}</h2>

      <form class="login-form" @submit.prevent="submit">
        <label class="field">
          <span>이메일</span>
          <input v-model="form.email" type="email" placeholder="you@example.com" />
        </label>
        <label class="field">
          <span>비밀번호</span>
          <input v-model="form.password" type="password" placeholder="와이어프레임 — 입력 없이 로그인 가능" />
        </label>

        <template v-if="mode === 'signup'">
          <label class="field">
            <span>비밀번호 확인</span>
            <input v-model="form.password_confirm" type="password" required minlength="8" />
          </label>
          <label class="field">
            <span>이름</span>
            <input v-model="form.username" type="text" required />
          </label>
          <label class="field">
            <span>닉네임</span>
            <input v-model="form.nickname" type="text" required maxlength="20" />
          </label>
          <label class="field">
            <span>출생연도</span>
            <input v-model.number="form.birth_year" type="number" required min="1900" max="2026" placeholder="2000" />
          </label>
          <label class="agree-row">
            <input v-model="form.agree_terms" type="checkbox" required />
            <span>이용약관에 동의합니다</span>
          </label>
        </template>

        <p v-if="errorMsg" class="login-error">{{ errorMsg }}</p>

        <button class="submit-btn" type="submit" :disabled="loading">
          {{ loading ? '처리 중…' : mode === 'login' ? '로그인' : '가입하고 시작하기' }}
        </button>
      </form>

      <button class="mode-toggle" @click="mode = mode === 'login' ? 'signup' : 'login'; errorMsg = ''">
        {{ mode === 'login' ? '아직 계정이 없나요? 회원가입' : '이미 계정이 있나요? 로그인' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.login-shell {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 32px 28px;
}

.login-brand {
  text-align: center;
  font-size: 30px;
  font-weight: 900;
  letter-spacing: -1px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-title {
  text-align: center;
  margin: 8px 0 16px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field span {
  font-size: 12px;
  font-weight: 900;
  color: var(--muted);
}

.field input {
  height: 42px;
  padding: 0 12px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--input-bg);
  font-size: 14px;
  color: var(--ink);
}

.field input:focus {
  outline: 2px solid rgba(49, 93, 255, 0.35);
  border-color: var(--accent);
}

.agree-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--muted);
  font-weight: 700;
}

.login-error {
  margin: 0;
  color: var(--negative, #cf3d3d);
  font-size: 13px;
  font-weight: 700;
}

.submit-btn {
  height: 46px;
  border: 0;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(49, 93, 255, 0.3);
}

.submit-btn:disabled { opacity: 0.6; cursor: default; }

.mode-toggle {
  margin-top: 10px;
  border: 0;
  background: none;
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}
</style>
