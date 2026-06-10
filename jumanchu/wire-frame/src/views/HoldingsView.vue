<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import SparklineChart from '../components/SparklineChart.vue'

const router = useRouter()

const marketFilter = ref('all')
const filters = [
  { key: 'all', label: '전체' },
  { key: 'domestic', label: '국내' },
  { key: 'overseas', label: '해외' },
]

const selectedCode = ref('000660')

const holdings = [
  {
    code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '전기·전자',
    qty: 15, avgPrice: 172000, currentPrice: 189300,
    color: '#0070c0',
    sparkline: [68, 70, 67, 72, 74, 71, 75, 73, 76, 79, 78, 81],
  },
  {
    code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자',
    qty: 40, avgPrice: 73500, currentPrice: 71200,
    color: '#1428A0',
    sparkline: [82, 80, 78, 75, 77, 74, 72, 73, 70, 68, 66, 64],
  },
  {
    code: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', sector: '반도체',
    qty: 8, avgPrice: 820, currentPrice: 1074,
    color: '#76b900',
    sparkline: [55, 57, 56, 59, 61, 63, 62, 65, 67, 69, 71, 73],
  },
  {
    code: 'AAPL', name: 'Apple', market: 'NASDAQ', sector: 'IT·소비재',
    qty: 20, avgPrice: 185, currentPrice: 192,
    color: '#555',
    sparkline: [50, 53, 52, 56, 58, 61, 60, 64, 66, 69, 71, 74],
  },
  {
    code: '035420', name: 'NAVER', market: 'KOSPI', sector: 'IT·소프트웨어',
    qty: 5, avgPrice: 195000, currentPrice: 214000,
    color: '#03c75a',
    sparkline: [44, 48, 47, 52, 55, 58, 62, 65, 68, 72, 75, 79],
  },
]

function evalAmount(h) { return h.qty * h.currentPrice }
function pnl(h) { return (h.currentPrice - h.avgPrice) * h.qty }
function returnRate(h) { return ((h.currentPrice - h.avgPrice) / h.avgPrice) * 100 }
function isKrw(h) { return h.market === 'KOSPI' || h.market === 'KOSDAQ' }
function fmtRate(v) { return (v >= 0 ? '+' : '') + v.toFixed(2) + '%' }

const totalEval = computed(() =>
  holdings.reduce((sum, h) => sum + (isKrw(h) ? evalAmount(h) : evalAmount(h) * 1380), 0)
)
const totalCost = computed(() =>
  holdings.reduce((sum, h) => sum + (isKrw(h) ? h.qty * h.avgPrice : h.qty * h.avgPrice * 1380), 0)
)
const totalPnl = computed(() => totalEval.value - totalCost.value)
const totalReturn = computed(() => (totalPnl.value / totalCost.value) * 100)

const filteredHoldings = computed(() => {
  if (marketFilter.value === 'domestic') return holdings.filter(h => isKrw(h))
  if (marketFilter.value === 'overseas') return holdings.filter(h => !isKrw(h))
  return holdings
})

const selectedHolding = computed(() =>
  holdings.find(h => h.code === selectedCode.value) ?? null
)

const marketGroups = computed(() => {
  const domestic = holdings.filter(h => isKrw(h))
  const overseas = holdings.filter(h => !isKrw(h))
  const domTotal = domestic.reduce((s, h) => s + evalAmount(h), 0)
  const ovsTotal = overseas.reduce((s, h) => s + evalAmount(h) * 1380, 0)
  const grand = domTotal + ovsTotal
  return [
    { label: '국내주식', amount: domTotal, pct: grand ? (domTotal / grand * 100) : 0, color: 'var(--accent)' },
    { label: '해외주식', amount: ovsTotal, pct: grand ? (ovsTotal / grand * 100) : 0, color: 'var(--purple)' },
  ]
})
</script>

