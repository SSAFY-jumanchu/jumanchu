<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { stocksApi, portfolioApi } from '../api'

const router = useRouter()
const route = useRoute()
const stockCode = route.params.code || '005930'

// 초기값은 와이어프레임 목업(삼성전자) — onMounted에서 실데이터로 교체
const stock = ref({
  code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자',
  currency: 'KRW',
  price: 317000, open: 309500, high: 319000, low: 305500, prevClose: 309500,
  volume: 24943808,
  marketCap: '237.1조',
  per: 14.2, pbr: 1.18, eps: 22324,
  roe: 8.57, beta: 1.27,
  high52w: 323000, low52w: 55600,
})

const change = computed(() => stock.value.price - stock.value.prevClose)
const changeRate = computed(() =>
  stock.value.prevClose ? (change.value / stock.value.prevClose) * 100 : 0,
)

// ===== 차트 데이터 (5분봉 9:00~15:30, 78개) =====
const intradayPrices = ref([
  309500, 308000, 306800, 306000, 306500, 307200,
  307800, 308300, 308800, 309200, 309500, 308800,
  308200, 308500, 309000, 309500, 310000, 310500, 311000, 310500, 310200, 310500, 311000, 311500,
  312000, 311500, 311200, 311500, 312000, 312500, 313000, 312500, 312200, 311800, 312000, 312500,
  313000, 313500, 314000, 313500, 313200, 313500, 314000, 314500, 315000, 314500, 315000, 315500,
  316000, 315500, 316000, 316500, 317000, 316500, 316200, 316500, 317000, 317500, 317000, 316500,
  317000, 317500, 318000, 317500, 317000, 316500, 317000, 317500, 317000, 317000, 316500, 317000,
  317500, 317000, 316500, 317000, 317500, 317000,
])

const volumeData = [
  85, 72, 80, 90, 65, 55, 45, 40, 38, 35, 32, 30,
  28, 30, 32, 35, 38, 42, 45, 40, 35, 30, 28, 25,
  22, 20, 18, 20, 22, 25, 28, 25, 22, 20, 22, 25,
  28, 32, 35, 32, 28, 30, 35, 40, 45, 42, 40, 38,
  42, 40, 45, 50, 55, 50, 45, 50, 55, 60, 55, 50,
  55, 60, 65, 60, 55, 50, 55, 60, 55, 52, 50, 55,
  70, 80, 85, 90, 95, 100,
]

// SVG 라인 차트 경로 계산
function buildPath(prices, w, h, padT = 16, padB = 16) {
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const n = prices.length
  const pts = prices.map((p, i) => {
    const x = (i / (n - 1)) * w
    const y = padT + (1 - (p - min) / range) * (h - padT - padB)
    return { x, y }
  })
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  const area = `${line} L${w},${h} L0,${h} Z`
  return { line, area }
}

const chartPath = computed(() => buildPath(intradayPrices.value, 560, 200))

// ===== 차트 기간 탭 =====
const chartPeriods = ['3분', '일', '주', '월', '년']
const selectedPeriod = ref('일')

// ===== 상단 탭 =====
const mainTabs = ['차트', '호가', '종목정보', '뉴스·공시', '거래현황', '커뮤니티']
const selectedTab = ref('차트')

// ===== 호가 데이터 =====
const asks = ref([
  { price: 321000, qty: 3456 },
  { price: 320500, qty: 6789 },
  { price: 320000, qty: 9012 },
  { price: 319500, qty: 12345 },
  { price: 319000, qty: 8901 },
  { price: 318500, qty: 15678 },
  { price: 318000, qty: 9876 },
  { price: 317500, qty: 23456 },
].reverse()) // 화면에서 낮은 ask가 현재가 위에 바로 오도록

const bids = ref([
  { price: 316500, qty: 18901 },
  { price: 316000, qty: 12345 },
  { price: 315500, qty: 8765 },
  { price: 315000, qty: 23456 },
  { price: 314500, qty: 9876 },
  { price: 314000, qty: 7654 },
  { price: 313500, qty: 5432 },
  { price: 313000, qty: 8901 },
])

const maxAskQty = computed(() => Math.max(...asks.value.map(a => a.qty)))
const maxBidQty = computed(() => Math.max(...bids.value.map(b => b.qty)))

// ===== 시세 (체결 내역) =====
const trades = [
  { price: 317000, qty: 5, rate: +2.42, time: '15:30:02', side: 'up' },
  { price: 317000, qty: 2, rate: +2.42, time: '15:29:58', side: 'up' },
  { price: 316500, qty: 8, rate: +2.26, time: '15:29:45', side: 'up' },
  { price: 317000, qty: 3, rate: +2.42, time: '15:29:32', side: 'up' },
  { price: 317500, qty: 1, rate: +2.58, time: '15:29:15', side: 'up' },
  { price: 317000, qty: 12, rate: +2.42, time: '15:28:50', side: 'up' },
  { price: 316500, qty: 4, rate: +2.26, time: '15:28:22', side: 'up' },
  { price: 316000, qty: 7, rate: +2.10, time: '15:27:55', side: 'up' },
  { price: 316500, qty: 2, rate: +2.26, time: '15:27:30', side: 'up' },
  { price: 317000, qty: 9, rate: +2.42, time: '15:27:08', side: 'up' },
  { price: 317500, qty: 3, rate: +2.58, time: '15:26:45', side: 'up' },
  { price: 317000, qty: 6, rate: +2.42, time: '15:26:20', side: 'up' },
  { price: 316500, qty: 15, rate: +2.26, time: '15:25:55', side: 'up' },
  { price: 316000, qty: 4, rate: +2.10, time: '15:25:30', side: 'up' },
  { price: 315500, qty: 8, rate: +1.94, time: '15:25:05', side: 'down' },
]

