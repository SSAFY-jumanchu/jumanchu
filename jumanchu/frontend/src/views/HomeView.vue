<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import SparklineChart from '../components/SparklineChart.vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

// 비로그인 랜딩 배너 캐러셀 (10초 자동 디졸브)
const slides = [
  { visual: 'swipe', theme: 'th-swipe', label: '스와이핑 추천', title: '나만의 주식 매칭!', desc: '카드를 넘기기만 하면 내 투자 성향에 맞는 종목을 추천해드려요. 관심·저장으로 나만의 종목 리스트를 완성하세요.' },
  { visual: 'care', theme: 'th-care', label: '장투 케어', title: '우리 오늘 며칠?', desc: '건강한 투자 습관을 함께 만들어가요. 보유 종목을 꾸준히 점검하고, 장기 보유 점수를 기록해드려요.' },
  { visual: 'ai', theme: 'th-ai', label: 'AI 분석 서비스', title: '지금 이대로 괜찮을까요?', desc: 'AI가 재무·성장·궁합을 분석해 보유 종목의 장기 적합성을 알려드려요. 똑똑한 매수&매도를 위해서!' },
]
const currentSlide = ref(0)
let slideTimer = null
function nextSlide() { currentSlide.value = (currentSlide.value + 1) % slides.length }
function prevSlide() { currentSlide.value = (currentSlide.value - 1 + slides.length) % slides.length }
function startSlideTimer() { clearInterval(slideTimer); slideTimer = setInterval(nextSlide, 8000) }
// 좌우 버튼 수동 전환 — 자동 타이머 리셋
function goPrev() { prevSlide(); startSlideTimer() }
function goNext() { nextSlide(); startSlideTimer() }
onMounted(() => {
  if (!auth.isAuthenticated) startSlideTimer()
  else { startAchievedCarousel(); startRankTicker() }
})
onUnmounted(() => { clearInterval(slideTimer); clearInterval(achievedTimer); clearInterval(rankTimer) })

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
// 궁합 랭킹 — 장투 점수 상위 종목을 버튼에서 회전 표시 (목업)
const compatRanking = [
  { rank: 1, name: 'SK하이닉스', score: 86 },
  { rank: 2, name: '삼성바이오로직스', score: 82 },
  { rank: 3, name: 'NVIDIA', score: 80 },
  { rank: 4, name: '삼성전자', score: 78 },
  { rank: 5, name: '셀트리온', score: 75 },
]
const rankIdx = ref(0)
let rankTimer = null
const rankPreview = computed(() => compatRanking[rankIdx.value])
function startRankTicker() {
  clearInterval(rankTimer)
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  rankTimer = setInterval(() => { rankIdx.value = (rankIdx.value + 1) % compatRanking.length }, 2200)
}
function goRanking() { router.push({ path: '/stocks', query: { view: 'ranking' } }) }

// 달성 완료 마일스톤 — 회전목마(코버플로)
const achievedMilestones = [
  { icon: '👜', name: '명품 가방' },
  { icon: '💻', name: '노트북' },
  { icon: '📺', name: 'TV' },
  { icon: '📷', name: '카메라' },
  { icon: '⌚', name: '스마트워치' },
  { icon: '🎮', name: '게임기' },
]
const achievedIndex = ref(0)
let achievedTimer = null
function startAchievedCarousel() {
  clearInterval(achievedTimer)
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return
  achievedTimer = setInterval(() => {
    achievedIndex.value = (achievedIndex.value + 1) % achievedMilestones.length
  }, 2500)
}
function pauseAchievedCarousel() { clearInterval(achievedTimer) }
// 활성 항목 기준 좌우 오프셋 → 코버플로 위치/크기/투명도
function carouselStyle(i) {
  const n = achievedMilestones.length
  let d = i - achievedIndex.value
  if (d > n / 2) d -= n
  if (d < -n / 2) d += n
  const abs = Math.abs(d)
  if (abs >= 2) {
    return { transform: `translateX(${(d > 0 ? 1 : -1) * 64}px) scale(0.4)`, opacity: 0, zIndex: 0, pointerEvents: 'none' }
  }
  return {
    transform: `translateX(${d * 38}px) scale(${abs === 0 ? 1 : 0.6})`,
    opacity: abs === 0 ? 1 : 0.55,
    zIndex: 3 - abs,
  }
}

