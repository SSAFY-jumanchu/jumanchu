import { defineStore } from 'pinia'

const MODE_KEY = 'jmc_mode'

// index.html 인라인 스크립트가 첫 페인트 전에 data-mode를 먼저 적용한다(FOUC 방지).
// 이 스토어는 그 상태를 이어받아 토글/저장을 담당한다.
// 'normal' = 팀원이 담당하는 기본 주식 서비스, 'dating' = 장기연애 컨셉 리스킨.
function getInitialMode() {
  const saved = localStorage.getItem(MODE_KEY)
  return saved === 'dating' ? 'dating' : 'normal'
}

export const useModeStore = defineStore('mode', {
  state: () => ({
    mode: getInitialMode(),
  }),
  getters: {
    isDating: (state) => state.mode === 'dating',
  },
  actions: {
    apply() {
      document.documentElement.setAttribute('data-mode', this.mode)
    },
    setMode(mode) {
      this.mode = mode
      localStorage.setItem(MODE_KEY, mode)
      this.apply()
    },
    toggle() {
      this.setMode(this.isDating ? 'normal' : 'dating')
    },
  },
})
