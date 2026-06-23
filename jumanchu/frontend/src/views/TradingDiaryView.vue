<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchDiaries, createDiary, updateDiary } from '../api/diary'
import { fetchOrders } from '../api/portfolio'
import { errMsg } from '../api/client'

// 액션/사유 enum ↔ 한글 라벨
const ACTION_LABEL = { BUY: '매수', SELL: '매도', WATCH: '관심' }
const ACTION_ENUM = { 매수: 'BUY', 매도: 'SELL', 관심: 'WATCH' }
const REASON_LABEL = {
  GROWTH: '장기 성장성', EARNINGS: '실적 개선', UNDERVALUED: '저평가',
  THEME: '테마/모멘텀', NEWS: '뉴스 호재', TECHNICAL: '기술적 반등',
}
const REASON_ENUM = Object.fromEntries(Object.entries(REASON_LABEL).map(([k, v]) => [v, k]))
const DIARY_PALETTE = ['#0f9f6e', '#3b5bdb', '#76b900', '#f59e0b', '#06b6d4', '#ec4899']
function diaryColor(code) {
  let h = 0
  for (const ch of String(code)) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return DIARY_PALETTE[h % DIARY_PALETTE.length]
}

const loadError = ref('')

// ===== 나의 매매일기 (BE 연동, 목업 fallback 제거) =====
const entries = ref([])

function mapDiary(d) {
  return {
    id: d.id,
    order_id: d.order_id ?? null,
    name: d.stock_name,
    logo: (d.stock_name || '?').slice(0, 1),
    color: diaryColor(d.stock_code),
    date: (d.created_at || '').slice(0, 10).replace(/-/g, '.'),
    side: ACTION_LABEL[d.action_type] || d.action_type,
    reasons: d.reason_category ? [REASON_LABEL[d.reason_category] || d.reason_category] : [],
    target: d.target_price != null ? '목표 ' + Number(d.target_price).toLocaleString() + '원' : '—',
    stop: d.stop_loss_price != null ? '손절 ' + Number(d.stop_loss_price).toLocaleString() + '원' : '—',
    confidence: d.confidence,
    actual: '—',
    review: d.memo ? { verdict: '보류', learned: d.memo } : null,
    note: d.memo || '',
  }
}

// ===== 작성 대기: 일지가 아직 없는 최근 주문 (주문내역 기반) =====
const pendingTrades = ref([])
const selectedPendingId = ref(null)
const pendingTrade = computed(
  () => pendingTrades.value.find((p) => p.order_id === selectedPendingId.value) || null,
)
function mapOrder(o) {
  return {
    order_id: o.id,
    name: o.stock_name || o.stock_code,
    code: o.stock_code,
    logo: (o.stock_name || o.stock_code || '?').slice(0, 1),
    color: diaryColor(o.stock_code),
    side: ACTION_LABEL[o.side] || o.side,
    date: (o.created_at || o.executed_at || '').slice(5, 10).replace(/-/g, '.'),
  }
}
function selectPending(p) {
  selectedPendingId.value = p.order_id
  if (p.side === '매수' || p.side === '매도') newDiary.value.type = p.side
}

async function loadAll() {
  loadError.value = ''
  try {
    const [diaryRes, orderRes] = await Promise.all([
      fetchDiaries({ size: 30 }),
      fetchOrders({ size: 30 }),
    ])
    const diaryItems = diaryRes.items || []
    entries.value = diaryItems.map(mapDiary)
    // 이미 일기가 작성된 주문(order_id 연결)은 작성 대기에서 제외
    const journaled = new Set(diaryItems.map((d) => d.order_id).filter((x) => x != null))
    pendingTrades.value = (orderRes.items || [])
      .filter((o) => !journaled.has(o.id))
      .map(mapOrder)
    selectedPendingId.value = pendingTrades.value[0]?.order_id ?? null
  } catch (e) {
    loadError.value = errMsg(e)
  }
}
onMounted(loadAll)