<template>
  <div class="holdings-page">

    <!-- 상단: 자산 요약 + 바로가기 -->
    <div class="top-section">
      <div class="asset-summary panel">
        <p class="eyebrow">가상 계좌 기준</p>
        <h1>보유 종목</h1>
        <div class="summary-grid">
          <div class="summary-item">
            <span>전체 총 평가액</span>
            <strong>{{ Math.round(totalEval / 10000).toLocaleString() }}<small>만원</small></strong>
          </div>
          <div class="summary-item" :class="totalPnl >= 0 ? 'tone-up' : 'tone-down'">
            <span>총 평가 손익</span>
            <strong :class="totalPnl >= 0 ? 'is-up' : 'is-down'">
              {{ totalPnl >= 0 ? '+' : '' }}{{ Math.round(totalPnl / 10000).toLocaleString() }}<small>만원</small>
            </strong>
            <em :class="totalPnl >= 0 ? 'is-up' : 'is-down'">({{ fmtRate(totalReturn) }})</em>
          </div>
          <div class="summary-item">
            <span>총 투자금</span>
            <strong>{{ Math.round(totalCost / 10000).toLocaleString() }}<small>만원</small></strong>
          </div>
        </div>
      </div>

      <div class="shortcut-panel panel">
        <p class="eyebrow">바로가기</p>
        <div class="shortcuts">
          <button class="shortcut-btn" @click="router.push('/trading-diary')">
            <span class="sc-icon">📋</span>
            <span class="sc-label">주문내역</span>
          </button>
          <button class="shortcut-btn" @click="router.push('/trading-diary')">
            <span class="sc-icon">📖</span>
            <span class="sc-label">매매일지</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 메인: 종목 목록 + 우측 패널 -->
    <div class="holdings-layout">

      <!-- 왼쪽: 보유 종목 목록 -->
      <section class="panel holdings-panel" aria-label="보유 종목 목록">
        <div class="panel-head">
          <h2>보유 종목 목록</h2>
          <div class="segmented">
            <button
              v-for="f in filters"
              :key="f.key"
              :class="{ 'is-selected': marketFilter === f.key }"
              @click="marketFilter = f.key"
              type="button"
            >{{ f.label }}</button>
          </div>
        </div>

        <div class="holdings-list">
          <div
            v-for="h in filteredHoldings"
            :key="h.code"
            class="holding-card"
            :class="{ 'is-selected': selectedCode === h.code }"
            @click="selectedCode = h.code"
          >
            <div class="hc-logo" :style="{ background: h.color }">{{ h.name[0] }}</div>
            <div class="hc-info">
              <strong class="hc-name">{{ h.name }}</strong>
              <span class="hc-sub">
                {{ h.market }} · {{ h.qty }}주 ·
                평단 {{ isKrw(h) ? h.avgPrice.toLocaleString() + '원' : '$' + h.avgPrice }}
              </span>
            </div>
            <div class="hc-price-col">
              <strong class="hc-price" :class="h.currentPrice > h.avgPrice ? 'is-up' : 'is-down'">
                {{ isKrw(h) ? h.currentPrice.toLocaleString() + '원' : '$' + h.currentPrice }}
              </strong>
              <span class="hc-rate" :class="returnRate(h) >= 0 ? 'is-up' : 'is-down'">
                {{ fmtRate(returnRate(h)) }}
              </span>
            </div>
            <SparklineChart
              :values="h.sparkline"
              :width="72"
              :height="32"
              class="hc-spark"
              :class="returnRate(h) >= 0 ? 'spark-up' : 'spark-down'"
            />
          </div>
        </div>
      </section>

      <!-- 오른쪽 패널 -->
      <aside class="right-panel">

        <!-- 자산 구성 -->
        <div class="panel alloc-card">
          <p class="eyebrow">자산 구성 (국내/해외)</p>
          <div class="alloc-bar-wrap">
            <div class="alloc-bar">
              <div
                v-for="g in marketGroups"
                :key="g.label"
                class="alloc-seg"
                :style="{ width: g.pct + '%', background: g.color }"
              ></div>
            </div>
          </div>
          <div class="alloc-legend">
            <div v-for="g in marketGroups" :key="g.label" class="alloc-legend-row">
              <span class="alloc-dot" :style="{ background: g.color }"></span>
              <span class="alloc-label">{{ g.label }}</span>
              <span class="alloc-amount">{{ Math.round(g.amount / 10000).toLocaleString() }}만원</span>
              <span class="alloc-pct">{{ g.pct.toFixed(1) }}%</span>
            </div>
          </div>
        </div>

        <!-- 선택 종목 상세 -->
        <div class="panel holding-detail-card" v-if="selectedHolding">
          <div class="hdc-head">
            <div class="hdc-logo" :style="{ background: selectedHolding.color }">
              {{ selectedHolding.name[0] }}
            </div>
            <div class="hdc-head-info">
              <strong class="hdc-name">{{ selectedHolding.name }}</strong>
              <span class="hdc-meta">{{ selectedHolding.code }} · {{ selectedHolding.market }}</span>
            </div>
            <button class="hdc-close" @click="selectedCode = null">✕</button>
          </div>

          <div class="hdc-price-block">
            <strong class="hdc-price" :class="selectedHolding.currentPrice > selectedHolding.avgPrice ? 'is-up' : 'is-down'">
              {{ isKrw(selectedHolding) ? '₩' : '$' }}{{ selectedHolding.currentPrice.toLocaleString() }}
            </strong>
            <span class="hdc-rate-badge" :class="returnRate(selectedHolding) >= 0 ? 'is-up' : 'is-down'">
              {{ returnRate(selectedHolding) >= 0 ? '▲' : '▼' }}
              {{ Math.abs(selectedHolding.currentPrice - selectedHolding.avgPrice).toLocaleString() }}원
              ({{ fmtRate(returnRate(selectedHolding)) }})
            </span>
          </div>

          <div class="hdc-metrics">
            <div class="hdc-metric">
              <span>보유 수량</span>
              <strong>{{ selectedHolding.qty }}주</strong>
            </div>
            <div class="hdc-metric">
              <span>평균 단가</span>
              <strong>{{ selectedHolding.avgPrice.toLocaleString() }}원</strong>
            </div>
            <div class="hdc-metric">
              <span>현재가</span>
              <strong>{{ selectedHolding.currentPrice.toLocaleString() }}원</strong>
            </div>
            <div class="hdc-metric">
              <span>평가 금액</span>
              <strong>{{ evalAmount(selectedHolding).toLocaleString() }}원</strong>
            </div>
            <div class="hdc-metric">
              <span>평가 손익</span>
              <strong :class="pnl(selectedHolding) >= 0 ? 'is-up' : 'is-down'">
                {{ pnl(selectedHolding) >= 0 ? '+' : '' }}{{ pnl(selectedHolding).toLocaleString() }}원
              </strong>
            </div>
            <div class="hdc-metric">
              <span>수익률</span>
              <strong :class="returnRate(selectedHolding) >= 0 ? 'is-up' : 'is-down'">
                {{ fmtRate(returnRate(selectedHolding)) }}
              </strong>
            </div>
          </div>

          <div class="hdc-action-btns">
            <button class="hdc-buy-btn">매수</button>
            <button class="hdc-sell-btn">매도</button>
          </div>
          <button
            class="hdc-detail-link"
            @click="router.push(`/stocks/${selectedHolding.code}`)"
          >
            종목 상세 보기 →
          </button>
        </div>

        <div class="panel holding-detail-empty" v-else>
          <span>👆</span>
          <p>종목을 클릭하면<br>상세 정보가 나타납니다</p>
        </div>

      </aside>
    </div>

  </div>
