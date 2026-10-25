import { defineStore } from 'pinia'

// 최근 조회한 종목 스택 — 종목 상세 진입 시 기록. localStorage에 저장해 새로고침에도 유지.
// 가장 최근이 맨 앞, 같은 종목 재방문 시 맨 앞으로 끌어올리고 중복 제거, 최대 MAX개 유지.
const STORAGE_KEY = 'jumanchu:recentStocks'
const MAX = 8

function loadItems() {
  try {
    const arr = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

export const useRecentStocksStore = defineStore('recentStocks', {
  state: () => ({
    items: loadItems(),
  }),
  actions: {
    visit(stock) {
      if (!stock || !stock.code) return
      const entry = {
        code: stock.code,
        name: stock.name || stock.code,
        market: stock.market || '',
        viewedAt: Date.now(),
      }
      this.items = [entry, ...this.items.filter((s) => s.code !== stock.code)].slice(0, MAX)
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
