<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ===== 보유 종목 (재무 30% · 성장 40% · 궁합 30%) =====
const holdings = [
  {
    code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '전기·전자', logo: 'SK', color: '#e3344f',
    recommend: '장기 보유 강력 추천',
    summary: '성장성(92)이 가중 40%로 종합을 끌어올렸습니다. 재무·궁합도 견조해 장기 보유 매력이 높으나, 포트 비중 38%는 분산 관점에서 관리가 필요합니다.',
    financial: {
      score: 78, note: '부채비율 업종 최저, 수익성 우수. HBM 믹스 개선으로 재무 체력 회복 중.',
      items: [
        { label: '부채비율', value: '22.4%' }, { label: 'ROE', value: '26.78%' },
        { label: '영업이익률', value: '32.1%' }, { label: '유동비율', value: '198.3%' },
      ],
    },
    growth: {
      score: 92, note: 'AI발 HBM 수요로 매출·이익 동반 급증. 중장기 성장 모멘텀 최상위.',
      items: [
        { label: '매출성장률(YoY)', value: '+48.2%' }, { label: '순이익성장률(YoY)', value: '+61.0%' },
        { label: 'EPS 증가율', value: '+58.4%' },
      ],
    },
    compat: {
      score: 87, note: '공격형 성향·반도체 선호와 잘 맞음. 비중 38%로 분산 유의.',
      items: [
        { label: '리스크 매칭', value: '공격형' }, { label: '섹터 매칭', value: '전기·전자' },
        { label: '기간 매칭', value: '12개월' }, { label: '경험 매칭', value: '중급' },
      ],
    },
    journal: [
      { side: 'buy', date: '06.02', note: 'HBM 기대감에 3주 추가 매수했어요.' },
      { side: 'buy', date: '04.12', note: '첫 진입. 장기 보유 목표로 잡음.' },
    ],
    history: [{ month: '3월', score: 81 }, { month: '4월', score: 83 }, { month: '5월', score: 84 }, { month: '6월', score: 86 }],
    news: [
      { headline: '브로드컴 쇼크에 반도체株 동반 약세', source: '한국경제' },
      { headline: 'SK하이닉스 외국인 매도 지속', source: '연합뉴스' },
      { headline: '"HBM은 견조" 증권가 저가매수 의견', source: '머니투데이' },
    ],
  },
  {
    code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자', logo: '삼', color: '#3b5bdb',
    recommend: '보유 유지 · 모니터링 적합',
    summary: '삼성전자는 재무적으로 안정적이며, 특히 성장성 면에서 매우 긍정적인 모습을 보이고 있습니다. 전기·전자 섹터 선호와 맞물려 보유 유지·모니터링에 적합한 종목으로 판단됩니다. 다만 일부 데이터가 부족해 모든 측면을 평가하기엔 제한이 있으나, 전반적으로 장기투자 관점에서 긍정적인 요소가 많습니다.',
    financial: {
      score: 80, note: '삼성전자의 재무 건전성은 부채비율이 27.9%로 낮고, 유동비율이 243.3%로 높아 안정적입니다.',
      items: [
        { label: '부채비율', value: '27.9%' }, { label: 'ROE', value: '8.57%' },
        { label: '영업이익률', value: '14.2%' }, { label: '유동비율', value: '243.3%' },
      ],
    },
    growth: {
      score: 74, note: '매출 성장률이 16.2%로 높고, 영업이익 성장률이 398.3%로 매우 강력하게 나타나고 있습니다.',
      items: [
        { label: '매출성장률(YoY)', value: '+16.2%' }, { label: '영업이익 성장률(YoY)', value: '+398.3%' },
        { label: 'EPS 증가율', value: '+35.1%' },
      ],
    },
    compat: {
      score: 88, note: '전기·전자 섹터에 대한 선호와 일치하며, 균형형 투자 성향에 적합한 종목입니다.',
      items: [
        { label: '리스크 매칭', value: '균형형' }, { label: '섹터 매칭', value: '전기·전자' },
        { label: '기간 매칭', value: '12개월' }, { label: '경험 매칭', value: '중급' },
      ],
    },
    journal: [
      { side: 'buy', date: '05.20', note: '분할 매수 2차. 평단 낮추는 중.' },
      { side: 'buy', date: '03.18', note: '배당 + 장기 보유 목적으로 진입.' },
    ],
    history: [{ month: '3월', score: 77 }, { month: '4월', score: 78 }, { month: '5월', score: 79 }, { month: '6월', score: 80 }],
    news: [
      { headline: '삼성전자 2nm 파운드리 수율 개선…퀄컴 수주 임박', source: '매일경제' },
      { headline: '삼성전자 1분기 영업이익 6.7조…전년비 3배', source: '이데일리' },
      { headline: '외국인 순매도 속 기관은 저가 매수', source: '서울경제' },
    ],
  },
  {
    code: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', sector: '전기·전자', logo: 'N', color: '#76b900',
    recommend: '장기 핵심 보유 추천',
    summary: '재무(92)·성장(96)이 모두 최상위로 종합 91점입니다. 변동성은 높지만 AI 인프라 핵심주로 장기 핵심 보유에 적합합니다.',
    financial: {
      score: 92, note: '압도적 수익성과 잉여현금흐름. 업계 최고 영업이익률.',
      items: [
        { label: '부채비율', value: '41.2%' }, { label: 'ROE', value: '114.3%' },
        { label: '영업이익률', value: '54.7%' }, { label: '유동비율', value: '320.0%' },
      ],
    },
    growth: {
      score: 96, note: '데이터센터 매출 폭증. Blackwell 수요와 CUDA 생태계로 성장 독주.',
      items: [
        { label: '매출성장률(YoY)', value: '+122.4%' }, { label: '순이익성장률(YoY)', value: '+168.0%' },
        { label: 'EPS 증가율', value: '+152.0%' },
      ],
    },
    compat: {
      score: 84, note: '고밸류·고변동성 유의. 해외 비중 확대엔 핵심 종목.',
      items: [
        { label: '리스크 매칭', value: '공격형' }, { label: '섹터 매칭', value: '전기·전자' },
        { label: '기간 매칭', value: '12개월' }, { label: '경험 매칭', value: '중급' },
      ],
    },
    journal: [
      { side: 'buy', date: '05.28', note: '실적 서프라이즈 보고 추가 매수.' },
      { side: 'buy', date: '02.10', note: 'AI 수혜 핵심주로 장기 진입.' },
    ],
    history: [{ month: '3월', score: 88 }, { month: '4월', score: 89 }, { month: '5월', score: 90 }, { month: '6월', score: 91 }],
    news: [
      { headline: 'Blackwell Ultra 출하 급증…Q2 가이던스 상향', source: 'Bloomberg' },
      { headline: '중국 수출 규제 완화 기대에 프리마켓 강세', source: 'CNBC' },
      { headline: '데이터센터 매출 전년비 4배 성장', source: 'Reuters' },
    ],
  },
  {
    code: 'AAPL', name: 'Apple', market: 'NASDAQ', sector: '전기·전자', logo: 'A', color: '#333a45',
    recommend: '장기 보유 적합',
    summary: '재무(88)와 궁합(84)은 견조하나 성장성(68)이 낮아 종합 79점입니다. 안정적 분산용 장기 보유에 적합합니다.',
    financial: {
      score: 88, note: '강력한 브랜드와 현금 창출. 자사주 매입으로 주당가치 상승.',
      items: [
        { label: '부채비율', value: '67.3%' }, { label: 'ROE', value: '141.5%' },
        { label: '영업이익률', value: '31.5%' }, { label: '유동비율', value: '98.0%' },
      ],
    },
    growth: {
      score: 68, note: '하드웨어 성숙으로 성장 둔화. 서비스 매출이 이를 보완.',
      items: [
        { label: '매출성장률(YoY)', value: '+6.2%' }, { label: '순이익성장률(YoY)', value: '+9.4%' },
        { label: 'EPS 증가율', value: '+12.1%' },
      ],
    },
    compat: {
      score: 84, note: '방어적 성장주로 분산 효과 우수. 환율 노출 고려.',
      items: [
        { label: '리스크 매칭', value: '균형형' }, { label: '섹터 매칭', value: '전기·전자' },
        { label: '기간 매칭', value: '12개월+' }, { label: '경험 매칭', value: '중급' },
      ],
    },
    journal: [
      { side: 'buy', date: '05.15', note: '분산 목적 분할 매수.' },
      { side: 'buy', date: '01.22', note: '장기 배당 + 성장 보유로 진입.' },
    ],
    history: [{ month: '3월', score: 76 }, { month: '4월', score: 77 }, { month: '5월', score: 78 }, { month: '6월', score: 79 }],
    news: [
      { headline: 'Apple Intelligence 2.0 공개…Siri 전면 재설계', source: 'Reuters' },
      { headline: '서비스 매출 고성장…하드웨어 둔화 보완', source: 'WSJ' },
      { headline: '인도 시장 판매 호조…신규 성장축 부상', source: 'CNBC' },
    ],
  },
]

