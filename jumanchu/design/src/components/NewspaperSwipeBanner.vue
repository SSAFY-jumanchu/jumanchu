<script setup>
import { ref, computed } from 'vue'

// 추천 종목 목업 — 카드 내용은 원본 와이어프레임과 동일한 구성
// (시장·섹터 배지 / 추천점수 / 종목명·코드 / 현재가·등락률 / 좋아요 수)
const stocks = [
  { name: 'SK하이닉스', code: '000660', market: 'KOSPI', sector: '전기·전자', score: 94, price: '189,300원', rate: '+2.1%', up: true, likes: 1284 },
  { name: '삼성전자', code: '005930', market: 'KOSPI', sector: '전기·전자', score: 88, price: '317,000원', rate: '+0.8%', up: true, likes: 2107 },
  { name: 'NAVER', code: '035420', market: 'KOSPI', sector: '서비스업', score: 81, price: '184,000원', rate: '-0.6%', up: false, likes: 864 },
  { name: 'NVIDIA', code: 'NVDA', market: 'NASDAQ', sector: '반도체', score: 92, price: '$171.20', rate: '+1.4%', up: true, likes: 3521 },
  { name: '카카오뱅크', code: '323410', market: 'KOSPI', sector: '금융업', score: 76, price: '28,450원', rate: '+0.3%', up: true, likes: 542 },
]

const index = ref(0)
const x = ref(0)              // 카드 가로 이동량(px)
const animating = ref(false)
const leaving = ref(false)    // 화면 밖으로 슬라이드 중
const stamped = ref(false)    // ♡ 클릭 시 "관심" 스탬프
const dragging = ref(false)

const current = computed(() => stocks[index.value % stocks.length])
const next = computed(() => stocks[(index.value + 1) % stocks.length])

let startX = 0

function onPointerDown(e) {
  if (animating.value) return
  dragging.value = true
  startX = e.clientX
  e.currentTarget.setPointerCapture(e.pointerId)
}

function onPointerMove(e) {
  if (!dragging.value || animating.value) return
  x.value = e.clientX - startX
}

function onPointerUp() {
  if (!dragging.value) return
  dragging.value = false
  if (Math.abs(x.value) > 110) slideOut(Math.sign(x.value))
  else springBack()
}

function springBack() {
  animating.value = true
  x.value = 0
  setTimeout(() => { animating.value = false }, 320)
}

// 카드 한 장이 옆으로 빠져나가고 다음 카드가 올라온다
function slideOut(dir) {
  if (animating.value) return
  animating.value = true
  leaving.value = true
  x.value = dir * 560
  setTimeout(() => {
    index.value = (index.value + 1) % stocks.length
    x.value = 0
    stamped.value = false
    leaving.value = false
    requestAnimationFrame(() => { animating.value = false })
  }, 380)
}

function pass() { slideOut(-1) }
function like() {
  if (animating.value || stamped.value) return
  stamped.value = true
  setTimeout(() => slideOut(1), 600)
}

const rotate = computed(() => x.value * 0.04)
const leaveOpacity = computed(() => (leaving.value ? 0 : 1 - Math.min(0.35, Math.abs(x.value) / 600)))
</script>

<template>
  <div class="swipe-card-area">
    <div class="card-stack">
      <!-- 뒷장: 다음 카드 -->
      <article class="news-card is-under" aria-hidden="true">
        <div class="nc-masthead">
          <span class="nc-paper">주만추 일보</span>
        </div>
        <div class="nc-body">
          <h3 class="nc-name">{{ next.name }}</h3>
          <div class="nc-code">{{ next.code }}</div>
        </div>
      </article>

      <!-- 앞장: 현재 카드 -->
      <article
        class="news-card is-top"
        :class="{ 'is-animating': animating, 'is-dragging': dragging }"
        :style="{ transform: `translateX(${x}px) rotate(${rotate}deg)`, opacity: leaveOpacity }"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
      >
        <!-- 신문 제호 라인 -->
        <div class="nc-masthead">
          <span class="nc-edition">오늘의 추천</span>
          <span class="nc-paper">주만추 일보</span>
          <span class="nc-edition">제 {{ 1025 + (index % stocks.length) }}호</span>
        </div>

        <div class="nc-top">
          <span class="nc-badge">{{ current.market }} · {{ current.sector }}</span>
          <div class="nc-score">
            {{ current.score }}
            <span>점</span>
          </div>
        </div>

        <div class="nc-body">
          <h3 class="nc-name">{{ current.name }}</h3>
          <div class="nc-code">{{ current.code }}</div>

          <div class="nc-prices">
            <div class="nc-price-box">
              <span>현재가</span>
              <strong>{{ current.price }}</strong>
            </div>
            <div class="nc-price-box">
              <span>등락률</span>
              <strong :class="current.up ? 'is-up' : 'is-down'">{{ current.rate }}</strong>
            </div>
          </div>
        </div>

        <!-- 관심 스탬프 -->
        <div class="nc-stamp" :class="{ 'is-on': stamped }">관심<br>등록</div>
      </article>
    </div>

    <!-- 소셜 증거 -->
    <div class="swipe-social">
      <span class="social-dot"></span>
      <span>{{ current.likes.toLocaleString('ko-KR') }}명의 사용자가 좋아요!</span>
    </div>

    <!-- 스와이프 액션 버튼 -->
    <div class="swipe-action-row">
      <button class="swipe-btn pass-btn" aria-label="패스" @click="pass">✕</button>
      <button class="swipe-btn heart-btn" aria-label="관심 추가" @click="like">♡</button>
      <button class="swipe-btn like-btn" aria-label="다음" @click="slideOut(1)">→</button>
    </div>
  </div>