</template>

<style scoped>
.holdings-page { display: flex; flex-direction: column; gap: 16px; }

/* ===== 상단 섹션 ===== */
.top-section {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 200px;
  gap: 16px;
  align-items: stretch;
}

.asset-summary {
  padding: 20px 24px;
}

.asset-summary h1 {
  font-size: 28px;
  font-weight: 900;
  color: var(--ink);
  margin: 4px 0 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.summary-item > span {
  display: block;
  font-size: 12px;
  font-weight: 900;
  color: var(--muted);
  margin-bottom: 6px;
}

.summary-item strong {
  display: block;
  font-size: 24px;
  font-weight: 900;
  color: var(--ink);
  line-height: 1;
}

.summary-item strong small {
  font-size: 13px;
  font-weight: 700;
  color: var(--faint);
  margin-left: 2px;
}

.summary-item em {
  display: block;
  font-style: normal;
  font-size: 13px;
  font-weight: 900;
  margin-top: 4px;
}

.summary-item.tone-up strong { color: var(--positive); }
.summary-item.tone-down strong { color: var(--negative); }

/* 바로가기 패널 */
.shortcut-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shortcut-panel .eyebrow { margin-bottom: 0; }

.shortcuts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  flex: 1;
}

.shortcut-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 14px 10px;
  border-radius: var(--radius);
  background: rgba(49, 93, 255, 0.06);
  border: 1px solid rgba(49, 93, 255, 0.15);
  cursor: pointer;
  transition: background 0.18s;
  flex: 1;
}

.shortcut-btn:hover { background: rgba(49, 93, 255, 0.12); }

.sc-icon { font-size: 20px; }

.sc-label {
  font-size: 12px;
  font-weight: 900;
  color: var(--ink);
}

/* ===== 메인 레이아웃 ===== */
.holdings-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}

/* ===== 보유 종목 목록 ===== */
.holdings-panel { padding: 20px; }

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-head h2 {
  font-size: 16px;
  font-weight: 900;
  color: var(--ink);
}

.holdings-list { display: flex; flex-direction: column; gap: 4px; }

.holding-card {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto 80px;
  align-items: center;
  gap: 12px;
  padding: 12px 10px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.38);
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.16s, border-color 0.16s;
}

.holding-card:hover {
  background: rgba(255, 255, 255, 0.62);
  border-color: var(--glass-border);
}

.holding-card.is-selected {
  background: rgba(49, 93, 255, 0.06);
  border-color: rgba(49, 93, 255, 0.25);
}

.hc-logo {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 900;
  color: #fff;
  flex-shrink: 0;
}

