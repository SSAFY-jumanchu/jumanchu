import { defineStore } from 'pinia'

// 디자인 프리뷰용 스텁 — 항상 로그인/온보딩 완료 상태로 시작해 모든 화면을 바로 볼 수 있다.
// 로그인/로그아웃 화면 UI 확인을 위해 액션은 로컬 상태만 바꾼다.
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: { nickname: '호영', email: 'preview@jumanchu.dev' },
    hasCompletedOnboarding: true,
    initialized: true,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
  },
  actions: {
    async login(email) {
      this.user = { nickname: email?.split('@')[0] || '호영', email }
      this.hasCompletedOnboarding = true
    },
    async signup(payload) {
      await this.login(payload.email)
    },
    async fetchMe() {},
    async submitOnboarding() {
      this.hasCompletedOnboarding = true
      return {}
    },
    async logout() {
      this.user = null
      this.hasCompletedOnboarding = false
    },
    async init() {},
  },
})
