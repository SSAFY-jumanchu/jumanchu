<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import SparklineChart from '../components/SparklineChart.vue'

const router = useRouter()

// 초기값은 와이어프레임 목업 — API 응답이 오면 실데이터로 교체
const holdings = ref([
  {
    code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '전기·전자',
    qty: 15, avgPrice: 172000, currentPrice: 189300,
    sparkline: [68, 70, 67, 72, 74, 71, 75, 73, 76, 79, 78, 81],
  },
  {
    code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자',
    qty: 40, avgPrice: 73500, currentPrice: 71200,
    sparkline: [82, 80, 78, 75, 77, 74, 72, 73, 70, 68, 66, 64],
  },
  {
    code: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', sector: '전기·전자',
    qty: 8, avgPrice: 820, currentPrice: 1074,
    sparkline: [55, 57, 56, 59, 61, 63, 62, 65, 67, 69, 71, 73],
  },
  {
    code: 'AAPL', name: 'Apple', market: 'NASDAQ', sector: '전기·전자',
    qty: 20, avgPrice: 185, currentPrice: 192,
    sparkline: [50, 53, 52, 56, 58, 61, 60, 64, 66, 69, 71, 74],
  },
  {
    code: '035420', name: 'NAVER', market: 'KOSPI', sector: 'IT 서비스',
    qty: 5, avgPrice: 195000, currentPrice: 214000,
    sparkline: [44, 48, 47, 52, 55, 58, 62, 65, 68, 72, 75, 79],
  },
])

// ===== 계산 =====
function evalAmount(h) { return h.qty * h.currentPrice }
function pnl(h) { return (h.currentPrice - h.avgPrice) * h.qty }
function returnRate(h) { return ((h.currentPrice - h.avgPrice) / h.avgPrice) * 100 }
function isKrw(h) { return h.market === 'KOSPI' || h.market === 'KOSDAQ' }