// ===== 개인/외국인/기관 =====
const investors = {
  individual: +962126,
  foreign: -710214,
  institution: -311468,
}

const investorHistory = [
  { date: '오늘', individual: +962126, foreign: -710214, institution: -311468 },
  { date: '26.06.04', individual: +238929, foreign: -321817, institution: +64521 },
  { date: '26.06.02', individual: +398595, foreign: -363599, institution: +44317 },
  { date: '26.06.01', individual: -86869, foreign: -732563, institution: +631686 },
  { date: '26.05.29', individual: +446850, foreign: -472461, institution: +12091 },
]

const maxInvAbs = computed(() =>
  Math.max(...investorHistory.map(r => Math.max(Math.abs(r.individual), Math.abs(r.foreign), Math.abs(r.institution))))
)

// ===== 종토방 커뮤니티 =====
const communityPosts = [
  { user: '장기투자자', badge: null, time: '3분', content: '오늘 +2.42% 상승이네요. 외국인이 사고 있어요!', likes: 12 },
  { user: '주린이123', badge: null, time: '15분', content: '반도체 업황 개선되면 삼성이 제일 먼저 올라가겠죠?', likes: 8 },
  { user: '전업투자자', badge: '고수', time: '28분', content: 'HBM 수주 기대감이 주가에 반영되고 있는 것 같습니다.', likes: 34 },
  { user: '스마트투자', badge: null, time: '42분', content: 'PER 14배면 저평가 구간이에요. 장기보유 전략이 좋을 것 같아요.', likes: 21 },
  { user: '배당킹', badge: '장기', time: '1시간', content: '배당 수익률도 좋고 지금 단가 낮을 때 매수 적기인 것 같습니다.', likes: 18 },
  { user: '반도체직업인', badge: null, time: '2시간', content: 'AI 서버 수요 폭발로 DRAM 업황은 계속 좋을 전망입니다.', likes: 45 },
]

// ===== 일지 작성 =====
const diaryText = ref('')
const diarySaved = ref(false)

function saveDiary() {
  if (!diaryText.value.trim()) return
  diarySaved.value = true
  setTimeout(() => { diarySaved.value = false }, 2000)
}

// ===== 주문 패널 =====
const orderSide = ref('BUY')
const orderType = ref('limit')   // limit | market
const orderPrice = ref(317000)
const orderQty = ref(0)
const orderTotal = computed(() => orderPrice.value * orderQty.value)
const orderFee = computed(() => orderTotal.value * 0.00015)

const balance = ref(10000000) // 기본값 — /portfolio/balance/ 응답으로 교체
const ordering = ref(false)
const orderMsg = ref(null) // { ok: boolean, text: string }

function setQtyPct(pct) {
  orderQty.value = Math.floor((balance.value * pct) / orderPrice.value)
}

// 주문: POST /orders/preview/ 검증 → POST /orders/ 체결 (시장가 즉시 체결 모델)
async function submitOrder() {
  if (orderQty.value < 1 || ordering.value) return
  ordering.value = true
  orderMsg.value = null
  try {
    const payload = {
      stock_code: stock.value.code,
      side: orderSide.value,
      quantity: orderQty.value,
    }
    const { data: previewRes } = await portfolioApi.previewOrder(payload)
    if (!previewRes.is_valid) {
      orderMsg.value = { ok: false, text: previewRes.errors?.join(' ') || '주문이 불가능합니다.' }
      return
    }
    const { data } = await portfolioApi.createOrder({
      ...payload,
      idempotency_key: crypto.randomUUID(),
    })
    balance.value = Number(data.balance_after)
    orderQty.value = 0
    orderMsg.value = {
      ok: true,
      text: `${orderSide.value === 'BUY' ? '매수' : '매도'} 체결 완료 (잔고 ₩${fmt(balance.value)})`,
    }
  } catch (e) {
    const d = e.response?.data
    orderMsg.value = {
      ok: false,
      text: d?.detail ?? (e.response?.status === 401 ? '로그인이 필요합니다.' : '주문 처리에 실패했습니다.'),
    }
  } finally {
    ordering.value = false
  }
}

// ===== 실데이터 로드 =====
onMounted(async () => {
  // 종목 기본 정보 + 현재가/지표/차트/호가는 각각 실패해도 나머지는 유지
  try {
    const { data } = await stocksApi.detail(stockCode)
    const s = data.stock
    stock.value = {
      ...stock.value,
      code: s.code, name: s.name, market: s.market, sector: s.sector,
      currency: s.currency,
      marketCap: s.market_cap ? fmtCompact(Number(s.market_cap)) : '-',
    }
  } catch (e) {
    console.warn('종목 정보 로드 실패 — 목업 유지', e)
  }

  try {
    const { data } = await stocksApi.price(stockCode)
    const p = data.price
    stock.value = {
      ...stock.value,
      price: Number(p.current), open: Number(p.open),
      high: Number(p.high), low: Number(p.low),
      prevClose: Number(p.prev_close), volume: p.volume,
    }
    orderPrice.value = Number(p.current)
  } catch (e) {
    console.warn('현재가 로드 실패 — 목업 유지', e)
  }

  try {
    const { data } = await stocksApi.financials(stockCode)
    const ind = data.indicator
    if (ind) {
      stock.value = {
        ...stock.value,
        per: ind.per, pbr: ind.pbr, eps: ind.eps,
        roe: ind.roe, beta: ind.beta,
        high52w: Number(ind.high_52w), low52w: Number(ind.low_52w),
      }
    }
  } catch (e) {
    console.warn('재무 지표 로드 실패 — 목업 유지', e)
  }

  try {
    const { data } = await stocksApi.chart(stockCode, { period: '1d', interval: '5m' })
    if (data.candles?.length) {
      intradayPrices.value = data.candles.map((c) => Number(c.close))
    }
  } catch (e) {
    console.warn('차트 로드 실패 — 목업 유지', e)
  }

  try {
    const { data } = await stocksApi.orderbook(stockCode)
    const ob = data.orderbook
    if (ob.asks?.length) asks.value = [...ob.asks.map((a) => ({ price: Number(a.price), qty: a.quantity }))].reverse()
    if (ob.bids?.length) bids.value = ob.bids.map((b) => ({ price: Number(b.price), qty: b.quantity }))
  } catch (e) {
    console.warn('호가 로드 실패 — 목업 유지', e)
  }

  try {
    const { data } = await portfolioApi.balance()
    balance.value = Number(data.account.balance)
  } catch (e) {
    console.warn('잔고 로드 실패 — 기본값 유지', e)
  }
})

