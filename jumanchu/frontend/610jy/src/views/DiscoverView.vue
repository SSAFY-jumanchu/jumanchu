<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { stocks } from '../data/stocks.js'
import { useWatchlist } from '../composables/useWatchlist.js'
import { useFormat } from '../composables/useFormat.js'

// ── 관심 종목 스와이프 / 오늘의 궁합 추천 (와이어프레임 image30) ──
// 궁합점수·Stock DNA는 추천 도메인(정율) 산출물 — 현재 목업 (백엔드 미구현, 검토 메모 참고)
const { watchedCodes, toggleWatch } = useWatchlist()
const { formatMoney, formatRate, signedClass } = useFormat()

// 종목별 Stock DNA + 궁합점수 + 관심자 수 (목업)
const dnaMap = {
  '005930': { match: 91, watchers: 1820, axes: { 변동성: 54, 성장: 62, 가치: 70, 안정성: 82 } },
  '000660': { match: 87, watchers: 1204, axes: { 변동성: 69, 성장: 88, 가치: 45, 안정성: 58 } },
  '005380': { match: 78, watchers: 642, axes: { 변동성: 62, 성장: 55, 가치: 76, 안정성: 60 } },
  AAPL: { match: 84, watchers: 980, axes: { 변동성: 41, 성장: 72, 가치: 58, 안정성: 80 } },
  NVDA: { match: 94, watchers: 2410, axes: { 변동성: 76, 성장: 95, 가치: 38, 안정성: 52 } },
  GOOGL: { match: 81, watchers: 760, axes: { 변동성: 49, 성장: 79, 가치: 64, 안정성: 71 } },
}

const swipeIndex = ref(0)
const card = computed(() => stocks[swipeIndex.value % stocks.length])
const dna = computed(() => dnaMap[card.value.code] || { match: 80, watchers: 500, axes: { 변동성: 50, 성장: 50, 가치: 50, 안정성: 50 } })
const change = computed(() => card.value.price - card.value.open)
const changeRate = computed(() => (card.value.open ? (change.value / card.value.open) * 100 : 0))

const toast = ref('')
let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 1800)
}

function onPass() { showToast('다음 종목을 볼게요'); swipeIndex.value++ }
function onLike() {
  if (!watchedCodes.value.includes(card.value.code)) toggleWatch(card.value.code)
  showToast(`${card.value.name} 관심 종목에 담았어요`)
  swipeIndex.value++
}
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">Stock Match</p>
        <h1>관심 종목</h1>
      </div>
      <span class="profile-pill">관심 {{ watchedCodes.length }}개</span>
    </header>

    <section class="swipe-stage">
      <p class="swipe-eyebrow">오늘의 궁합 추천 💝</p>
      <p class="swipe-desc">당신의 투자 성향과 맞는 종목이에요. 넘기면서 관심 종목을 골라보세요.</p>
      <p class="swipe-count">추천 {{ (swipeIndex % stocks.length) + 1 }} / {{ stocks.length }}</p>

      <article class="match-card">
        <div class="mc-top">
          <span class="mc-tag">{{ card.market }} · {{ card.sector }}</span>
          <div class="mc-score">
            <strong>{{ dna.match }}</strong>
            <span>궁합 점수</span>
          </div>
        </div>

        <h2 class="mc-name">{{ card.name }}</h2>
        <p class="mc-code">{{ card.code }}</p>

        <div class="mc-price">
          <div><span>현재가</span><strong>{{ formatMoney(card.price, card.currency) }}</strong></div>
          <div><span>등락률</span><strong :class="signedClass(changeRate)">{{ formatRate(changeRate) }}</strong></div>
        </div>

        <div class="mc-dna">
          <p class="mc-dna-title">🧬 Stock DNA</p>
          <div class="mc-dna-grid">
            <div v-for="(val, key) in dna.axes" :key="key" class="dna-axis">
              <span class="dna-label">{{ key }}</span>
              <div class="dna-track"><div class="dna-fill" :style="{ width: `${val}%` }"></div></div>
              <span class="dna-val">{{ val }}</span>
            </div>
          </div>
        </div>

        <p class="mc-reason">{{ card.reason }}</p>
        <p class="mc-watchers">👀 {{ dna.watchers.toLocaleString('ko-KR') }}명이 이 종목에 관심 있어요</p>
      </article>

      <div class="swipe-actions">
        <button type="button" class="swipe-btn pass" @click="onPass" title="패스">✕</button>
        <button type="button" class="swipe-btn like" @click="onLike" title="관심 추가">♥</button>
        <RouterLink :to="`/stocks/${card.code}`" class="swipe-btn detail" title="상세">↗</RouterLink>
      </div>
      <div class="swipe-hint"><span>✕ 패스</span><span>♥ 관심 추가</span><span>↗ 상세</span></div>
    </section>

    <div class="swipe-toast" :class="{ show: !!toast }" role="status" aria-live="polite">{{ toast }}</div>
  </div>