function man(v) { return Math.round(v / 10000).toLocaleString('ko-KR') }
function fmtRate(v) { return (v >= 0 ? '+' : '') + v.toFixed(2) + '%' }
function priceStr(v, h) {
  return isKrw(h)
    ? v.toLocaleString('ko-KR') + '원'
    : '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtPnl(h) {
  const v = pnl(h)
  const abs = Math.abs(v)
  const prefix = v >= 0 ? '+' : '-'
  return isKrw(h)
    ? prefix + abs.toLocaleString('ko-KR') + '원'
    : prefix + '$' + abs.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const logoColors = { '000660': '#e3344f', '005930': '#3b5bdb', NVDA: '#76b900', AAPL: '#333a45', '035420': '#22c55e' }
function logoColor(h) { return logoColors[h.code] || '#315dff' }

const totalEval = computed(() => holdings.value.reduce((s, h) => s + (isKrw(h) ? evalAmount(h) : evalAmount(h) * 1380), 0))
const totalCost = computed(() => holdings.value.reduce((s, h) => s + (isKrw(h) ? h.qty * h.avgPrice : h.qty * h.avgPrice * 1380), 0))
const totalPnl = computed(() => totalEval.value - totalCost.value)
const totalReturn = computed(() => totalCost.value ? (totalPnl.value / totalCost.value) * 100 : 0)

// ===== 보유 종목 목록 (필터) =====
const marketFilter = ref('all')
const filteredHoldings = computed(() => {
  if (marketFilter.value === 'domestic') return holdings.value.filter(isKrw)
  if (marketFilter.value === 'overseas') return holdings.value.filter(h => !isKrw(h))
  return holdings.value
})

// ===== 자산 구성 (국내·해외) =====
const marketGroups = computed(() => {
  const domTotal = holdings.value.filter(isKrw).reduce((s, h) => s + evalAmount(h), 0)
  const ovsTotal = holdings.value.filter(h => !isKrw(h)).reduce((s, h) => s + evalAmount(h) * 1380, 0)
  const grand = domTotal + ovsTotal || 1
  return {
    dom: { amount: domTotal, pct: (domTotal / grand) * 100 },
    ovs: { amount: ovsTotal, pct: (ovsTotal / grand) * 100 },
  }
})

// ===== 선택 종목 =====
const selectedCode = ref('000660')
const selectedHolding = computed(() => holdings.value.find(h => h.code === selectedCode.value) || null)

// ===== 뉴스/커뮤니티 =====
const holdingNews = [
  { ticker: 'SK하이닉스', title: 'HBM3E 양산 확대...AI 수요 견조', source: '이데일리', time: '30분 전' },
  { ticker: '삼성전자', title: '파운드리 수주 회복세...2분기 기대감', source: '전자신문', time: '1시간 전' },
  { ticker: 'NVIDIA', title: '실적 서프라이즈...관련 국내주 동반 강세', source: 'Bloomberg', time: '2시간 전' },
]
const communityPost = { user: 'TECL미친놈', time: '6분 전', content: 'SK하이닉스 지금 들어가도 되는 자리인가요?' }
</script>

<template>
  <div class="holdings-page">

    <!-- 헤더 -->
    <header class="hv-header">
      <h1>보유 종목</h1>
      <span class="hv-badge"><span class="hv-badge-dot"></span>가상 계좌 기준</span>
    </header>

    <div class="holdings-grid">

      <!-- ===== 좌측 ===== -->
      <div class="hv-left">

        <!-- 상단: 내 자산 요약 + 바로가기 -->
        <div class="hv-top-row">
          <section class="panel hv-summary" aria-label="내 자산 요약">
            <p class="hv-card-title">내 자산 요약</p>
            <div class="hv-sum-row">
              <span class="hv-sum-label">현재 총 평가액</span>
              <strong class="hv-sum-big">{{ man(totalEval) }}<small>만원</small></strong>
            </div>
            <div class="hv-sum-row">
              <span class="hv-sum-label">총 평가 손익</span>
              <strong class="hv-sum-pnl" :class="totalPnl >= 0 ? 'is-up' : 'is-down'">
                {{ totalPnl >= 0 ? '+' : '' }}{{ man(totalPnl) }}만원 ({{ fmtRate(totalReturn) }})
              </strong>
            </div>
            <div class="hv-sum-row">
              <span class="hv-sum-label">총 투자원금</span>
              <strong class="hv-sum-mid">{{ man(totalCost) }}만원</strong>
            </div>
          </section>

          <section class="panel hv-shortcut" aria-label="바로가기">
            <p class="hv-card-title">바로가기</p>
            <div class="hv-shortcut-list">
              <button class="hv-shortcut-btn" type="button" @click="router.push('/mypage')">
                <span class="hv-shortcut-ico">📄</span> 주문내역
              </button>
              <button class="hv-shortcut-btn" type="button" @click="router.push('/trading-diary')">
                <span class="hv-shortcut-ico">📓</span> 매매일지
              </button>
            </div>
          </section>
        </div>

        <!-- 보유 종목 목록 -->
        <section class="panel hv-list-card" aria-label="보유 종목 목록">
          <div class="hv-list-head">
            <h2>보유 종목 목록</h2>
            <div class="hv-seg">
              <button :class="{ 'is-active': marketFilter === 'all' }" @click="marketFilter = 'all'">전체</button>
              <button :class="{ 'is-active': marketFilter === 'domestic' }" @click="marketFilter = 'domestic'">국내</button>
              <button :class="{ 'is-active': marketFilter === 'overseas' }" @click="marketFilter = 'overseas'">해외</button>
            </div>
          </div>

          <div class="hv-list">
            <div
              v-for="h in filteredHoldings"
              :key="h.code"
              class="hv-holding-row"
              :class="{ active: selectedCode === h.code }"
              @click="selectedCode = h.code"
            >
              <div class="hv-logo" :style="{ background: logoColor(h) }">{{ h.name.slice(0, 1) }}</div>
              <div class="hv-h-info">
                <strong class="hv-h-name">{{ h.name }}</strong>
                <span class="hv-h-sub">{{ h.market }} · {{ h.sector }}</span>
                <span class="hv-h-sub">{{ h.qty }}주 · 평단 {{ isKrw(h) ? h.avgPrice.toLocaleString() + '원' : '$' + h.avgPrice }}</span>
              </div>
              <SparklineChart
                :values="h.sparkline"
                :width="84"
                :height="36"
                class="hv-h-spark"
                :class="returnRate(h) >= 0 ? 'spark-up-card' : 'spark-down-card'"
              />
              <div class="hv-h-figures">
                <strong class="hv-h-eval">{{ priceStr(evalAmount(h), h) }}</strong>
                <span class="hv-h-pnl" :class="pnl(h) >= 0 ? 'is-up' : 'is-down'">
                  {{ fmtPnl(h) }} ({{ fmtRate(returnRate(h)) }})
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- ===== 우측 ===== -->
      <div class="hv-right">

        <!-- 자산 구성 -->
        <section class="panel hv-alloc" aria-label="자산 구성">
          <p class="hv-card-title">자산 구성 (국내·해외)</p>
          <div class="hv-alloc-bar">
            <span class="dom" :style="{ width: marketGroups.dom.pct + '%' }"></span>
            <span class="ovs" :style="{ width: marketGroups.ovs.pct + '%' }"></span>
          </div>
          <div class="hv-alloc-legend">
            <div>
              <span class="dot dom"></span>국내주식
              <strong>{{ man(marketGroups.dom.amount) }}만원 · {{ marketGroups.dom.pct.toFixed(1) }}%</strong>
            </div>
            <div>
              <span class="dot ovs"></span>해외주식
              <strong>{{ man(marketGroups.ovs.amount) }}만원 · {{ marketGroups.ovs.pct.toFixed(1) }}%</strong>
            </div>
          </div>
        </section>

        <!-- 선택 종목 상세 -->
        <section class="panel hv-detail" aria-label="종목 정보" v-if="selectedHolding">
          <div class="hv-detail-head">
            <div>
              <strong class="hv-detail-name">{{ selectedHolding.name }}</strong>
              <span class="hv-detail-meta">{{ selectedHolding.code }} · {{ selectedHolding.market }}</span>
            </div>
            <div class="hv-detail-logo" :style="{ background: logoColor(selectedHolding) }">{{ selectedHolding.name.slice(0, 1) }}</div>
          </div>
          <dl class="hv-detail-rows">
            <div><dt>보유 수량</dt><dd>{{ selectedHolding.qty }}주</dd></div>
            <div><dt>평균 단가</dt><dd>{{ priceStr(selectedHolding.avgPrice, selectedHolding) }}</dd></div>
            <div><dt>현재가</dt><dd>{{ priceStr(selectedHolding.currentPrice, selectedHolding) }}</dd></div>
            <div><dt>평가 금액</dt><dd>{{ priceStr(evalAmount(selectedHolding), selectedHolding) }}</dd></div>
            <div>
              <dt>평가 손익</dt>
              <dd :class="pnl(selectedHolding) >= 0 ? 'is-up' : 'is-down'">{{ fmtPnl(selectedHolding) }}</dd>
            </div>
            <div>
              <dt>수익률</dt>
              <dd :class="returnRate(selectedHolding) >= 0 ? 'is-up' : 'is-down'">{{ fmtRate(returnRate(selectedHolding)) }}</dd>
            </div>
          </dl>
          <div class="hv-detail-actions">
            <button class="hv-buy" type="button">매수</button>
            <button class="hv-sell" type="button">매도</button>
          </div>
          <button class="hv-detail-go" type="button" @click="router.push(`/stocks/${selectedHolding.code}`)">종목 상세 보기 →</button>
        </section>

        <!-- 뉴스 / 커뮤니티 -->
        <section class="panel hv-news" aria-label="뉴스 커뮤니티">
          <p class="hv-card-title">뉴스 · 커뮤니티</p>
          <article v-for="n in holdingNews" :key="n.title" class="hv-news-item">
            <span class="hv-news-chip">{{ n.ticker }}</span>
            <div>
              <p class="hv-news-title">{{ n.title }}</p>
              <span class="hv-news-src">{{ n.source }} · {{ n.time }}</span>
            </div>
          </article>
          <div class="hv-comm">
            <span class="hv-comm-avatar">{{ communityPost.user.slice(0, 1) }}</span>
            <div>
              <p class="hv-comm-content">{{ communityPost.content }}</p>
              <span class="hv-news-src">{{ communityPost.user }} · {{ communityPost.time }}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.holdings-page { display: flex; flex-direction: column; gap: 16px; }

/* 헤더 */
.hv-header { display: flex; align-items: center; gap: 12px; padding: 4px 2px; }
.hv-header h1 { font-size: 24px; font-weight: 900; color: var(--ink); margin: 0; letter-spacing: -0.5px; }
.hv-badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px; background: var(--glass-subtle); border: 1px solid var(--glass-border); font-size: 12px; font-weight: 800; color: var(--muted); }
.hv-badge-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--positive); }