// ===== 새 매매일기 작성 =====
const reasonOptions = ['장기 성장성', '실적 개선', '저평가', '테마/모멘텀', '뉴스 호재', '기술적 반등', '배당 매력', '분산 목적']
const targetOptions = ['+10%', '+20%', '+30%', '+50%']
const stopOptions = ['-5%', '-10%', '-15%', '-20%']
const typeOptions = [
  { key: '매수', color: '#e3344f' },
  { key: '매도', color: '#2b59d6' },
  { key: '관심', color: '#7d4ee8' },
]

const newDiary = ref({ type: '매수', reasons: ['장기 성장성', '테마/모멘텀'], confidence: 4, target: '+20%', stop: '-10%', note: '' })

function toggleReason(r) {
  const arr = newDiary.value.reasons
  const i = arr.indexOf(r)
  if (i === -1) arr.push(r)
  else arr.splice(i, 1)
}

const saving = ref(false)
async function saveDiary() {
  if (saving.value) return
  const pending = pendingTrade.value
  if (!pending) { loadError.value = '작성할 매매 내역을 위에서 선택해 주세요.'; return }
  saving.value = true
  loadError.value = ''
  // 첫 번째 매핑 가능한 사유만 단일 enum으로 전송(BE는 reason_category 단일)
  const reasonEnum = newDiary.value.reasons.map((r) => REASON_ENUM[r]).find(Boolean)
  try {
    await createDiary({
      stock_code: pending.code,
      order_id: pending.order_id, // 주문 연결 → 작성 대기에서 제외됨
      action_type: ACTION_ENUM[newDiary.value.type] || 'BUY',
      reason_category: reasonEnum || '',
      confidence: newDiary.value.confidence,
      memo: newDiary.value.note, // 목표/손절은 %라 절대가 변환 불가 → 미전송
    })
    await loadAll()
    newDiary.value = { type: '매수', reasons: [], confidence: 3, target: '+20%', stop: '-10%', note: '' }
  } catch (e) {
    loadError.value = errMsg(e)
  } finally {
    saving.value = false
  }
}

// ===== 일기 인라인 수정 (복기 박스 작성/수정) =====
const editingId = ref(null)
const editText = ref('')
function startEdit(e) {
  if (editingId.value === e.id) { editingId.value = null; return }
  editingId.value = e.id
  editText.value = e.review?.learned ?? ''
}
async function saveEdit(e) {
  const text = editText.value.trim()
  try {
    await updateDiary(e.id, { memo: text }) // 부분 수정(memo) — 복기 메모로 사용
    if (e.review) e.review.learned = text
    else if (text) e.review = { verdict: '보류', learned: text }
    e.note = text
    editingId.value = null
  } catch (err) {
    loadError.value = errMsg(err)
  }
}

// ===== 상태 헬퍼 =====
function statusLabel(e) { return e.review ? '복기 완료' : '복기 대기' }
const verdictColor = { 성공: '#0f9f6e', 보류: '#315dff', 실패: '#cf3d3d' }
</script>