</template>

<style scoped>
.swipe-card-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.card-stack {
  position: relative;
  width: 100%;
  min-height: 280px;
}

/* ===== 신문지 질감 카드 ===== */
.news-card {
  position: absolute;
  inset: 0;
  border-radius: 10px;
  padding: 18px 22px 22px;
  display: flex;
  flex-direction: column;
  background: var(--paper-bg);
  border: 1px solid var(--paper-line);
  color: var(--paper-ink);
  /* 신문 용지 결 */
  background-image:
    repeating-linear-gradient(0deg, var(--paper-grain) 0px, transparent 1px, transparent 3px),
    radial-gradient(ellipse at 70% 0%, var(--paper-sheen) 0%, transparent 55%);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1), 0 10px 28px rgba(0, 0, 0, 0.08);
}

.news-card.is-under {
  transform: rotate(-1.2deg) translateY(7px) scale(0.985);
  opacity: 0.75;
}

.news-card.is-under .nc-body { opacity: 0.4; }

.news-card.is-top {
  cursor: grab;
  touch-action: pan-y;
  user-select: none;
  z-index: 2;
}

.news-card.is-top.is-dragging { cursor: grabbing; }

.news-card.is-top.is-animating {
  transition: transform 0.38s cubic-bezier(0.3, 0.7, 0.3, 1), opacity 0.38s ease;
}

/* ===== 제호 라인 (신문 머리) ===== */
.nc-masthead {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 8px;
  margin-bottom: 14px;
  border-bottom: 2px solid var(--paper-ink);
  box-shadow: 0 3px 0 -2px var(--paper-ink); /* 이중 괘선 */
}

.nc-paper {
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 0.5em;
  text-indent: 0.5em;
}

.nc-edition {
  font-size: 11px;
  font-weight: 700;
  opacity: 0.55;
  white-space: nowrap;
}

/* ===== 카드 내용 — 원본 와이어프레임과 동일 구성 ===== */
.nc-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.nc-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 11px;
  border: 1.5px solid var(--paper-ink);
  font-size: 12px;
  font-weight: 900;
}

.nc-score {
  text-align: right;
  font-size: 40px;
  font-weight: 900;
  line-height: 0.9;
  letter-spacing: -2px;
  color: var(--paper-accent);
  flex-shrink: 0;
}

.nc-score span {
  display: block;
  font-size: 12px;
  letter-spacing: 0;
  font-weight: 900;
  opacity: 0.7;
  margin-top: 4px;
}

.nc-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.nc-name {
  font-size: 32px;
  font-weight: 900;
  color: var(--paper-ink);
  letter-spacing: -1px;
  line-height: 1.1;
  margin: 0 0 4px;
}

.nc-code {
  font-size: 13px;
  font-weight: 900;
  opacity: 0.55;
  margin-bottom: 14px;
}

.nc-prices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.nc-price-box {
  padding: 10px 12px;
  border-top: 1.5px solid var(--paper-ink);
  border-bottom: 1px dotted var(--paper-line);
  background: color-mix(in srgb, var(--paper-ink) 3%, transparent);
}

.nc-price-box span {
  display: block;
  font-size: 11px;
  font-weight: 900;
  opacity: 0.55;
  margin-bottom: 4px;
}

.nc-price-box strong {
  display: block;
  font-size: 15px;
  font-weight: 900;
}

/* ===== 관심 스탬프 ===== */
.nc-stamp {
  position: absolute;
  top: 50%;
  left: 50%;
  padding: 10px 14px;
  border: 3px double var(--paper-accent);
  border-radius: 8px;
  color: var(--paper-accent);
  font-size: 20px;
  font-weight: 900;
  line-height: 1.2;
  text-align: center;
  letter-spacing: 0.15em;
  transform: translate(-50%, -50%) rotate(-14deg) scale(2.2);
  opacity: 0;
  pointer-events: none;
}

.nc-stamp.is-on {
  animation: stamp-in 0.35s cubic-bezier(0.25, 1.4, 0.5, 1) forwards;
}

@keyframes stamp-in {
  from { opacity: 0; transform: translate(-50%, -50%) rotate(-14deg) scale(2.2); }
  to { opacity: 0.9; transform: translate(-50%, -50%) rotate(-14deg) scale(1); }
}

/* ===== 소셜 증거 ===== */
.swipe-social {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.social-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--positive);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--positive) 20%, transparent);
  flex-shrink: 0;
}

/* ===== 스와이프 버튼 ===== */
.swipe-action-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.swipe-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 1px solid var(--glass-border);
  background: var(--card);
  font-size: 20px;
  font-weight: 900;
  color: var(--ink);
  box-shadow: var(--glass-shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.swipe-btn.pass-btn { color: var(--negative); }
.swipe-btn.like-btn { color: var(--positive); }

.swipe-btn.heart-btn {
  width: 68px;
  height: 68px;
  border: 0;
  background: var(--accent);
  color: #fff;
  font-size: 24px;
}

.swipe-btn:hover {
  transform: translateY(-3px) scale(1.06);
}
</style>
