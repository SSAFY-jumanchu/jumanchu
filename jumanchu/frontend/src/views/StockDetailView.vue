<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  fetchStockDetail,
  fetchStockPrice,
  fetchStockChart,
  fetchStockFinancials,
  fetchStockPosts,
  fetchStockOrderbook,
} from '../api/stocks'
import { createOrder, fetchBalance, fetchHoldingDetail } from '../api/portfolio'
import { fetchStockNews } from '../api/news'
import { addWatchlist, removeWatchlist } from '../api/recommend'
import { errMsg } from '../api/client'
import { useRecentStocksStore } from '../stores/recentStocks'

const router = useRouter()
const route = useRoute()
const recentStore = useRecentStocksStore()

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

const loading = ref(false)
const loadError = ref('')

// 원(KRW) 시가총액 → "237.1조" / "5,420억" 형태로
function fmtMarketCap(won) {
  if (!won) return ''
  const n = Number(won)
  if (n >= 1e12) return (n / 1e12).toFixed(1) + '조'
  if (n >= 1e8) return Math.round(n / 1e8).toLocaleString('ko-KR') + '억'
  return n.toLocaleString('ko-KR')
}

async function loadStock(code) {
  loading.value = true
  loadError.value = ''
  try {
    // 식별·메타 + 실시간 현재가(KIS 라이브)를 동시에
    const [detail, priceRes] = await Promise.all([
      fetchStockDetail(code),
      fetchStockPrice(code).catch(() => null), // 가격은 실패해도 메타는 표시
    ])
    const d = detail.stock
    const p = priceRes?.price
    stock.value = {
      ...stock.value,
      code: d.code,
      name: d.name,
      market: d.market,
      sector: d.sector || stock.value.sector,
      currency: d.currency,
      marketCap: fmtMarketCap(d.market_cap) || stock.value.marketCap,
      ...(p && {
        price: Number(p.current),
        open: Number(p.open),
        high: Number(p.high),
        low: Number(p.low),
        prevClose: Number(p.prev_close),
        volume: Number(p.volume),
      }),
    }
    // 종목정보 탭 — BE 메타로 채움(없는 필드는 템플릿에서 숨김)
    stockInfo.value = {
      ceo: d.ceo_name || '',
      listedDate: d.listed_at ? String(d.listed_at).slice(0, 10).replace(/-/g, '.') : '',
      desc: d.description || '',
      homepage: d.homepage_url || '',
      employees: d.employee_count ?? null,
      industry: d.industry || d.sector || '',
    }
    isWatched.value = !!d.is_in_watchlist // 관심종목 상태(BE UserLikedStock 기준)
    // 주문/시뮬 기본가를 실시간 현재가로 맞춤
    if (p) {
      orderPrice.value = Number(p.current)
      addPrice.value = Number(p.current)
    }
  } catch (e) {
    loadError.value = errMsg(e)
  } finally {
    loading.value = false
  }
}

// ===== 관심종목 토글 (BE /watchlist/ — UserLikedStock) =====
const isWatched = ref(false)
const watching = ref(false)
async function toggleWatch() {
  if (watching.value) return
  watching.value = true
  const next = !isWatched.value
  isWatched.value = next // 낙관적 토글
  try {
    if (next) await addWatchlist(stock.value.code)
    else await removeWatchlist(stock.value.code)
  } catch {
    isWatched.value = !next // 실패(비로그인 401 등) 시 롤백 — 별표 원복으로 신호
  } finally {
    watching.value = false
  }
}

const change = computed(() => stock.value.price - stock.value.prevClose)
const changeRate = computed(() =>
  stock.value.prevClose ? (change.value / stock.value.prevClose) * 100 : 0,
)

// 통화 심볼 (KRW=₩ / USD=$) — 해외 종목 원화 오표기 방지
const curSym = computed(() => (stock.value.currency === 'USD' ? '$' : '₩'))

// ===== 헤더 가격 달러/원화 토글 =====
const USD_KRW = 1500   // 백엔드 USD_KRW_RATE와 동일 (TODO: 라이브 환율)
const showAltCcy = ref(false)   // false=종목 원통화, true=반대 통화로 환산 표시
const nativeCcy = computed(() => (stock.value.currency === 'USD' ? 'USD' : 'KRW'))
// 토글은 미국 주식에서만 — 국내 주식은 항상 원(₩)으로 표시
const dispCcy = computed(() => (nativeCcy.value === 'USD' && showAltCcy.value ? 'KRW' : nativeCcy.value))
// 종목 원통화 값 v를 현재 표시 통화로 환산 + 심볼 포함 포맷
function fmtCcy(v) {
  let c = v
  if (dispCcy.value !== nativeCcy.value) c = nativeCcy.value === 'USD' ? v * USD_KRW : v / USD_KRW
  if (dispCcy.value === 'KRW') return '₩' + Math.round(c).toLocaleString('ko-KR')
  return '$' + Number(c).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// ISO 일시 → 상대시간("3분 전" 등)
function relTime(iso) {
  if (!iso) return ''
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return ''
  const diff = Math.max(0, Date.now() - t)
  const m = Math.floor(diff / 60000)
  if (m < 1) return '방금'
  if (m < 60) return `${m}분 전`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}시간 전`
  return `${Math.floor(h / 24)}일 전`
}

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

const volumeData = ref([
  85, 72, 80, 90, 65, 55, 45, 40, 38, 35, 32, 30,
  28, 30, 32, 35, 38, 42, 45, 40, 35, 30, 28, 25,
  22, 20, 18, 20, 22, 25, 28, 25, 22, 20, 22, 25,
  28, 32, 35, 32, 28, 30, 35, 40, 45, 42, 40, 38,
  42, 40, 45, 50, 55, 50, 45, 50, 55, 60, 55, 50,
  55, 60, 65, 60, 55, 50, 55, 60, 55, 52, 50, 55,
  70, 80, 85, 90, 95, 100,
])

// SVG 라인 차트 경로 계산 (last = 추세선 마지막 점 좌표)
// padR로 우측에 살짝 여백을 둬 라인 끝이 가장자리에 붙지 않게 하고, 끝점(last)을 점과 공유한다.
function buildPath(prices, w, h, padT = 36, padB = 16, padL = 0, padR = 48) {
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const n = prices.length
  const innerW = w - padL - padR
  const pts = prices.map((p, i) => {
    const x = padL + (n > 1 ? (i / (n - 1)) * innerW : innerW)
    const y = padT + (1 - (p - min) / range) * (h - padT - padB)
    return { x, y }
  })
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  const last = pts[pts.length - 1] || { x: w - padR, y: h / 2 }
  return { line, last }
}

const chartPath = computed(() => buildPath(intradayPrices.value, 560, 200))
// 현재가 점 — 추세선 마지막 점 좌표 그대로 사용 (라인 끝과 정확히 일치)
const chartDot = computed(() => ({ x: chartPath.value.last.x, y: chartPath.value.last.y }))
// 현재가 라벨 가로 위치 — 점 x를 %로 (translateX(-50%)로 점 중앙 정렬)
const labelLeft = computed(() => (chartDot.value.x / 560) * 100)
// 주가 태그는 평상시 숨김 — 점에 마우스 호버 시에만 표시 (항상 점 위로 — 커서 가림 방지)
const showPriceLabel = ref(false)
const maxVolume = computed(() => Math.max(...volumeData.value, 1))

// ===== 차트 기간 탭 =====
const chartPeriods = ['1분', '5분', '일', '주', '월']
const selectedPeriod = ref('일')

// ===== 차트 축 (종목·기간에 맞춰 동적 생성) =====
function fmtAxisPrice(v) {
  if (stock.value.currency === 'USD') return v >= 1000 ? Math.round(v).toLocaleString('en-US') : v.toFixed(2)
  return Math.round(v).toLocaleString('ko-KR')
}
// Y축: 현재 차트 데이터의 max→min 5단계
const priceAxis = computed(() => {
  const prices = intradayPrices.value
  if (!prices.length) return []
  const max = Math.max(...prices)
  const min = Math.min(...prices)
  const N = 5
  return Array.from({ length: N }, (_, i) => fmtAxisPrice(max - (i / (N - 1)) * (max - min)))
})
// X축: 분봉/일(장중)=시간, 주/월=날짜. 시장(USD/KRW)별 장 운영시간 반영
const timeAxis = computed(() => {
  const label = selectedPeriod.value
  const N = 7
  if (label === '1분' || label === '5분' || label === '일') {
    const [sH, sM, eH, eM] = stock.value.currency === 'USD' ? [9, 30, 16, 0] : [9, 0, 15, 30]
    const start = sH * 60 + sM
    const end = eH * 60 + eM
    return Array.from({ length: N }, (_, i) => {
      const m = Math.round(start + (i / (N - 1)) * (end - start))
      return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, '0')}`
    })
  }
  const days = label === '주' ? 7 : 30
  const now = new Date()
  return Array.from({ length: N }, (_, i) => {
    const d = new Date(now)
    d.setDate(now.getDate() - Math.round((1 - i / (N - 1)) * days))
    return `${d.getMonth() + 1}/${d.getDate()}`
  })
})

