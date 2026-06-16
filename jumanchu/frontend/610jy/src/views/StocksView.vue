<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import SparklineChart from '../components/stock/SparklineChart.vue'
import { stocks } from '../data/stocks.js'
import { useFormat } from '../composables/useFormat.js'

// ── 주식 조회 (와이어프레임 image40) ──
// 백엔드: GET /stocks/?market=&sort= (목록) + /stocks/{code}/price/ + /posts/ + stock_news
const { formatMoney, formatRate, formatCompact, signedClass } = useFormat()

// 종목별 핵심 뉴스 (stock_news 목업)
const headlines = {
  '005930': '반도체 업황 회복 기대… 외국인 순매수 전환',
  '000660': 'HBM 수요 지속 전망, 증권가 목표가 상향',
  '005380': '전기차 판매 둔화 우려에 약세',
  AAPL: '신제품 사이클 기대감에 강보합',
  NVDA: 'AI 가속기 수요 강세, 사상 최고가 경신',
  GOOGL: '광고 매출 회복… 클라우드 성장 지속',
}

function change(s) { return s.price - s.open }
function changeRate(s) { return s.open ? (change(s) / s.open) * 100 : 0 }
function tradingValue(s) { return s.price * s.volume }

const filters = ['전체', '국내', '해외']
const activeFilter = ref('전체')

const sorts = ['실시간', '상승률', '하락률', '거래대금']
const activeSort = ref('실시간')

const list = computed(() => {
  let arr = stocks.slice()
  if (activeFilter.value === '국내') arr = arr.filter((s) => ['KOSPI', 'KOSDAQ'].includes(s.market))
  if (activeFilter.value === '해외') arr = arr.filter((s) => ['NASDAQ', 'NYSE'].includes(s.market))
  if (activeSort.value === '상승률') arr.sort((a, b) => changeRate(b) - changeRate(a))
  else if (activeSort.value === '하락률') arr.sort((a, b) => changeRate(a) - changeRate(b))
  else if (activeSort.value === '거래대금') arr.sort((a, b) => tradingValue(b) - tradingValue(a))
  return arr
})

const selectedCode = ref('000660')
const selected = computed(() => stocks.find((s) => s.code === selectedCode.value) || stocks[0])

const stockPosts = [
  { id: 1, nickname: '주린이탈출', title: '여기 지금 들어가도 되나요?', time: '12분 전' },
  { id: 2, nickname: '존버왕', title: '실적 발표 후 흐름 정리', time: '1시간 전' },
]
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">종목별 시세와 핵심 뉴스를 한눈에</p>
        <h1>주식 조회</h1>
      </div>
      <div class="top-actions">
        <label class="search-box">
          <span>검색</span>
          <input type="search" placeholder="종목명, 코드, 섹터" />
        </label>
      </div>
    </header>

    <div class="stocks-toolbar">
      <div class="segmented" aria-label="시장 필터">
        <button v-for="f in filters" :key="f" type="button" :class="{ 'is-selected': activeFilter === f }" @click="activeFilter = f">{{ f }}</button>
      </div>
      <div class="segmented" aria-label="정렬">
        <button v-for="s in sorts" :key="s" type="button" :class="{ 'is-selected': activeSort === s }" @click="activeSort = s">{{ s }}</button>
      </div>
    </div>

    <div class="stocks-layout">
      <!-- 목록 -->
      <section class="panel">
        <div class="slist-head">
          <span>종목 · 핵심 뉴스</span>
          <span>차트</span>
          <span class="num">현재가 · 등락</span>
        </div>
        <div class="slist">
          <button
            v-for="(s, i) in list"
            :key="s.code"
            type="button"
            class="srow"
            :class="{ 'is-selected': selectedCode === s.code }"
            @click="selectedCode = s.code"
          >
            <span class="srow-rank">{{ i + 1 }}</span>
            <span class="srow-info">
              <span class="srow-name">{{ s.name }}</span>
              <span class="srow-meta">{{ s.market }} · {{ s.sector }} · 거래대금 {{ formatCompact(tradingValue(s)) }}</span>
              <span class="srow-news">{{ headlines[s.code] || '관련 뉴스 준비 중' }}</span>
            </span>
            <SparklineChart :values="s.sparkline" :width="90" :height="38" class="srow-spark" :class="change(s) >= 0 ? 'spark-up' : 'spark-down'" />
            <span class="srow-figures">
              <span class="srow-price">{{ formatMoney(s.price, s.currency) }}</span>
              <span class="srow-rate" :class="signedClass(changeRate(s))">{{ change(s) > 0 ? '▲' : '▼' }} {{ formatMoney(Math.abs(change(s)), s.currency) }} ({{ formatRate(changeRate(s)) }})</span>
            </span>
          </button>
        </div>
      </section>

      <!-- 우측 상세 -->
      <aside class="panel sdetail">
        <div class="sd-head">
          <div>
            <h2>{{ selected.name }}</h2>
            <p>{{ selected.code }} · {{ selected.market }}</p>
          </div>
        </div>
        <div class="sd-price">
          <strong>{{ formatMoney(selected.price, selected.currency) }}</strong>
          <span :class="signedClass(changeRate(selected))">
            {{ change(selected) > 0 ? '▲' : '▼' }} {{ formatMoney(Math.abs(change(selected)), selected.currency) }} ({{ formatRate(changeRate(selected)) }})
          </span>
        </div>
        <SparklineChart :values="selected.sparkline" :width="280" :height="80" class="sd-spark" :class="change(selected) >= 0 ? 'spark-up' : 'spark-down'" />

        <div class="sd-section">
          <p class="eyebrow">관련 뉴스</p>
          <p class="sd-news">{{ headlines[selected.code] || '관련 뉴스 준비 중' }}</p>
        </div>

        <div class="sd-section">
          <p class="eyebrow">종목토론</p>
          <div class="sd-posts">
            <div v-for="p in stockPosts" :key="p.id" class="sd-post">
              <span class="sd-post-author">{{ p.nickname }}</span>
              <span class="sd-post-title">{{ p.title }}</span>
              <span class="sd-post-time">{{ p.time }}</span>
            </div>
          </div>
        </div>

        <RouterLink :to="`/stocks/${selected.code}`" class="sd-detail-btn">종목 상세 보기 →</RouterLink>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.is-up { color: var(--positive); }