<template>
  <div class="td-page">

    <!-- 헤더 -->
    <header class="td-header">
      <h1>매매일기</h1>
      <p class="td-sub">왜 샀는지 고르기만 하면 끝 — 나중에 결과로 복기하며 투자 습관을 만들어요.</p>
    </header>

    <!-- 로드 오류 -->
    <p v-if="loadError" class="td-error">{{ loadError }}</p>

    <!-- 작성 대기 알림 -->
    <div class="td-pending panel">
      <div class="td-pending-left">
        <span class="td-pending-ico">📝</span>
        <div>
          <strong>작성 대기 {{ pendingTrades.length }}건</strong>
          <span class="td-pending-desc">
            {{ pendingTrades.length ? '매매했는데 아직 일기를 안 쓴 거래예요. 선택해 작성하세요.' : '작성할 매매 내역이 없어요.' }}
          </span>
        </div>
      </div>
      <div v-if="pendingTrades.length" class="td-pending-chips">
        <button
          v-for="p in pendingTrades"
          :key="p.order_id"
          type="button"
          class="td-pending-chip"
          :class="{ on: selectedPendingId === p.order_id }"
          @click="selectPending(p)"
        >
          <span class="td-chip-logo" :style="{ background: p.color }">{{ p.logo }}</span>
          {{ p.name }} · {{ p.side }} · {{ p.date }}
        </button>
      </div>
    </div>

    <div class="td-grid">

      <!-- ===== 좌: 나의 매매일기 ===== -->
      <section class="panel td-list" aria-label="나의 매매일기">
        <div class="td-list-head">
          <h2>나의 매매일기</h2>
          <span class="td-list-count">총 {{ entries.length }}건</span>
        </div>

        <div class="td-entries">
          <div v-for="e in entries" :key="e.id" class="td-entry">
            <div class="td-entry-head">
              <span class="td-logo" :style="{ background: e.color }">{{ e.logo }}</span>
              <div class="td-entry-id">
                <div class="td-name-row">
                  <strong class="td-name">{{ e.name }}</strong>
                  <span class="td-side buy">{{ e.side }}</span>
                  <button type="button" class="td-edit-btn" @click="startEdit(e)">수정</button>
                </div>
                <span class="td-date">{{ e.date }}</span>
              </div>
              <span class="td-status" :class="e.review ? 'done' : 'pending'">{{ statusLabel(e) }}</span>
            </div>

            <div class="td-tags">
              <span v-for="r in e.reasons" :key="r" class="td-reason">{{ r }}</span>
              <span class="td-metric">목표 {{ e.target }}</span>
              <span class="td-metric">손절 {{ e.stop }}</span>
              <span class="td-stars">
                <span v-for="n in 5" :key="n" :class="n <= e.confidence ? 'on' : ''">★</span>
              </span>
            </div>

            <div v-if="e.review" class="td-review-box">
              <p class="td-review-line">
                🔍 실제 <strong :class="e.actual.startsWith('-') ? 'is-down' : 'is-up'">{{ e.actual }}</strong>
                · 판단 <strong :style="{ color: verdictColor[e.review.verdict] }">{{ e.review.verdict }}</strong>
              </p>
              <p class="td-review-learned">{{ e.review.learned }}</p>
            </div>

            <div v-if="editingId === e.id" class="td-edit-box">
              <textarea
                v-model="editText"
                class="td-textarea"
                placeholder="이번 매매에서 배운 점을 적어보세요. (더 정확한 추천이 가능해집니다!)"
              ></textarea>
              <div class="td-edit-actions">
                <button type="button" class="td-edit-save" @click="saveEdit(e)">저장</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ===== 우: 작성 ===== -->
      <div class="td-right">

        <!-- 새 매매일기 작성 -->
        <section class="panel td-form" aria-label="새 매매일기 작성">
          <p v-if="pendingTrade" class="td-form-title">🔍 새 매매일기 ({{ pendingTrade.name }} · {{ pendingTrade.date }}) — 다 고르기만!</p>
          <p v-else class="td-form-title">🔍 작성할 매매 내역을 위에서 선택하세요</p>

          <div class="td-field">
            <span class="td-field-label">매매 유형</span>
            <div class="td-chips">
              <button
                v-for="t in typeOptions"
                :key="t.key"
                type="button"
                class="td-chip-btn"
                :class="{ on: newDiary.type === t.key }"
                :style="newDiary.type === t.key ? { background: t.color, borderColor: t.color, color: '#fff' } : {}"
                @click="newDiary.type = t.key"
              >{{ t.key }}</button>
            </div>
          </div>

          <div class="td-field">
            <span class="td-field-label">이유 (복수 선택)</span>
            <div class="td-chips">
              <button
                v-for="r in reasonOptions"
                :key="r"
                type="button"
                class="td-chip-btn"
                :class="{ on: newDiary.reasons.includes(r) }"
                @click="toggleReason(r)"
              >{{ r }}</button>
            </div>
          </div>

          <div class="td-field">
            <span class="td-field-label">확신도</span>
            <div class="td-star-pick">
              <button
                v-for="n in 5"
                :key="n"
                type="button"
                class="td-star-btn"
                :class="{ on: n <= newDiary.confidence }"
                @click="newDiary.confidence = n"
              >★</button>
            </div>
          </div>

          <div class="td-field">
            <span class="td-field-label">목표 수익률</span>
            <div class="td-chips">
              <button
                v-for="o in targetOptions"
                :key="o"
                type="button"
                class="td-chip-btn"
                :class="{ on: newDiary.target === o }"
                @click="newDiary.target = o"
              >{{ o }}</button>
            </div>
          </div>

          <div class="td-field">
            <span class="td-field-label">손절 라인</span>
            <div class="td-chips">
              <button
                v-for="o in stopOptions"
                :key="o"
                type="button"
                class="td-chip-btn"
                :class="{ on: newDiary.stop === o }"
                @click="newDiary.stop = o"
              >{{ o }}</button>
            </div>
          </div>

          <div class="td-field">
            <textarea
              v-model="newDiary.note"
              class="td-textarea"
              placeholder="일지를 작성해 주세요. (더 정확한 추천이 가능해집니다!)"
            ></textarea>
          </div>

          <button class="td-save-btn" type="button" @click="saveDiary" :disabled="!pendingTrade || saving">매매일기 저장</button>
          <p class="td-form-hint">자유 서술·눈치 전부 없이, 선택만으로 1초 작성</p>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.td-page { display: flex; flex-direction: column; gap: 16px; max-width: 1200px; margin: 0 auto; }