// ===== 유틸 =====
function fmt(v) { return v.toLocaleString('ko-KR') }
function fmtCompact(v) {
  if (v >= 100000000) return `${(v / 100000000).toFixed(1)}억`
  if (v >= 10000) return `${(v / 10000).toFixed(1)}만`
  return v.toLocaleString()
}
function fmtInv(v) {
  const sign = v >= 0 ? '+' : ''
  if (Math.abs(v) >= 10000) return `${sign}${Math.round(v / 10000)}만`
  return `${sign}${v.toLocaleString()}`
}
function invBarWidth(v, max) { return Math.round((Math.abs(v) / max) * 100) }
</script>

<template>
  <div class="sd-page">

    <!-- ===== 상단 헤더 ===== -->
    <header class="sd-header panel">

      <!-- 뒤로 가기 -->
      <button class="back-btn" @click="router.back()">
        <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
          <path d="M13 4L7 10l6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        목록으로
      </button>

      <div class="sd-header-body">
        <!-- 좌: 종목명·가격 -->
        <div class="sd-title-block">
          <div class="sd-name-row">
            <span class="eyebrow">{{ stock.market }} · {{ stock.sector }}</span>
          </div>
          <div class="sd-name-price">
            <h1>{{ stock.name }}</h1>
            <span class="sd-code">{{ stock.code }}</span>
            <button class="watch-toggle-btn">☆ 관심종목 추가</button>
          </div>
          <div class="sd-price-row">
            <strong class="sd-price">₩{{ fmt(stock.price) }}</strong>
            <span class="sd-change" :class="change >= 0 ? 'is-up' : 'is-down'">
              {{ change >= 0 ? '+' : '-' }}₩{{ fmt(Math.abs(change)) }} ({{ change >= 0 ? '+' : '' }}{{ changeRate.toFixed(2) }}%)
            </span>
          </div>
        </div>

        <!-- 우: 키 메트릭 -->
        <div class="sd-key-metrics">
          <div class="metric"><span>시가</span><strong>₩{{ fmt(stock.open) }}</strong></div>
          <div class="metric"><span>고가</span><strong class="is-up">₩{{ fmt(stock.high) }}</strong></div>
          <div class="metric"><span>저가</span><strong class="is-down">₩{{ fmt(stock.low) }}</strong></div>
          <div class="metric"><span>거래량</span><strong>{{ fmtCompact(stock.volume) }}</strong></div>
          <div class="metric"><span>PER</span><strong>{{ stock.per }}</strong></div>
          <div class="metric"><span>시가총액</span><strong>{{ stock.marketCap }}</strong></div>
          <div class="metric"><span>52주 최고</span><strong>₩{{ fmt(stock.high52w) }}</strong></div>
          <div class="metric"><span>52주 최저</span><strong>₩{{ fmt(stock.low52w) }}</strong></div>
        </div>
      </div>

      <!-- 메인 탭 -->
      <nav class="sd-main-tabs">
        <button
          v-for="tab in mainTabs"
          :key="tab"
          :class="{ 'is-active': selectedTab === tab }"
          @click="selectedTab = tab"
        >{{ tab }}</button>
      </nav>
    </header>

    <!-- ===== 3컬럼 메인 그리드 ===== -->
    <div class="sd-grid">

      <!-- ===== 좌: 차트 + 종토방 ===== -->
      <div class="sd-col-left">

        <!-- 차트 패널 -->
        <div class="panel chart-panel">
          <div class="chart-top-bar">
            <div class="period-tabs">
              <button
                v-for="p in chartPeriods"
                :key="p"
                :class="{ 'is-active': selectedPeriod === p }"
                @click="selectedPeriod = p"
              >{{ p }}</button>
            </div>
            <div class="chart-tools">
              <span>보조지표</span>
              <span>그리기</span>
              <span>종목비교</span>
            </div>
          </div>

          <!-- 가격 축 레이블 -->
          <div class="chart-area-wrap">
            <div class="price-axis">
              <span>319,000</span>
              <span>315,000</span>
              <span>311,000</span>
              <span>307,000</span>
              <span>305,500</span>
            </div>

            <!-- 가격 라인 차트 -->
            <div class="chart-svg-wrap">
              <svg viewBox="0 0 560 200" preserveAspectRatio="none" class="price-chart-svg">
                <defs>
                  <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="rgba(49,93,255,0.22)" />
                    <stop offset="100%" stop-color="rgba(49,93,255,0)" />
                  </linearGradient>
                </defs>
                <!-- 그리드 -->
                <line v-for="y in [40, 80, 120, 160]" :key="y" x1="0" :y1="y" x2="560" :y2="y"
                  stroke="rgba(180,200,255,0.25)" stroke-width="1" stroke-dasharray="4 4" />
                <!-- 현재가 수평선 -->
                <line x1="0" y1="92" x2="560" y2="92"
                  stroke="rgba(49,93,255,0.5)" stroke-width="1" stroke-dasharray="6 3" />
                <!-- 면적 -->
                <path :d="chartPath.area" fill="url(#priceGrad)" />
                <!-- 라인 -->
                <path :d="chartPath.line" fill="none" stroke="var(--accent)" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" />
                <!-- 현재가 점 -->
                <circle cx="556" cy="92" r="4" fill="var(--accent)" />
              </svg>

              <!-- 현재가 라벨 -->
              <div class="current-price-label">₩317,000</div>
            </div>
          </div>

          <!-- 시간 축 -->
          <div class="time-axis">
            <span>9:00</span>
            <span>10:00</span>
            <span>11:00</span>
            <span>12:00</span>
            <span>13:00</span>
            <span>14:00</span>
            <span>15:00</span>
            <span>15:30</span>
          </div>

          <!-- 거래량 차트 -->
          <div class="volume-label-row">
            <span class="eyebrow">거래량 (2억)</span>
          </div>
          <div class="volume-chart-wrap">
            <svg viewBox="0 0 560 70" preserveAspectRatio="none" class="volume-svg">
              <rect
                v-for="(v, i) in volumeData"
                :key="i"
                :x="(i / volumeData.length) * 560"
                :width="(560 / volumeData.length) - 1"
                :y="70 - (v / 100) * 68"
                :height="(v / 100) * 68"
                :fill="intradayPrices[i] >= (intradayPrices[i-1] ?? intradayPrices[i]) ? 'rgba(49,93,255,0.5)' : 'rgba(255,59,92,0.45)'"
              />
            </svg>
          </div>
        </div>

        <!-- 종목토론방 -->
        <div class="panel community-panel">
          <div class="community-head">
            <div>
              <p class="eyebrow">Community</p>
              <h3>종목토론방</h3>
            </div>
            <button class="text-btn">전체보기 ›</button>
          </div>

          <div class="community-tabs">
            <button class="is-active">인기순</button>
            <button>최신순</button>
          </div>

          <div class="community-list">
            <div v-for="(post, i) in communityPosts" :key="i" class="community-post">
              <div class="post-head">
                <div class="post-author-row">
                  <div class="post-avatar">{{ post.user.slice(0, 1) }}</div>
                  <strong class="post-user">{{ post.user }}</strong>
                  <span v-if="post.badge" class="post-badge">{{ post.badge }}</span>
                  <span class="post-time">{{ post.time }} 전</span>
                </div>
                <span class="post-likes">♡ {{ post.likes }}</span>
              </div>
              <p class="post-content">{{ post.content }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 중: 호가 + 시세 ===== -->
      <div class="sd-col-mid">

        <!-- 호가 패널 -->
        <div class="panel hoga-panel">
          <div class="hoga-head">
            <h3>호가</h3>
            <div class="hoga-meta-tabs">
              <button class="is-active">실시간</button>
              <button>일별</button>
            </div>
          </div>

          <!-- 매도 총잔량 -->
          <div class="hoga-total-row ask">
            <span class="hoga-total-label">매도잔량</span>
            <span class="hoga-total-val">{{ fmt(asks.reduce((s,a)=>s+a.qty,0)) }}</span>
          </div>

          <!-- 매도 호가 (낮은 ask가 맨 아래, 현재가와 가까운 순) -->
          <div class="hoga-asks">
            <div
              v-for="ask in asks"
              :key="ask.price"
              class="hoga-row ask-row"
            >
              <div class="hoga-bar-wrap">
                <div
                  class="hoga-bar ask-bar"
                  :style="{ width: (ask.qty / maxAskQty * 100) + '%' }"
                ></div>
              </div>
              <span class="hoga-price ask-price">{{ fmt(ask.price) }}</span>
              <span class="hoga-qty">{{ fmt(ask.qty) }}</span>
            </div>
          </div>

          <!-- 현재가 -->
          <div class="hoga-current">
            <span class="hoga-current-price">₩317,000</span>
            <span class="hoga-current-change is-up">+2.42%</span>
          </div>

          <!-- 매수 호가 -->
          <div class="hoga-bids">
            <div
              v-for="bid in bids"
              :key="bid.price"
              class="hoga-row bid-row"
            >
              <span class="hoga-qty">{{ fmt(bid.qty) }}</span>
              <span class="hoga-price bid-price">{{ fmt(bid.price) }}</span>
              <div class="hoga-bar-wrap">
                <div
                  class="hoga-bar bid-bar"
                  :style="{ width: (bid.qty / maxBidQty * 100) + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <!-- 매수 총잔량 -->
          <div class="hoga-total-row bid">
            <span class="hoga-total-val">{{ fmt(bids.reduce((s,b)=>s+b.qty,0)) }}</span>
            <span class="hoga-total-label">매수잔량</span>
          </div>
        </div>

        <!-- 시세 패널 -->
        <div class="panel trade-feed-panel">
          <h3>시세</h3>

          <div class="trade-feed-head">
            <span>체결가</span>
            <span>체결량</span>
            <span>등락</span>
            <span>시각</span>
          </div>

          <div class="trade-feed-list">
            <div
              v-for="(t, i) in trades"
              :key="i"
              class="trade-row"
              :class="t.side === 'up' ? 'is-up-row' : 'is-down-row'"
            >
              <span class="trade-price" :class="t.side === 'up' ? 'is-up' : 'is-down'">
                {{ fmt(t.price) }}
              </span>
              <span class="trade-qty">{{ t.qty }}</span>
              <span class="trade-rate" :class="t.side === 'up' ? 'is-up' : 'is-down'">
                +{{ t.rate.toFixed(2) }}%
              </span>
              <span class="trade-time">{{ t.time }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 우: 주문 + 일지 + 개인/외국인/기관 ===== -->
      <div class="sd-col-right">

        <!-- 주문 패널 -->
        <div class="panel order-panel">
          <p class="eyebrow">일반주문</p>
          <h3>주문하기</h3>

          <!-- 매수/매도 토글 -->
          <div class="order-side-tabs">
            <button
              :class="['buy-tab', { 'is-active-buy': orderSide === 'BUY' }]"
              @click="orderSide = 'BUY'"
            >매수</button>
            <button
              :class="['sell-tab', { 'is-active-sell': orderSide === 'SELL' }]"
              @click="orderSide = 'SELL'"
            >매도</button>
          </div>

          <!-- 주문 유형 -->
          <div class="order-type-row">
            <button
              class="order-type-btn"
              :class="{ 'is-selected': orderType === 'limit' }"
              @click="orderType = 'limit'"
            >지정가</button>
            <button
              class="order-type-btn"
              :class="{ 'is-selected': orderType === 'market' }"
              @click="orderType = 'market'"
            >시장가</button>
          </div>

          <!-- 구매 가격 -->
          <label class="order-field">
            <span>구매 가격 (원)</span>
            <div class="order-input-row">
              <input
                v-if="orderType === 'limit'"
                v-model.number="orderPrice"
                type="number"
                step="500"
                min="0"
              />
              <div v-else class="market-price-display">시장가</div>
              <div class="price-stepper">
                <button @click="orderPrice += 500">+</button>
                <button @click="orderPrice = Math.max(0, orderPrice - 500)">−</button>
              </div>
            </div>
          </label>

          <!-- 수량 -->
          <label class="order-field">
            <span>수량</span>
            <input v-model.number="orderQty" type="number" min="0" placeholder="수량 입력" />
          </label>

          <!-- % 버튼 -->
          <div class="qty-shortcuts">
            <button @click="setQtyPct(0.1)">10%</button>
            <button @click="setQtyPct(0.25)">25%</button>
            <button @click="setQtyPct(0.5)">50%</button>
            <button @click="setQtyPct(1)">최대</button>
          </div>

          <!-- 총 금액 -->
          <dl class="order-summary">
            <div>
              <dt>총 주문 금액</dt>
              <dd>{{ orderTotal > 0 ? '₩' + fmt(orderTotal) : '주문 가능 금액 입력' }}</dd>
            </div>
          </dl>

          <!-- 주문 버튼 -->
          <button
            class="order-submit-btn"
            :class="orderSide === 'BUY' ? 'is-buy' : 'is-sell'"
            :disabled="ordering || orderQty < 1"
            @click="submitOrder"
          >
            {{ ordering ? '주문 처리 중…' : orderSide === 'BUY' ? '매수하기' : '매도하기' }}
          </button>

          <p
            v-if="orderMsg"
            class="fine-print"
            :style="{ color: orderMsg.ok ? 'var(--positive)' : 'var(--negative, #cf3d3d)', fontWeight: 700 }"
          >
            {{ orderMsg.text }}
          </p>
        </div>

        <!-- 일지 작성 -->
        <div class="panel diary-inline-panel">
          <div class="diary-inline-head">
            <p class="eyebrow">매매 일기</p>
            <h3>일지 작성</h3>
          </div>
          <textarea
            v-model="diaryText"
            class="diary-inline-textarea"
            placeholder="이 종목에 대한 매수/매도 이유, 목표가, 오늘의 판단을 기록해두세요."
          ></textarea>
          <button
            class="diary-inline-save-btn"
            :class="{ 'is-saved': diarySaved }"
            :disabled="!diaryText.trim()"
            @click="saveDiary"
          >
            {{ diarySaved ? '✓ 저장됨' : '일지 저장' }}
          </button>
        </div>

        <!-- 개인/외국인/기관 -->
        <div class="panel investor-panel">
          <h3>개인·외국인·기관</h3>

          <!-- 오늘 순매수 막대 -->
          <div class="investor-summary">
            <div class="inv-row" v-for="({ key, label, val }) in [
              { key:'individual', label:'개인', val: investors.individual },
              { key:'foreign', label:'외국인', val: investors.foreign },
              { key:'institution', label:'기관', val: investors.institution },
            ]" :key="key">
              <span class="inv-label">{{ label }}</span>
              <div class="inv-bar-track">
                <div
                  class="inv-bar"
                  :class="val >= 0 ? 'is-buy' : 'is-sell'"
                  :style="{
                    width: invBarWidth(val, Math.max(Math.abs(investors.individual), Math.abs(investors.foreign), Math.abs(investors.institution))) + '%',
                    [val >= 0 ? 'marginLeft' : 'marginRight']: val >= 0 ? '50%' : 'auto',
                  }"
                ></div>
              </div>
              <span class="inv-val" :class="val >= 0 ? 'is-up' : 'is-down'">{{ fmtInv(val) }}</span>
            </div>
          </div>

          <!-- 날짜별 히스토리 -->
          <div class="inv-history-head">
            <span>일자</span>
            <span>개인</span>
            <span>외국인</span>
            <span>기관</span>
          </div>

          <div class="inv-history-list">
            <div v-for="(row, i) in investorHistory" :key="i" class="inv-history-row">
              <span class="inv-date">{{ row.date }}</span>
              <span :class="row.individual >= 0 ? 'is-up' : 'is-down'">{{ fmtInv(row.individual) }}</span>
              <span :class="row.foreign >= 0 ? 'is-up' : 'is-down'">{{ fmtInv(row.foreign) }}</span>
              <span :class="row.institution >= 0 ? 'is-up' : 'is-down'">{{ fmtInv(row.institution) }}</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  </div>
