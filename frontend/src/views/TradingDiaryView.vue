<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { fetchDiaries, createDiary, updateDiary } from '../api/diary'
import { fetchOrders } from '../api/portfolio'
import { errMsg } from '../api/client'
import { useCopy } from '../composables/useCopy'

const { t } = useCopy()

// ===== 액션/사유 enum ↔ 한글 라벨 =====
const ACTION_LABEL = { BUY: '매수', SELL: '매도', WATCH: '관심' }
const REASON_LABEL = {
  // 매수 사유
  GROWTH: '장기 성장성', EARNINGS: '실적 개선', UNDERVALUED: '저평가',
  THEME: '테마/모멘텀', NEWS: '뉴스 호재', TECHNICAL: '기술적 반등',
  DIVIDEND: '배당 매력', DIVERSIFY: '분산 목적',
  // 매도 사유(결과)
  TARGET_HIT: '목표 달성', STOP_LOSS: '손절', PROFIT_TAKING: '차익 실현',
  DETERIORATED: '펀더멘털 악화', BETTER_OPP: '더 좋은 기회', REBALANCE: '리밸런싱',
}
const REASON_ENUM = Object.fromEntries(Object.entries(REASON_LABEL).map(([k, v]) => [v, k]))
// 매수/매도 이유 세트 분리 — 매도는 "결과" 사유 (BE는 reason_category 단일이라 단일 선택)
const BUY_REASONS = ['장기 성장성', '실적 개선', '저평가', '테마/모멘텀', '뉴스 호재', '기술적 반등', '배당 매력', '분산 목적']
const SELL_REASONS = ['목표 달성', '손절', '차익 실현', '펀더멘털 악화', '더 좋은 기회', '리밸런싱']
const targetOptions = ['+10%', '+20%', '+30%', '+50%']
const stopOptions = ['-5%', '-10%', '-15%', '-20%']

const DIARY_PALETTE = ['#0f9f6e', '#3b5bdb', '#76b900', '#f59e0b', '#06b6d4', '#ec4899']
function diaryColor(code) {
  let h = 0
  for (const ch of String(code)) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return DIARY_PALETTE[h % DIARY_PALETTE.length]
}
const curUnit = (cur) => (cur === 'USD' ? '$' : '원')

// ===== %(목표 수익률/손절) ↔ 절대가 변환 (BE는 절대가 Decimal 저장) =====
// 일기엔 진입가가 없어 연결 주문(order)의 체결단가로 환산/역산한다.
function parsePct(s) { return Number(String(s).replace('%', '')) / 100 }
function pctToPrice(entry, pctStr, currency) {
  const raw = entry * (1 + parsePct(pctStr))
  return currency === 'USD' ? Math.round(raw * 100) / 100 : Math.round(raw)
}
function nearestOption(entry, price, options) {
  if (!entry || price == null) return options[0]
  const pct = (Number(price) / entry - 1) * 100
  let best = options[0], bd = Infinity
  for (const o of options) {
    const d = Math.abs(parsePct(o) * 100 - pct)
    if (d < bd) { bd = d; best = o }
  }
  return best
}

// ===== 상태 =====
const tab = ref('write')         // 'write'(작성하기) | 'done'(작성 완료)
const loadError = ref('')
const entries = ref([])          // 작성 완료 (최신순 — BE가 -created_at 정렬)
const pendingTrades = ref([])    // 작성 대기 (오래된 순)
const entryById = ref({})        // order_id -> { price, currency, side }

function mapDiary(d) {
  const ord = d.order_id != null ? entryById.value[d.order_id] : null
  const cur = ord?.currency || 'KRW'
  return {
    id: d.id,
    order_id: d.order_id ?? null,
    code: d.stock_code,
    name: d.stock_name,
    logo: (d.stock_name || '?').slice(0, 1),
    color: diaryColor(d.stock_code),
    date: (d.created_at || '').slice(0, 10).replace(/-/g, '.'),
    actionType: d.action_type,
    side: ACTION_LABEL[d.action_type] || d.action_type,
    reason: d.reason_category ? (REASON_LABEL[d.reason_category] || d.reason_category) : '',
    targetPrice: d.target_price != null ? Number(d.target_price) : null,
    stopPrice: d.stop_loss_price != null ? Number(d.stop_loss_price) : null,
    currency: cur,
    confidence: d.confidence,
    memo: d.memo || '',
  }
}
function fmtTarget(e) { return e.targetPrice != null ? Number(e.targetPrice).toLocaleString() + curUnit(e.currency) : '—' }
function fmtStop(e) { return e.stopPrice != null ? Number(e.stopPrice).toLocaleString() + curUnit(e.currency) : '—' }

