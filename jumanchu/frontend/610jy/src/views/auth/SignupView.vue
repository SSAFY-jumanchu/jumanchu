<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const username = ref('')
const nickname = ref('')
const birthYear = ref('')
const password = ref('')
const passwordConfirm = ref('')
const agreeTerms = ref(false)
const error = ref('')

// 만 14세 이상만 가입 가능 → 출생연도 상한
const maxBirthYear = new Date().getFullYear() - 14

function validate() {
  if (!email.value || !username.value || !nickname.value || !birthYear.value || !password.value) {
    return '모든 필드를 입력해주세요.'
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) return '올바른 이메일 형식이 아닙니다.'
  if (nickname.value.length < 2 || nickname.value.length > 20) return '닉네임은 2~20자여야 합니다.'
  const year = Number(birthYear.value)
  if (!Number.isInteger(year) || year < 1900 || year > maxBirthYear) {
    return `출생연도는 1900 ~ ${maxBirthYear}년 사이여야 합니다. (만 14세 이상)`
  }
  if (password.value.length < 8) return '비밀번호는 8자 이상이어야 합니다.'
  if (!/[a-zA-Z]/.test(password.value) || !/[0-9]/.test(password.value)) return '비밀번호는 영문+숫자 조합이어야 합니다.'
  if (password.value !== passwordConfirm.value) return '비밀번호가 일치하지 않습니다.'
  if (!agreeTerms.value) return '약관에 동의해주세요.'
  return null
}

function onSubmit() {
  const err = validate()
  if (err) { error.value = err; return }
  error.value = ''
  // TODO: POST /api/v1/auth/signup
  // payload: { email, password, password_confirm, username, nickname, birth_year, agree_terms }
  router.push('/onboarding')
}
</script>

<template>
  <div class="auth-shell">
    <div class="auth-card panel">
      <div class="auth-brand">
        <strong class="brand-wordmark">주만추</strong>
        <p>자연스러운 주식과의 만남 추구</p>
      </div>

      <form class="auth-form" @submit.prevent="onSubmit">
        <p class="eyebrow" style="text-align: center; margin-bottom: 20px;">회원가입</p>

        <label class="field">
          <span>이메일</span>
          <input v-model="email" type="email" placeholder="example@email.com" autocomplete="email" />
        </label>

        <label class="field">
          <span>아이디 <em class="field-hint">로그인 ID</em></span>
          <input v-model="username" type="text" placeholder="아이디를 입력하세요" autocomplete="username" />
        </label>

        <label class="field">
          <span>닉네임 <em class="field-hint">2~20자</em></span>
          <input v-model="nickname" type="text" placeholder="닉네임을 입력하세요" maxlength="20" />
        </label>

        <label class="field">
          <span>출생연도 <em class="field-hint">만 14세 이상</em></span>
          <input v-model="birthYear" type="number" placeholder="예) 2000" min="1900" :max="maxBirthYear" />
        </label>

        <label class="field">
          <span>비밀번호 <em class="field-hint">영문+숫자 8자 이상</em></span>
          <input v-model="password" type="password" placeholder="비밀번호" autocomplete="new-password" />
        </label>

        <label class="field">
          <span>비밀번호 확인</span>
          <input v-model="passwordConfirm" type="password" placeholder="비밀번호 재입력" autocomplete="new-password" />
        </label>

        <label class="agree-row">
          <input v-model="agreeTerms" type="checkbox" />
          <span>이용약관 및 개인정보 처리방침에 동의합니다. <em class="field-hint">필수</em></span>
        </label>

        <p v-if="error" class="auth-error" role="alert">{{ error }}</p>

        <button class="primary-action" type="submit">가입하기</button>

        <p class="auth-switch">
          이미 계정이 있으신가요?
          <RouterLink to="/login">로그인</RouterLink>
        </p>
      </form>
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

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 36px;
}

.auth-brand {
  text-align: center;
  margin-bottom: 28px;
}

.auth-brand p {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 14px;
}

.auth-form {
  display: grid;
  gap: 14px;
}

.field-hint {
  font-style: normal;
  color: var(--faint);
  font-size: 11px;
  font-weight: 900;
  margin-left: 6px;
}

.agree-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.45;
  cursor: pointer;
}

.agree-row input {
  margin-top: 2px;
  flex-shrink: 0;
  accent-color: var(--accent);
}

.auth-error {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius);
  background: rgba(207, 61, 61, 0.08);
  border: 1px solid rgba(207, 61, 61, 0.25);
  color: var(--negative);
  font-size: 13px;
  font-weight: 900;
}

.auth-switch {
  margin: 4px 0 0;
  text-align: center;
  color: var(--muted);
  font-size: 13px;
}

.auth-switch a {
  color: var(--accent);
  font-weight: 900;
  text-decoration: underline;
}
</style>
