<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'

// ── 장투 케어 (와이어프레임 image46) ──
// "내가 산 종목, 계속 들고 갈 만한가요? — 재무 30% · 성장 40% · 궁합 30%"
// 점수 산출은 추천 도메인(정율) — 현재 목업 (백엔드 미구현, 검토 메모 참고)

const careStocks = [
  {
    code: '000660', name: 'SK하이닉스', market: 'KOSPI', code2: 'SK', color: '#e6007e',
    total: 86, grade: 'B+', headline: '장기 보유 강력 추천',
    desc: '성장성(92)이 가장 종합을 끌어올렸습니다. 재무도 견조해 장기 매력이 높으나, 포트 비중 38%는 분산 관점에서 관리가 필요합니다.',
    finance: { score: 78, items: [['부채비율', '22.4%'], ['ROE', '26.78%'], ['영업이익률', '32.1%'], ['유동비율', '198.3%']], note: '부채비율 업종 평균 하회, 수익성 우수. HBM 사이클 진입으로 현금흐름 개선.' },
    growth: { score: 92, items: [['매출성장(YoY)', '+48.2%'], ['순이익성장(YoY)', '+61.0%'], ['EPS 증가율', '+58.4%']], note: 'AI·HBM 수요로 매출·이익 동반 급증. 성장 모멘텀 최상위.' },
    fit: { score: 87, items: [['리스크 매칭', '공격형'], ['섹터 매칭', '전기전자'], ['기간 매칭', '12개월'], ['경험 매칭', '중급']], note: '공격형 성향·섹터 선호와 잘 맞음. 비중 38%만 분산 유의.' },
    diary: [
      { date: '06.02', side: '매수', text: 'HBM 기대감에 3주 추가 매수' },
      { date: '04.12', side: '매수', text: '첫 진입, 장기 보유 목표로 잡음' },
    ],
    history: [{ m: '3월', s: 81 }, { m: '4월', s: 83 }, { m: '5월', s: 84 }, { m: '6월', s: 86 }],
    news: [['브로드컴 4분기 실적 쇼크…반도체 동반 약세', '한국경제'], ['SK하이닉스 외국인 매도 지속', '연합뉴스'], ['"HBM은 견조" 증권가 저가매수 의견', '머니투데이']],
  },
  {
    code: '005930', name: '삼성전자', market: 'KOSPI', code2: '삼', color: '#315dff',
    total: 80, grade: 'B+', headline: '보유 유지 권장',
    desc: '안정적 재무와 배당 매력이 강점. 성장성은 업종 내 평균 수준으로, 분산 코어 자산으로 적합합니다.',
    finance: { score: 84, items: [['부채비율', '11.2%'], ['ROE', '8.57%'], ['영업이익률', '14.6%'], ['유동비율', '241.0%']], note: '재무 안정성 최상위, 보수적 포지션에 적합.' },
    growth: { score: 71, items: [['매출성장(YoY)', '+9.4%'], ['순이익성장(YoY)', '+12.1%'], ['EPS 증가율', '+10.3%']], note: '완만한 성장. 메모리 업황 회복 기대.' },
    fit: { score: 83, items: [['리스크 매칭', '중립형'], ['섹터 매칭', '전기전자'], ['기간 매칭', '12개월'], ['경험 매칭', '초급']], note: '코어 분산 종목으로 성향과 부합.' },
    diary: [{ date: '05.22', side: '매도', text: '비중 조절 차익 실현' }, { date: '03.15', side: '매수', text: '코어 자산으로 분할 매수' }],
    history: [{ m: '3월', s: 77 }, { m: '4월', s: 78 }, { m: '5월', s: 79 }, { m: '6월', s: 80 }],
    news: [['반도체 업황 회복 기대… 외국인 순매수 전환', '한국경제'], ['갤럭시 신제품 사이클 기대', '머니투데이']],
  },
  {
    code: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', code2: 'NV', color: '#0f9f6e',
    total: 91, grade: 'A', headline: '장기 보유 강력 추천',
    desc: '폭발적 성장성이 종합을 견인. 다만 밸류에이션·변동성이 높아 비중 관리가 핵심입니다.',
    finance: { score: 82, items: [['부채비율', '17.0%'], ['ROE', '114.29%'], ['영업이익률', '54.1%'], ['유동비율', '420.0%']], note: '높은 수익성·현금창출력. 부채 부담 낮음.' },
    growth: { score: 98, items: [['매출성장(YoY)', '+122.4%'], ['순이익성장(YoY)', '+168.0%'], ['EPS 증가율', '+150.2%']], note: 'AI 가속기 독점적 수요. 성장 최상위.' },
    fit: { score: 88, items: [['리스크 매칭', '공격형'], ['섹터 매칭', '반도체'], ['기간 매칭', '12개월'], ['경험 매칭', '중급']], note: '공격형 성향에 최적. 변동성 유의.' },
    diary: [{ date: '06.03', side: '매수', text: '실적 발표 전 분할 매수' }],
    history: [{ m: '3월', s: 86 }, { m: '4월', s: 88 }, { m: '5월', s: 90 }, { m: '6월', s: 91 }],
    news: [['AI 가속기 수요 강세, 사상 최고가 경신', '연합뉴스'], ['데이터센터 매출 가이던스 상향', '머니투데이']],
  },
  {
    code: 'AAPL', name: 'Apple', market: 'NASDAQ', code2: 'A', color: '#7d4ee8',
    total: 79, grade: 'B', headline: '보유 유지',
    desc: '안정적 현금흐름과 브랜드 파워가 강점. 성장 둔화 구간이라 코어 분산 종목으로 적합합니다.',
    finance: { score: 86, items: [['부채비율', '31.0%'], ['ROE', '141.47%'], ['영업이익률', '30.2%'], ['유동비율', '98.0%']], note: '압도적 수익성·현금흐름. 자사주 매입 지속.' },
    growth: { score: 70, items: [['매출성장(YoY)', '+4.9%'], ['순이익성장(YoY)', '+7.2%'], ['EPS 증가율', '+9.1%']], note: '성장 둔화 구간. 서비스 부문 성장 의존.' },
    fit: { score: 80, items: [['리스크 매칭', '중립형'], ['섹터 매칭', 'IT·소비재'], ['기간 매칭', '12개월'], ['경험 매칭', '초급']], note: '안정 코어 자산으로 성향과 부합.' },
    diary: [{ date: '05.28', side: '매수', text: '미국장 코어로 소액 진입' }],
    history: [{ m: '3월', s: 76 }, { m: '4월', s: 77 }, { m: '5월', s: 78 }, { m: '6월', s: 79 }],
    news: [['신제품 사이클 기대감에 강보합', '연합뉴스'], ['서비스 매출 사상 최대', '한국경제']],
  },
]

