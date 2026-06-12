<script setup>
import { ref, computed, onMounted } from 'vue'
import SparklineChart from '../components/SparklineChart.vue'
import { portfolioApi } from '../api'

const sortKey = ref('evalAmount')

// 초기값은 와이어프레임 목업 — API 응답이 오면 실데이터로 교체
const holdings = ref([
  {
    code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '전기·전자',
    qty: 15, avgPrice: 172000, currentPrice: 189300,
    sparkline: [68, 70, 67, 72, 74, 71, 75, 73, 76, 79, 78, 81],
  },
  {
    code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자',
    qty: 40, avgPrice: 73500, currentPrice: 71200,
    sparkline: [82, 80, 78, 75, 77, 74, 72, 73, 70, 68, 66, 64],
  },
  {
    code: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', sector: '반도체',
    qty: 8, avgPrice: 820, currentPrice: 1074,
    sparkline: [55, 57, 56, 59, 61, 63, 62, 65, 67, 69, 71, 73],
  },
  {
    code: 'AAPL', name: 'Apple', market: 'NASDAQ', sector: 'IT·소비재',
    qty: 20, avgPrice: 185, currentPrice: 192,
    sparkline: [50, 53, 52, 56, 58, 61, 60, 64, 66, 69, 71, 74],
  },
  {
    code: '035420', name: 'NAVER', market: 'KOSPI', sector: 'IT·소프트웨어',
    qty: 5, avgPrice: 195000, currentPrice: 214000,
    sparkline: [44, 48, 47, 52, 55, 58, 62, 65, 68, 72, 75, 79],
  },
])

const defaultSpark = [60, 62, 61, 63, 65, 64, 66, 68, 67, 69, 71, 70]

onMounted(async () => {
  // GET /api/v1/portfolio/holdings/
  try {
    const { data } = await portfolioApi.holdings()
    if (data.items) {
      holdings.value = data.items.map((h) => ({
        code: h.stock.code,
        name: h.stock.name,
        market: h.stock.market,
        sector: h.stock.sector,
        qty: h.quantity,
        avgPrice: Number(h.average_price),
        currentPrice: Number(h.current_price),
        sparkline: defaultSpark,
      }))
    }
  } catch (e) {
    console.warn('보유 종목 로드 실패 — 목업 유지', e)
  }
})

function evalAmount(h) { return h.qty * h.currentPrice }
function pnl(h) { return (h.currentPrice - h.avgPrice) * h.qty }
function returnRate(h) { return ((h.currentPrice - h.avgPrice) / h.avgPrice) * 100 }
function isKrw(h) { return h.market === 'KOSPI' || h.market === 'KOSDAQ' }

function fmtPrice(v, krw = true) {
  return krw
    ? v.toLocaleString('ko-KR') + '원'
    : '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2 })
}
function fmtRate(v) {
  return (v >= 0 ? '+' : '') + v.toFixed(2) + '%'
}
function fmtPnl(h) {
  const v = pnl(h)
  const prefix = v >= 0 ? '+' : ''
  return isKrw(h) ? prefix + v.toLocaleString('ko-KR') + '원' : prefix + '$' + Math.abs(v).toLocaleString()
}

const totalEval = computed(() => holdings.value.reduce((sum, h) => sum + (isKrw(h) ? evalAmount(h) : evalAmount(h) * 1380), 0))
const totalCost = computed(() => holdings.value.reduce((sum, h) => sum + (isKrw(h) ? h.qty * h.avgPrice : h.qty * h.avgPrice * 1380), 0))
const totalPnl = computed(() => totalEval.value - totalCost.value)
const totalReturn = computed(() => totalCost.value ? (totalPnl.value / totalCost.value) * 100 : 0)

const sortedHoldings = computed(() => {
  return [...holdings.value].sort((a, b) => evalAmount(b) - evalAmount(a))
})

