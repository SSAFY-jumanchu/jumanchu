<script setup>
import { ref, onMounted } from 'vue'
import SparklineChart from '../components/SparklineChart.vue'
import NewspaperSwipeBanner from '../components/NewspaperSwipeBanner.vue'
import { useRouter } from 'vue-router'
import { stocksApi, portfolioApi } from '../api'

const router = useRouter()

// 초기값은 와이어프레임 목업 — API 응답이 오면 실데이터로 교체
const marketIndices = ref([
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
])

const generalNews = [
  { title: 'FOMC 금리 동결 가능성 높아져...시장 반응은?', source: '한국경제', time: '1시간 전', category: '금리' },
  { title: '반도체 수출 전월 대비 18% 증가, 하이닉스 수혜', source: '매일경제', time: '2시간 전', category: '반도체' },
  { title: 'S&P500 신고가 경신...나스닥도 동반 상승', source: '연합뉴스', time: '3시간 전', category: '해외' },
  { title: '코스피 2720선 회복, 외국인 선물 매수 전환', source: '서울경제', time: '4시간 전', category: '코스피' },
]

const holdings = ref([
  { name: '삼성전자', ticker: '005930', qty: 20, avg: 310500, cur: 317000, color: '#315dff' },
  { name: 'SK하이닉스', ticker: '000660', qty: 10, avg: 238000, cur: 243000, color: '#7d4ee8' },
  { name: 'NVIDIA',   ticker: 'NVDA',   qty: 3,  avg: 1251000, cur: 1285000, color: '#22c55e' },
  { name: 'NAVER',    ticker: '035420', qty: 8,  avg: 189500, cur: 184000, color: '#f59e0b' },
  { name: 'APPLE',    ticker: 'AAPL',   qty: 2,  avg: 248000, cur: 261000, color: '#06b6d4' },
])

const holdingColors = ['#315dff', '#7d4ee8', '#22c55e', '#f59e0b', '#06b6d4']
const defaultSpark = [60, 62, 61, 63, 65, 64, 66, 68, 67, 69, 71, 70]

onMounted(async () => {
  // 시장 지표: GET /api/v1/markets/summary/
  try {
    const { data } = await stocksApi.marketSummary()
    if (data.indices?.length) {
      marketIndices.value = data.indices.map((idx) => ({
        name: idx.name,
        value: idx.current.toLocaleString('ko-KR'),
        change: (idx.change >= 0 ? '+' : '') + idx.change.toLocaleString('ko-KR'),
        rate: (idx.change_rate >= 0 ? '+' : '') + idx.change_rate.toFixed(2) + '%',
        up: idx.change >= 0,
        sub: '',
        sparkline: defaultSpark,
      }))
    }
  } catch (e) {
    console.warn('시장 지표 로드 실패 — 목업 유지', e)
  }

  // 보유 종목 미리보기: GET /api/v1/portfolio/
  try {
    const { data } = await portfolioApi.summary()
    if (data.holdings_preview?.length) {
      holdings.value = data.holdings_preview.map((h, i) => ({
        name: h.stock.name,
        ticker: h.stock.code,
        qty: h.quantity,
        avg: Number(h.average_price),
        cur: Number(h.current_price),
        color: holdingColors[i % holdingColors.length],
      }))
    }
  } catch (e) {
    console.warn('포트폴리오 로드 실패 — 목업 유지', e)
  }
})

const recentDiaries = [
  { date: '2026-06-10', stock: 'APPLE',    ticker: 'AAPL',   type: 'hold', title: 'WWDC 전 홀딩 전략' },
  { date: '2026-06-05', stock: '삼성전자', ticker: '005930', type: 'buy',  title: '오늘 매수 이유' },
  { date: '2026-06-04', stock: 'SK하이닉스', ticker: '000660', type: 'sell', title: '단기 수익 실현' },
]
const diaryTypeColor = { buy: '#315dff', sell: '#ef4444', hold: '#f59e0b' }
const diaryTypeLabel = { buy: '매수', sell: '매도', hold: '홀딩' }

