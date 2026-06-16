<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { stocks } from '../data/stocks.js'
import { useWatchlist } from '../composables/useWatchlist.js'
import { useFormat } from '../composables/useFormat.js'

const route = useRoute()
const { watchedCodes, toggleWatch } = useWatchlist()
const { formatMoney, formatCompact, formatRate, signedClass } = useFormat()

// ── 종목 (data/stocks.js 목업 → 실제론 GET /stocks/{code}/ + /price/ + /financials/) ──
const stock = computed(() => stocks.find((s) => s.code === route.params.code) || stocks[0])
const isWatched = computed(() => watchedCodes.value.includes(stock.value.code))

// ── 가격 (GET /stocks/{code}/price/) — prev_close 프록시로 open 사용 ──
const change = computed(() => stock.value.price - stock.value.open)
const changeRate = computed(() => (stock.value.open ? (change.value / stock.value.open) * 100 : 0))

// ── 핵심 지표 (stock_indicator) — 목업 PER/PBR/EPS 보강 ──
const indicatorMock = {
  '005930': { per: 13.2, pbr: 1.4, eps: 5283 },
  '000660': { per: 18.7, pbr: 2.1, eps: 9420 },
  '005380': { per: 5.4, pbr: 0.6, eps: 41200 },
  AAPL: { per: 31.5, pbr: 48.2, eps: 6.42 },
  NVDA: { per: 62.1, pbr: 41.0, eps: 1.92 },
  GOOGL: { per: 24.8, pbr: 6.7, eps: 7.54 },
}
const indicators = computed(() => {
  const s = stock.value
  const extra = indicatorMock[s.code] || { per: null, pbr: null, eps: null }
  return [
    { label: 'PER', value: extra.per != null ? `${extra.per}배` : '—' },
    { label: 'PBR', value: extra.pbr != null ? `${extra.pbr}배` : '—' },
    { label: 'EPS', value: extra.eps != null ? formatCompact(extra.eps) : '—' },
    { label: 'ROE', value: s.roe != null ? `${s.roe.toFixed(2)}%` : '—' },
    { label: 'Beta', value: s.beta != null ? s.beta.toFixed(2) : '—' },
    { label: '52주 최고', value: formatMoney(s.high52w, s.currency) },
    { label: '52주 최저', value: formatMoney(s.low52w, s.currency) },
    { label: '변동성', value: s.volatility != null ? `${s.volatility.toFixed(1)}%` : '—' },
  ]
})

// ── 탭 ──
const tabs = ['종목홈', '종목정보', '뉴스', '커뮤니티']
const activeTab = ref('종목홈')

// ── 차트 기간 (stock_price 일/주/월/년봉 + KIS 라이브 분봉) ──
const periods = ['1분', '일', '주', '월', '년']
const activePeriod = ref('일')
const chartPoints = computed(() => {
  const values = stock.value.sparkline
  const w = 640, h = 220, pad = 16
  const min = Math.min(...values), max = Math.max(...values)
  const range = max - min || 1
  return values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w
      const y = h - ((v - min) / range) * (h - pad * 2) - pad
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})

// ── 호가 8단계 (GET /stocks/{code}/orderbook/) — KIS 라이브 목업 ──
function niceTick(price) {
  if (price >= 1000000) return 1000
  if (price >= 100000) return 500
  if (price >= 10000) return 100
  if (price >= 1000) return 50
  if (price >= 100) return 0.5
  return 0.05
}
const orderbook = computed(() => {
  const base = Math.round(stock.value.price)
  const tick = niceTick(base)
  const qty = (n) => 1200 + ((n * 73 + base) % 9) * 940 + (n % 3) * 320
  const asks = []
  const bids = []
  for (let i = 1; i <= 8; i++) {
    asks.push({ price: base + tick * i, quantity: qty(i) })
    bids.push({ price: base - tick * i, quantity: qty(i + 8) })
  }
  asks.reverse() // 위에서부터 높은 호가
  const maxQty = Math.max(...asks.map((a) => a.quantity), ...bids.map((b) => b.quantity))
  return { asks, bids, maxQty }
})

// ── 주문 패널 (가상 브로커: account · holding · order / preview→order) ──
const orderSide = ref('BUY')
const orderType = ref('LIMIT')
const orderPrice = ref(0)
const orderQty = ref(0)
const orderableBalance = 1247800 // 목업: account.balance 의 주문가능액