// ===== 상단 탭 =====
const mainTabs = ['종목 홈', '종목정보', '뉴스', '커뮤니티']
const selectedTab = ref('종목 홈')

// ===== 호가 데이터 (실데이터: GET /stocks/:code/orderbook/ — KIS 10호가) =====
const asks = ref([])   // 화면 표시용: 높은 가격이 위 → 낮은 가격이 아래 (내림차순)
const bids = ref([])   // 높은 가격이 위 → 낮은 가격이 아래 (내림차순)
const totalAskQty = ref(0)
const totalBidQty = ref(0)
const obMarketOpen = ref(true)
const obLoaded = ref(false)

const maxAskQty = computed(() => Math.max(...asks.value.map(a => a.qty), 1))
const maxBidQty = computed(() => Math.max(...bids.value.map(b => b.qty), 1))
const totalAsk = computed(() => totalAskQty.value || asks.value.reduce((s, a) => s + a.qty, 0))
const totalBid = computed(() => totalBidQty.value || bids.value.reduce((s, b) => s + b.qty, 0))
const hogaEmpty = computed(() => obLoaded.value && asks.value.length === 0 && bids.value.length === 0)

async function loadOrderbook(code) {
  try {
    const { orderbook } = await fetchStockOrderbook(code)
    const lv = (e) => ({ price: Number(e.price), qty: Number(e.quantity) })
    const valid = (e) => e.price > 0
    // KIS asks = 최저가→최고가 → 역순으로 (높은 가격 위, 낮은 가격 아래)
    asks.value = (orderbook.asks || []).map(lv).filter(valid).reverse()
    // KIS bids = 최고가→최저가 → 그대로 (높은 가격 위)
    bids.value = (orderbook.bids || []).map(lv).filter(valid)
    totalAskQty.value = Number(orderbook.total_ask_quantity || 0)
    totalBidQty.value = Number(orderbook.total_bid_quantity || 0)
    obMarketOpen.value = orderbook.is_market_open !== false
  } catch {
    // KIS 오류 등 → 빈 상태 표시
  } finally {
    obLoaded.value = true
  }
}

// ===== 시세 (체결 내역) =====
// 전용 체결(tick) API가 없어 가장 세밀한 실데이터인 1분봉으로 구성:
// 체결가=종가, 체결량=분 거래량, 등락=전일대비, 시각=캔들 시각, 최신순.
const trades = ref([])
const tradesLoaded = ref(false)

function fmtTradeTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', hour12: false })
}

async function loadTrades(code) {
  try {
    const { candles = [] } = await fetchStockChart(code, { period: '1d', interval: '1m' })
    const prev = Number(stock.value.prevClose) || 0
    const rows = candles.map((c) => {
      const price = Number(c.close)
      const rate = prev ? ((price - prev) / prev) * 100 : 0
      return { price, qty: Number(c.volume), rate, time: fmtTradeTime(c.time), side: rate >= 0 ? 'up' : 'down' }
    })
    trades.value = rows.reverse().slice(0, 30)   // 최신순 최근 30건
  } catch {
    // 분봉(KIS) 실패 등 → 빈 목록
  } finally {
    tradesLoaded.value = true
  }
}

// ===== 종토방 커뮤니티 (BE /posts/ 응답으로 채움 — 목업 fallback 제거) =====
const communityPosts = ref([])

// ===== 보유 현황 (시뮬 프리필 · 매도 최대수량 산출용) =====
const holding = ref(null) // { quantity, average_price } | null
async function loadHolding(code) {
  try {
    const { holding: h } = await fetchHoldingDetail(code)
    if (h && Number(h.quantity) > 0) {
      holding.value = h
      holdQty.value = Number(h.quantity)
      holdAvg.value = Math.round(Number(h.average_price))
    } else {
      holding.value = null
    }
  } catch {
    holding.value = null // 미보유/비로그인 → 0으로
  }
}

// ===== 물타기(평단) 시뮬레이션 (보유 연동) =====
const avgSide = ref('BUY') // BUY=매수 물타기, SELL=매도
const holdQty = ref(0)
const holdAvg = ref(0)
const addPrice = ref(0)
const addQty = ref(0)

const simResult = computed(() => {
  const hQty = Math.max(0, holdQty.value || 0)
  const hAvg = Math.max(0, holdAvg.value || 0)
  const aQty = Math.max(0, addQty.value || 0)
  const aPrice = Math.max(0, addPrice.value || 0)
  const cur = stock.value.price
  if (avgSide.value === 'BUY') {
    const totalQty = hQty + aQty
    const newAvg = totalQty ? (hQty * hAvg + aQty * aPrice) / totalQty : 0
    const pnl = (cur - newAvg) * totalQty
    const pnlPct = newAvg ? ((cur - newAvg) / newAvg) * 100 : 0
    return { totalQty, newAvg, pnl, pnlPct }
  }
  const totalQty = Math.max(0, hQty - aQty)
  const realized = Math.min(aQty, hQty) * (aPrice - hAvg)
  return { totalQty, newAvg: hAvg, realized }
})

// ===== 주문 패널 =====
const orderSide = ref('BUY')
const orderType = ref('limit')   // limit | market
const orderPrice = ref(317000)
const orderQty = ref(0)
const orderTotal = computed(() => orderPrice.value * orderQty.value)
const orderFee = computed(() => orderTotal.value * 0.00015)

// 가격 증감 단위 (USD는 0.5달러, KRW는 500원)
const priceStep = computed(() => (stock.value.currency === 'USD' ? 0.5 : 500))
function bumpPrice(dir) {
  const next = orderPrice.value + dir * priceStep.value
  orderPrice.value = Math.max(0, Math.round(next * 100) / 100)
}
function selectLimit() { orderType.value = 'limit' }
// 시장가 선택 시 현재가에서 시작 → +/-로 조정 가능
function selectMarket() {
  orderType.value = 'market'
  orderPrice.value = Math.round((Number(stock.value.price) || 0) * 100) / 100
}

const balance = ref(10000000) // 기본값 — /portfolio/balance/ 응답으로 교체
const ordering = ref(false)
const orderMsg = ref(null) // { ok: boolean, text: string }

function setQtyPct(pct) {
  if (orderSide.value === 'SELL') {
    // 매도: 보유 수량 기준
    const owned = holding.value ? Number(holding.value.quantity) : 0
    orderQty.value = Math.floor(owned * pct)
  } else {
    // 매수: 잔고 기준
    orderQty.value = orderPrice.value ? Math.floor((balance.value * pct) / orderPrice.value) : 0
  }
}

// 가상계좌 잔고 로드 (GET /portfolio/balance/)
async function loadBalance() {
  try {
    const { account } = await fetchBalance()
    if (account) balance.value = Number(account.balance)
  } catch {
    // 비로그인 등 → 기본값 유지
  }
}

// 실제 매매 실행 (POST /orders/ — 현재가 시장체결, 수량·방향만 전송)
async function submitOrder() {
  if (orderQty.value < 1 || ordering.value) return
  orderMsg.value = null
  // 매수 잔고 사전 체크(UX) — 최종 검증은 서버
  const cost = orderTotal.value + orderFee.value
  if (orderSide.value === 'BUY' && cost > balance.value) {
    orderMsg.value = { ok: false, text: '잔고가 부족합니다.' }
    return
  }
  ordering.value = true
  try {
    const res = await createOrder({
      stock_code: stock.value.code,
      side: orderSide.value,
      quantity: orderQty.value,
      idempotency_key: `ord-${stock.value.code}-${orderSide.value}-${Date.now()}`,
    })
    balance.value = Number(res.balance_after)
    orderMsg.value = {
      ok: true,
      text: `${orderSide.value === 'BUY' ? '매수' : '매도'} 체결 완료 (잔고 ${curSym.value}${fmt(balance.value)})`,
      cta: true, // 체결 후 매매일기 작성 유도(BE order_id 핸드셰이크 — TradingDiary가 미작성 주문 노출)
    }
    orderQty.value = 0
    loadHolding(stock.value.code) // 체결 후 보유/시뮬 갱신
  } catch (e) {
    orderMsg.value = { ok: false, text: errMsg(e) }
  } finally {
    ordering.value = false
  }
}

// ===== 종목정보 탭 데이터 (BE detail로 채움 — 하드코딩 제거) =====
const stockInfo = ref({
  ceo: '', listedDate: '', desc: '', homepage: '', employees: null, industry: '',
})

const valuation = ref([
  { k: 'PER', v: '14.2배' },
  { k: 'PSR', v: '1.4배' },
  { k: 'PBR', v: '1.18배' },
])
const earningsMetrics = ref([
  { k: 'EPS', v: '22,324원' },
  { k: 'BPS', v: '268,500원' },
  { k: 'ROE', v: '8.57%' },
])
const dividendMetrics = ref([
  { k: '횟수', v: '4번' },
  { k: '주당 배당금', v: '1,444원' },
  { k: '수익률', v: '1.8%' },
])
const financials = ref([
  { k: '부채비율', v: '24.8%' },
  { k: '유동비율', v: '258.3%' },
  { k: '이자보상비율', v: '3,210%' },
])

