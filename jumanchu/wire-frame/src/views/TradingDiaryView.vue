<script setup>
import { ref, computed } from 'vue'

// ── reason_category 선택지 ──────────────────────────────────
const reasonCategories = ['장기성장성', '실적개선', '저평가', '테마', '뉴스호재', '기술적반등', '배당', '분산']

// ── DiaryReview judgment 선택지 ─────────────────────────────
const judgmentOptions = ['탁월한 판단', '적절한 판단', '보통', '아쉬운 판단', '잘못된 판단']

// ── 더미 데이터 ──────────────────────────────────────────────
const entries = ref([
  { id: 1,  date: '2026-06-05', stock: '삼성전자', ticker: '005930', type: 'buy',  reason_category: '뉴스호재',   confidence: 4, target_price: 350000, stop_loss_price: 290000,
    review: { judgment: '적절한 판단', lesson: 'HBM 수요 회복 뉴스에 빠르게 진입한 건 좋았지만 목표가 설정을 더 구체적으로 해야 했다.' } },
  { id: 2,  date: '2026-06-05', stock: 'NVIDIA',   ticker: 'NVDA',    type: 'hold', reason_category: '장기성장성', confidence: 5, target_price: 250,    stop_loss_price: 180,
    review: null },
  { id: 3,  date: '2026-06-04', stock: 'SK하이닉스', ticker: '000660', type: 'sell', reason_category: '실적개선',   confidence: 3, target_price: null,   stop_loss_price: null,
    review: { judgment: '탁월한 판단', lesson: '목표가 도달 시 분할 매도 전략이 효과적이었다.' } },
  { id: 4,  date: '2026-06-02', stock: '삼성전자', ticker: '005930', type: 'sell', reason_category: '기술적반등',  confidence: 2, target_price: null,   stop_loss_price: 295000,
    review: { judgment: '보통', lesson: '손절 기준을 미리 설정했더라면 더 빠르게 대응할 수 있었다.' } },
  { id: 5,  date: '2026-05-30', stock: 'NAVER',    ticker: '035420', type: 'buy',  reason_category: '저평가',     confidence: 3, target_price: 290000, stop_loss_price: 230000,
    review: null },
  { id: 6,  date: '2026-05-22', stock: '삼성전자', ticker: '005930', type: 'sell', reason_category: '실적개선',   confidence: 4, target_price: null,   stop_loss_price: null,
    review: null },
  { id: 7,  date: '2026-05-20', stock: '카카오',   ticker: '035720', type: 'sell', reason_category: '기술적반등',  confidence: 2, target_price: null,   stop_loss_price: 55000,
    review: { judgment: '아쉬운 판단', lesson: '실적 부진 시그널을 더 일찍 포착했어야 했다.' } },
  { id: 8,  date: '2026-05-15', stock: 'ALPHABET', ticker: 'GOOGL',  type: 'buy',  reason_category: '장기성장성', confidence: 5, target_price: 220,    stop_loss_price: 155,
    review: null },
  { id: 9,  date: '2026-06-10', stock: 'APPLE',    ticker: 'AAPL',   type: 'hold', reason_category: '테마',       confidence: 4, target_price: 360,    stop_loss_price: 280,
    review: null },
])

// ── 캘린더 상태 ────────────────────────────────────────────
const today = new Date()
const viewYear  = ref(today.getFullYear())
const viewMonth = ref(today.getMonth()) // 0-indexed

function prevMonth() {
  if (viewMonth.value === 0) { viewYear.value--; viewMonth.value = 11 }
  else viewMonth.value--
}
function nextMonth() {
  if (viewMonth.value === 11) { viewYear.value++; viewMonth.value = 0 }
  else viewMonth.value++
}

const monthLabel = computed(() => `${viewYear.value}년 ${viewMonth.value + 1}월`)

// 해당 월의 캘린더 날짜 배열 (빈 셀 포함)
const calendarDays = computed(() => {
  const firstDay = new Date(viewYear.value, viewMonth.value, 1).getDay() // 0=일
  const daysInMonth = new Date(viewYear.value, viewMonth.value + 1, 0).getDate()
  const cells = []
  for (let i = 0; i < firstDay; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)
  return cells
})

