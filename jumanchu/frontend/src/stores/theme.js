import { defineStore } from 'pinia'

const THEME_KEY = 'jmc_theme'
const PALETTE_KEY = 'jmc_palette'

// index.html 인라인 스크립트가 첫 페인트 전에 data-theme을 먼저 적용한다(FOUC 방지).
// 이 스토어는 그 상태를 이어받아 토글/저장을 담당한다.
function getInitialTheme() {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getInitialPalette() {
  const saved = localStorage.getItem(PALETTE_KEY)
  return saved === 'love' ? 'love' : 'default'
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: getInitialTheme(),
    palette: getInitialPalette(),
  }),
  getters: {
    isDark: (state) => state.theme === 'dark',
    isLove: (state) => state.palette === 'love',
  },
  actions: {
    apply() {
      document.documentElement.setAttribute('data-theme', this.theme)
      document.documentElement.setAttribute('data-palette', this.palette)
    },
    setTheme(theme) {
      this.theme = theme
      localStorage.setItem(THEME_KEY, theme)
      this.apply()
    },
    toggle() {
      this.setTheme(this.isDark ? 'light' : 'dark')
    },
    setPalette(palette) {
      this.palette = palette === 'love' ? 'love' : 'default'
      localStorage.setItem(PALETTE_KEY, this.palette)
      this.apply()
    },
  },
})
