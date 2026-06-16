<script setup>
import { computed } from 'vue'
import { useFormat } from '../../composables/useFormat.js'

const props = defineProps({
  stock: { type: Object, required: true },
  isSelected: { type: Boolean, default: false },
  isWatched: { type: Boolean, default: false },
})

const emit = defineEmits(['select', 'toggle-watch'])

const { formatMoney, formatRate, signedClass } = useFormat()

const changeRate = computed(() =>
  props.stock.open ? ((props.stock.price - props.stock.open) / props.stock.open) * 100 : 0,
)
</script>

<template>
  <article class="stock-row" :class="{ 'is-selected': isSelected }">
    <button class="stock-main" type="button" @click="emit('select', stock.code)">
      <span>
        <strong>{{ stock.name }}</strong>
        <small>{{ stock.code }} · {{ stock.market }} · {{ stock.sector }}</small>
      </span>
      <span>
        <strong>{{ formatMoney(stock.price, stock.currency) }}</strong>
        <small :class="signedClass(changeRate)">{{ formatRate(changeRate) }}</small>
      </span>
    </button>
    <button
      class="watch-button"
      type="button"
      :aria-label="`${stock.name} 관심종목 토글`"
      @click="emit('toggle-watch', stock.code)"
    >
      {{ isWatched ? '★' : '☆' }}
    </button>
  </article>
</template>