const marketGroups = computed(() => {
  const domestic = holdings.value.filter(h => isKrw(h))
  const overseas = holdings.value.filter(h => !isKrw(h))
  const domTotal = domestic.reduce((s, h) => s + evalAmount(h), 0)
  const ovsTotal = overseas.reduce((s, h) => s + evalAmount(h) * 1380, 0)
  const grand = domTotal + ovsTotal
  return [
    { label: '국내주식', amount: domTotal, pct: grand ? (domTotal / grand * 100) : 0, color: 'var(--accent)' },
    { label: '해외주식', amount: ovsTotal, pct: grand ? (ovsTotal / grand * 100) : 0, color: 'var(--purple)' },
  ]
})

const selectedCode = ref(null)
function toggleDetail(code) {
  selectedCode.value = selectedCode.value === code ? null : code
}
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">가상 계좌 기준</p>
        <h1>보유 종목</h1>
      </div>
      <div class="top-actions">
        <div class="market-state">
          <span class="status-dot local"></span>
          샘플 데이터
        </div>
      </div>
    </header>

    <!-- 요약 strip -->
    <div class="summary-strip holdings-strip">
      <div class="metric-tile tone-blue">
        <span>총 평가금액</span>
        <strong>{{ Math.round(totalEval / 10000).toLocaleString() }}<small style="font-size:16px;font-weight:700;"> 만원</small></strong>
        <p>국내 + 해외(환율 1,380)</p>
      </div>
      <div class="metric-tile" :class="totalPnl >= 0 ? 'tone-green' : 'tone-red'">
        <span>총 평가손익</span>
        <strong :class="totalPnl >= 0 ? 'is-up' : 'is-down'">
          {{ totalPnl >= 0 ? '+' : '' }}{{ Math.round(totalPnl / 10000).toLocaleString() }}<small style="font-size:16px;font-weight:700;"> 만원</small>
        </strong>
        <p :class="totalPnl >= 0 ? 'is-up' : 'is-down'">{{ fmtRate(totalReturn) }}</p>
      </div>
      <div class="metric-tile tone-purple">
        <span>보유 종목 수</span>
        <strong>{{ holdings.length }}<small style="font-size:16px;font-weight:700;"> 종목</small></strong>
        <p>국내 {{ holdings.filter(h => isKrw(h)).length }} · 해외 {{ holdings.filter(h => !isKrw(h)).length }}</p>
      </div>
      <div class="metric-tile tone-amber">
        <span>예수금 잔고</span>
        <strong>8,432<small style="font-size:16px;font-weight:700;"> 만원</small></strong>
        <p>주문 가능 금액</p>
      </div>
    </div>

    <div class="holdings-layout">
      <!-- 왼쪽: 종목 리스트 -->
      <section class="panel holdings-panel" aria-label="보유 종목 목록">
        <div class="panel-head">
          <h2>보유 종목 목록</h2>
          <div class="segmented">
            <button class="is-selected" type="button">전체</button>
            <button type="button">국내</button>
            <button type="button">해외</button>
          </div>
        </div>

        <div class="holdings-table">
          <!-- 헤더 -->
          <div class="holdings-row holdings-header">
            <span>종목</span>
            <span class="align-right">보유수량</span>
            <span class="align-right">평균 단가</span>
            <span class="align-right">현재가</span>
            <span class="align-right">평가금액</span>
            <span class="align-right">수익률</span>
            <span class="align-right">추이</span>
          </div>

          <!-- 종목 행 -->
          <div
            v-for="h in sortedHoldings"
            :key="h.code"
            class="holdings-row holdings-data"
            :class="{ 'is-expanded': selectedCode === h.code }"
            @click="toggleDetail(h.code)"
          >
            <div class="holding-name-cell">
              <div class="holding-market-badge">{{ h.market }}</div>
              <div>
                <strong class="holding-name">{{ h.name }}</strong>
                <span class="holding-code">{{ h.code }}</span>
              </div>
            </div>
            <span class="align-right holding-qty">{{ h.qty.toLocaleString() }}주</span>
            <span class="align-right holding-avg">{{ isKrw(h) ? h.avgPrice.toLocaleString() + '원' : '$' + h.avgPrice }}</span>
            <span class="align-right holding-cur" :class="h.currentPrice > h.avgPrice ? 'is-up' : 'is-down'">
              {{ isKrw(h) ? h.currentPrice.toLocaleString() + '원' : '$' + h.currentPrice }}
            </span>
            <span class="align-right holding-eval">{{ isKrw(h) ? evalAmount(h).toLocaleString() + '원' : '$' + evalAmount(h).toLocaleString() }}</span>
            <span class="align-right holding-rate" :class="returnRate(h) >= 0 ? 'is-up' : 'is-down'">
              {{ fmtRate(returnRate(h)) }}
            </span>
            <div class="align-right holding-spark">
              <SparklineChart :values="h.sparkline" :width="72" :height="28" class="spark-mini" :class="returnRate(h) >= 0 ? 'spark-up-card' : 'spark-down-card'" />
            </div>
          </div>
        </div>
      </section>

      <!-- 오른쪽: 자산 배분 -->
      <aside class="panel allocation-panel" aria-label="자산 배분">
        <div class="panel-head">
          <h2>자산 배분</h2>
        </div>

        <!-- 시장별 비율 -->
        <div class="alloc-section">
          <p class="eyebrow">시장별</p>
          <div class="alloc-bars">
            <div v-for="g in marketGroups" :key="g.label" class="alloc-row">
              <div class="alloc-row-head">
                <span class="alloc-label">{{ g.label }}</span>
                <span class="alloc-pct">{{ g.pct.toFixed(1) }}%</span>
              </div>
              <div class="bar-track">
                <span :style="{ width: g.pct + '%', background: g.color }"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 종목별 비중 -->
        <div class="alloc-section">
          <p class="eyebrow">종목별 비중</p>
          <div class="alloc-bars">
            <div v-for="h in sortedHoldings" :key="h.code" class="alloc-row">
              <div class="alloc-row-head">
                <span class="alloc-label">{{ h.name }}</span>
                <span class="alloc-pct">{{ ((evalAmount(h) * (isKrw(h) ? 1 : 1380)) / totalEval * 100).toFixed(1) }}%</span>
              </div>
              <div class="bar-track">
                <span :style="{
                  width: ((evalAmount(h) * (isKrw(h) ? 1 : 1380)) / totalEval * 100) + '%',
                  background: 'linear-gradient(90deg, var(--accent), var(--purple))',
                }"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 손익 요약 -->
        <div class="alloc-section">
          <p class="eyebrow">종목별 손익</p>
          <div class="pnl-list">
            <div v-for="h in sortedHoldings" :key="h.code" class="pnl-row">
              <span class="pnl-name">{{ h.name }}</span>
              <span class="pnl-val" :class="pnl(h) >= 0 ? 'is-up' : 'is-down'">{{ fmtPnl(h) }}</span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  min-height: 72px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 20px;
  margin-bottom: 16px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.52);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow), var(--glass-inset);
}

