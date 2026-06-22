<script setup>
import { ref } from 'vue'

// ===== 작성 대기 (와이어프레임: 미작성 매매가 있다고 가정) =====
const pendingTrade = { name: '로보스타', logo: '로', color: '#0f9f6e', side: '매수', date: '06.09' }

// ===== 나의 매매일기 (종목 전체) =====
const entries = ref([
  {
    id: 1, name: '로보스타', logo: '로', color: '#0f9f6e', date: '2026.06.09', side: '매수',
    reasons: ['장기 성장성', '테마/모멘텀'], target: '+20%', stop: '-10%', confidence: 4,
    actual: '+5.2%', review: null, note: '',
  },
  {
    id: 2, name: '삼성전자', logo: '삼', color: '#3b5bdb', date: '2026.05.28', side: '매수',
    reasons: ['저평가'], target: '+15%', stop: '-10%', confidence: 3,
    actual: '+2.4%', review: { verdict: '보류', learned: '단기 변동성에 흔들려 추가 매수를 못 했다. 다음엔 분할매수로 접근하자.' }, note: '',
  },
  {
    id: 3, name: 'NVIDIA', logo: 'NV', color: '#76b900', date: '2026.05.15', side: '매수',
    reasons: ['실적 개선', '테마/모멘텀'], target: '+30%', stop: '-15%', confidence: 5,
    actual: '+8.2%', review: { verdict: '성공', learned: '실적 모멘텀에 대한 확신이 맞았다. 비중을 더 실어도 좋았을 듯.' }, note: '',
  },
])

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

function saveDiary() {
  entries.value.unshift({
    id: Date.now(),
    name: pendingTrade.name, logo: pendingTrade.logo, color: pendingTrade.color,
    date: '2026.' + pendingTrade.date.replace('.', '.'),
    side: newDiary.value.type,
    reasons: [...newDiary.value.reasons],
    target: newDiary.value.target, stop: newDiary.value.stop,
    confidence: newDiary.value.confidence,
    actual: '+0.0%', review: null, note: newDiary.value.note,
  })
  newDiary.value = { type: '매수', reasons: [], confidence: 3, target: '+20%', stop: '-10%', note: '' }
}

// ===== 일기 인라인 수정 (복기 박스 작성/수정) =====
const editingId = ref(null)
const editText = ref('')
function startEdit(e) {
  if (editingId.value === e.id) { editingId.value = null; return }
  editingId.value = e.id
  editText.value = e.review?.learned ?? ''
}
function saveEdit(e) {
  const text = editText.value.trim()
  if (e.review) e.review.learned = text          // 기존 복기 메모 수정
  else if (text) e.review = { verdict: '보류', learned: text } // 복기 박스 신규 생성
  editingId.value = null
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

    <!-- 작성 대기 알림 -->
    <div class="td-pending panel">
      <div class="td-pending-left">
        <span class="td-pending-ico">📝</span>
        <div>
          <strong>작성 대기 1건</strong>
          <span class="td-pending-desc">매매했는데 아직 일기를 안 쓴 거래예요.</span>
        </div>
      </div>
      <button class="td-pending-chip">
        <span class="td-chip-logo" :style="{ background: pendingTrade.color }">{{ pendingTrade.logo }}</span>
        {{ pendingTrade.name }} · {{ pendingTrade.side }} · {{ pendingTrade.date }} →
      </button>
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
          <p class="td-form-title">🔍 새 매매일기 ({{ pendingTrade.name }} · {{ pendingTrade.date }}) — 다 고르기만!</p>

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

          <button class="td-save-btn" type="button" @click="saveDiary">매매일기 저장</button>
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
.td-chip-logo { width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 11px; font-weight: 900; }

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
.td-status.pending { background: rgba(49,93,255,0.12); color: var(--accent); }
.td-status.done { background: rgba(15,159,110,0.12); color: #0f9f6e; }

.td-tags { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.td-reason { padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; background: rgba(49,93,255,0.08); color: var(--accent); }
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
  box-shadow: 0 6px 18px rgba(49,93,255,0.3); transition: opacity 0.16s, transform 0.16s;
}
.td-save-btn:hover { opacity: 0.92; transform: translateY(-1px); }
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
