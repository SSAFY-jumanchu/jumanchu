import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'

// access 토큰은 메모리(state)에만 보관 — localStorage 사용 안 함(XSS 방지).
// refresh 토큰은 httpOnly 쿠키라 JS에서 못 읽으며, 갱신은 /auth/token/refresh/가 처리.
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    access: null,
    hasCompletedOnboarding: false,
    initialized: false,
  }),
  getters: {
    isAuthenticated: (s) => !!s.access,
  },
  actions: {
    async login(email, password) {
      const data = await authApi.login(email, password) // { access, user }
      this.access = data.access
      this.user = data.user
      // 로그인 응답엔 온보딩 플래그가 없음 → profile 존재로 판별
      this.hasCompletedOnboarding = data.user?.profile != null
    },
    async signup(payload) {
      await authApi.signup(payload) // 가입 응답엔 토큰이 없음
      await this.login(payload.email, payload.password) // 같은 자격증명으로 바로 로그인
    },
    async refresh() {
      const data = await authApi.refresh() // { access } 뿐
      this.access = data.access
      return data.access
    },
    async fetchMe() {
      const data = await authApi.me() // { user, has_completed_onboarding }
      this.user = data.user
      this.hasCompletedOnboarding = data.has_completed_onboarding
      return data.user
    },
    async submitOnboarding(payload) {
      const data = await authApi.onboarding(payload)
      this.user = data.user
      this.hasCompletedOnboarding = true
      return data
    },
    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.clear()
      }
    },
    clear() {
      this.user = null
      this.access = null
      this.hasCompletedOnboarding = false
    },
    // 앱 부팅 1회: 쿠키로 세션 복원 (refresh → me). 쿠키 없으면 비로그인 상태.
    async init() {
      if (this.initialized) return
      try {
        await this.refresh()
        await this.fetchMe()
      } catch {
        this.clear()
      } finally {
        this.initialized = true
      }
    },
  },
})
