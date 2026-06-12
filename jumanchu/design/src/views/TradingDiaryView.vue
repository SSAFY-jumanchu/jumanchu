<script setup>
import { ref, computed } from 'vue'

// ── 더미 데이터 ──────────────────────────────────────────────
const entries = ref([
  { id: 1,  date: '2026-06-05', stock: '삼성전자', ticker: '005930', type: 'buy',  title: '오늘 매수 이유', body: 'HBM 수요 회복 소식에 반도체 섹터 전반 매수 진입. 목표가 35만원.' },
  { id: 2,  date: '2026-06-05', stock: 'NVIDIA',   ticker: 'NVDA',    type: 'hold', title: 'NVDA 계속 보유', body: '실적 발표 앞두고 홀딩. 어닝 서프라이즈 기대감 있음.' },
  { id: 3,  date: '2026-06-04', stock: 'SK하이닉스', ticker: '000660', type: 'sell', title: '단기 수익 실현', body: '목표가 도달해 5주 전량 매도. 수익 +87,500원.' },
  { id: 4,  date: '2026-06-02', stock: '삼성전자', ticker: '005930', type: 'sell', title: '손절 결정', body: '예상과 다른 방향. 손절 -35,000원. 더 지켜볼 명분이 없다고 판단.' },
  { id: 5,  date: '2026-05-30', stock: 'NAVER',    ticker: '035420', type: 'buy',  title: 'NAVER 신규 진입', body: '광고 매출 회복 전망. 8주 매수.' },
  { id: 6,  date: '2026-05-22', stock: '삼성전자', ticker: '005930', type: 'sell', title: '분할 매도', body: '15주 분할 매도. 수익 +120,000원.' },
  { id: 7,  date: '2026-05-20', stock: '카카오',   ticker: '035720', type: 'sell', title: '손절', body: '카카오 실적 부진 확인 후 전량 손절. -62,000원.' },
  { id: 8,  date: '2026-05-15', stock: 'ALPHABET', ticker: 'GOOGL',  type: 'buy',  title: '구글 장기 보유 시작', body: 'AI 검색 광고 성장 기대. 1주 매수.' },
  { id: 9,  date: '2026-06-10', stock: 'APPLE',    ticker: 'AAPL',   type: 'hold', title: 'WWDC 전 홀딩 전략', body: 'AI 기능 대거 공개 예정. 발표 후 추가 매수 여부 판단 예정.' },
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

// ── 캘린더 날짜 선택 (하이라이트용만) ─────────────────────
const selectedDate = ref(null)

function selectDay(day) {
  if (!day) return
  const k = dateKey(day)
  selectedDate.value = selectedDate.value === k ? null : k
}

// ── 최근 작성 일지 목록 (날짜 내림차순) ───────────────────
const recentEntries = computed(() =>
  [...entries.value].sort((a, b) => b.date.localeCompare(a.date))
)

// ── 새 일지 작성 ───────────────────────────────────────────
const showForm = ref(false)
const form = ref({ stock: '', ticker: '', type: 'buy', title: '', body: '' })

function openForm() {
  if (!selectedDate.value) selectedDate.value = dateKey(today.getDate())
  form.value = { stock: '', ticker: '', type: 'buy', title: '', body: '' }
  showForm.value = true
}

function submitForm() {
  if (!form.value.stock || !form.value.title) return
  entries.value.push({
    id: Date.now(),
    date: selectedDate.value,
    ...form.value,
  })
  showForm.value = false
}

// ── 타입 스타일 헬퍼 ──────────────────────────────────────
const typeColor = { buy: '#315dff', sell: '#ef4444', hold: '#f59e0b' }
const typeLabel = { buy: '매수', sell: '매도', hold: '홀딩' }

function dotColors(day) {
  const es = entriesByDate.value[dateKey(day)] ?? []
  return [...new Set(es.map(e => typeColor[e.type]))]
}
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
      <div class="panel calendar-panel">
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
              'has-entry': day && entriesByDate[dateKey(day)],
              'is-selected': day && selectedDate === dateKey(day),
              'is-sunday': idx % 7 === 0,
              'is-saturday': idx % 7 === 6,
            }"
            @click="selectDay(day)"
          >
            <span v-if="day" class="cal-day-num">{{ day }}</span>
            <!-- 종목 타입 닷 -->
            <div v-if="day && dotColors(day).length" class="cal-dots">
              <span
                v-for="(color, ci) in dotColors(day).slice(0, 3)"
                :key="ci"
                class="cal-dot"
                :style="{ background: color }"
              ></span>
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

      <!-- ── 오른쪽 패널: 최근 작성 일지 목록 ── -->
      <div class="diary-right">
        <div class="panel recent-panel">
          <div class="recent-header">
            <span class="recent-title">최근 작성 일지</span>
            <span class="recent-count">{{ recentEntries.length }}건</span>
          </div>
          <div class="entry-list">
            <div v-for="e in recentEntries" :key="e.id" class="entry-card">
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
              <div class="entry-title">{{ e.title }}</div>
              <p class="entry-body">{{ e.body }}</p>
            </div>
          </div>
        </div>
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
          <div class="form-field span2">
            <label>제목</label>
            <input v-model="form.title" placeholder="오늘의 투자 한 줄 요약" class="form-input" />
          </div>
          <div class="form-field span2">
            <label>내용</label>
            <textarea v-model="form.body" placeholder="매수/매도 이유, 목표가, 느낀 점 등 자유롭게 기록하세요." class="form-textarea"></textarea>
          </div>
        </div>

        <div class="modal-actions">
          <button class="cancel-btn" @click="showForm = false">취소</button>
          <button class="submit-btn" :disabled="!form.stock || !form.title" @click="submitForm">저장</button>
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
  box-shadow: 0 4px 14px color-mix(in srgb, var(--accent) 30%, transparent);
  transition: transform 0.15s, box-shadow 0.15s;
}
.write-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 18px color-mix(in srgb, var(--accent) 38%, transparent); }