function fmt(n) { return n.toLocaleString('ko-KR') }

const watchlistNews = [
  { title: 'SK하이닉스, HBM3E 양산 확대...AI 수요 견조', source: '이데일리', time: '30분 전', ticker: 'SK하이닉스' },
  { title: '삼성전자, 파운드리 수주 회복세...2분기 기대감', source: '전자신문', time: '1시간 전', ticker: '삼성전자' },
  { title: 'NVIDIA 실적 서프라이즈...관련 국내주 수혜', source: 'Bloomberg', time: '2시간 전', ticker: 'NVDA' },
  { title: '애플 WWDC AI 기능 대거 공개 예정', source: '디지털데일리', time: '3시간 전', ticker: 'AAPL' },
]
</script>

<template>
  <div class="home-page">

    <!-- ===== 섹션 1: 자산 목표 + 스와이핑 추천 ===== -->
    <div class="hero-grid">

      <!-- 왼쪽: 현재 총 자산 가치 및 다음 목표 -->
      <section class="panel goal-panel" aria-label="자산 현황 및 목표">
        <div class="panel-head">
          <div>
            <p class="eyebrow">현재 총 자산 가치 및 다음 목표</p>
            <h2>자산 현황</h2>
          </div>
        </div>

        <div class="goal-list">
          <!-- 현재 진행중인 목표 -->
          <div class="goal-card target">
            <div class="goal-card-icon">🖥️</div>
            <div class="goal-card-info">
              <span class="goal-card-label">다음 목표</span>
              <strong class="goal-card-name">게이밍 데스크탑</strong>
              <span class="goal-card-amount">목표 3,500,000원</span>
            </div>
            <span class="goal-badge in-progress">진행중</span>
          </div>

          <!-- 진행률 바 -->
          <div class="goal-track-wrap">
            <div class="goal-track-bar">
              <div class="goal-track-fill" style="width: 13%"></div>
            </div>
            <span class="goal-track-pct">13% 달성</span>
          </div>

          <!-- 이전 달성 목표 -->
          <div class="goal-card achieved">
            <div class="goal-card-icon">🚗</div>
            <div class="goal-card-info">
              <span class="goal-card-label">달성 완료</span>
              <strong class="goal-card-name">국산 정차</strong>
              <span class="goal-card-amount">45,000,000원</span>
            </div>
            <span class="goal-badge done">달성</span>
          </div>
        </div>

        <!-- 다음 투자 추천 전략 -->
        <div class="recommendation-box">
          <p class="eyebrow" style="color: var(--purple);">다음 추천 전략</p>
          <strong class="recommendation-title">공격형 · 반도체 우선 매점</strong>
          <p class="recommendation-desc">
            단계를 위한 투자 포트폴리오 조정이 필요합니다.
            현재 목표와 연결된 반도체 섹터 비중 확대를 추천합니다.
          </p>
        </div>
      </section>

      <!-- 오른쪽: 스와이핑 주식 추천 (신문 넘기기) -->
      <section class="swipe-recommend-panel" aria-label="스와이핑 주식 추천">
        <div class="swipe-recommend-header">
          <p class="eyebrow">AI 기반 추천</p>
          <h2>스와이핑 주식 추천</h2>
        </div>

        <NewspaperSwipeBanner />
      </section>
    </div>

    <!-- ===== 섹션 2: 시장 지표 ===== -->
    <section class="panel market-section" aria-label="시장 지표">
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

      <!-- 4개 지표 카드 -->
      <div class="market-indices-grid">
        <article
          v-for="idx in marketIndices"
          :key="idx.name"
          class="index-card"
          :class="idx.up ? 'is-up-card' : 'is-down-card'"
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
    </section>

    <!-- ===== 섹션 3: 경제 뉴스 ===== -->
    <div class="news-grid">

      <!-- 종합 뉴스 -->
      <section class="panel news-panel" aria-label="종합 뉴스">
        <div class="panel-head">
          <div>
            <p class="eyebrow">최신 경제 뉴스</p>
            <h2>종합 뉴스</h2>
          </div>
          <button class="more-btn">더보기 →</button>
        </div>

        <div class="news-list">
          <article v-for="item in generalNews" :key="item.title" class="news-item">
            <div class="news-meta">
              <span class="news-category">{{ item.category }}</span>
              <span class="news-time">{{ item.time }}</span>
            </div>
            <h4 class="news-title">{{ item.title }}</h4>
            <span class="news-source">{{ item.source }}</span>
          </article>
        </div>
      </section>

      <!-- 관심 종목 뉴스 -->
      <section class="panel news-panel" aria-label="관심 종목 뉴스">
        <div class="panel-head">
          <div>
            <p class="eyebrow">내 관심 종목 소식</p>
            <h2>관심 종목 뉴스</h2>
          </div>
          <button class="more-btn">더보기 →</button>
        </div>

        <div class="news-list">
          <article v-for="item in watchlistNews" :key="item.title" class="news-item">
            <div class="news-meta">
              <span class="news-ticker">{{ item.ticker }}</span>
              <span class="news-time">{{ item.time }}</span>
            </div>
            <h4 class="news-title">{{ item.title }}</h4>
            <span class="news-source">{{ item.source }}</span>
          </article>
        </div>
      </section>
    </div>

    <!-- ===== 섹션 4: 보유 종목 + 매매 일기 ===== -->
    <div class="bottom-grid">

      <!-- 보유 종목 -->
      <section class="panel bottom-panel" aria-label="보유 종목">
        <div class="panel-head">
          <div>
            <p class="eyebrow">내 포트폴리오</p>
            <h2>보유 종목</h2>
          </div>
          <button class="more-btn" @click="router.push('/holdings')">더보기 →</button>
        </div>
        <div class="holdings-list">
          <div v-for="h in holdings" :key="h.ticker" class="holding-row">
            <div class="hr-dot" :style="{ background: h.color }"></div>
            <div class="hr-info">
              <span class="hr-name">{{ h.name }}</span>
              <span class="hr-ticker">{{ h.ticker }}</span>
            </div>
            <div class="hr-qty">{{ h.qty }}주</div>
            <div class="hr-price">{{ fmt(h.cur) }}원</div>
            <div class="hr-pnl" :class="h.cur >= h.avg ? 'is-up' : 'is-down'">
              {{ h.cur >= h.avg ? '+' : '' }}{{ ((h.cur - h.avg) / h.avg * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </section>

      <!-- 매매 일기 -->
      <section class="panel bottom-panel" aria-label="매매 일기">
        <div class="panel-head">
          <div>
            <p class="eyebrow">나의 투자 기록</p>
            <h2>매매 일기</h2>
          </div>
          <button class="more-btn" @click="router.push('/trading-diary')">더보기 →</button>
        </div>
        <div class="diary-list">
          <div v-for="d in recentDiaries" :key="d.date + d.ticker" class="diary-row" @click="router.push('/trading-diary')">
            <div class="diary-date">{{ d.date }}</div>
            <div class="diary-info">
              <span class="diary-type-badge" :style="{ background: diaryTypeColor[d.type] + '22', color: diaryTypeColor[d.type] }">
                {{ diaryTypeLabel[d.type] }}
              </span>
              <span class="diary-stock">{{ d.stock }}</span>
            </div>
            <div class="diary-title">{{ d.title }}</div>
          </div>
        </div>
        <button class="diary-write-btn" @click="router.push('/trading-diary')">+ 오늘 일지 작성</button>
      </section>

    </div>

  </div>
</template>

<style scoped>
/* ===== 페이지 레이아웃 ===== */
.home-page {
  display: grid;
  gap: 18px;
}

/* ===== 섹션 1: 히어로 그리드 ===== */
.hero-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  align-items: start;
}

/* --- 자산/목표 패널 --- */
.goal-panel { display: flex; flex-direction: column; gap: 0; }

.goal-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.goal-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: var(--radius);
}

.goal-card.target {
  background: linear-gradient(135deg, rgba(20, 24, 32, 0.88) 0%, rgba(40, 48, 72, 0.85) 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
}

.goal-card.achieved {
  background: linear-gradient(135deg, rgba(15, 60, 40, 0.82) 0%, rgba(20, 80, 55, 0.78) 100%);
  border: 1px solid color-mix(in srgb, var(--positive) 25%, transparent);
  box-shadow: 0 4px 16px color-mix(in srgb, var(--positive) 12%, transparent);
}

.goal-card-icon {
  font-size: 22px;
  flex-shrink: 0;
  width: 40px;
  text-align: center;
}

.goal-card-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.goal-card-label {
  font-size: 11px;
  font-weight: 900;
  color: rgba(255, 255, 255, 0.5);
}

.goal-card-name {
  font-size: 16px;
  font-weight: 900;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.goal-card-amount {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.55);
}

.goal-badge {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.goal-badge.in-progress {
  background: color-mix(in srgb, var(--accent) 22%, transparent);
  color: #93b8ff;
  border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent);
}

.goal-badge.done {
  background: color-mix(in srgb, var(--positive) 22%, transparent);
  color: #5de8b8;
  border: 1px solid color-mix(in srgb, var(--positive) 35%, transparent);
}

.goal-track-wrap {
  padding: 0 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.goal-track-bar {
  height: 5px;
  background: color-mix(in srgb, var(--line-tint) 35%, transparent);
  border-radius: 999px;
  overflow: hidden;
}

.goal-track-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--positive), var(--accent));
  border-radius: 999px;
}

