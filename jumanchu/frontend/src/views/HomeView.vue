<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import SparklineChart from '../components/SparklineChart.vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import logoWall from '../../0621ref/q.png'
import notebookBg from '../../0621ref/2.png'
import aiHandImg from '../../0621ref/3.jpg'

const router = useRouter()
const auth = useAuthStore()

// 비로그인 랜딩 배너 캐러셀 (5초 자동 슬라이드)
const slides = [
  { visual: 'swipe', theme: 'th-swipe', label: '스와이핑 추천', title: '나만의 주식 매칭!', desc: '카드를 넘기기만 하면 내 투자 성향에 맞는 종목을 추천해드려요. 관심·저장으로 나만의 종목 리스트를 완성하세요.' },
  { visual: 'care', theme: 'th-care', label: '장투 케어', title: '우리 오늘 며칠?', desc: '건강한 투자 습관을 함께 만들어가요. 보유 종목을 꾸준히 점검하고, 장기 보유 점수를 기록해드려요.' },
  { visual: 'ai', theme: 'th-ai', label: 'AI 분석 서비스', title: '지금 이대로\n괜찮을까요?', desc: 'AI가 재무·성장·궁합을 분석해 보유 종목의 장기 적합성을 알려드려요. 매수·매도 판단을 똑똑하게.' },
]
const currentSlide = ref(0)
let slideTimer = null
function nextSlide() { currentSlide.value = (currentSlide.value + 1) % slides.length }
function prevSlide() { currentSlide.value = (currentSlide.value - 1 + slides.length) % slides.length }
function startSlideTimer() { clearInterval(slideTimer); slideTimer = setInterval(nextSlide, 5000) }
// 좌우 버튼 수동 이동 — 이동 후 자동 슬라이드 타이머 리셋
function goPrev() { prevSlide(); startSlideTimer() }
function goNext() { nextSlide(); startSlideTimer() }
// 지금 이대로 괜찮을까요?: 손+칩을 배경(하늘색)에서 분리(런타임 canvas 키잉) → 단일 하늘색 위에 올려 좌우 분할 제거
const aiCutout = ref(aiHandImg)
function buildAiCutout() {
  const img = new Image()
  img.onload = () => {
    try {
      const c = document.createElement('canvas')
      c.width = img.naturalWidth
      c.height = img.naturalHeight
      const ctx = c.getContext('2d', { willReadFrequently: true })
      ctx.drawImage(img, 0, 0)
      const d = ctx.getImageData(0, 0, c.width, c.height)
      const p = d.data
      // 네 모서리 평균 = 배경 하늘색
      const corners = [0, (c.width - 1) * 4, c.width * (c.height - 1) * 4, (c.width * c.height - 1) * 4]
      let br = 0, bg = 0, bb = 0
      for (const k of corners) { br += p[k]; bg += p[k + 1]; bb += p[k + 2] }
      br /= 4; bg /= 4; bb /= 4
      const t0 = 24, t1 = 62 // 배경과의 색거리: t0 이하=투명, t1 이상=불투명(가장자리 페더링)
      for (let i = 0; i < p.length; i += 4) {
        const dr = p[i] - br, dg = p[i + 1] - bg, db = p[i + 2] - bb
        const dist = Math.sqrt(dr * dr + dg * dg + db * db)
        if (dist <= t0) p[i + 3] = 0
        else if (dist < t1) p[i + 3] = Math.round((255 * (dist - t0)) / (t1 - t0))
      }
      ctx.putImageData(d, 0, 0)
      aiCutout.value = c.toDataURL('image/png')
    } catch (e) {
      /* 캔버스 미지원/보안 시 원본 유지 */
    }
  }
  img.src = aiHandImg
}

