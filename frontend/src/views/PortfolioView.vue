<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchHoldings, fetchOrders } from '../api/portfolio'
import { fetchStockFinancials } from '../api/stocks'
import { fetchLongtermReport, fetchLongtermHistory } from '../api/recommend'
import { fetchHoldingsNews } from '../api/news'
import { fetchDiaries } from '../api/diary'
import { errMsg, retry } from '../api/client'
import { useCopy } from '../composables/useCopy'

// 이 컴포넌트는 v-for 루프 변수로 t를 쓰므로 헬퍼는 tr로 별칭
const { t: tr } = useCopy()
const router = useRouter()
const loading = ref(true)
const loadError = ref('')

// 보유 종목 (실데이터: GET /portfolio/holdings/ + 종목별 장투 리포트). 목업 fallback 제거 — 실패 시 가짜 노출 방지.
const holdings = ref([])

// ===== 선택 =====
const selectedIdx = ref(0)
const s = computed(() => holdings.value[selectedIdx.value] || holdings.value[0] || null)

// ===== 점수 계산 =====
// report.total.score(h.total)가 있으면 사용. 리포트 없는 종목은 null → 0점/C 오표시 대신 "—" 표시.
function total(h) {
  if (!h || h.total == null) return null
  return Math.round(h.total)
}
function grade(score) {
  if (score == null) return '—'
  if (score >= 90) return 'A'
  if (score >= 80) return 'B+'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C+'
  return 'C'
}
function gradeColor(score) {
  if (score == null) return 'var(--muted)' // 리포트 없음 — 중립
  if (score >= 80) return '#e3344f'    // 빨강 — 장기 보유 핵심·강력 추천 (80~100)
  if (score >= 40) return 'var(--positive)' // 초록 — 보유 적합 (40~80)
  return '#2b59d6'                      // 파랑 — 40 미만
}
function gradeClass(score) {
  if (score == null) return 'g-none'
  if (score >= 90) return 'g-a'
  if (score >= 80) return 'g-bplus'
  if (score >= 70) return 'g-b'
  return 'g-c'
}

const scoreCards = computed(() => {
  if (!s.value) return []
  return [
    { name: '재무', weight: '30%', ...s.value.financial },
    { name: '성장', weight: '40%', ...s.value.growth },
    { name: '궁합', weight: '30%', ...s.value.compat },
  ]
})

// ===== 실데이터 로딩 (보유 → 종목별 장투 리포트 + 재무, 보유 뉴스 1회 그룹핑) =====
const PALETTE = ['#e3344f', '#3b5bdb', '#76b900', '#333a45', '#22c55e', '#8b5cf6', '#06b6d4', '#f59e0b']
function colorFor(code) {
  let h = 0
  for (const ch of code) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return PALETTE[h % PALETTE.length]
}
const pct = (v, d = 1) => (v == null ? null : (v * 100).toFixed(d) + '%')
const signedPct = (v) => (v == null ? null : (v >= 0 ? '+' : '') + (v * 100).toFixed(1) + '%')