/* 헤더 */
.td-header h1 { font-size: clamp(26px, 4vw, 34px); font-weight: 900; color: var(--ink); letter-spacing: -1px; margin: 0; }
.td-sub { margin: 6px 0 0; font-size: 13px; font-weight: 700; color: var(--muted); word-break: keep-all; }

/* 작성 대기 */
.td-pending {
  display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap;
  padding: 16px 20px; border: 1px solid rgba(245,158,11,0.3);
  background: linear-gradient(135deg, rgba(245,158,11,0.08), rgba(245,158,11,0.02));
}
.td-pending-left { display: flex; align-items: center; gap: 12px; }
.td-pending-ico { font-size: 22px; }
.td-pending-left strong { display: block; font-size: 14px; font-weight: 900; color: var(--ink); }
.td-pending-desc { font-size: 12px; font-weight: 700; color: var(--muted); }
.td-pending-chip {
  display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 999px;
  border: 1px solid var(--glass-border); background: var(--glass); color: var(--ink);
  font-size: 13px; font-weight: 900; cursor: pointer; transition: background 0.16s;
}
.td-pending-chip:hover { background: var(--surface-hover); }
.td-pending-chip.on { border-color: var(--accent); background: rgba(var(--accent-rgb),0.12); color: var(--accent); }
.td-pending-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.td-chip-logo { width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 11px; font-weight: 900; }
.td-error {
  margin: 0; padding: 10px 14px; border-radius: var(--radius);
  border: 1px solid rgba(207,61,61,0.3); background: rgba(207,61,61,0.08);
  color: #cf3d3d; font-size: 13px; font-weight: 800;
}

/* 레이아웃 */
.td-grid { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 16px; align-items: start; }
.td-right { display: flex; flex-direction: column; gap: 16px; }

/* 나의 매매일기 */
.td-list { padding: 20px; }
.td-list-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 8px; }
.td-list-head h2 { font-size: 17px; font-weight: 900; color: var(--ink); margin: 0; }
.td-list-count { font-size: 12px; font-weight: 800; color: var(--muted); }
.td-entries { display: flex; flex-direction: column; }
.td-entry { padding: 16px 0; border-bottom: 1px solid var(--faint); }
.td-entry:last-child { border-bottom: 0; }

