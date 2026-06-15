<script setup>
import { ref, computed } from 'vue'
import SparklineChart from '../components/SparklineChart.vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

// 검색 바
const searchQuery = ref('')
const popularKeywords = ['SK하이닉스', '엔비디아', '삼성전자']
function goSearch() {
  // 와이어프레임: 검색 실행 시 주식 조회 페이지로 이동
  router.push('/stocks')
}

// 자산 현황
const hideAmount = ref(false)
const totalAsset = 12345000
const totalReturn = 8.2
const holdingNewsList = [
  { ticker: 'SK하이닉스', title: 'HBM3E 12단 양산 본격화...NVIDIA 독점 공급' },
  { ticker: '삼성전자', title: '파운드리 2나노 수율 개선...대형 수주 기대감' },
  { ticker: 'NVIDIA', title: 'AI 가속기 신제품 공개, 데이터센터 수요 견조' },
  { ticker: 'NAVER', title: '커머스·클라우드 AI 전환 가속...실적 반등 전망' },
  { ticker: 'APPLE', title: 'WWDC서 온디바이스 AI 기능 대거 공개 예고' },
  { ticker: '셀트리온', title: '바이오시밀러 미국 점유율 확대...수출 증가세' },
]

// 궁합 추천 스와이프 덱
const matchStocks = [
  {
    name: '삼성바이오로직스', code: '207940', market: 'KOSPI · 바이오', sector: '바이오',
    score: 86, price: '1,042,000원', change: '+1.4%', up: true, interest: 612,
    dna: [
      { label: '변동성', value: 63 }, { label: '성장', value: 85 },
      { label: '가치', value: 45 }, { label: '안정성', value: 60 },
    ],
    gradient: 'linear-gradient(135deg, #6d28d9 0%, #a855f7 45%, #db2777 100%)',
  },
  {
    name: 'SK하이닉스', code: '000660', market: 'KOSPI · 전기·전자', sector: '반도체',
    score: 94, price: '189,300원', change: '+2.1%', up: true, interest: 1284,
    dna: [
      { label: '변동성', value: 72 }, { label: '성장', value: 88 },
      { label: '가치', value: 52 }, { label: '안정성', value: 58 },
    ],
    gradient: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #db2777 100%)',
  },
  {
    name: 'NAVER', code: '035420', market: 'KOSPI · 플랫폼', sector: '플랫폼',
    score: 80, price: '192,500원', change: '+1.4%', up: true, interest: 430,
    dna: [
      { label: '변동성', value: 58 }, { label: '성장', value: 76 },
      { label: '가치', value: 55 }, { label: '안정성', value: 62 },
    ],
    gradient: 'linear-gradient(135deg, #059669 0%, #10b981 50%, #06b6d4 100%)',
  },
  {
    name: '셀트리온', code: '068270', market: 'KOSPI · 바이오', sector: '바이오',
    score: 82, price: '168,300원', change: '+2.4%', up: true, interest: 521,
    dna: [
      { label: '변동성', value: 66 }, { label: '성장', value: 80 },
      { label: '가치', value: 48 }, { label: '안정성', value: 57 },
    ],
    gradient: 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #a855f7 100%)',
  },
]

const cardEl = ref(null)
const matchIndex = ref(0)
const current = computed(() => matchStocks[matchIndex.value])
const feedbackType = ref(null) // 'like' | 'pass' | 'save'
const feedbackOpacity = ref(0)

// Stock DNA 4축(변동성/성장/가치/안정성) → 다이아몬드 폴리곤 좌표
const dnaPolygon = computed(() => {
  const d = current.value.dna
  const cx = 60, cy = 60, R = 46
  return [
    `${cx},${cy - (R * d[0].value) / 100}`,
    `${cx + (R * d[1].value) / 100},${cy}`,
    `${cx},${cy + (R * d[2].value) / 100}`,
    `${cx - (R * d[3].value) / 100},${cy}`,
  ].join(' ')
})

let dragging = false
let animating = false
let startX = 0
let startY = 0
let curX = 0
let curY = 0

const EXIT_MS = 540

