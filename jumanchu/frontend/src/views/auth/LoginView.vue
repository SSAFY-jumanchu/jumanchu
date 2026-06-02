<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')

function onSubmit() {
  if (!email.value || !password.value) {
    error.value = '이메일과 비밀번호를 입력해주세요.'
    return
  }
  // TODO: POST /api/v1/auth/login
  router.push('/')
}
</script>

<template>
  <div class="auth-shell">
    <div class="auth-card panel">
      <div class="auth-brand">
        <strong class="brand-wordmark">주만추</strong>
        <p>건강한 투자 습관을 시작하세요</p>
      </div>

      <form class="auth-form" @submit.prevent="onSubmit">
        <p class="eyebrow" style="text-align: center; margin-bottom: 20px;">로그인</p>

        <label class="field">
          <span>이메일</span>
          <input v-model="email" type="email" placeholder="example@email.com" autocomplete="email" />
        </label>

        <label class="field">
          <span>비밀번호</span>
          <input v-model="password" type="password" placeholder="비밀번호를 입력하세요" autocomplete="current-password" />
        </label>

        <p v-if="error" class="auth-error" role="alert">{{ error }}</p>

        <button class="primary-action" type="submit">로그인</button>

        <p class="auth-switch">
          계정이 없으신가요?
          <RouterLink to="/signup">회원가입</RouterLink>
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