.is-down { color: var(--negative); }
.is-flat { color: var(--muted); }

.stocks-toolbar { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }

.stocks-layout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }

.slist-head {
  display: grid; grid-template-columns: minmax(0, 1fr) 90px 160px;
  gap: 12px; padding: 0 12px 10px; border-bottom: 1px solid var(--line);
  color: var(--muted); font-size: 12px; font-weight: 900;
}
.slist-head .num { text-align: right; }
.slist { display: grid; gap: 4px; padding-top: 6px; }
.srow {
  display: grid; grid-template-columns: 24px minmax(0, 1fr) 90px 160px;
  align-items: center; gap: 12px; padding: 12px; border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.42); border: 1px solid transparent; text-align: left;
  transition: background 0.16s ease, border-color 0.16s ease;
}
.srow:hover { background: rgba(255, 255, 255, 0.7); }
.srow.is-selected { border-color: var(--accent); background: rgba(49, 93, 255, 0.06); }
.srow-rank { color: var(--faint); font-size: 14px; font-weight: 900; text-align: center; }
.srow-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.srow-name { color: var(--ink); font-size: 15px; font-weight: 900; }
.srow-meta { color: var(--muted); font-size: 11px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.srow-news { color: var(--faint); font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.srow-spark { flex-shrink: 0; }
.srow-spark.spark-up :deep(.sparkline-line) { stroke: var(--positive); }
.srow-spark.spark-down :deep(.sparkline-line) { stroke: var(--negative); }
.srow-figures { display: flex; flex-direction: column; gap: 3px; text-align: right; white-space: nowrap; }
.srow-price { color: var(--ink); font-size: 15px; font-weight: 900; }
.srow-rate { font-size: 12px; font-weight: 900; }

/* 우측 상세 */
.sdetail { position: sticky; top: 80px; }
.sd-head h2 { margin: 0; font-size: 19px; }
.sd-head p { margin: 2px 0 12px; color: var(--muted); font-size: 12px; }
.sd-price { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.sd-price strong { font-size: 24px; color: var(--ink); letter-spacing: -0.5px; }
.sd-price span { font-size: 13px; font-weight: 900; }
.sd-spark { width: 100%; margin-bottom: 16px; }
.sd-spark.spark-up :deep(.sparkline-line) { stroke: var(--positive); }
.sd-spark.spark-down :deep(.sparkline-line) { stroke: var(--negative); }
.sd-section { padding: 14px 0; border-top: 1px solid var(--line); }
.sd-news { margin: 8px 0 0; color: var(--ink); font-size: 13px; line-height: 1.5; word-break: keep-all; }
.sd-posts { display: grid; gap: 8px; margin-top: 8px; }
.sd-post { display: flex; flex-direction: column; gap: 2px; }
.sd-post-author { color: var(--accent); font-size: 11px; font-weight: 900; }
.sd-post-title { color: var(--ink); font-size: 13px; font-weight: 900; }
.sd-post-time { color: var(--faint); font-size: 11px; }
.sd-detail-btn { display: block; text-align: center; margin-top: 14px; min-height: 46px; line-height: 46px; border-radius: var(--radius); background: linear-gradient(135deg, var(--accent) 0%, #2f80ed 100%); color: #fff; font-size: 14px; font-weight: 900; }

@media (max-width: 1080px) {
  .stocks-layout { grid-template-columns: 1fr; }
  .sdetail { position: static; }
}
@media (max-width: 640px) {
  .slist-head { grid-template-columns: 1fr auto; }
  .slist-head span:nth-child(2) { display: none; }
  .srow { grid-template-columns: 20px minmax(0, 1fr) auto; }
  .srow-spark { display: none; }
}
</style>