</template>

<style scoped>
/* ===== 페이지 ===== */
.sd-page { display: flex; flex-direction: column; gap: 16px; }

/* ===== 헤더 ===== */
.sd-header { padding: 18px 22px 0; display: flex; flex-direction: column; gap: 14px; }

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  width: fit-content;
  padding: 5px 12px 5px 8px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.52);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
}
.back-btn:hover { background: rgba(255,255,255,0.78); color: var(--ink); }

.sd-header-body {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.sd-name-row { margin-bottom: 4px; }

.sd-name-price {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.sd-name-price h1 {
  font-size: clamp(22px, 3vw, 32px);
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -1px;
  margin: 0;
}

.sd-code {
  font-size: 14px;
  font-weight: 700;
  color: var(--faint);
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(0,0,0,0.05);
}

.watch-toggle-btn {
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(245,183,0,0.4);
  background: rgba(245,183,0,0.08);
  color: #c49000;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.18s;
}
.watch-toggle-btn:hover { background: rgba(245,183,0,0.16); }

.sd-price-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-top: 6px;
}

.sd-price {
  font-size: 32px;
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -1px;
}

.sd-change {
  font-size: 16px;
  font-weight: 900;
}

/* 키 메트릭 */
.sd-key-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 20px;
  padding: 12px 16px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.42);
  border: 1px solid var(--glass-border);
}