// 날짜별 엔트리 맵
const entriesByDate = computed(() => {
  const map = {}
  for (const e of entries.value) {
    if (!map[e.date]) map[e.date] = []
    map[e.date].push(e)
  }
  return map
})

function dateKey(day) {
  const m = String(viewMonth.value + 1).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  return `${viewYear.value}-${m}-${d}`
}

function isToday(day) {
  return (
    viewYear.value === today.getFullYear() &&
    viewMonth.value === today.getMonth() &&
    day === today.getDate()
  )
}

function isFuture(day) {
  if (!day) return false
  const cellDate = new Date(viewYear.value, viewMonth.value, day)
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  return cellDate > todayStart
}

// ── 선택된 일지 (우측 상세 패널) ──────────────────────────
const selectedEntry = ref(null)

function selectEntry(e) {
  selectedEntry.value = selectedEntry.value?.id === e.id ? null : e
}

// ── 캘린더 날짜 선택 (오늘 이하만 선택 가능) ──────────────
const selectedDate = ref(null)

function selectDay(day) {
  if (!day || isFuture(day)) return
  const k = dateKey(day)
  selectedDate.value = selectedDate.value === k ? null : k
}

// ── 최근 작성 일지 목록 (날짜 내림차순) ───────────────────
const recentEntries = computed(() =>
  [...entries.value].sort((a, b) => b.date.localeCompare(a.date))
)

// ── 새 일지 작성 ───────────────────────────────────────────
const showForm = ref(false)
const form = ref({ stock: '', ticker: '', type: 'buy', reason_category: '', confidence: 0, target_price: '', stop_loss_price: '' })

function openForm() {
  if (!selectedDate.value) selectedDate.value = dateKey(today.getDate())
  form.value = { stock: '', ticker: '', type: 'buy', title: '', body: '' }
  showForm.value = true
}

function submitForm() {
  if (!form.value.stock || !form.value.reason_category) return
  entries.value.push({
    id: Date.now(),
    date: selectedDate.value,
    review: null,
    ...form.value,
    target_price: form.value.target_price ? Number(form.value.target_price) : null,
    stop_loss_price: form.value.stop_loss_price ? Number(form.value.stop_loss_price) : null,
  })
  showForm.value = false
}

// ── 타입 스타일 헬퍼 ──────────────────────────────────────
const typeColor = { buy: '#315dff', sell: '#ef4444', hold: '#f59e0b' }
const typeLabel = { buy: '매수', sell: '매도', hold: '홀딩' }

</script>