watch(stock, () => { orderPrice.value = Math.round(stock.value.price) }, { immediate: true })

const orderEstimate = computed(() => orderPrice.value * orderQty.value)
const orderFee = computed(() => orderEstimate.value * (stock.value.currency === 'KRW' ? 0.00015 : 0.0007))
const orderTotal = computed(() => orderEstimate.value + orderFee.value)

// 매매일지 작성 (주문 직후 바로 기록 — POST /api/v1/diaries 의 order_id 연결)
// reason_category 선택지 (image50 TextChoices)
const reasonCategories = ['장기성장성', '실적개선', '저평가', '테마', '뉴스호재', '기술적반등', '배당', '분산']
const showDiary = ref(false)
const diaryForm = ref({ confidence: 3, category: '', reason: '', target: '', stop: '' })

function setPercent(pct) {
  if (!orderPrice.value) return
  orderQty.value = Math.floor(((orderableBalance * pct) / 100) / orderPrice.value)
}

// ── 종토방 (community_post WHERE stock) / 뉴스 (stock_news) 목업 ──
const stockPosts = [
  { id: 1, nickname: '주린이탈출', title: '여기 지금 들어가도 되나요?', likes: 14, comments: 6, time: '12분 전' },
  { id: 2, nickname: '존버왕', title: '실적 발표 후 흐름 정리해봤습니다', likes: 33, comments: 12, time: '1시간 전' },
  { id: 3, nickname: '배당러버', title: '배당 재투자 전략 공유', likes: 8, comments: 3, time: '3시간 전' },
]
const stockNews = [
  { id: 1, source: '한국경제', title: `${'반도체 업황 회복 기대… 외국인 순매수 전환'}`, time: '34분 전' },
  { id: 2, source: '머니투데이', title: 'HBM 수요 지속 전망, 증권가 목표가 상향', time: '2시간 전' },
  { id: 3, source: '연합뉴스', title: '1분기 실적 컨센서스 상회… 영업이익 개선', time: '5시간 전' },
]
</script>