.metric { display: flex; flex-direction: column; gap: 2px; min-width: 80px; }
.metric span { font-size: 11px; font-weight: 700; color: var(--faint); }
.metric strong { font-size: 14px; font-weight: 900; color: var(--ink); }

/* 메인 탭 */
.sd-main-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--line);
  padding-bottom: 0;
}

.sd-main-tabs button {
  padding: 10px 18px;
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 0.16s, border-color 0.16s;
}

.sd-main-tabs button:hover { color: var(--ink); }
.sd-main-tabs button.is-active { color: var(--accent); border-bottom-color: var(--accent); }

/* ===== 3컬럼 그리드 ===== */
.sd-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) 220px 260px;
  gap: 14px;
  align-items: start;
}

.sd-col-left, .sd-col-mid, .sd-col-right {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ===== 차트 패널 ===== */
.chart-panel { padding: 16px; }

.chart-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.period-tabs {
  display: flex;
  gap: 2px;
  padding: 3px;
  border-radius: 999px;
  background: rgba(255,255,255,0.42);
  border: 1px solid var(--glass-border);
}

.period-tabs button {
  padding: 4px 12px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.period-tabs button.is-active {
  background: rgba(255,255,255,0.88);
  color: var(--ink);
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

.chart-tools {
  display: flex;
  gap: 10px;
}

.chart-tools span {
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.14s;
}

.chart-tools span:hover { background: rgba(255,255,255,0.5); color: var(--ink); }

/* 차트 영역 */
.chart-area-wrap {
  display: flex;
  gap: 0;
  position: relative;
}

.price-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 8px 8px 8px 0;
  width: 60px;
  flex-shrink: 0;
  text-align: right;
}

.price-axis span {
  font-size: 10px;
  font-weight: 700;
  color: var(--faint);
}

.chart-svg-wrap {
  flex: 1;
  position: relative;
  height: 200px;
  border-radius: var(--radius);
  overflow: hidden;
  background: rgba(255,255,255,0.28);
  border: 1px solid var(--glass-border);
}

.price-chart-svg { width: 100%; height: 100%; }

.current-price-label {
  position: absolute;
  right: 6px;
  top: 83px;
  font-size: 11px;
  font-weight: 900;
  color: var(--accent);
  background: rgba(49,93,255,0.1);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(49,93,255,0.25);
}

/* 시간 축 */
.time-axis {
  display: flex;
  justify-content: space-between;
  padding: 4px 60px 6px 68px;
  font-size: 10px;
  font-weight: 700;
  color: var(--faint);
}

/* 거래량 */
.volume-label-row {
  padding: 4px 68px 2px;
}

.volume-chart-wrap {
  height: 70px;
  margin-left: 68px;
  border-radius: var(--radius);
  overflow: hidden;
  background: rgba(255,255,255,0.22);
  border: 1px solid var(--glass-border);
}

.volume-svg { width: 100%; height: 100%; }

/* ===== 종목토론방 ===== */
.community-panel { padding: 16px; }

.community-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 10px;
}

.community-head h3 { font-size: 15px; font-weight: 900; color: var(--ink); margin: 3px 0 0; }

.text-btn {
  border: 0; background: transparent;
  color: var(--accent); font-size: 12px; font-weight: 900;
  cursor: pointer;
}

.community-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.community-tabs button {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.42);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.14s, color 0.14s;
}