<template>
  <div class="diary-page">

    <!-- ── 페이지 헤더 ── -->
    <div class="page-header">
      <div>
        <p class="eyebrow">나의 투자 기록</p>
        <h1 class="page-title">매매 일기</h1>
      </div>
      <button class="write-btn" @click="openForm">+ 일지 작성</button>
    </div>

    <div class="diary-layout">

      <!-- ── 캘린더 ── -->
      <div class="panel calendar-panel" style="min-width:0">
        <!-- 월 네비게이션 -->
        <div class="cal-nav">
          <button class="cal-nav-btn" @click="prevMonth">‹</button>
          <span class="cal-month-label">{{ monthLabel }}</span>
          <button class="cal-nav-btn" @click="nextMonth">›</button>
        </div>

        <!-- 요일 헤더 -->
        <div class="cal-grid">
          <div v-for="w in ['일','월','화','수','목','금','토']" :key="w" class="cal-weekday">{{ w }}</div>

          <!-- 날짜 셀 -->
          <div
            v-for="(day, idx) in calendarDays"
            :key="idx"
            class="cal-cell"
            :class="{
              'is-empty': !day,
              'is-today': day && isToday(day),
              'is-future': day && isFuture(day),
              'has-entry': day && entriesByDate[dateKey(day)],
              'is-selected': day && selectedDate === dateKey(day),
              'is-sunday': idx % 7 === 0,
              'is-saturday': idx % 7 === 6,
            }"
            @click="selectDay(day)"
          >
            <span v-if="day" class="cal-day-num">{{ day }}</span>
            <!-- 종목 칩 -->
            <div v-if="day && entriesByDate[dateKey(day)]" class="cal-stocks">
              <span
                v-for="e in entriesByDate[dateKey(day)].slice(0, 2)"
                :key="e.id"
                class="cal-stock-chip"
                :style="{ background: typeColor[e.type] + '22', color: typeColor[e.type] }"
              >{{ e.stock }}</span>
              <span
                v-if="entriesByDate[dateKey(day)].length > 2"
                class="cal-stock-more"
              >+{{ entriesByDate[dateKey(day)].length - 2 }}</span>
            </div>
          </div>
        </div>

        <!-- 범례 -->
        <div class="cal-legend">
          <span v-for="(color, key) in typeColor" :key="key" class="legend-item">
            <span class="legend-dot" :style="{ background: color }"></span>
            {{ typeLabel[key] }}
          </span>
        </div>
      </div>

      <!-- ── 오른쪽 패널: 최근 작성 일지 목록 + 상세 ── -->
      <div class="diary-right">

        <!-- 일지 목록 -->
        <div class="panel recent-panel">
          <div class="recent-header">
            <span class="recent-title">최근 작성 일지</span>
            <span class="recent-count">{{ recentEntries.length }}건</span>
          </div>
          <div class="entry-list">
            <div
              v-for="e in recentEntries" :key="e.id"
              class="entry-card"
              :class="{ 'is-selected': selectedEntry?.id === e.id }"
              @click="selectEntry(e)"
            >
              <div class="entry-card-head">
                <div class="entry-stock-info">
                  <span class="entry-type-badge" :style="{ background: typeColor[e.type] + '22', color: typeColor[e.type], borderColor: typeColor[e.type] + '55' }">
                    {{ typeLabel[e.type] }}
                  </span>
                  <span class="entry-stock-name">{{ e.stock }}</span>
                  <span class="entry-ticker">{{ e.ticker }}</span>
                </div>
                <span class="entry-date">{{ e.date }}</span>
              </div>
              <div class="entry-bottom-row">
                <span class="entry-reason-chip">{{ e.reason_category }}</span>
                <span class="entry-confidence">{{ '★'.repeat(e.confidence) }}{{ '☆'.repeat(5 - e.confidence) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 선택된 일지 상세 패널 -->
        <Transition name="slide-down">
          <div v-if="selectedEntry" class="panel detail-panel">
            <!-- 종목 정보 -->
            <div class="detail-stock-card">
              <div class="dsc-left">
                <span class="dsc-type-badge" :style="{ background: typeColor[selectedEntry.type] + '22', color: typeColor[selectedEntry.type] }">
                  {{ typeLabel[selectedEntry.type] }}
                </span>
                <strong class="dsc-name">{{ selectedEntry.stock }}</strong>
                <span class="dsc-ticker">{{ selectedEntry.ticker }}</span>
              </div>
              <div class="dsc-date">{{ selectedEntry.date }}</div>
            </div>

            <!-- 별점 (confidence) -->
            <div class="detail-row">
              <span class="detail-label">확신도</span>
              <span class="detail-confidence">
                <span v-for="i in 5" :key="i" :class="i <= selectedEntry.confidence ? 'star-on' : 'star-off'">★</span>
              </span>
            </div>

            <!-- reason_category -->
            <div class="detail-row">
              <span class="detail-label">매매 이유</span>
              <span class="detail-reason-chip">{{ selectedEntry.reason_category }}</span>
            </div>

            <!-- 목표가 / 손절가 -->
            <div class="detail-prices" v-if="selectedEntry.target_price || selectedEntry.stop_loss_price">
              <div v-if="selectedEntry.target_price" class="detail-price-item is-target">
                <span>목표가</span>
                <strong>{{ typeof selectedEntry.target_price === 'number' && selectedEntry.target_price < 1000
                  ? '$' + selectedEntry.target_price
                  : '₩' + selectedEntry.target_price?.toLocaleString() }}</strong>
              </div>
              <div v-if="selectedEntry.stop_loss_price" class="detail-price-item is-stop">
                <span>손절가</span>
                <strong>{{ typeof selectedEntry.stop_loss_price === 'number' && selectedEntry.stop_loss_price < 1000
                  ? '$' + selectedEntry.stop_loss_price
                  : '₩' + selectedEntry.stop_loss_price?.toLocaleString() }}</strong>
              </div>
            </div>

            <!-- 복기 (DiaryReview) -->
            <div class="detail-review">
              <div class="detail-review-head">복기</div>
              <template v-if="selectedEntry.review">
                <div class="detail-row">
                  <span class="detail-label">판단</span>
                  <span class="detail-judgment">{{ selectedEntry.review.judgment }}</span>
                </div>
                <p class="detail-lesson">{{ selectedEntry.review.lesson }}</p>
              </template>
              <div v-else class="detail-review-empty">
                <p>아직 복기가 작성되지 않았습니다.</p>
                <button class="write-review-btn">복기 작성하기</button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- ── 일지 작성 모달 ── -->
    <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
      <div class="modal panel">
        <div class="modal-header">
          <h3>일지 작성</h3>
          <button class="modal-close" @click="showForm = false">✕</button>
        </div>
        <div class="modal-date">{{ selectedDate }}</div>

        <div class="form-grid">
          <div class="form-field">
            <label>종목명</label>
            <input v-model="form.stock" placeholder="예) 삼성전자" class="form-input" />
          </div>
          <div class="form-field">
            <label>티커</label>
            <input v-model="form.ticker" placeholder="예) 005930" class="form-input" />
          </div>
          <div class="form-field">
            <label>구분</label>
            <div class="type-btns">
              <button
                v-for="(label, key) in typeLabel"
                :key="key"
                class="type-btn"
                :class="{ active: form.type === key }"
                :style="form.type === key ? { background: typeColor[key] + '22', color: typeColor[key], borderColor: typeColor[key] } : {}"
                @click="form.type = key"
              >{{ label }}</button>
            </div>
          </div>
          <div class="form-field">
            <label>확신도</label>
            <div class="type-btns">
              <button
                v-for="n in 5" :key="n"
                class="type-btn"
                :style="form.confidence >= n ? { color: '#f59e0b', borderColor: '#f59e0b', background: 'rgba(245,158,11,0.1)' } : {}"
                @click="form.confidence = n"
              >{{ '★'.repeat(n) }}</button>
            </div>
          </div>
          <div class="form-field span2">
            <label>매매 이유</label>
            <div class="reason-chips">
              <button
                v-for="cat in reasonCategories" :key="cat"
                class="reason-chip-btn"
                :class="{ active: form.reason_category === cat }"
                @click="form.reason_category = cat"
              >{{ cat }}</button>
            </div>
          </div>
          <div class="form-field">
            <label>목표가</label>
            <input v-model="form.target_price" type="number" placeholder="예) 350000" class="form-input" />
          </div>
          <div class="form-field">
            <label>손절가</label>
            <input v-model="form.stop_loss_price" type="number" placeholder="예) 290000" class="form-input" />
          </div>
        </div>

        <div class="modal-actions">
          <button class="cancel-btn" @click="showForm = false">취소</button>
          <button class="submit-btn" :disabled="!form.stock || !form.reason_category" @click="submitForm">저장</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
.diary-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 64px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── 헤더 ── */
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.page-title {
  font-size: 28px;
  font-weight: 900;
  color: var(--ink);
  margin: 4px 0 0;
  letter-spacing: -0.5px;
}

.write-btn {
  height: 38px;
  padding: 0 18px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 4px 14px rgba(49,93,255,0.3);
  transition: transform 0.15s, box-shadow 0.15s;
}
.write-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(49,93,255,0.38); }

/* ── 레이아웃 ── */
.diary-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

/* ── 캘린더 ── */
.calendar-panel { padding: 20px 24px; }

.cal-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.cal-month-label { font-size: 16px; font-weight: 900; color: var(--ink); }
.cal-nav-btn {
  width: 32px; height: 32px; border-radius: 50%;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  font-size: 18px; font-weight: 900; color: var(--muted);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.15s, color 0.15s;
}
.cal-nav-btn:hover { background: rgba(255,255,255,0.8); color: var(--ink); }

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 3px;
}
.cal-weekday {
  text-align: center;
  font-size: 11px;
  font-weight: 900;
  color: var(--muted);
  padding: 6px 0;
}

