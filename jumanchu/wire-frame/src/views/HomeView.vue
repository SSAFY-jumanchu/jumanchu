<script setup>
import SparklineChart from '../components/SparklineChart.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

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
]

const generalNews = [
  { title: 'FOMC 금리 동결 가능성 높아져...시장 반응은?', source: '한국경제', time: '1시간 전', category: '금리' },
  { title: '반도체 수출 전월 대비 18% 증가, 하이닉스 수혜', source: '매일경제', time: '2시간 전', category: '반도체' },
  { title: 'S&P500 신고가 경신...나스닥도 동반 상승', source: '연합뉴스', time: '3시간 전', category: '해외' },
  { title: '코스피 2720선 회복, 외국인 선물 매수 전환', source: '서울경제', time: '4시간 전', category: '코스피' },
]

const holdings = [
  { name: '삼성전자', ticker: '005930', qty: 20, avg: 310500, cur: 317000, color: '#315dff' },
  { name: 'SK하이닉스', ticker: '000660', qty: 10, avg: 238000, cur: 243000, color: '#7d4ee8' },
  { name: 'NVIDIA',   ticker: 'NVDA',   qty: 3,  avg: 1251000, cur: 1285000, color: '#22c55e' },
  { name: 'NAVER',    ticker: '035420', qty: 8,  avg: 189500, cur: 184000, color: '#f59e0b' },
  { name: 'APPLE',    ticker: 'AAPL',   qty: 2,  avg: 248000, cur: 261000, color: '#06b6d4' },
]

const recentDiaries = [
  { date: '2026-06-10', stock: 'APPLE',    ticker: 'AAPL',   type: 'hold', title: 'WWDC 전 홀딩 전략' },
  { date: '2026-06-05', stock: '삼성전자', ticker: '005930', type: 'buy',  title: '오늘 매수 이유' },
  { date: '2026-06-04', stock: 'SK하이닉스', ticker: '000660', type: 'sell', title: '단기 수익 실현' },
]
const diaryTypeColor = { buy: '#315dff', sell: '#ef4444', hold: '#f59e0b' }
const diaryTypeLabel = { buy: '매수', sell: '매도', hold: '홀딩' }

function fmt(n) { return n.toLocaleString('ko-KR') }

const swipeCard = {
  name: '삼성바이오로직스',
  code: '207940',
  market: 'KOSPI',
  sector: '바이오',
  price: 1042000,
  rate: 1.4,
  score: 86,
  gradient: 'linear-gradient(135deg, #1a3a6e 0%, #1e5fb5 45%, #6b21a8 100%)',
  dna: { growth: 85, stability: 60, value: 45, volatility: 6 },
  matchReason: '성장 선호와 바이오 모멘텀(성장 8x)이 잘 맞아요.',
  interestedCount: 6.7,
}