<template>
  <div>
    <!-- ① 상단 헤더 -->
    <section class="panel detail-header">
      <div class="dh-left">
        <p class="eyebrow">{{ stock.market }} · {{ stock.sector }} · {{ stock.code }}</p>
        <div class="dh-title">
          <h1>{{ stock.name }}</h1>
          <button
            type="button"
            class="watch-star"
            :class="{ on: isWatched }"
            @click="toggleWatch(stock.code)"
          >{{ isWatched ? '★ 관심' : '☆ 관심 추가' }}</button>
        </div>
        <div class="dh-price">
          <strong>{{ formatMoney(stock.price, stock.currency) }}</strong>
          <span :class="signedClass(changeRate)">
            {{ change > 0 ? '+' : '' }}{{ formatMoney(change, stock.currency) }} ({{ formatRate(changeRate) }})
          </span>
        </div>
        <dl class="dh-ohlc">
          <div><dt>시가</dt><dd>{{ formatMoney(stock.open, stock.currency) }}</dd></div>
          <div><dt>고가</dt><dd>{{ formatMoney(stock.high, stock.currency) }}</dd></div>
          <div><dt>저가</dt><dd>{{ formatMoney(stock.low, stock.currency) }}</dd></div>
          <div><dt>거래량</dt><dd>{{ formatCompact(stock.volume) }}</dd></div>
        </dl>
      </div>
      <div class="dh-indicators">
        <div v-for="ind in indicators" :key="ind.label" class="ind-cell">
          <span>{{ ind.label }}</span>
          <strong>{{ ind.value }}</strong>
        </div>
      </div>
    </section>

    <!-- 탭 -->
    <div class="tab-list detail-tabs" aria-label="종목 상세 탭">
      <button
        v-for="t in tabs"
        :key="t"
        type="button"
        :class="{ 'is-selected': activeTab === t }"
        @click="activeTab = t"
      >{{ t }}</button>
    </div>

    <!-- ============ 종목홈 ============ -->
    <div v-if="activeTab === '종목홈'" class="detail-grid">
      <!-- 차트 + 종토방/뉴스 -->
      <div class="detail-main">
        <section class="panel">
          <div class="chart-head">
            <div class="segmented period-seg" aria-label="차트 기간">
              <button v-for="p in periods" :key="p" type="button" :class="{ 'is-selected': activePeriod === p }" @click="activePeriod = p">{{ p }}</button>
            </div>
            <span class="chart-note">{{ activePeriod === '1분' ? 'KIS 라이브 (저장 X)' : 'stock_price 집계' }}</span>
          </div>
          <div class="chart-frame" role="img" :aria-label="`${stock.name} 가격 흐름`">
            <svg viewBox="0 0 640 260" preserveAspectRatio="none">
              <polyline class="chart-grid-line" points="0,65 640,65" />
              <polyline class="chart-grid-line" points="0,130 640,130" />
              <polyline class="chart-grid-line" points="0,195 640,195" />
              <polyline class="chart-line" :points="chartPoints" />
            </svg>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><div><p class="eyebrow">community_post</p><h2>종토방</h2></div></div>
          <div class="mini-post-list">
            <article v-for="p in stockPosts" :key="p.id" class="mini-post">
              <span class="mini-post-author">{{ p.nickname }}</span>
              <span class="mini-post-title">{{ p.title }}</span>
              <span class="mini-post-stats">♥ {{ p.likes }} 💬 {{ p.comments }} · {{ p.time }}</span>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><div><p class="eyebrow">stock_news</p><h2>뉴스</h2></div></div>
          <ul class="mini-news-list">
            <li v-for="n in stockNews" :key="n.id">
              <span class="mini-news-source">{{ n.source }}</span>
              <span class="mini-news-title">{{ n.title }}</span>
              <span class="mini-news-time">{{ n.time }}</span>
            </li>
          </ul>
        </section>
      </div>

      <!-- ③ 호가 8단계 -->
      <section class="panel orderbook-panel">
        <div class="panel-head"><div><p class="eyebrow">호가 8단계</p><h2>호가</h2></div></div>
        <div class="ob-list">
          <div v-for="(a, i) in orderbook.asks" :key="`a${i}`" class="ob-row ask">
            <span class="ob-bar ask" :style="{ width: `${(a.quantity / orderbook.maxQty) * 100}%` }"></span>
            <span class="ob-qty">{{ formatCompact(a.quantity) }}</span>
            <span class="ob-price">{{ formatMoney(a.price, stock.currency) }}</span>
          </div>
          <div class="ob-current">
            <span>현재가</span>
            <strong :class="signedClass(changeRate)">{{ formatMoney(stock.price, stock.currency) }}</strong>
          </div>
          <div v-for="(b, i) in orderbook.bids" :key="`b${i}`" class="ob-row bid">
            <span class="ob-bar bid" :style="{ width: `${(b.quantity / orderbook.maxQty) * 100}%` }"></span>
            <span class="ob-price">{{ formatMoney(b.price, stock.currency) }}</span>
            <span class="ob-qty">{{ formatCompact(b.quantity) }}</span>
          </div>
        </div>
      </section>

      <!-- ⑥ 주문 패널 -->
      <aside class="panel order-panel">
        <p class="eyebrow">일반주문</p>
        <h2 class="order-title">주문하기</h2>

        <div class="segmented full order-side" aria-label="매수 매도">
          <button type="button" class="buy" :class="{ 'is-selected': orderSide === 'BUY' }" @click="orderSide = 'BUY'">매수</button>
          <button type="button" class="sell" :class="{ 'is-selected': orderSide === 'SELL' }" @click="orderSide = 'SELL'">매도</button>
        </div>

        <div class="segmented full" aria-label="주문 유형">
          <button type="button" :class="{ 'is-selected': orderType === 'LIMIT' }" @click="orderType = 'LIMIT'">지정가</button>
          <button type="button" :class="{ 'is-selected': orderType === 'MARKET' }" @click="orderType = 'MARKET'">시장가</button>
        </div>

        <label class="field">
          <span>구매 가격 ({{ stock.currency === 'KRW' ? '원' : '달러' }})</span>
          <input v-model.number="orderPrice" type="number" :disabled="orderType === 'MARKET'" min="0" />
        </label>

        <label class="field">
          <span>수량</span>
          <input v-model.number="orderQty" type="number" min="0" />
        </label>

        <div class="pct-row">
          <button v-for="pct in [10, 25, 50, 100]" :key="pct" type="button" @click="setPercent(pct)">
            {{ pct === 100 ? '최대' : `${pct}%` }}
          </button>
        </div>

        <dl class="order-summary">
          <div><dt>총 주문 금액</dt><dd>{{ formatMoney(orderTotal, stock.currency) }}</dd></div>
          <div><dt>주문 가능 금액</dt><dd>{{ formatMoney(orderableBalance, stock.currency) }}</dd></div>
        </dl>

        <button type="button" class="order-submit" :class="orderSide === 'BUY' ? 'buy' : 'sell'">
          {{ orderSide === 'BUY' ? '매수하기' : '매도하기' }}
          <em>주문 API 연결 예정</em>
        </button>
        <p class="fine-print">실제 체결은 <code>/orders/preview/</code> 검증 뒤 <code>/orders/</code>로 분리합니다.</p>

        <!-- 매매일지 작성 (주문 직후 바로 기록) -->
        <button type="button" class="diary-toggle" @click="showDiary = !showDiary">
          📔 매매일지 작성 <span>{{ showDiary ? '▲' : '▼' }}</span>
        </button>
        <div v-if="showDiary" class="order-diary">
          <p class="od-auto">
            <span class="od-side" :class="orderSide === 'BUY' ? 'buy' : 'sell'">{{ orderSide === 'BUY' ? '매수' : '매도' }}</span>
            {{ stock.name }} · {{ orderQty }}주 @ {{ formatMoney(orderPrice, stock.currency) }}
          </p>

          <div class="field">
            <span>확신도</span>
            <div class="star-pick">
              <button v-for="n in 5" :key="n" type="button" :class="{ on: n <= diaryForm.confidence }" @click="diaryForm.confidence = n">★</button>
            </div>
          </div>

          <div class="field">
            <span>매매 이유</span>
            <div class="cat-chips">
              <button
                v-for="c in reasonCategories"
                :key="c"
                type="button"
                class="cat-chip"
                :class="{ 'is-selected': diaryForm.category === c }"
                @click="diaryForm.category = c"
              >{{ c }}</button>
            </div>
          </div>

          <label class="field"><span>메모</span><textarea v-model="diaryForm.reason" rows="2" placeholder="이 매매를 결정한 이유"></textarea></label>
          <div class="od-2col">
            <label class="field"><span>목표가</span><input v-model="diaryForm.target" type="number" placeholder="선택" /></label>
            <label class="field"><span>손절가</span><input v-model="diaryForm.stop" type="number" placeholder="선택" /></label>
          </div>

          <button type="button" class="diary-save">매매일지 저장</button>
          <p class="fine-print"><code>POST /api/v1/diaries</code> (order_id 연결) · 조회는 <RouterLink to="/diary">매매일기</RouterLink>에서.</p>
        </div>
      </aside>
    </div>

    <!-- ============ 종목정보 ============ -->
    <section v-else-if="activeTab === '종목정보'" class="panel">
      <div class="panel-head"><div><p class="eyebrow">financial_summary + stock.description</p><h2>종목 정보</h2></div></div>
      <p class="info-desc">{{ stock.points?.join(' · ') || '기업 개요 데이터는 stock.description / financial_summary 에서 제공됩니다.' }}</p>
      <dl class="quote-stats info-grid">
        <div v-for="ind in indicators" :key="ind.label"><dt>{{ ind.label }}</dt><dd>{{ ind.value }}</dd></div>
      </dl>
    </section>

    <!-- ============ 뉴스 ============ -->
    <section v-else-if="activeTab === '뉴스'" class="panel">
      <div class="panel-head"><div><p class="eyebrow">stock_news</p><h2>뉴스 · 공시</h2></div></div>
      <ul class="mini-news-list">
        <li v-for="n in stockNews" :key="n.id">
          <span class="mini-news-source">{{ n.source }}</span>
          <span class="mini-news-title">{{ n.title }}</span>
          <span class="mini-news-time">{{ n.time }}</span>
        </li>
      </ul>
    </section>

    <!-- ============ 커뮤니티 ============ -->
    <section v-else class="panel">
      <div class="panel-head"><div><p class="eyebrow">community_post WHERE stock</p><h2>커뮤니티 (종토방)</h2></div></div>
      <div class="mini-post-list">
        <article v-for="p in stockPosts" :key="p.id" class="mini-post">
          <span class="mini-post-author">{{ p.nickname }}</span>
          <span class="mini-post-title">{{ p.title }}</span>
          <span class="mini-post-stats">♥ {{ p.likes }} 💬 {{ p.comments }} · {{ p.time }}</span>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.is-up { color: var(--positive); }
