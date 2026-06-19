import { defineStore } from 'pinia'

// 와이어프레임 모드: 백엔드/DB 연동 없이 로컬 상태만으로 동작한다.
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    hasCompletedOnboarding: false,
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
  },
  actions: {
    // 이메일/비밀번호 검증 없이 즉시 로그인.
    // 온보딩 미완료 상태로 두어 로그인 직후 온보딩 설문으로 이동시킨다.
    mockLogin(nickname = '김주만') {
      this.user = { nickname, email: 'guest@jumanchu.app' }
      this.hasCompletedOnboarding = false
      this.initialized = true
    },
    // 온보딩 결과를 로컬 상태에만 저장.
    completeOnboarding(profile) {
      this.user = { ...this.user, ...profile }
      this.hasCompletedOnboarding = true
    },
    logout() {
      this.user = null
      this.hasCompletedOnboarding = false
    },
    // 세션 복원 없음 — 라우터 가드 호환을 위해 유지.
    init() {
      this.initialized = true
    },
  },
})
