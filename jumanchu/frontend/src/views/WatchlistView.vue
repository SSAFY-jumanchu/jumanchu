<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ===== 데이터 =====
const stocks = [
  {
    code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자', currency: 'KRW',
    price: 317000, open: 309500, high: 319000, low: 305500, volume: 24943808,
    beta: 1.27, volatility: 54.0, roe: 8.57, high52w: 323000, low52w: 55600,
    sparkline: [61, 64, 60, 68, 72, 75, 78, 81, 84, 82, 88, 91],
    points: ['국내 반도체·가전 대표주', '배당 수익률 안정적', '분산형 포트폴리오 편입 적합'],
  },
  {
    code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '전기·전자', currency: 'KRW',
    price: 2303000, open: 2352000, high: 2379000, low: 2290500, volume: 3927670,
    beta: 1.55, volatility: 68.7, roe: 26.78, high52w: 2379000, low52w: 203000,
    sparkline: [44, 51, 55, 61, 69, 74, 82, 89, 92, 95, 91, 86],
    points: ['AI 반도체 HBM 모멘텀', '공격형 성향과 높은 적합도', '변동성 크지만 기대수익 높음'],
  },
  {
    code: '005380', name: '현대차', market: 'KOSPI', sector: '운송장비·부품', currency: 'KRW',
    price: 728000, open: 704000, high: 739000, low: 701000, volume: 2534369,
    beta: 1.03, volatility: 61.9, roe: null, high52w: 774500, low52w: 183100,
    sparkline: [52, 54, 53, 57, 58, 62, 66, 63, 68, 71, 74, 79],
    points: ['글로벌 전기차 전환 수혜', '경기 민감 섹터 대표주', '포트폴리오 분산 효과'],
  },
  {
    code: 'AAPL', name: 'APPLE INC', market: 'NASDAQ', sector: '컴퓨터전자장비/기기', currency: 'USD',
    price: 312.51, open: 310.68, high: 312.8, low: 309.57, volume: 48220390,
    beta: 0.94, volatility: 22.1, roe: 141.47, high52w: 313, low52w: 195,
    sparkline: [64, 66, 65, 67, 70, 73, 71, 76, 79, 83, 86, 89],
    points: ['미국 대형주 진입 카드', '안정적 현금흐름 보유', '소액 분할매수 적합'],
  },
  {
    code: 'NVDA', name: 'NVIDIA CORP', market: 'NASDAQ', sector: '반도체 및 반도체장비', currency: 'USD',
    price: 214.25, open: 214.25, high: 214.25, low: 214.25, volume: 0,
    beta: 1.79, volatility: 33.6, roe: 114.29, high52w: 237, low52w: 133,
    sparkline: [58, 61, 66, 70, 78, 82, 87, 91, 94, 90, 92, 96],
    points: ['AI 가속기 독점 수혜', '고성장·고변동 종목', '공격형 투자자 최우선 추천'],
  },
  {
    code: 'GOOGL', name: 'ALPHABET INC', market: 'NASDAQ', sector: '미디어', currency: 'USD',
    price: 390.13, open: 390.13, high: 390.13, low: 390.13, volume: 0,
    beta: 1.34, volatility: 28.8, roe: 38.88, high52w: 409, low52w: 162,
    sparkline: [50, 55, 57, 62, 64, 69, 73, 75, 79, 82, 84, 86],
    points: ['AI 플랫폼 광고 수익', '멀티 서비스 분산 효과', '중장기 성장 기대'],
  },
]

// ===== 관심종목 =====
const watchedCodes = ref(['005930', 'NVDA'])

function toggleWatch(code) {
  const i = watchedCodes.value.indexOf(code)
  if (i >= 0) watchedCodes.value.splice(i, 1)
  else watchedCodes.value.push(code)
}

// ===== 선택 종목 =====
const selectedCode = ref('005930')
const selectedStock = computed(() => stocks.find(s => s.code === selectedCode.value) || stocks[0])
const watchlist = computed(() => stocks.filter(s => watchedCodes.value.includes(s.code)))

// ===== 필터 =====
const marketFilters = ['전체', '국내', '미국']
const selectedMarket = ref('전체')
const filteredStocks = computed(() => {
  if (selectedMarket.value === '국내') return stocks.filter(s => ['KOSPI', 'KOSDAQ'].includes(s.market))
  if (selectedMarket.value === '미국') return stocks.filter(s => ['NASDAQ', 'NYSE'].includes(s.market))
  return stocks
})