.top-actions { display: flex; align-items: center; gap: 12px; }

.market-state {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow), var(--glass-inset);
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

.status-dot {
  width: 8px; height: 8px; flex: 0 0 auto; border-radius: 50%; display: inline-block;
  background: var(--faint);
}
.status-dot.local { background: var(--accent); box-shadow: 0 0 0 3px rgba(49,93,255,0.2); }

/* Summary strip */
.summary-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.metric-tile {
  border-radius: var(--radius);
  background: var(--glass);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow), var(--glass-inset);
  min-height: 120px;
  padding: 16px;
}

.metric-tile.tone-blue { background: linear-gradient(145deg, rgba(49,93,255,.07) 0%, rgba(255,255,255,.62) 55%); }
.metric-tile.tone-green { background: linear-gradient(145deg, rgba(15,159,110,.07) 0%, rgba(255,255,255,.62) 55%); }
.metric-tile.tone-red { background: linear-gradient(145deg, rgba(207,61,61,.07) 0%, rgba(255,255,255,.62) 55%); }
.metric-tile.tone-purple { background: linear-gradient(145deg, rgba(125,78,232,.07) 0%, rgba(255,255,255,.62) 55%); }
.metric-tile.tone-amber { background: linear-gradient(145deg, rgba(184,120,0,.07) 0%, rgba(255,255,255,.62) 55%); }

