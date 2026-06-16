<script setup>
import { ref, computed } from 'vue'
import { useFormat } from '../../composables/useFormat.js'

const props = defineProps({
  stock: { type: Object, required: true },
})

const { formatMoney, formatRate, formatCompact, signedClass } = useFormat()

const tabs = ['요약', '차트', '재무', '커뮤니티']
const selectedTab = ref('요약')
const orderSide = ref('BUY')
const orderQuantity = ref(3)

const change = computed(() => props.stock.price - props.stock.open)
const changeRate = computed(() => (props.stock.open ? (change.value / props.stock.open) * 100 : 0))

const orderEstimate = computed(() => props.stock.price * orderQuantity.value)
const orderFee = computed(() => orderEstimate.value * (props.stock.currency === 'KRW' ? 0.00015 : 0.0007))
const orderTotal = computed(() => orderEstimate.value + orderFee.value)

const chartPoints = computed(() => {
  const values = props.stock.sparkline
  const width = 520
  const height = 180
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  return values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width
      const y = height - ((v - min) / range) * 150 - 15
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})
</script>

<template>
  <section class="stock-workspace">
    <section class="panel quote-panel">
      <div class="quote-heading">
        <div>
          <p class="eyebrow">{{ stock.market }} · {{ stock.sector }}</p>
          <h2>{{ stock.name }}</h2>
          <span>{{ stock.code }}</span>
        </div>
        <div class="quote-price">
          <strong>{{ formatMoney(stock.price, stock.currency) }}</strong>
          <span :class="signedClass(changeRate)">
            {{ formatMoney(change, stock.currency) }} {{ formatRate(changeRate) }}
          </span>
          <RouterLink :to="`/stocks/${stock.code}`" class="detail-link">종목 상세 보기 →</RouterLink>
        </div>
      </div>

      <div class="tab-list" aria-label="종목 상세 탭">
        <button
          v-for="tab in tabs"
          :key="tab"
          type="button"
          :class="{ 'is-selected': selectedTab === tab }"
          @click="selectedTab = tab"
        >
          {{ tab }}
        </button>
      </div>

      <div class="chart-frame" role="img" :aria-label="`${stock.name} 샘플 가격 흐름`">
        <svg viewBox="0 0 520 200" preserveAspectRatio="none">
          <polyline class="chart-grid-line" points="0,50 520,50" />
          <polyline class="chart-grid-line" points="0,100 520,100" />
          <polyline class="chart-grid-line" points="0,150 520,150" />
          <polyline class="chart-line" :points="chartPoints" />
        </svg>
      </div>

      <dl class="quote-stats">
        <div><dt>52주 최고</dt><dd>{{ formatMoney(stock.high52w, stock.currency) }}</dd></div>
        <div><dt>52주 최저</dt><dd>{{ formatMoney(stock.low52w, stock.currency) }}</dd></div>
        <div><dt>Beta</dt><dd>{{ stock.beta.toFixed(2) }}</dd></div>
        <div><dt>변동성</dt><dd>{{ stock.volatility.toFixed(1) }}%</dd></div>
        <div><dt>ROE</dt><dd>{{ stock.roe ? `${stock.roe.toFixed(2)}%` : '준비 중' }}</dd></div>
        <div><dt>거래량</dt><dd>{{ formatCompact(stock.volume) }}</dd></div>
      </dl>
    </section>

    <aside class="panel trade-panel" aria-labelledby="trade-heading">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Order Preview</p>
          <h2 id="trade-heading">주문 미리보기</h2>
        </div>
      </div>

      <div class="segmented full" aria-label="매수 매도 선택">
        <button type="button" :class="{ 'is-selected': orderSide === 'BUY' }" @click="orderSide = 'BUY'">매수</button>
        <button type="button" :class="{ 'is-selected': orderSide === 'SELL' }" @click="orderSide = 'SELL'">매도</button>
      </div>

      <label class="field">
        <span>수량</span>
        <input v-model.number="orderQuantity" type="number" min="1" />
      </label>

      <dl class="order-summary">
        <div><dt>예상 금액</dt><dd>{{ formatMoney(orderEstimate, stock.currency) }}</dd></div>
        <div><dt>수수료 가정</dt><dd>{{ formatMoney(orderFee, stock.currency) }}</dd></div>
        <div><dt>총 필요 금액</dt><dd>{{ formatMoney(orderTotal, stock.currency) }}</dd></div>
      </dl>

      <button class="primary-action" type="button">주문 API 연결 예정</button>
      <p class="fine-print">실제 체결은 <code>/orders/preview/</code> 검증 뒤 <code>/orders/</code>로 분리합니다.</p>
    </aside>
  </section>
</template>

<style scoped>
.quote-price .detail-link {
  display: inline-flex;
  align-items: center;
  margin-left: auto;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(49, 93, 255, 0.1);
  border: 1px solid rgba(49, 93, 255, 0.25);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  white-space: nowrap;
  transition: background 0.16s ease;
}
.quote-price .detail-link:hover {
  background: rgba(49, 93, 255, 0.18);
}
</style>
