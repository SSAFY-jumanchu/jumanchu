<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import SparklineChart from '../components/SparklineChart.vue'

const router = useRouter()

// ===== 필터 상태 =====
const marketFilter = ref('all')   // all | domestic | overseas
const sortPeriod = ref('rt')      // rt | 1d | 1w | 1m | 3m | 6m | 1y
const selectedStock = ref(null)

// ===== 종목 데이터 (초기값은 와이어프레임 목업 — API 응답이 오면 교체) =====
const stocks = ref([
  {
    rank: 1, code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '전기·전자',
    price: 2031000, change: -239200, rate: -11.61,
    volume: '748억', buyRatio: 38, sellRatio: 62,
    aiNote: '브로드컴 실적 쇼크',
    color: '#FF3B5C',
    sparkline: [90,88,86,84,82,79,76,72,68,64,60,56],
    chartPoints: [100,98,97,99,96,94,91,88,84,80,75,70,65,60,56,52,50,48,46,44],
    aiReason: '브로드컴 실적 쇼크로 SK하이닉스 -11.10% 하락',
    summary: ['외국인과 기관이 많이 판 Top 10 종목이에요.', '외국인 투자자가 20일 연속 팔고 있어요. (주가 -9.9%)'],
    community: [
      { user: 'TECL미친놈', time: '6분', content: '신입인에요 실부탁해요!' },
      { type: 'alert', content: 'SK하이닉스 1주 2,032,000원 · 오늘 16:07' },
    ],
  },
  {
    rank: 2, code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자',
    price: 325500, change: -26000, rate: -7.39,
    volume: '467억', buyRatio: 41, sellRatio: 59,
    aiNote: '브로드컴 실적 쇼크',
    color: '#1428A0',
    sparkline: [85,83,82,80,78,75,72,70,68,65,63,61],
    chartPoints: [100,99,97,96,94,92,90,88,86,83,81,78,76,73,71,69,67,65,63,61],
    aiReason: '브로드컴 쇼크 여파로 반도체 전반 하락세',
    summary: ['기관이 이틀 연속 순매도 중이에요.', '52주 최저가 근접 중이에요.'],
    community: [
      { user: '장기투자자', time: '12분', content: '지금 담기 좋은 가격인가요?' },
    ],
  },
  {
    rank: 3, code: '009150', name: '삼성전기', market: 'KOSPI', sector: '전기·전자',
    price: 1704000, change: -11800, rate: -0.69,
    volume: '137억', buyRatio: 52, sellRatio: 48,
    aiNote: '외국인 대규모 순매도',
    color: '#1428A0',
    sparkline: [72,73,71,72,70,71,69,70,71,70,69,71],
    chartPoints: [100,101,100,99,100,99,98,99,99,100,99,98,99,100,99,98,99,100,99,99],
    aiReason: '외국인 순매도 지속으로 소폭 하락',
    summary: ['기관은 매수 중이에요.', '거래량이 평소보다 낮아요.'],
    community: [],
  },
  {
    rank: 4, code: '066570', name: 'LG전자', market: 'KOSPI', sector: '전기·전자',
    price: 293500, change: -34200, rate: -10.51,
    volume: '93억', buyRatio: 34, sellRatio: 66,
    aiNote: '아이폰 소진',
    color: '#FF3B5C',
    sparkline: [88,86,83,80,77,74,72,70,67,65,63,61],
    chartPoints: [100,98,96,94,91,89,86,84,82,79,77,75,73,71,69,67,65,63,61,59],
    aiReason: '아이폰 관련 부품 수요 감소 우려',
    summary: ['외국인이 대량 매도 중이에요.', '주가가 3개월 저점 근처예요.'],
    community: [],
  },
  {
    rank: 5, code: '215380', name: '로보스타', market: 'KOSPI', sector: '기계·장비',
    price: 140300, change: +1100, rate: +0.79,
    volume: '75억', buyRatio: 57, sellRatio: 43,
    aiNote: '아이벤트 소진',
    color: '#06C',
    sparkline: [60,61,62,61,63,62,63,64,63,64,65,64],
    chartPoints: [100,101,102,101,102,103,102,103,104,103,104,105,104,105,104,105,106,105,106,105],
    aiReason: '로봇 수요 증가 기대감으로 소폭 상승',
    summary: ['개인 투자자 중심의 매수세예요.', '이틀 연속 상승 중이에요.'],
    community: [],
  },
  {
    rank: 6, code: '005380', name: '현대차', market: 'KOSPI', sector: '운송장비·부품',
    price: 675000, change: -24900, rate: -3.57,
    volume: '58억', buyRatio: 57, sellRatio: 43,
    aiNote: '외국인 순매수 확대',
    color: '#FF3B5C',
    sparkline: [80,79,77,76,75,74,73,72,71,70,69,68],
    chartPoints: [100,99,98,97,96,95,94,93,92,91,90,89,88,87,86,85,84,83,82,81],
    aiReason: '미국 관세 우려 지속으로 하락',
    summary: ['외국인은 오히려 사고 있어요.', '배당 기대감이 있어요.'],
    community: [],
  },
  {
    rank: 7, code: 'SOXL', name: 'SOXL', market: 'NASDAQ', sector: '전기·전자',
    price: 365778, change: -35900, rate: -8.91,
    volume: '40억', buyRatio: 43, sellRatio: 57,
    aiNote: '브로드컴 실적 쇼크',
    color: '#FF3B5C',
    sparkline: [85,82,79,76,73,70,68,65,63,61,59,57],
    chartPoints: [100,98,95,92,89,87,84,82,79,77,75,73,71,69,67,65,63,62,60,58],
    aiReason: 'SOX 지수 하락으로 3배 레버리지 ETF 급락',
    summary: ['레버리지 ETF 특성상 하락폭이 커요.', '해외 반도체 섹터 전반 약세예요.'],
    community: [],
  },
  {
    rank: 8, code: '035420', name: 'NAVER', market: 'KOSPI', sector: 'IT 서비스',
    price: 248500, change: -19100, rate: -7.10,
    volume: '37억', buyRatio: 47, sellRatio: 53,
    aiNote: '아이벤트 소진',
    color: '#FF3B5C',
    sparkline: [82,80,78,76,74,72,70,68,66,64,62,60],
    chartPoints: [100,98,96,94,92,90,88,87,85,83,81,80,78,76,74,73,71,70,68,66],
    aiReason: 'AI 경쟁 심화 우려와 광고 매출 둔화 우려',
    summary: ['기관과 외국인 동반 매도 중이에요.', '1개월 최저가예요.'],
    community: [],
  },
  {
    rank: 9, code: '454910', name: '두산로보틱스', market: 'KOSPI', sector: '기계·장비',
    price: 133800, change: -23600, rate: -15.26,
    volume: '31억', buyRatio: 40, sellRatio: 60,
    aiNote: '아이벤트 소진',
    color: '#FF3B5C',
    sparkline: [92,89,85,82,78,74,71,67,63,60,57,54],
    chartPoints: [100,97,94,91,88,85,82,79,76,73,70,67,64,62,59,57,55,53,51,49],
    aiReason: '기대감 소진으로 급격한 조정',
    summary: ['단기 급등 이후 차익 실현 매물이 나왔어요.', '거래량이 평소 대비 3배 이상이에요.'],
    community: [],
  },
  {
    rank: 10, code: '085620', name: '미래에셋생명', market: 'KOSPI', sector: '금융',
    price: 21200, change: +1800, rate: +9.22,
    volume: '28억', buyRatio: 36, sellRatio: 64,
    aiNote: '기관 순매수 지속',
    color: '#06C',
    sparkline: [55,57,59,61,63,65,67,68,70,72,74,75],
    chartPoints: [100,102,104,106,108,110,112,114,115,117,119,121,122,124,125,127,128,129,130,131],
    aiReason: '보험사 실적 개선 기대감으로 급등',
    summary: ['기관이 3일 연속 매수 중이에요.', '배당 수익률이 높아요.'],
    community: [],
  },
  {
    rank: 11, code: 'SOXS', name: 'SOXS', market: 'NASDAQ', sector: '전기·전자',
    price: 8682, change: +740, rate: +9.23,
    volume: '27억', buyRatio: 33, sellRatio: 67,
    aiNote: '브로드컴 실적 쇼크',
    color: '#06C',
    sparkline: [50,53,56,59,62,64,67,70,73,76,78,80],
    chartPoints: [100,103,106,109,112,115,118,121,124,127,130,132,135,137,139,141,143,145,146,148],
    aiReason: '반도체 인버스 ETF, SOX 하락으로 수익',
    summary: ['반도체 하락 시 수익 나는 ETF예요.', '오늘 거래량이 급증했어요.'],
    community: [],
  },
  {
    rank: 12, code: '032640', name: 'LG이노텍', market: 'KOSPI', sector: '전기·전자',
    price: 1100000, change: -72000, rate: -6.22,
    volume: '27억', buyRatio: 66, sellRatio: 34,
    aiNote: '이벤트 기대감 소진',
    color: '#FF3B5C',
    sparkline: [84,82,80,78,76,74,72,70,68,66,64,63],
    chartPoints: [100,98,96,94,92,90,88,86,85,83,81,80,78,76,75,73,72,70,69,67],
    aiReason: '아이폰17 부품 수요 기대감 소진',
    summary: ['외국인 매도세가 강해요.', '애플 관련주 전반 약세예요.'],
    community: [],
  },
  {
    rank: 13, code: 'MUU', name: 'MUU', market: 'NASDAQ', sector: '전기·전자',
    price: 1232051, change: -145200, rate: -10.59,
    volume: '22억', buyRatio: 40, sellRatio: 60,
    aiNote: '브로드컴 실적 쇼크',
    color: '#FF3B5C',
    sparkline: [88,85,82,79,76,73,70,67,64,61,59,57],
    chartPoints: [100,97,94,91,88,85,82,79,76,73,71,68,65,63,60,58,56,54,52,50],
    aiReason: '반도체 관련 ETF 전반 하락',
    summary: ['반도체 섹터 약세가 ETF에 반영됐어요.', '단기 낙폭이 커요.'],
    community: [],
  },
  {
    rank: 14, code: '012330', name: '현대모비스', market: 'KOSPI', sector: '운송장비·부품',
    price: 673000, change: -74800, rate: -10.02,
    volume: '19억', buyRatio: 52, sellRatio: 48,
    aiNote: '브로드컴 실적 쇼크',
    color: '#FF3B5C',
    sparkline: [86,83,80,77,74,72,69,67,65,63,61,60],
    chartPoints: [100,97,94,91,88,86,83,81,78,76,74,72,70,68,66,64,62,61,59,57],
    aiReason: '전기차 수요 둔화 우려로 하락',
    summary: ['외국인 순매도가 지속되고 있어요.', '전기차 관련주 동반 약세예요.'],
    community: [],
  },
  {
    rank: 15, code: '034220', name: 'LG디스플레이', market: 'KOSPI', sector: '전기·전자',
    price: 112500, change: -13900, rate: -10.99,
    volume: '19억', buyRatio: 47, sellRatio: 53,
    aiNote: '기대감 소진',
    color: '#FF3B5C',
    sparkline: [86,83,80,77,74,72,70,68,65,62,60,58],
    chartPoints: [100,97,94,91,88,86,83,81,78,76,74,72,70,68,65,63,61,59,57,55],
    aiReason: 'OLED 패널 수요 회복 기대감 소진',
    summary: ['기관 매도세가 이어지고 있어요.', '디스플레이 업황 개선이 더딘 상황이에요.'],
    community: [],
  },
])