function dnaPoints(dna) {
  const cx = 50, cy = 50, r = 38
  const top    = `${cx},${(cy - dna.growth / 100 * r).toFixed(1)}`
  const right  = `${(cx + dna.stability / 100 * r).toFixed(1)},${cy}`
  const bottom = `${cx},${(cy + dna.value / 100 * r).toFixed(1)}`
  const left   = `${(cx - dna.volatility / 100 * r).toFixed(1)},${cy}`
  return `${top} ${right} ${bottom} ${left}`
}

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

      <!-- 오른쪽: 스와이핑 주식 추천 -->
      <section class="swipe-recommend-panel" aria-label="스와이핑 주식 추천">
        <div class="swipe-recommend-header">
          <div class="swipe-rec-head-row">
            <div>
              <p class="eyebrow">AI 궁합 매칭</p>
              <h2>오늘의 궁합 추천 ❤️</h2>
            </div>
            <span class="swipe-counter">스와이프 1 / 4</span>
          </div>
          <p class="swipe-sub">당신의 투자 성향과 잘 맞는 종목에요. 좌우로 스와이프해 관심 종목을 골라보세요.</p>
        </div>

        <div class="swipe-card-area">
          <!-- 궁합 추천 카드 -->
          <article class="swipe-hero-card" :style="{ background: swipeCard.gradient }">
            <div class="swipe-hero-top">
              <span class="swipe-hero-badge">{{ swipeCard.market }} · {{ swipeCard.sector }}</span>
              <div class="swipe-hero-score">
                {{ swipeCard.score }}
                <span>궁합점수</span>
              </div>
            </div>
            <div class="swipe-hero-body">
              <h3 class="swipe-hero-name">{{ swipeCard.name }}</h3>
              <div class="swipe-hero-code">{{ swipeCard.code }}</div>
              <div class="swipe-mid-row">
                <div class="swipe-prices-stack">
                  <div class="swipe-price-item">
                    <span>현재가</span>
                    <strong>{{ fmt(swipeCard.price) }}원</strong>
                  </div>
                  <div class="swipe-price-item">
                    <span>등락률</span>
                    <strong class="up-pill">+{{ swipeCard.rate }}%</strong>
                  </div>
                </div>
                <div class="dna-chart-area">
                  <svg viewBox="0 0 100 100" class="dna-svg">
                    <polygon points="50,10 90,50 50,90 10,50" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>
                    <polygon points="50,30 70,50 50,70 30,50" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="0.5" stroke-dasharray="2 2"/>
                    <polygon :points="dnaPoints(swipeCard.dna)" fill="rgba(255,255,255,0.2)" stroke="rgba(255,255,255,0.75)" stroke-width="1.5"/>
                    <text x="50" y="7" text-anchor="middle" font-size="7.5" fill="rgba(255,255,255,0.7)">성장</text>
                    <text x="97" y="53" text-anchor="end" font-size="7.5" fill="rgba(255,255,255,0.7)">안정</text>
                    <text x="50" y="100" text-anchor="middle" font-size="7.5" fill="rgba(255,255,255,0.7)">가치</text>
                    <text x="3" y="53" text-anchor="start" font-size="7.5" fill="rgba(255,255,255,0.7)">변동</text>
                  </svg>
                  <span class="dna-label">Stock DNA</span>
                </div>
              </div>
              <div class="swipe-match-reason">✦ {{ swipeCard.matchReason }}</div>
            </div>
          </article>

          <!-- 소셜 증거 -->
          <div class="swipe-social">
            <span class="social-dot"></span>
            <span>{{ swipeCard.interestedCount }}명이 이 종목에 관심 갖았어요</span>
          </div>

          <!-- 스와이프 액션 버튼 -->
          <div class="swipe-action-row">
            <button class="swipe-btn pass-btn" aria-label="패스">✕</button>
            <button class="swipe-btn heart-btn" aria-label="관심 추가">♡</button>
            <button class="swipe-btn detail-btn" aria-label="상세 보기">↗</button>
          </div>
        </div>
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
  border: 1px solid rgba(15, 159, 110, 0.25);
  box-shadow: 0 4px 16px rgba(15, 159, 110, 0.12);
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
  background: rgba(49, 93, 255, 0.22);
  color: #93b8ff;
  border: 1px solid rgba(49, 93, 255, 0.35);
}

.goal-badge.done {
  background: rgba(15, 159, 110, 0.22);
  color: #5de8b8;
  border: 1px solid rgba(15, 159, 110, 0.35);
}