</template>

<style scoped>
.is-up { color: var(--positive); }
.is-down { color: var(--negative); }
.is-flat { color: var(--muted); }

.swipe-stage { display: flex; flex-direction: column; align-items: center; text-align: center; padding-top: 6px; }
.swipe-eyebrow { margin: 0; font-size: 18px; font-weight: 900; color: var(--ink); }
.swipe-desc { margin: 6px 0 0; color: var(--muted); font-size: 13px; word-break: keep-all; max-width: 360px; }
.swipe-count { margin: 4px 0 16px; color: var(--faint); font-size: 12px; font-weight: 900; }

.match-card {
  width: 100%;
  max-width: 380px;
  border-radius: 24px;
  padding: 22px;
  color: #fff;
  background: linear-gradient(160deg, #7b5cff 0%, #b14bdb 55%, #ff5fa8 100%);
  box-shadow: 0 18px 48px rgba(123, 92, 255, 0.4);
}
.mc-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.mc-tag { padding: 5px 12px; border-radius: 999px; background: rgba(255, 255, 255, 0.22); font-size: 12px; font-weight: 900; }
.mc-score { display: flex; flex-direction: column; align-items: center; }
.mc-score strong { font-size: 34px; line-height: 1; }
.mc-score span { font-size: 11px; opacity: 0.85; font-weight: 900; }
.mc-name { margin: 16px 0 0; font-size: 28px; }
.mc-code { margin: 2px 0 0; opacity: 0.8; font-size: 13px; }

.mc-price { display: flex; gap: 28px; margin: 16px 0; }
.mc-price > div { display: flex; flex-direction: column; gap: 3px; text-align: left; }
.mc-price span { font-size: 11px; opacity: 0.8; font-weight: 900; }
.mc-price strong { font-size: 18px; }
.mc-price strong.is-up { color: #c9ffe6; }
.mc-price strong.is-down { color: #ffd6d6; }

.mc-dna { background: rgba(255, 255, 255, 0.92); border-radius: 16px; padding: 16px; color: var(--ink); }
.mc-dna-title { margin: 0 0 12px; font-size: 13px; font-weight: 900; color: var(--purple); }
.mc-dna-grid { display: grid; gap: 9px; }
.dna-axis { display: grid; grid-template-columns: 52px 1fr 28px; align-items: center; gap: 10px; }
.dna-label { color: var(--muted); font-size: 12px; font-weight: 900; }
.dna-track { height: 7px; border-radius: 999px; background: rgba(180, 200, 255, 0.4); overflow: hidden; }
.dna-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--purple)); }
.dna-val { color: var(--ink); font-size: 12px; font-weight: 900; text-align: right; }

.mc-reason { margin: 16px 0 0; font-size: 13px; line-height: 1.5; opacity: 0.95; word-break: keep-all; }
.mc-watchers { margin: 8px 0 0; font-size: 12px; font-weight: 900; opacity: 0.9; }

.swipe-actions { display: flex; gap: 18px; margin-top: 22px; }
.swipe-btn {
  width: 58px; height: 58px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: 0; font-size: 22px; font-weight: 900; cursor: pointer;
  box-shadow: var(--glass-shadow);
  transition: transform 0.14s ease;
}
.swipe-btn:hover { transform: translateY(-2px); }
.swipe-btn.pass { background: #fff; color: var(--muted); }
.swipe-btn.like { background: linear-gradient(135deg, #ff3d8b, #ff5fa8); color: #fff; width: 66px; height: 66px; font-size: 26px; }
.swipe-btn.detail { background: #fff; color: var(--accent); }
.swipe-hint { display: flex; gap: 18px; margin-top: 14px; color: var(--faint); font-size: 12px; font-weight: 900; }

.swipe-toast {
  position: fixed; left: 50%; bottom: 36px; transform: translateX(-50%) translateY(20px);
  padding: 12px 22px; border-radius: 999px;
  background: rgba(20, 24, 48, 0.92); color: #fff; font-size: 13px; font-weight: 900;
  opacity: 0; pointer-events: none; transition: opacity 0.2s ease, transform 0.2s ease; z-index: 60;
}
.swipe-toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
</style>
