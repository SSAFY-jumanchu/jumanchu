<script setup>
import { inventory, stocks } from '../data/stocks.js'
import { useFormat } from '../composables/useFormat.js'
import SparklineChart from '../components/stock/SparklineChart.vue'

const { formatNumber } = useFormat()

const trendingStocks = stocks.slice(0, 3)

const marketIndices = [
  {
    name: '코스피',
    value: '2,720.45',
    change: '+8.35',
    rate: '+0.31%',
    up: true,
    sub: '개인 +84,455  외국인 -81,853',
    sparkline: [68, 70, 67, 72, 74, 71, 75, 73, 76, 79, 78, 81],
  },
  {
    name: '코스닥',
    value: '878.12',
    change: '-12.34',
    rate: '-1.38%',
    up: false,
    sub: '개인 대규모 순매도',
    sparkline: [82, 80, 78, 75, 77, 74, 72, 73, 70, 68, 66, 64],
  },
  {
    name: '달러 환율',
    value: '1,395.20',
    change: '+3.50',
    rate: '+0.25%',
    up: true,
    sub: '지정학적 불안',
    sparkline: [60, 61, 62, 61, 63, 64, 65, 64, 66, 67, 68, 69],
  },
  {
    name: 'VIX',
    value: '14.85',
    change: '-0.32',
    rate: '-2.11%',
    up: false,
    sparkline: [72, 70, 68, 66, 65, 63, 62, 60, 58, 57, 56, 55],
  },
  {
    name: 'S&P 500',
    value: '5,820.14',
    change: '+15.23',
    rate: '+0.26%',
    up: true,
    sparkline: [55, 57, 56, 59, 61, 63, 62, 65, 67, 69, 71, 73],
  },
  {
    name: '나스닥',
    value: '18,942.67',
    change: '+89.12',
    rate: '+0.47%',
    up: true,
    sparkline: [50, 53, 52, 56, 58, 61, 60, 64, 66, 69, 71, 74],
  },
  {
    name: '필라델피아 반도체',
    value: '5,234.18',
    change: '+112.45',
    rate: '+2.19%',
    up: true,
    sub: 'AI 반도체',
    sparkline: [44, 48, 47, 52, 55, 58, 62, 65, 68, 72, 75, 79],
  },
  {
    name: '비트코인',
    value: '97,452,000',
    change: '-1,240,000',
    rate: '-1.26%',
    up: false,
    sparkline: [80, 78, 82, 79, 76, 74, 71, 73, 70, 68, 66, 63],
  },
]

const schedule = [
  { date: '오늘', label: '노동시장 신규 구인건수(JOLTs) 발표', urgent: true },
  { date: '6/5 (목)', label: '비농업부문 고용변화량(ADP) 발표' },
  { date: '6/7 (토)', label: '미국 비농업 고용지수 발표' },
  { date: '6/11 (수)', label: 'FOMC 회의 (기준금리 결정)' },
  { date: '6/13 (금)', label: '미국 소비자물가지수(CPI) 발표' },
]
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">DB 기준일 2026-05-29</p>
        <h1>홈</h1>
      </div>
      <div class="top-actions">
        <label class="search-box">
          <span>검색</span>
          <input type="search" placeholder="종목명, 코드, 섹터" />
        </label>
        <div class="market-state">
          <span class="status-dot local"></span>
          샘플 모드
        </div>
      </div>
    </header>

    <!-- 데이터 인벤토리 -->
    <section class="summary-strip" aria-label="데이터 인벤토리">
      <article v-for="item in inventory" :key="item.label" class="metric-tile" :class="`tone-${item.tone}`">
        <span>{{ item.label }}</span>
        <strong>{{ formatNumber(item.value) }}</strong>
        <p>{{ item.helper }}</p>
        <code>{{ item.endpoint }}</code>
      </article>
    </section>

    <!-- 시장 지표 패널 -->
    <section class="panel market-pulse-panel" aria-label="시장 지표">
      <!-- 시장 상태 바 -->
      <div class="market-status-bar">
        <span class="mstatus-item">
          <span class="mstatus-dot open"></span>
          국내 애프터마켓 <em>15:30 ~ 20:00</em>
        </span>
        <span class="mstatus-item">
          <span class="mstatus-dot open"></span>
          해외 프리마켓 <em>17:00 ~ 22:30</em>
        </span>
      </div>

      <!-- 지표 + 일정 레이아웃 -->
      <div class="market-body">
        <div class="indices-scroll" role="list">
          <article
            v-for="idx in marketIndices"
            :key="idx.name"
            class="index-card"
            :class="idx.up ? 'is-up-card' : 'is-down-card'"
            role="listitem"
          >
            <div class="index-top">
              <span class="index-name">{{ idx.name }}</span>
              <SparklineChart
                :values="idx.sparkline"
                :width="80"
                :height="36"
                class="index-spark"
                :class="idx.up ? 'spark-up' : 'spark-down'"
              />
            </div>
            <div class="index-value">{{ idx.value }}</div>
            <div class="index-change" :class="idx.up ? 'is-up' : 'is-down'">
              {{ idx.change }} <span class="index-rate">({{ idx.rate }})</span>
            </div>
            <div v-if="idx.sub" class="index-sub">{{ idx.sub }}</div>
          </article>
        </div>

        <!-- 주요 일정 -->
        <aside class="schedule-aside" aria-label="주요 일정">
          <p class="eyebrow" style="margin-bottom: 12px;">주요 일정</p>
          <ul class="schedule-list">
            <li v-for="item in schedule" :key="item.label" class="schedule-item" :class="{ urgent: item.urgent }">
              <span class="schedule-date">{{ item.date }}</span>
              <span class="schedule-label">{{ item.label }}</span>
            </li>
          </ul>
        </aside>
      </div>
    </section>

    <!-- 트렌딩 추천 미리보기 -->
    <section class="panel trending-preview" aria-labelledby="trending-heading">
      <div class="panel-head">
        <div>
          <p class="eyebrow">트렌드 기반 추천</p>
          <h2 id="trending-heading">오늘의 추천 종목</h2>
        </div>
        <RouterLink to="/discover" class="see-all-link">발견하러 가기 →</RouterLink>
      </div>

      <div class="trending-grid">
        <article v-for="stock in trendingStocks" :key="stock.code" class="trending-card">
          <div class="trending-badge">{{ stock.sector }}</div>
          <h3>{{ stock.name }}</h3>
          <p>{{ stock.reason }}</p>
          <div class="trending-footer">
            <span class="trending-stance">{{ stock.stance }}</span>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ===== 시장 지표 패널 ===== */