function mapOrder(o) {
  return {
    order_id: o.id,
    name: o.stock_name || o.stock_code,
    code: o.stock_code,
    logo: (o.stock_name || o.stock_code || '?').slice(0, 1),
    color: diaryColor(o.stock_code),
    actionType: o.side,                       // 'BUY' | 'SELL'
    side: ACTION_LABEL[o.side] || o.side,
    fullDate: (o.created_at || o.executed_at || '').slice(0, 10).replace(/-/g, '.'),
    entry: Number(o.price),
    currency: o.currency || 'KRW',
    createdAt: o.created_at || o.executed_at || '',
  }
}

async function loadAll() {
  loadError.value = ''
  try {
    const [diaryRes, orderRes] = await Promise.all([
      fetchDiaries({ size: 50 }),
      fetchOrders({ size: 50 }),
    ])
    const orders = orderRes.items || []
    const map = {}
    for (const o of orders) map[o.id] = { price: Number(o.price), currency: o.currency || 'KRW', side: o.side }
    entryById.value = map

    const diaryItems = diaryRes.items || []
    entries.value = diaryItems.map(mapDiary)   // 최신순 유지
    // 이미 일기가 작성된 주문(order_id 연결)은 작성 대기에서 제외 + 오래된 순 정렬
    const journaled = new Set(diaryItems.map((d) => d.order_id).filter((x) => x != null))
    pendingTrades.value = orders
      .filter((o) => !journaled.has(o.id))
      .map(mapOrder)
      .sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt))
    selectedPendingId.value = pendingTrades.value[0]?.order_id ?? null
  } catch (e) {
    loadError.value = errMsg(e)
  }
}
onMounted(loadAll)

// ===== 작성하기: 새 일기 =====
const selectedPendingId = ref(null)
const pendingTrade = computed(
  () => pendingTrades.value.find((p) => p.order_id === selectedPendingId.value) || null,
)
const writeForm = ref({ reason: '', confidence: 3, target: '+20%', stop: '-10%', memo: '' })
// 대기 종목을 바꾸면 폼 초기화 (매매 유형은 주문에서 고정되므로 폼에 없음)
watch(selectedPendingId, () => {
  writeForm.value = { reason: '', confidence: 3, target: '+20%', stop: '-10%', memo: '' }
})
const writeIsSell = computed(() => pendingTrade.value?.actionType === 'SELL')
const writeReasonOptions = computed(() => (writeIsSell.value ? SELL_REASONS : BUY_REASONS))
function pickWriteReason(r) { writeForm.value.reason = writeForm.value.reason === r ? '' : r }

const saving = ref(false)
async function saveDiary() {
  if (saving.value) return
  const p = pendingTrade.value
  if (!p) { loadError.value = '작성할 매매 내역을 선택해 주세요.'; return }
  saving.value = true
  loadError.value = ''
  try {
    const payload = {
      stock_code: p.code,
      order_id: p.order_id,                   // 주문 연결 → 작성 대기에서 제외됨
      action_type: p.actionType,              // 주문에서 고정
      reason_category: REASON_ENUM[writeForm.value.reason] || '',
      confidence: writeForm.value.confidence,
      memo: writeForm.value.memo.trim(),      // 복기(선택)
    }
    // 목표/손절은 진입 시점 목표 → 매수에서만, 주문 체결단가로 절대가 환산
    if (!writeIsSell.value && p.entry) {
      payload.target_price = pctToPrice(p.entry, writeForm.value.target, p.currency)
      payload.stop_loss_price = pctToPrice(p.entry, writeForm.value.stop, p.currency)
    }
    await createDiary(payload)
    await loadAll()
  } catch (e) {
    loadError.value = errMsg(e)
  } finally {
    saving.value = false
  }
}

