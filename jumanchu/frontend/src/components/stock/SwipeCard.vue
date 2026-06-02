<script setup>
import { ref, computed } from 'vue'
import SparklineChart from './SparklineChart.vue'
import { useFormat } from '../../composables/useFormat.js'

const props = defineProps({
  card: { type: Object, required: true },
})

const emit = defineEmits(['like', 'pass', 'save'])

const { formatMoney, formatRate } = useFormat()

const isExiting = ref(false)
const exitDir = ref('')
const isDragging = ref(false)
const dragStartX = ref(0)
const dragCurrentX = ref(0)

const cardTransform = computed(() => {
  if (isExiting.value) {
    if (exitDir.value === 'save') return 'translate3d(0,-70px,0) rotate(0deg) scale(.92)'
    return `translate3d(${exitDir.value === 'right' ? 540 : -540}px, 40px, 0) rotate(${exitDir.value === 'right' ? 18 : -18}deg)`
  }
  if (isDragging.value) {
    const r = dragCurrentX.value / 18
    const s = Math.max(0.94, 1 - Math.abs(dragCurrentX.value) / 1800)
    return `translate3d(${dragCurrentX.value}px, 0, 0) rotate(${r}deg) scale(${s})`
  }
  return 'translate3d(0,0,0) rotate(0deg) scale(1)'
})

const cardOpacity = computed(() => (isExiting.value ? 0 : 1))
const cardTransition = computed(() =>
  isDragging.value ? 'none' : 'transform .42s cubic-bezier(.2,.8,.2,1), opacity .3s ease',
)

const likeOpacity = computed(() => {
  if (isExiting.value && exitDir.value === 'right') return 1
  if (isDragging.value && dragCurrentX.value > 40) return Math.min(dragCurrentX.value / 130, 1)
  return 0
})

const passOpacity = computed(() => {
  if (isExiting.value && exitDir.value === 'left') return 1
  if (isDragging.value && dragCurrentX.value < -40) return Math.min(Math.abs(dragCurrentX.value) / 130, 1)
  return 0
})

const changeRate = computed(() =>
  props.card.open ? ((props.card.price - props.card.open) / props.card.open) * 100 : 0,
)

function triggerSwipe(dir) {
  if (isExiting.value) return
  isExiting.value = true
  exitDir.value = dir
  setTimeout(() => {
    isExiting.value = false
    exitDir.value = ''
    dragCurrentX.value = 0
    emit(dir === 'right' ? 'like' : dir === 'left' ? 'pass' : 'save')
  }, 360)
}

function onPointerDown(e) {
  if (isExiting.value) return
  isDragging.value = true
  dragStartX.value = e.clientX ?? 0
  dragCurrentX.value = 0
  e.currentTarget.setPointerCapture?.(e.pointerId)
}

function onPointerMove(e) {
  if (!isDragging.value) return
  dragCurrentX.value = (e.clientX ?? 0) - dragStartX.value
}

function onPointerUp() {
  if (!isDragging.value) return
  isDragging.value = false
  if (dragCurrentX.value > 120) { triggerSwipe('right'); return }
  if (dragCurrentX.value < -120) { triggerSwipe('left'); return }
  dragCurrentX.value = 0
}
</script>

<template>
  <div class="swipe-deck">
    <div class="swipe-deck-bg" :style="{ background: card.bg }"></div>

    <div class="swipe-stamp like" :style="{ opacity: likeOpacity }">관심</div>
    <div class="swipe-stamp pass" :style="{ opacity: passOpacity }">패스</div>

    <article
      class="swipe-card"
      :style="{ transform: cardTransform, opacity: cardOpacity, transition: cardTransition }"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <div class="swipe-card-header">
        <span class="swipe-badge">{{ card.market }} · {{ card.sector }}</span>
        <div class="swipe-score">{{ card.fit }}<span>적합도</span></div>
      </div>

      <div class="swipe-card-body">
        <h3 class="swipe-name">{{ card.name }}</h3>
        <div class="swipe-code">{{ card.code }}</div>

        <div class="swipe-info-grid">
          <div class="swipe-info-box">
            <div class="swipe-info-k">현재가</div>
            <div class="swipe-info-v">
              {{ formatMoney(card.price, card.currency) }}
              <em class="swipe-change-pill">{{ formatRate(changeRate) }}</em>
            </div>
          </div>
          <div class="swipe-info-box">
            <div class="swipe-info-k">추천 타입</div>
            <div class="swipe-info-v">{{ card.stance }}</div>
          </div>
        </div>

        <div class="swipe-reason">{{ card.reason }}</div>

        <div class="swipe-card-details">
          <div class="swipe-detail-box">
            <div class="swipe-detail-title">매칭 포인트</div>
            <ul class="swipe-detail-list">
              <li v-for="pt in card.points" :key="pt">{{ pt }}</li>
            </ul>
          </div>
          <div class="swipe-detail-box">
            <div class="swipe-detail-title">최근 흐름</div>
            <SparklineChart :values="card.sparkline" class="swipe-mini-chart" />
          </div>
        </div>
      </div>
    </article>

    <div class="swipe-controls">
      <button class="swipe-btn" type="button" @click="triggerSwipe('left')" aria-label="패스">✕</button>
      <button class="swipe-btn main" type="button" @click="triggerSwipe('save')" aria-label="저장">♥</button>
      <button class="swipe-btn like-btn" type="button" @click="triggerSwipe('right')" aria-label="관심">→</button>
    </div>
  </div>
</template>

<style scoped>
.swipe-mini-chart {
  height: 54px;
  margin-top: 4px;
}
</style>