.td-entry-head { display: flex; align-items: center; gap: 10px; }
.td-logo { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 12px; font-weight: 900; flex-shrink: 0; }
.td-entry-id { flex: 1; min-width: 0; }
.td-name-row { display: flex; align-items: center; gap: 7px; }
.td-name { font-size: 15px; font-weight: 900; color: var(--ink); }
.td-side { padding: 1px 8px; border-radius: 6px; font-size: 11px; font-weight: 900; }
.td-side.buy { background: rgba(227,52,79,0.12); color: #e3344f; }
.td-date { font-size: 12px; font-weight: 700; color: var(--muted); }
.td-status { flex-shrink: 0; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 900; }
.td-status.pending { background: rgba(var(--accent-rgb),0.12); color: var(--accent); }
.td-status.done { background: rgba(15,159,110,0.12); color: #0f9f6e; }

.td-tags { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.td-reason { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; background: rgba(var(--accent-rgb),0.08); color: var(--accent); }
.td-metric { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; background: var(--glass-subtle); color: var(--muted); }
.td-stars { margin-left: auto; font-size: 13px; letter-spacing: 1px; color: var(--faint); }
.td-stars .on { color: #f5b301; }

.td-review-box { margin-top: 12px; padding: 12px 14px; border-radius: var(--radius); background: var(--glass-subtle); border: 1px solid var(--glass-border); }
.td-review-line { margin: 0 0 5px; font-size: 12px; font-weight: 800; color: var(--muted); }
.td-review-learned { margin: 0; font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1.5; word-break: keep-all; }

/* 작성 폼 */
.td-form { padding: 18px 20px; }
.td-form-title { font-size: 14px; font-weight: 900; color: var(--ink); margin: 0 0 14px; word-break: keep-all; }
.td-field { margin-bottom: 14px; }
.td-field-label { display: block; font-size: 12px; font-weight: 900; color: var(--muted); margin-bottom: 8px; }
.td-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.td-chip-btn {
  padding: 7px 13px; border-radius: 999px; border: 1px solid var(--glass-border);
  background: var(--surface-soft); color: var(--muted); font-size: 12px; font-weight: 900;
  cursor: pointer; transition: background 0.14s, color 0.14s, border-color 0.14s;
}
.td-chip-btn:hover { background: var(--surface-hover); color: var(--ink); }
.td-chip-btn.on { background: var(--accent); border-color: var(--accent); color: #fff; }

.td-star-pick { display: flex; gap: 4px; }
.td-star-btn { border: 0; background: none; font-size: 24px; color: var(--faint); cursor: pointer; padding: 0; line-height: 1; transition: color 0.14s, transform 0.12s; }
.td-star-btn.on { color: #f5b301; }
.td-star-btn:hover { transform: scale(1.12); }

.td-save-btn {
  width: 100%; height: 46px; margin-top: 6px; border: 0; border-radius: var(--radius);
  background: linear-gradient(135deg, var(--accent), var(--purple)); color: #fff;
  font-size: 14px; font-weight: 900; cursor: pointer;
  box-shadow: 0 6px 18px rgba(var(--accent-rgb),0.3); transition: opacity 0.16s, transform 0.16s;
}
.td-save-btn:hover { opacity: 0.92; transform: translateY(-1px); }
.td-save-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
.td-form-hint { margin: 10px 0 0; text-align: center; font-size: 11px; font-weight: 700; color: var(--faint); }

/* 일지 textarea (작성/수정 공통) */
.td-textarea {
  width: 100%; min-height: 84px; padding: 12px 14px; border-radius: var(--radius);
  border: 1px solid var(--glass-border); background: var(--surface-soft); color: var(--ink);
  font-size: 13px; font-weight: 700; line-height: 1.6; outline: none; resize: vertical;
  box-sizing: border-box; font-family: inherit; transition: border-color 0.18s;
}
.td-textarea::placeholder { color: var(--faint); font-weight: 700; }
.td-textarea:focus { border-color: var(--accent); }

/* 일기 인라인 수정 */
.td-edit-btn {
  margin-left: 2px; padding: 0; border: 0; background: none;
  font-size: 11px; font-weight: 800; color: var(--muted); cursor: pointer; transition: color 0.14s;
}
.td-edit-btn:hover { color: var(--accent); }
.td-edit-box { margin-top: 12px; }
.td-edit-actions { display: flex; justify-content: flex-end; margin-top: 8px; }
.td-edit-save {
  padding: 7px 16px; border-radius: 999px; border: 0;
  background: var(--accent); color: #fff; font-size: 12px; font-weight: 900; cursor: pointer;
  transition: opacity 0.16s;
}
.td-edit-save:hover { opacity: 0.9; }

/* 색상 */
.is-up { color: #e3344f; }
.is-down { color: #2b59d6; }

@media (max-width: 1000px) {
  .td-grid { grid-template-columns: 1fr; }
}
</style>