// ===== 스와이프로 관심종목 만들기 =====
const SWIPE_GOAL = 10
const swipeIndex = ref(0)
const swipedCount = ref(0)
const savedStocks = ref([]) // { ...stock, action: 'like' | 'save' }
const swipeDone = computed(() => swipedCount.value >= SWIPE_GOAL)

// 기존 종목 데이터 → 메인 페이지 궁합 카드 형태로 파생 (궁합점수·Stock DNA·관심 수)
function deriveCard(s) {
  if (!s) return s
  const growth = Math.min(95, Math.round(s.buyRatio + 25))
  const volatility = Math.min(95, 40 + Math.round(Math.abs(s.rate) * 4))
  const value = Math.max(30, 70 - Math.round(Math.abs(s.rate) * 2))
  const stability = Math.max(35, Math.min(90, 120 - volatility))
  return {
    ...s,
    score: Math.min(98, Math.max(62, Math.round(60 + s.buyRatio * 0.45))),
    interest: 200 + Math.round(s.buyRatio * 9),
    dna: [
      { label: '변동성', value: volatility },
      { label: '성장', value: growth },
      { label: '가치', value: value },
      { label: '안정성', value: stability },
    ],
  }
}
const currentCard = computed(() => deriveCard(stocks.value[swipeIndex.value % stocks.value.length]))
const dnaPolygon = computed(() => {
  const d = currentCard.value?.dna
  if (!d) return ''
  const cx = 60, cy = 60, R = 46
  return [
    `${cx},${cy - (R * d[0].value) / 100}`,
    `${cx + (R * d[1].value) / 100},${cy}`,
    `${cx},${cy + (R * d[2].value) / 100}`,
    `${cx - (R * d[3].value) / 100},${cy}`,
  ].join(' ')
})

function cardGradient(s) {
  if (!s) return ''
  return s.rate >= 0
    ? 'linear-gradient(135deg, #2563eb 0%, #7c3aed 55%, #06b6d4 100%)'
    : 'linear-gradient(135deg, #db2777 0%, #7c3aed 55%, #2563eb 100%)'
}

const swipeCardEl = ref(null)
const feedbackType = ref(null)
const feedbackOpacity = ref(0)
let dragging = false
let animating = false
let sx = 0, sy = 0, dx = 0, dy = 0
const SWIPE_EXIT = 460