const profitDesc = '2026년 1분기 삼성전자의 순이익은 11조원으로 직전 분기 대비 +10.0% 더 높아요.'
const profitability = [
  { label: '24 9월', revenue: 79, profit: 9, margin: 11.4 },
  { label: '24 12월', revenue: 75, profit: 7, margin: 9.3 },
  { label: '25 3월', revenue: 71, profit: 6, margin: 8.5 },
  { label: '25 6월', revenue: 74, profit: 8, margin: 10.8 },
  { label: '25 9월', revenue: 82, profit: 10, margin: 12.2 },
  { label: '25 12월', revenue: 86, profit: 11, margin: 12.8 },
]
const profChart = computed(() => {
  const data = profitability
  const maxRev = Math.max(...data.map(d => d.revenue))
  const maxMargin = Math.max(...data.map(d => d.margin))
  const W = 600, base = 175, top = 20
  const groupW = W / data.length
  const barW = groupW * 0.24
  const span = base - top
  const bars = data.map((d, i) => {
    const cx = i * groupW + groupW / 2
    const revH = (d.revenue / maxRev) * span
    const profH = (d.profit / maxRev) * span
    return {
      label: d.label,
      revX: cx - barW - 2, revY: base - revH, revH,
      profX: cx + 2, profY: base - profH, profH,
      barW,
      lineX: cx, lineY: base - (d.margin / maxMargin) * span,
    }
  })
  const linePath = bars.map((b, i) => `${i === 0 ? 'M' : 'L'}${b.lineX.toFixed(1)},${b.lineY.toFixed(1)}`).join(' ')
  return { bars, linePath }
})

// 동종업계 순위·예상 목표주가는 BE 데이터 소스 없음 → 비우고 템플릿에서 숨김(하드코딩 제거)
const peers = ref([])
const targetPrice = ref(null)

// ===== 뉴스 탭 (BE /news/stocks/{code}/ 연동 — 목업 제거) =====
const stockNews = ref([])
async function loadNews(code) {
  try {
    const { items = [] } = await fetchStockNews(code)
    stockNews.value = items.map((n) => ({
      title: n.title,
      source: n.source || '',
      url: n.url || '',
      time: relTime(n.published_at),
    }))
  } catch {
    stockNews.value = []
  }
}

// ===== 커뮤니티 탭 (피드) =====
const communitySort = ref('인기순')
const newPostText = ref('')
const communityFeed = ref([
  { author: '노나먹어보자', avatar: '노', title: '210대 뚫으면 털어야겠다', likes: 11, comments: 1, reposts: 0, time: '3분', followed: false },
  { author: '고전적인고릴라3', avatar: '고', title: '와 아직도 마이나스다^^', likes: 8, comments: 4, reposts: 0, time: '4분', followed: false },
  { author: 'Rubyruby777', avatar: 'R', badge: '1억대 자산가', title: '200 고고', likes: 5, comments: 0, reposts: 0, time: '7분', followed: false },
  { author: '마멜조아', avatar: '마', title: '파멸적 상승 ㄱㄱ', sub: '샌디스크처럼 ㄱㄱ', likes: 5, comments: 0, reposts: 0, time: '4분', followed: false },
  { author: '오니돌마미', avatar: '오', title: '삼전기 상치는 거 보신 적 있으신가요?', sub: '보고 싶어서 ㅎㅎ', likes: 4, comments: 0, reposts: 0, time: '6분', followed: false },
  { author: '존버왕', avatar: '존', title: '7만전자 가즈아 🚀', likes: 9, comments: 3, reposts: 1, time: '12분', followed: false },
  { author: '반도체신봉자', avatar: '반', badge: '고수', title: 'HBM 매출 본격화되면 우상향 각이에요', sub: '실적 발표가 기대됩니다', likes: 21, comments: 6, reposts: 2, time: '20분', followed: false },
])
function addPost() {
  const text = newPostText.value.trim()
  if (!text) return
  communityFeed.value.unshift({ author: '김주만', avatar: '김', title: text, likes: 0, comments: 0, reposts: 0, time: '방금', followed: false })
  newPostText.value = ''
}
const popularPosts = [
  { title: 'HBM 양산 확대...삼성도 수혜 받을까?', likes: 34 },
  { title: '삼성전자 vs SK하이닉스 비교 분석', likes: 21 },
  { title: '배당주로 삼성전자 모아가는 중입니다', likes: 18 },
]

// ===== 유틸 =====
function fmt(v) { return v.toLocaleString('ko-KR') }
function fmtCompact(v) {
  if (v >= 100000000) return `${(v / 100000000).toFixed(1)}억`
  if (v >= 10000) return `${(v / 10000).toFixed(1)}만`
  return v.toLocaleString()
}

// ===== 차트·재무·종토방 실데이터 로딩 =====
const pct = (v, digits = 1) => (v == null ? null : (v * 100).toFixed(digits) + '%')

// 기간 탭 → period/interval.
// 1분·5분·일 = 오늘 장중(분봉, period=1d), 주 = 최근 7일·월 = 최근 30일 일봉(DB StockPrice).
const CHART_PARAM = {
  '1분': { period: '1d', interval: '1m' },
  '5분': { period: '1d', interval: '5m' },
  '일': { period: '1d', interval: '15m' },   // 하루(오늘) 기준 장중 추세
  '주': { period: '1w', interval: '1d' },     // 최근 7일 일봉
  '월': { period: '1m', interval: '1d' },     // 최근 30일 일봉
}

// 실데이터(캔들)가 없을 때 기간별로 모양이 다른 추세선을 합성한다.
// 기간마다 포인트 수·변동성·시드가 달라 그래프가 겹치지 않으며, 마지막 값은 현재가로 수렴시켜 점/라벨과 맞춘다.
function syntheticSeries(label) {
  const cfg = {
    '1분': { n: 200, vol: 0.0010 },   // 가장 상세한 장중
    '5분': { n: 80, vol: 0.0022 },
    '일': { n: 40, vol: 0.0045 },     // 하루 장중
    '주': { n: 18, vol: 0.011 },      // 주간
    '월': { n: 30, vol: 0.021 },      // 30일
  }[label] || { n: 60, vol: 0.005 }
  const base = Number(stock.value.price) || 100
  let seed = 0
  for (const ch of String(stock.value.code) + label) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0
  const rand = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff }
  const raw = []
  const volumes = []
  let p = base
  for (let i = 0; i < cfg.n; i++) {
    p *= 1 + (rand() - 0.5) * 2 * cfg.vol
    raw.push(p)
    volumes.push(Math.round(20 + rand() * 80))
  }
  const adj = base / raw[raw.length - 1]   // 마지막 값을 현재가에 맞춤
  return { prices: raw.map((v) => Math.round(v * adj)), volumes }
}

async function loadChart(code, label) {
  const p = CHART_PARAM[label] || CHART_PARAM['일']
  try {
    const { candles = [] } = await fetchStockChart(code, p)
    if (candles.length) {
      intradayPrices.value = candles.map((c) => Number(c.close))
      volumeData.value = candles.map((c) => Number(c.volume))
      return
    }
  } catch {
    // 실패 → 아래 합성 폴백
  }
  // 캔들 없음(분봉 KIS 미가동·일봉 미적재 등) → 기간별로 다른 추세선을 합성해 표시
  const { prices, volumes } = syntheticSeries(label)
  intradayPrices.value = prices
  volumeData.value = volumes
}

async function loadFinancials(code) {
  try {
    const data = await fetchStockFinancials(code)
    const ind = data.indicator || {}
    const sum = (data.summaries && data.summaries[0]) || {}
    // 헤더 지표
    stock.value = {
      ...stock.value,
      per: ind.per ?? stock.value.per,
      pbr: ind.pbr ?? stock.value.pbr,
      eps: ind.eps ?? stock.value.eps,
      roe: ind.roe != null ? +(ind.roe * 100).toFixed(2) : stock.value.roe,
      beta: ind.beta ?? stock.value.beta,
      high52w: ind.high_52w ?? stock.value.high52w,
      low52w: ind.low_52w ?? stock.value.low52w,
    }
    // 종목정보 탭 지표 칩 (응답에 있는 항목만)
    const val = []
    if (ind.per != null) val.push({ k: 'PER', v: `${ind.per}배` })
    if (ind.pbr != null) val.push({ k: 'PBR', v: `${ind.pbr}배` })
    if (val.length) valuation.value = val

    const earn = []
    if (ind.eps != null) earn.push({ k: 'EPS', v: `${fmt(ind.eps)}원` })
    if (ind.roe != null) earn.push({ k: 'ROE', v: pct(ind.roe, 2) })
    if (ind.roa != null) earn.push({ k: 'ROA', v: pct(ind.roa, 2) })
    if (earn.length) earningsMetrics.value = earn

    const fin = []
    if (sum.debt_ratio != null) fin.push({ k: '부채비율', v: pct(sum.debt_ratio) })
    if (sum.current_ratio != null) fin.push({ k: '유동비율', v: pct(sum.current_ratio) })
    if (sum.operating_margin != null) fin.push({ k: '영업이익률', v: pct(sum.operating_margin) })
    if (fin.length) financials.value = fin

    if (sum.payout_ratio != null) dividendMetrics.value = [{ k: '배당성향', v: pct(sum.payout_ratio) }]
  } catch {
    // 재무 없으면 목업 유지
  }
}