.community-tabs button.is-active {
  background: rgba(49,93,255,0.1);
  border-color: rgba(49,93,255,0.22);
  color: var(--accent);
}

.community-list { display: flex; flex-direction: column; gap: 1px; }

.community-post {
  padding: 10px 8px;
  border-radius: var(--radius);
  transition: background 0.14s;
  cursor: pointer;
}

.community-post:hover { background: rgba(255,255,255,0.48); }

.post-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}

.post-author-row { display: flex; align-items: center; gap: 6px; }

.post-avatar {
  width: 24px; height: 24px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff; font-size: 11px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.post-user { font-size: 12px; font-weight: 900; color: var(--ink); }

.post-badge {
  font-size: 10px;
  font-weight: 900;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(125,78,232,0.12);
  color: var(--purple);
}

.post-time { font-size: 11px; font-weight: 700; color: var(--faint); }
.post-likes { font-size: 11px; font-weight: 700; color: var(--faint); }

.post-content {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.5;
  word-break: keep-all;
}

/* ===== 호가 패널 ===== */
.hoga-panel { padding: 14px; }

.hoga-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.hoga-head h3 { font-size: 14px; font-weight: 900; color: var(--ink); margin: 0; }

.hoga-meta-tabs { display: flex; gap: 4px; }

.hoga-meta-tabs button {
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.42);
  color: var(--muted);
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
}