// ===== 선택 =====
const selectedIdx = ref(0)
const s = computed(() => holdings[selectedIdx.value])

// ===== 점수 계산 =====
function total(h) { return Math.round(h.financial.score * 0.3 + h.growth.score * 0.4 + h.compat.score * 0.3) }
function grade(score) {
  if (score >= 90) return 'A'
  if (score >= 80) return 'B+'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C+'
  return 'C'
}
function gradeColor(score) {
  if (score >= 80) return '#e3344f'    // 빨강 — 장기 보유 핵심·강력 추천 (80~100)
  if (score >= 40) return 'var(--positive)' // 초록 — 보유 적합 (40~80)
  return '#2b59d6'                      // 파랑 — 40 미만
}
function gradeClass(score) {
  if (score >= 90) return 'g-a'
  if (score >= 80) return 'g-bplus'
  if (score >= 70) return 'g-b'
  return 'g-c'
}

const scoreCards = computed(() => [
  { name: '재무', weight: '30%', ...s.value.financial },
  { name: '성장', weight: '40%', ...s.value.growth },
  { name: '궁합', weight: '30%', ...s.value.compat },
])
</script>

<template>
  <div class="lt-page">

    <!-- 헤더 -->
    <header class="lt-header">
      <h1>장투 페이지</h1>
      <p class="lt-sub">내가 산 종목, 계속 들고 갈 만한가요? — 재무 30% · 성장 40% · 궁합 30% 가중으로 점검해드려요.</p>
    </header>

    <div class="lt-grid">

      <!-- ===== 좌: 보유 종목 ===== -->
      <aside class="panel lt-list" aria-label="보유 종목">
        <p class="lt-list-title">보유 종목</p>
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
            <strong :style="{ color: gradeColor(total(h)) }">{{ total(h) }}</strong>
            <span class="lt-grade" :class="gradeClass(total(h))">{{ grade(total(h)) }}</span>
          </div>
        </button>
      </aside>

      <!-- ===== 우: 상세 ===== -->
      <div class="lt-detail">

        <!-- 종합 정보 -->
        <section class="panel lt-overview">
          <div class="lt-ov-circle" :style="{ background: gradeColor(total(s)) }">
            {{ total(s) }}
            <span>{{ grade(total(s)) }}</span>
          </div>
          <div class="lt-ov-body">
            <div class="lt-ov-head">
              <strong class="lt-ov-name">{{ s.name }}</strong>
              <span class="lt-ov-code">{{ s.code }}</span>
            </div>
            <div class="lt-ov-reco" :style="{ color: gradeColor(total(s)) }">{{ s.recommend }}</div>
            <p class="lt-ov-summary">🐤 {{ s.summary }}</p>
          </div>
          <button class="lt-ov-go" type="button" @click="router.push(`/stocks/${s.code}`)">
            종목 상세 →
          </button>
        </section>

        <!-- 재무 / 성장 / 궁합 -->
        <div class="lt-score-row">
          <div v-for="card in scoreCards" :key="card.name" class="panel lt-score-card">
            <div class="lt-score-top">
              <span class="lt-score-name">{{ card.name }} <span class="lt-weight">{{ card.weight }}</span></span>
              <strong class="lt-score-num">{{ card.score }}</strong>
            </div>
            <div class="lt-score-bar"><div :style="{ width: card.score + '%' }"></div></div>
            <div class="lt-score-items">
              <div v-for="it in card.items" :key="it.label" class="lt-score-item">
                <span>{{ it.label }}</span>
                <strong>{{ it.value }}</strong>
              </div>
            </div>
            <p class="lt-score-note">🐤 {{ card.note }}</p>
          </div>
        </div>

        <!-- 매매일지 + 점수 히스토리 -->
        <div class="lt-mid-row">
          <section class="panel lt-card">
            <p class="lt-card-title">📒 이 종목 매매일지</p>
            <div class="lt-journal-list">
              <div v-for="(j, i) in s.journal" :key="i" class="lt-journal-item">
                <div class="lt-j-head">
                  <span class="lt-j-side" :class="j.side">{{ j.side === 'buy' ? '매수' : '매도' }}</span>
                  <span class="lt-j-date">{{ j.date }}</span>
                </div>
                <p class="lt-j-note">{{ j.note }}</p>
              </div>
            </div>
          </section>

          <section class="panel lt-card">
            <p class="lt-card-title">📈 장투 점수 히스토리</p>
            <div class="lt-history-list">
              <div v-for="(hi, i) in s.history" :key="hi.month" class="lt-history-row">
                <span class="lt-h-month">{{ hi.month }}</span>
                <span class="lt-h-score" :style="{ color: gradeColor(hi.score) }">
                  {{ hi.score }}점
                  <span v-if="i > 0 && hi.score > s.history[i - 1].score" class="lt-h-up">▲</span>
                </span>
              </div>
            </div>
          </section>
        </div>

        <!-- 종목 관련 뉴스 -->
        <section class="panel lt-card">
          <p class="lt-card-title">📰 종목 관련 뉴스</p>
          <div class="lt-news-list">
            <article v-for="(n, i) in s.news" :key="i" class="lt-news-item">
              <strong class="lt-news-headline">{{ n.headline }}</strong>
              <span class="lt-news-source">{{ n.source }}</span>
            </article>
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