.is-down { color: var(--negative); }
.is-flat { color: var(--muted); }

/* 헤더 */
.detail-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr);
  gap: 24px;
  align-items: center;
  margin-bottom: 14px;
}
.dh-title { display: flex; align-items: center; gap: 12px; margin: 4px 0 8px; }
.dh-title h1 { margin: 0; font-size: 26px; }
.watch-star {
  padding: 5px 12px; border-radius: 999px;
  border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.5);
  color: var(--muted); font-size: 12px; font-weight: 900;
}
.watch-star.on { background: rgba(15, 159, 110, 0.1); border-color: rgba(15, 159, 110, 0.3); color: var(--positive); }
.dh-price { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; }
.dh-price strong { font-size: 30px; color: var(--ink); letter-spacing: -0.5px; }
.dh-price span { font-size: 15px; font-weight: 900; }
.dh-ohlc { display: flex; flex-wrap: wrap; gap: 18px; margin: 0; }
.dh-ohlc > div { display: flex; gap: 6px; align-items: baseline; }
.dh-ohlc dt { color: var(--muted); font-size: 12px; }
.dh-ohlc dd { margin: 0; color: var(--ink); font-size: 13px; font-weight: 900; }

.dh-indicators {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
  border-radius: var(--radius); overflow: hidden;
  background: rgba(180, 200, 255, 0.3); border: 1px solid var(--glass-border);
}
.ind-cell { background: rgba(255, 255, 255, 0.55); padding: 12px; display: flex; flex-direction: column; gap: 3px; }
.ind-cell span { color: var(--muted); font-size: 11px; font-weight: 900; }
.ind-cell strong { color: var(--ink); font-size: 14px; }