/* 레이아웃 */
.holdings-grid { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 16px; align-items: start; }
.hv-left, .hv-right { display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.hv-top-row { display: grid; grid-template-columns: 1.3fr 1fr; gap: 16px; }
.hv-card-title { font-size: 13px; font-weight: 900; color: var(--muted); margin: 0 0 14px; }

/* 내 자산 요약 */
.hv-summary { padding: 20px; }
.hv-sum-row { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding: 11px 0; border-bottom: 1px solid var(--faint); }
.hv-sum-row:last-child { border-bottom: 0; }
.hv-sum-label { font-size: 13px; font-weight: 700; color: var(--muted); }
.hv-sum-big { font-size: 24px; font-weight: 900; color: var(--ink); letter-spacing: -0.5px; }
.hv-sum-big small { font-size: 14px; font-weight: 700; margin-left: 2px; }
.hv-sum-mid { font-size: 16px; font-weight: 900; color: var(--ink); }
.hv-sum-pnl { font-size: 16px; font-weight: 900; }

/* 바로가기 */
.hv-shortcut { padding: 20px; }
.hv-shortcut-list { display: flex; flex-direction: column; gap: 10px; }
.hv-shortcut-btn { display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-radius: var(--radius); border: 1px solid var(--glass-border); background: var(--surface-soft); color: var(--ink); font-size: 14px; font-weight: 800; cursor: pointer; transition: background 0.16s; text-align: left; }
.hv-shortcut-btn:hover { background: var(--glass-strong); }
.hv-shortcut-ico { font-size: 17px; }

/* 보유 종목 목록 */
.hv-list-card { padding: 20px; }
.hv-list-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.hv-list-head h2 { font-size: 17px; font-weight: 900; color: var(--ink); margin: 0; }
.hv-list { display: flex; flex-direction: column; }
.hv-holding-row {
  display: grid; grid-template-columns: auto minmax(0, 1fr) auto auto; align-items: center; gap: 14px;
  padding: 14px 10px; border-bottom: 1px solid var(--faint); border-left: 3px solid transparent;
  cursor: pointer; transition: background 0.16s, border-color 0.16s;
}
.hv-holding-row:last-child { border-bottom: 0; }
.hv-holding-row:hover { background: var(--surface-soft); }
.hv-holding-row.active { background: rgba(49,93,255,0.06); border-left-color: var(--accent); }
.hv-logo { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 15px; font-weight: 900; flex-shrink: 0; }
.hv-h-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.hv-h-name { font-size: 15px; font-weight: 900; color: var(--ink); }
.hv-h-sub { font-size: 12px; font-weight: 700; color: var(--muted); }
.hv-h-spark { width: 84px; height: 36px; flex-shrink: 0; }
.hv-h-figures { display: flex; flex-direction: column; align-items: flex-end; gap: 3px; }
.hv-h-eval { font-size: 15px; font-weight: 900; color: var(--ink); }
.hv-h-pnl { font-size: 12px; font-weight: 800; white-space: nowrap; }

.spark-up-card :deep(.sparkline-line) { stroke: #e3344f; }
.spark-up-card :deep(.sparkline-fill) { fill: rgba(227,52,79,0.1); }
.spark-down-card :deep(.sparkline-line) { stroke: #2b59d6; }
.spark-down-card :deep(.sparkline-fill) { fill: rgba(43,89,214,0.1); }

/* segmented 필터 */
.hv-seg { display: inline-flex; gap: 4px; padding: 4px; border-radius: 999px; background: var(--glass-subtle); border: 1px solid var(--glass-border); }
.hv-seg button { min-width: 48px; min-height: 28px; border: 0; border-radius: 999px; background: transparent; color: var(--muted); font-size: 12px; font-weight: 900; cursor: pointer; transition: background 0.16s, color 0.16s; }
.hv-seg button.is-active { background: var(--accent); color: #fff; }

/* 자산 구성 */
.hv-alloc { padding: 18px 20px; }
.hv-alloc-bar { display: flex; height: 12px; border-radius: 999px; overflow: hidden; background: var(--surface-soft); margin-bottom: 14px; }
.hv-alloc-bar .dom { background: var(--accent); }
.hv-alloc-bar .ovs { background: var(--purple); }
.hv-alloc-legend { display: flex; flex-direction: column; gap: 10px; }
.hv-alloc-legend > div { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: var(--muted); }
.hv-alloc-legend .dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.hv-alloc-legend .dot.dom { background: var(--accent); }
.hv-alloc-legend .dot.ovs { background: var(--purple); }
.hv-alloc-legend strong { margin-left: auto; color: var(--ink); font-weight: 900; }

/* 선택 종목 상세 */
.hv-detail { padding: 18px 20px; }
.hv-detail-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 14px; }
.hv-detail-name { font-size: 17px; font-weight: 900; color: var(--ink); display: block; }
.hv-detail-meta { font-size: 12px; font-weight: 700; color: var(--muted); }
.hv-detail-logo { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px; font-weight: 900; flex-shrink: 0; }
.hv-detail-rows { display: flex; flex-direction: column; margin: 0 0 16px; }
.hv-detail-rows > div { display: flex; justify-content: space-between; align-items: center; padding: 9px 0; border-bottom: 1px solid var(--faint); }
.hv-detail-rows > div:last-child { border-bottom: 0; }
.hv-detail-rows dt { font-size: 13px; font-weight: 700; color: var(--muted); }
.hv-detail-rows dd { margin: 0; font-size: 14px; font-weight: 900; color: var(--ink); }
.hv-detail-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
.hv-buy, .hv-sell { height: 46px; border: 0; border-radius: var(--radius); font-size: 15px; font-weight: 900; color: #fff; cursor: pointer; transition: opacity 0.16s; }
.hv-buy { background: #e3344f; }
.hv-sell { background: #2b59d6; }
.hv-buy:hover, .hv-sell:hover { opacity: 0.9; }
.hv-detail-go { width: 100%; height: 42px; border-radius: var(--radius); border: 1px solid rgba(49,93,255,0.2); background: rgba(49,93,255,0.08); color: var(--accent); font-size: 13px; font-weight: 900; cursor: pointer; transition: background 0.16s; }
.hv-detail-go:hover { background: rgba(49,93,255,0.16); }

/* 뉴스 / 커뮤니티 */
.hv-news { padding: 18px 20px; }
.hv-news-item { display: flex; gap: 10px; align-items: flex-start; padding: 11px 0; border-bottom: 1px solid var(--faint); cursor: pointer; }
.hv-news-chip { flex-shrink: 0; padding: 3px 8px; border-radius: 999px; font-size: 10px; font-weight: 900; background: rgba(125,78,232,0.1); color: var(--purple); }
.hv-news-title { font-size: 13px; font-weight: 700; color: var(--ink); margin: 0 0 3px; line-height: 1.4; word-break: keep-all; }
.hv-news-src { font-size: 11px; font-weight: 700; color: var(--faint); }
.hv-comm { display: flex; gap: 10px; align-items: flex-start; padding-top: 12px; }
.hv-comm-avatar { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--accent), var(--purple)); color: #fff; font-size: 12px; font-weight: 900; }
.hv-comm-content { font-size: 13px; font-weight: 700; color: var(--ink); margin: 0 0 3px; line-height: 1.4; word-break: keep-all; }

/* 등락 색상 (한국식: 상승=빨강, 하락=파랑) */
.is-up { color: #e3344f; }
.is-down { color: #2b59d6; }

@media (max-width: 1100px) {
  .holdings-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .hv-top-row { grid-template-columns: 1fr; }
  .hv-holding-row { grid-template-columns: auto minmax(0, 1fr) auto; }
  .hv-h-spark { display: none; }
}
</style>
