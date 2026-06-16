<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import SparklineChart from '../components/stock/SparklineChart.vue'
import { useFormat } from '../composables/useFormat.js'

// ── 보유 종목 (와이어프레임 image41) ──
// 백엔드: holding + account + stock + KIS 현재가 (image42 — 새 테이블 0)
//   평가금액 = 수량 × 현재가 / 평가손익 = (현재가 − 평단) × 수량 / 수익률 = 손익 / (평단×수량)
const { formatMoney, formatRate, signedClass } = useFormat()

const summary = {
  totalValue: 23910000,
  totalPnl: 3260000,
  totalPnlRate: 15.78,
  totalCost: 20650000,
  domesticValue: 6760000,
  overseasValue: 17160000,
}
const domesticRate = computed(() => (summary.domesticValue / summary.totalValue) * 100)
const overseasRate = computed(() => (summary.overseasValue / summary.totalValue) * 100)

const holdings = [
  { code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '전기·전자', region: '국내', currency: 'KRW', code2: 'SK', color: '#e6007e', qty: 15, avg: 172000, current: 189300, spark: [60, 62, 61, 64, 66, 69, 72, 70, 74, 77, 80, 84] },
  { code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자', region: '국내', currency: 'KRW', code2: '삼', color: '#315dff', qty: 40, avg: 73500, current: 71200, spark: [72, 70, 71, 68, 66, 64, 65, 63, 62, 60, 61, 59] },
  { code: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', sector: '반도체', region: '해외', currency: 'USD', code2: 'NV', color: '#0f9f6e', qty: 8, avg: 820, current: 1074, spark: [50, 54, 58, 62, 66, 70, 74, 79, 83, 86, 90, 94] },
  { code: 'AAPL', name: 'Apple', market: 'NASDAQ', sector: 'IT·소비재', region: '해외', currency: 'USD', code2: 'A', color: '#7d4ee8', qty: 20, avg: 185, current: 192, spark: [58, 60, 59, 62, 64, 63, 66, 68, 67, 70, 72, 71] },
  { code: '035420', name: 'NAVER', market: 'KOSPI', sector: 'IT·소프트웨어', region: '국내', currency: 'KRW', code2: 'N', color: '#03c75a', qty: 5, avg: 195000, current: 214000, spark: [55, 57, 56, 60, 63, 67, 70, 73, 76, 79, 82, 85] },
]

function evalValue(h) { return h.current * h.qty }
function pnl(h) { return (h.current - h.avg) * h.qty }
function pnlRate(h) { return ((h.current - h.avg) / h.avg) * 100 }

const filters = ['전체', '국내', '해외']
const activeFilter = ref('전체')
const filteredHoldings = computed(() =>
  activeFilter.value === '전체' ? holdings : holdings.filter((h) => h.region === activeFilter.value),
)

const selectedCode = ref('000660')
const selected = computed(() => holdings.find((h) => h.code === selectedCode.value) || holdings[0])

function manwon(n) { return `${Math.round(n / 10000).toLocaleString('ko-KR')}만원` }
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">My Holdings</p>
        <h1>보유 종목</h1>
      </div>
      <span class="profile-pill">가상 계좌 기준</span>
    </header>

    <!-- 자산 요약 -->
    <section class="panel asset-summary">
      <div class="as-metrics">
        <div><span>현재 총 평가액</span><strong>{{ manwon(summary.totalValue) }}</strong></div>
        <div>
          <span>총 평가 손익</span>
          <strong :class="signedClass(summary.totalPnl)">
            +{{ manwon(summary.totalPnl) }} ({{ formatRate(summary.totalPnlRate) }})
          </strong>
        </div>
        <div><span>총 투자원금</span><strong>{{ manwon(summary.totalCost) }}</strong></div>
      </div>

      <div class="as-shortcuts">
        <p class="eyebrow">바로가기</p>
        <RouterLink to="/profile" class="shortcut">📄 주문내역</RouterLink>
        <RouterLink to="/diary" class="shortcut">📔 매매일지</RouterLink>
      </div>

      <div class="as-composition">
        <p class="eyebrow">자산 구성 (국내·해외)</p>
        <div class="comp-bar">
          <span class="comp-seg domestic" :style="{ width: `${domesticRate}%` }"></span>
          <span class="comp-seg overseas" :style="{ width: `${overseasRate}%` }"></span>
        </div>
        <ul class="comp-legend">
          <li><span class="dot domestic"></span>국내주식 <strong>{{ manwon(summary.domesticValue) }}</strong> · {{ domesticRate.toFixed(1) }}%</li>
          <li><span class="dot overseas"></span>해외주식 <strong>{{ manwon(summary.overseasValue) }}</strong> · {{ overseasRate.toFixed(1) }}%</li>
        </ul>
      </div>
    </section>

    <div class="holdings-layout">
      <!-- 보유 종목 목록 -->
      <section class="panel">
        <div class="panel-head">
          <div><p class="eyebrow">Holdings</p><h2>보유 종목 목록</h2></div>
          <div class="segmented" aria-label="지역 필터">
            <button v-for="f in filters" :key="f" type="button" :class="{ 'is-selected': activeFilter === f }" @click="activeFilter = f">{{ f }}</button>
          </div>
        </div>

        <div class="hold-list">
          <button
            v-for="h in filteredHoldings"
            :key="h.code"
            type="button"
            class="hold-row"
            :class="{ 'is-selected': selectedCode === h.code }"
            @click="selectedCode = h.code"
          >
            <span class="hold-logo" :style="{ background: h.color }">{{ h.code2 }}</span>
            <span class="hold-info">
              <span class="hold-name">{{ h.name }}</span>
              <span class="hold-sub">{{ h.market }} · {{ h.sector }} · {{ h.qty }}주 · 평단 {{ formatMoney(h.avg, h.currency) }}</span>
            </span>
            <SparklineChart :values="h.spark" :width="80" :height="34" class="hold-spark" :class="pnl(h) >= 0 ? 'spark-up' : 'spark-down'" />
            <span class="hold-figures">
              <span class="hold-value">{{ formatMoney(evalValue(h), h.currency) }}</span>
              <span class="hold-pnl" :class="signedClass(pnl(h))">{{ pnl(h) > 0 ? '+' : '' }}{{ formatMoney(pnl(h), h.currency) }} ({{ formatRate(pnlRate(h)) }})</span>
            </span>
          </button>
        </div>
      </section>

      <!-- 우측 상세 패널 -->
      <aside class="panel hold-detail">
        <div class="hd-head">
          <div>
            <h2>{{ selected.name }}</h2>
            <p>{{ selected.code }} · {{ selected.market }}</p>
          </div>
          <span class="hold-logo lg" :style="{ background: selected.color }">{{ selected.code2 }}</span>
        </div>

        <dl class="hd-list">
          <div><dt>보유 수량</dt><dd>{{ selected.qty }}주</dd></div>
          <div><dt>평균 단가</dt><dd>{{ formatMoney(selected.avg, selected.currency) }}</dd></div>
          <div><dt>현재가</dt><dd>{{ formatMoney(selected.current, selected.currency) }}</dd></div>
          <div><dt>평가 금액</dt><dd>{{ formatMoney(evalValue(selected), selected.currency) }}</dd></div>
          <div><dt>평가 손익</dt><dd :class="signedClass(pnl(selected))">{{ pnl(selected) > 0 ? '+' : '' }}{{ formatMoney(pnl(selected), selected.currency) }}</dd></div>
          <div><dt>수익률</dt><dd :class="signedClass(pnl(selected))">{{ formatRate(pnlRate(selected)) }}</dd></div>
        </dl>

        <div class="hd-actions">
          <RouterLink :to="`/stocks/${selected.code}`" class="hd-btn buy">매수</RouterLink>
          <RouterLink :to="`/stocks/${selected.code}`" class="hd-btn sell">매도</RouterLink>
        </div>
        <RouterLink :to="`/stocks/${selected.code}`" class="hd-detail-link">종목 상세 보기 →</RouterLink>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.is-up { color: var(--positive); }
.is-down { color: var(--negative); }
.is-flat { color: var(--muted); }

/* 자산 요약 */
.asset-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) 180px minmax(0, 1.3fr);
  gap: 24px;
  margin-bottom: 16px;
  align-items: center;
}
.as-metrics { display: grid; gap: 14px; }
.as-metrics > div { display: flex; flex-direction: column; gap: 4px; }
.as-metrics span { color: var(--muted); font-size: 13px; font-weight: 900; }
.as-metrics strong { color: var(--ink); font-size: 22px; letter-spacing: -0.5px; }