// 드래그 방향에 따라 가운데 피드백(관심/패스/저장) 갱신
function updateFeedback() {
  if (curY < -50 && Math.abs(curY) > Math.abs(curX)) {
    feedbackType.value = 'save'
    feedbackOpacity.value = Math.min(Math.abs(curY) / 120, 1)
  } else if (curX > 40) {
    feedbackType.value = 'like'
    feedbackOpacity.value = Math.min(curX / 120, 1)
  } else if (curX < -40) {
    feedbackType.value = 'pass'
    feedbackOpacity.value = Math.min(Math.abs(curX) / 120, 1)
  } else {
    feedbackOpacity.value = 0
  }
}

// 다음 카드 진입: 살짝 작게+투명 → 제자리로 부드럽게
function enterCard() {
  const el = cardEl.value
  if (!el) return
  feedbackOpacity.value = 0
  el.style.transition = 'none'
  el.style.transform = 'translate3d(0,0,0) scale(.94)'
  el.style.opacity = '0'
  requestAnimationFrame(() => {
    el.style.transition = 'transform .5s cubic-bezier(.2,.8,.2,1), opacity .42s ease'
    el.style.transform = 'translate3d(0,0,0) scale(1)'
    el.style.opacity = '1'
  })
}

function advance() {
  matchIndex.value = (matchIndex.value + 1) % matchStocks.length
  requestAnimationFrame(enterCard)
}

// direction: 'left'=관심없음, 'right'=관심, 'save'=관심 종목 저장(위로)
function swipe(direction) {
  const el = cardEl.value
  if (!auth.isAuthenticated || animating || !el) return
  animating = true
  feedbackType.value = direction === 'save' ? 'save' : direction === 'right' ? 'like' : 'pass'
  feedbackOpacity.value = 1
  el.style.transition = `transform ${EXIT_MS}ms cubic-bezier(.4,0,.2,1), opacity ${EXIT_MS}ms ease`
  if (direction === 'save') {
    el.style.transform = 'translate3d(0,-220px,0) scale(.9)'
  } else {
    const right = direction === 'right'
    el.style.transform = `translate3d(${right ? 460 : -460}px,40px,0) rotate(${right ? 16 : -16}deg)`
  }
  el.style.opacity = '0'
  setTimeout(() => { advance(); animating = false }, EXIT_MS)
}