// 궁합 추천 스와이프 덱
const matchStocks = [
  {
    name: '삼성바이오로직스', code: '207940', market: 'KOSPI · 제약', sector: '제약',
    score: 86, price: '1,042,000원', change: '+1.4%', up: true, interest: 612,
    dna: [
      { label: '변동성', value: 63 }, { label: '성장', value: 85 },
      { label: '가치', value: 45 }, { label: '안정성', value: 60 },
    ],
    gradient: 'linear-gradient(135deg, #6d28d9 0%, #a855f7 45%, #db2777 100%)',
  },
  {
    name: 'SK하이닉스', code: '000660', market: 'KOSPI · 전기·전자', sector: '전기·전자',
    score: 94, price: '189,300원', change: '+2.1%', up: true, interest: 1284,
    dna: [
      { label: '변동성', value: 72 }, { label: '성장', value: 88 },
      { label: '가치', value: 52 }, { label: '안정성', value: 58 },
    ],
    gradient: 'linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #db2777 100%)',
  },
  {
    name: 'NAVER', code: '035420', market: 'KOSPI · IT 서비스', sector: 'IT 서비스',
    score: 80, price: '192,500원', change: '+1.4%', up: true, interest: 430,
    dna: [
      { label: '변동성', value: 58 }, { label: '성장', value: 76 },
      { label: '가치', value: 55 }, { label: '안정성', value: 62 },
    ],
    gradient: 'linear-gradient(135deg, #059669 0%, #10b981 50%, #06b6d4 100%)',
  },
  {
    name: '셀트리온', code: '068270', market: 'KOSPI · 제약', sector: '제약',
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

// Stock DNA 4축(변동성/성장/가치/안정성) → 레이더 차트 좌표
const dnaVertices = computed(() => {
  const d = current.value.dna
  const cx = 60, cy = 60, R = 46
  return [
    { x: cx, y: cy - (R * d[0].value) / 100 },
    { x: cx + (R * d[1].value) / 100, y: cy },
    { x: cx, y: cy + (R * d[2].value) / 100 },
    { x: cx - (R * d[3].value) / 100, y: cy },
  ]
})
const dnaPolygon = computed(() => dnaVertices.value.map(({ x, y }) => `${x},${y}`).join(' '))

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
  { name: '카카오',   ticker: '035720', qty: 30, avg: 41000,  cur: 44500,  color: '#facc15' },
  { name: '셀트리온', ticker: '068270', qty: 15, avg: 175000, cur: 168000, color: '#ec4899' },
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

    <!-- ===== 검색 바 (로그인 시 상단 노출) ===== -->
    <section v-if="auth.isAuthenticated" class="panel home-search" aria-label="종목 검색">
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

    <!-- ===== 섹션 1: 자산 목표 + 스와이핑 추천 (로그인 시) ===== -->
    <div v-if="auth.isAuthenticated" class="hero-grid">

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

        <!-- 보유 종목 (많으면 스크롤) -->
        <div class="asset-block">
          <div class="asset-block-head">
            <span class="asset-block-title">📊 보유 종목</span>
            <button class="asset-block-more" type="button" @click="router.push('/holdings')">전체 →</button>
          </div>
          <div class="asset-holdings">
            <button
              v-for="h in holdings"
              :key="h.ticker"
              type="button"
              class="ah-row"
              @click="router.push('/holdings')"
            >
              <span class="ah-dot" :style="{ background: h.color }"></span>
              <span class="ah-info">
                <strong class="ah-name">{{ h.name }}</strong>
                <small class="ah-meta">{{ h.ticker }} · {{ h.qty }}주</small>
              </span>
              <span class="ah-value">{{ hideAmount ? '••••' : fmt(h.qty * h.cur) + '원' }}</span>
              <span class="ah-pnl" :class="h.cur >= h.avg ? 'up' : 'down'">
                {{ h.cur >= h.avg ? '+' : '' }}{{ ((h.cur - h.avg) / h.avg * 100).toFixed(1) }}%
              </span>
            </button>
          </div>
        </div>

        <!-- 궁합 랭킹 (장투 점수 상위 종목 회전 표시 · 클릭 시 주식조회 궁합 랭킹) -->
        <button class="ltc-score" type="button" @click="goRanking">
          <span class="ltc-circle">{{ rankPreview.score }}<span>점</span></span>
          <span class="ltc-info">
            <span class="ltc-label">🏆 궁합 랭킹</span>
            <Transition name="ltc-roll" mode="out-in">
              <strong class="ltc-ticker" :key="rankIdx">
                <span class="ltc-rk">{{ rankPreview.rank }}위</span> {{ rankPreview.name }} · {{ rankPreview.score }}점
              </strong>
            </Transition>
          </span>
          <span class="ltc-arrow">→</span>
        </button>

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

        <!-- 현재 자산 마일스톤 (2열) -->
        <div class="milestone-block">
          <span class="asset-block-title">🎯 현재 자산 마일스톤</span>
          <div class="milestone-grid">
            <!-- 다음 목표 (넓게) -->
            <div class="milestone-card target">
              <div class="milestone-top">
                <span class="milestone-icon">✈️</span>
                <span class="goal-badge in-progress">진행중</span>
              </div>
              <span class="milestone-label">다음 목표</span>
              <strong class="milestone-name">유럽 여행</strong>
              <span class="milestone-amount">목표 5,000,000원</span>
              <div class="milestone-track">
                <div class="milestone-track-bar"><div style="width: 13%"></div></div>
                <span class="milestone-track-pct">13%</span>
              </div>
            </div>
            <!-- 달성 완료 (회전목마) -->
            <div class="milestone-card achieved milestone-carousel">
              <span class="milestone-done-title">달성 완료</span>
              <div
                class="carousel-stage"
                @mouseenter="pauseAchievedCarousel"
                @mouseleave="startAchievedCarousel"
              >
                <button
                  v-for="(m, i) in achievedMilestones"
                  :key="m.name"
                  type="button"
                  class="carousel-item"
                  :class="{ active: i === achievedIndex }"
                  :style="carouselStyle(i)"
                  :title="m.name"
                  @click="achievedIndex = i"
                >{{ m.icon }}</button>
              </div>
              <span class="carousel-name">{{ achievedMilestones[achievedIndex].name }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 오른쪽: 궁합 추천 스와이프 -->
      <section class="swipe-recommend-panel" aria-label="궁합 추천">
        <div class="match-header">
          <h2 class="match-title">오늘의 궁합 추천 💝</h2>
          <p class="match-sub">당신의 투자 성향과 잘 맞는 종목이에요. 넘기면서 관심 종목을 골라보세요.</p>
          <span class="match-count">추천 {{ matchIndex + 1 }} / {{ matchStocks.length }}</span>
        </div>

        <div class="deck-wrap">
          <article
            ref="cardEl"
            class="match-card"
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
              <div class="dna-head">
                <span class="dna-head-icon" aria-hidden="true">✦</span>
                <div>
                  <strong class="dna-title">Stock DNA</strong>
                  <span class="dna-caption">투자 성향 밸런스</span>
                </div>
              </div>
              <div class="dna-body">
                <div class="dna-chart-shell">
                  <svg class="dna-radar" viewBox="0 0 120 120" aria-hidden="true">
                    <defs>
                      <linearGradient id="dnaAreaGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#8b5cf6" stop-opacity=".9" />
                        <stop offset="55%" stop-color="#4f7cff" stop-opacity=".7" />
                        <stop offset="100%" stop-color="#22d3ee" stop-opacity=".82" />
                      </linearGradient>
                      <linearGradient id="dnaStrokeGradient" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stop-color="#a78bfa" />
                        <stop offset="50%" stop-color="#4f7cff" />
                        <stop offset="100%" stop-color="#22d3ee" />
                      </linearGradient>
                      <filter id="dnaGlow" x="-50%" y="-50%" width="200%" height="200%">
                        <feGaussianBlur stdDeviation="2.5" result="blur" />
                        <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                      </filter>
                    </defs>
                    <polygon class="dna-grid dna-grid-outer" points="60,8 112,60 60,112 8,60" />
                    <polygon class="dna-grid" points="60,25 95,60 60,95 25,60" />
                    <polygon class="dna-grid" points="60,42 78,60 60,78 42,60" />
                    <line class="dna-axis" x1="60" y1="8" x2="60" y2="112" />
                    <line class="dna-axis" x1="8" y1="60" x2="112" y2="60" />
                    <polygon class="dna-shape-glow" :points="dnaPolygon" />
                    <polygon class="dna-shape" :points="dnaPolygon" />
                    <circle
                      v-for="(point, pointIndex) in dnaVertices"
                      :key="pointIndex"
                      class="dna-point"
                      :cx="point.x"
                      :cy="point.y"
                      r="2.8"
                    />
                    <circle class="dna-center" cx="60" cy="60" r="2" />
                  </svg>
                </div>
                <div class="dna-metrics">
                  <div v-for="d in current.dna" :key="d.label" class="dna-metric">
                    <div class="dna-metric-head">
                      <span class="dna-k">{{ d.label }}</span>
                      <strong class="dna-v">{{ d.value }}</strong>
                    </div>
                    <div class="dna-track" aria-hidden="true">
                      <i :style="{ width: `${d.value}%` }"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="mc-reason">🐤 성장 선호와 {{ current.sector }} 모멘텀(성장 {{ current.dna[1].value }})이 맞아요.</div>
            <div class="mc-interest">❤️ {{ current.interest.toLocaleString('ko-KR') }}명이 이 종목에 관심 있어요</div>
          </article>
        </div>

        <!-- 액션 버튼 -->
        <div class="match-controls">
          <button class="match-btn pass" type="button" aria-label="관심없음" @click="swipe('left')">✕</button>
          <button class="match-btn save" type="button" aria-label="관심 종목 저장" @click="swipe('save')">♥</button>
          <button class="match-btn like" type="button" aria-label="관심" @click="swipe('right')">↗</button>
        </div>
        <p class="match-hint">카드를 좌우로 드래그하거나 버튼을 눌러 넘길 수 있어요</p>
      </section>
    </div>

    <!-- ===== 비로그인: 100vh 풀스크린 배너 (5초 자동 슬라이드) + 로그인 CTA ===== -->
    <template v-else>
      <section class="lp-banner" aria-label="서비스 소개">
        <!-- 검색바 오버레이 (배너 위에 떠 있음) -->
        <div class="lp-search-overlay">
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
        </div>

        <div class="lp-track">
          <div v-for="(s, i) in slides" :key="i" class="lp-slide" :class="[s.theme, { 'is-active': i === currentSlide }]">
            <video
              v-if="s.visual === 'swipe'"
              class="lp-slide-video"
              src="/videos/ai_comment.mp4"
              autoplay
              loop
              muted
              playsinline
              preload="metadata"
              aria-hidden="true"
            ></video>
            <video
              v-if="s.visual === 'care'"
              class="lp-slide-video"
              src="/videos/movie.mp4"
              autoplay
              loop
              muted
              playsinline
              preload="metadata"
              aria-hidden="true"
            ></video>
            <video
              v-if="s.visual === 'ai'"
              class="lp-slide-video"
              src="/videos/ai-analysis.mp4"
              autoplay
              loop
              muted
              playsinline
              preload="metadata"
              aria-hidden="true"
            ></video>
            <div class="lp-slide-inner">
              <div class="lp-slide-text">
                <div class="lp-slide-meta">
                  <span class="lp-num">0{{ i + 1 }} / 03</span>
                  <span class="lp-label">{{ s.label }}</span>
                </div>
                <h1 class="lp-slide-title">
                  <template v-if="s.visual === 'ai'">지금 이대로<br />괜찮을까요?</template>
                  <template v-else>{{ s.title }}</template>
                </h1>
                <p class="lp-slide-desc">{{ s.desc }}</p>
              </div>
            </div>
          </div>
        </div>
        <!-- 좌우 배너 전환 버튼 -->
        <button class="lp-nav lp-nav-prev" type="button" @click="goPrev" aria-label="이전 배너">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 5l-7 7 7 7" /></svg>
        </button>
        <button class="lp-nav lp-nav-next" type="button" @click="goNext" aria-label="다음 배너">
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 5l7 7-7 7" /></svg>
        </button>

        <!-- 로그인 CTA: 배너 하단 그라데이션 밴드 -->
        <div class="lp-login">
          <span class="lp-login-text">나만의 주식을 만나보아요!</span>
          <button class="lp-login-btn" type="button" @click="router.push('/login')">로그인하기 →</button>
        </div>
      </section>
    </template>

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
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ===== 비로그인: 100vh 풀스크린 배너 캐러셀 ===== */
.lp-banner {
  position: relative;
  width: 100vw;
  max-width: 100vw;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  /* 네비(64 + border 1) + main 상단 패딩(24)만큼 끌어올려 화면 최상단에 붙이고 네비/검색바가 위로 겹치게 */
  margin-top: -89px;
  min-height: 100vh;
  overflow: hidden;
}
.lp-track {
  display: grid;
  min-height: 100vh;
}
/* 디졸브(크로스페이드): 모든 슬라이드를 같은 그리드 셀에 겹쳐 두고 opacity로 전환 */
.lp-slide {
  grid-area: 1 / 1;
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
  z-index: 0;
  transition: opacity 0.8s ease;
}
.lp-slide.is-active {
  opacity: 1;
  pointer-events: auto;
  z-index: 1;
}

/* 좌우 배너 전환 버튼 */
.lp-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 6;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s ease;
}
.lp-nav:hover { background: rgba(255, 255, 255, 0.16); }
.lp-nav:active { background: rgba(255, 255, 255, 0.24); }
.lp-nav svg {
  width: 30px;
  height: 30px;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.lp-nav-prev { left: 18px; }
.lp-nav-next { right: 18px; }

/* 배너 배경: 라이트 모드 (밝고 선명한 브랜드 톤) */
.lp-slide.th-swipe { background: linear-gradient(135deg, #7c4dff 0%, #b35cd6 52%, #ff5fa2 100%); }
.lp-slide.th-care { background: linear-gradient(135deg, #14b88a 0%, #2f8fe0 55%, #5566e8 100%); }
.lp-slide.th-ai { background: linear-gradient(135deg, #3f74ff 0%, #7b57f0 52%, #ad5ce0 100%); }

/* 배너 배경: 다크 모드 (깊고 차분한 톤) */
html[data-theme='dark'] .lp-slide.th-swipe { background: linear-gradient(135deg, #2a1560 0%, #561d83 52%, #7a1f55 100%); }
html[data-theme='dark'] .lp-slide.th-care { background: linear-gradient(135deg, #06382b 0%, #0c3b66 55%, #181f6b 100%); }
html[data-theme='dark'] .lp-slide.th-ai { background: linear-gradient(135deg, #122259 0%, #281c68 52%, #441d66 100%); }

/* 세 번째 배너: 영상이 슬라이드 전체를 채우는 시네마틱 배경 */
.lp-slide-video {
  position: absolute;
  inset: 0;
  z-index: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  transform: scale(1.01);
  filter: saturate(1.08) contrast(1.04);
}

/* 배너 위에 떠 있는 검색바 오버레이 */
.lp-search-overlay {
  position: absolute;
  top: 76px;
  left: 0;
  right: 0;
  z-index: 5;
  display: flex;
  justify-content: center;
  padding: 0 28px;
  pointer-events: none;
}
.lp-search-overlay .home-search { width: min(1480px, 100%); pointer-events: auto; }
.lp-slide::before {
  content: ''; position: absolute; inset: 0; z-index: 1; pointer-events: none;
  background: radial-gradient(50% 60% at 78% 28%, rgba(255,255,255,0.12), transparent 60%);
}
.lp-slide.th-ai::before {
  background:
    linear-gradient(90deg, rgba(7, 10, 27, 0.82) 0%, rgba(12, 15, 38, 0.62) 38%, rgba(12, 15, 38, 0.14) 72%, rgba(7, 10, 27, 0.38) 100%),
    linear-gradient(180deg, rgba(5, 8, 22, 0.4) 0%, transparent 34%, rgba(5, 8, 22, 0.3) 100%);
}
.lp-slide.th-swipe::before {
  background: linear-gradient(90deg, rgba(8, 6, 24, 0.34) 0%, rgba(8, 6, 24, 0.12) 50%, transparent 100%);
}
.lp-slide.th-care::before {
  background:
    linear-gradient(90deg, rgba(4, 18, 14, 0.78) 0%, rgba(6, 24, 18, 0.58) 40%, rgba(6, 24, 18, 0.2) 74%, rgba(4, 18, 14, 0.42) 100%),
    linear-gradient(180deg, rgba(3, 14, 11, 0.4) 0%, transparent 36%, rgba(3, 14, 11, 0.32) 100%);
}
.lp-slide-inner {
  position: relative;
  z-index: 2;
  width: min(1480px, 100%);
  margin: 0 auto;
  padding: 0 60px;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 40px;
  align-items: center;
}
.lp-slide.th-ai .lp-slide-inner,
.lp-slide.th-swipe .lp-slide-inner,
.lp-slide.th-care .lp-slide-inner { grid-template-columns: minmax(0, 760px); }
.lp-slide.th-ai .lp-slide-text,
.lp-slide.th-swipe .lp-slide-text,
.lp-slide.th-care .lp-slide-text { text-shadow: 0 3px 24px rgba(0, 0, 0, 0.4); }
.lp-slide-text { color: #fff; }
.lp-slide-meta { display: flex; align-items: center; gap: 12px; }
.lp-num { font-size: 13px; font-weight: 900; color: rgba(255,255,255,0.6); letter-spacing: 0.1em; }
.lp-label {
  padding: 5px 14px; border-radius: 999px;
  background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.24);
  color: #fff; font-size: 13px; font-weight: 900;
}
.lp-slide-title { margin: 20px 0 16px; font-size: clamp(38px, 6vw, 76px); font-weight: 900; line-height: 1.05; letter-spacing: -2px; color: rgb(255, 255, 255);}
.lp-slide-desc { margin: 0; max-width: 480px; font-size: 16px; font-weight: 600; line-height: 1.7; color: rgba(255,255,255,0.82); word-break: keep-all; }
.lp-slide-visual { display: flex; align-items: center; justify-content: center; }
.lp-vis { position: relative; width: 280px; height: 300px; display: flex; align-items: center; justify-content: center; }

/* 비주얼: 스와이프 데모 */
.demo-card { position: absolute; width: 200px; height: 240px; border-radius: 20px; box-shadow: 0 16px 44px rgba(0,0,0,0.35); }
.demo-card.c1 {
  z-index: 3; padding: 18px; color: #fff;
  background: linear-gradient(135deg, #6d28d9, #db2777);
  display: flex; flex-direction: column; gap: 8px;
  animation: demoSway 3.2s ease-in-out infinite;
}
.demo-card.c2 { z-index: 2; background: rgba(255,255,255,0.45); transform: rotate(6deg) translateX(14px) scale(0.96); }
.demo-card.c3 { z-index: 1; background: rgba(255,255,255,0.25); transform: rotate(-7deg) translateX(-16px) scale(0.92); }
@keyframes demoSway { 0%, 100% { transform: rotate(-7deg) translateX(-10px); } 50% { transform: rotate(7deg) translateX(10px); } }
.demo-badge { align-self: flex-start; padding: 4px 10px; border-radius: 999px; background: rgba(255,255,255,0.2); font-size: 10px; font-weight: 900; }
.demo-name { margin-top: auto; font-size: 22px; font-weight: 900; letter-spacing: -0.5px; }
.demo-pill { align-self: flex-start; padding: 3px 10px; border-radius: 999px; background: rgba(255,255,255,0.22); font-size: 12px; font-weight: 900; }
.demo-like { position: absolute; right: 16px; bottom: 16px; font-size: 26px; }

/* 비주얼: 장투 케어 */
.care-card {
  width: 220px; padding: 24px; border-radius: 22px; text-align: center;
  background: #fff; box-shadow: 0 18px 50px rgba(0,0,0,0.3);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.care-label { font-size: 11px; font-weight: 900; color: var(--muted); letter-spacing: 0.08em; }
.care-day { font-size: 42px; font-weight: 900; letter-spacing: -2px; background: linear-gradient(135deg, #0f9f6e, var(--accent)); -webkit-background-clip: text; background-clip: text; color: transparent; }
.care-dots { display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; max-width: 168px; }
.care-dots i { width: 12px; height: 12px; border-radius: 4px; background: #e6ecf5; }
.care-dots i.on { background: #0f9f6e; }
.care-sub { font-size: 12px; font-weight: 800; color: #0f9f6e; }

/* ===== 로그인 유도 CTA (배너 하단 그라데이션 밴드) ===== */
.lp-login {
  position: absolute; left: 0; right: 0; bottom: 0; z-index: 3;
  display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap;
  padding: 30px 24px 42px;
  background: linear-gradient(to top, rgba(12,14,34,0.8) 0%, rgba(12,14,34,0.35) 55%, transparent 100%);
}
.lp-login-text { font-size: clamp(16px, 2.2vw, 22px); font-weight: 900; color: #fff; letter-spacing: -0.3px; }
.lp-login-btn {
  height: 48px; padding: 0 28px; border: 0; border-radius: 999px;
  background: linear-gradient(135deg, var(--accent), var(--purple) 68%, #ff5b8f);
  color: #fff; font-size: 15px; font-weight: 900; cursor: pointer;
  box-shadow: 0 12px 30px rgba(var(--accent-rgb), 0.45);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.lp-login-btn:hover { transform: translateY(-2px); box-shadow: 0 16px 38px rgba(var(--accent-rgb), 0.55); }

@media (max-width: 800px) {
  .lp-slide-inner { grid-template-columns: 1fr; padding: 0 22px; text-align: center; justify-items: center; gap: 22px; }
  .lp-slide.th-ai .lp-slide-inner,
  .lp-slide.th-swipe .lp-slide-inner,
  .lp-slide.th-care .lp-slide-inner { grid-template-columns: 1fr; }
  .lp-slide.th-ai::before {
    background:
      linear-gradient(180deg, rgba(6, 9, 25, 0.52) 0%, rgba(8, 11, 29, 0.48) 50%, rgba(5, 8, 22, 0.68) 100%),
      radial-gradient(circle at center, rgba(14, 18, 45, 0.12), rgba(5, 8, 22, 0.45));
  }
  /* 번호(01/03) 위, 라벨(스와이핑 추천) 아래로 — 가운데 정렬 */
  .lp-slide-meta { flex-direction: column; gap: 8px; }
  .lp-slide-title { margin: 12px 0 12px; font-size: clamp(32px, 8vw, 52px); letter-spacing: -1px; }
  .lp-slide-desc { margin: 0 auto; font-size: 15px; }
  .lp-vis { width: 240px; height: 250px; }
  .lp-nav { top: auto; bottom: 32px; width: 40px; height: 40px; transform: none; }
  .lp-nav svg { width: 22px; height: 22px; }
  .lp-nav-prev { left: 4px; }
  .lp-nav-next { right: 4px; }
}

@media (prefers-reduced-motion: reduce) {
  .lp-slide { transition: none; }
  .demo-card.c1 { animation: none; }
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
  grid-template-columns: minmax(0, 1.02fr) minmax(0, 0.98fr);
  gap: clamp(30px, 3.5vw, 56px);
  align-items: start;
  padding: 0;
}

/* --- 자산/목표 패널 --- */
.goal-panel {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: clamp(22px, 1.8vw, 26px);
}
.goal-panel .panel-head { margin-bottom: 0; }

/* --- 자산 마일스톤 (2열) --- */
.milestone-block { display: flex; flex-direction: column; gap: 10px; }
.milestone-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr); gap: 12px; align-items: stretch; }
.milestone-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px;
  border-radius: var(--radius);
}
.milestone-card.target,
.milestone-card.achieved {
  background: var(--surface-soft);
  border: 1px solid var(--glass-border);
}
.milestone-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px; }
.milestone-icon { font-size: 20px; }
.milestone-label { font-size: 11px; font-weight: 900; color: var(--muted); }
.milestone-name { font-size: 15px; font-weight: 900; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.milestone-amount { font-size: 12px; font-weight: 700; color: var(--muted); }
.milestone-track { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.milestone-track-bar { flex: 1; height: 5px; background: var(--track); border-radius: 999px; overflow: hidden; }
.milestone-track-bar > div { height: 100%; background: #8b95a5; border-radius: 999px; }
.milestone-track-pct { font-size: 11px; font-weight: 900; color: var(--muted); }

/* 달성 완료 — 회전목마(코버플로) */
.milestone-carousel { gap: 6px; text-align: center; }
.milestone-done-title { font-size: 12px; font-weight: 900; color: var(--muted); }
.carousel-stage {
  position: relative;
  flex: 1;
  min-height: 72px;
}
.carousel-item {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 52px;
  height: 52px;
  margin: -26px 0 0 -26px;
  display: grid;
  place-items: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.25));
  transition: transform 0.45s cubic-bezier(0.34, 1.3, 0.5, 1), opacity 0.4s ease, background 0.3s ease, box-shadow 0.3s ease;
  will-change: transform, opacity;
}
.carousel-item.active {
  background: var(--chip-active);
  border: 1px solid var(--glass-border);
  box-shadow: 0 2px 7px rgba(17, 24, 39, 0.08);
}
.carousel-name {
  font-size: 12px;
  font-weight: 800;
  color: var(--ink);
  text-shadow: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  background: var(--glass-subtle);
  color: var(--muted);
  border: 1px solid var(--glass-border);
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
  gap: 18px;
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
.asset-return-value.is-up { color: var(--krx-up) !important; }
.asset-return-value.is-down { color: var(--krx-down) !important; }

/* --- 액션 버튼 2개 --- */
.asset-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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

/* --- 보유 종목 리스트 (많으면 스크롤) --- */
.asset-block { display: flex; flex-direction: column; gap: 10px; }
.asset-block-head { display: flex; align-items: center; justify-content: space-between; }
.asset-block-title { font-size: 13px; font-weight: 900; color: var(--ink); }
.asset-block-more {
  border: 0; background: none; padding: 0;
  font-size: 12px; font-weight: 900; color: var(--accent); cursor: pointer;
}
.asset-holdings {
  display: flex;
  flex-direction: column;
  max-height: 392px;
  overflow-y: auto;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius);
  background: var(--surface-soft);
}
.ah-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 11px 14px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background 0.14s;
}
.ah-row:last-child { border-bottom: 0; }
.ah-row:hover { background: var(--surface-hover); }
.ah-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.ah-info { min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.ah-name { font-size: 13px; font-weight: 800; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ah-meta { font-size: 11px; font-weight: 700; color: var(--muted); }
.ah-value { font-size: 13px; font-weight: 800; color: var(--ink); white-space: nowrap; }
.ah-pnl { font-size: 12px; font-weight: 900; white-space: nowrap; min-width: 48px; text-align: right; }
.ah-pnl.up { color: #e3344f; }
.ah-pnl.down { color: #2b59d6; }

/* --- 장투 케어 종합 점수 + 랭킹 --- */
.ltc-score {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
  padding: 16px 18px;
  border-radius: var(--radius);
  border: 1px solid rgba(var(--accent-rgb), 0.22);
  background: var(--surface-soft);
  cursor: pointer;
  text-align: left;
  transition: background 0.16s, transform 0.15s;
}
.ltc-score:hover { background: var(--surface-hover); transform: translateY(-1px); }
.ltc-circle {
  position: relative;
  flex-shrink: 0;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  font-size: 19px;
  font-weight: 900;
  line-height: 1;
  box-shadow: 0 6px 16px rgba(var(--accent-rgb), 0.3);
}
.ltc-circle span {
  position: absolute;
  right: -4px;
  bottom: -4px;
  padding: 1px 6px;
  border-radius: 999px;
  background: #fff;
  color: var(--accent);
  font-size: 10px;
  font-weight: 900;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}
.ltc-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.ltc-label { font-size: 12px; font-weight: 900; color: var(--muted); }
.ltc-ticker { display: block; font-size: 15px; font-weight: 900; color: var(--ink); letter-spacing: -0.3px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ltc-rk { color: var(--accent); margin-right: 2px; }
.ltc-roll-enter-active, .ltc-roll-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.ltc-roll-enter-from { opacity: 0; transform: translateY(6px); }
.ltc-roll-leave-to { opacity: 0; transform: translateY(-6px); }
.ltc-arrow { color: var(--faint); font-size: 16px; font-weight: 900; flex-shrink: 0; }

/* --- 궁합 추천 스와이프 패널 --- */
.swipe-recommend-panel {
  position: relative;
  isolation: isolate;
  align-self: stretch;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
  min-width: 0;
  padding: clamp(16px, 2vh, 24px) clamp(6px, 1.8vw, 24px);
}

/* 단색 페이지의 여백을 깨지 않도록 장식용 컬러 오라는 제거한다. */
.swipe-recommend-panel::before,
.swipe-recommend-panel::after {
  content: none;
}
.swipe-recommend-panel > * { position: relative; z-index: 1; }

.match-header {
  width: min(100%, 640px);
  margin: 0 auto 20px;
  text-align: center;
}
.match-title {
  margin: 0;
  font-size: 23px;
  font-weight: 900;
  letter-spacing: -0.5px;
  color: var(--ink);
}
.match-sub {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
  word-break: keep-all;
}
.match-count {
  display: inline-block;
  margin-top: 10px;
  color: var(--faint);
  font-size: 12px;
  font-weight: 900;
}

.deck-wrap {
  position: relative;
  width: min(100%, 680px);
  margin: 0 auto;
}

.match-card {
  position: relative;
  width: 100%;
  border-radius: 24px;
  padding: 26px;
  color: #fff;
  box-shadow: 0 12px 40px rgba(109, 40, 217, 0.3), 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  user-select: none;
  touch-action: none;
  cursor: grab;
  will-change: transform, opacity;
}
.match-card:active { cursor: grabbing; }
html[data-palette='love'] .match-card {
  background: linear-gradient(135deg, #ff6036 0%, #ff385c 44%, #fd267a 100%) !important;
  box-shadow: 0 18px 48px rgba(255, 56, 92, 0.3), 0 5px 16px rgba(113, 21, 54, 0.2);
}
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

.mc-name-block { margin-top: 20px; }
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
  margin-top: 18px;
}
.mc-price-box {
  padding: 13px 14px;
  border-radius: 14px;
  background: #f7f8fb;
  border: 1px solid #dfe4ea;
  box-shadow: 0 2px 7px rgba(17, 24, 39, 0.08);
}
.mc-price-box span {
  display: block;
  color: rgba(23, 33, 61, 0.62);
  font-size: 11px;
  font-weight: 900;
  margin-bottom: 4px;
}
.mc-price-box strong { display: block; color: #17213d; font-size: 15px; font-weight: 900; }
.mc-price-box strong.up { color: #b6193c; }
.mc-price-box strong.down { color: #075db8; }

html[data-theme='dark'] .mc-price-box {
  background: #1b2230;
  border-color: #354052;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}
html[data-theme='dark'] .mc-price-box span { color: rgba(235, 240, 255, 0.7); }
html[data-theme='dark'] .mc-price-box strong { color: #fff; }
html[data-theme='dark'] .mc-price-box strong.up { color: #ff8298; }
html[data-theme='dark'] .mc-price-box strong.down { color: #86bcff; }

/* Stock DNA */
.mc-dna {
  --dna-ink: #17213d;
  --dna-muted: #69758f;
  --dna-accent: #4f6fff;
  --dna-track: rgba(79, 111, 255, 0.12);
  margin-top: 18px;
  padding: 18px 18px 20px;
  border: 1px solid #dfe4ea;
  border-radius: 16px;
  background: #f7f8fb;
  box-shadow: 0 3px 10px rgba(17, 24, 39, 0.08);
  color: var(--dna-ink);
}
.dna-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.dna-head-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: linear-gradient(135deg, #7c3aed, #4f7cff 58%, #22d3ee);
  color: #fff;
  font-size: 15px;
  box-shadow: 0 6px 14px rgba(79, 111, 255, 0.28);
}
.dna-title {
  display: block;
  color: var(--dna-ink);
  font-size: 14px;
  font-weight: 950;
  line-height: 1.15;
  letter-spacing: -0.1px;
}
.dna-caption {
  display: block;
  margin-top: 2px;
  color: var(--dna-muted);
  font-size: 10px;
  font-weight: 750;
}
.dna-body {
  display: grid;
  grid-template-columns: 126px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
}
.dna-chart-shell {
  position: relative;
  display: grid;
  place-items: center;
  aspect-ratio: 1;
  border-radius: 50%;
  background: #eef2ff;
  box-shadow: inset 0 0 0 1px #dce4ff;
}
.dna-chart-shell::after {
  content: '';
  position: absolute;
  inset: 9px;
  border: 1px solid rgba(79, 111, 255, 0.1);
  border-radius: 50%;
  pointer-events: none;
}
.dna-radar { width: 88%; height: 88%; overflow: visible; }
.dna-grid { fill: rgba(79, 111, 255, 0.018); stroke: rgba(79, 111, 255, 0.16); stroke-width: 0.8; }
.dna-grid-outer { fill: rgba(79, 111, 255, 0.025); stroke: rgba(79, 111, 255, 0.24); stroke-width: 1; }
.dna-axis { stroke: rgba(79, 111, 255, 0.13); stroke-width: 0.8; stroke-dasharray: 2 3; }
.dna-shape-glow { fill: none; stroke: rgba(79, 124, 255, 0.38); stroke-width: 6; filter: url(#dnaGlow); }
.dna-shape { fill: url(#dnaAreaGradient); fill-opacity: 0.54; stroke: url(#dnaStrokeGradient); stroke-width: 2.2; stroke-linejoin: round; }
.dna-point { fill: #fff; stroke: #5877ff; stroke-width: 1.8; filter: url(#dnaGlow); }
.dna-center { fill: #4f7cff; }
.dna-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.dna-metric {
  min-width: 0;
  padding: 10px 11px;
  border: 1px solid #e1e5eb;
  border-radius: 12px;
  background: #ffffff;
  box-shadow: none;
}
.dna-metric-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}
.dna-k { color: var(--dna-muted); font-size: 11px; font-weight: 850; white-space: nowrap; }
.dna-v { color: var(--dna-accent); font-size: 15px; font-weight: 950; line-height: 1; }
.dna-track {
  height: 5px;
  margin-top: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--dna-track);
}
.dna-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #7c3aed, #4f7cff 62%, #22d3ee);
  box-shadow: 0 0 10px rgba(79, 124, 255, 0.38);
}

html[data-theme='dark'] .mc-dna {
  --dna-ink: #f5f7ff;
  --dna-muted: #aeb9d7;
  --dna-accent: #aabaff;
  --dna-track: rgba(149, 169, 255, 0.14);
  border-color: #354052;
  background: #151b27;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2);
}
html[data-theme='dark'] .dna-chart-shell {
  background: #1c2434;
  box-shadow: inset 0 0 0 1px #303b50;
}
html[data-theme='dark'] .dna-chart-shell::after { border-color: rgba(171, 186, 255, 0.12); }
html[data-theme='dark'] .dna-grid { fill: rgba(150, 168, 255, 0.025); stroke: rgba(171, 186, 255, 0.2); }
html[data-theme='dark'] .dna-grid-outer { stroke: rgba(171, 186, 255, 0.34); }
html[data-theme='dark'] .dna-axis { stroke: rgba(171, 186, 255, 0.18); }
html[data-theme='dark'] .dna-metric {
  border-color: #303a4b;
  background: #202735;
  box-shadow: none;
}

.mc-reason { margin-top: 16px; font-size: 13px; font-weight: 800; color: #fff; text-shadow: 0 1px 6px rgba(0, 0, 0, 0.3); }
.mc-interest { margin-top: 14px; font-size: 13px; font-weight: 800; color: #fff; text-shadow: 0 1px 6px rgba(0, 0, 0, 0.3); }

/* 컨트롤 버튼 */
.match-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 24px;
}
.match-btn {
  width: 54px;
  height: 54px;
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
.match-btn.like { color: var(--accent); border-color: rgba(var(--accent-rgb), 0.4); background: rgba(var(--accent-rgb), 0.07); }
.match-btn.save {
  width: 66px;
  height: 66px;
  border: 0;
  background: linear-gradient(135deg, #ff3d8b 0%, #e3344f 100%);
  color: #fff;
  font-size: 26px;
  box-shadow: 0 10px 30px rgba(255, 61, 139, 0.45);
}
html[data-palette='love'] .match-btn.save {
  background: linear-gradient(135deg, #ff6036, #ff385c 50%, #fd267a);
  box-shadow: 0 11px 32px rgba(255, 56, 92, 0.42);
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
.index-card.is-up-card :deep(.sparkline-fill) { fill: rgba(var(--accent-rgb), 0.08); }
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

/* 지수 등락 글자색 (한국 관례: 상승=빨강, 하락=파랑) */
.index-change.is-up { color: var(--krx-up) !important; }
.index-change.is-down { color: var(--krx-down) !important; }

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
  border: 1px solid rgba(var(--accent-rgb), 0.25);
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
  transition: background 0.18s ease;
  flex-shrink: 0;
}

.more-btn:hover { background: rgba(var(--accent-rgb), 0.15); }

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
  background: rgba(var(--accent-rgb), 0.1);
  color: var(--accent);
  border: 1px solid rgba(var(--accent-rgb), 0.2);
}

.news-ticker {
  background: rgba(var(--purple-rgb), 0.1);
  color: var(--purple);
  border-color: rgba(var(--purple-rgb), 0.2);
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
  padding: 10px 0; border-bottom: 1px solid var(--line);
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
.hr-pnl.is-up { color: var(--krx-up) !important; }
.hr-pnl.is-down { color: var(--krx-down) !important; }

.diary-list { display: flex; flex-direction: column; }
.diary-row {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid var(--line);
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
  border: 1px dashed rgba(var(--accent-rgb), 0.3);
  background: rgba(var(--accent-rgb), 0.04);
  color: var(--accent); font-size: 13px; font-weight: 900;
  cursor: pointer; transition: background 0.15s;
}
.diary-write-btn:hover { background: rgba(var(--accent-rgb), 0.1); }

/* ===== 반응형 ===== */
@media (max-width: 1100px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: 30px;
    min-height: auto;
    padding-top: 8px;
  }
  .swipe-recommend-panel { padding: 32px 0 12px; }
}

@media (max-width: 800px) {
  .market-indices-grid { grid-template-columns: repeat(2, 1fr); }
  .index-card:nth-child(2n) { border-right: 0; }
  .index-card:nth-child(n+3) { border-top: 1px solid var(--line); }
  .news-grid { grid-template-columns: 1fr; }
  .bottom-grid { grid-template-columns: 1fr; }
}

@media (max-width: 600px) {
  .goal-panel { padding: 20px; gap: 16px; }
  .asset-summary { gap: 14px; }
  .asset-actions { grid-template-columns: 1fr; }
  .swipe-recommend-panel { padding-top: 24px; }
  .match-header { margin-bottom: 22px; }
  .match-title { font-size: 22px; }
  .match-card { padding: 18px; }
  .mc-dna { padding: 14px; }
  .dna-body { grid-template-columns: 108px minmax(0, 1fr); gap: 12px; }
  .dna-metrics { grid-template-columns: 1fr; gap: 6px; }
  .dna-metric { padding: 7px 9px; }
  .dna-track { margin-top: 5px; }
}
</style>