.cal-cell {
  min-height: 72px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 3px;
  cursor: pointer;
  transition: background 0.15s;
  position: relative;
  padding: 6px 4px;
}
.cal-cell.is-empty { cursor: default; pointer-events: none; }
.cal-cell.is-future { cursor: not-allowed; opacity: 0.3; pointer-events: none; }
.cal-cell:not(.is-empty):hover { background: rgba(255,255,255,0.6); }
.cal-cell.is-today .cal-day-num {
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  border-radius: 50%;
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
}
.cal-cell.is-selected { background: rgba(49,93,255,0.1); }
.cal-cell.has-entry { background: rgba(255,255,255,0.45); }
.cal-cell.is-sunday .cal-day-num { color: var(--negative); }
.cal-cell.is-saturday .cal-day-num { color: var(--accent); }

.cal-day-num { font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1; align-self: center; }

.cal-stocks { display: flex; flex-direction: column; gap: 2px; width: 100%; margin-top: 2px; }
.cal-stock-chip {
  font-size: 9px;
  font-weight: 900;
  padding: 1px 4px;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.cal-stock-more { font-size: 9px; font-weight: 700; color: var(--muted); padding-left: 2px; }

.cal-legend {
  display: flex;
  gap: 14px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--faint);
  justify-content: center;
}
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 700; color: var(--muted); }
.legend-dot { width: 7px; height: 7px; border-radius: 50%; }