/* ── 레이아웃 ── */
.diary-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
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
  background: color-mix(in srgb, var(--overlay) 50%, transparent);
  font-size: 18px; font-weight: 900; color: var(--muted);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: background 0.15s, color 0.15s;
}
.cal-nav-btn:hover { background: color-mix(in srgb, var(--overlay) 80%, transparent); color: var(--ink); }

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
  aspect-ratio: 1;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  cursor: pointer;
  transition: background 0.15s;
  position: relative;
  padding: 4px 2px;
}
.cal-cell.is-empty { cursor: default; pointer-events: none; }
.cal-cell:not(.is-empty):hover { background: color-mix(in srgb, var(--overlay) 60%, transparent); }
.cal-cell.is-today .cal-day-num {
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  border-radius: 50%;
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
}
.cal-cell.is-selected { background: color-mix(in srgb, var(--accent) 10%, transparent); }
.cal-cell.has-entry { background: color-mix(in srgb, var(--overlay) 45%, transparent); }
.cal-cell.is-sunday .cal-day-num { color: var(--negative); }
.cal-cell.is-saturday .cal-day-num { color: var(--accent); }

.cal-day-num { font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1; }

.cal-dots { display: flex; gap: 2px; justify-content: center; }
.cal-dot { width: 5px; height: 5px; border-radius: 50%; }

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
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  padding: 2px 8px; border-radius: 999px;
}

.entry-list { display: flex; flex-direction: column; gap: 0; }
.entry-card {
  padding: 14px 0;
  border-bottom: 1px solid var(--faint);
  display: flex; flex-direction: column; gap: 6px;
}
.entry-card:last-child { border-bottom: none; }

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
.entry-title { font-size: 15px; font-weight: 900; color: var(--ink); }
.entry-body { font-size: 13px; color: var(--muted); line-height: 1.65; margin: 0; }

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
  background: color-mix(in srgb, var(--overlay) 50%, transparent);
  font-size: 13px; color: var(--muted); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.modal-close:hover { color: var(--ink); background: color-mix(in srgb, var(--overlay) 80%, transparent); }
.modal-date { font-size: 13px; font-weight: 700; color: var(--accent); }

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-field { display: flex; flex-direction: column; gap: 5px; }
.form-field.span2 { grid-column: 1 / -1; }
.form-field label { font-size: 12px; font-weight: 900; color: var(--muted); }
.form-input {
  height: 36px; padding: 0 10px;
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--overlay) 60%, transparent);
  font-size: 13px; color: var(--ink);
  outline: none;
}
.form-input:focus { border-color: var(--accent); }
.form-textarea {
  padding: 10px;
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  background: color-mix(in srgb, var(--overlay) 60%, transparent);
  font-size: 13px; color: var(--ink);
  min-height: 100px; resize: vertical;
  outline: none; font-family: inherit; line-height: 1.6;
}
.form-textarea:focus { border-color: var(--accent); }

.type-btns { display: flex; gap: 6px; }
.type-btn {
  height: 32px; padding: 0 14px; border-radius: 6px;
  border: 1px solid var(--glass-border);
  background: color-mix(in srgb, var(--overlay) 50%, transparent);
  font-size: 12px; font-weight: 900; color: var(--muted);
  cursor: pointer; transition: all 0.15s;
}
.type-btn:hover { background: color-mix(in srgb, var(--overlay) 80%, transparent); color: var(--ink); }

.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
.cancel-btn {
  height: 36px; padding: 0 16px; border-radius: 8px;
  border: 1px solid var(--glass-border);
  background: color-mix(in srgb, var(--overlay) 50%, transparent);
  font-size: 13px; font-weight: 900; color: var(--muted); cursor: pointer;
}
.cancel-btn:hover { background: color-mix(in srgb, var(--overlay) 80%, transparent); color: var(--ink); }
.submit-btn {
  height: 36px; padding: 0 20px; border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff; font-size: 13px; font-weight: 900; cursor: pointer;
  box-shadow: 0 4px 12px color-mix(in srgb, var(--accent) 28%, transparent);
  transition: opacity 0.15s;
}
.submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.submit-btn:not(:disabled):hover { opacity: 0.9; }
</style>