.hc-info { min-width: 0; }

.hc-name {
  display: block;
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hc-sub {
  display: block;
  font-size: 11px;
  color: var(--faint);
  font-weight: 700;
  margin-top: 2px;
}

.hc-price-col { text-align: right; }

.hc-price {
  display: block;
  font-size: 13px;
  font-weight: 900;
}

.hc-rate {
  display: block;
  font-size: 12px;
  font-weight: 900;
  margin-top: 2px;
}

.hc-spark { display: flex; justify-content: flex-end; }

.spark-up :deep(.sparkline-line) { stroke: var(--positive); }
.spark-up :deep(.sparkline-fill) { fill: rgba(15,159,110,0.1); }
.spark-down :deep(.sparkline-line) { stroke: var(--negative); }
.spark-down :deep(.sparkline-fill) { fill: rgba(207,61,61,0.1); }

/* ===== 오른쪽 패널 ===== */
.right-panel { display: flex; flex-direction: column; gap: 14px; }

/* 자산 구성 */
.alloc-card { padding: 16px 18px; }

.alloc-bar-wrap { margin: 10px 0 12px; }

.alloc-bar {
  display: flex;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  gap: 2px;
}

.alloc-seg { height: 100%; border-radius: inherit; opacity: 0.85; }

.alloc-legend { display: flex; flex-direction: column; gap: 8px; }

.alloc-legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
}

.alloc-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.alloc-label { flex: 1; color: var(--ink); }
.alloc-amount { color: var(--muted); white-space: nowrap; }
.alloc-pct { color: var(--ink); font-weight: 900; min-width: 38px; text-align: right; white-space: nowrap; }

/* 선택 종목 상세 */
.holding-detail-card { padding: 0; overflow: hidden; }

.hdc-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
}

.hdc-logo {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 900;
  color: #fff;
  flex-shrink: 0;
}

.hdc-head-info { flex: 1; min-width: 0; }

.hdc-name {
  display: block;
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
}

.hdc-meta {
  display: block;
  font-size: 11px;
  color: var(--faint);
  font-weight: 700;
  margin-top: 2px;
}

.hdc-close {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}
.hdc-close:hover { background: rgba(255,255,255,0.85); color: var(--ink); }

.hdc-price-block {
  padding: 12px 16px 10px;
  border-bottom: 1px solid var(--line);
}

.hdc-price {
  display: block;
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -0.5px;
  margin-bottom: 4px;
}

.hdc-rate-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 900;
}

.hdc-metrics {
  padding: 10px 16px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px;
  border-bottom: 1px solid var(--line);
}

.hdc-metric {
  padding: 7px 4px;
}

.hdc-metric span {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: var(--faint);
  margin-bottom: 3px;
}

.hdc-metric strong {
  display: block;
  font-size: 13px;
  font-weight: 900;
  color: var(--ink);
}

.hdc-action-btns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 12px 16px 6px;
}

.hdc-buy-btn,
.hdc-sell-btn {
  height: 36px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: opacity 0.18s;
}

.hdc-buy-btn {
  background: rgba(49, 93, 255, 0.12);
  border: 1px solid rgba(49, 93, 255, 0.3);
  color: var(--accent);
}

.hdc-sell-btn {
  background: rgba(207, 61, 61, 0.1);
  border: 1px solid rgba(207, 61, 61, 0.3);
  color: var(--negative);
}

.hdc-buy-btn:hover { opacity: 0.8; }
.hdc-sell-btn:hover { opacity: 0.8; }

.hdc-detail-link {
  display: block;
  width: 100%;
  padding: 10px 16px;
  text-align: center;
  font-size: 13px;
  font-weight: 900;
  color: var(--accent);
  border: 0;
  background: transparent;
  cursor: pointer;
  border-top: 1px solid var(--line);
  transition: background 0.15s;
}
.hdc-detail-link:hover { background: rgba(49,93,255,0.05); }

.holding-detail-empty {
  padding: 40px 20px;
  text-align: center;
  color: var(--faint);
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
}
.holding-detail-empty span { font-size: 28px; display: block; margin-bottom: 8px; }

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
  cursor: pointer;
}

.segmented button.is-selected {
  background: rgba(255,255,255,0.85);
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.9);
}

.is-up { color: var(--positive); }
.is-down { color: var(--negative); }

@media (max-width: 1100px) {
  .top-section { grid-template-columns: 1fr; }
  .holdings-layout { grid-template-columns: 1fr; }
  .right-panel { display: grid; grid-template-columns: 1fr 1fr; }
}

@media (max-width: 800px) {
  .summary-grid { grid-template-columns: 1fr 1fr; }
  .right-panel { grid-template-columns: 1fr; }
}
</style>