// ===== 종목 상세 탭 =====
const tabs = ['요약', '차트', '재무', '커뮤니티']
const selectedTab = ref('요약')

// ===== 주문 미리보기 =====
const orderSide = ref('BUY')
const orderQuantity = ref(3)

const change = computed(() => selectedStock.value.price - selectedStock.value.open)
const changeRate = computed(() =>
  selectedStock.value.open ? (change.value / selectedStock.value.open) * 100 : 0
)
const orderEstimate = computed(() => selectedStock.value.price * orderQuantity.value)
const orderFee = computed(() => orderEstimate.value * (selectedStock.value.currency === 'KRW' ? 0.00015 : 0.0007))
const orderTotal = computed(() => orderEstimate.value + orderFee.value)

// ===== 차트 SVG 포인트 =====
const chartPoints = computed(() => {
  const values = selectedStock.value.sparkline
  const w = 520, h = 180
  const min = Math.min(...values), max = Math.max(...values), range = max - min || 1
  return values.map((v, i) => {
    const x = (i / (values.length - 1)) * w
    const y = h - ((v - min) / range) * 150 - 15
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
})

// ===== 유틸 =====
function fmtMoney(v, currency) {
  const isKrw = currency === 'KRW'
  const opts = isKrw ? { maximumFractionDigits: 0 } : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
  return `${isKrw ? '₩' : '$'}${new Intl.NumberFormat('ko-KR', opts).format(v)}`
}

function fmtRate(v) {
  if (v === null || v === undefined) return '준비 중'
  return `${v > 0 ? '+' : ''}${v.toFixed(2)}%`
}

function fmtCompact(v) {
  return new Intl.NumberFormat('ko-KR', { notation: 'compact', maximumFractionDigits: 1 }).format(v)
}

function signedClass(v) {
  if (v > 0) return 'is-up'
  if (v < 0) return 'is-down'
  return 'is-flat'
}
</script>

<template>
  <div class="watchlist-page">

    <!-- ===== 상단 헤더 ===== -->
    <header class="wl-header">
      <h1>관심 종목</h1>
      <div class="wl-header-actions">
        <label class="search-box">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="2"/>
            <path d="M13.5 13.5L17 17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <input type="search" placeholder="종목명, 코드, 섹터" />
        </label>
        <div class="segmented">
          <button
            v-for="f in marketFilters"
            :key="f"
            type="button"
            :class="{ 'is-selected': selectedMarket === f }"
            @click="selectedMarket = f"
          >{{ f }}</button>
        </div>
      </div>
    </header>

    <!-- ===== 상단 그리드: 추천 + 관심종목 슬롯 ===== -->
    <div class="top-grid">

      <!-- 추천 후보와 관심종목 -->
      <section class="panel recommendation-panel">
        <div class="rec-panel-head">
          <div>
            <p class="eyebrow">Personal Match</p>
            <h2>추천 후보와 관심종목</h2>
          </div>
          <span class="profile-pill">균형형 · 12개월 · 전기전자 선호</span>
        </div>

        <div class="stock-list">
          <article
            v-for="s in filteredStocks"
            :key="s.code"
            class="stock-row"
            :class="{ 'is-selected': selectedCode === s.code }"
          >
            <button class="stock-main" type="button" @click="selectedCode = s.code; selectedTab = '요약'">
              <div class="stock-info">
                <strong>{{ s.name }}</strong>
                <small>{{ s.code }} · {{ s.market }} · {{ s.sector }}</small>
              </div>
              <div class="stock-price-col">
                <strong>{{ fmtMoney(s.price, s.currency) }}</strong>
                <small :class="signedClass((s.price - s.open) / s.open * 100)">
                  {{ fmtRate((s.price - s.open) / s.open * 100) }}
                </small>
              </div>
            </button>
            <button
              class="watch-button"
              type="button"
              :class="{ 'is-watched': watchedCodes.includes(s.code) }"
              @click="toggleWatch(s.code)"
            >
              {{ watchedCodes.includes(s.code) ? '★' : '☆' }}
            </button>
          </article>
        </div>
      </section>

      <!-- 관심종목 슬롯 -->
      <section class="panel watch-panel">
        <div class="rec-panel-head">
          <div>
            <p class="eyebrow">Watchlist</p>
            <h2>관심종목</h2>
          </div>
        </div>

        <div v-if="watchlist.length > 0" class="watch-list">
          <button
            v-for="s in watchlist"
            :key="s.code"
            type="button"
            class="watch-item"
            :class="{ 'is-selected': selectedCode === s.code }"
            @click="selectedCode = s.code; selectedTab = '요약'"
          >
            <span class="watch-item-name">{{ s.name }}</span>
            <strong class="watch-item-price">{{ fmtMoney(s.price, s.currency) }}</strong>
          </button>
        </div>

        <div v-else class="empty-state">
          <span>☆</span>
          <p>관심종목을 선택하면<br>실시간 시세 슬롯으로 올라옵니다.</p>
        </div>
      </section>
    </div>

    <!-- ===== 하단: 종목 상세 + 주문 미리보기 ===== -->
    <section class="stock-workspace">

      <!-- 종목 Quote 패널 -->
      <section class="panel quote-panel">

        <div class="quote-heading">
          <div>
            <p class="eyebrow">{{ selectedStock.market }} · {{ selectedStock.sector }}</p>
            <h2>{{ selectedStock.name }}</h2>
            <span class="stock-code">{{ selectedStock.code }}</span>
          </div>

          <div class="quote-right">
            <div class="quote-price-block">
              <strong class="quote-price-val">{{ fmtMoney(selectedStock.price, selectedStock.currency) }}</strong>
              <span :class="signedClass(changeRate)">
                {{ fmtMoney(change, selectedStock.currency) }} {{ fmtRate(changeRate) }}
              </span>
            </div>
            <button class="detail-link-btn" type="button"
              @click="router.push(`/stocks/${selectedStock.code}`)">
              해당 종목 상세 페이지로 이동
              <svg width="13" height="13" viewBox="0 0 20 20" fill="none">
                <path d="M7 4l6 6-6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- 탭 -->
        <div class="tab-list">
          <button
            v-for="tab in tabs"
            :key="tab"
            type="button"
            :class="{ 'is-selected': selectedTab === tab }"
            @click="selectedTab = tab"
          >{{ tab }}</button>
        </div>

        <!-- 차트 영역 -->
        <div class="chart-frame">
          <svg viewBox="0 0 520 200" preserveAspectRatio="none" aria-hidden="true">
            <defs>
              <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="rgba(49,93,255,0.20)" />
                <stop offset="100%" stop-color="rgba(49,93,255,0)" />
              </linearGradient>
            </defs>
            <line x1="0" y1="50"  x2="520" y2="50"  class="chart-grid-line" />
            <line x1="0" y1="100" x2="520" y2="100" class="chart-grid-line" />
            <line x1="0" y1="150" x2="520" y2="150" class="chart-grid-line" />
            <polygon :points="chartPoints + ` 520,185 0,185`" fill="url(#chartFill)" />
            <polyline class="chart-line" :points="chartPoints" />
          </svg>
        </div>

        <!-- 통계 -->
        <dl class="quote-stats">
          <div><dt>52주 최고</dt><dd>{{ fmtMoney(selectedStock.high52w, selectedStock.currency) }}</dd></div>
          <div><dt>52주 최저</dt><dd>{{ fmtMoney(selectedStock.low52w, selectedStock.currency) }}</dd></div>
          <div><dt>Beta</dt><dd>{{ selectedStock.beta.toFixed(2) }}</dd></div>
          <div><dt>변동성</dt><dd>{{ selectedStock.volatility.toFixed(1) }}%</dd></div>
          <div><dt>ROE</dt><dd>{{ selectedStock.roe ? `${selectedStock.roe.toFixed(2)}%` : '준비 중' }}</dd></div>
          <div><dt>거래량</dt><dd>{{ fmtCompact(selectedStock.volume) }}</dd></div>
        </dl>
      </section>

      <!-- 주문 미리보기 -->
      <aside class="panel trade-panel">
        <div class="rec-panel-head">
          <div>
            <p class="eyebrow">Order Preview</p>
            <h2>주문 미리보기</h2>
          </div>
        </div>

        <div class="segmented full">
          <button type="button" :class="{ 'is-selected': orderSide === 'BUY' }" @click="orderSide = 'BUY'">매수</button>
          <button type="button" :class="{ 'is-selected': orderSide === 'SELL' }" @click="orderSide = 'SELL'">매도</button>
        </div>

        <label class="field">
          <span>수량</span>
          <input v-model.number="orderQuantity" type="number" min="1" />
        </label>

        <dl class="order-summary">
          <div><dt>예상 금액</dt><dd>{{ fmtMoney(orderEstimate, selectedStock.currency) }}</dd></div>
          <div><dt>수수료 가정</dt><dd>{{ fmtMoney(orderFee, selectedStock.currency) }}</dd></div>
          <div><dt>총 필요 금액</dt><dd>{{ fmtMoney(orderTotal, selectedStock.currency) }}</dd></div>
        </dl>

        <button class="primary-action" type="button">주문 API 연결 예정</button>
        <p class="fine-print">
          실제 체결은 <code>/orders/preview/</code> 검증 뒤 <code>/orders/</code>로 분리합니다.
        </p>
      </aside>
    </section>

  </div>
</template>

<style scoped>
/* ===== 페이지 ===== */
.watchlist-page { display: flex; flex-direction: column; gap: 20px; }

/* ===== 상단 헤더 ===== */
.wl-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.wl-header h1 {
  font-size: clamp(28px, 4vw, 42px);
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -1.5px;
  margin: 0;
  line-height: 1;
}

.wl-header-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

/* 검색창 */
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  height: 36px;
  border-radius: 999px;
  background: var(--glass);
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  color: var(--faint);
  cursor: text;
}

.search-box input {
  border: 0;
  background: transparent;
  outline: none;
  color: var(--ink);
  font-size: 13px;
  font-weight: 700;
  width: 180px;
}

.search-box input::placeholder { color: var(--faint); }

/* 세그먼트 */
.segmented {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: var(--glass-subtle);
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
}

.segmented button {
  min-height: 28px;
  min-width: 52px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.segmented button.is-selected {
  background: var(--chip-active);
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08), var(--glass-inset);
}

.segmented.full {
  display: flex;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  padding: 4px;
}

.segmented.full button {
  flex: 1;
  border-radius: calc(var(--radius) - 2px);
  min-height: 36px;
  font-size: 14px;
}

/* ===== 상단 그리드 ===== */
.top-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(200px, 1fr);
  gap: 16px;
  align-items: start;
}