const selectedCode = ref('000660')
const sel = computed(() => careStocks.find((s) => s.code === selectedCode.value) || careStocks[0])
const blocks = computed(() => [
  { key: 'finance', label: '재무', weight: 30, color: '#315dff', ...sel.value.finance },
  { key: 'growth', label: '성장', weight: 40, color: '#0f9f6e', ...sel.value.growth },
  { key: 'fit', label: '궁합', weight: 30, color: '#e58b10', ...sel.value.fit },
])
const maxHist = computed(() => Math.max(...sel.value.history.map((h) => h.s)))
</script>

<template>
  <div>
    <header class="topbar">
      <div>
        <p class="eyebrow">내가 산 종목, 계속 들고 갈 만한가요? — 재무 30% · 성장 40% · 궁합 30%</p>
        <h1>장투 케어</h1>
      </div>
    </header>

    <div class="care-layout">
      <!-- 보유 종목 리스트 -->
      <section class="panel">
        <div class="panel-head"><div><p class="eyebrow">보유 종목</p><h2>점검 종목</h2></div></div>
        <div class="care-list">
          <button
            v-for="s in careStocks"
            :key="s.code"
            type="button"
            class="care-row"
            :class="{ 'is-selected': selectedCode === s.code }"
            @click="selectedCode = s.code"
          >
            <span class="care-logo" :style="{ background: s.color }">{{ s.code2 }}</span>
            <span class="care-row-info">
              <span class="care-row-name">{{ s.name }}</span>
              <span class="care-row-market">{{ s.market }}</span>
            </span>
            <span class="care-row-score">{{ s.total }}</span>
          </button>
        </div>
      </section>

      <!-- 상세 -->
      <div class="care-main">
        <!-- 종합 점수 -->
        <section class="panel care-overall">
          <div class="co-badge">
            <strong>{{ sel.total }}</strong>
            <span>{{ sel.grade }}</span>
          </div>
          <div class="co-info">
            <h2>{{ sel.name }}</h2>
            <p class="co-headline">🌱 {{ sel.headline }}</p>
            <p class="co-desc">{{ sel.desc }}</p>
          </div>
        </section>

        <!-- 3대 점수 -->
        <div class="score-grid">
          <section v-for="b in blocks" :key="b.key" class="panel score-card">
            <div class="sc-head">
              <span class="sc-label">{{ b.label }} <em>{{ b.weight }}%</em></span>
              <strong class="sc-score" :style="{ color: b.color }">{{ b.score }}</strong>
            </div>
            <div class="sc-track"><div class="sc-fill" :style="{ width: `${b.score}%`, background: b.color }"></div></div>
            <dl class="sc-items">
              <div v-for="it in b.items" :key="it[0]"><dt>{{ it[0] }}</dt><dd>{{ it[1] }}</dd></div>
            </dl>
            <p class="sc-note">🌱 {{ b.note }}</p>
          </section>
        </div>

        <div class="care-grid2">
          <!-- 매매일지 -->
          <section class="panel">
            <div class="panel-head"><div><p class="eyebrow">order ⋈ diary</p><h2>이 종목 매매일지</h2></div></div>
            <div class="care-diary">
              <div v-for="(d, i) in sel.diary" :key="i" class="cd-item">
                <span class="cd-side" :class="d.side === '매수' ? 'buy' : 'sell'">{{ d.side }}</span>
                <span class="cd-date">{{ d.date }}</span>
                <span class="cd-text">{{ d.text }}</span>
              </div>
            </div>
          </section>

          <!-- 점수 히스토리 -->
          <section class="panel">
            <div class="panel-head"><div><p class="eyebrow">Score History</p><h2>장투 점수 히스토리</h2></div></div>
            <div class="hist-rows">
              <div v-for="h in sel.history" :key="h.m" class="hist-row">
                <span class="hist-m">{{ h.m }}</span>
                <div class="hist-track"><div class="hist-fill" :style="{ width: `${(h.s / maxHist) * 100}%` }"></div></div>
                <span class="hist-s">{{ h.s }}점</span>
              </div>
            </div>
          </section>
        </div>

        <!-- 관련 뉴스 -->
        <section class="panel">
          <div class="panel-head"><div><p class="eyebrow">stock_news</p><h2>이 종목 관련 뉴스</h2></div></div>
          <ul class="care-news">
            <li v-for="(n, i) in sel.news" :key="i">
              <span class="cn-title">{{ n[0] }}</span>
              <span class="cn-source">{{ n[1] }}</span>
            </li>
          </ul>
        </section>

        <RouterLink :to="`/stocks/${sel.code}`" class="care-detail-link">종목 상세 보기 →</RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.care-layout { display: grid; grid-template-columns: 240px minmax(0, 1fr); gap: 16px; align-items: start; }