// ===== 작성 완료: 인라인 수정 =====
const editingId = ref(null)
const editForm = ref({ reason: '', confidence: 3, target: '+20%', stop: '-10%', memo: '' })
const editEntryKnown = ref(false)
function editReasonOptions(e) { return e.actionType === 'SELL' ? SELL_REASONS : BUY_REASONS }
function pickEditReason(r) { editForm.value.reason = editForm.value.reason === r ? '' : r }

function startEdit(e) {
  if (editingId.value === e.id) { editingId.value = null; return }
  reviewingId.value = null
  editingId.value = e.id
  const ord = e.order_id != null ? entryById.value[e.order_id] : null
  editEntryKnown.value = !!(ord && ord.price)
  editForm.value = {
    reason: e.reason || '',
    confidence: e.confidence,
    target: editEntryKnown.value ? nearestOption(ord.price, e.targetPrice, targetOptions) : '+20%',
    stop: editEntryKnown.value ? nearestOption(ord.price, e.stopPrice, stopOptions) : '-10%',
    memo: e.memo || '',
  }
}
async function saveEdit(e) {
  loadError.value = ''
  try {
    const payload = {
      reason_category: REASON_ENUM[editForm.value.reason] || '',
      confidence: editForm.value.confidence,
      memo: editForm.value.memo.trim(),
    }
    // 주문 단가를 아는 매수 일기만 목표/손절 갱신 (모르면 기존 절대가 보존)
    const ord = e.order_id != null ? entryById.value[e.order_id] : null
    if (e.actionType !== 'SELL' && ord && ord.price) {
      payload.target_price = pctToPrice(ord.price, editForm.value.target, e.currency)
      payload.stop_loss_price = pctToPrice(ord.price, editForm.value.stop, e.currency)
    }
    await updateDiary(e.id, payload)
    await loadAll()
    editingId.value = null
  } catch (err) {
    loadError.value = errMsg(err)
  }
}

// ===== 작성 완료: 복기 작성(미작성 시 빠른 경로, memo 저장) =====
const reviewingId = ref(null)
const reviewText = ref('')
function startReview(e) {
  editingId.value = null
  reviewingId.value = reviewingId.value === e.id ? null : e.id
  reviewText.value = e.memo || ''
}
async function saveReview(e) {
  loadError.value = ''
  try {
    await updateDiary(e.id, { memo: reviewText.value.trim() })
    await loadAll()
    reviewingId.value = null
  } catch (err) {
    loadError.value = errMsg(err)
  }
}
</script>