.goal-track-pct {
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  text-align: right;
}

.recommendation-box {
  padding: 16px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, color-mix(in srgb, var(--purple) 8%, transparent) 0%, color-mix(in srgb, var(--accent) 5%, transparent) 100%);
  border: 1px solid color-mix(in srgb, var(--purple) 20%, transparent);
}

.recommendation-title {
  display: block;
  font-size: 15px;
  font-weight: 900;
  color: var(--ink);
  margin: 6px 0 8px;
}

.recommendation-desc {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
  word-break: keep-all;
}

/* --- 스와이핑 추천 패널 --- */
.swipe-recommend-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.swipe-recommend-header {
  margin-bottom: 16px;
}

/* ===== 섹션 2: 시장 지표 ===== */
.market-section {
  padding: 0;
  overflow: hidden;
}

.market-status-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--line);
  background: color-mix(in srgb, var(--overlay) 38%, transparent);
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
  box-shadow: 0 0 0 2.5px color-mix(in srgb, var(--positive) 22%, transparent);
}

.market-indices-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.index-card {
  padding: 16px 20px;
  border-right: 1px solid var(--line);
  transition: background 0.16s ease;
  cursor: pointer;
}

.index-card:last-child { border-right: 0; }

.index-card:hover { background: color-mix(in srgb, var(--overlay) 48%, transparent); }

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
}