.hoga-meta-tabs button.is-active {
  background: rgba(255,255,255,0.78);
  color: var(--ink);
}

.hoga-total-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 6px;
  background: rgba(255,255,255,0.35);
  border-radius: 6px;
  margin-bottom: 4px;
}

.hoga-total-row.ask { margin-bottom: 4px; }
.hoga-total-row.bid { margin-top: 4px; }

.hoga-total-label { font-size: 11px; font-weight: 700; color: var(--faint); }
.hoga-total-val { font-size: 11px; font-weight: 900; color: var(--ink); }

.hoga-row {
  display: grid;
  grid-template-columns: 60px auto auto;
  align-items: center;
  padding: 3px 4px;
  gap: 4px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.12s;
}

.hoga-row:hover { background: rgba(255,255,255,0.52); }

.ask-row { grid-template-columns: 60px 1fr auto; }
.bid-row { grid-template-columns: auto 1fr 60px; }

.hoga-bar-wrap {
  height: 16px;
  position: relative;
  overflow: hidden;
  border-radius: 3px;
  background: rgba(0,0,0,0.04);
}

.hoga-bar {
  position: absolute;
  top: 0;
  height: 100%;
  border-radius: 3px;
}

.ask-bar { right: 0; background: rgba(255,59,92,0.2); }
.bid-bar { left: 0; background: rgba(0,102,204,0.2); }

.hoga-price {
  font-size: 13px;
  font-weight: 900;
  text-align: center;
}

.ask-price { color: #FF3B5C; }
.bid-price { color: #0066CC; }

.hoga-qty {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  white-space: nowrap;
}

.hoga-asks .hoga-qty { text-align: right; }
.hoga-bids .hoga-qty { text-align: left; }

/* 현재가 중간 */
.hoga-current {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px;
  background: rgba(49,93,255,0.07);
  border-radius: 6px;
  border: 1px solid rgba(49,93,255,0.18);
  margin: 4px 0;
}

.hoga-current-price { font-size: 15px; font-weight: 900; color: var(--ink); }
.hoga-current-change { font-size: 12px; font-weight: 900; }

/* ===== 시세 패널 ===== */
.trade-feed-panel { padding: 14px; }

.trade-feed-panel h3 {
  font-size: 14px; font-weight: 900; color: var(--ink);
  margin: 0 0 10px;
}

.trade-feed-head, .trade-row {
  display: grid;
  grid-template-columns: 1fr auto auto auto;
  gap: 4px;
  padding: 4px 4px;
  font-size: 11px;
  font-weight: 700;
}

.trade-feed-head {
  color: var(--faint);
  border-bottom: 1px solid var(--line);
  padding-bottom: 5px;
  margin-bottom: 2px;
  text-align: right;
}

.trade-feed-list { display: flex; flex-direction: column; gap: 1px; max-height: 240px; overflow-y: auto; }

.trade-row { border-radius: 4px; }
.trade-row:hover { background: rgba(255,255,255,0.48); }

.trade-price { font-size: 12px; font-weight: 900; text-align: left; }
.trade-qty { font-size: 11px; font-weight: 700; color: var(--muted); text-align: right; }
.trade-rate { font-size: 11px; font-weight: 900; text-align: right; }
.trade-time { font-size: 10px; font-weight: 700; color: var(--faint); text-align: right; }

/* ===== 개인/외국인/기관 ===== */
.investor-panel { padding: 14px; }

.investor-panel h3 {
  font-size: 14px; font-weight: 900; color: var(--ink);
  margin: 0 0 12px;
}

.investor-summary { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }

.inv-row { display: flex; align-items: center; gap: 8px; }

.inv-label { font-size: 12px; font-weight: 900; color: var(--muted); width: 42px; flex-shrink: 0; }

.inv-bar-track {
  flex: 1;
  height: 8px;
  background: rgba(0,0,0,0.06);
  border-radius: 999px;
  position: relative;
  overflow: hidden;
}

.inv-bar {
  position: absolute;
  top: 0;
  height: 100%;
  border-radius: 999px;
}

.inv-bar.is-buy { background: #0066CC; left: 0; }
.inv-bar.is-sell { background: #FF3B5C; right: 0; }

.inv-val { font-size: 12px; font-weight: 900; width: 44px; text-align: right; flex-shrink: 0; }

/* 히스토리 */
.inv-history-head, .inv-history-row {
  display: grid;
  grid-template-columns: 60px 1fr 1fr 1fr;
  gap: 4px;
  padding: 5px 4px;
  font-size: 11px;
  font-weight: 700;
  text-align: right;
}

.inv-history-head {
  color: var(--faint);
  border-bottom: 1px solid var(--line);
  padding-bottom: 5px;
}

.inv-history-head span:first-child,
.inv-history-row span:first-child { text-align: left; }

.inv-history-list { display: flex; flex-direction: column; gap: 0; }

.inv-history-row { border-radius: 4px; transition: background 0.12s; }
.inv-history-row:hover { background: rgba(255,255,255,0.48); }

.inv-date { font-size: 11px; font-weight: 700; color: var(--muted); }

/* ===== 주문 패널 ===== */
.order-panel { padding: 16px; display: flex; flex-direction: column; gap: 12px; }

.order-panel h3 { font-size: 16px; font-weight: 900; color: var(--ink); margin: 2px 0 0; }

.order-side-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--glass-border);
}

.buy-tab, .sell-tab {
  padding: 10px;
  border: 0;
  background: rgba(255,255,255,0.42);
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
  color: var(--muted);
}

.buy-tab.is-active-buy {
  background: rgba(0,102,204,0.12);
  color: #0066CC;
}

.sell-tab.is-active-sell {
  background: rgba(255,59,92,0.10);
  color: #FF3B5C;
}

.order-type-row {
  display: flex;
  gap: 6px;
}

.order-type-btn {
  flex: 1;
  padding: 6px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.42);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
}

.order-type-btn.is-selected {
  background: rgba(255,255,255,0.88);
  color: var(--ink);
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

.order-field { display: flex; flex-direction: column; gap: 5px; }

.order-field span {
  font-size: 11px;
  font-weight: 900;
  color: var(--muted);
}

.order-input-row {
  display: flex;
  gap: 4px;
}

.order-field input, .market-price-display {
  flex: 1;
  height: 38px;
  padding: 0 10px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.55);
  color: var(--ink);
  font-size: 14px;
  font-weight: 900;
  outline: none;
  transition: border-color 0.18s;
}

.order-field input:focus { border-color: var(--accent); }

.market-price-display {
  display: flex;
  align-items: center;
  color: var(--muted);
  font-size: 13px;
}

.price-stepper {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.price-stepper button {
  width: 28px; height: 18px;
  border-radius: 4px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.52);
  color: var(--ink);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  line-height: 1;
  transition: background 0.14s;
}

.price-stepper button:hover { background: rgba(255,255,255,0.8); }

.qty-shortcuts {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
}

.qty-shortcuts button {
  padding: 6px 0;
  border-radius: 6px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.42);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.14s, color 0.14s;
}