.market-pulse-panel {
  margin-bottom: 18px;
  padding: 0;
  overflow: hidden;
}

.market-status-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 18px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.38);
}

.mstatus-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.mstatus-item em {
  font-style: normal;
  color: var(--ink);
}

.mstatus-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--faint);
  flex-shrink: 0;
}

.mstatus-dot.open {
  background: var(--positive);
  box-shadow: 0 0 0 2.5px rgba(15, 159, 110, 0.22);
}

.market-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  align-items: start;
}

.indices-scroll {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  padding: 0;
}

.index-card {
  padding: 16px 18px;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  transition: background 0.16s ease;
  cursor: pointer;
}

.index-card:hover {
  background: rgba(255, 255, 255, 0.48);
}

.index-card:nth-child(4n) {
  border-right: 0;
}

.index-card:nth-last-child(-n+4) {
  border-bottom: 0;
}

.index-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.index-name {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  line-height: 1.3;
  word-break: keep-all;
}

.index-spark {
  flex-shrink: 0;
  width: 72px;
  height: 32px;
}

/* 상승 카드는 파란 sparkline, 하락 카드는 빨간 sparkline */
.index-card.is-up-card :deep(.sparkline-line) {
  stroke: var(--accent);
}
.index-card.is-up-card :deep(.sparkline-fill) {
  fill: rgba(49, 93, 255, 0.08);
}
.index-card.is-down-card :deep(.sparkline-line) {
  stroke: var(--negative);
}
.index-card.is-down-card :deep(.sparkline-fill) {
  fill: rgba(207, 61, 61, 0.08);
}

.index-value {
  color: var(--ink);
  font-size: 20px;
  font-weight: 900;
  letter-spacing: -0.5px;
  line-height: 1.15;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.index-change {
  font-size: 13px;
  font-weight: 900;
}

.index-rate {
  font-weight: 700;
  opacity: 0.85;
}

.index-sub {
  margin-top: 5px;
  color: var(--faint);
  font-size: 11px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 주요 일정 */
.schedule-aside {
  padding: 16px 18px;
  border-left: 1px solid var(--line);
  height: 100%;
}

.schedule-list {
  display: grid;
  gap: 10px;
  padding: 0;
  margin: 0;
  list-style: none;
}

.schedule-item {
  display: grid;
  grid-template-columns: 70px 1fr;
  gap: 8px;
  align-items: baseline;
}

.schedule-item.urgent .schedule-date {
  color: var(--accent);
}

.schedule-item.urgent .schedule-label {
  color: var(--ink);
}

.schedule-date {
  color: var(--faint);
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.schedule-label {
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  line-height: 1.4;
  word-break: keep-all;
}

/* 반응형 */
@media (max-width: 1180px) {
  .market-body {
    grid-template-columns: 1fr;
  }

  .indices-scroll {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .schedule-aside {
    border-left: 0;
    border-top: 1px solid var(--line);
  }
}

@media (max-width: 760px) {
  .indices-scroll {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .index-card:nth-child(4n) {
    border-right: 1px solid var(--line);
  }

  .index-card:nth-child(2n) {
    border-right: 0;
  }
}

/* ===== 트렌딩 추천 ===== */
.trending-preview {
  margin-top: 18px;
}

.see-all-link {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(49, 93, 255, 0.1);
  border: 1px solid rgba(49, 93, 255, 0.25);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
  transition: background 0.18s ease;
}

.see-all-link:hover {
  background: rgba(49, 93, 255, 0.18);
}

.trending-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.trending-card {
  padding: 16px;
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.52);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow), var(--glass-inset);
}

.trending-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(49, 93, 255, 0.1);
  border: 1px solid rgba(49, 93, 255, 0.2);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  margin-bottom: 10px;
}

.trending-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--ink);
}

.trending-card p {
  margin: 0 0 14px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
  word-break: keep-all;
}

.trending-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.trending-stance {
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
}

@media (max-width: 900px) {
  .trending-grid {
    grid-template-columns: 1fr;
  }
}
</style>