/* ===== 패널 헤더 ===== */
.rec-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.rec-panel-head h2 {
  font-size: 16px;
  font-weight: 900;
  color: var(--ink);
  margin: 2px 0 0;
}

.profile-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(49,93,255,0.08);
  border: 1px solid rgba(49,93,255,0.18);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
}

/* ===== 종목 행 ===== */
.stock-list { display: flex; flex-direction: column; gap: 2px; }

.stock-row {
  display: flex;
  align-items: center;
  border-radius: var(--radius);
  transition: background 0.14s;
}

.stock-row:hover { background: var(--surface-soft); }

.stock-row.is-selected {
  background: rgba(49,93,255,0.07);
  outline: 1px solid rgba(49,93,255,0.2);
}

.stock-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex: 1;
  padding: 10px 12px 10px 10px;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.stock-info strong {
  display: block;
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
  white-space: nowrap;
}

.stock-info small {
  display: block;
  font-size: 11px;
  color: var(--faint);
  font-weight: 700;
  margin-top: 1px;
}

.stock-price-col { text-align: right; flex-shrink: 0; }
.stock-price-col > strong { display: block; font-size: 14px; font-weight: 900; color: var(--ink); }
.stock-price-col > small { display: block; font-size: 12px; font-weight: 900; margin-top: 2px; }