function onPointerDown(e) {
  if (!auth.isAuthenticated || animating) return
  dragging = true
  startX = e.clientX
  startY = e.clientY
  curX = 0
  curY = 0
  cardEl.value.style.transition = 'none'
  cardEl.value.setPointerCapture?.(e.pointerId)
}
function onPointerMove(e) {
  if (!dragging) return
  curX = e.clientX - startX
  curY = e.clientY - startY
  const rotate = curX / 20
  const scale = Math.max(0.96, 1 - (Math.abs(curX) + Math.abs(curY)) / 2400)
  cardEl.value.style.transform = `translate3d(${curX}px, ${curY}px, 0) rotate(${rotate}deg) scale(${scale})`
  updateFeedback()
}
function onPointerUp() {
  if (!dragging) return
  dragging = false
  // 위로 스와이프 = 저장(하트 버튼과 동일), 좌우 = 관심없음/관심
  if (curY < -110 && Math.abs(curY) > Math.abs(curX)) return swipe('save')
  if (curX > 110) return swipe('right')
  if (curX < -110) return swipe('left')
  // 임계값 미만 — 제자리 복귀
  const el = cardEl.value
  el.style.transition = 'transform .45s cubic-bezier(.2,.8,.2,1)'
  el.style.transform = 'translate3d(0,0,0) rotate(0deg) scale(1)'
  feedbackOpacity.value = 0
}

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

    <!-- ===== 검색 바 ===== -->
    <section class="panel home-search" aria-label="종목 검색">
      <form class="search-box" @submit.prevent="goSearch">
        <svg class="search-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="2" />
          <path d="M14 14l4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="종목명 또는 코드로 검색 (예: 삼성전자, 005930, NVDA)"
        />
      </form>
      <div class="search-popular">
        <span class="popular-label">🔥 인기검색</span>
        <button
          v-for="kw in popularKeywords"
          :key="kw"
          type="button"
          class="popular-kw"
          @click="goSearch"
        >{{ kw }}</button>
      </div>
    </section>

    <!-- ===== 섹션 1: 자산 목표 + 스와이핑 추천 ===== -->
    <div class="hero-grid">

      <!-- 왼쪽: 현재 총 자산 가치 및 다음 목표 -->
      <section class="panel goal-panel" aria-label="자산 현황 및 목표">
        <div class="panel-head">
          <div>
            <p class="eyebrow">나의 자산</p>
            <h2>자산 현황</h2>
          </div>
          <button class="hide-amount-btn" type="button" @click="hideAmount = !hideAmount">
            👁 {{ hideAmount ? '금액 보기' : '금액 숨기기' }}
          </button>
        </div>

        <!-- 총 평가액 -->
        <div class="asset-summary">
          <div class="asset-total">
            <span class="asset-total-label">총 평가액</span>
            <strong class="asset-total-value">{{ hideAmount ? '••••••••' : fmt(totalAsset) + '원' }}</strong>
          </div>
          <div class="asset-return">
            <span class="asset-return-label">총 수익률</span>
            <strong class="asset-return-value" :class="totalReturn >= 0 ? 'is-up' : 'is-down'">
              {{ totalReturn >= 0 ? '+' : '' }}{{ totalReturn }}%
            </strong>
          </div>
        </div>

        <div class="goal-list">
          <!-- 현재 진행중인 목표 -->
          <div class="goal-card target">
            <div class="goal-card-icon">✈️</div>
            <div class="goal-card-info">
              <span class="goal-card-label">다음 목표</span>
              <strong class="goal-card-name">유럽 여행</strong>
              <span class="goal-card-amount">목표 5,000,000원</span>
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
            <div class="goal-card-icon">👜</div>
            <div class="goal-card-info">
              <span class="goal-card-label">달성 완료</span>
              <strong class="goal-card-name">명품 가방</strong>
              <span class="goal-card-amount">8,900,000원</span>
            </div>
            <span class="goal-badge done">달성</span>
          </div>
        </div>

        <!-- 액션 버튼 -->
        <div class="asset-actions">
          <button class="asset-action-card" type="button" @click="router.push('/trading-diary')">
            <span class="aac-icon">📓</span>
            <span class="aac-body">
              <strong>투자 일기 쓰러 가기</strong>
              <small>작성 대기 1건 (매매 후 미작성)</small>
            </span>
            <span class="aac-arrow">→</span>
          </button>
          <button class="asset-action-card" type="button" @click="router.push('/portfolio')">
            <span class="aac-icon">🩺</span>
            <span class="aac-body">
              <strong>장투 점검하기</strong>
              <small>내 종목 지금 점검해보세요</small>
            </span>
            <span class="aac-arrow">→</span>
          </button>
        </div>

        <!-- 보유 종목 뉴스 -->
        <div class="asset-news">
          <div class="asset-news-head">
            <span class="asset-news-label">📰 보유 종목 뉴스</span>
            <span class="asset-news-nav">← → 넘기기</span>
          </div>
          <article v-for="n in holdingNewsList" :key="n.title" class="asset-news-item">
            <span class="news-ticker">{{ n.ticker }}</span>
            <span class="asset-news-headline">{{ n.title }}</span>
          </article>
        </div>
      </section>

      <!-- 오른쪽: 궁합 추천 스와이프 -->
      <section class="panel swipe-recommend-panel" aria-label="궁합 추천">
        <div class="match-header">
          <h2 class="match-title">오늘의 궁합 추천 💝</h2>
          <p class="match-sub">당신의 투자 성향과 잘 맞는 종목이에요. 넘기면서 관심 종목을 골라보세요.</p>
          <span class="match-count">추천 {{ matchIndex + 1 }} / {{ matchStocks.length }}</span>
        </div>

        <div class="deck-wrap">
          <article
            ref="cardEl"
            class="match-card"
            :class="{ blurred: !auth.isAuthenticated }"
            :style="{ background: current.gradient }"
            @pointerdown="onPointerDown"
            @pointermove="onPointerMove"
            @pointerup="onPointerUp"
          >
            <div class="match-feedback" :class="feedbackType" :style="{ opacity: feedbackOpacity }">
              <span v-if="feedbackType === 'like'">❤️ 관심</span>
              <span v-else-if="feedbackType === 'pass'">✕ 패스</span>
              <span v-else-if="feedbackType === 'save'">⭐ 저장</span>
            </div>

            <div class="mc-top">
              <span class="mc-badge">{{ current.market }}</span>
              <div class="mc-score">{{ current.score }}<span>궁합점수</span></div>
            </div>

            <div class="mc-name-block">
              <h3 class="mc-name">{{ current.name }}</h3>
              <div class="mc-code">{{ current.code }}</div>
            </div>

            <div class="mc-prices">
              <div class="mc-price-box">
                <span>현재가</span>
                <strong>{{ current.price }}</strong>
              </div>
              <div class="mc-price-box">
                <span>등락률</span>
                <strong :class="current.up ? 'up' : 'down'">{{ current.change }}</strong>
              </div>
            </div>

            <!-- Stock DNA -->
            <div class="mc-dna">
              <svg class="dna-radar" viewBox="0 0 120 120" aria-hidden="true">
                <polygon class="dna-grid" points="60,14 106,60 60,106 14,60" />
                <polygon class="dna-grid" points="60,37 83,60 60,83 37,60" />
                <line class="dna-axis" x1="60" y1="14" x2="60" y2="106" />
                <line class="dna-axis" x1="14" y1="60" x2="106" y2="60" />
                <polygon class="dna-shape" :points="dnaPolygon" />
              </svg>
              <div class="dna-info">
                <div class="dna-title">🧬 Stock DNA</div>
                <div class="dna-vals">
                  <template v-for="d in current.dna" :key="d.label">
                    <span class="dna-k">{{ d.label }}</span>
                    <span class="dna-v">{{ d.value }}</span>
                  </template>
                </div>
              </div>
            </div>

            <div class="mc-reason">🐤 성장 선호와 {{ current.sector }} 모멘텀(성장 {{ current.dna[1].value }})이 맞아요.</div>
            <div class="mc-interest">❤️ {{ current.interest.toLocaleString('ko-KR') }}명이 이 종목에 관심 있어요</div>
          </article>

          <!-- 미로그인: 카드 블러 + 로그인 버튼 -->
          <div v-if="!auth.isAuthenticated" class="match-login-overlay">
            <button class="match-login-btn" type="button" @click="router.push('/login')">로그인을 해주세요</button>
          </div>
        </div>

        <!-- 액션 버튼 -->
        <div class="match-controls">
          <button class="match-btn pass" type="button" aria-label="관심없음" :disabled="!auth.isAuthenticated" @click="swipe('left')">✕</button>
          <button class="match-btn save" type="button" aria-label="관심 종목 저장" :disabled="!auth.isAuthenticated" @click="swipe('save')">♥</button>
          <button class="match-btn like" type="button" aria-label="관심" :disabled="!auth.isAuthenticated" @click="swipe('right')">↗</button>
        </div>
        <p class="match-hint">카드를 좌우로 드래그하거나 버튼을 눌러 넘길 수 있어요</p>
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