function updateSwipeFeedback() {
  if (dy < -50 && Math.abs(dy) > Math.abs(dx)) {
    feedbackType.value = 'save'; feedbackOpacity.value = Math.min(Math.abs(dy) / 120, 1)
  } else if (dx > 40) {
    feedbackType.value = 'like'; feedbackOpacity.value = Math.min(dx / 120, 1)
  } else if (dx < -40) {
    feedbackType.value = 'pass'; feedbackOpacity.value = Math.min(Math.abs(dx) / 120, 1)
  } else {
    feedbackOpacity.value = 0
  }
}
function enterSwipeCard() {
  const el = swipeCardEl.value
  if (!el) return
  feedbackOpacity.value = 0
  el.style.transition = 'none'
  el.style.transform = 'translate3d(0,0,0) scale(.94)'
  el.style.opacity = '0'
  requestAnimationFrame(() => {
    el.style.transition = 'transform .42s cubic-bezier(.2,.8,.2,1), opacity .3s ease'
    el.style.transform = 'translate3d(0,0,0) scale(1)'
    el.style.opacity = '1'
  })
}
function swipeAction(action) {
  const el = swipeCardEl.value
  if (animating || !el || swipeDone.value) return
  animating = true
  const card = currentCard.value
  if (action === 'like') savedStocks.value.push({ ...card, action: 'like' })
  else if (action === 'save') savedStocks.value.push({ ...card, action: 'save' })
  feedbackType.value = action === 'save' ? 'save' : action === 'like' ? 'like' : 'pass'
  feedbackOpacity.value = 1
  el.style.transition = `transform ${SWIPE_EXIT}ms cubic-bezier(.4,0,.2,1), opacity ${SWIPE_EXIT}ms ease`
  if (action === 'save') {
    el.style.transform = 'translate3d(0,-220px,0) scale(.9)'
  } else {
    const r = action === 'like'
    el.style.transform = `translate3d(${r ? 460 : -460}px,40px,0) rotate(${r ? 16 : -16}deg)`
  }
  el.style.opacity = '0'
  setTimeout(() => {
    swipedCount.value += 1
    swipeIndex.value += 1
    animating = false
    if (!swipeDone.value) requestAnimationFrame(enterSwipeCard)
  }, SWIPE_EXIT)
}
function onSwipeDown(e) {
  if (animating) return
  dragging = true; sx = e.clientX; sy = e.clientY; dx = 0; dy = 0
  swipeCardEl.value.style.transition = 'none'
  swipeCardEl.value.setPointerCapture?.(e.pointerId)
}
function onSwipeMove(e) {
  if (!dragging) return
  dx = e.clientX - sx; dy = e.clientY - sy
  const rot = dx / 20
  const sc = Math.max(0.96, 1 - (Math.abs(dx) + Math.abs(dy)) / 2400)
  swipeCardEl.value.style.transform = `translate3d(${dx}px,${dy}px,0) rotate(${rot}deg) scale(${sc})`
  updateSwipeFeedback()
}
function onSwipeUp() {
  if (!dragging) return
  dragging = false
  if (dy < -110 && Math.abs(dy) > Math.abs(dx)) return swipeAction('save')
  if (dx > 110) return swipeAction('like')
  if (dx < -110) return swipeAction('pass')
  const el = swipeCardEl.value
  el.style.transition = 'transform .35s cubic-bezier(.2,.8,.2,1)'
  el.style.transform = 'translate3d(0,0,0) rotate(0deg) scale(1)'
  feedbackOpacity.value = 0
}
function resetSwipe() {
  swipeIndex.value = 0; swipedCount.value = 0; savedStocks.value = []
}

// ===== 결과 목록 필터링 (관심·저장한 종목) =====
const filteredStocks = computed(() => {
  let list = savedStocks.value
  if (marketFilter.value === 'domestic') list = list.filter(s => s.market === 'KOSPI' || s.market === 'KOSDAQ')
  if (marketFilter.value === 'overseas') list = list.filter(s => s.market === 'NASDAQ' || s.market === 'NYSE')
  return list
})

// ===== 유틸 =====
function fmtPrice(v, market) {
  const isKrw = market === 'KOSPI' || market === 'KOSDAQ'
  return isKrw ? v.toLocaleString('ko-KR') + '원' : '$' + (v / 1380).toLocaleString('en-US', { maximumFractionDigits: 2 })
}

function fmtChange(v, market) {
  const isKrw = market === 'KOSPI' || market === 'KOSDAQ'
  const prefix = v >= 0 ? '+' : ''
  return isKrw ? prefix + v.toLocaleString('ko-KR') + '원' : prefix + '$' + Math.abs(v / 1380).toFixed(2)
}