.care-list { display: grid; gap: 8px; }
.care-row {
  display: grid; grid-template-columns: 36px minmax(0, 1fr) auto; align-items: center; gap: 10px;
  padding: 10px; border-radius: var(--radius); background: rgba(255, 255, 255, 0.48);
  border: 1px solid transparent; text-align: left; transition: background 0.16s ease, border-color 0.16s ease;
}
.care-row:hover { background: rgba(255, 255, 255, 0.7); }
.care-row.is-selected { border-color: var(--accent); background: rgba(49, 93, 255, 0.06); }
.care-logo { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 12px; font-weight: 900; }
.care-row-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.care-row-name { color: var(--ink); font-size: 14px; font-weight: 900; }
.care-row-market { color: var(--muted); font-size: 11px; }
.care-row-score { color: var(--accent); font-size: 18px; font-weight: 900; }

.care-main { display: grid; gap: 16px; }

.care-overall { display: flex; align-items: center; gap: 20px; }
.co-badge {
  width: 96px; height: 96px; border-radius: 24px; flex-shrink: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%); color: #fff;
}
.co-badge strong { font-size: 38px; line-height: 1; }
.co-badge span { font-size: 14px; font-weight: 900; opacity: 0.9; }
.co-info h2 { margin: 0; font-size: 22px; }
.co-headline { margin: 4px 0 8px; color: var(--positive); font-size: 14px; font-weight: 900; }
.co-desc { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.55; word-break: keep-all; }