.watch-button {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border: 0;
  background: transparent;
  font-size: 17px;
  color: var(--faint);
  cursor: pointer;
  border-radius: var(--radius);
  transition: color 0.18s, background 0.18s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.watch-button:hover { background: var(--glass); color: var(--ink); }
.watch-button.is-watched { color: #f5b700; }

/* ===== 관심종목 슬롯 ===== */
.watch-panel { padding: 20px; }

.watch-list { display: flex; flex-direction: column; gap: 6px; }

.watch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--glass-subtle);
  cursor: pointer;
  transition: background 0.16s, border-color 0.16s;
  text-align: left;
}

.watch-item:hover { background: var(--surface-hover); }
.watch-item.is-selected { background: rgba(49,93,255,0.07); border-color: rgba(49,93,255,0.22); }

.watch-item-name { font-size: 14px; font-weight: 900; color: var(--ink); }
.watch-item-price { font-size: 14px; font-weight: 900; color: var(--ink); flex-shrink: 0; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 16px;
  color: var(--faint);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  line-height: 1.6;
}

.empty-state span { font-size: 28px; }

/* ===== 워크스페이스 ===== */
.stock-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}

/* ===== Quote Panel ===== */
.quote-panel { padding: 20px; }

.quote-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.quote-heading h2 {
  font-size: 22px;
  font-weight: 900;
  color: var(--ink);
  margin: 4px 0 2px;
}