.metric-tile > span {
  display: block;
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
}
.metric-tile.tone-green > span { color: var(--positive); }
.metric-tile.tone-red > span { color: var(--negative); }
.metric-tile.tone-purple > span { color: var(--purple); }
.metric-tile.tone-amber > span { color: var(--warning); }

.metric-tile strong {
  display: block;
  margin-top: 8px;
  color: var(--ink);
  font-size: 26px;
  line-height: 1;
  font-weight: 900;
}

.metric-tile p {
  margin: 8px 0 0;
  color: var(--text);
  font-size: 12px;
  line-height: 1.4;
  font-weight: 700;
}

/* Layout */
.holdings-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 18px;
  align-items: start;
}

/* Holdings table */
.holdings-panel { padding: 20px; }

.holdings-table { display: grid; gap: 2px; }

.holdings-row {
  display: grid;
  grid-template-columns: minmax(160px, 2fr) 80px 100px 100px 110px 80px 80px;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius);
}

.holdings-header {
  font-size: 11px;
  font-weight: 900;
  color: var(--faint);
  background: transparent;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--line);
}

.holdings-data {
  background: rgba(255,255,255,0.38);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.16s, border-color 0.16s;
}

.holdings-data:hover {
  background: rgba(255,255,255,0.62);
  border-color: var(--glass-border);
}

.holdings-data.is-expanded {
  background: rgba(49,93,255,0.06);
  border-color: rgba(49,93,255,0.25);
}

.holding-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.holding-market-badge {
  flex-shrink: 0;
  padding: 3px 6px;
  border-radius: 6px;
  background: rgba(49,93,255,0.1);
  color: var(--accent);
  font-size: 10px;
  font-weight: 900;
}

.holding-name {
  display: block;
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.holding-code {
  display: block;
  font-size: 11px;
  color: var(--faint);
  font-weight: 700;
}

.align-right { text-align: right; }

.holding-qty, .holding-avg { color: var(--muted); font-size: 13px; font-weight: 700; }
.holding-cur { font-size: 13px; font-weight: 900; }
.holding-eval { font-size: 13px; font-weight: 900; color: var(--ink); }
.holding-rate { font-size: 13px; font-weight: 900; }

.holding-spark { display: flex; justify-content: flex-end; }

.spark-mini { width: 72px; height: 28px; }
.spark-up-card :deep(.sparkline-line) { stroke: var(--positive); }
.spark-up-card :deep(.sparkline-fill) { fill: rgba(15,159,110,.1); }
.spark-down-card :deep(.sparkline-line) { stroke: var(--negative); }
.spark-down-card :deep(.sparkline-fill) { fill: rgba(207,61,61,.1); }

/* Segmented control */
.segmented {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(255,255,255,0.42);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  border: 1px solid var(--glass-border);
}

.segmented button {
  min-height: 30px;
  min-width: 52px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  transition: background 0.18s, color 0.18s;
}

.segmented button.is-selected {
  background: rgba(255,255,255,0.85);
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.9);
}

/* Allocation panel */
.allocation-panel { padding: 20px; }

.alloc-section { margin-bottom: 22px; }
.alloc-section:last-child { margin-bottom: 0; }

.alloc-bars { display: grid; gap: 10px; }

.alloc-row-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.alloc-label { color: var(--text); font-size: 12px; font-weight: 900; }
.alloc-pct { color: var(--muted); font-size: 12px; font-weight: 900; }

.bar-track {
  height: 7px;
  background: rgba(255,255,255,0.5);
  border: 1px solid rgba(255,255,255,0.6);
  border-radius: 999px;
  overflow: hidden;
}

.bar-track span {
  height: 100%;
  display: block;
  border-radius: inherit;
  opacity: 0.85;
}

.pnl-list { display: grid; gap: 6px; }

.pnl-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.38);
}

.pnl-name { font-size: 13px; font-weight: 900; color: var(--ink); }
.pnl-val { font-size: 13px; font-weight: 900; }

@media (max-width: 1100px) {
  .holdings-layout { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
  .summary-strip { grid-template-columns: repeat(2, 1fr); }
  .holdings-row {
    grid-template-columns: minmax(120px, 1.5fr) 60px 80px 80px 90px 70px;
  }
  .holding-spark { display: none; }
}
</style>