// ===== 차트 포인트 → SVG path =====
function buildChartPath(pts, w, h) {
  const min = Math.min(...pts), max = Math.max(...pts), range = max - min || 1
  const xs = pts.map((_, i) => (i / (pts.length - 1)) * w)
  const ys = pts.map(v => h - 8 - ((v - min) / range) * (h - 20))
  const line = xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${ys[i].toFixed(1)}`).join(' ')
  const area = line + ` L${w},${h} L0,${h} Z`
  return { line, area, lastY: ys[ys.length - 1] }
}

function selectStock(s) {
  selectedStock.value = selectedStock.value?.code === s.code ? null : s
}

const marketFilters = [
  { key: 'all', label: '전체' },
  { key: 'domestic', label: '국내' },
  { key: 'overseas', label: '해외' },
]

const periods = [
  { key: 'rt', label: '실시간' },
  { key: '1d', label: '1일' },
  { key: '1w', label: '1주일' },
  { key: '1m', label: '1개월' },
  { key: '3m', label: '3개월' },
  { key: '6m', label: '6개월' },
  { key: '1y', label: '1년' },
]

// ===== 뷰 토글: 인기 종목 / 선호 종목 =====
const viewMode = ref('popular') // 'popular' | 'preference'

// ===== 인기 종목 (실시간 랭킹) =====
const popularSort = ref('value')
const popularSortOptions = [
  { key: 'value', label: '거래대금' },
  { key: 'volume', label: '거래량' },
  { key: 'up', label: '급상승' },
  { key: 'down', label: '급하락' },
]
const liked = reactive({})
function toggleLike(code) { liked[code] = !liked[code] }
const nowLabel = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false })

const popularStocks = computed(() => {
  let list = stocks.value.filter((s) => {
    if (marketFilter.value === 'domestic') return s.market === 'KOSPI' || s.market === 'KOSDAQ'
    if (marketFilter.value === 'overseas') return s.market === 'NASDAQ' || s.market === 'NYSE'
    return true
  })
  if (popularSort.value === 'up') list = [...list].sort((a, b) => b.rate - a.rate)
  else if (popularSort.value === 'down') list = [...list].sort((a, b) => a.rate - b.rate)
  return list
})
</script>

<template>
  <div class="stocks-page">

    <!-- ===== 상단 헤더 ===== -->
    <header class="stocks-header panel">
      <div>
        <p class="eyebrow">실시간 시장</p>
        <h1>주식 조회</h1>
      </div>
      <div class="header-pills">
        <span class="market-pill open">
          <span class="mdot open"></span>국내 정규장 <em>09:00 ~ 15:30</em>
        </span>
        <span class="market-pill">
          <span class="mdot open"></span>해외 프리마켓 <em>17:00 ~ 22:30</em>
        </span>
      </div>
    </header>

    <div class="stocks-layout">

      <!-- ===== 왼쪽: 종목 리스트 ===== -->
      <section class="panel stocks-list-panel" aria-label="종목 목록">

        <!-- ===== 뷰 토글 (리퀴드 글래스 슬라이드) ===== -->
        <div class="view-toggle" :class="viewMode">
          <span class="view-toggle-thumb" aria-hidden="true"></span>
          <button type="button" :class="{ on: viewMode === 'popular' }" @click="viewMode = 'popular'">인기 종목</button>
          <button type="button" :class="{ on: viewMode === 'preference' }" @click="viewMode = 'preference'">선호 종목</button>
        </div>

        <!-- ===== 인기 종목 (실시간 랭킹) ===== -->
        <template v-if="viewMode === 'popular'">
          <div class="pop-filter">
            <div class="segmented">
              <button
                v-for="f in marketFilters"
                :key="f.key"
                type="button"
                :class="{ 'is-selected': marketFilter === f.key }"
                @click="marketFilter = f.key"
              >{{ f.label }}</button>
            </div>
            <div class="pop-sort">
              <button
                v-for="o in popularSortOptions"
                :key="o.key"
                type="button"
                :class="{ 'is-selected': popularSort === o.key }"
                @click="popularSort = o.key"
              >{{ o.label }}</button>
            </div>
            <div class="period-tabs">
              <button
                v-for="p in periods"
                :key="p.key"
                type="button"
                :class="{ 'is-selected': sortPeriod === p.key }"
                @click="sortPeriod = p.key"
              >{{ p.label }}</button>
            </div>
          </div>

          <p class="pop-caption">순위 · 오늘 {{ nowLabel }} 기준</p>

          <div class="pop-table">
            <div class="pop-row pop-head">
              <span class="pop-rank-h">순위</span>
              <span>종목</span>
              <span class="pop-num">현재가</span>
              <span class="pop-num">등락률</span>
              <span class="pop-num">거래대금</span>
              <span class="pop-ratio-h">거래 비율</span>
              <span class="pop-ai-h">AI 요약</span>
            </div>

            <div
              v-for="(s, i) in popularStocks"
              :key="s.code"
              class="pop-row"
              :class="{ active: selectedStock?.code === s.code }"
              @click="selectStock(s)"
            >
              <span class="pop-rank">
                <button class="pop-heart" :class="{ on: liked[s.code] }" @click.stop="toggleLike(s.code)">
                  {{ liked[s.code] ? '♥' : '♡' }}
                </button>
                <span class="pop-rank-num">{{ i + 1 }}</span>
              </span>
              <div class="pop-name">
                <span class="pop-logo" :style="{ background: s.color }">{{ s.name.slice(0, 1) }}</span>
                <div class="pop-name-info">
                  <strong>{{ s.name }}</strong>
                  <span>{{ s.market }} · {{ s.sector }}</span>
                </div>
              </div>
              <span class="pop-num pop-price">{{ s.price.toLocaleString() }}원</span>
              <span class="pop-num pop-rate" :class="s.rate >= 0 ? 'up' : 'down'">
                {{ s.rate >= 0 ? '+' : '' }}{{ s.rate.toFixed(2) }}%
              </span>
              <span class="pop-num pop-vol">{{ s.volume }}</span>
              <div class="pop-ratio">
                <div class="pop-ratio-bar">
                  <span class="buy" :style="{ width: s.buyRatio + '%' }"></span>
                  <span class="sell" :style="{ width: s.sellRatio + '%' }"></span>
                </div>
                <div class="pop-ratio-nums">
                  <span class="b">{{ s.buyRatio }}</span>
                  <span class="s">{{ s.sellRatio }}</span>
                </div>
              </div>
              <span class="pop-ai">{{ s.aiNote }}</span>
            </div>
          </div>
        </template>

        <!-- ===== 선호 종목 (스와이프 → 관심·저장) ===== -->
        <template v-else>
        <!-- ===== 스와이프 모드 (관심종목 고르기) ===== -->
        <template v-if="!swipeDone">
          <div class="sv-match-header">
            <h2 class="sv-match-title">오늘의 궁합 추천 💝</h2>
            <p class="sv-match-sub">당신의 투자 성향과 잘 맞는 종목이에요. 넘기면서 관심 종목을 골라보세요.</p>
            <span class="sv-match-count">추천 {{ swipedCount + 1 }} / {{ SWIPE_GOAL }}</span>
          </div>

          <div class="sv-deck">
            <article
              ref="swipeCardEl"
              class="sv-card"
              :style="{ background: cardGradient(currentCard) }"
              @pointerdown="onSwipeDown"
              @pointermove="onSwipeMove"
              @pointerup="onSwipeUp"
            >
              <div class="sv-feedback" :class="feedbackType" :style="{ opacity: feedbackOpacity }">
                <span v-if="feedbackType === 'like'">❤️ 관심</span>
                <span v-else-if="feedbackType === 'pass'">✕ 관심없음</span>
                <span v-else-if="feedbackType === 'save'">⭐ 저장</span>
              </div>

              <div class="mc-top">
                <span class="mc-badge">{{ currentCard.market }} · {{ currentCard.sector }}</span>
                <div class="mc-score">{{ currentCard.score }}<span>궁합점수</span></div>
              </div>

              <div class="mc-name-block">
                <h3 class="mc-name">{{ currentCard.name }}</h3>
                <div class="mc-code">{{ currentCard.code }}</div>
              </div>

              <div class="mc-prices">
                <div class="mc-price-box">
                  <span>현재가</span>
                  <strong>{{ currentCard.price.toLocaleString() }}원</strong>
                </div>
                <div class="mc-price-box">
                  <span>등락률</span>
                  <strong :class="currentCard.rate >= 0 ? 'up' : 'down'">{{ currentCard.rate >= 0 ? '+' : '' }}{{ currentCard.rate.toFixed(2) }}%</strong>
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
                    <template v-for="d in currentCard.dna" :key="d.label">
                      <span class="dna-k">{{ d.label }}</span>
                      <span class="dna-v">{{ d.value }}</span>
                    </template>
                  </div>
                </div>
              </div>

              <div class="mc-reason">🐤 성장 선호와 {{ currentCard.sector }} 모멘텀(성장 {{ currentCard.dna[1].value }})이 맞아요.</div>
              <div class="mc-interest">❤️ {{ currentCard.interest.toLocaleString() }}명이 이 종목에 관심 있어요</div>
            </article>
          </div>

          <div class="sv-controls">
            <button class="sv-ctrl pass" type="button" @click="swipeAction('pass')">✕</button>
            <button class="sv-ctrl save" type="button" @click="swipeAction('save')">♥</button>
            <button class="sv-ctrl like" type="button" @click="swipeAction('like')">↗</button>
          </div>
          <p class="sv-hint">카드를 좌우로 드래그하거나 버튼을 눌러 넘길 수 있어요</p>
        </template>

        <!-- ===== 결과 모드 (관심·저장한 종목) ===== -->
        <template v-else>
        <div class="sv-result-head">
          <div>
            <p class="eyebrow">스와이프 완료 🎉</p>
            <h2>관심 · 저장한 종목 {{ savedStocks.length }}개</h2>
          </div>
          <button class="sv-reset" type="button" @click="resetSwipe">다시 고르기</button>
        </div>

        <!-- 필터 탭 -->
        <div class="filter-row">
          <div class="segmented">
            <button
              v-for="f in marketFilters"
              :key="f.key"
              type="button"
              :class="{ 'is-selected': marketFilter === f.key }"
              @click="marketFilter = f.key"
            >{{ f.label }}</button>
          </div>
          <div class="period-tabs">
            <button
              v-for="p in periods"
              :key="p.key"
              type="button"
              :class="{ 'is-selected': sortPeriod === p.key }"
              @click="sortPeriod = p.key"
            >{{ p.label }}</button>
          </div>
        </div>

        <!-- 테이블 헤더 -->
        <div class="stock-row stock-row-head">
          <span class="col-rank">순위</span>
          <span class="col-name">종목명</span>
          <span class="col-price">현재가</span>
          <span class="col-rate">등락률</span>
          <span class="col-vol">거래대금</span>
          <span class="col-bar">매수/매도</span>
          <span class="col-note">AI 요약</span>
          <span class="col-spark">추이</span>
        </div>

        <!-- 종목 행 -->
        <div class="stock-list">
          <div v-if="!filteredStocks.length" class="sv-empty">
            선택한 종목이 없어요.
            <button type="button" @click="resetSwipe">다시 고르기</button>
          </div>
          <div
            v-for="s in filteredStocks"
            :key="s.code"
            class="stock-row stock-row-data"
            :class="{ 'is-selected': selectedStock?.code === s.code }"
            @click="selectStock(s)"
          >
            <!-- 순위 -->
            <span class="col-rank rank-num">{{ s.rank }}</span>

            <!-- 종목명 -->
            <div class="col-name stock-name-cell">
              <div class="stock-logo" :style="{ background: s.color }">
                {{ s.name.slice(0, 1) }}
              </div>
              <div class="stock-name-info">
                <strong>{{ s.name }}</strong>
                <span>{{ s.market }} · {{ s.sector }}</span>
              </div>
              <span class="saved-tag" :class="s.action">{{ s.action === 'like' ? '관심' : '저장' }}</span>
            </div>

            <!-- 현재가 -->
            <span class="col-price price-val">{{ s.price.toLocaleString() }}<small>원</small></span>

            <!-- 등락률 -->
            <span
              class="col-rate rate-pill"
              :class="s.rate >= 0 ? 'up' : 'down'"
            >
              {{ s.rate >= 0 ? '+' : '' }}{{ s.rate.toFixed(2) }}%
            </span>

            <!-- 거래대금 -->
            <span class="col-vol vol-val">{{ s.volume }}</span>

            <!-- 매수/매도 비율 바 -->
            <div class="col-bar ratio-bar-wrap">
              <div class="ratio-bar">
                <div class="ratio-buy" :style="{ width: s.buyRatio + '%' }"></div>
                <div class="ratio-sell" :style="{ width: s.sellRatio + '%' }"></div>
              </div>
              <div class="ratio-labels">
                <span class="buy-lbl">{{ s.buyRatio }}</span>
                <span class="sell-lbl">{{ s.sellRatio }}</span>
              </div>
            </div>

            <!-- AI 요약 -->
            <span class="col-note ai-note">{{ s.aiNote }}</span>

            <!-- 스파크라인 -->
            <div class="col-spark">
              <SparklineChart
                :values="s.sparkline"
                :width="72"
                :height="28"
                class="spark-mini"
                :class="s.rate >= 0 ? 'spark-pos' : 'spark-neg'"
              />
            </div>
          </div>
        </div>
        </template>
        </template>
      </section>

      <!-- ===== 오른쪽: 종목 상세 ===== -->
      <aside
        class="detail-panel panel"
        :class="{ 'is-visible': selectedStock }"
        aria-label="종목 상세"
      >
        <div v-if="!selectedStock" class="detail-empty">
          <span>👆</span>
          <p>종목을 클릭하면<br>상세 정보가 나타납니다</p>
        </div>

        <div v-else class="detail-content">
          <!-- 종목 헤더 -->
          <div class="detail-stock-head">
            <div class="detail-logo" :style="{ background: selectedStock.color }">
              {{ selectedStock.name.slice(0, 1) }}
            </div>
            <div>
              <h3 class="detail-name">{{ selectedStock.name }}</h3>
              <span class="detail-meta">{{ selectedStock.market }} · {{ selectedStock.code }}</span>
            </div>
            <button class="detail-go-btn" type="button"
              @click="router.push(`/stocks/${selectedStock.code}`)">상세 →</button>
            <button class="detail-close" @click="selectedStock = null">✕</button>
          </div>

          <div class="detail-price-row">
            <strong class="detail-price">{{ selectedStock.price.toLocaleString() }}<small>원</small></strong>
            <span
              class="detail-rate"
              :class="selectedStock.rate >= 0 ? 'is-up' : 'is-down'"
            >
              {{ selectedStock.rate >= 0 ? '+' : '' }}{{ selectedStock.rate.toFixed(2) }}%
            </span>
          </div>
          <div class="detail-change" :class="selectedStock.rate >= 0 ? 'is-up' : 'is-down'">
            {{ fmtChange(selectedStock.change, selectedStock.market) }}
          </div>

          <!-- 차트 -->
          <div class="detail-chart-wrap">
            <div class="chart-period-tabs">
              <button v-for="p in ['1분','3분','10분','일']" :key="p"
                class="chart-tab" :class="{ 'is-active': p === '3분' }">{{ p }}</button>
            </div>
            <svg
              class="detail-chart"
              viewBox="0 0 280 120"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <!-- 그리드 라인 -->
              <line v-for="y in [30,60,90]" :key="y" :x1="0" :y1="y" x2="280" :y2="y"
                stroke="rgba(180,200,255,0.3)" stroke-width="1" stroke-dasharray="4 4" />

              <!-- 면적 채우기 -->
              <path
                :d="buildChartPath(selectedStock.chartPoints, 280, 120).area"
                :fill="selectedStock.rate >= 0 ? 'rgba(15,159,110,0.1)' : 'rgba(255,59,92,0.1)'"
              />
              <!-- 라인 -->
              <path
                :d="buildChartPath(selectedStock.chartPoints, 280, 120).line"
                fill="none"
                :stroke="selectedStock.rate >= 0 ? 'var(--positive)' : '#FF3B5C'"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <!-- 현재가 점 -->
              <circle
                :cx="280"
                :cy="buildChartPath(selectedStock.chartPoints, 280, 120).lastY"
                r="4"
                :fill="selectedStock.rate >= 0 ? 'var(--positive)' : '#FF3B5C'"
              />
            </svg>
            <div class="chart-time-labels">
              <span>09:00</span>
              <span>11:00</span>
              <span>13:00</span>
              <span>15:30</span>
            </div>
          </div>

          <!-- 매수/매도 비율 -->
          <div class="detail-ratio-section">
            <div class="detail-ratio-bar">
              <div class="detail-ratio-buy" :style="{ width: selectedStock.buyRatio + '%' }">
                {{ selectedStock.buyRatio }}
              </div>
              <div class="detail-ratio-sell" :style="{ width: selectedStock.sellRatio + '%' }">
                {{ selectedStock.sellRatio }}
              </div>
            </div>
            <div class="detail-ratio-labels">
              <span class="buy-text">매수</span>
              <span class="sell-text">매도</span>
            </div>
          </div>

          <!-- AI 분석 -->
          <div class="detail-section">
            <div class="detail-section-head">
              <strong>왜 {{ selectedStock.rate >= 0 ? '올랐을까' : '떨어졌을까' }}?</strong>
              <span class="detail-time">20분 전</span>
            </div>
            <div class="detail-ai-box">
              <span class="detail-ai-icon">✦</span>
              <p class="detail-ai-text">{{ selectedStock.aiReason }}</p>
            </div>
          </div>

          <!-- 한 줄 요약 -->
          <div class="detail-section">
            <strong class="detail-section-label">한 줄 요약</strong>
            <ul class="detail-summary-list">
              <li v-for="(s, i) in selectedStock.summary" :key="i">
                <span class="summary-dot"></span>{{ s }}
              </li>
            </ul>
          </div>

          <!-- 커뮤니티 -->
          <div class="detail-section" v-if="selectedStock.community.length">
            <strong class="detail-section-label">커뮤니티</strong>
            <div class="detail-community">
              <div
                v-for="(c, i) in selectedStock.community"
                :key="i"
                class="community-item"
                :class="{ 'is-alert': c.type === 'alert' }"
              >
                <div v-if="c.type === 'alert'" class="community-alert">
                  <span class="alert-badge">구독</span>
                  <span>{{ c.content }}</span>
                </div>
                <div v-else class="community-post">
                  <div class="community-post-head">
                    <strong>{{ c.user }}</strong>
                    <span>{{ c.time }}분 전</span>
                  </div>
                  <p>{{ c.content }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>

  </div>
</template>

<style scoped>
/* ===== 페이지 ===== */
.stocks-page { display: flex; flex-direction: column; gap: 16px; }

/* ===== 헤더 ===== */
.stocks-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 22px;
}

.header-pills {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.market-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 14px;
  border-radius: 999px;
  background: var(--surface-soft);
  border: 1px solid var(--glass-border);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
}

.market-pill em { font-style: normal; color: var(--ink); }

.mdot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--faint); flex-shrink: 0;
}
.mdot.open { background: var(--positive); box-shadow: 0 0 0 2.5px rgba(15,159,110,.22); }

/* ===== 레이아웃 ===== */
.stocks-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
  align-items: start;
}

/* ===== 필터 탭 ===== */
.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.segmented {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: var(--glass-subtle);
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
  background: var(--chip-active);
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08), var(--glass-inset);
}

.period-tabs {
  display: flex;
  gap: 2px;
  background: var(--glass-subtle);
  padding: 4px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
}

.period-tabs button {
  min-height: 28px;
  padding: 0 10px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.18s, color 0.18s;
}

.period-tabs button.is-selected {
  background: var(--chip-active);
  color: var(--ink);
  box-shadow: 0 2px 6px rgba(0,0,0,0.06), var(--glass-inset);
}

/* ===== 테이블 ===== */
.stocks-list-panel { padding: 20px; }

.stock-row {
  display: grid;
  grid-template-columns: 36px minmax(140px, 1.8fr) 90px 72px 58px 90px minmax(80px, 1fr) 80px;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
}

.stock-row-head {
  font-size: 11px;
  font-weight: 900;
  color: var(--faint);
  padding-bottom: 6px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 2px;
}

.stock-list { display: flex; flex-direction: column; gap: 1px; max-height: 70vh; overflow-y: auto; }

.stock-row-data {
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.14s;
}

.stock-row-data:hover { background: var(--surface-soft); }
.stock-row-data.is-selected {
  background: rgba(49,93,255,0.07);
  outline: 1px solid rgba(49,93,255,0.2);
}

/* 컬럼 */
.col-rank { text-align: center; }
.col-price, .col-rate, .col-vol { text-align: right; }
.col-spark { display: flex; justify-content: flex-end; }

.rank-num { font-size: 13px; font-weight: 900; color: var(--faint); }

/* 종목명 셀 */
.stock-name-cell { display: flex; align-items: center; gap: 10px; min-width: 0; }

.stock-logo {
  width: 34px; height: 34px; border-radius: 50%;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 900; color: #fff;
}

.stock-name-info strong {
  display: block;
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stock-name-info span {
  display: block;
  font-size: 11px;
  color: var(--faint);
  font-weight: 700;
}

/* 가격/등락 */
.price-val {
  font-size: 13px;
  font-weight: 900;
  color: var(--ink);
}
.price-val small { font-size: 10px; font-weight: 700; color: var(--faint); margin-left: 1px; }

.rate-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

.rate-pill.up { background: rgba(15,159,110,0.12); color: var(--positive); }
.rate-pill.down { background: rgba(255,59,92,0.1); color: #FF3B5C; }

.vol-val { font-size: 12px; font-weight: 900; color: var(--muted); }

/* 매수/매도 바 */
.ratio-bar-wrap {}

.ratio-bar {
  display: flex;
  height: 5px;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 3px;
}

.ratio-buy { background: #0066CC; height: 100%; }
.ratio-sell { background: #FF3B5C; height: 100%; }

.ratio-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  font-weight: 900;
}

.buy-lbl { color: var(--krx-down); }
.sell-lbl { color: var(--krx-up); }

/* AI 노트 */
.ai-note {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 스파크 */
.spark-mini { width: 72px; height: 28px; }
.spark-pos :deep(.sparkline-line) { stroke: var(--positive); }
.spark-pos :deep(.sparkline-fill) { fill: rgba(15,159,110,0.1); }
.spark-neg :deep(.sparkline-line) { stroke: #FF3B5C; }
.spark-neg :deep(.sparkline-fill) { fill: rgba(255,59,92,0.08); }

/* ===== 상세 패널 ===== */
.detail-panel {
  padding: 0;
  overflow: hidden;
  transition: opacity 0.22s ease;
  position: sticky;
  top: 80px;
}

.detail-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 300px;
  color: var(--faint);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  line-height: 1.6;
}

.detail-empty span { font-size: 32px; }

.detail-content { display: flex; flex-direction: column; }

/* 종목 헤더 */
.detail-stock-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--line);
}

.detail-logo {
  width: 38px; height: 38px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 900; color: #fff;
  flex-shrink: 0;
}

.detail-name {
  font-size: 16px;
  font-weight: 900;
  color: var(--ink);
  margin: 0 0 2px;
}

.detail-meta { font-size: 11px; font-weight: 700; color: var(--faint); }

.detail-go-btn {
  margin-left: auto;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(49,93,255,0.3);
  background: rgba(49,93,255,0.07);
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.18s;
}

.detail-go-btn:hover { background: rgba(49,93,255,0.14); }

.detail-close {
  width: 28px; height: 28px;
  border-radius: 50%;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 12px;
  flex-shrink: 0;
  cursor: pointer;
  transition: background 0.18s;
}

.detail-close:hover { background: var(--glass-strong); color: var(--ink); }

/* 가격 */
.detail-price-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 12px 16px 2px;
}

.detail-price {
  font-size: 22px;
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -0.5px;
}

.detail-price small { font-size: 13px; font-weight: 700; color: var(--faint); margin-left: 2px; }

.detail-rate {
  font-size: 15px;
  font-weight: 900;
}

.detail-change {
  padding: 0 16px 12px;
  font-size: 13px;
  font-weight: 900;
}

/* 차트 */
.detail-chart-wrap {
  padding: 0 0 8px;
  border-bottom: 1px solid var(--line);
}

.chart-period-tabs {
  display: flex;
  gap: 2px;
  padding: 8px 12px 6px;
}

.chart-tab {
  padding: 4px 10px;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: var(--faint);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.chart-tab.is-active {
  background: rgba(49,93,255,0.1);
  color: var(--accent);
}

.detail-chart {
  display: block;
  width: 100%;
  height: 120px;
}

.chart-time-labels {
  display: flex;
  justify-content: space-between;
  padding: 4px 10px 2px;
  font-size: 10px;
  font-weight: 700;
  color: var(--faint);
}

/* 매수/매도 비율 */
.detail-ratio-section { padding: 10px 16px; border-bottom: 1px solid var(--line); }

.detail-ratio-bar {
  display: flex;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 4px;
  font-size: 10px;
  font-weight: 900;
  color: #fff;
}

.detail-ratio-buy {
  background: #0066CC;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 6px;
}

.detail-ratio-sell {
  background: #FF3B5C;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 6px;
}

.detail-ratio-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 900;
}

.buy-text { color: var(--krx-down); }
.sell-text { color: var(--krx-up); }

/* 섹션 */
.detail-section {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.detail-section:last-child { border-bottom: 0; }

.detail-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.detail-section-head strong,
.detail-section-label {
  font-size: 13px;
  font-weight: 900;
  color: var(--ink);
  display: block;
  margin-bottom: 8px;
}

.detail-time { font-size: 11px; font-weight: 700; color: var(--faint); }

.detail-ai-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--radius);
  background: var(--surface-soft);
  border: 1px solid var(--glass-border);
}

.detail-ai-icon {
  color: var(--accent);
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 1px;
}

.detail-ai-text {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.5;
  word-break: keep-all;
}

/* 한 줄 요약 */
.detail-summary-list {
  margin: 0; padding: 0; list-style: none;
  display: flex; flex-direction: column; gap: 6px;
}

.detail-summary-list li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.5;
  word-break: keep-all;
}

.summary-dot {
  flex-shrink: 0;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--accent);
  margin-top: 5px;
}

/* 커뮤니티 */
.detail-community { display: flex; flex-direction: column; gap: 8px; }

.community-post-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 3px;
}

.community-post-head strong { font-size: 12px; font-weight: 900; color: var(--ink); }
.community-post-head span { font-size: 11px; color: var(--faint); }

.community-post p {
  margin: 0;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.4;
  word-break: keep-all;
}

.community-alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius);
  background: rgba(49,93,255,0.07);
  border: 1px solid rgba(49,93,255,0.2);
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
}

.alert-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  font-size: 10px;
  font-weight: 900;
  flex-shrink: 0;
}

/* ===== 뷰 토글 (리퀴드 글래스) ===== */
.view-toggle {
  position: relative;
  display: inline-flex;
  padding: 4px;
  border-radius: 999px;
  background: var(--glass-subtle);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-inset);
  margin-bottom: 16px;
}
.view-toggle button {
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 112px;
  padding: 9px 22px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: color 0.2s ease;
}
.view-toggle button.on { color: var(--accent); }

/* 물방울처럼 슝 미끄러지는 글래스 인디케이터 */
.view-toggle-thumb {
  position: absolute;
  top: 4px;
  bottom: 4px;
  left: 4px;
  width: calc(50% - 4px);
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(232,238,255,0.62) 100%);
  border: 1px solid rgba(255,255,255,0.8);
  box-shadow:
    0 6px 18px rgba(49,93,255,0.22),
    inset 0 1px 1px rgba(255,255,255,0.95),
    inset 0 -3px 8px rgba(49,93,255,0.12);
  backdrop-filter: blur(10px) saturate(1.4);
  -webkit-backdrop-filter: blur(10px) saturate(1.4);
  pointer-events: none;
  z-index: 0;
  /* 스프링 오버슈트로 '슝~' 하는 액체 느낌 */
  transition: transform 0.36s cubic-bezier(0.34, 1.56, 0.64, 1);
  will-change: transform;
}
.view-toggle.preference .view-toggle-thumb { transform: translateX(100%); }

@media (prefers-reduced-motion: reduce) {
  .view-toggle-thumb { transition: transform 0.2s ease; }
}

/* ===== 인기 종목 (실시간 랭킹) ===== */
.pop-filter { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 10px; }
.pop-sort { display: inline-flex; gap: 4px; padding: 3px; border-radius: 999px; background: var(--glass-subtle); border: 1px solid var(--glass-border); }
.pop-sort button { padding: 5px 12px; border: 0; border-radius: 999px; background: transparent; color: var(--muted); font-size: 12px; font-weight: 900; cursor: pointer; transition: background 0.15s, color 0.15s; }
.pop-sort button.is-selected { background: var(--chip-active); color: var(--ink); box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.pop-caption { margin: 0 0 8px; font-size: 12px; font-weight: 700; color: var(--faint); }

.pop-table { display: flex; flex-direction: column; }
.pop-row {
  display: grid;
  grid-template-columns: 60px minmax(120px, 1.5fr) 92px 78px 80px 108px minmax(110px, 1.2fr);
  align-items: center; gap: 10px;
  padding: 11px 8px; border-bottom: 1px solid var(--faint);
  cursor: pointer; transition: background 0.14s;
}
.pop-row:last-child { border-bottom: 0; }
.pop-row.pop-head { border-bottom: 1px solid var(--line); cursor: default; }
.pop-row.pop-head span { font-size: 11px; font-weight: 800; color: var(--faint); }
.pop-row:not(.pop-head):hover { background: var(--surface-soft); }
.pop-row.active { background: rgba(49,93,255,0.07); }

.pop-num { text-align: right; }
.pop-rank-h { text-align: left; }
.pop-ratio-h, .pop-ai-h { text-align: left; }

.pop-rank { display: flex; align-items: center; gap: 8px; }
.pop-heart { border: 0; background: none; padding: 0; font-size: 16px; color: var(--faint); cursor: pointer; line-height: 1; transition: color 0.14s, transform 0.12s; }
.pop-heart.on { color: #e3344f; }
.pop-heart:hover { transform: scale(1.15); }
.pop-rank-num { font-size: 14px; font-weight: 900; color: var(--ink); }

.pop-name { display: flex; align-items: center; gap: 10px; min-width: 0; }
.pop-logo { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 12px; font-weight: 900; flex-shrink: 0; }
.pop-name-info { min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.pop-name-info strong { font-size: 14px; font-weight: 900; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pop-name-info span { font-size: 11px; font-weight: 700; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.pop-price { font-size: 14px; font-weight: 900; color: var(--ink); font-variant-numeric: tabular-nums; }
.pop-rate { font-size: 13px; font-weight: 900; padding: 3px 8px; border-radius: 8px; justify-self: end; }
.pop-rate.up { color: #e3344f; background: rgba(227,52,79,0.1); }
.pop-rate.down { color: #2b59d6; background: rgba(43,89,214,0.1); }
.pop-vol { font-size: 13px; font-weight: 800; color: var(--muted); }

.pop-ratio { display: flex; flex-direction: column; gap: 3px; }
.pop-ratio-bar { display: flex; height: 5px; border-radius: 999px; overflow: hidden; background: var(--surface-soft); }
.pop-ratio-bar .buy { background: #2b59d6; }
.pop-ratio-bar .sell { background: #e3344f; }
.pop-ratio-nums { display: flex; justify-content: space-between; font-size: 10px; font-weight: 900; }
.pop-ratio-nums .b { color: #2b59d6; }
.pop-ratio-nums .s { color: #e3344f; }

.pop-ai { font-size: 12px; font-weight: 700; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ===== 반응형 ===== */
@media (max-width: 1200px) {
  .stocks-layout { grid-template-columns: 1fr; }
  .detail-panel { position: static; }
}

@media (max-width: 820px) {
  .pop-row { grid-template-columns: 52px minmax(110px, 1.4fr) 84px 70px; }
  .pop-num.pop-vol, .pop-ratio, .pop-ratio-h, .pop-ai, .pop-ai-h { display: none; }
}

@media (max-width: 900px) {
  .stock-row {
    grid-template-columns: 28px minmax(120px, 1.4fr) 80px 64px 50px;
  }
  .col-bar, .col-note, .col-spark { display: none; }
}

/* ===== 스와이프 관심종목 ===== */
.sv-match-header { text-align: center; margin-bottom: 16px; }
.sv-match-title { font-size: 22px; font-weight: 900; letter-spacing: -0.5px; color: var(--ink); margin: 0; }
.sv-match-sub { margin: 6px 0 0; color: var(--muted); font-size: 13px; line-height: 1.5; word-break: keep-all; }
.sv-match-count { display: inline-block; margin-top: 8px; color: var(--faint); font-size: 12px; font-weight: 900; }

.sv-deck { position: relative; display: flex; justify-content: center; }
.sv-card {
  position: relative; width: 100%; max-width: 460px; border-radius: 24px; padding: 22px; color: #fff;
  box-shadow: 0 16px 44px rgba(109,40,217,0.28), 0 6px 14px rgba(0,0,0,0.12);
  overflow: hidden; user-select: none; touch-action: none; cursor: grab; will-change: transform, opacity;
}
.sv-card:active { cursor: grabbing; }
.sv-card::before { content: ''; position: absolute; width: 200px; height: 200px; top: -60px; right: -60px; border-radius: 50%; background: rgba(255,255,255,0.15); pointer-events: none; }
.sv-card > * { position: relative; z-index: 1; }

.sv-feedback { position: absolute; inset: 0; z-index: 6; display: flex; align-items: center; justify-content: center; pointer-events: none; opacity: 0; transition: opacity 0.14s ease; }
.sv-feedback span { padding: 12px 26px; border-radius: 16px; font-size: 28px; font-weight: 900; color: #fff; border: 4px solid currentColor; background: rgba(8,12,24,0.34); box-shadow: 0 14px 44px rgba(0,0,0,0.3); transform: rotate(-7deg); }
.sv-feedback.like span { color: #2fe39f; }
.sv-feedback.pass span { color: #ff6f8b; }
.sv-feedback.save span { color: #ffce5a; }

/* 카드 내용 (메인 페이지 궁합 카드와 동일) */
.mc-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.mc-badge { display: inline-flex; align-items: center; padding: 5px 12px; border-radius: 999px; background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.28); color: rgba(255,255,255,0.92); font-size: 12px; font-weight: 900; }
.mc-score { text-align: right; font-size: 36px; font-weight: 900; line-height: 0.9; letter-spacing: -2px; color: #fff; flex-shrink: 0; text-shadow: 0 2px 10px rgba(0,0,0,0.28); }
.mc-score span { display: block; font-size: 11px; letter-spacing: 0; font-weight: 900; color: rgba(255,255,255,0.75); margin-top: 4px; }
.mc-name-block { margin-top: 18px; }
.mc-name { margin: 0; color: #fff; font-size: 28px; font-weight: 900; letter-spacing: -1px; line-height: 1.1; text-shadow: 0 2px 12px rgba(0,0,0,0.32), 0 1px 2px rgba(0,0,0,0.25); }
.mc-code { margin-top: 4px; color: rgba(255,255,255,0.85); font-size: 13px; font-weight: 900; text-shadow: 0 1px 6px rgba(0,0,0,0.28); }
.mc-prices { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.mc-price-box { padding: 10px 12px; border-radius: 14px; background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2); }
.mc-price-box span { display: block; color: rgba(255,255,255,0.65); font-size: 11px; font-weight: 900; margin-bottom: 4px; }
.mc-price-box strong { display: block; color: #fff; font-size: 15px; font-weight: 900; }
.mc-price-box strong.up { color: #6effc9; }
.mc-price-box strong.down { color: #93b8ff; }
.mc-dna { display: flex; align-items: center; gap: 12px; margin-top: 14px; padding: 14px; border-radius: 18px; background: rgba(255,255,255,0.94); }
.dna-radar { width: 96px; height: 96px; flex-shrink: 0; }
.dna-grid { fill: rgba(49,93,255,0.05); stroke: rgba(49,93,255,0.2); stroke-width: 1; }
.dna-axis { stroke: rgba(49,93,255,0.18); stroke-width: 1; }
.dna-shape { fill: rgba(49,93,255,0.45); stroke: var(--accent); stroke-width: 2; }
.dna-info { flex: 1; min-width: 0; }
.dna-title { font-size: 13px; font-weight: 900; color: var(--ink); margin-bottom: 10px; }
.dna-vals { display: grid; grid-template-columns: auto 1fr auto 1fr; gap: 8px 10px; align-items: center; }
.dna-k { font-size: 12px; font-weight: 800; color: var(--muted); }
.dna-v { font-size: 13px; font-weight: 900; color: var(--accent); text-align: right; }
.mc-reason { margin-top: 14px; font-size: 13px; font-weight: 800; color: #fff; text-shadow: 0 1px 6px rgba(0,0,0,0.3); }
.mc-interest { margin-top: 12px; font-size: 13px; font-weight: 800; color: #fff; text-shadow: 0 1px 6px rgba(0,0,0,0.3); }

.sv-controls { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 18px; }
.sv-ctrl { width: 56px; height: 56px; border-radius: 50%; border: 1.5px solid var(--glass-border); background: var(--surface-soft); font-size: 22px; font-weight: 900; color: var(--ink); cursor: pointer; box-shadow: 0 6px 18px rgba(0,0,0,0.1); transition: transform 0.18s ease; }
.sv-ctrl.pass { color: var(--negative); border-color: rgba(207,61,61,0.4); background: rgba(207,61,61,0.07); }
.sv-ctrl.like { color: var(--accent); border-color: rgba(49,93,255,0.4); background: rgba(49,93,255,0.07); }
.sv-ctrl.save { width: 68px; height: 68px; border: 0; background: linear-gradient(135deg, #ff3d8b 0%, #e3344f 100%); color: #fff; font-size: 26px; box-shadow: 0 10px 30px rgba(255,61,139,0.4); }
.sv-ctrl:hover { transform: translateY(-3px) scale(1.05); }
.sv-hint { margin: 12px 0 0; text-align: center; font-size: 12px; font-weight: 700; color: var(--faint); }

.sv-result-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.sv-result-head h2 { font-size: 18px; font-weight: 900; color: var(--ink); margin: 2px 0 0; }
.sv-reset { flex-shrink: 0; padding: 7px 14px; border-radius: 999px; border: 1px solid var(--glass-border); background: var(--surface-soft); color: var(--muted); font-size: 12px; font-weight: 900; cursor: pointer; }
.sv-reset:hover { background: var(--glass-strong); color: var(--ink); }

.saved-tag { flex-shrink: 0; margin-left: 8px; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 900; }
.saved-tag.like { background: rgba(49,93,255,0.12); color: var(--accent); }
.saved-tag.save { background: rgba(255,61,139,0.12); color: #e3344f; }

.sv-empty { padding: 48px 20px; text-align: center; color: var(--muted); font-size: 14px; font-weight: 700; }
.sv-empty button { margin-left: 8px; border: 0; background: none; color: var(--accent); font-weight: 900; cursor: pointer; text-decoration: underline; }
</style>