async function loadCommunity(code) {
  try {
    const { items = [] } = await fetchStockPosts(code)
    // 항상 실데이터로 교체(0건이면 빈 목록 — 가짜 노출 방지). 글 본문은 미제공이라 title 사용.
    communityPosts.value = items.map((p) => ({
      id: p.id,
      user: p.author_nickname || '익명',
      badge: null,
      time: relTime(p.created_at),
      content: p.title,
      likes: p.like_count ?? 0,
    }))
  } catch {
    communityPosts.value = []
  }
}

// 기간 탭 변경 시 차트만 재로딩
watch(selectedPeriod, (label) => loadChart(stock.value.code, label))

onMounted(async () => {
  const code = route.params.code || '005930'
  await loadStock(code)
  // 실데이터 로드 성공 시에만 최근 조회 종목으로 기록 (실패 시 목업 기록 방지)
  if (!loadError.value) {
    recentStore.visit({ code: stock.value.code, name: stock.value.name, market: stock.value.market })
  }
  loadChart(code, selectedPeriod.value)
  loadOrderbook(code)
  loadTrades(code)
  loadFinancials(code)
  loadCommunity(code)
  loadNews(code)
  loadHolding(code)
  loadBalance()
})
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
            <button
              class="watch-toggle-btn"
              :class="{ on: isWatched }"
              type="button"
              :disabled="watching"
              @click="toggleWatch"
            >{{ isWatched ? '★ 관심종목' : '☆ 관심종목 추가' }}</button>
          </div>
          <div class="sd-price-row">
            <strong class="sd-price">{{ fmtCcy(stock.price) }}</strong>
            <span class="sd-change" :class="change >= 0 ? 'is-up' : 'is-down'">
              {{ change >= 0 ? '+' : '-' }}{{ fmtCcy(Math.abs(change)) }} ({{ change >= 0 ? '+' : '' }}{{ changeRate.toFixed(2) }}%)
            </span>
            <div v-if="nativeCcy === 'USD'" class="ccy-toggle" role="group" aria-label="통화 표시 전환">
              <button type="button" :class="{ 'is-active': !showAltCcy }" @click="showAltCcy = false">$</button>
              <button type="button" :class="{ 'is-active': showAltCcy }" @click="showAltCcy = true">원</button>
            </div>
          </div>
        </div>

        <!-- 우: 키 메트릭 -->
        <div class="sd-key-metrics">
          <div class="metric"><span>시가</span><strong>{{ curSym }}{{ fmt(stock.open) }}</strong></div>
          <div class="metric"><span>고가</span><strong class="is-up">{{ curSym }}{{ fmt(stock.high) }}</strong></div>
          <div class="metric"><span>저가</span><strong class="is-down">{{ curSym }}{{ fmt(stock.low) }}</strong></div>
          <div class="metric"><span>거래량</span><strong>{{ fmtCompact(stock.volume) }}</strong></div>
          <div class="metric"><span>PER</span><strong>{{ stock.per }}</strong></div>
          <div class="metric"><span>시가총액</span><strong>{{ stock.marketCap }}</strong></div>
          <div class="metric"><span>52주 최고</span><strong>{{ curSym }}{{ fmt(stock.high52w) }}</strong></div>
          <div class="metric"><span>52주 최저</span><strong>{{ curSym }}{{ fmt(stock.low52w) }}</strong></div>
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

    <!-- ===== 메인 그리드 (탭에 따라 전환) ===== -->
    <div class="sd-grid" :class="{
      'is-info': selectedTab === '종목정보' || selectedTab === '뉴스',
      'is-community': selectedTab === '커뮤니티',
    }">

      <!-- ===== 종목 홈: 차트/호가/시세 ===== -->
      <template v-if="selectedTab === '종목 홈'">
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
          </div>

          <!-- 가격 축 레이블 -->
          <div class="chart-area-wrap">
            <!-- 가격 라인 차트 -->
            <div class="chart-svg-wrap">
              <svg viewBox="0 0 560 200" preserveAspectRatio="none" class="price-chart-svg">
                <!-- 그리드 -->
                <line v-for="y in [40, 80, 120, 160]" :key="y" x1="0" :y1="y" x2="560" :y2="y"
                  stroke="rgba(180,200,255,0.25)" stroke-width="1" stroke-dasharray="4 4" />
                <!-- 현재가 수평선 (추세선 끝점 높이에 맞춤) -->
                <line x1="0" :y1="chartDot.y" x2="560" :y2="chartDot.y"
                  stroke="rgba(var(--accent-rgb),0.5)" stroke-width="1" stroke-dasharray="6 3" />
                <!-- 라인 -->
                <path :d="chartPath.line" fill="none" stroke="var(--accent)" stroke-width="2"
                  stroke-linecap="round" stroke-linejoin="round" />
              </svg>

              <!-- 현재가 점 — HTML 오버레이(고정 px 정원). SVG는 preserveAspectRatio=none이라 내부 도형이 눌려서 밖으로 뺌 -->
              <div
                class="chart-dot-hit"
                :style="{ left: labelLeft + '%', top: chartDot.y + 'px' }"
                @mouseenter="showPriceLabel = true"
                @mouseleave="showPriceLabel = false"
              >
                <span class="chart-dot"></span>
              </div>

              <!-- 현재가 라벨 — 평상시 숨김, 점 호버 시에만 표시 -->
              <div
                v-show="showPriceLabel"
                class="current-price-label"
                :style="{ left: labelLeft + '%', top: chartDot.y + 'px' }"
              >{{ curSym }}{{ fmt(stock.price) }}</div>
            </div>

            <!-- 가격 축 (그래프 오른쪽) -->
            <div class="price-axis">
              <span v-for="(p, i) in priceAxis" :key="i">{{ p }}</span>
            </div>
          </div>

          <!-- 시간 축 -->
          <div class="time-axis">
            <span v-for="(t, i) in timeAxis" :key="i">{{ t }}</span>
          </div>

          <!-- 거래량 차트 -->
          <div class="volume-label-row">
            <span class="eyebrow">거래량</span>
          </div>
          <div class="volume-chart-wrap">
            <svg viewBox="0 0 560 70" preserveAspectRatio="none" class="volume-svg">
              <rect
                v-for="(v, i) in volumeData"
                :key="i"
                :x="(i / volumeData.length) * 560"
                :width="(560 / volumeData.length) - 1"
                :y="70 - (v / maxVolume) * 68"
                :height="(v / maxVolume) * 68"
                :fill="intradayPrices[i] >= (intradayPrices[i-1] ?? intradayPrices[i]) ? 'rgba(var(--accent-rgb),0.5)' : 'rgba(255,59,92,0.45)'"
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
            <div v-for="post in communityPosts" :key="post.id" class="community-post">
              <div class="post-head">
                <div class="post-author-row">
                  <div class="post-avatar">{{ post.user.slice(0, 1) }}</div>
                  <strong class="post-user">{{ post.user }}</strong>
                  <span v-if="post.badge" class="post-badge">{{ post.badge }}</span>
                  <span class="post-time">{{ post.time }}</span>
                </div>
                <span class="post-likes">♡ {{ post.likes }}</span>
              </div>
              <p class="post-content">{{ post.content }}</p>
            </div>
            <p v-if="!communityPosts.length" class="community-empty">아직 종목토론방 글이 없어요.</p>
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
            </div>
          </div>

          <!-- 매도 총잔량 -->
          <div class="hoga-total-row ask">
            <span class="hoga-total-label">매도잔량</span>
            <span class="hoga-total-val">{{ fmt(totalAsk) }}</span>
          </div>

          <!-- 매도 호가 (높은 가격이 위, 낮은 가격이 아래 — 현재가와 가까운 호가가 맨 아래) -->
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

          <!-- 호가 없음(장 마감/미제공) -->
          <p v-if="hogaEmpty" class="hoga-empty">
            {{ obMarketOpen ? '실시간 호가 정보가 없어요.' : '장 마감 — 호가가 제공되지 않아요.' }}
          </p>

          <!-- 현재가 -->
          <div class="hoga-current">
            <span class="hoga-current-price">{{ curSym }}{{ fmt(stock.price) }}</span>
            <span class="hoga-current-change" :class="change >= 0 ? 'is-up' : 'is-down'">
              {{ change >= 0 ? '+' : '' }}{{ changeRate.toFixed(2) }}%
            </span>
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
            <span class="hoga-total-val">{{ fmt(totalBid) }}</span>
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
              <span class="trade-qty">{{ fmt(t.qty) }}</span>
              <span class="trade-rate" :class="t.side === 'up' ? 'is-up' : 'is-down'">
                {{ t.rate >= 0 ? '+' : '' }}{{ t.rate.toFixed(2) }}%
              </span>
              <span class="trade-time">{{ t.time }}</span>
            </div>
            <p v-if="tradesLoaded && !trades.length" class="trade-empty">실시간 체결 정보가 없어요.</p>
          </div>
        </div>
      </div>
      </template>

      <!-- ===== 종목정보 탭 ===== -->
      <div v-else-if="selectedTab === '종목정보'" class="sd-col-info">

        <!-- 주요 정보 -->
        <div class="panel info-block">
          <div class="info-block-head">
            <div>
              <h3 class="info-name">{{ stock.name }}<span class="info-name-sub">{{ stock.market }} · {{ stock.code }}</span></h3>
              <p class="info-source">출처: 연합인포맥스 및 기업 IR자료</p>
            </div>
            <a
              v-if="stockInfo.homepage"
              class="info-home-link"
              :href="stockInfo.homepage"
              target="_blank"
              rel="noopener"
            >↗ 홈페이지</a>
          </div>
          <p v-if="stockInfo.desc" class="info-desc">{{ stockInfo.desc }}</p>
          <div class="info-facts">
            <div v-if="stock.marketCap" class="fact"><dt>시가총액</dt><dd>{{ stock.marketCap }}</dd></div>
            <div v-if="stockInfo.industry" class="fact"><dt>산업</dt><dd>{{ stockInfo.industry }}</dd></div>
            <div v-if="stockInfo.ceo" class="fact"><dt>대표이사</dt><dd>{{ stockInfo.ceo }}</dd></div>
            <div v-if="stockInfo.listedDate" class="fact"><dt>상장일</dt><dd>{{ stockInfo.listedDate }}</dd></div>
            <div v-if="stockInfo.employees != null" class="fact"><dt>임직원수</dt><dd>{{ fmt(stockInfo.employees) }}명</dd></div>
          </div>
        </div>

        <!-- 주요 사업 -->
        <div class="panel info-block" v-if="stockInfo.industry">
          <h3 class="info-section-title">주요 사업</h3>
          <div class="biz-row">
            <div class="biz-icon">🏢</div>
            <div class="biz-info">
              <strong class="biz-name">{{ stockInfo.industry }}</strong>
              <span class="biz-rank">{{ stock.market }} · {{ stock.sector }}</span>
            </div>
          </div>
        </div>

        <!-- 투자 지표 -->
        <div class="panel info-block">
          <h3 class="info-section-title">투자 지표 <span class="info-section-sub">14:02 기준</span></h3>
          <div class="metric-cards">
            <div class="metric-card">
              <div class="metric-card-title">가치평가</div>
              <div v-for="m in valuation" :key="m.k" class="metric-line"><span>{{ m.k }}</span><strong>{{ m.v }}</strong></div>
            </div>
            <div class="metric-card">
              <div class="metric-card-title">수익</div>
              <div v-for="m in earningsMetrics" :key="m.k" class="metric-line"><span>{{ m.k }}</span><strong>{{ m.v }}</strong></div>
            </div>
            <div class="metric-card">
              <div class="metric-card-title">배당 <span class="metric-card-sub">최근 12개월</span></div>
              <div v-for="m in dividendMetrics" :key="m.k" class="metric-line"><span>{{ m.k }}</span><strong>{{ m.v }}</strong></div>
            </div>
          </div>
        </div>

        <!-- 재무 -->
        <div class="panel info-block">
          <h3 class="info-section-title">재무</h3>
          <div class="fin-cards">
            <div v-for="f in financials" :key="f.k" class="fin-card">
              <div class="fin-k">{{ f.k }}</div>
              <div class="fin-v">{{ f.v }}</div>
            </div>
          </div>
        </div>

        <!-- 수익성 -->
        <div class="panel info-block">
          <h3 class="info-section-title">수익성 <span class="info-section-sub">매출·순이익 성장률</span></h3>
          <p class="info-section-desc">{{ profitDesc }}</p>
          <div class="prof-chart-wrap">
            <svg viewBox="0 0 600 200" class="prof-svg">
              <line v-for="g in [25, 75, 125, 175]" :key="g" x1="0" :y1="g" x2="600" :y2="g" stroke="var(--line)" stroke-width="1" stroke-dasharray="3 4" />
              <template v-for="(b, i) in profChart.bars" :key="i">
                <rect :x="b.revX" :y="b.revY" :width="b.barW" :height="b.revH" rx="2" fill="rgba(var(--accent-rgb),0.35)" />
                <rect :x="b.profX" :y="b.profY" :width="b.barW" :height="b.profH" rx="2" fill="rgba(var(--accent-rgb),0.9)" />
              </template>
              <path :d="profChart.linePath" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
              <circle v-for="(b, i) in profChart.bars" :key="'c' + i" :cx="b.lineX" :cy="b.lineY" r="3.5" fill="#f59e0b" />
            </svg>
            <div class="prof-axis">
              <span v-for="b in profChart.bars" :key="b.label">{{ b.label }}</span>
            </div>
          </div>
          <div class="prof-legend">
            <span><i class="dot rev"></i>매출</span>
            <span><i class="dot prof"></i>순이익</span>
            <span><i class="dot line"></i>순이익률</span>
          </div>
        </div>

        <!-- 동종 업계 순위 -->
        <div class="panel info-block" v-if="peers.length">
          <h3 class="info-section-title">동종 업계 순위 <span class="info-section-sub">{{ stockInfo.industry }}</span></h3>
          <p class="info-section-desc">PER이 낮을수록 같은 이익 대비 저평가 구간일 수 있어요.</p>
          <table class="peer-table">
            <thead>
              <tr><th>순위</th><th>종목</th><th class="num">PER</th><th class="num">시가총액</th><th class="num">주가</th></tr>
            </thead>
            <tbody>
              <tr v-for="p in peers" :key="p.name" :class="{ 'is-me': p.isMe, 'is-median': p.median }">
                <td class="peer-rank">{{ p.rank }}</td>
                <td class="peer-name">{{ p.name }}</td>
                <td class="num">{{ p.per }}</td>
                <td class="num">{{ p.cap }}</td>
                <td class="num">{{ p.price }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 예상 목표 주가 -->
        <div class="panel info-block" v-if="targetPrice">
          <h3 class="info-section-title">예상 목표 주가</h3>
          <p class="info-section-desc">{{ targetPrice.desc }}</p>
          <div class="target-list">
            <div class="target-row high">
              <span class="target-tag">최고</span>
              <span class="target-price">{{ fmt(targetPrice.high.price) }}원</span>
              <span class="target-pct">+{{ targetPrice.high.pct }}%</span>
            </div>
            <div class="target-row avg">
              <span class="target-tag">평균</span>
              <span class="target-price">{{ fmt(targetPrice.avg.price) }}원</span>
              <span class="target-pct">+{{ targetPrice.avg.pct }}%</span>
            </div>
            <div class="target-row low">
              <span class="target-tag">최저</span>
              <span class="target-price">{{ fmt(targetPrice.low.price) }}원</span>
              <span class="target-pct">+{{ targetPrice.low.pct }}%</span>
            </div>
          </div>
          <div class="target-current">현재가 <strong>{{ curSym }}{{ fmt(stock.price) }}</strong></div>
        </div>

      </div>

      <!-- ===== 뉴스 탭 ===== -->
      <div v-else-if="selectedTab === '뉴스'" class="sd-col-info">
        <div class="panel info-block">
          <div class="news-head">
            <h3 class="info-section-title" style="margin:0">{{ stock.name }} 뉴스</h3>
          </div>
          <div class="news-list">
            <a
              v-for="(n, i) in stockNews"
              :key="i"
              class="news-row"
              :href="n.url || undefined"
              target="_blank"
              rel="noopener"
            >
              <div class="news-row-meta">
                <span class="news-chip">{{ stock.name }}</span>
                <span class="news-time">{{ n.time }}</span>
              </div>
              <h4 class="news-row-title">{{ n.title }}</h4>
              <span class="news-row-source">{{ n.source }}</span>
            </a>
            <p v-if="!stockNews.length" class="news-empty">관련 뉴스가 아직 없어요.</p>
          </div>
        </div>
      </div>

      <!-- ===== 커뮤니티 탭 (피드) ===== -->
      <div v-else class="sd-col-community">

        <!-- 작성 박스 -->
        <div class="panel comm-composer">
          <div class="comm-avatar">김</div>
          <input
            v-model="newPostText"
            class="comm-composer-input"
            placeholder="지금 무슨 생각을 하고 있나요?"
            @keyup.enter="addPost"
          />
          <div class="comm-composer-tools">
            <span title="이미지">🖼️</span>
            <span title="목록">☰</span>
            <span title="게시" @click="addPost">↻</span>
          </div>
        </div>

        <!-- 정렬 -->
        <button class="comm-sort" type="button" @click="communitySort = communitySort === '인기순' ? '최신순' : '인기순'">
          {{ communitySort }} ↕
        </button>

        <!-- 피드 -->
        <div class="panel feed-panel">
          <div class="feed-list">
            <div v-for="(p, i) in communityFeed" :key="i" class="feed-post">
              <div class="feed-avatar-col">
                <div class="comm-avatar">{{ p.avatar }}</div>
                <span class="feed-holder">주주</span>
              </div>
              <div class="feed-body">
                <div class="feed-head">
                  <div>
                    <div class="feed-author-line">
                      <strong>{{ p.author }}</strong>
                      <span v-if="p.badge" class="comm-badge">{{ p.badge }}</span>
                    </div>
                    <div class="feed-time">{{ p.time }}</div>
                  </div>
                  <button class="feed-follow" :class="{ 'is-following': p.followed }" @click="p.followed = !p.followed">
                    {{ p.followed ? '팔로잉' : '팔로우' }}
                  </button>
                </div>
                <p class="feed-title">{{ p.title }}</p>
                <p v-if="p.sub" class="feed-sub">{{ p.sub }}</p>
                <div class="feed-actions">
                  <button class="feed-act"><span>♡</span>{{ p.likes }}</button>
                  <button class="feed-act"><span>💬</span>{{ p.comments }}</button>
                  <button class="feed-act"><span>↻</span>{{ p.reposts || '' }}</button>
                  <button class="feed-act"><span>↗</span></button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 우: 주문 / 커뮤니티 사이드바 ===== -->
      <div class="sd-col-right">

        <!-- 커뮤니티 사이드바 -->
        <template v-if="selectedTab === '커뮤니티'">
          <div class="panel comm-stock-card">
            <p class="eyebrow">이 글의 종목</p>
            <div class="comm-stock-head">
              <strong class="comm-stock-name">{{ stock.name }}</strong>
              <span class="comm-stock-code">{{ stock.code }} · {{ stock.market }}</span>
            </div>
            <div class="comm-stock-price">{{ curSym }}{{ fmt(stock.price) }}</div>
            <div class="comm-stock-change" :class="change >= 0 ? 'is-up' : 'is-down'">
              ▲ {{ fmt(Math.abs(change)) }} ({{ change >= 0 ? '+' : '' }}{{ changeRate.toFixed(2) }}%)
            </div>
            <button class="comm-stock-btn" type="button" @click="selectedTab = '종목 홈'">종목 상세 보기 →</button>
          </div>

          <div class="panel comm-popular">
            <p class="eyebrow">{{ stock.name }} 인기글</p>
            <div class="comm-popular-list">
              <div v-for="(p, i) in popularPosts" :key="i" class="comm-popular-item">
                <span class="comm-popular-rank">{{ i + 1 }}</span>
                <div class="comm-popular-info">
                  <span class="comm-popular-title">{{ p.title }}</span>
                  <span class="comm-popular-like">♡ {{ p.likes }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 주문/시뮬/수급 (그 외 탭) -->
        <template v-else>

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
              @click="selectLimit"
            >지정가</button>
            <button
              class="order-type-btn"
              :class="{ 'is-selected': orderType === 'market' }"
              @click="selectMarket"
            >시장가</button>
          </div>

          <!-- 구매 가격 -->
          <label class="order-field">
            <span>구매 가격 ({{ stock.currency === 'USD' ? '$' : '원' }})</span>
            <div class="order-input-row">
              <input
                v-if="orderType === 'limit'"
                v-model.number="orderPrice"
                type="number"
                :step="priceStep"
                min="0"
              />
              <div v-else class="market-price-display">{{ curSym }}{{ fmt(orderPrice) }}</div>
              <div class="price-stepper">
                <button @click="bumpPrice(1)">+</button>
                <button @click="bumpPrice(-1)">−</button>
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
              <dd>{{ orderTotal > 0 ? curSym + fmt(orderTotal) : '주문 가능 금액 입력' }}</dd>
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
          <button
            v-if="orderMsg && orderMsg.ok && orderMsg.cta"
            type="button"
            class="diary-cta-btn"
            @click="router.push('/trading-diary')"
          >📓 이 매매 일기 쓰러가기 →</button>
        </div>

        <!-- 평단 시뮬레이션 (물타기) -->
        <div class="panel sim-panel">
          <p class="eyebrow">매수·매도 시뮬레이션</p>
          <h3>물타기 · 평단 계산기</h3>

          <div class="sim-side-tabs">
            <button :class="{ 'is-on': avgSide === 'BUY' }" @click="avgSide = 'BUY'">매수</button>
            <button :class="{ 'is-on-sell': avgSide === 'SELL' }" @click="avgSide = 'SELL'">매도</button>
          </div>

          <div class="sim-grid">
            <label class="sim-field">
              <span>보유 수량</span>
              <input v-model.number="holdQty" type="number" min="0" />
            </label>
            <label class="sim-field">
              <span>보유 평단</span>
              <input v-model.number="holdAvg" type="number" min="0" step="500" />
            </label>
            <label class="sim-field">
              <span>{{ avgSide === 'BUY' ? '추가 매수가' : '매도가' }}</span>
              <input v-model.number="addPrice" type="number" min="0" step="500" />
            </label>
            <label class="sim-field">
              <span>{{ avgSide === 'BUY' ? '추가 수량' : '매도 수량' }}</span>
              <input v-model.number="addQty" type="number" min="0" />
            </label>
          </div>

          <div class="sim-result">
            <div class="sim-result-main">
              <span>{{ avgSide === 'BUY' ? '예상 평단가' : '실현 손익' }}</span>
              <strong v-if="avgSide === 'BUY'">{{ curSym }}{{ fmt(Math.round(simResult.newAvg)) }}</strong>
              <strong v-else :class="simResult.realized >= 0 ? 'is-up' : 'is-down'">
                {{ simResult.realized >= 0 ? '+' : '-' }}{{ curSym }}{{ fmt(Math.abs(Math.round(simResult.realized))) }}
              </strong>
            </div>
            <dl class="sim-sub">
              <div>
                <dt>총 보유 수량</dt>
                <dd>{{ fmt(simResult.totalQty) }}주</dd>
              </div>
              <div v-if="avgSide === 'BUY'">
                <dt>현재가 대비 평가손익</dt>
                <dd :class="simResult.pnl >= 0 ? 'is-up' : 'is-down'">
                  {{ simResult.pnl >= 0 ? '+' : '-' }}{{ curSym }}{{ fmt(Math.abs(Math.round(simResult.pnl))) }}
                  ({{ simResult.pnlPct >= 0 ? '+' : '' }}{{ simResult.pnlPct.toFixed(2) }}%)
                </dd>
              </div>
              <div v-else>
                <dt>잔여 평단가</dt>
                <dd>{{ curSym }}{{ fmt(Math.round(simResult.newAvg)) }}</dd>
              </div>
            </dl>
          </div>
        </div>

        </template>

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
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
}
.back-btn:hover { background: var(--glass-strong); color: var(--ink); }

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
.watch-toggle-btn.on { background: rgba(245,183,0,0.22); color: #b07d00; border-color: rgba(245,183,0,0.7); }
.watch-toggle-btn:disabled { opacity: 0.6; cursor: default; }

.diary-cta-btn {
  margin-top: 8px;
  width: 100%;
  padding: 9px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--glass-subtle);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s;
}
.diary-cta-btn:hover { background: var(--surface-hover); }

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

/* 달러/원화 토글 (세그먼트, 미국 주식만) */
.ccy-toggle {
  align-self: center;
  display: inline-flex;
  gap: 2px;
  padding: 2px;
  border-radius: 999px;
  background: var(--glass-subtle);
  border: 1px solid var(--glass-border);
}
.ccy-toggle button {
  min-width: 28px;
  height: 22px;
  padding: 0 8px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
}
.ccy-toggle button.is-active { background: var(--glass-strong); color: var(--ink); }

/* 키 메트릭 */
.sd-key-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 20px;
  padding: 12px 16px;
  border-radius: var(--radius);
  background: var(--glass-subtle);
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
  background: var(--glass-subtle);
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
  background: var(--chip-active);
  color: var(--ink);
  box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

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
  padding: 8px 0 8px 8px;
  width: 60px;
  flex-shrink: 0;
  text-align: left;
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
  background: var(--surface-faint);
  border: 1px solid var(--glass-border);
}

