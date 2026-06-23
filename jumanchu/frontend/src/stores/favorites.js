import { defineStore } from 'pinia'

// 선호 종목 — 종목 하트로 등록/해제. 하트 누른 시점의 종목 객체 스냅샷을 보관한다.
// 뷰 이동에는 보존되고(SPA 세션), 새로고침 시 초기화. (서버 watchlist 연동은 추후)
export const useFavoritesStore = defineStore('favorites', {
  state: () => ({
    items: [],   // 선호 종목 객체 배열
  }),
  getters: {
    // 파라미터 getter: favStore.isFav(code)
    isFav: (state) => (code) => state.items.some((s) => s.code === code),
  },
  actions: {
    toggle(stock) {
      if (!stock || !stock.code) return
      const i = this.items.findIndex((s) => s.code === stock.code)
      if (i >= 0) this.items.splice(i, 1)
      else this.items.push({ ...stock })
    },
    remove(code) {
      const i = this.items.findIndex((s) => s.code === code)
      if (i >= 0) this.items.splice(i, 1)
    },
  },
})
