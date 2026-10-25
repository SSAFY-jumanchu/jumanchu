<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { errMsg } from '../api/client'

const router = useRouter()
const route = useRoute()
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

// ===== 이용약관 팝업 =====
const showTerms = ref(false)
function agreeFromTerms() {
  form.value.agree_terms = true
  showTerms.value = false
}
const termsSections = [
  { title: '제1조 (목적)', body: '이 약관은 주만추(이하 "서비스")가 제공하는 모의 주식 투자 및 커뮤니티 서비스의 이용 조건·절차와 이용자·서비스의 권리·의무를 규정함을 목적으로 합니다.' },
  { title: '제2조 (가상 모의 투자 고지)', body: '본 서비스의 모든 매매·잔고·수익률은 실제 금전 거래가 아닌 가상(모의) 데이터입니다. 서비스가 제공하는 시세·추천·점수·리포트는 투자 참고용 정보이며, 어떠한 경우에도 특정 종목의 매수·매도를 권유하거나 투자 수익을 보장하지 않습니다.' },
  { title: '제3조 (서비스 내용)', body: '서비스는 모의 매매, 종목·시장 정보 조회, 궁합 추천, 장기투자 케어, 매매일기, 커뮤니티(게시글·댓글·팔로우) 등을 제공합니다. 서비스 내용은 운영상 필요에 따라 변경될 수 있습니다.' },
  { title: '제4조 (회원가입 및 계정)', body: '이용자는 본인의 정확한 정보로 가입해야 하며, 계정 정보의 관리 책임은 이용자 본인에게 있습니다. 타인의 정보를 도용하거나 계정을 부정하게 다중 운용해서는 안 됩니다.' },
  { title: '제5조 (이용자의 의무)', body: '이용자는 다음 행위를 해서는 안 됩니다.\n1) 허위 정보 게시 또는 시세 조종성 정보 유포\n2) 타인 비방·욕설·명예훼손\n3) 저작권 등 타인의 권리 침해\n4) 서비스 운영을 방해하는 행위\n5) 기타 관계 법령을 위반하는 행위' },
  { title: '제6조 (게시물의 관리)', body: '이용자가 작성한 게시글·댓글의 책임은 작성자에게 있으며, 제5조를 위반하는 게시물은 사전 통지 없이 삭제되거나 이용이 제한될 수 있습니다.' },
  { title: '제7조 (개인정보 보호)', body: '서비스는 회원가입 시 수집한 최소한의 정보를 서비스 제공 목적 범위 내에서만 이용하며, 관련 법령에 따라 보호합니다.' },
  { title: '제8조 (면책)', body: '서비스가 제공하는 정보는 정확성을 위해 노력하나 외부 데이터 제공처의 사정으로 지연·오류가 있을 수 있습니다. 이용자가 본 서비스의 정보를 토대로 행한 실제 투자 등 의사결정의 결과에 대해 서비스는 책임지지 않습니다.' },
  { title: '제9조 (약관의 변경)', body: '본 약관은 관련 법령을 위배하지 않는 범위에서 변경될 수 있으며, 변경 시 서비스 내에 공지합니다.' },
  { title: '부칙', body: '본 약관은 2026년 6월 24일부터 적용됩니다.' },
]

async function submit() {
  if (loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    if (mode.value === 'signup') {
      await auth.signup(form.value) // 가입 후 자동 로그인까지 처리
    } else {
      await auth.login(form.value.email, form.value.password)
    }
    // 온보딩 미완료면 설문으로, 완료면 원래 가려던 곳(redirect) 또는 홈으로.
    const dest = !auth.hasCompletedOnboarding
      ? '/onboarding'
      : (route.query.redirect || '/')
    router.push(dest)
  } catch (e) {
    errorMsg.value = errMsg(e)
  } finally {
    loading.value = false
  }
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
          <input v-model="form.email" type="email" placeholder="you@example.com" required />
        </label>
        <label class="field">
          <span>비밀번호</span>
          <input v-model="form.password" type="password" placeholder="비밀번호" required minlength="8" />
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
          <div class="agree-row">
            <label class="agree-check">
              <input v-model="form.agree_terms" type="checkbox" required />
              <span>이용약관에 동의합니다</span>
            </label>
            <button type="button" class="terms-view-btn" @click="showTerms = true">(보기)</button>
          </div>
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

    <!-- ===== 이용약관 팝업 ===== -->
    <Transition name="terms-fade">
      <div v-if="showTerms" class="terms-modal" @click.self="showTerms = false">
        <div class="terms-dialog panel" role="dialog" aria-modal="true" aria-label="주만추 이용약관">
          <div class="terms-head">
            <h3>주만추 이용약관</h3>
            <button class="terms-close" type="button" aria-label="닫기" @click="showTerms = false">✕</button>
          </div>
          <div class="terms-content">
            <section v-for="(s, i) in termsSections" :key="i" class="terms-section">
              <h4>{{ s.title }}</h4>
              <p style="white-space: pre-line">{{ s.body }}</p>
            </section>
          </div>
          <div class="terms-foot">
            <button class="terms-close-btn" type="button" @click="showTerms = false">닫기</button>
            <button class="terms-agree-btn" type="button" @click="agreeFromTerms">동의하고 닫기</button>
          </div>
        </div>
      </div>
    </Transition>
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
  outline: 2px solid rgba(var(--accent-rgb), 0.35);
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

.agree-check { display: flex; align-items: center; gap: 8px; cursor: pointer; }

.terms-view-btn {
  border: 0;
  background: none;
  padding: 0;
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  text-decoration: underline;
}

/* ===== 이용약관 팝업 ===== */
.terms-modal {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background: rgba(8, 11, 22, 0.55);
  backdrop-filter: blur(2px);
}

.terms-dialog {
  width: 100%;
  max-width: 560px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.terms-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px;
  border-bottom: 1px solid var(--line);
}
.terms-head h3 { margin: 0; font-size: 18px; font-weight: 900; color: var(--ink); }
.terms-close {
  width: 30px; height: 30px;
  border: 0; border-radius: 50%;
  background: transparent;
  color: var(--muted);
  font-size: 15px;
  cursor: pointer;
  transition: background 0.15s;
}
.terms-close:hover { background: var(--surface-soft); color: var(--ink); }

.terms-content {
  padding: 16px 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.terms-section h4 { margin: 0 0 5px; font-size: 14px; font-weight: 900; color: var(--ink); }
.terms-section p { margin: 0; font-size: 13px; font-weight: 600; line-height: 1.65; color: var(--muted); word-break: keep-all; }

.terms-foot {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px;
  border-top: 1px solid var(--line);
}
.terms-close-btn {
  height: 40px; padding: 0 18px;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius);
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
}
.terms-agree-btn {
  height: 40px; padding: 0 20px;
  border: 0;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
}

.terms-fade-enter-active, .terms-fade-leave-active { transition: opacity 0.2s ease; }
.terms-fade-enter-from, .terms-fade-leave-to { opacity: 0; }

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
  box-shadow: 0 8px 24px rgba(var(--accent-rgb), 0.3);
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