.as-shortcuts { display: grid; gap: 8px; align-content: start; }
.shortcut {
  display: flex; align-items: center; gap: 6px;
  min-height: 38px; padding: 0 12px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid var(--glass-border);
  color: var(--ink); font-size: 13px; font-weight: 900;
  transition: background 0.16s ease;
}
.shortcut:hover { background: rgba(255, 255, 255, 0.75); }

.comp-bar { display: flex; height: 12px; border-radius: 999px; overflow: hidden; margin: 8px 0 12px; background: rgba(180, 200, 255, 0.3); }
.comp-seg.domestic { background: var(--accent); }
.comp-seg.overseas { background: var(--purple); }
.comp-legend { display: grid; gap: 6px; margin: 0; padding: 0; list-style: none; }
.comp-legend li { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }
.comp-legend strong { color: var(--ink); }
.dot { width: 9px; height: 9px; border-radius: 50%; }
.dot.domestic { background: var(--accent); }
.dot.overseas { background: var(--purple); }

/* 레이아웃 */
.holdings-layout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }

.hold-list { display: grid; gap: 8px; }
.hold-row {
  display: grid;
  grid-template-columns: 40px minmax(0, 1fr) 80px minmax(0, auto);
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.48);
  border: 1px solid var(--glass-border);
  text-align: left;
  transition: background 0.16s ease, border-color 0.16s ease;
}
.hold-row:hover { background: rgba(255, 255, 255, 0.7); }
.hold-row.is-selected { border-color: var(--accent); background: rgba(49, 93, 255, 0.06); }
.hold-logo { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 900; flex-shrink: 0; }
.hold-logo.lg { width: 44px; height: 44px; border-radius: 12px; font-size: 15px; }
.hold-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.hold-name { color: var(--ink); font-size: 15px; font-weight: 900; }
.hold-sub { color: var(--muted); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hold-spark { flex-shrink: 0; }
.hold-spark.spark-up :deep(.sparkline-line) { stroke: var(--positive); }
.hold-spark.spark-down :deep(.sparkline-line) { stroke: var(--negative); }
.hold-figures { display: flex; flex-direction: column; gap: 3px; text-align: right; white-space: nowrap; }
.hold-value { color: var(--ink); font-size: 15px; font-weight: 900; }
.hold-pnl { font-size: 12px; font-weight: 900; }

/* 상세 패널 */
.hold-detail { position: sticky; top: 80px; }
.hd-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.hd-head h2 { margin: 0; font-size: 19px; }
.hd-head p { margin: 2px 0 0; color: var(--muted); font-size: 12px; }
.hd-list { display: grid; gap: 0; margin: 0 0 16px; }
.hd-list > div { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--line); }
.hd-list > div:last-child { border-bottom: 0; }
.hd-list dt { color: var(--muted); font-size: 13px; }
.hd-list dd { margin: 0; color: var(--ink); font-size: 14px; font-weight: 900; }
.hd-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; }
.hd-btn { min-height: 44px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius); color: #fff; font-size: 15px; font-weight: 900; }
.hd-btn.buy { background: linear-gradient(135deg, var(--accent) 0%, #2f80ed 100%); }
.hd-btn.sell { background: linear-gradient(135deg, var(--negative) 0%, #e05a5a 100%); }
.hd-detail-link { display: block; text-align: center; padding: 10px; border-radius: var(--radius); background: rgba(49, 93, 255, 0.08); color: var(--accent); font-size: 13px; font-weight: 900; }

@media (max-width: 1080px) {
  .asset-summary { grid-template-columns: 1fr; }
  .holdings-layout { grid-template-columns: 1fr; }
  .hold-detail { position: static; }
}
@media (max-width: 640px) {
  .hold-row { grid-template-columns: 36px minmax(0, 1fr) auto; }
  .hold-spark { display: none; }
}
</style>