.price-chart-svg { width: 100%; height: 100%; }

/* 현재가 점 — SVG 밖 HTML 오버레이라 화면 크기와 무관하게 항상 정원 */
.chart-dot-hit {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.chart-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--accent);
  pointer-events: none;
}

.current-price-label {
  position: absolute;
  left: 0;                                          /* 실제 left/top은 인라인(점 x%·y px) */
  top: 0;
  transform: translate(-50%, calc(-100% - 13px));   /* 점 중앙 위 + 점과 살짝 간격 (아래로 향한 꼬리) */
  font-size: 11px;
  font-weight: 900;
  color: #fff;
  background: var(--accent);
  padding: 2px 7px;
  border-radius: 6px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 2;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
}
/* 말풍선 꼬리 — 기본(점 위): 아래쪽 가운데에서 점을 가리킴 */
.current-price-label::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 100%;
  transform: translateX(-50%);
  border: 5px solid transparent;
  border-top-color: var(--accent);
}

/* 시간 축 */
.time-axis {
  display: flex;
  justify-content: space-between;
  padding: 4px 60px 6px 0;
  font-size: 10px;
  font-weight: 700;
  color: var(--faint);
}

/* 거래량 */
.volume-label-row {
  padding: 4px 60px 2px 0;
}

.volume-chart-wrap {
  height: 70px;
  margin-left: 0;
  margin-right: 60px;
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--surface-faint);
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
  background: var(--glass-subtle);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.14s, color 0.14s;
}

