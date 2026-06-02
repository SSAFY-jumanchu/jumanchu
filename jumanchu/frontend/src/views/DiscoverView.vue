<script setup>
import { ref, computed } from 'vue'
import SwipeCard from '../components/stock/SwipeCard.vue'
import { stocks } from '../data/stocks.js'
import { useWatchlist } from '../composables/useWatchlist.js'

const { watchedCodes, toggleWatch } = useWatchlist()

const tabs = ['패턴 기반', '뉴스 기반']
const activeTab = ref('패턴 기반')

const swipeIndex = ref(0)
const toastVisible = ref(false)
const toastMsg = ref('')
let toastTimer = null

const currentCard = computed(() => stocks[swipeIndex.value % stocks.length])

function showToast(msg) {
  toastMsg.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2000)
}

function onLike() {
  toggleWatch(currentCard.value.code)
  showToast(`${currentCard.value.name} 관심종목에 저장했어요`)
  swipeIndex.value++
}

function onPass() {
  showToast('다음 종목을 볼게요')
  swipeIndex.value++
}

function onSave() {
  toggleWatch(currentCard.value.code)
  showToast(`${currentCard.value.name} 저장했어요`)
  swipeIndex.value++
}
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">Stock Match</p>
        <h1>종목 발견</h1>
      </div>
      <div class="tab-selector segmented" aria-label="추천 방식 선택">
        <button
          v-for="tab in tabs"
          :key="tab"
          type="button"
          :class="{ 'is-selected': activeTab === tab }"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </div>
    </header>

    <section class="panel swipe-section" aria-label="종목 매칭 스와이프">
      <div class="swipe-layout">
        <div class="swipe-intro">
          <p class="eyebrow">{{ activeTab }}</p>
          <h2>오늘의 종목 매칭</h2>

          <div class="goal-widget">
            <div class="goal-widget-title">나의 투자 목표</div>
            <div class="goal-item achieved">
              <div class="goal-item-badge">✓</div>
              <div class="goal-item-info">
                <div class="goal-item-label">현재 자산</div>
                <div class="goal-item-name">게이밍 데스크탑</div>
                <div class="goal-item-amount">₩2,000,000</div>
              </div>
            </div>
            <div class="goal-track">
              <div class="goal-track-bar"><div class="goal-track-fill"></div></div>
              <span class="goal-track-pct">경차까지 13%</span>
            </div>
            <div class="goal-item target">
              <div class="goal-item-badge">→</div>
              <div class="goal-item-info">
                <div class="goal-item-label">다음 목표</div>
                <div class="goal-item-name">경차</div>
                <div class="goal-item-amount">₩15,000,000</div>
              </div>
            </div>
          </div>

          <div class="swipe-hint-keys">
            <span>← 패스</span>
            <span>↑ 저장</span>
            <span>→ 관심</span>
          </div>

          <div class="watchlist-preview" v-if="watchedCodes.length">
            <p class="eyebrow" style="margin-top: 18px;">관심종목 {{ watchedCodes.length }}개</p>
            <div class="watched-chips">
              <span v-for="code in watchedCodes" :key="code" class="watched-chip">{{ code }}</span>
            </div>
          </div>
        </div>

        <SwipeCard :card="currentCard" @like="onLike" @pass="onPass" @save="onSave" />
      </div>
    </section>

    <div class="swipe-toast" :class="{ show: toastVisible }" role="status" aria-live="polite">
      {{ toastMsg }}
    </div>
  </div>
</template>

<style scoped>
.tab-selector {
  align-self: center;
}

.watchlist-preview {
  margin-top: 6px;
}

.watched-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.watched-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(15, 159, 110, 0.1);
  border: 1px solid rgba(15, 159, 110, 0.3);
  color: var(--positive);
  font-size: 12px;
  font-weight: 900;
}
</style>