<template>
  <div class="td-page">

    <!-- 헤더 -->
    <header class="td-header">
      <h1>{{ t('td.title', '매매일기') }}</h1>
      <p class="td-sub">{{ t('td.sub', '왜 샀는지 고르기만 하면 끝 — 나중에 결과로 복기하며 투자 습관을 만들어요.') }}</p>
    </header>

    <!-- 로드 오류 -->
    <p v-if="loadError" class="td-error">{{ loadError }}</p>

    <!-- ===== 탭 토글 ===== -->
    <div class="td-tabs" role="tablist">
      <button type="button" role="tab" :class="{ on: tab === 'write' }" @click="tab = 'write'">
        작성하기 <span class="td-tab-badge">{{ pendingTrades.length }}</span>
      </button>
      <button type="button" role="tab" :class="{ on: tab === 'done' }" @click="tab = 'done'">
        작성 완료 <span class="td-tab-badge">{{ entries.length }}</span>
      </button>
    </div>

    <!-- ===== 작성하기 ===== -->
    <section v-if="tab === 'write'" class="td-write-grid">

      <!-- 작성 대기 목록 (오래된 순) -->
      <div class="panel td-pending-list">
        <div class="td-list-head">
          <h2>작성할 매매</h2>
          <span class="td-list-count">{{ pendingTrades.length }}건</span>
        </div>
        <p v-if="!pendingTrades.length" class="td-empty">작성할 매매 내역이 없어요 👍</p>
        <div v-else class="td-pending-rows">
          <button
            v-for="p in pendingTrades"
            :key="p.order_id"
            type="button"
            class="td-pending-row"
            :class="{ on: selectedPendingId === p.order_id }"
            @click="selectedPendingId = p.order_id"
          >
            <span class="td-chip-logo" :style="{ background: p.color }">{{ p.logo }}</span>
            <span class="td-pending-row-info">
              <strong>{{ p.name }}</strong>
              <span>{{ p.fullDate }}</span>
            </span>
            <span class="td-side" :class="p.actionType === 'SELL' ? 'sell' : 'buy'">{{ p.side }}</span>
          </button>
        </div>
      </div>

      <!-- 작성 폼 -->
      <section v-if="pendingTrade" class="panel td-form" aria-label="새 매매일기 작성">
        <!-- 매매 유형은 주문에서 고정 → 제목 옆 배지로만 표시 -->
        <div class="td-form-title">
          <span>🔍 새 매매일기 ({{ pendingTrade.name }} · {{ pendingTrade.fullDate }})</span>
          <span class="td-type-fixed" :class="pendingTrade.actionType === 'SELL' ? 'sell' : 'buy'">{{ pendingTrade.side }}</span>
        </div>

        <!-- 이유 (단일 선택 — BE reason_category 단일) -->
        <div class="td-field">
          <span class="td-field-label">이유</span>
          <div class="td-chips">
            <button
              v-for="r in writeReasonOptions"
              :key="r"
              type="button"
              class="td-chip-btn"
              :class="{ on: writeForm.reason === r }"
              @click="pickWriteReason(r)"
            >{{ r }}</button>
          </div>
        </div>

        <!-- 확신도 -->
        <div class="td-field">
          <span class="td-field-label">확신도</span>
          <div class="td-star-pick">
            <button
              v-for="n in 5"
              :key="n"
              type="button"
              class="td-star-btn"
              :class="{ on: n <= writeForm.confidence }"
              @click="writeForm.confidence = n"
            >★</button>
          </div>
        </div>

        <!-- 목표/손절은 진입 시점 목표 → 매도(결과) 기록 땐 숨김 -->
        <template v-if="!writeIsSell">
          <div class="td-field">
            <span class="td-field-label">목표 수익률</span>
            <div class="td-chips">
              <button
                v-for="o in targetOptions"
                :key="o"
                type="button"
                class="td-chip-btn"
                :class="{ on: writeForm.target === o }"
                @click="writeForm.target = o"
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
                :class="{ on: writeForm.stop === o }"
                @click="writeForm.stop = o"
              >{{ o }}</button>
            </div>
          </div>
        </template>

        <!-- 복기 (선택) -->
        <div class="td-field">
          <span class="td-field-label">복기 <span class="td-optional">(선택)</span></span>
          <textarea
            v-model="writeForm.memo"
            class="td-textarea"
            placeholder="이번 매매에서 배운 점이나 생각을 적어보세요. (나중에 작성해도 돼요)"
          ></textarea>
        </div>

        <button class="td-save-btn" type="button" @click="saveDiary" :disabled="saving">{{ t('td.save', '매매일기 저장') }}</button>
        <p class="td-form-hint">매매 유형은 고정, 나머지는 선택만으로 1초 작성</p>
      </section>

      <section v-else class="panel td-form td-form-empty">
        <p>{{ pendingTrades.length ? '왼쪽에서 작성할 매매를 선택하세요.' : '작성할 매매 내역이 없어요. 매매를 하면 여기에 나타나요.' }}</p>
      </section>
    </section>

    <!-- ===== 작성 완료 (최신순) ===== -->
    <section v-else class="panel td-list" aria-label="작성 완료한 매매일기">
      <div class="td-list-head">
        <h2>작성 완료</h2>
        <span class="td-list-count">{{ t('td.list.countPre', '총') }} {{ entries.length }}{{ t('td.list.countSuf', '건') }}</span>
      </div>

      <p v-if="!entries.length" class="td-empty">작성한 매매일기가 없어요.</p>

      <div class="td-entries">
        <div v-for="e in entries" :key="e.id" class="td-entry">
          <div class="td-entry-head">
            <span class="td-logo" :style="{ background: e.color }">{{ e.logo }}</span>
            <div class="td-entry-id">
              <div class="td-name-row">
                <strong class="td-name">{{ e.name }}</strong>
                <span class="td-side" :class="e.actionType === 'SELL' ? 'sell' : 'buy'">{{ e.side }}</span>
              </div>
              <span class="td-date">{{ e.date }}</span>
            </div>
            <span class="td-status" :class="e.memo ? 'done' : 'pending'">{{ e.memo ? t('td.status.done', '복기 완료') : t('td.status.pending', '복기 대기') }}</span>
            <button type="button" class="td-edit-btn" @click="startEdit(e)">{{ editingId === e.id ? '닫기' : '수정' }}</button>
          </div>

          <!-- 기본 보기 -->
          <template v-if="editingId !== e.id">
            <div class="td-tags">
              <span v-if="e.reason" class="td-reason">{{ e.reason }}</span>
              <span v-else class="td-reason td-reason-none">이유 미입력</span>
              <span class="td-metric">{{ t('td.tag.target', '목표') }} {{ fmtTarget(e) }}</span>
              <span class="td-metric">{{ t('td.tag.stop', '손절') }} {{ fmtStop(e) }}</span>
              <span class="td-stars">
                <span v-for="n in 5" :key="n" :class="n <= e.confidence ? 'on' : ''">★</span>
              </span>
            </div>

            <!-- 복기: 작성됨 → 표시 / 미작성 → 작성 버튼 -->
            <div v-if="e.memo && reviewingId !== e.id" class="td-review-box">
              <p class="td-review-learned">🔍 {{ e.memo }}</p>
            </div>
            <button
              v-else-if="reviewingId !== e.id"
              type="button"
              class="td-review-add-btn"
              @click="startReview(e)"
            >＋ 복기 작성</button>

            <!-- 복기 작성 textarea -->
            <div v-if="reviewingId === e.id" class="td-edit-box">
              <textarea
                v-model="reviewText"
                class="td-textarea"
                placeholder="이번 매매를 돌아보며 배운 점을 적어보세요."
              ></textarea>
              <div class="td-edit-actions">
                <button type="button" class="td-edit-cancel" @click="reviewingId = null">취소</button>
                <button type="button" class="td-edit-save" @click="saveReview(e)">저장</button>
              </div>
            </div>
          </template>

          <!-- 수정 모드 — 선택지 재노출 -->
          <div v-else class="td-edit-form">
            <div class="td-field">
              <span class="td-field-label">이유</span>
              <div class="td-chips">
                <button
                  v-for="r in editReasonOptions(e)"
                  :key="r"
                  type="button"
                  class="td-chip-btn"
                  :class="{ on: editForm.reason === r }"
                  @click="pickEditReason(r)"
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
                  :class="{ on: n <= editForm.confidence }"
                  @click="editForm.confidence = n"
                >★</button>
              </div>
            </div>

            <template v-if="e.actionType !== 'SELL'">
              <template v-if="editEntryKnown">
                <div class="td-field">
                  <span class="td-field-label">목표 수익률</span>
                  <div class="td-chips">
                    <button
                      v-for="o in targetOptions"
                      :key="o"
                      type="button"
                      class="td-chip-btn"
                      :class="{ on: editForm.target === o }"
                      @click="editForm.target = o"
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
                      :class="{ on: editForm.stop === o }"
                      @click="editForm.stop = o"
                    >{{ o }}</button>
                  </div>
                </div>
              </template>
              <p v-else class="td-edit-note">
                목표/손절가는 연결된 주문 정보가 없어 수정할 수 없어요. (기존 값 유지 · 목표 {{ fmtTarget(e) }} · 손절 {{ fmtStop(e) }})
              </p>
            </template>

            <div class="td-field">
              <span class="td-field-label">복기 <span class="td-optional">(선택)</span></span>
              <textarea
                v-model="editForm.memo"
                class="td-textarea"
                placeholder="복기 내용을 적어보세요."
              ></textarea>
            </div>

            <div class="td-edit-actions">
              <button type="button" class="td-edit-cancel" @click="editingId = null">취소</button>
              <button type="button" class="td-edit-save" @click="saveEdit(e)">저장</button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.td-page { display: flex; flex-direction: column; gap: 16px; max-width: 1200px; margin: 0 auto; }