.community-tabs button.is-active {
  background: rgba(var(--accent-rgb),0.1);
  border-color: rgba(var(--accent-rgb),0.22);
  color: var(--accent);
}

.community-list { display: flex; flex-direction: column; gap: 1px; }

.community-post {
  padding: 10px 8px;
  border-radius: var(--radius);
  transition: background 0.14s;
  cursor: pointer;
}

.community-post:hover { background: var(--surface-soft); }

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
  background: rgba(var(--purple-rgb),0.12);
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
  background: var(--glass-subtle);
  color: var(--muted);
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
}

.hoga-meta-tabs button.is-active {
  background: var(--glass-strong);
  color: var(--ink);
}

.hoga-total-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 6px;
  background: var(--glass-subtle);
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

.hoga-row:hover { background: var(--surface-soft); }

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

.ask-price { color: var(--krx-up); }
.bid-price { color: var(--krx-down); }

.hoga-qty {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  white-space: nowrap;
}

.hoga-asks .hoga-qty { text-align: right; }
.hoga-bids .hoga-qty { text-align: left; }

.hoga-empty {
  margin: 8px 0;
  padding: 18px 8px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--faint);
}

/* 현재가 중간 */
.hoga-current {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px;
  background: rgba(var(--accent-rgb),0.07);
  border-radius: 6px;
  border: 1px solid rgba(var(--accent-rgb),0.18);
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
.trade-row:hover { background: var(--surface-soft); }

.trade-price { font-size: 12px; font-weight: 900; text-align: left; }
.trade-qty { font-size: 11px; font-weight: 700; color: var(--muted); text-align: right; }
.trade-rate { font-size: 11px; font-weight: 900; text-align: right; }
.trade-time { font-size: 10px; font-weight: 700; color: var(--faint); text-align: right; }
.trade-empty { padding: 24px 8px; text-align: center; font-size: 12px; font-weight: 700; color: var(--faint); }

/* ===== 주문 패널 ===== */
.order-panel { padding: 16px 16px 18px; display: flex; flex-direction: column; gap: 16px; }

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
  background: var(--glass-subtle);
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
  color: var(--muted);
}