.qty-shortcuts button:hover {
  background: rgba(255,255,255,0.72);
  color: var(--ink);
}

.order-summary {
  margin: 0;
  padding: 12px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.38);
  border: 1px solid var(--glass-border);
}

.order-summary > div { display: flex; justify-content: space-between; }
.order-summary dt { font-size: 12px; font-weight: 700; color: var(--muted); }
.order-summary dd { font-size: 13px; font-weight: 900; color: var(--ink); margin: 0; }

.order-submit-btn {
  width: 100%;
  height: 46px;
  border-radius: var(--radius);
  border: 0;
  font-size: 15px;
  font-weight: 900;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  transition: opacity 0.18s, transform 0.18s;
}

.order-submit-btn small {
  font-size: 10px;
  font-weight: 700;
  opacity: 0.72;
}

.order-submit-btn:hover { opacity: 0.88; transform: translateY(-1px); }

.order-submit-btn.is-buy {
  background: #0066CC;
  color: #fff;
  box-shadow: 0 4px 16px rgba(0,102,204,0.3);
}

.order-submit-btn.is-sell {
  background: #FF3B5C;
  color: #fff;
  box-shadow: 0 4px 16px rgba(255,59,92,0.3);
}

.fine-print {
  font-size: 11px;
  font-weight: 700;
  color: var(--faint);
  text-align: center;
  line-height: 1.6;
  margin: 0;
}

.fine-print code {
  font-family: monospace;
  font-size: 10px;
  background: rgba(0,0,0,0.06);
  padding: 1px 4px;
  border-radius: 3px;
  color: var(--muted);
}

/* ===== 일지 작성 패널 ===== */
.diary-inline-panel { padding: 16px; display: flex; flex-direction: column; gap: 10px; }

.diary-inline-head { display: flex; flex-direction: column; gap: 2px; }
.diary-inline-head h3 { font-size: 15px; font-weight: 900; color: var(--ink); margin: 0; }

.diary-inline-textarea {
  width: 100%;
  min-height: 100px;
  resize: vertical;
  padding: 10px 12px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.55);
  color: var(--ink);
  font-size: 13px;
  font-weight: 700;
  line-height: 1.6;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.18s;
  font-family: inherit;
}

.diary-inline-textarea:focus { border-color: var(--accent); }

.diary-inline-textarea::placeholder { color: var(--faint); font-weight: 700; }

.diary-inline-save-btn {
  width: 100%;
  height: 40px;
  border-radius: var(--radius);
  border: 0;
  background: rgba(49,93,255,0.12);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.18s, opacity 0.18s;
  border: 1px solid rgba(49,93,255,0.22);
}

.diary-inline-save-btn:hover:not(:disabled) { background: rgba(49,93,255,0.2); }
.diary-inline-save-btn:disabled { opacity: 0.4; cursor: default; }
.diary-inline-save-btn.is-saved { background: rgba(16,185,129,0.14); border-color: rgba(16,185,129,0.3); color: #059669; }

/* ===== 색상 ===== */
.is-up   { color: var(--positive); }
.is-down { color: var(--negative); }
.is-flat { color: var(--muted); }

/* ===== 반응형 ===== */
@media (max-width: 1280px) {
  .sd-grid { grid-template-columns: minmax(0, 1.5fr) 200px 240px; }
}

@media (max-width: 1000px) {
  .sd-grid { grid-template-columns: 1fr 1fr; }
  .sd-col-left { grid-column: 1 / -1; }
}

@media (max-width: 700px) {
  .sd-grid { grid-template-columns: 1fr; }
  .sd-header-body { flex-direction: column; }
}
</style>
