<script setup>
import { computed } from 'vue'

const props = defineProps({
  values: { type: Array, required: true },
  width: { type: Number, default: 180 },
  height: { type: Number, default: 60 },
})

const points = computed(() => {
  const { values, width, height } = props
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  return values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * width
      const y = height - 8 - ((v - min) / range) * (height - 16)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})

const areaPath = computed(() => {
  const { values, width, height } = props
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width
    const y = height - 8 - ((v - min) / range) * (height - 16)
    return [x.toFixed(1), y.toFixed(1)]
  })
  return `M0,${props.height} L${pts.map((p) => p.join(',')).join(' L')} L${props.width},${props.height} Z`
})
</script>

<template>
  <svg
    class="sparkline"
    :viewBox="`0 0 ${width} ${height}`"
    preserveAspectRatio="none"
    aria-hidden="true"
  >
    <path class="sparkline-fill" :d="areaPath" />
    <polyline class="sparkline-line" :points="points" />
  </svg>
</template>

<style scoped>
.sparkline {
  width: 100%;
  overflow: visible;
}

.sparkline-line {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sparkline-fill {
  fill: color-mix(in srgb, var(--accent) 10%, transparent);
}
</style>