.buy-tab.is-active-buy {
  background: rgba(0,102,204,0.12);
  color: var(--krx-down);
}

.sell-tab.is-active-sell {
  background: rgba(255,59,92,0.10);
  color: var(--krx-up);
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
  background: var(--glass-subtle);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
}

.order-type-btn.is-selected {
  background: var(--chip-active);
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
  background: var(--surface-soft);
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
  background: var(--surface-soft);
  color: var(--ink);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  line-height: 1;
  transition: background 0.14s;
}

.price-stepper button:hover { background: var(--glass-strong); }

.qty-shortcuts {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
}

.qty-shortcuts button {
  padding: 6px 0;
  border-radius: 6px;
  border: 1px solid var(--glass-border);
  background: var(--glass-subtle);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.14s, color 0.14s;
}

.qty-shortcuts button:hover {
  background: var(--surface-hover);
  color: var(--ink);
}

.order-summary {
  margin: 0;
  padding: 12px;
  border-radius: var(--radius);
  background: var(--glass-subtle);
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

/* ===== 평단 시뮬레이션 패널 ===== */
.sim-panel { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.sim-panel h3 { font-size: 16px; font-weight: 900; color: var(--ink); margin: 2px 0 0; }

.sim-side-tabs { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.sim-side-tabs button {
  padding: 8px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--glass-subtle);
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
}
.sim-side-tabs button.is-on { background: rgba(0,102,204,0.12); color: var(--krx-down); border-color: rgba(0,102,204,0.3); }
.sim-side-tabs button.is-on-sell { background: rgba(255,59,92,0.10); color: var(--krx-up); border-color: rgba(255,59,92,0.3); }

.sim-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.sim-field { display: flex; flex-direction: column; gap: 4px; }
.sim-field span { font-size: 11px; font-weight: 900; color: var(--muted); }
.sim-field input {
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  color: var(--ink);
  font-size: 13px;
  font-weight: 900;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.18s;
}
.sim-field input:focus { border-color: var(--accent); }

.sim-result {
  margin-top: 2px;
  padding: 14px;
  border-radius: var(--radius);
  background: var(--glass-subtle);
  border: 1px solid var(--glass-border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.sim-result-main { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.sim-result-main span { font-size: 12px; font-weight: 900; color: var(--muted); }
.sim-result-main strong { font-size: 22px; font-weight: 900; color: var(--ink); letter-spacing: -0.5px; }
.sim-sub { margin: 0; display: flex; flex-direction: column; gap: 6px; }
.sim-sub > div { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.sim-sub dt { font-size: 12px; font-weight: 700; color: var(--muted); }
.sim-sub dd { font-size: 13px; font-weight: 900; color: var(--ink); margin: 0; text-align: right; }

/* ===== 종목정보 탭 ===== */
.sd-grid.is-info { grid-template-columns: minmax(0, 1fr) 260px; }
.sd-col-info { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.info-block { padding: 20px 22px; }

.info-block-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.info-name { font-size: 20px; font-weight: 900; color: var(--ink); margin: 0; display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }
.info-name-sub { font-size: 13px; font-weight: 800; color: var(--muted); }
.info-source { margin: 4px 0 0; font-size: 12px; color: var(--faint); font-weight: 700; }
.info-home-link {
  flex-shrink: 0; padding: 6px 12px; border-radius: 999px;
  border: 1px solid var(--glass-border); background: var(--surface-soft);
  color: var(--muted); font-size: 12px; font-weight: 900; cursor: pointer;
  text-decoration: none; display: inline-block;
  transition: background 0.16s, color 0.16s;
}
.info-home-link:hover { background: var(--glass-strong); color: var(--ink); }

.info-desc {
  margin: 0 0 16px; padding: 14px 16px; border-radius: var(--radius);
  background: var(--glass-subtle); border: 1px solid var(--glass-border);
  font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1.6; word-break: keep-all;
}

.info-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 0 32px; }
.fact { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--faint); }
.fact dt { font-size: 13px; font-weight: 700; color: var(--muted); flex-shrink: 0; }
.fact dd { margin: 0; font-size: 13px; font-weight: 900; color: var(--ink); text-align: right; }
.fact dd small { display: block; font-size: 11px; font-weight: 700; color: var(--faint); margin-top: 2px; }

.info-section-title { font-size: 17px; font-weight: 900; color: var(--ink); margin: 0 0 14px; }
.info-section-sub { font-size: 12px; font-weight: 800; color: var(--faint); margin-left: 6px; }
.info-section-desc { margin: -4px 0 16px; font-size: 13px; color: var(--muted); font-weight: 700; line-height: 1.55; word-break: keep-all; }

/* 주요 사업 */
.biz-row { display: flex; align-items: center; gap: 14px; }
.biz-icon {
  width: 48px; height: 48px; border-radius: 14px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 24px;
  background: linear-gradient(135deg, rgba(var(--accent-rgb),0.12), rgba(var(--purple-rgb),0.12));
  border: 1px solid var(--glass-border);
}
.biz-info { display: flex; flex-direction: column; gap: 2px; }
.biz-name { font-size: 15px; font-weight: 900; color: var(--ink); }
.biz-rank { font-size: 12px; font-weight: 700; color: var(--muted); }

/* 투자 지표 */
.metric-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.metric-card { padding: 14px 16px; border-radius: var(--radius); background: var(--glass-subtle); border: 1px solid var(--glass-border); }
.metric-card-title { font-size: 13px; font-weight: 900; color: var(--ink); margin-bottom: 8px; display: flex; align-items: baseline; justify-content: space-between; }
.metric-card-sub { font-size: 10px; font-weight: 700; color: var(--faint); }
.metric-line { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-top: 1px solid var(--faint); }
.metric-line:first-of-type { border-top: 0; }
.metric-line span { font-size: 12px; font-weight: 700; color: var(--muted); }
.metric-line strong { font-size: 13px; font-weight: 900; color: var(--ink); }

/* 재무 */
.fin-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.fin-card { padding: 16px; border-radius: var(--radius); background: var(--glass-subtle); border: 1px solid var(--glass-border); }
.fin-k { font-size: 12px; font-weight: 800; color: var(--muted); margin-bottom: 8px; }
.fin-v { font-size: 22px; font-weight: 900; color: var(--ink); letter-spacing: -0.5px; }

/* 수익성 */
.prof-chart-wrap { margin-top: 4px; }
.prof-svg { width: 100%; height: auto; display: block; }
.prof-axis { display: flex; margin-top: 6px; padding: 0 4px; }
.prof-axis span { flex: 1; text-align: center; font-size: 11px; font-weight: 700; color: var(--faint); }
.prof-legend { display: flex; gap: 16px; margin-top: 12px; }
.prof-legend span { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 800; color: var(--muted); }
.prof-legend .dot { width: 10px; height: 10px; border-radius: 3px; }
.prof-legend .dot.rev { background: rgba(var(--accent-rgb),0.35); }
.prof-legend .dot.prof { background: rgba(var(--accent-rgb),0.9); }
.prof-legend .dot.line { background: #f59e0b; border-radius: 50%; }

/* 동종 업계 순위 */
.peer-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.peer-table th { padding: 8px 10px; text-align: left; font-size: 11px; font-weight: 800; color: var(--muted); border-bottom: 1px solid var(--line); white-space: nowrap; }
.peer-table th.num, .peer-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.peer-table td { padding: 11px 10px; border-bottom: 1px solid var(--faint); color: var(--ink); font-weight: 700; white-space: nowrap; }
.peer-table tr:last-child td { border-bottom: 0; }
.peer-rank { color: var(--muted); font-weight: 900; width: 36px; }
.peer-name { font-weight: 900; }
.peer-table tr.is-me td { background: rgba(var(--accent-rgb),0.07); color: var(--accent); }
.peer-table tr.is-me .peer-rank, .peer-table tr.is-me .peer-name { color: var(--accent); }
.peer-table tr.is-median td { color: var(--faint); font-weight: 700; background: var(--glass-subtle); }

/* 예상 목표 주가 */
.target-list { display: flex; flex-direction: column; gap: 8px; }
.target-row { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: var(--radius); border: 1px solid var(--glass-border); }
.target-tag { font-size: 12px; font-weight: 900; padding: 3px 10px; border-radius: 999px; }
.target-price { font-size: 15px; font-weight: 900; color: var(--ink); }
.target-pct { margin-left: auto; font-size: 14px; font-weight: 900; }
.target-row.high { background: rgba(255,59,92,0.06); }
.target-row.high .target-tag { background: rgba(255,59,92,0.14); color: var(--negative); }
.target-row.high .target-pct { color: var(--negative); }
.target-row.avg { background: rgba(16,185,129,0.06); }
.target-row.avg .target-tag { background: rgba(16,185,129,0.14); color: #059669; }
.target-row.avg .target-pct { color: #059669; }
.target-row.low { background: rgba(var(--accent-rgb),0.06); }
.target-row.low .target-tag { background: rgba(var(--accent-rgb),0.14); color: var(--accent); }
.target-row.low .target-pct { color: var(--accent); }
.target-current { margin-top: 12px; text-align: right; font-size: 12px; font-weight: 700; color: var(--muted); }
.target-current strong { color: var(--ink); font-size: 14px; }

@media (max-width: 1100px) {
  .sd-grid.is-info { grid-template-columns: 1fr; }
  .metric-cards, .fin-cards, .info-facts { grid-template-columns: 1fr; }
}

/* ===== 뉴스 탭 ===== */
.news-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.news-list { display: flex; flex-direction: column; }
.news-row { display: block; text-decoration: none; color: inherit; padding: 16px 6px; border-bottom: 1px solid var(--faint); cursor: pointer; transition: background 0.14s; }
.news-row:last-child { border-bottom: 0; }
.news-empty, .community-empty { padding: 28px 6px; text-align: center; font-size: 13px; font-weight: 700; color: var(--faint); }
.news-row:hover { background: var(--surface-soft); border-radius: var(--radius); }
.news-row-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 7px; }
.news-chip { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 900; background: rgba(var(--purple-rgb),0.1); color: var(--purple); border: 1px solid rgba(var(--purple-rgb),0.2); }
.news-time { margin-left: auto; font-size: 11px; font-weight: 700; color: var(--faint); }
.news-row-title { font-size: 15px; font-weight: 800; color: var(--ink); margin: 0 0 5px; line-height: 1.45; word-break: keep-all; }
.news-row-source { font-size: 12px; font-weight: 700; color: var(--faint); }

/* ===== 커뮤니티 탭 ===== */
.sd-grid.is-community { grid-template-columns: minmax(0, 1fr) 300px; }
.sd-col-community { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.comm-avatar {
  width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff; font-size: 14px; font-weight: 900;
}
.comm-badge { padding: 2px 7px; border-radius: 999px; font-size: 10px; font-weight: 900; background: rgba(16,185,129,0.12); color: #059669; }

/* 작성 박스 */
.comm-composer { display: flex; align-items: center; gap: 10px; padding: 12px 16px; }
.comm-composer-input {
  flex: 1; min-width: 0; height: 40px; border: 0; background: transparent;
  color: var(--ink); font-size: 14px; font-weight: 600; outline: none;
}
.comm-composer-input::placeholder { color: var(--faint); font-weight: 600; }
.comm-composer-tools { display: flex; gap: 4px; flex-shrink: 0; }
.comm-composer-tools span {
  width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center;
  border-radius: 8px; cursor: pointer; font-size: 15px; color: var(--faint);
}
.comm-composer-tools span:hover { background: var(--surface-soft); color: var(--ink); }

/* 정렬 */
.comm-sort {
  align-self: flex-start; display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 12px; border-radius: 999px; border: 1px solid var(--glass-border);
  background: var(--glass-subtle); color: var(--muted); font-size: 12px; font-weight: 900; cursor: pointer;
}
.comm-sort:hover { color: var(--ink); }

/* 피드 */
.feed-panel { padding: 0; overflow: hidden; }
.feed-list { display: flex; flex-direction: column; }
.feed-post { display: flex; gap: 12px; padding: 16px 18px; border-top: 1px solid var(--faint); }
.feed-post:first-child { border-top: 0; }
.feed-avatar-col { display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; }
.feed-holder { font-size: 10px; font-weight: 900; color: var(--accent); }
.feed-body { flex: 1; min-width: 0; }
.feed-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.feed-author-line { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.feed-author-line strong { font-size: 13px; font-weight: 900; color: var(--ink); }
.feed-time { font-size: 11px; font-weight: 700; color: var(--faint); margin-top: 1px; }
.feed-follow {
  flex-shrink: 0; padding: 5px 12px; border-radius: 8px; border: 0;
  background: rgba(var(--accent-rgb),0.12); color: var(--accent); font-size: 12px; font-weight: 900;
  cursor: pointer; transition: background 0.16s;
}
.feed-follow:hover { background: rgba(var(--accent-rgb),0.2); }
.feed-follow.is-following { background: var(--surface-soft); color: var(--muted); }
.feed-title { font-size: 15px; font-weight: 800; color: var(--ink); margin: 8px 0 0; line-height: 1.45; word-break: keep-all; }
.feed-sub { font-size: 14px; font-weight: 600; color: var(--muted); margin: 2px 0 0; line-height: 1.45; word-break: keep-all; }
.feed-actions { display: flex; align-items: center; gap: 18px; margin-top: 10px; }
.feed-act { display: inline-flex; align-items: center; gap: 5px; border: 0; background: none; padding: 0; color: var(--muted); font-size: 12px; font-weight: 800; cursor: pointer; transition: color 0.15s; }
.feed-act:hover { color: var(--accent); }

/* 커뮤니티 사이드바 */
.comm-stock-card { padding: 18px; }
.comm-stock-head { display: flex; flex-direction: column; gap: 2px; margin: 6px 0 10px; }
.comm-stock-name { font-size: 16px; font-weight: 900; color: var(--ink); }
.comm-stock-code { font-size: 12px; font-weight: 700; color: var(--muted); }
.comm-stock-price { font-size: 22px; font-weight: 900; color: var(--ink); letter-spacing: -0.5px; }
.comm-stock-change { font-size: 13px; font-weight: 900; margin-top: 2px; }
.comm-stock-btn {
  width: 100%; margin-top: 14px; height: 40px; border-radius: var(--radius);
  border: 1px solid rgba(var(--accent-rgb),0.25); background: rgba(var(--accent-rgb),0.08);
  color: var(--accent); font-size: 13px; font-weight: 900; cursor: pointer; transition: background 0.16s;
}
.comm-stock-btn:hover { background: rgba(var(--accent-rgb),0.16); }

.comm-popular { padding: 18px; }
.comm-popular-list { display: flex; flex-direction: column; margin-top: 10px; }
.comm-popular-item { display: flex; gap: 10px; align-items: flex-start; padding: 10px 0; border-top: 1px solid var(--faint); }
.comm-popular-item:first-child { border-top: 0; }
.comm-popular-rank { font-size: 13px; font-weight: 900; color: var(--accent); flex-shrink: 0; width: 14px; }
.comm-popular-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.comm-popular-title { font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1.4; word-break: keep-all; }
.comm-popular-like { font-size: 11px; font-weight: 800; color: var(--muted); }

@media (max-width: 1100px) {
  .sd-grid.is-community { grid-template-columns: 1fr; }
}

/* ===== 색상 (한국식: 상승=빨강, 하락=파랑) — 전역 .is-up/.is-down(초록/빨강) !important 덮어쓰기 ===== */
.is-up   { color: #e3344f !important; }
.is-down { color: #2b59d6 !important; }
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
