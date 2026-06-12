import { ref } from 'vue'

// 화이트 / 다크 / 신문지 — html[data-theme]로 전환, localStorage에 유지
export const THEMES = [
  { id: 'light', label: '화이트', icon: '☀️' },
  { id: 'dark', label: '다크', icon: '🌙' },
  { id: 'paper', label: '신문지', icon: '📰' },
]

const STORAGE_KEY = 'jmc_design_theme'
const theme = ref(localStorage.getItem(STORAGE_KEY) || 'light')

function apply(id) {
  document.documentElement.dataset.theme = id
}

apply(theme.value)

export function useTheme() {
  function setTheme(id) {
    theme.value = id
    localStorage.setItem(STORAGE_KEY, id)
    apply(id)
  }
  return { theme, setTheme }
}
