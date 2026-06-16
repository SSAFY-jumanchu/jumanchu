<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'

// ── 매매일기 (캘린더 조회) ──
// 작성은 매수/매도 직후 종목 상세(StockDetailView) → POST /api/v1/diaries (order_id 연결)
// 이 페이지는 GET /api/v1/diaries — 캘린더에서 날짜별 일지 제목 → 클릭 시 상세
const actionLabels = { BUY: '매수', SELL: '매도', WATCH: '관심' }

const diaries = [
  { id: 1, stock_code: '005930', stock_name: '삼성전자', currency: 'KRW', action_type: 'BUY', reason_category: '배당', confidence: 4, reason_text: '배당주 포트폴리오 편입. 전기전자 섹터 비중 확대.', target_price: 90000, stop_loss_price: 62000, date: '2026-06-02' },
  { id: 2, stock_code: '000660', stock_name: 'SK하이닉스', currency: 'KRW', action_type: 'SELL', reason_category: '실적개선', confidence: 3, reason_text: '단기 급등 후 비중 조절. 일부 차익 실현.', target_price: null, stop_loss_price: null, date: '2026-06-02' },
  { id: 3, stock_code: 'NVDA', stock_name: 'NVIDIA', currency: 'USD', action_type: 'BUY', reason_category: '장기성장성', confidence: 5, reason_text: 'AI 반도체 독점적 수요. 고변동 감수, 장기 보유 목표.', target_price: 1400, stop_loss_price: 820, date: '2026-06-03' },
  { id: 4, stock_code: '035420', stock_name: 'NAVER', currency: 'KRW', action_type: 'BUY', reason_category: '저평가', confidence: 4, reason_text: '광고 회복 + 커머스 성장 기대. 분할 매수.', target_price: 260000, stop_loss_price: 175000, date: '2026-06-16' },
  { id: 5, stock_code: 'AAPL', stock_name: 'Apple', currency: 'USD', action_type: 'BUY', reason_category: '분산', confidence: 3, reason_text: '미국장 코어 자산으로 소액 진입.', target_price: 230, stop_loss_price: 165, date: '2026-06-23' },
]

// 일자별 그룹
const byDate = computed(() => {
  const map = {}
  for (const d of diaries) (map[d.date] ||= []).push(d)
  return map
})

// 캘린더 상태
const year = ref(2026)
const month = ref(6) // 1~12
const weekdays = ['일', '월', '화', '수', '목', '금', '토']

