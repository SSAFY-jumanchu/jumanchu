<script setup>
import { ref, computed } from 'vue'
import StockRow from '../components/stock/StockRow.vue'
import StockWorkspace from '../components/stock/StockWorkspace.vue'
import { stocks } from '../data/stocks.js'
import { useWatchlist } from '../composables/useWatchlist.js'
import { useFormat } from '../composables/useFormat.js'

const { watchedCodes, toggleWatch } = useWatchlist()
const { formatMoney } = useFormat()

const marketFilters = ['전체', '국내', '미국']
const selectedMarket = ref('전체')
const selectedCode = ref('005930')

const filteredStocks = computed(() => {
  if (selectedMarket.value === '국내') return stocks.filter((s) => ['KOSPI', 'KOSDAQ'].includes(s.market))
  if (selectedMarket.value === '미국') return stocks.filter((s) => ['NASDAQ', 'NYSE'].includes(s.market))
  return stocks
})

const selectedStock = computed(() => stocks.find((s) => s.code === selectedCode.value) || stocks[0])
const watchlist = computed(() => stocks.filter((s) => watchedCodes.value.includes(s.code)))
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">Stock Explorer</p>
        <h1>종목 탐색</h1>
      </div>
      <div class="top-actions">
        <label class="search-box">
          <span>검색</span>
          <input type="search" placeholder="종목명, 코드, 섹터" />
        </label>
        <div class="segmented" aria-label="시장 필터">
          <button
            v-for="filter in marketFilters"
            :key="filter"
            type="button"
            :class="{ 'is-selected': selectedMarket === filter }"
            @click="selectedMarket = filter"
          >
            {{ filter }}
          </button>
        </div>
      </div>
    </header>

    <div class="layout-grid stock-layout">
      <!-- 종목 목록 -->
      <section class="panel recommendation-panel" aria-labelledby="recommend-heading">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Personal Match</p>
            <h2 id="recommend-heading">추천 후보와 관심종목</h2>
          </div>
          <span class="profile-pill">균형형 · 12개월 · 전기전자 선호</span>
        </div>

        <div class="stock-list">
          <StockRow
            v-for="stock in filteredStocks"
            :key="stock.code"
            :stock="stock"
            :is-selected="selectedStock.code === stock.code"
            :is-watched="watchedCodes.includes(stock.code)"
            @select="selectedCode = $event"
            @toggle-watch="toggleWatch"
          />
        </div>
      </section>

      <!-- 관심종목 -->
      <section class="panel watch-panel" aria-labelledby="watch-heading">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Watchlist</p>
            <h2 id="watch-heading">관심종목</h2>
          </div>
        </div>

        <div class="watch-list">
          <button
            v-for="stock in watchlist"
            :key="stock.code"
            type="button"
            :class="{ 'is-selected': selectedStock.code === stock.code }"
            @click="selectedCode = stock.code"
          >
            <span>{{ stock.name }}</span>
            <strong>{{ formatMoney(stock.price, stock.currency) }}</strong>
          </button>
        </div>

        <div class="empty-state" v-if="watchlist.length === 0">
          관심종목을 선택하면 실시간 시세 슬롯으로 올라옵니다.
        </div>
      </section>
    </div>

    <!-- 종목 상세 + 주문 -->
    <StockWorkspace :stock="selectedStock" />
  </div>
</template>