.score-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.sc-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 10px; }
.sc-label { color: var(--ink); font-size: 15px; font-weight: 900; }
.sc-label em { font-style: normal; color: var(--faint); font-size: 12px; margin-left: 4px; }
.sc-score { font-size: 28px; font-weight: 900; }
.sc-track { height: 8px; border-radius: 999px; background: rgba(180, 200, 255, 0.35); overflow: hidden; margin-bottom: 14px; }
.sc-fill { height: 100%; border-radius: 999px; }
.sc-items { display: grid; gap: 8px; margin: 0 0 12px; }
.sc-items > div { display: flex; justify-content: space-between; }
.sc-items dt { color: var(--muted); font-size: 13px; }
.sc-items dd { margin: 0; color: var(--ink); font-size: 13px; font-weight: 900; }
.sc-note { margin: 0; padding-top: 12px; border-top: 1px solid var(--line); color: var(--muted); font-size: 12px; line-height: 1.5; word-break: keep-all; }

.care-grid2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.care-diary { display: grid; gap: 8px; }
.cd-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: var(--radius); background: rgba(255, 255, 255, 0.48); border: 1px solid var(--glass-border); }
.cd-side { padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 900; flex-shrink: 0; }
.cd-side.buy { background: rgba(49, 93, 255, 0.1); color: var(--accent); }
.cd-side.sell { background: rgba(207, 61, 61, 0.1); color: var(--negative); }
.cd-date { color: var(--faint); font-size: 12px; font-weight: 900; flex-shrink: 0; }
.cd-text { color: var(--ink); font-size: 13px; }

.hist-rows { display: grid; gap: 12px; }
.hist-row { display: grid; grid-template-columns: 40px 1fr 48px; align-items: center; gap: 10px; }
.hist-m { color: var(--muted); font-size: 13px; font-weight: 900; }
.hist-track { height: 10px; border-radius: 999px; background: rgba(180, 200, 255, 0.35); overflow: hidden; }
.hist-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, var(--accent), var(--purple)); }
.hist-s { color: var(--ink); font-size: 13px; font-weight: 900; text-align: right; }

.care-news { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; }
.care-news li { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 11px 0; border-bottom: 1px solid var(--line); }
.care-news li:last-child { border-bottom: 0; }
.cn-title { color: var(--ink); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cn-source { color: var(--faint); font-size: 11px; font-weight: 900; flex-shrink: 0; }

.care-detail-link { display: block; text-align: center; padding: 12px; border-radius: var(--radius); background: rgba(49, 93, 255, 0.08); color: var(--accent); font-size: 14px; font-weight: 900; }

@media (max-width: 1080px) {
  .care-layout { grid-template-columns: 1fr; }
  .score-grid { grid-template-columns: 1fr; }
  .care-grid2 { grid-template-columns: 1fr; }
}
</style>