.goal-track-wrap {
  padding: 0 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.goal-track-bar {
  height: 5px;
  background: rgba(200, 215, 255, 0.35);
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
  background: linear-gradient(135deg, rgba(125, 78, 232, 0.08) 0%, rgba(49, 93, 255, 0.05) 100%);
  border: 1px solid rgba(125, 78, 232, 0.2);
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

.swipe-card-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.swipe-hero-card {
  width: 100%;
  border-radius: 24px;
  padding: 22px;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 12px 40px rgba(109, 40, 217, 0.3), 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.swipe-hero-card::before {
  content: '';
  position: absolute;
  width: 200px;
  height: 200px;
  top: -60px;
  right: -60px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  pointer-events: none;
}

.swipe-hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.swipe-hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 900;
}

.swipe-hero-score {
  text-align: right;
  font-size: 40px;
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -2px;
  color: #fff;
  flex-shrink: 0;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.swipe-hero-score span {
  display: block;
  font-size: 12px;
  letter-spacing: 0;
  font-weight: 900;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 4px;
}

.swipe-hero-body { position: relative; z-index: 1; }

.swipe-hero-name {
  font-size: 32px;
  font-weight: 900;
  color: #fff;
  letter-spacing: -1px;
  line-height: 1.1;
  margin: 0 0 4px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.swipe-hero-code {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  font-weight: 900;
  margin-bottom: 14px;
}

.swipe-hero-prices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.swipe-price-box {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.swipe-price-box span {
  display: block;
  color: rgba(255, 255, 255, 0.6);
  font-size: 11px;
  font-weight: 900;
  margin-bottom: 4px;
}

.swipe-price-box strong {
  display: block;
  color: #fff;
  font-size: 15px;
  font-weight: 900;
}

.up-pill {
  color: #6effc9 !important;
}

/* 소셜 증거 */
.swipe-social {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.social-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--positive);
  box-shadow: 0 0 0 3px rgba(15, 159, 110, 0.2);
  flex-shrink: 0;
}

/* 스와이프 버튼 */
.swipe-action-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.swipe-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  font-size: 20px;
  font-weight: 900;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  color: var(--ink);
}

.swipe-btn.pass-btn { color: var(--negative); border-color: rgba(207, 61, 61, 0.3); }
.swipe-btn.like-btn { color: var(--positive); border-color: rgba(15, 159, 110, 0.3); }

.swipe-btn.heart-btn {
  width: 68px;
  height: 68px;
  border: 0;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 24px;
  box-shadow: 0 8px 28px rgba(49, 93, 255, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.swipe-btn:hover {
  transform: translateY(-3px) scale(1.06);
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

.index-card:hover { background: rgba(255, 255, 255, 0.48); }

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
.index-card.is-up-card :deep(.sparkline-fill) { fill: rgba(49, 93, 255, 0.08); }
.index-card.is-down-card :deep(.sparkline-line) { stroke: var(--negative); }
.index-card.is-down-card :deep(.sparkline-fill) { fill: rgba(207, 61, 61, 0.08); }

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
  border: 1px solid rgba(49, 93, 255, 0.25);
  background: rgba(49, 93, 255, 0.08);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
  transition: background 0.18s ease;
  flex-shrink: 0;
}

.more-btn:hover { background: rgba(49, 93, 255, 0.15); }

.news-list { display: grid; gap: 2px; }

.news-item {
  padding: 14px 12px;
  border-radius: calc(var(--radius) - 2px);
  transition: background 0.15s ease;
  cursor: pointer;
  border-bottom: 1px solid rgba(200, 215, 255, 0.35);
}

.news-item:last-child { border-bottom: 0; }

.news-item:hover { background: rgba(255, 255, 255, 0.48); }

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
  background: rgba(49, 93, 255, 0.1);
  color: var(--accent);
  border: 1px solid rgba(49, 93, 255, 0.2);
}

.news-ticker {
  background: rgba(125, 78, 232, 0.1);
  color: var(--purple);
  border-color: rgba(125, 78, 232, 0.2);
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
.holding-row:hover { background: rgba(255,255,255,0.4); border-radius: var(--radius); padding-left: 6px; }
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
.diary-row:hover { background: rgba(255,255,255,0.4); border-radius: var(--radius); padding-left: 6px; }
.diary-date { font-size: 11px; color: var(--muted); font-weight: 700; white-space: nowrap; min-width: 80px; }
.diary-info { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.diary-type-badge { padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 900; }
.diary-stock { font-size: 12px; font-weight: 800; color: var(--ink); white-space: nowrap; }
.diary-title { flex: 1; font-size: 12px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.diary-write-btn {
  margin-top: 14px; height: 34px; border-radius: 8px;
  border: 1px dashed rgba(49,93,255,0.3);
  background: rgba(49,93,255,0.04);
  color: var(--accent); font-size: 13px; font-weight: 900;
  cursor: pointer; transition: background 0.15s;
}
.diary-write-btn:hover { background: rgba(49,93,255,0.1); }

.swipe-rec-head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.swipe-counter {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(49,93,255,0.1);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  border: 1px solid rgba(49,93,255,0.2);
  white-space: nowrap;
  flex-shrink: 0;
}

.swipe-sub {
  font-size: 12px;
  color: var(--muted);
  margin: 6px 0 0;
  line-height: 1.5;
  word-break: keep-all;
}

.swipe-mid-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
}

.swipe-prices-stack {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.swipe-price-item {
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255,255,255,0.14);
  border: 1px solid rgba(255,255,255,0.18);
}

.swipe-price-item span {
  display: block;
  color: rgba(255,255,255,0.6);
  font-size: 11px;
  font-weight: 900;
  margin-bottom: 3px;
}

.swipe-price-item strong {
  display: block;
  color: #fff;
  font-size: 14px;
  font-weight: 900;
}

.dna-chart-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.dna-svg { width: 88px; height: 88px; }

.dna-label {
  color: rgba(255,255,255,0.6);
  font-size: 10px;
  font-weight: 900;
  text-align: center;
}

.swipe-match-reason {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.18);
  font-size: 12px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  line-height: 1.5;
}

.swipe-btn.detail-btn { color: var(--accent); border-color: rgba(49,93,255,0.3); }

/* ===== 반응형 ===== */
@media (max-width: 1100px) {
  .hero-grid { grid-template-columns: 1fr; }
  .swipe-hero-card { min-height: 220px; }
}

@media (max-width: 800px) {
  .market-indices-grid { grid-template-columns: repeat(2, 1fr); }
  .index-card:nth-child(2n) { border-right: 0; }
  .index-card:nth-child(n+3) { border-top: 1px solid var(--line); }
  .news-grid { grid-template-columns: 1fr; }
}
</style>