.index-spark { flex-shrink: 0; width: 72px; height: 32px; }

.index-card.is-up-card :deep(.sparkline-line) { stroke: var(--accent); }
.index-card.is-up-card :deep(.sparkline-fill) { fill: color-mix(in srgb, var(--accent) 8%, transparent); }
.index-card.is-down-card :deep(.sparkline-line) { stroke: var(--negative); }
.index-card.is-down-card :deep(.sparkline-fill) { fill: color-mix(in srgb, var(--negative) 8%, transparent); }

.index-value {
  font-size: 20px;
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -0.5px;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.index-change {
  font-size: 13px;
  font-weight: 900;
}

.index-rate { font-weight: 700; opacity: 0.85; }

.index-sub {
  margin-top: 5px;
  color: var(--faint);
  font-size: 11px;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== 섹션 3: 경제 뉴스 ===== */
.news-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.news-panel {}

.more-btn {
  min-height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  background: color-mix(in srgb, var(--accent) 8%, transparent);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
  transition: background 0.18s ease;
  flex-shrink: 0;
}

.more-btn:hover { background: color-mix(in srgb, var(--accent) 15%, transparent); }

.news-list { display: grid; gap: 2px; }

.news-item {
  padding: 14px 12px;
  border-radius: calc(var(--radius) - 2px);
  transition: background 0.15s ease;
  cursor: pointer;
  border-bottom: 1px solid color-mix(in srgb, var(--line-tint) 35%, transparent);
}

.news-item:last-child { border-bottom: 0; }

.news-item:hover { background: color-mix(in srgb, var(--overlay) 48%, transparent); }

.news-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.news-category,
.news-ticker {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 900;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
}

.news-ticker {
  background: color-mix(in srgb, var(--purple) 10%, transparent);
  color: var(--purple);
  border-color: color-mix(in srgb, var(--purple) 20%, transparent);
}

.news-time {
  color: var(--faint);
  font-size: 11px;
  font-weight: 700;
  margin-left: auto;
}

.news-title {
  color: var(--ink);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.45;
  margin: 0 0 5px;
  word-break: keep-all;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.news-source {
  color: var(--faint);
  font-size: 12px;
  font-weight: 700;
}

/* ===== 섹션 4: 보유종목 + 매매일기 ===== */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.bottom-panel { display: flex; flex-direction: column; gap: 0; }

.holdings-list { display: flex; flex-direction: column; }
.holding-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid var(--faint);
  font-size: 13px; cursor: pointer;
  transition: background 0.15s;
}
.holding-row:last-child { border-bottom: none; }
.holding-row:hover { background: color-mix(in srgb, var(--overlay) 40%, transparent); border-radius: var(--radius); padding-left: 6px; }
.hr-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.hr-info { flex: 1; display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.hr-name { font-weight: 800; color: var(--ink); font-size: 13px; }
.hr-ticker { font-size: 11px; color: var(--muted); }
.hr-qty { color: var(--muted); font-size: 12px; white-space: nowrap; }
.hr-price { font-size: 13px; font-weight: 700; color: var(--ink); white-space: nowrap; min-width: 80px; text-align: right; }
.hr-pnl { font-weight: 900; font-size: 13px; min-width: 50px; text-align: right; }
.hr-pnl.is-up { color: var(--positive); }
.hr-pnl.is-down { color: var(--negative); }

.diary-list { display: flex; flex-direction: column; }
.diary-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid var(--faint);
  cursor: pointer; transition: background 0.15s;
}
.diary-row:last-child { border-bottom: none; }
.diary-row:hover { background: color-mix(in srgb, var(--overlay) 40%, transparent); border-radius: var(--radius); padding-left: 6px; }
.diary-date { font-size: 11px; color: var(--muted); font-weight: 700; white-space: nowrap; min-width: 80px; }
.diary-info { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.diary-type-badge { padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 900; }
.diary-stock { font-size: 12px; font-weight: 800; color: var(--ink); white-space: nowrap; }
.diary-title { flex: 1; font-size: 12px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.diary-write-btn {
  margin-top: 14px; height: 34px; border-radius: 8px;
  border: 1px dashed color-mix(in srgb, var(--accent) 30%, transparent);
  background: color-mix(in srgb, var(--accent) 4%, transparent);
  color: var(--accent); font-size: 13px; font-weight: 900;
  cursor: pointer; transition: background 0.15s;
}
.diary-write-btn:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }

/* ===== 반응형 ===== */
@media (max-width: 1100px) {
  .hero-grid { grid-template-columns: 1fr; }
}

@media (max-width: 800px) {
  .market-indices-grid { grid-template-columns: repeat(2, 1fr); }
  .index-card:nth-child(2n) { border-right: 0; }
  .index-card:nth-child(n+3) { border-top: 1px solid var(--line); }
  .news-grid { grid-template-columns: 1fr; }
}
</style>