/* 탭 */
.detail-tabs { margin-bottom: 16px; }

/* 그리드 */
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px 300px;
  gap: 16px;
  align-items: start;
}
.detail-main { display: grid; gap: 16px; }

.chart-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.chart-note { color: var(--faint); font-size: 12px; font-weight: 900; }
.chart-frame { width: 100%; }
.chart-frame svg { width: 100%; height: 240px; }
.chart-grid-line { fill: none; stroke: var(--line); stroke-width: 1; }
.chart-line { fill: none; stroke: var(--accent); stroke-width: 2.5; stroke-linejoin: round; stroke-linecap: round; }

/* 종토방/뉴스 미니 */
.mini-post-list { display: grid; gap: 8px; }
.mini-post { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: var(--radius); background: rgba(255, 255, 255, 0.48); border: 1px solid var(--glass-border); }
.mini-post-author { color: var(--accent); font-size: 12px; font-weight: 900; flex-shrink: 0; }
.mini-post-title { flex: 1; color: var(--ink); font-size: 13px; font-weight: 900; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mini-post-stats { color: var(--faint); font-size: 11px; font-weight: 900; flex-shrink: 0; }

.mini-news-list { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; }
.mini-news-list li { display: flex; align-items: center; gap: 10px; padding: 11px 0; border-bottom: 1px solid var(--line); }
.mini-news-list li:last-child { border-bottom: 0; }
.mini-news-source { color: var(--muted); font-size: 11px; font-weight: 900; min-width: 64px; flex-shrink: 0; }
.mini-news-title { flex: 1; color: var(--ink); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mini-news-time { color: var(--faint); font-size: 11px; flex-shrink: 0; }

/* 호가 */
.ob-list { display: grid; gap: 2px; }
.ob-row { position: relative; display: grid; grid-template-columns: 1fr 1fr; align-items: center; min-height: 28px; padding: 0 8px; font-size: 12px; font-weight: 900; overflow: hidden; border-radius: 4px; }
.ob-row.ask { background: rgba(207, 61, 61, 0.05); }
.ob-row.bid { background: rgba(49, 93, 255, 0.05); }
.ob-bar { position: absolute; top: 0; bottom: 0; opacity: 0.5; }
.ob-bar.ask { right: 0; background: rgba(207, 61, 61, 0.18); }
.ob-bar.bid { left: 0; background: rgba(49, 93, 255, 0.18); }
.ob-qty, .ob-price { position: relative; z-index: 1; }
.ob-row.ask .ob-qty { text-align: left; color: var(--muted); }
.ob-row.ask .ob-price { text-align: right; color: var(--negative); }
.ob-row.bid .ob-price { text-align: left; color: var(--accent); }
.ob-row.bid .ob-qty { text-align: right; color: var(--muted); }
.ob-current { display: flex; align-items: center; justify-content: space-between; padding: 8px; margin: 2px 0; border-radius: var(--radius); background: rgba(255, 255, 255, 0.6); border: 1px solid var(--glass-border); }
.ob-current span { color: var(--muted); font-size: 12px; font-weight: 900; }
.ob-current strong { font-size: 15px; }

/* 주문 패널 */
.order-panel { position: sticky; top: 80px; }
.order-title { margin: 4px 0 14px; font-size: 18px; }
.order-side { margin-bottom: 8px; }
.order-side .buy.is-selected { color: var(--accent); }
.order-side .sell.is-selected { color: var(--negative); }
.pct-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 10px 0 14px; }
.pct-row button { min-height: 34px; border-radius: var(--radius); border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.5); color: var(--muted); font-size: 12px; font-weight: 900; transition: background 0.16s ease; }
.pct-row button:hover { background: rgba(255, 255, 255, 0.75); color: var(--ink); }
.order-summary { display: grid; gap: 8px; margin: 0 0 14px; }
.order-summary > div { display: flex; justify-content: space-between; }
.order-summary dt { color: var(--muted); font-size: 13px; }
.order-summary dd { margin: 0; color: var(--ink); font-size: 14px; font-weight: 900; }
.order-submit { width: 100%; min-height: 52px; border-radius: var(--radius); border: 0; color: #fff; font-size: 15px; font-weight: 900; display: flex; flex-direction: column; gap: 2px; align-items: center; justify-content: center; }
.order-submit.buy { background: linear-gradient(135deg, var(--accent) 0%, #2f80ed 100%); }
.order-submit.sell { background: linear-gradient(135deg, var(--negative) 0%, #e05a5a 100%); }
.order-submit em { font-style: normal; font-size: 11px; opacity: 0.85; font-weight: 700; }
.fine-print { margin: 10px 0 0; color: var(--faint); font-size: 11px; }

/* 매매일지 작성 */
.diary-toggle {
  width: 100%; min-height: 42px; margin-top: 12px;
  border-radius: var(--radius); border: 1px dashed var(--glass-border);
  background: rgba(255, 255, 255, 0.4); color: var(--ink);
  font-size: 13px; font-weight: 900;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  transition: background 0.16s ease;
}
.diary-toggle:hover { background: rgba(255, 255, 255, 0.65); }
.diary-toggle span { color: var(--muted); }
.order-diary { margin-top: 12px; display: grid; gap: 12px; }
.od-auto { margin: 0; padding: 10px 12px; border-radius: var(--radius); background: rgba(49, 93, 255, 0.06); color: var(--ink); font-size: 13px; font-weight: 900; }
.od-side { padding: 2px 8px; border-radius: 999px; font-size: 11px; margin-right: 4px; }
.od-side.buy { background: rgba(49, 93, 255, 0.12); color: var(--accent); }
.od-side.sell { background: rgba(207, 61, 61, 0.12); color: var(--negative); }
.order-diary textarea { width: 100%; resize: vertical; border-radius: var(--radius); border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.6); padding: 9px 11px; font: inherit; color: var(--ink); }
.od-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.star-pick { display: flex; gap: 4px; }
.star-pick button { font-size: 22px; color: rgba(180, 200, 255, 0.7); background: none; border: 0; cursor: pointer; padding: 0; line-height: 1; }
.star-pick button.on { color: var(--accent); }
.cat-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.cat-chip { padding: 5px 10px; border-radius: 999px; border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.5); color: var(--muted); font-size: 12px; font-weight: 900; transition: background 0.16s ease, color 0.16s ease, border-color 0.16s ease; }
.cat-chip.is-selected { border-color: var(--accent); background: rgba(49, 93, 255, 0.08); color: var(--accent); }
.diary-save { width: 100%; min-height: 44px; border-radius: var(--radius); border: 0; background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%); color: #fff; font-size: 14px; font-weight: 900; }

/* 종목정보 탭 */
.info-desc { margin: 0 0 14px; color: var(--muted); font-size: 14px; line-height: 1.6; word-break: keep-all; }
.info-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }

@media (max-width: 1180px) {
  .detail-header { grid-template-columns: 1fr; }
  .dh-indicators { grid-template-columns: repeat(4, 1fr); }
  .detail-grid { grid-template-columns: 1fr; }
  .order-panel { position: static; }
}
@media (max-width: 720px) {
  .dh-indicators { grid-template-columns: repeat(2, 1fr); }
}
</style>