/* ===== 검색 바 ===== */
.home-search {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.search-icon {
  width: 18px;
  height: 18px;
  color: var(--muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 28px;
  border: 0;
  background: transparent;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  outline: none;
}

.search-input::placeholder { color: var(--muted); font-weight: 600; }

.search-popular {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.popular-label {
  font-size: 13px;
  font-weight: 900;
  color: var(--ink);
  white-space: nowrap;
  margin-right: 4px;
}

.popular-kw {
  border: 0;
  background: none;
  padding: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.15s ease;
}

.popular-kw:hover { color: var(--accent); }

.popular-kw:not(:last-child)::after {
  content: '·';
  margin: 0 6px;
  color: var(--faint);
}

@media (max-width: 800px) {
  .home-search { flex-direction: column; align-items: stretch; gap: 10px; }
  .search-popular { flex-wrap: wrap; }
}

/* ===== 섹션 1: 히어로 그리드 ===== */
.hero-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  align-items: stretch;
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
  background: var(--track);
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

/* --- 총 평가액 + 금액 숨기기 --- */
.hide-amount-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
}
.hide-amount-btn:hover { background: var(--surface-hover); color: var(--ink); }

.asset-summary {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 16px;
}
.asset-total { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.asset-total-label { font-size: 12px; font-weight: 900; color: var(--muted); }
.asset-total-value {
  font-size: 30px;
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -1px;
  line-height: 1;
}
.asset-return { display: flex; flex-direction: column; gap: 4px; padding-bottom: 3px; }
.asset-return-label { font-size: 12px; font-weight: 900; color: var(--muted); }
.asset-return-value { font-size: 16px; font-weight: 900; }
.asset-return-value.is-up { color: var(--positive); }
.asset-return-value.is-down { color: var(--negative); }

/* --- 액션 버튼 2개 --- */
.asset-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}
.asset-action-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, transform 0.15s ease;
}
.asset-action-card:hover { background: var(--surface-hover); transform: translateY(-2px); }
.aac-icon { font-size: 20px; flex-shrink: 0; }
.aac-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.aac-body strong { font-size: 13px; font-weight: 900; color: var(--ink); }
.aac-body small { font-size: 11px; color: var(--muted); font-weight: 700; }
.aac-arrow { color: var(--faint); font-size: 16px; font-weight: 900; flex-shrink: 0; }

/* --- 보유 종목 뉴스 (카드 하단에 고정해 높이 균형) --- */
.asset-news { margin-top: auto; border-top: 1px solid var(--line); padding-top: 14px; }
.asset-news-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.asset-news-label { font-size: 13px; font-weight: 900; color: var(--ink); }
.asset-news-nav { font-size: 12px; font-weight: 700; color: var(--faint); }
.asset-news-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  cursor: pointer;
  padding: 9px 0;
  border-bottom: 1px solid var(--faint);
}
.asset-news-item:last-child { border-bottom: none; }
.asset-news-headline {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --- 궁합 추천 스와이프 패널 --- */
.swipe-recommend-panel {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
}

/* 흰 패널에 포인트를 주는 은은한 컬러 오라 */
.swipe-recommend-panel::before,
.swipe-recommend-panel::after {
  content: '';
  position: absolute;
  width: 360px;
  height: 360px;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}
.swipe-recommend-panel::before {
  top: -140px;
  right: -120px;
  background: radial-gradient(circle, rgba(125, 78, 232, 0.22), transparent 68%);
  animation: matchAura 7s ease-in-out infinite;
}
.swipe-recommend-panel::after {
  bottom: -150px;
  left: -120px;
  background: radial-gradient(circle, rgba(255, 61, 139, 0.18), transparent 70%);
  animation: matchAura 7s ease-in-out infinite reverse;
}
.swipe-recommend-panel > * { position: relative; z-index: 1; }

@keyframes matchAura {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

.match-header { text-align: center; margin-bottom: 18px; }
.match-title {
  margin: 0;
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -0.5px;
  color: var(--ink);
}
.match-sub {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
  word-break: keep-all;
}
.match-count {
  display: inline-block;
  margin-top: 8px;
  color: var(--faint);
  font-size: 12px;
  font-weight: 900;
}

.deck-wrap { position: relative; }

.match-card {
  position: relative;
  width: 100%;
  border-radius: 24px;
  padding: 22px;
  color: #fff;
  box-shadow: 0 12px 40px rgba(109, 40, 217, 0.3), 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  user-select: none;
  touch-action: none;
  cursor: grab;
  will-change: transform, opacity;
}
.match-card:active { cursor: grabbing; }
.match-card.blurred { filter: blur(7px); pointer-events: none; }
.match-card::before {
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
.match-card > * { position: relative; z-index: 1; }

/* 상호작용 피드백 — 카드 가운데에 크게 표시 */
.match-feedback {
  position: absolute;
  inset: 0;
  z-index: 6;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.14s ease;
}
.match-feedback span {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 30px;
  border-radius: 18px;
  font-size: 32px;
  font-weight: 900;
  letter-spacing: -0.5px;
  color: #fff;
  border: 4px solid currentColor;
  background: rgba(8, 12, 24, 0.34);
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  box-shadow: 0 14px 44px rgba(0, 0, 0, 0.3);
  transform: rotate(-7deg);
}
.match-feedback.like span { color: #2fe39f; }
.match-feedback.pass span { color: #ff6f8b; }
.match-feedback.save span { color: #ffce5a; }

.mc-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.mc-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.28);
  color: rgba(255, 255, 255, 0.92);
  font-size: 12px;
  font-weight: 900;
}
.mc-score {
  text-align: right;
  font-size: 36px;
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -2px;
  color: #fff;
  flex-shrink: 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.28);
}
.mc-score span {
  display: block;
  font-size: 11px;
  letter-spacing: 0;
  font-weight: 900;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 4px;
}

.mc-name-block { margin-top: 18px; }
.mc-name {
  margin: 0;
  color: #fff;
  font-size: 28px;
  font-weight: 900;
  letter-spacing: -1px;
  line-height: 1.1;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.32), 0 1px 2px rgba(0, 0, 0, 0.25);
}
.mc-code {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  font-weight: 900;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.28);
}

.mc-prices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 16px;
}
.mc-price-box {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.mc-price-box span {
  display: block;
  color: rgba(255, 255, 255, 0.65);
  font-size: 11px;
  font-weight: 900;
  margin-bottom: 4px;
}
.mc-price-box strong { display: block; color: #fff; font-size: 15px; font-weight: 900; }
.mc-price-box strong.up { color: #6effc9; }
.mc-price-box strong.down { color: #93b8ff; }

/* Stock DNA */
.mc-dna {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
}
.dna-radar { width: 96px; height: 96px; flex-shrink: 0; }
.dna-grid { fill: rgba(49, 93, 255, 0.05); stroke: rgba(49, 93, 255, 0.2); stroke-width: 1; }
.dna-axis { stroke: rgba(49, 93, 255, 0.18); stroke-width: 1; }
.dna-shape { fill: rgba(49, 93, 255, 0.45); stroke: var(--accent); stroke-width: 2; }
.dna-info { flex: 1; min-width: 0; }
.dna-title { font-size: 13px; font-weight: 900; color: var(--ink); margin-bottom: 10px; }
.dna-vals {
  display: grid;
  grid-template-columns: auto 1fr auto 1fr;
  gap: 8px 10px;
  align-items: center;
}
.dna-k { font-size: 12px; font-weight: 800; color: var(--muted); }
.dna-v { font-size: 13px; font-weight: 900; color: var(--accent); text-align: right; }

.mc-reason { margin-top: 14px; font-size: 13px; font-weight: 800; color: #fff; text-shadow: 0 1px 6px rgba(0, 0, 0, 0.3); }
.mc-interest { margin-top: 12px; font-size: 13px; font-weight: 800; color: #fff; text-shadow: 0 1px 6px rgba(0, 0, 0, 0.3); }

/* 로그인 오버레이 */
.match-login-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}
.match-login-btn {
  padding: 0 22px;
  height: 48px;
  border: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(49, 93, 255, 0.4);
  transition: transform 0.18s ease;
}
.match-login-btn:hover { transform: translateY(-2px); }

/* 컨트롤 버튼 */
.match-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 18px;
}
.match-btn {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  border: 1.5px solid var(--glass-border);
  background: var(--surface-soft);
  font-size: 22px;
  font-weight: 900;
  color: var(--ink);
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease, background 0.18s ease, box-shadow 0.18s ease;
}
.match-btn.pass { color: var(--negative); border-color: rgba(207, 61, 61, 0.4); background: rgba(207, 61, 61, 0.07); }
.match-btn.like { color: var(--accent); border-color: rgba(49, 93, 255, 0.4); background: rgba(49, 93, 255, 0.07); }
.match-btn.save {
  width: 70px;
  height: 70px;
  border: 0;
  background: linear-gradient(135deg, #ff3d8b 0%, #e3344f 100%);
  color: #fff;
  font-size: 26px;
  box-shadow: 0 10px 30px rgba(255, 61, 139, 0.45);
}
.match-btn:hover:not(:disabled) { transform: translateY(-3px) scale(1.05); box-shadow: 0 10px 24px rgba(0, 0, 0, 0.14); }
.match-btn:active:not(:disabled) { transform: translateY(-1px) scale(0.98); }
.match-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.match-hint {
  margin: 12px 0 0;
  text-align: center;
  color: var(--faint);
  font-size: 12px;
  font-weight: 700;
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
  background: var(--glass-subtle);
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

.index-card:hover { background: var(--surface-soft); }

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
  border-bottom: 1px solid var(--line);
}

.news-item:last-child { border-bottom: 0; }

.news-item:hover { background: var(--surface-soft); }

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
.holding-row:hover { background: var(--glass-subtle); border-radius: var(--radius); padding-left: 6px; }
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
.diary-row:hover { background: var(--glass-subtle); border-radius: var(--radius); padding-left: 6px; }
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