/* 매매일지 + 히스토리 */
.lt-mid-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; align-items: start; }
.lt-card { padding: 18px 20px; }
.lt-card-title { font-size: 14px; font-weight: 900; color: var(--ink); margin: 0 0 14px; }

.lt-journal-list { display: flex; flex-direction: column; gap: 12px; }
.lt-journal-item { padding-bottom: 12px; border-bottom: 1px solid var(--line); }
.lt-journal-item:last-child { padding-bottom: 0; border-bottom: 0; }
.lt-j-head { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.lt-j-side { padding: 2px 9px; border-radius: 6px; font-size: 11px; font-weight: 900; }
.lt-j-side.buy { background: rgba(227,52,79,0.12); color: #e3344f; }
.lt-j-side.sell { background: rgba(43,89,214,0.12); color: #2b59d6; }
.lt-j-date { font-size: 12px; font-weight: 800; color: var(--muted); }
.lt-j-note { margin: 0; font-size: 13px; font-weight: 700; color: var(--ink); line-height: 1.5; word-break: keep-all; }

.lt-history-list { display: flex; flex-direction: column; }
.lt-history-row { display: flex; align-items: center; justify-content: space-between; padding: 11px 0; border-bottom: 1px solid var(--line); }
.lt-history-row:last-child { border-bottom: 0; }
.lt-h-month { font-size: 13px; font-weight: 700; color: var(--muted); }
.lt-h-score { font-size: 14px; font-weight: 900; }
.lt-h-up { color: #0f9f6e; font-size: 11px; margin-left: 2px; }

/* 뉴스 */
.lt-news-list { display: flex; flex-direction: column; }
.lt-news-item { display: flex; align-items: baseline; gap: 10px; padding: 12px 0; border-bottom: 1px solid var(--line); cursor: pointer; }
.lt-news-item:last-child { border-bottom: 0; }
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