// 스와이핑 추천: q.png 어두운 배경을 키잉(투명화) → 로고 모양 그대로 발광시키기 위한 알파 소스
const keyedWall = ref(logoWall)
function buildLogoWallKey() {
  const img = new Image()
  img.onload = () => {
    try {
      const c = document.createElement('canvas')
      c.width = img.naturalWidth
      c.height = img.naturalHeight
      const ctx = c.getContext('2d', { willReadFrequently: true })
      ctx.drawImage(img, 0, 0)
      const d = ctx.getImageData(0, 0, c.width, c.height)
      const p = d.data
      const corners = [0, (c.width - 1) * 4, c.width * (c.height - 1) * 4, (c.width * c.height - 1) * 4]
      let br = 0, bg = 0, bb = 0
      for (const k of corners) { br += p[k]; bg += p[k + 1]; bb += p[k + 2] }
      br /= 4; bg /= 4; bb /= 4
      const t0 = 34, t1 = 78
      for (let i = 0; i < p.length; i += 4) {
        const dr = p[i] - br, dg = p[i + 1] - bg, db = p[i + 2] - bb
        const dist = Math.sqrt(dr * dr + dg * dg + db * db)
        if (dist <= t0) p[i + 3] = 0
        else if (dist < t1) p[i + 3] = Math.round((255 * (dist - t0)) / (t1 - t0))
      }
      ctx.putImageData(d, 0, 0)
      keyedWall.value = c.toDataURL('image/png')
    } catch (e) { /* 미지원/보안 시 원본 유지 */ }
  }
  img.src = logoWall
}

onMounted(() => {
  if (!auth.isAuthenticated) startSlideTimer()
  buildAiCutout()
  buildLogoWallKey()
})
onUnmounted(() => clearInterval(slideTimer))

