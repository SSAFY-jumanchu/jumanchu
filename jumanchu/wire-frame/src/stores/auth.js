import { defineStore } from 'pinia'
import { authApi } from '../api'
import { getAccessToken, setAccessToken } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    hasCompletedOnboarding: false,
    initialized: false, // 새로고침 후 me() 복원 완료 여부
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
  },
  actions: {
    async login(email, password) {
      const { data } = await authApi.login(email, password)
      setAccessToken(data.access)
      this.user = data.user
      await this.fetchMe()
    },
    async signup(payload) {
      await authApi.signup(payload)
      await this.login(payload.email, payload.password)
    },
    async fetchMe() {
      const { data } = await authApi.me()
      this.user = data.user
      this.hasCompletedOnboarding = data.has_completed_onboarding
    },
    async submitOnboarding(payload) {
      const { data } = await authApi.submitOnboarding(payload)
      this.user = data.user
      this.hasCompletedOnboarding = true
      return data
    },
    async logout() {
      try {
        await authApi.logout()
      } finally {
        setAccessToken(null)
        this.user = null
        this.hasCompletedOnboarding = false
      }
    },
    // 앱 시작 시 1회: access 토큰이 남아 있으면 세션 복원
    async init() {
      if (this.initialized) return
      if (getAccessToken()) {
        try {
          await this.fetchMe()
        } catch {
          setAccessToken(null)
        }
      }
      this.initialized = true
    },
  },
})
