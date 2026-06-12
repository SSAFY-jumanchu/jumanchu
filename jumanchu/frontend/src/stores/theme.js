import { defineStore } from 'pinia'

const THEME_KEY = 'jmc_theme'

// index.html 인라인 스크립트가 첫 페인트 전에 data-theme을 먼저 적용한다(FOUC 방지).
// 이 스토어는 그 상태를 이어받아 토글/저장을 담당한다.
function getInitialTheme() {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: getInitialTheme(),
  }),
  getters: {
    isDark: (state) => state.theme === 'dark',
  },
  actions: {
    apply() {
      document.documentElement.setAttribute('data-theme', this.theme)
    },
    setTheme(theme) {
      this.theme = theme
      localStorage.setItem(THEME_KEY, theme)
      this.apply()
    },
    toggle() {
      this.setTheme(this.isDark ? 'light' : 'dark')
    },
  },
})