/* ── 오른쪽 패널 ── */
.diary-right { display: flex; flex-direction: column; }

.recent-panel { padding: 20px 24px; }
.recent-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.recent-title { font-size: 15px; font-weight: 900; color: var(--ink); }
.recent-count {
  font-size: 12px; font-weight: 900; color: var(--accent);
  background: rgba(49,93,255,0.1);
  padding: 2px 8px; border-radius: 999px;
}

.entry-list { display: flex; flex-direction: column; gap: 0; }
.entry-card {
  padding: 12px 8px;
  border-bottom: 1px solid var(--faint);
  display: flex; flex-direction: column; gap: 6px;
  cursor: pointer; border-radius: 8px;
  transition: background 0.15s;
}
.entry-card:last-child { border-bottom: none; }
.entry-card:hover { background: rgba(255,255,255,0.5); }
.entry-card.is-selected { background: rgba(49,93,255,0.07); border-color: rgba(49,93,255,0.2); }

.entry-card-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.entry-stock-info { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.entry-date { font-size: 11px; color: var(--muted); font-weight: 700; white-space: nowrap; flex-shrink: 0; }
.entry-type-badge {
  padding: 2px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 900;
  border: 1px solid transparent;
}
.entry-stock-name { font-size: 14px; font-weight: 900; color: var(--ink); }
.entry-ticker { font-size: 11px; color: var(--muted); }

.entry-bottom-row { display: flex; align-items: center; justify-content: space-between; }
.entry-reason-chip {
  font-size: 11px; font-weight: 900;
  padding: 2px 8px; border-radius: 999px;
  background: rgba(49,93,255,0.08); color: var(--accent);
}
.entry-confidence { font-size: 12px; color: #f59e0b; letter-spacing: 1px; }

/* ── 상세 패널 ── */
.detail-panel { padding: 20px; display: flex; flex-direction: column; gap: 14px; margin-top: 12px; }

.detail-stock-card {
  display: flex; align-items: center; justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--faint);
}
.dsc-left { display: flex; align-items: center; gap: 8px; }
.dsc-type-badge { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 900; }
.dsc-name { font-size: 16px; font-weight: 900; color: var(--ink); }
.dsc-ticker { font-size: 12px; color: var(--muted); }
.dsc-date { font-size: 12px; color: var(--muted); font-weight: 700; }

.detail-row { display: flex; align-items: center; gap: 12px; }
.detail-label { font-size: 12px; font-weight: 900; color: var(--muted); min-width: 60px; }
.detail-confidence { display: flex; gap: 2px; }
.star-on { color: #f59e0b; font-size: 18px; }
.star-off { color: var(--faint); font-size: 18px; }
.detail-reason-chip {
  font-size: 13px; font-weight: 900;
  padding: 4px 12px; border-radius: 999px;
  background: rgba(49,93,255,0.1); color: var(--accent);
}

.detail-prices { display: flex; gap: 10px; }
.detail-price-item {
  flex: 1; padding: 10px 14px; border-radius: 8px;
  display: flex; flex-direction: column; gap: 3px;
}
.detail-price-item span { font-size: 11px; font-weight: 700; color: var(--muted); }
.detail-price-item strong { font-size: 15px; font-weight: 900; }
.detail-price-item.is-target { background: rgba(0,102,204,0.07); }
.detail-price-item.is-target strong { color: var(--accent); }
.detail-price-item.is-stop { background: rgba(255,59,92,0.07); }
.detail-price-item.is-stop strong { color: var(--negative); }

.detail-review { border-top: 1px solid var(--faint); padding-top: 14px; display: flex; flex-direction: column; gap: 10px; }
.detail-review-head { font-size: 13px; font-weight: 900; color: var(--ink); }
.detail-judgment {
  font-size: 13px; font-weight: 900;
  padding: 3px 10px; border-radius: 6px;
  background: rgba(255,255,255,0.6); border: 1px solid var(--glass-border);
}
.detail-lesson { margin: 0; font-size: 13px; color: var(--muted); line-height: 1.6; }
.detail-review-empty { text-align: center; padding: 16px 0; }
.detail-review-empty p { font-size: 13px; color: var(--faint); margin: 0 0 10px; }
.write-review-btn {
  padding: 6px 16px; border-radius: 999px;
  border: 1px solid rgba(49,93,255,0.3);
  background: rgba(49,93,255,0.07); color: var(--accent);
  font-size: 12px; font-weight: 900; cursor: pointer;
}

/* ── reason_category 칩 ── */
.reason-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.reason-chip-btn {
  padding: 5px 12px; border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  font-size: 12px; font-weight: 900; color: var(--muted);
  cursor: pointer; transition: all 0.15s;
}
.reason-chip-btn:hover { background: rgba(255,255,255,0.8); color: var(--ink); }
.reason-chip-btn.active {
  background: rgba(49,93,255,0.1);
  border-color: rgba(49,93,255,0.35);
  color: var(--accent);
}

/* ── 모달 ── */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.35);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 200;
  padding: 24px;
}
.modal {
  width: 100%; max-width: 540px;
  padding: 28px 28px 24px;
  display: flex; flex-direction: column; gap: 16px;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
}
.modal-header h3 { font-size: 18px; font-weight: 900; color: var(--ink); margin: 0; }
.modal-close {
  width: 28px; height: 28px; border-radius: 50%;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  font-size: 13px; color: var(--muted); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { color: var(--ink); background: rgba(255,255,255,0.8); }
.modal-date { font-size: 13px; font-weight: 700; color: var(--accent); }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-field { display: flex; flex-direction: column; gap: 5px; }
.form-field.span2 { grid-column: 1 / -1; }
.form-field label { font-size: 12px; font-weight: 900; color: var(--muted); }
.form-input {
  height: 36px; padding: 0 10px;
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  background: rgba(255,255,255,0.6);
  font-size: 13px; color: var(--ink);
  outline: none;
}
.form-input:focus { border-color: var(--accent); }
.form-textarea {
  padding: 10px;
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  background: rgba(255,255,255,0.6);
  font-size: 13px; color: var(--ink);
  min-height: 100px; resize: vertical;
  outline: none; font-family: inherit; line-height: 1.6;
}
.form-textarea:focus { border-color: var(--accent); }

.type-btns { display: flex; gap: 6px; }
.type-btn {
  height: 32px; padding: 0 14px; border-radius: 6px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  font-size: 12px; font-weight: 900; color: var(--muted);
  cursor: pointer; transition: all 0.15s;
}
.type-btn:hover { background: rgba(255,255,255,0.8); color: var(--ink); }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
.cancel-btn {
  height: 36px; padding: 0 16px; border-radius: 8px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  font-size: 13px; font-weight: 900; color: var(--muted); cursor: pointer;
}
.cancel-btn:hover { background: rgba(255,255,255,0.8); color: var(--ink); }
.submit-btn {
  height: 36px; padding: 0 20px; border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff; font-size: 13px; font-weight: 900; cursor: pointer;
  box-shadow: 0 4px 12px rgba(49,93,255,0.28);
  transition: opacity 0.15s;
}
.submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.submit-btn:not(:disabled):hover { opacity: 0.9; }
</style>