.stock-code { font-size: 13px; font-weight: 700; color: var(--faint); }

.quote-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.quote-price-block { text-align: right; }

.quote-price-val {
  display: block;
  font-size: 26px;
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -0.5px;
}

.quote-price-block span {
  display: block;
  font-size: 14px;
  font-weight: 900;
  margin-top: 3px;
}

/* 상세 페이지 이동 버튼 */
.detail-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border-radius: 999px;
  border: 1px solid rgba(49,93,255,0.3);
  background: rgba(49,93,255,0.07);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.18s;
}

.detail-link-btn:hover { background: rgba(49,93,255,0.14); }

/* 탭 */
.tab-list {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: var(--radius);
  background: var(--glass-subtle);
  border: 1px solid var(--glass-border);
  margin-bottom: 16px;
  width: fit-content;
}

.tab-list button {
  padding: 6px 18px;
  border: 0;
  border-radius: calc(var(--radius) - 2px);
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s;
}

.tab-list button.is-selected {
  background: var(--chip-active);
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

/* 차트 */
.chart-frame {
  height: 200px;
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--surface-faint);
  border: 1px solid var(--glass-border);
  margin-bottom: 16px;
}

.chart-frame svg { width: 100%; height: 100%; }

.chart-grid-line {
  stroke: rgba(180,200,255,0.4);
  stroke-width: 1;
  stroke-dasharray: 5 5;
}

.chart-line {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* 통계 */
.quote-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 16px;
  margin: 0;
  padding: 14px 0 0;
  border-top: 1px solid var(--line);
}

.quote-stats > div { display: flex; flex-direction: column; gap: 3px; }
.quote-stats dt { font-size: 11px; font-weight: 700; color: var(--faint); }
.quote-stats dd { font-size: 15px; font-weight: 900; color: var(--ink); margin: 0; }

/* ===== Trade Panel ===== */
.trade-panel { padding: 20px; display: flex; flex-direction: column; gap: 14px; }

.field { display: flex; flex-direction: column; gap: 5px; }

.field span { font-size: 12px; font-weight: 900; color: var(--muted); }

.field input {
  height: 40px;
  padding: 0 12px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  color: var(--ink);
  font-size: 15px;
  font-weight: 900;
  outline: none;
  transition: border-color 0.18s;
}

.field input:focus { border-color: var(--accent); }

.order-summary {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: var(--radius);
  background: var(--glass-subtle);
  border: 1px solid var(--glass-border);
}

.order-summary > div {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-summary dt { font-size: 12px; font-weight: 700; color: var(--muted); }
.order-summary dd { font-size: 14px; font-weight: 900; color: var(--ink); margin: 0; }

.primary-action {
  width: 100%;
  height: 44px;
  border-radius: var(--radius);
  border: 0;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(49,93,255,0.3);
  transition: opacity 0.18s, transform 0.18s;
}

.primary-action:hover { opacity: 0.88; transform: translateY(-1px); }

.fine-print {
  font-size: 11px;
  font-weight: 700;
  color: var(--faint);
  text-align: center;
  line-height: 1.5;
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

/* ===== 색상 ===== */
.is-up   { color: var(--positive); }
.is-down { color: var(--negative); }
.is-flat { color: var(--muted); }

/* ===== 반응형 ===== */
@media (max-width: 1100px) {
  .top-grid { grid-template-columns: 1fr; }
  .stock-workspace { grid-template-columns: 1fr; }
}

@media (max-width: 700px) {
  .quote-heading { flex-direction: column; }
  .quote-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