async function loadPortfolio() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await retry(() => fetchHoldings(), { attempts: 5, delayMs: 500 }) // KIS 간헐 503 대비
    const items = data.items || []

    // 보유 뉴스는 한 번만 호출해 종목코드별로 그룹핑
    const newsByCode = {}
    try {
      const nz = await fetchHoldingsNews()
      for (const n of nz.items || []) {
        const c = n.stock?.code
        if (c) (newsByCode[c] ||= []).push({ headline: n.title, source: n.source, url: n.url })
      }
    } catch {
      // 뉴스 실패 무시
    }

    // 내 매매일지도 한 번만 호출해 종목코드별로 그룹핑(장투 페이지에 반영)
    const REASON_LABEL = {
      GROWTH: '장기 성장성', EARNINGS: '실적 개선', UNDERVALUED: '저평가',
      THEME: '테마/모멘텀', NEWS: '뉴스 호재', TECHNICAL: '기술적 반등',
    }
    const diaryByCode = {}
    try {
      const dz = await fetchDiaries({ size: 100 })
      for (const d of dz.items || []) {
        const c = d.stock_code
        if (!c) continue
        const side = d.action_type === 'SELL' ? 'sell' : 'buy'
        ;(diaryByCode[c] ||= []).push({
          side,
          date: (d.created_at || '').slice(0, 10).replace(/-/g, '.'),
          note: d.memo || REASON_LABEL[d.reason_category] || (side === 'sell' ? '매도 기록' : '매수 기록'),
        })
      }
    } catch {
      // 일지 실패 무시
    }

    // 거래내역(주문)도 한 번 호출해 종목코드별로 그룹핑(최신순)
    const ordersByCode = {}
    try {
      const oz = await fetchOrders({ size: 200 })
      for (const o of oz.items || []) {
        const c = o.stock_code
        if (!c) continue
        ;(ordersByCode[c] ||= []).push({
          side: o.side === 'SELL' ? 'sell' : 'buy',
          date: (o.executed_at || o.created_at || '').slice(0, 10).replace(/-/g, '.'),
          qty: o.quantity,
          price: o.price == null ? '' : Number(o.price).toLocaleString('ko-KR'),
        })
      }
    } catch {
      // 거래내역 실패 무시
    }

    holdings.value = await Promise.all(
      items.map(async (it) => {
        const code = it.stock.code
        const [report, fin, hist] = await Promise.all([
          fetchLongtermReport(code).catch(() => null),
          fetchStockFinancials(code).catch(() => null),
          fetchLongtermHistory(code).catch(() => null),
        ])
        const sum = fin?.summaries?.[0] || {}
        const ind = fin?.indicator || {}
        const finItems = []
        if (sum.debt_ratio != null) finItems.push({ label: '부채비율', value: pct(sum.debt_ratio) })
        if (ind.roe != null) finItems.push({ label: 'ROE', value: pct(ind.roe, 2) })
        if (sum.operating_margin != null) finItems.push({ label: '영업이익률', value: pct(sum.operating_margin) })
        if (sum.current_ratio != null) finItems.push({ label: '유동비율', value: pct(sum.current_ratio) })
        const growthItems = []
        if (sum.revenue_yoy != null) growthItems.push({ label: '매출성장률(YoY)', value: signedPct(sum.revenue_yoy) })
        if (sum.operating_profit_yoy != null) growthItems.push({ label: '영업이익성장률(YoY)', value: signedPct(sum.operating_profit_yoy) })
        if (sum.net_profit_yoy != null) growthItems.push({ label: '순이익성장률(YoY)', value: signedPct(sum.net_profit_yoy) })

        const r = report || {}
        const uf = r.userfit
        return {
          code,
          hasReport: !!r.total, // 장투 리포트 존재 여부 — 없으면 0점 카드 대신 안내
          name: it.stock.name,
          market: it.stock.market,
          sector: it.stock.sector,
          logo: it.stock.name.slice(0, 1),
          color: colorFor(code),
          total: r.total?.score ?? null, // 리포트 없으면 null → "—" 표시(0점/C 오표시 방지)
          recommend: r.total?.label ?? '리포트 준비 중',
          summary: r.total?.opinion ?? '리포트를 준비 중이에요.',
          financial: { score: Math.round(r.financial?.score ?? 0), note: r.financial?.summary ?? '', items: finItems },
          growth: { score: Math.round(r.growth?.score ?? 0), note: r.growth?.summary ?? '', items: growthItems },
          compat: uf
            ? { score: Math.round(uf.score), note: uf.summary, items: uf.components || [] }
            : { score: 0, note: '온보딩을 완료하면 궁합 분석을 볼 수 있어요.', items: [] },
          journal: diaryByCode[code] || [],
          trades: ordersByCode[code] || [],
          history: (hist?.items || []).map((h) => ({ month: h.month, score: Math.round(h.score) })),
          news: newsByCode[code] || [],
        }
      }),
    )
    selectedIdx.value = 0
  } catch (e) {
    loadError.value = errMsg(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadPortfolio)
</script>

<template>
  <div class="lt-page">

    <!-- 헤더 -->
    <header class="lt-header">
      <h1>{{ tr('lt.title', '장투 페이지') }} <span class="ai-tag ai-tag-lg">AI</span></h1>
      <p class="lt-sub">{{ tr('lt.sub', '내가 산 종목, 계속 들고 갈 만한가요? — 재무 30% · 성장 40% · 궁합 30% 가중으로 점검해드려요.') }}</p>
    </header>

    <!-- 로드 오류 -->
    <p v-if="loadError" class="lt-error">{{ loadError }}</p>

    <div class="lt-grid">

      <!-- ===== 좌: 보유 종목 ===== -->
      <aside class="panel lt-list" aria-label="보유 종목">
        <p class="lt-list-title">{{ tr('lt.list.title', '보유 종목') }}</p>
        <button
          v-for="(h, i) in holdings"
          :key="h.code"
          type="button"
          class="lt-list-item"
          :class="{ active: selectedIdx === i }"
          @click="selectedIdx = i"
        >
          <span class="lt-logo" :style="{ background: h.color }">{{ h.logo }}</span>
          <div class="lt-list-info">
            <strong>{{ h.name }}</strong>
            <span>{{ h.sector }} · {{ h.market }}</span>
          </div>
          <div class="lt-list-score">
            <strong :style="{ color: gradeColor(total(h)) }">{{ total(h) ?? '—' }}</strong>
            <span class="lt-grade" :class="gradeClass(total(h))">{{ grade(total(h)) }}</span>
          </div>
        </button>
      </aside>

      <!-- ===== 우: 상세 ===== -->
      <div v-if="!s" class="panel" style="padding: 28px; text-align: center; color: var(--muted); font-weight: 700;">
        {{ loading ? '장투 리포트를 분석하는 중이에요…'
          : loadError ? '보유 종목을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'
          : '보유 종목이 없어요. 종목을 매수하면 장투 분석이 표시됩니다.' }}
      </div>
      <div v-else class="lt-detail">

        <!-- 종합 정보 -->
        <section class="panel lt-overview">
          <div class="lt-ov-circle" :style="{ background: gradeColor(total(s)) }">
            {{ total(s) ?? '—' }}
            <span>{{ total(s) == null ? '분석중' : grade(total(s)) }}</span>
          </div>
          <div class="lt-ov-body">
            <div class="lt-ov-head">
              <strong class="lt-ov-name">{{ s.name }}</strong>
              <span class="lt-ov-code">{{ s.code }}</span>
            </div>
            <div class="lt-ov-reco" :style="{ color: gradeColor(total(s)) }">{{ s.recommend }}</div>
            <p class="lt-ov-summary"><span class="ai-tag">AI</span> {{ s.summary }}</p>
          </div>
          <button class="lt-ov-go" type="button" @click="router.push(`/stocks/${s.code}`)">
            {{ tr('lt.overview.go', '종목 상세 →') }}
          </button>
        </section>

        <!-- 리포트 없는 종목: 0점 카드 대신 안내 -->
        <section v-if="!s.hasReport" class="panel lt-no-report">
          <span class="ai-tag">AI</span> 아직 이 종목의 장투 리포트가 준비되지 않았어요. 분석이 완료되면 재무·성장·궁합 점수가 표시됩니다.
        </section>

        <!-- 재무 / 성장 / 궁합 -->
        <div v-else class="lt-score-row">
          <div v-for="card in scoreCards" :key="card.name" class="panel lt-score-card">
            <div class="lt-score-top">
              <span class="lt-score-name">{{ tr('lt.score.' + card.name, card.name) }} <span class="lt-weight">{{ card.weight }}</span></span>
              <strong class="lt-score-num">{{ card.score }}</strong>
            </div>
            <div class="lt-score-bar"><div :style="{ width: card.score + '%' }"></div></div>
            <div class="lt-score-items">
              <div v-for="it in card.items" :key="it.label" class="lt-score-item">
                <span>{{ it.label }}</span>
                <strong>{{ it.value }}</strong>
              </div>
            </div>
            <p class="lt-score-note"><span class="ai-tag">AI</span> {{ card.note }}</p>
          </div>
        </div>

        <!-- 거래내역 + 매매일기 + 궁합 히스토리 (3분할) -->
        <div class="lt-mid-row">
          <section class="panel lt-card">
            <p class="lt-card-title">🧾 이 종목 거래내역</p>
            <div class="lt-journal-list">
              <div v-for="(t, i) in s.trades" :key="i" class="lt-row1">
                <span class="lt-j-side" :class="t.side">{{ t.side === 'buy' ? tr('lt.side.buy', '매수') : tr('lt.side.sell', '매도') }}</span>
                <span class="lt-j-date">{{ t.date }}</span>
                <span class="lt-row1-note">{{ t.qty }}주 @ {{ t.price }}</span>
              </div>
              <p v-if="!s.trades.length" class="lt-empty">이 종목 거래내역이 없어요.</p>
            </div>
          </section>

          <section class="panel lt-card">
            <p class="lt-card-title">{{ tr('lt.journal.title', '📒 이 종목 매매일기') }}</p>
            <div class="lt-journal-list">
              <div v-for="(j, i) in s.journal" :key="i" class="lt-row1">
                <span class="lt-j-side" :class="j.side">{{ j.side === 'buy' ? tr('lt.side.buy', '매수') : tr('lt.side.sell', '매도') }}</span>
                <span class="lt-j-date">{{ j.date }}</span>
                <span class="lt-row1-note">{{ j.note }}</span>
              </div>
              <p v-if="!s.journal.length" class="lt-empty">이 종목으로 작성한 매매일기가 없어요.</p>
            </div>
          </section>

          <section class="panel lt-card">
            <p class="lt-card-title">{{ tr('lt.history.title', '📈 장투 점수 히스토리') }}</p>
            <div class="lt-history-list">
              <div v-for="(hi, i) in s.history" :key="hi.month" class="lt-history-row">
                <span class="lt-h-month">{{ hi.month }}</span>
                <span class="lt-h-score" :style="{ color: gradeColor(hi.score) }">
                  {{ hi.score }}점
                  <span v-if="i > 0 && hi.score > s.history[i - 1].score" class="lt-h-up">▲</span>
                </span>
              </div>
              <p v-if="!s.history.length" class="lt-empty">장투 점수 히스토리가 아직 없어요.</p>
            </div>
          </section>
        </div>

        <!-- 종목 관련 뉴스 -->
        <section class="panel lt-card">
          <p class="lt-card-title">{{ tr('lt.news.title', '📰 종목 관련 뉴스') }}</p>
          <div class="lt-news-list">
            <a
              v-for="(n, i) in s.news"
              :key="i"
              class="lt-news-item"
              :href="n.url || undefined"
              :target="n.url ? '_blank' : undefined"
              rel="noopener noreferrer"
            >
              <strong class="lt-news-headline">{{ n.headline }}</strong>
              <span class="lt-news-source">{{ n.source }}</span>
            </a>
            <p v-if="!s.news.length" class="lt-empty">관련 뉴스가 아직 없어요.</p>
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<style scoped>
.lt-page { display: flex; flex-direction: column; gap: 16px; }

/* 헤더 */
.lt-header h1 { font-size: clamp(26px, 4vw, 36px); font-weight: 900; color: var(--ink); letter-spacing: -1px; margin: 0; }
.lt-sub { margin: 6px 0 0; font-size: 13px; font-weight: 700; color: var(--muted); word-break: keep-all; }

/* 레이아웃 */
.lt-grid { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 16px; align-items: start; }

/* 좌: 보유 종목 */
.lt-list { padding: 14px; display: flex; flex-direction: column; gap: 4px; position: sticky; top: 80px; }
.lt-list-title { font-size: 13px; font-weight: 900; color: var(--muted); margin: 2px 4px 8px; }
.lt-list-item {
  display: flex; align-items: center; gap: 10px; width: 100%;
  padding: 12px; border: 0; border-left: 3px solid transparent; border-radius: var(--radius);
  background: transparent; cursor: pointer; text-align: left; transition: background 0.16s, box-shadow 0.2s ease, border-color 0.16s;
}
.lt-list-item:hover { background: var(--surface-soft); }
.lt-list-item.active {
  background: rgba(var(--accent-rgb),0.08);
  border-left-color: var(--accent);
  box-shadow: 0 1px 3px rgba(17,24,39,0.06);
}
.lt-logo { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 900; flex-shrink: 0; }
.lt-list-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.lt-list-info strong { font-size: 14px; font-weight: 900; color: var(--ink); }
.lt-list-info span { font-size: 11px; font-weight: 700; color: var(--muted); }
.lt-list-score { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.lt-list-score > strong { font-size: 17px; font-weight: 900; }
.lt-grade { padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 900; }
.g-a { background: rgba(15,159,110,0.12); color: #0f9f6e; }
.g-bplus { background: rgba(var(--accent-rgb),0.12); color: var(--accent); }
.g-b { background: rgba(229,139,16,0.14); color: #e58b10; }
.g-c { background: rgba(207,61,61,0.12); color: #cf3d3d; }
.g-none { background: var(--glass-subtle); color: var(--muted); }

/* 오류 배너 / 빈 상태 / 리포트 없음 */
.lt-error { margin: 0; padding: 10px 14px; border-radius: var(--radius); border: 1px solid rgba(207,61,61,0.3); background: rgba(207,61,61,0.08); color: #cf3d3d; font-size: 13px; font-weight: 800; }
.lt-empty { margin: 4px 0 0; padding: 14px 0; text-align: center; font-size: 12px; font-weight: 700; color: var(--faint); }
.lt-no-report { padding: 20px 22px; font-size: 13px; font-weight: 700; color: var(--muted); line-height: 1.6; word-break: keep-all; }

/* 우 */
.lt-detail { display: flex; flex-direction: column; gap: 16px; min-width: 0; }

/* 종합 정보 */
.lt-overview { display: flex; align-items: center; gap: 20px; padding: 22px 24px; background: var(--glass); }
.lt-ov-circle {
  width: 80px; height: 80px; border-radius: 50%; flex-shrink: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #fff; font-size: 28px; font-weight: 900; line-height: 1;
  box-shadow: 0 8px 24px rgba(var(--accent-rgb),0.25);
}
.lt-ov-circle span { font-size: 12px; font-weight: 900; margin-top: 3px; opacity: 0.92; }
.lt-ov-body { flex: 1; min-width: 0; }
.lt-ov-head { display: flex; align-items: baseline; gap: 8px; }
.lt-ov-name { font-size: 22px; font-weight: 900; color: var(--ink); letter-spacing: -0.5px; }
.lt-ov-code { font-size: 13px; font-weight: 700; color: var(--muted); }
.lt-ov-reco { font-size: 15px; font-weight: 900; margin: 4px 0 8px; }
.lt-ov-summary { margin: 0; font-size: 13px; font-weight: 700; color: var(--text); line-height: 1.6; word-break: keep-all; }

/* LLM 분석 표시용 텍스트형 AI 배지 */
.ai-tag {
  display: inline-block;
  padding: 1px 6px;
  margin-right: 5px;
  border-radius: 5px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.5px;
  vertical-align: middle;
}
/* 헤더 옆 큰 버전 */
.ai-tag-lg {
  font-size: 16px;
  padding: 3px 11px;
  border-radius: 8px;
  letter-spacing: 1px;
  margin-left: 4px;
  vertical-align: 4px;
  box-shadow: 0 4px 12px rgba(var(--accent-rgb),0.3);
}
.lt-ov-go {
  align-self: flex-start;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 9px 16px;
  border-radius: 999px;
  border: 1px solid rgba(var(--accent-rgb),0.28);
  background: rgba(var(--accent-rgb),0.1);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.16s, transform 0.16s;
}
.lt-ov-go:hover { background: rgba(var(--accent-rgb),0.2); transform: translateY(-1px); }

/* 재무/성장/궁합 카드 */
.lt-score-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.lt-score-card { padding: 18px; display: flex; flex-direction: column; }
.lt-score-top { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.lt-score-name { font-size: 15px; font-weight: 900; color: var(--ink); }
.lt-weight { font-size: 11px; font-weight: 900; color: var(--faint); margin-left: 4px; }
.lt-score-num { font-size: 28px; font-weight: 900; color: var(--ink); letter-spacing: -1px; }
.lt-score-bar { height: 7px; border-radius: 999px; background: var(--surface-soft); overflow: hidden; margin-bottom: 14px; }
.lt-score-bar > div { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--purple)); transition: width 0.5s ease; }
.lt-score-items { display: flex; flex-direction: column; gap: 0; margin-bottom: 14px; }
.lt-score-item { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line); }
.lt-score-item:last-child { border-bottom: 0; }
.lt-score-item span { font-size: 12px; font-weight: 700; color: var(--muted); }
.lt-score-item strong { font-size: 13px; font-weight: 900; color: var(--accent); }
.lt-score-note { margin: auto 0 0; padding: 12px 14px; border-radius: var(--radius); background: var(--glass-subtle); border: 1px solid var(--glass-border); font-size: 12px; font-weight: 700; color: var(--muted); line-height: 1.55; word-break: keep-all; }

/* 거래내역 + 매매일기 + 궁합 히스토리 (3분할) */
.lt-mid-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; align-items: start; }
.lt-card { padding: 18px 20px; }
.lt-card-title { font-size: 14px; font-weight: 900; color: var(--ink); margin: 0 0 14px; }

/* 한 줄 항목 리스트 (거래내역·매매일기) — 높이 제한 + 넘치면 스크롤 */
.lt-journal-list { display: flex; flex-direction: column; gap: 0; max-height: 168px; overflow-y: auto; }
.lt-row1 { display: flex; align-items: center; gap: 8px; padding: 7px 2px; border-bottom: 1px solid var(--line); }
.lt-row1:last-child { border-bottom: 0; }
.lt-j-side { padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 900; flex-shrink: 0; }
.lt-j-side.buy { background: rgba(227,52,79,0.12); color: #e3344f; }
.lt-j-side.sell { background: rgba(43,89,214,0.12); color: #2b59d6; }
.lt-j-date { font-size: 12px; font-weight: 800; color: var(--muted); flex-shrink: 0; }
.lt-row1-note { flex: 1; min-width: 0; text-align: right; font-size: 12.5px; font-weight: 700; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.lt-history-list { display: flex; flex-direction: column; max-height: 168px; overflow-y: auto; }
.lt-history-row { display: flex; align-items: center; justify-content: space-between; padding: 11px 0; border-bottom: 1px solid var(--line); }
.lt-history-row:last-child { border-bottom: 0; }
.lt-h-month { font-size: 13px; font-weight: 700; color: var(--muted); }
.lt-h-score { font-size: 14px; font-weight: 900; }
.lt-h-up { color: #0f9f6e; font-size: 11px; margin-left: 2px; }

/* 뉴스 */
.lt-news-list { display: flex; flex-direction: column; }
.lt-news-item { display: flex; align-items: baseline; gap: 10px; padding: 12px 0; border-bottom: 1px solid var(--line); cursor: pointer; text-decoration: none; color: inherit; transition: opacity 0.15s; }
.lt-news-item:last-child { border-bottom: 0; }
.lt-news-item:hover .lt-news-headline { color: var(--accent); }
.lt-news-headline { font-size: 14px; font-weight: 800; color: var(--ink); line-height: 1.45; word-break: keep-all; }
.lt-news-source { font-size: 11px; font-weight: 700; color: var(--faint); flex-shrink: 0; }

/* 반응형 */
@media (max-width: 1100px) {
  .lt-grid { grid-template-columns: 1fr; }
  .lt-list { position: static; flex-direction: row; flex-wrap: wrap; }
  .lt-list-item { flex: 1; min-width: 200px; }
  .lt-score-row { grid-template-columns: 1fr; }
  .lt-mid-row { grid-template-columns: 1fr; }
}

/* 모바일: 보유 종목 리스트를 1열로 */
@media (max-width: 800px) {
  .lt-list { flex-direction: column; }
  .lt-list-item { flex: none; min-width: 0; }
}
</style>