// 슬라이드별 배경: 공책(우리 오늘 며칠?) / AI손(지금 이대로 괜찮을까요?)
// 스와이핑 추천은 우주배경 대신 다크 그라데이션 + 아래 로고 클라우드 사용
// 스와이핑 추천 로고월(q.png) — 화이트 위에 흐릿하게 (채도/블러/투명도는 .swipe-bg CSS)
const swipeBgStyle = { backgroundImage: `url(${logoWall})` }
// 각 로고 위 hover 핫스팟 — 마우스 올리면 브랜드 색으로 로고 모양 그대로 발광
// x,y=화면 % 중심, w,h=로고 박스 크기(%) → 이 영역만 클립해 모양 알파 확보 (위치/크기 조정 가능)
const swipeLogos = [
  { key: 'lg', x: 16, y: 24, w: 18, h: 14, color: '#e23b6d' },
  { key: 'sk', x: 42, y: 23, w: 16, h: 14, color: '#ff4d3d' },
  { key: 'hyundai', x: 72, y: 24, w: 22, h: 14, color: '#3f74e6' },
  { key: 'samsung', x: 18, y: 38, w: 20, h: 13, color: '#3b5bd9' },
  { key: 'posco', x: 45, y: 38, w: 16, h: 13, color: '#19a7e6' },
  { key: 'soil', x: 63, y: 38, w: 16, h: 13, color: '#ff4d4d' },
  { key: 'kia', x: 85, y: 39, w: 16, h: 14, color: '#9aa6b6' },
  { key: 'shinhan', x: 24, y: 52, w: 19, h: 13, color: '#2a5bff' },
  { key: 'gs', x: 50, y: 52, w: 16, h: 13, color: '#13b5b1' },
  { key: 'hanwha', x: 79, y: 52, w: 19, h: 13, color: '#ff8a2a' },
  { key: 'kakao', x: 18, y: 67, w: 17, h: 13, color: '#ffd400' },
  { key: 'kb', x: 47, y: 67, w: 22, h: 13, color: '#ffc01e' },
  { key: 'naver', x: 77, y: 67, w: 19, h: 13, color: '#19c95f' },
]
const keyedBg = computed(() => `url(${keyedWall.value})`)
// 로고를 부드러운 타원 마스크로 (사각형 경계 없이 로고 전체가 빛나게) — vw/vh로 로고 크기에 맞춤
function logoMask(lg) {
  return `radial-gradient(ellipse ${lg.w}vw ${lg.h * 1.15}vh at ${lg.x}% ${lg.y}%, #000 48%, rgba(0,0,0,0) 84%)`
}
// 공책 — 줄(라인)이 오른쪽(다이어리)에 오도록 좌우 반전해서 배경 레이어로
const careBgStyle = { backgroundImage: `url(${notebookBg})` }
// 손+칩 누끼 결과를 .ai-hand 배경으로 (처리 전엔 원본)
const aiHandStyle = computed(() => ({ backgroundImage: `url(${aiCutout.value})` }))

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
        <!-- 상단 흰 영역: 네비/검색 영역까지는 세 화면 모두 흰 배경 -->
        <div class="lp-top-white" aria-hidden="true"></div>
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

        <div class="lp-track" :style="{ transform: `translateX(-${currentSlide * 100}%)` }">
          <div v-for="(s, i) in slides" :key="i" class="lp-slide" :class="s.theme">
            <!-- 스와이핑 추천: q.png 로고월 배경 + 로고별 hover 발광 핫스팟 -->
            <template v-if="s.visual === 'swipe'">
              <div class="swipe-bg" :style="swipeBgStyle" aria-hidden="true"></div>
              <div class="logo-hots">
                <span
                  v-for="lg in swipeLogos"
                  :key="lg.key"
                  class="logo-hot"
                  :style="{ '--glow': lg.color }"
                >
                  <span class="logo-hit" :style="{ left: lg.x + '%', top: lg.y + '%', width: lg.w + '%', height: lg.h + '%' }"></span>
                  <span class="logo-hot-img" :style="{ backgroundImage: keyedBg, maskImage: logoMask(lg), WebkitMaskImage: logoMask(lg) }"></span>
                </span>
              </div>
            </template>
            <!-- 우리 오늘 며칠?: 공책 줄을 오른쪽에 두려 좌우 반전한 배경 레이어 -->
            <div v-else-if="s.visual === 'care'" class="care-bg" :style="careBgStyle" aria-hidden="true"></div>
            <!-- 지금 이대로 괜찮을까요?: 흐릿한 하늘색 풀배경 + 선명한 로봇팔(오른쪽) + 'AI' 글자 발광 -->
            <template v-else>
              <div class="ai-hand" :style="aiHandStyle" aria-hidden="true"></div>
              <!-- 손이 든 칩만 따로 분리(같은 배경을 칩 영역만 클립) → 그 칩이 빛남 -->
              <div class="ai-chip-wrap" aria-hidden="true">
                <div class="ai-chip" :style="aiHandStyle"></div>
              </div>
            </template>
            <div class="lp-slide-inner">
              <div class="lp-slide-text">
                <div class="lp-slide-meta">
                  <span class="lp-num">0{{ i + 1 }} / 03</span>
                  <span class="lp-label">{{ s.label }}</span>
                </div>
                <h1 class="lp-slide-title">{{ s.title }}</h1>
                <p class="lp-slide-desc">{{ s.desc }}</p>
              </div>
              <div class="lp-slide-visual">
                <div v-if="s.visual === 'care'" class="lp-vis lp-vis-care">
                  <div class="diary-note" :class="{ 'is-active': currentSlide === i }">
                    <span class="dw-line dw-date">6월 21일</span>
                    <span class="dw-line dw-head">매매일지 기록</span>
                    <span class="dw-line dw-l1">주만추 매수</span>
                    <span class="dw-line dw-l2">장기성장성 / 목표 100%</span>
                    <svg class="dw-check" viewBox="0 0 52 40" aria-hidden="true">
                      <path d="M6 22 L20 35 L46 6" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 좌우 스와이프 버튼 -->
        <button class="lp-nav lp-nav-prev" type="button" aria-label="이전 화면" @click="goPrev">‹</button>
        <button class="lp-nav lp-nav-next" type="button" aria-label="다음 화면" @click="goNext">›</button>
        <!-- 슬라이드 인디케이터 -->
        <div class="lp-dots" role="tablist" aria-label="화면 선택">
          <button
            v-for="(s, i) in slides"
            :key="i"
            type="button"
            class="lp-dot"
            :class="{ active: currentSlide === i }"
            :aria-label="`${i + 1}번 화면`"
            @click="currentSlide = i; startSlideTimer()"
          ></button>
        </div>
        <!-- 로그인 CTA: 배너 하단 그라데이션 밴드 -->
        <div class="lp-login">
          <span class="lp-login-text">나만의 주식을 만나보아요!</span>
          <button class="lp-login-btn" type="button" @click="router.push('/login')">로그인하기 →</button>
        </div>
      </section>
      <!-- 배너(다크) → 흰 콘텐츠로 자연스럽게 잇는 전환 띠 -->
      <div class="lp-fade-out" aria-hidden="true"></div>
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
  display: flex;
  min-height: 100vh;
  transition: transform 0.7s cubic-bezier(0.4, 0, 0.2, 1);
}
.lp-slide {
  flex: 0 0 100%;
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

/* 배너 배경: 라이트 모드 (밝고 선명한 브랜드 톤) */
/* 스와이핑 추천: 화이트 배경 (로고월 .swipe-bg는 그 위에 흐릿하게) */
.lp-slide.th-swipe { background: #ffffff; }
.lp-slide.th-care { background: linear-gradient(135deg, #14b88a 0%, #2f8fe0 55%, #5566e8 100%); }
.lp-slide.th-ai { background: #aec1d6; }

/* 배너 배경: 다크 모드 (깊고 차분한 톤) — care/ai는 인라인 이미지 배경이 우선 적용됨 */
html[data-theme='dark'] .lp-slide.th-swipe { background: #ffffff; }
html[data-theme='dark'] .lp-slide.th-care { background: linear-gradient(135deg, #06382b 0%, #0c3b66 55%, #181f6b 100%); }
html[data-theme='dark'] .lp-slide.th-ai { background: #aec1d6; }

/* 스와이핑 추천: 텍스트 뒤 로고를 흰 그라데이션으로 흐리게 덮어 글씨 명시성 ↑ */
.lp-slide.th-swipe::before {
  background: linear-gradient(to right, #fff 0%, rgba(255, 255, 255, 0.9) 32%, rgba(255, 255, 255, 0.35) 58%, rgba(255, 255, 255, 0) 80%);
}
/* 메인 타이틀: 주만추 브랜드와 동일한 그라디언트 컬러 */
.lp-slide.th-swipe .lp-slide-title {
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}
.lp-slide.th-swipe .lp-slide-desc { color: #4a5365; }
.lp-slide.th-swipe .lp-num { color: #8a93a6; }
.lp-slide.th-swipe .lp-label {
  background: rgba(49, 93, 255, 0.1);
  border-color: rgba(49, 93, 255, 0.25);
  color: var(--accent);
}
/* 지금 이대로 괜찮을까요?: 하늘색을 화면 전체에 균일하게 — 스크림 제거 + 텍스트는 하늘색 위에서 읽히게 어둡게 */
.lp-slide.th-ai::before { background: none; }
.lp-slide.th-ai .lp-slide-title { color: #16233f; text-shadow: none; }
.lp-slide.th-ai .lp-slide-desc { color: #2c3c5c; }
.lp-slide.th-ai .lp-num { color: #5a6a86; }
.lp-slide.th-ai .lp-label {
  background: rgba(20, 40, 90, 0.1);
  border-color: rgba(20, 40, 90, 0.22);
  color: #20407a;
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
.lp-search-overlay .home-search {
  width: min(1480px, 100%);
  pointer-events: auto;
  /* 검색박스: 흰 배경 + 검정 글씨 (테마 무관) */
  background: #fff;
  border: 1px solid #e3e8f0;
  box-shadow: 0 6px 22px rgba(20, 30, 60, 0.1);
}
/* 검색 박스 텍스트: 주만추 브랜드처럼 그라디언트 컬러로, 확실하게 보이게 */
.lp-search-overlay .home-search .popular-label,
.lp-search-overlay .home-search .popular-kw,
.lp-search-overlay .home-search .search-input {
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  font-weight: 800;
}
.lp-search-overlay .home-search .popular-kw:not(:last-child)::after { -webkit-text-fill-color: #b9b1e6; }
/* 입력 캐럿/플레이스홀더도 또렷한 브랜드 톤 */
.lp-search-overlay .home-search .search-input { caret-color: var(--accent); }
.lp-search-overlay .home-search .search-input::placeholder { -webkit-text-fill-color: #7b6fe0; color: #7b6fe0; opacity: 1; }
.lp-search-overlay .home-search .search-icon { color: var(--accent); }

/* 상단 흰 영역 — 세 화면 모두 네비/검색 영역까지는 흰 배경 */
.lp-top-white {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 150px;
  z-index: 4;
  pointer-events: none;
  background: linear-gradient(to bottom, #fff 0%, #fff 80%, rgba(255, 255, 255, 0) 100%);
}
/* 텍스트 가독성 스크림 — 왼쪽(텍스트)은 어둡게, 오른쪽(비주얼/이미지)은 투명하게 */
.lp-slide::before {
  content: ''; position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: linear-gradient(to right, rgba(8,12,28,0.82) 0%, rgba(8,12,28,0.45) 42%, rgba(8,12,28,0.05) 70%, transparent 100%);
}
.lp-slide-inner {
  position: relative;
  z-index: 3;
  /* 내부에 인터랙션 요소가 없어 포인터를 통과시켜 뒤쪽 로고 클라우드 hover를 모두 허용 */
  pointer-events: none;
  width: min(1480px, 100%);
  margin: 0 auto;
  padding: 0 60px;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 40px;
  align-items: center;
}
.lp-slide-text { color: #fff; }
.lp-slide-meta { display: flex; align-items: center; gap: 12px; }
.lp-num { font-size: 13px; font-weight: 900; color: rgba(255,255,255,0.6); letter-spacing: 0.1em; }
.lp-label {
  padding: 5px 14px; border-radius: 999px;
  background: rgba(255,255,255,0.16); border: 1px solid rgba(255,255,255,0.24);
  color: #fff; font-size: 13px; font-weight: 900;
}
.lp-slide-title { margin: 20px 0 16px; font-size: clamp(38px, 6vw, 76px); font-weight: 900; line-height: 1.05; letter-spacing: -2px; color: #fff; white-space: pre-line; }
.lp-slide-desc { margin: 0; max-width: 480px; font-size: 16px; font-weight: 600; line-height: 1.7; color: rgba(255,255,255,0.82); word-break: keep-all; }
.lp-slide-visual { display: flex; align-items: center; justify-content: center; }
.lp-vis { position: relative; width: 280px; height: 300px; display: flex; align-items: center; justify-content: center; }

/* 비주얼: 스와이핑 추천 q.png 로고월 — 화이트 위에 흐릿하게 (채도/블러/투명도) */
.swipe-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.72;
  filter: saturate(1.35);
  pointer-events: none;
}
/* 로고별 hover — 마우스 올리면 브랜드 색으로 로고 전체가 부드럽게(사각형 경계 없이) 발광 */
.logo-hots { position: absolute; inset: 0; z-index: 2; }
/* wrap: 전체 슬라이드. drop-shadow를 여기(마스크 안 됨)에 줘 로고 외형을 따라 글로우가 바깥까지 퍼짐 */
.logo-hot { position: absolute; inset: 0; pointer-events: none; }
/* hit: 로고 위 투명 hover 영역 */
.logo-hit {
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: auto;
  cursor: pointer;
}
/* inner: 키잉된 로고월을 .swipe-bg와 동일 cover/center로, 해당 로고를 부드러운 타원 마스크로 표시 */
.logo-hot-img {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.22s ease, filter 0.22s ease;
}
.logo-hot:has(.logo-hit:hover) .logo-hot-img {
  opacity: 1;
  filter: brightness(1.18) saturate(1.2);
}
.logo-hot:has(.logo-hit:hover) {
  filter: drop-shadow(0 0 6px var(--glow)) drop-shadow(0 0 16px var(--glow))
    drop-shadow(0 0 32px var(--glow));
}

/* 비주얼: 우리 오늘 며칠? — 공책 배경(줄을 오른쪽에 두려 좌우 반전) */
.care-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  transform: scaleX(-1);
  pointer-events: none;
}

/* 비주얼: 우리 오늘 며칠? — 공책 줄에 맞춰 손글씨로 써지는 매매일지 */
.lp-vis-care { width: auto; height: auto; align-items: flex-start; justify-content: flex-start; }
.diary-note {
  display: flex;
  flex-direction: column;
  gap: 0;
  /* 공책 줄 기울기에 맞춤 (조정 가능) */
  transform: rotate(2deg) translateY(-6px);
  font-family: 'Nanum Pen Script', 'Gaegu', 'Segoe Script', cursive;
}
.dw-line {
  display: flex;
  align-items: flex-end;
  /* 공책 줄 간격에 맞춰 한 줄=한 칸, 글자는 줄 위에 얹힘 (조정 가능) */
  height: 58px;
  padding-bottom: 2px;
  white-space: nowrap;
  /* 기본은 왼→오로 숨김 → 활성 시 써지는 애니메이션으로 드러남 */
  clip-path: inset(0 100% 0 0);
}
.diary-note.is-active .dw-line { animation: writeIn 0.95s steps(26, end) forwards; }
.diary-note.is-active .dw-date { animation-delay: 0.25s; }
.diary-note.is-active .dw-head { animation-delay: 1.15s; }
.diary-note.is-active .dw-l1 { animation-delay: 2s; }
.diary-note.is-active .dw-l2 { animation-delay: 2.85s; }
.dw-date { font-size: 42px; font-weight: 700; color: #c0392b; }
.dw-head { font-size: 40px; font-weight: 700; color: #1f2d6e; }
.dw-l1 { font-size: 40px; font-weight: 700; color: #15803d; }
.dw-l2 { font-size: 37px; font-weight: 700; color: #2436a8; }
/* 매매일지 체크표시 — 글이 다 써진 뒤 손으로 그어지듯 그려짐 */
.dw-check { position: absolute; right: -46px; bottom: 4px; width: 50px; height: 38px; overflow: visible; }
.dw-check path {
  fill: none;
  stroke: #16a34a;
  stroke-width: 6;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 66;
  stroke-dashoffset: 66;
}
.diary-note.is-active .dw-check path { animation: checkDraw 0.5s ease-out 3.8s forwards; }
@keyframes checkDraw { to { stroke-dashoffset: 0; } }
@keyframes writeIn { to { clip-path: inset(0 0 0 0); } }
@media (prefers-reduced-motion: reduce) {
  .diary-note .dw-line { clip-path: inset(0 0 0 0); }
  .diary-note.is-active .dw-line { animation: none; }
}

/* 비주얼: 지금 이대로 괜찮을까요? */
/* 손+칩 누끼(투명 배경) — 단일 하늘색(th-ai) 위에 올려 화면 전체가 하나의 하늘색으로 통일 */
.ai-hand {
  position: absolute;
  inset: 0;
  z-index: 1;
  background-size: auto 100%;
  background-position: right center;
  background-repeat: no-repeat;
}
/* 칩만 따로 분리해 발광 — 손과 동일 배경을 칩 영역만 클립해 겹친 뒤, 그 칩에 밝기/글로우 펄스 */
.ai-chip-wrap {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  animation: aiChipGlow 1.7s ease-in-out infinite;
}
.ai-chip {
  position: absolute;
  inset: 0;
  background-size: auto 100%;
  background-position: right center;
  background-repeat: no-repeat;
  /* 칩 영역만 보이게: inset(top right bottom left) — 위치/크기 조정 가능 */
  clip-path: inset(30% 36% 50% 50% round 14px);
  -webkit-clip-path: inset(30% 36% 50% 50% round 14px);
}
@keyframes aiChipGlow {
  0%, 100% {
    filter: brightness(1) saturate(1) drop-shadow(0 0 2px rgba(95, 227, 255, 0.35));
  }
  50% {
    filter: brightness(1.4) saturate(1.6)
      drop-shadow(0 0 12px #7ef0ff) drop-shadow(0 0 26px rgba(95, 227, 255, 0.85));
  }
}

/* ===== 좌우 스와이프 버튼 ===== */
.lp-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 6;
  width: 52px;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 50%;
  background: rgba(12, 16, 34, 0.42);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  color: #fff;
  font-size: 30px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
  transition: background 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}
.lp-nav-prev { left: 24px; }
.lp-nav-next { right: 24px; }
.lp-nav:hover {
  background: rgba(49, 93, 255, 0.55);
  transform: translateY(-50%) scale(1.08);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}
.lp-nav:active { transform: translateY(-50%) scale(0.96); }

/* ===== 슬라이드 인디케이터 ===== */
.lp-dots {
  position: absolute;
  left: 50%;
  bottom: 132px;
  transform: translateX(-50%);
  z-index: 6;
  display: flex;
  gap: 10px;
}
.lp-dot {
  width: 10px;
  height: 10px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: width 0.25s ease, background 0.25s ease;
}
.lp-dot.active { width: 28px; background: #fff; }

/* ===== 로그인 유도 CTA (배너 하단 그라데이션 밴드) ===== */
.lp-login {
  position: absolute; left: 0; right: 0; bottom: 0; z-index: 3;
  display: flex; align-items: flex-end; justify-content: center; gap: 20px; flex-wrap: wrap;
  /* 위로 길고 부드럽게 어두워져 슬라이드와 경계를 모호하게, 아래로 갈수록 진하게(텍스트 가독성), CTA는 아래쪽 배치 */
  padding: 170px 24px 44px;
  background: linear-gradient(to bottom,
    transparent 0%,
    rgba(8, 10, 26, 0.32) 40%,
    rgba(8, 10, 26, 0.7) 72%,
    rgba(8, 10, 26, 0.92) 100%);
}
.lp-login-text {
  font-size: clamp(16px, 2.2vw, 22px);
  font-weight: 900;
  color: #fff;
  letter-spacing: -0.3px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.6);
}
.lp-login-btn {
  height: 48px; padding: 0 28px; border: 0; border-radius: 999px;
  background: linear-gradient(135deg, #315dff, #7d4ee8 60%, #ff3d8b);
  color: #fff; font-size: 15px; font-weight: 900; cursor: pointer;
  box-shadow: 0 12px 30px rgba(49,93,255,0.45);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.lp-login-btn:hover { transform: translateY(-2px); box-shadow: 0 16px 38px rgba(49,93,255,0.55); }

/* 배너(다크) → 흰 콘텐츠 전환 띠 — 풀블리드, 배너 하단에 바로 붙여 다크에서 흰색으로 자연스럽게 */
.lp-fade-out {
  width: 100vw;
  max-width: 100vw;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  margin-top: -18px; /* .home-page flex gap(18px) 상쇄 → 배너 하단에 밀착 */
  height: 160px;
  pointer-events: none;
  background: linear-gradient(to bottom,
    rgb(20, 22, 37) 0%,
    rgba(20, 22, 37, 0.5) 34%,
    rgba(255, 255, 255, 0) 100%);
}

@media (max-width: 800px) {
  .lp-slide-inner { grid-template-columns: 1fr; padding: 0 22px; text-align: center; justify-items: center; gap: 22px; }
  /* 번호(01/03) 위, 라벨(스와이핑 추천) 아래로 — 가운데 정렬 */
  .lp-slide-meta { flex-direction: column; gap: 8px; }
  .lp-slide-title { margin: 12px 0 12px; font-size: clamp(32px, 8vw, 52px); letter-spacing: -1px; }
  .lp-slide-desc { margin: 0 auto; font-size: 15px; }
  .lp-vis { width: 240px; height: 250px; }
  /* 모바일은 가운데 정렬이라 스크림을 전체적으로 균일하게 어둡게 */
  .lp-slide::before { background: rgba(8, 12, 28, 0.6); }
  .lp-nav { width: 42px; height: 42px; font-size: 24px; }
  .lp-nav-prev { left: 10px; }
  .lp-nav-next { right: 10px; }
  .lp-dots { bottom: 118px; }
}

@media (prefers-reduced-motion: reduce) {
  .lp-track { transition: none; }
  .ai-chip-wrap { animation: none !important; }
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