/* 헤더 */
.td-header h1 { font-size: clamp(26px, 4vw, 34px); font-weight: 900; color: var(--ink); letter-spacing: -1px; margin: 0; }
.td-sub { margin: 6px 0 0; font-size: 13px; font-weight: 700; color: var(--muted); word-break: keep-all; }

/* 오류 */
.td-error {
  margin: 0; padding: 10px 14px; border-radius: var(--radius);
  border: 1px solid rgba(207,61,61,0.3); background: rgba(207,61,61,0.08);
  color: #cf3d3d; font-size: 13px; font-weight: 800;
}

/* 탭 토글 */
.td-tabs {
  display: inline-flex; gap: 4px; padding: 4px; border-radius: 999px;
  background: var(--glass-subtle); border: 1px solid var(--glass-border); align-self: flex-start;
}
.td-tabs button {
  display: inline-flex; align-items: center; gap: 7px; min-height: 34px; padding: 0 18px;
  border: 0; border-radius: 999px; background: transparent; color: var(--muted);
  font-size: 13px; font-weight: 900; cursor: pointer; transition: background 0.16s, color 0.16s;
}
.td-tabs button.on { background: var(--accent); color: #fff; box-shadow: 0 4px 12px rgba(var(--accent-rgb),0.3); }
.td-tab-badge {
  min-width: 20px; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 900;
  background: rgba(0,0,0,0.12); color: inherit;
}
.td-tabs button.on .td-tab-badge { background: rgba(255,255,255,0.25); }

/* 레이아웃 */
.td-write-grid { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 16px; align-items: start; }

/* 공통 리스트 헤더 */
.td-list-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; }
.td-list-head h2 { font-size: 17px; font-weight: 900; color: var(--ink); margin: 0; }
.td-list-count { font-size: 12px; font-weight: 800; color: var(--muted); }
.td-empty { margin: 12px 0; font-size: 13px; font-weight: 700; color: var(--muted); }