const weeks = computed(() => {
  const first = new Date(year.value, month.value - 1, 1)
  const startDay = first.getDay()
  const daysInMonth = new Date(year.value, month.value, 0).getDate()
  const cells = []
  for (let i = 0; i < startDay; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) {
    const key = `${year.value}-${String(month.value).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    cells.push({ day: d, key, diaries: byDate.value[key] || [] })
  }
  while (cells.length % 7 !== 0) cells.push(null)
  const rows = []
  for (let i = 0; i < cells.length; i += 7) rows.push(cells.slice(i, i + 7))
  return rows
})

const monthCount = computed(() => diaries.filter((d) => d.date.startsWith(`${year.value}-${String(month.value).padStart(2, '0')}`)).length)

function prevMonth() {
  if (month.value === 1) { month.value = 12; year.value-- } else month.value--
}
function nextMonth() {
  if (month.value === 12) { month.value = 1; year.value++ } else month.value++
}

const selected = ref(null)
function selectDiary(d) { selected.value = d }

function won(d, n) {
  if (n == null) return '—'
  return d.currency === 'KRW' ? `₩${n.toLocaleString('ko-KR')}` : `$${n.toLocaleString('en-US')}`
}
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">Trade Diary</p>
        <h1>매매일기</h1>
      </div>
    </header>

    <p class="diary-hint">
      📔 일기는 <strong>매수·매도 직후 종목 상세 화면</strong>에서 작성합니다. 여기서는 날짜별로 조회해요.
      <RouterLink to="/stocks">주식 조회로 이동 →</RouterLink>
    </p>

    <div class="diary-layout">
      <!-- 캘린더 -->
      <section class="panel">
        <div class="cal-head">
          <button type="button" class="cal-nav" @click="prevMonth">←</button>
          <h2>{{ year }}년 {{ month }}월 <span class="cal-count">일기 {{ monthCount }}개</span></h2>
          <button type="button" class="cal-nav" @click="nextMonth">→</button>
        </div>

        <div class="cal-weekdays">
          <span v-for="(w, i) in weekdays" :key="w" :class="{ sun: i === 0, sat: i === 6 }">{{ w }}</span>
        </div>

        <div class="cal-grid">
          <template v-for="(week, wi) in weeks" :key="wi">
            <div
              v-for="(cell, di) in week"
              :key="di"
              class="cal-cell"
              :class="{ empty: !cell, today: cell && cell.diaries.length }"
            >
              <template v-if="cell">
                <span class="cal-day" :class="{ sun: di === 0, sat: di === 6 }">{{ cell.day }}</span>
                <button
                  v-for="d in cell.diaries"
                  :key="d.id"
                  type="button"
                  class="cal-entry"
                  :class="[d.action_type === 'BUY' ? 'buy' : 'sell', { active: selected && selected.id === d.id }]"
                  @click="selectDiary(d)"
                >{{ actionLabels[d.action_type] }} {{ d.stock_name }}</button>
              </template>
            </div>
          </template>
        </div>
      </section>

      <!-- 선택 일기 상세 -->
      <aside class="panel diary-detail">
        <template v-if="selected">
          <div class="dd-head">
            <span class="dd-action" :class="selected.action_type === 'BUY' ? 'buy' : 'sell'">{{ actionLabels[selected.action_type] }}</span>
            <h2>{{ selected.stock_name }}</h2>
            <p>{{ selected.stock_code }} · {{ selected.date.replaceAll('-', '.') }}</p>
          </div>
          <span class="dd-cat">{{ selected.reason_category }}</span>
          <p class="dd-reason">{{ selected.reason_text }}</p>
          <dl class="dd-list">
            <div><dt>확신도</dt><dd><span class="stars">{{ '★'.repeat(selected.confidence) }}{{ '☆'.repeat(5 - selected.confidence) }}</span></dd></div>
            <div><dt>목표가</dt><dd>{{ won(selected, selected.target_price) }}</dd></div>
            <div><dt>손절가</dt><dd>{{ won(selected, selected.stop_loss_price) }}</dd></div>
          </dl>
          <RouterLink :to="`/stocks/${selected.stock_code}`" class="dd-link">종목 상세 보기 →</RouterLink>
        </template>
        <div v-else class="dd-empty">
          캘린더에서 일기 제목을 클릭하면<br />상세 내용이 여기에 표시됩니다.
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.diary-hint {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  margin: 0 0 16px; padding: 12px 16px; border-radius: var(--radius);
  background: rgba(49, 93, 255, 0.06); border: 1px solid rgba(49, 93, 255, 0.18);
  color: var(--muted); font-size: 13px;
}
.diary-hint strong { color: var(--ink); }
.diary-hint a { color: var(--accent); font-weight: 900; }

.diary-layout { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }

/* 캘린더 */
.cal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.cal-head h2 { margin: 0; font-size: 18px; }
.cal-count { margin-left: 8px; color: var(--accent); font-size: 13px; font-weight: 900; }
.cal-nav { width: 36px; height: 36px; border-radius: 50%; border: 1px solid var(--glass-border); background: rgba(255, 255, 255, 0.5); color: var(--ink); font-size: 15px; font-weight: 900; }
.cal-nav:hover { background: rgba(255, 255, 255, 0.75); }

.cal-weekdays { display: grid; grid-template-columns: repeat(7, 1fr); margin-bottom: 6px; }
.cal-weekdays span { text-align: center; color: var(--muted); font-size: 12px; font-weight: 900; padding: 4px 0; }
.cal-weekdays .sun { color: var(--negative); }
.cal-weekdays .sat { color: var(--accent); }

.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.cal-cell {
  min-height: 88px; padding: 6px; border-radius: 10px;
  background: rgba(255, 255, 255, 0.4); border: 1px solid var(--glass-border);
  display: flex; flex-direction: column; gap: 4px;
}
.cal-cell.empty { background: transparent; border-color: transparent; }
.cal-cell.today { background: rgba(49, 93, 255, 0.05); border-color: rgba(49, 93, 255, 0.2); }
.cal-day { color: var(--muted); font-size: 12px; font-weight: 900; }
.cal-day.sun { color: var(--negative); }
.cal-day.sat { color: var(--accent); }
.cal-entry {
  text-align: left; padding: 4px 6px; border-radius: 6px; border: 0;
  font-size: 11px; font-weight: 900; cursor: pointer; line-height: 1.25;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.cal-entry.buy { background: rgba(49, 93, 255, 0.12); color: var(--accent); }
.cal-entry.sell { background: rgba(207, 61, 61, 0.12); color: var(--negative); }
.cal-entry.active { outline: 2px solid var(--accent); }

/* 상세 패널 */
.diary-detail { position: sticky; top: 80px; min-height: 220px; }
.dd-head { margin-bottom: 12px; }
.dd-action { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 900; margin-bottom: 8px; }
.dd-action.buy { background: rgba(49, 93, 255, 0.1); color: var(--accent); }
.dd-action.sell { background: rgba(207, 61, 61, 0.1); color: var(--negative); }
.dd-head h2 { margin: 0; font-size: 20px; }
.dd-head p { margin: 2px 0 0; color: var(--muted); font-size: 12px; }
.dd-cat { display: inline-block; padding: 3px 10px; border-radius: 999px; background: rgba(255, 255, 255, 0.6); border: 1px solid var(--glass-border); color: var(--muted); font-size: 12px; font-weight: 900; margin-bottom: 12px; }
.dd-reason { margin: 0 0 16px; color: var(--text); font-size: 14px; line-height: 1.6; word-break: keep-all; }
.dd-list { display: grid; gap: 0; margin: 0 0 16px; }
.dd-list > div { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--line); }
.dd-list > div:last-child { border-bottom: 0; }
.dd-list dt { color: var(--muted); font-size: 13px; }
.dd-list dd { margin: 0; color: var(--ink); font-size: 14px; font-weight: 900; }
.stars { color: var(--accent); letter-spacing: 1px; }
.dd-link { display: block; text-align: center; padding: 11px; border-radius: var(--radius); background: rgba(49, 93, 255, 0.08); color: var(--accent); font-size: 13px; font-weight: 900; }
.dd-empty { color: var(--faint); font-size: 13px; line-height: 1.6; text-align: center; padding: 40px 0; }

@media (max-width: 1080px) {
  .diary-layout { grid-template-columns: 1fr; }
  .diary-detail { position: static; }
}
@media (max-width: 640px) {
  .cal-cell { min-height: 64px; }
  .cal-entry { font-size: 10px; }
}
</style>
