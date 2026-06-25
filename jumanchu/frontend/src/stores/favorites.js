import { defineStore } from 'pinia'

// 선호 종목 — 종목 하트로 등록/해제. 하트 누른 시점의 종목 객체 스냅샷을 보관한다.
// localStorage에 저장해 뷰 이동·새로고침에도 유지된다. (서버 watchlist 연동은 추후)
const STORAGE_KEY = 'jumanchu:favorites'

function loadItems() {
  try {
    const arr = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(arr) ? arr : []
  } catch {
    return []   // 파싱 실패(손상된 값 등)는 빈 목록으로
  }
}

export const useFavoritesStore = defineStore('favorites', {
  state: () => ({
    items: loadItems(),   // 새로고침 시 localStorage에서 복원
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
      this.persist()
    },
    remove(code) {
      const i = this.items.findIndex((s) => s.code === code)
      if (i >= 0) this.items.splice(i, 1)
      this.persist()
    },
    // 스냅샷 이후 현재가·등락률 보강 (스와이프로 담은 종목 시세 업데이트용)
    updatePrice(code, price, rate) {
      const it = this.items.find((s) => s.code === code)
      if (!it) return
      it.price = price
      it.rate = rate
      this.persist()
    },
    persist() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.items))
      } catch {
        // 저장 실패(용량 초과 등)는 무시 — 메모리 상태는 그대로 동작
      }
    },
  },
})