/* 작성 대기 목록 */
.td-pending-list { padding: 18px; }
.td-pending-rows { display: flex; flex-direction: column; gap: 6px; max-height: 70vh; overflow-y: auto; }
.td-pending-row {
  display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 12px; text-align: left;
  border-radius: var(--radius); border: 1px solid var(--glass-border); background: var(--surface-soft);
  cursor: pointer; transition: background 0.14s, border-color 0.14s;
}
.td-pending-row:hover { background: var(--surface-hover); }
.td-pending-row.on { border-color: var(--accent); background: rgba(var(--accent-rgb),0.1); }
.td-pending-row-info { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.td-pending-row-info strong { font-size: 14px; font-weight: 900; color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.td-pending-row-info span { font-size: 11px; font-weight: 700; color: var(--muted); }
.td-chip-logo { width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 12px; font-weight: 900; }

/* 작성 완료 리스트 */
.td-list { padding: 20px; }
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
.td-side.sell { background: rgba(43,89,214,0.12); color: #2b59d6; }
.td-date { font-size: 12px; font-weight: 700; color: var(--muted); }
.td-status { flex-shrink: 0; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 900; }
.td-status.pending { background: rgba(var(--accent-rgb),0.12); color: var(--accent); }
.td-status.done { background: rgba(15,159,110,0.12); color: #0f9f6e; }

.td-tags { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.td-reason { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; background: rgba(var(--accent-rgb),0.08); color: var(--accent); }
.td-reason-none { background: var(--glass-subtle); color: var(--faint); }
.td-metric { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; background: var(--glass-subtle); color: var(--muted); }
.td-stars { margin-left: auto; font-size: 13px; letter-spacing: 1px; color: var(--faint); }
.td-stars .on { color: #f5b301; }

.td-review-box { margin-top: 12px; padding: 12px 14px; border-radius: var(--radius); background: var(--glass-subtle); border: 1px solid var(--glass-border); }
.td-review-learned { margin: 0; font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1.5; word-break: keep-all; }
.td-review-add-btn {
  margin-top: 12px; padding: 8px 14px; border-radius: 999px; border: 1px dashed var(--glass-border);
  background: transparent; color: var(--muted); font-size: 12px; font-weight: 900; cursor: pointer; transition: background 0.14s, color 0.14s, border-color 0.14s;
}
.td-review-add-btn:hover { background: rgba(var(--accent-rgb),0.08); color: var(--accent); border-color: var(--accent); }

/* 작성 폼 / 수정 폼 공통 */
.td-form { padding: 18px 20px; }
.td-form-empty { display: flex; align-items: center; justify-content: center; min-height: 160px; color: var(--muted); font-size: 13px; font-weight: 700; }
.td-form-title { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 14px; font-weight: 900; color: var(--ink); margin: 0 0 14px; word-break: keep-all; }
.td-field { margin-bottom: 14px; }
.td-field-label { display: block; font-size: 12px; font-weight: 900; color: var(--muted); margin-bottom: 8px; }
.td-optional { color: var(--faint); font-weight: 800; }
.td-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.td-chip-btn {
  padding: 7px 13px; border-radius: 999px; border: 1px solid var(--glass-border);
  background: var(--surface-soft); color: var(--muted); font-size: 12px; font-weight: 900;
  cursor: pointer; transition: background 0.14s, color 0.14s, border-color 0.14s;
}
.td-chip-btn:hover { background: var(--surface-hover); color: var(--ink); }
.td-chip-btn.on { background: var(--accent); border-color: var(--accent); color: #fff; }

/* 매매 유형(읽기 전용 배지 — 작성 폼 제목 옆) */
.td-type-fixed { padding: 6px 16px; border-radius: 999px; font-size: 13px; font-weight: 900; }
.td-type-fixed.buy { background: rgba(227,52,79,0.14); color: #e3344f; }
.td-type-fixed.sell { background: rgba(43,89,214,0.14); color: #2b59d6; }

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

/* textarea (작성/수정/복기 공통) */
.td-textarea {
  width: 100%; min-height: 84px; padding: 12px 14px; border-radius: var(--radius);
  border: 1px solid var(--glass-border); background: var(--surface-soft); color: var(--ink);
  font-size: 13px; font-weight: 700; line-height: 1.6; outline: none; resize: vertical;
  box-sizing: border-box; font-family: inherit; transition: border-color 0.18s;
}
.td-textarea::placeholder { color: var(--faint); font-weight: 700; }
.td-textarea:focus { border-color: var(--accent); }

/* 인라인 수정 */
.td-edit-btn {
  margin-left: 2px; padding: 0; border: 0; background: none;
  font-size: 11px; font-weight: 800; color: var(--muted); cursor: pointer; transition: color 0.14s; flex-shrink: 0;
}
.td-edit-btn:hover { color: var(--accent); }
.td-edit-box { margin-top: 12px; }
.td-edit-form { margin-top: 14px; padding-top: 14px; border-top: 1px dashed var(--glass-border); }
.td-edit-note { margin: 0 0 4px; font-size: 12px; font-weight: 700; color: var(--faint); line-height: 1.5; word-break: keep-all; }
.td-edit-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.td-edit-save {
  padding: 7px 16px; border-radius: 999px; border: 0;
  background: var(--accent); color: #fff; font-size: 12px; font-weight: 900; cursor: pointer; transition: opacity 0.16s;
}
.td-edit-save:hover { opacity: 0.9; }
.td-edit-cancel {
  padding: 7px 16px; border-radius: 999px; border: 1px solid var(--glass-border);
  background: transparent; color: var(--muted); font-size: 12px; font-weight: 900; cursor: pointer; transition: background 0.16s;
}
.td-edit-cancel:hover { background: var(--surface-hover); }

@media (max-width: 1000px) {
  .td-write-grid { grid-template-columns: 1fr; }
}
</style>
