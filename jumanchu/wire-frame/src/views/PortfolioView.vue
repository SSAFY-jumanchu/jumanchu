<script setup>
import { ref, computed } from 'vue'

// ===== 보유 종목 데이터 =====
const holdings = [
  {
    code: '000660', name: 'SK하이닉스', market: 'KOSPI', sector: '반도체',
    qty: 3, avgPrice: 1950000, currentPrice: 2031000, currency: 'KRW',
    color: '#e94560',
    scores: {
      financial: {
        score: 78,
        items: [
          { label: '부채비율', value: '22.4%', comment: '업종 평균 대비 낮은 수준' },
          { label: 'ROE', value: '26.78%', comment: '높은 자기자본이익률' },
          { label: '영업이익률', value: '32.1%', comment: '전분기 대비 개선 중' },
          { label: '유동비율', value: '198.3%', comment: '단기 유동성 양호' },
        ],
        summary: 'HBM 중심의 고부가 제품 믹스 개선으로 재무 체력이 빠르게 회복되고 있습니다. 부채비율은 업종 내 최저 수준이며 현금성 자산도 충분합니다.',
      },
      growth: {
        score: 92,
        items: [
          { label: 'AI 서버 수요', value: '↑ 급성장', comment: 'HBM3E 수주 확대' },
          { label: '매출 성장률', value: '+48.2%', comment: 'YoY 기준' },
          { label: '신규 제품', value: 'HBM4 개발 중', comment: '2026 Q4 양산 예정' },
          { label: '시장 점유율', value: '36.8%', comment: 'DRAM 글로벌 2위' },
        ],
        summary: 'AI 인프라 확장에 따른 HBM 수요가 급증하고 있으며, 차세대 HBM4 양산 로드맵이 구체화되어 중장기 성장 모멘텀이 매우 강합니다.',
      },
      userfit: {
        score: 87,
        items: [
          { label: '리스크 성향', value: '공격형 ✓', comment: '변동성 높으나 기대수익도 높음' },
          { label: '보유기간', value: '12개월 ✓', comment: '단기 변동성 감내 가능' },
          { label: '선호 섹터', value: '전기전자 ✓', comment: '관심 섹터 일치' },
          { label: '포트비중', value: '38.4%', comment: '집중 투자 주의 필요' },
        ],
        summary: '사용자의 공격형 투자 성향과 반도체 섹터 선호에 매우 잘 맞는 종목입니다. 다만 포트폴리오 비중이 높아 분산 관점에서 모니터링이 필요합니다.',
      },
      total: { score: 86, grade: 'B+', label: '장기 보유 강력 추천', color: '#0066CC' },
    },
  },
  {
    code: '005930', name: '삼성전자', market: 'KOSPI', sector: '전기·전자',
    qty: 10, avgPrice: 309000, currentPrice: 317000, currency: 'KRW',
    color: '#1428A0',
    scores: {
      financial: {
        score: 82,
        items: [
          { label: '부채비율', value: '26.8%', comment: '안정적인 재무 구조' },
          { label: 'ROE', value: '8.57%', comment: '회복세 진입' },
          { label: '영업이익률', value: '14.2%', comment: '전년 대비 개선' },
          { label: '배당수익률', value: '2.1%', comment: '안정적 배당 지속' },
        ],
        summary: '세계 최대 반도체·가전 기업으로 재무 안정성이 높습니다. 최근 실적 회복 추세이며 풍부한 현금 보유로 배당과 투자를 병행하고 있습니다.',
      },
      growth: {
        score: 68,
        items: [
          { label: '파운드리 수주', value: '개선 중', comment: '삼성 2nm 공정 개발 중' },
          { label: '매출 성장률', value: '+12.3%', comment: 'YoY 기준' },
          { label: 'AI 반도체', value: '추격 중', comment: 'HBM3E 양산 개시' },
          { label: '가전 시장', value: '보합세', comment: '프리미엄 중심 전략' },
        ],
        summary: '반도체 업황 개선의 수혜를 받고 있으나 SK하이닉스 대비 HBM 시장 진입이 늦어 단기 성장성은 다소 제한적입니다. 중장기 파운드리 성장이 기대됩니다.',
      },
      userfit: {
        score: 91,
        items: [
          { label: '리스크 성향', value: '균형형 ✓', comment: '안정성과 성장성 균형' },
          { label: '보유기간', value: '12개월 ✓', comment: '중기 보유 적합' },
          { label: '선호 섹터', value: '전기전자 ✓', comment: '1순위 관심 섹터' },
          { label: '포트비중', value: '28.7%', comment: '적정 비중 유지 중' },
        ],
        summary: '균형형 투자 성향과 전기전자 섹터 선호에 완벽하게 부합하는 종목입니다. 배당 안정성과 중장기 성장성을 동시에 추구하는 사용자 목표에 적합합니다.',
      },
      total: { score: 80, grade: 'B+', label: '장기 보유 추천', color: '#0066CC' },
    },
  },
  {
    code: 'NVDA', name: 'NVIDIA', market: 'NASDAQ', sector: '반도체',
    qty: 5, avgPrice: 198.00, currentPrice: 214.25, currency: 'USD',
    color: '#76b900',
    scores: {
      financial: {
        score: 95,
        items: [
          { label: '부채비율', value: '41.2%', comment: '관리 가능 수준' },
          { label: 'ROE', value: '114.29%', comment: '압도적 수익성' },
          { label: '영업이익률', value: '54.7%', comment: '업계 최고 수준' },
          { label: '잉여현금흐름', value: '$26.9B', comment: '최근 12개월' },
        ],
        summary: 'AI GPU 독점적 지위로 압도적인 수익성을 보유합니다. 영업이익률이 54%를 넘어서며 잉여현금흐름도 역대 최대를 기록 중입니다.',
      },
      growth: {
        score: 97,
        items: [
          { label: '데이터센터 매출', value: '+427%', comment: 'YoY 기준' },
          { label: 'Blackwell GPU', value: '출시', comment: '차세대 GPU 수요 폭발' },
          { label: '소프트웨어', value: 'CUDA 독점', comment: '생태계 진입장벽' },
          { label: '자율주행', value: '신사업 확장', comment: '중장기 성장동력' },
        ],
        summary: 'AI 인프라 구축의 핵심 수혜주입니다. 데이터센터 매출이 전년 대비 4배 이상 성장하였으며 CUDA 생태계의 진입장벽이 매우 높습니다.',
      },
      userfit: {
        score: 82,
        items: [
          { label: '리스크 성향', value: '고위험 ⚠', comment: '공격형 이상 권장' },
          { label: '보유기간', value: '12개월 ✓', comment: '장기 보유 시 유리' },
          { label: '선호 섹터', value: '해외주 ✓', comment: '해외 비중 확대 적합' },
          { label: '환율 리스크', value: 'USD', comment: '달러 노출 고려 필요' },
        ],
        summary: '성장성은 최상위이나 PER 40배 이상의 고밸류에이션과 높은 변동성은 유의가 필요합니다. 해외 비중 확대 관점에서 핵심 보유 종목으로 적합합니다.',
      },
      total: { score: 91, grade: 'A', label: '장기 핵심 보유 추천', color: '#0f9f6e' },
    },
  },
  {
    code: 'AAPL', name: 'Apple', market: 'NASDAQ', sector: '소비자가전',
    qty: 8, avgPrice: 295.00, currentPrice: 312.51, currency: 'USD',
    color: '#555',
    scores: {
      financial: {
        score: 88,
        items: [
          { label: '부채비율', value: '67.3%', comment: '자사주 매입으로 증가' },
          { label: 'ROE', value: '141.47%', comment: '자본효율성 극대화' },
          { label: '영업이익률', value: '31.5%', comment: '매우 안정적' },
          { label: '배당+자사주', value: '$29B', comment: '주주환원 최우선' },
        ],
        summary: '압도적인 브랜드 파워와 애플 생태계를 기반으로 안정적인 현금 창출이 지속되고 있습니다. 공격적인 자사주 매입으로 주당 가치를 꾸준히 높이고 있습니다.',
      },
      growth: {
        score: 62,
        items: [
          { label: '서비스 매출', value: '+17.2%', comment: '고마진 사업 확대' },
          { label: 'AI 기능', value: 'Apple Intelligence', comment: 'iOS 탑재 중' },
          { label: '인도 시장', value: '고성장', comment: '새 성장 시장 공략' },
          { label: '하드웨어', value: '포화 시장', comment: '교체 주기 장기화' },
        ],
        summary: '하드웨어 시장 성숙에 따라 성장률이 둔화되고 있으나 서비스 매출이 빠르게 성장하며 이를 보완하고 있습니다. Apple Intelligence를 통한 AI 경쟁력 확보가 관건입니다.',
      },
      userfit: {
        score: 85,
        items: [
          { label: '리스크 성향', value: '균형형 ✓', comment: '방어적 성격의 성장주' },
          { label: '보유기간', value: '12개월+ ✓', comment: '장기 보유 시 유리' },
          { label: '분산 효과', value: '높음', comment: '국내 종목과 상관 낮음' },
          { label: '환율 리스크', value: 'USD', comment: '달러 헤지 고려' },
        ],
        summary: '안정성과 성장성을 겸비한 장기 보유형 종목입니다. 국내 종목과의 상관관계가 낮아 포트폴리오 분산 효과가 뛰어납니다.',
      },
      total: { score: 78, grade: 'B', label: '장기 보유 적합', color: '#0066CC' },
    },
  },
  {
    code: '035420', name: 'NAVER', market: 'KOSPI', sector: 'IT·소프트웨어',
    qty: 12, avgPrice: 261000, currentPrice: 248500, currency: 'KRW',
    color: '#03c75a',
    scores: {
      financial: {
        score: 71,
        items: [
          { label: '부채비율', value: '58.1%', comment: '관리 가능 수준' },
          { label: 'ROE', value: '7.2%', comment: '개선 여지 있음' },
          { label: '영업이익률', value: '11.8%', comment: '광고 경기에 민감' },
          { label: '현금성 자산', value: '2.1조원', comment: '투자 여력 충분' },
        ],
        summary: '국내 최대 포털·검색 기업으로 안정적인 광고 수익 기반을 보유합니다. 커머스·클라우드·AI 사업 확대를 위한 투자가 지속되고 있습니다.',
      },
      growth: {
        score: 65,
        items: [
          { label: 'AI 검색', value: '개발 중', comment: 'Clova X 강화' },
          { label: '커머스', value: '+18.4%', comment: 'YoY 성장 중' },
          { label: '라인야후', value: '분리 위기', comment: '일본 사업 리스크' },
          { label: '클라우드', value: '성장 중', comment: '기업 고객 확대' },
        ],
        summary: 'AI 기반 검색 경쟁이 심화되는 가운데 국내 시장 지위는 견고합니다. 라인야후 분리 이슈와 글로벌 AI 경쟁이 단기 리스크 요인입니다.',
      },
      userfit: {
        score: 76,
        items: [
          { label: '리스크 성향', value: '균형형 ✓', comment: '중위험 IT주' },
          { label: '보유기간', value: '12개월 ✓', comment: '중기 관점 적합' },
          { label: '현재 평가손익', value: '-12,500원', comment: '평균단가 대비 하락' },
          { label: '선호 섹터', value: 'IT 적합', comment: '관심 섹터 포함' },
        ],
        summary: '국내 IT 섹터 대표주로 균형형 투자자에게 적합합니다. 현재 평가손이 발생 중이나 AI 경쟁력 회복 시 반등 기대감이 있습니다.',
      },
      total: { score: 71, grade: 'B', label: '보유 유지, 추가 모니터링', color: '#e58b10' },
    },
  },
]

// ===== 선택 종목 =====
const selectedIdx = ref(0)
const selectedHolding = computed(() => holdings[selectedIdx.value])

// ===== 등급 계산 =====
function getGrade(score) {
  if (score >= 90) return 'A'
  if (score >= 80) return 'B+'
  if (score >= 70) return 'B'
  if (score >= 60) return 'C+'
  if (score >= 50) return 'C'
  return 'D'
}

function getGradeColor(score) {
  if (score >= 85) return 'var(--positive)'
  if (score >= 70) return 'var(--accent)'
  if (score >= 55) return '#e58b10'
  return 'var(--negative)'
}

// ===== 매매일지 =====
const tradeJournal = [
  { date: '2026.06.05', code: '005930', name: '삼성전자', side: 'BUY',  qty: 5,  price: 315000 },
  { date: '2026.06.03', code: '000660', name: 'SK하이닉스', side: 'BUY', qty: 1, price: 2280000 },
  { date: '2026.05.28', code: 'NVDA',   name: 'NVIDIA',    side: 'BUY',  qty: 2,  price: 206.50 },
  { date: '2026.05.20', code: '005930', name: '삼성전자',   side: 'BUY',  qty: 5,  price: 303000 },
  { date: '2026.05.15', code: 'AAPL',   name: 'Apple',     side: 'BUY',  qty: 3,  price: 308.50 },
  { date: '2026.05.10', code: '035420', name: 'NAVER',     side: 'BUY',  qty: 12, price: 261000 },
  { date: '2026.05.07', code: 'AAPL',   name: 'Apple',     side: 'BUY',  qty: 5,  price: 284.00 },
  { date: '2026.04.22', code: 'NVDA',   name: 'NVIDIA',    side: 'BUY',  qty: 3,  price: 192.00 },
  { date: '2026.04.15', code: '000660', name: 'SK하이닉스', side: 'BUY', qty: 2, price: 1930000 },
]

// ===== 총점 히스토리 (8주) =====
const scoreHistory = [
  { week: '4/14', score: 74 },
  { week: '4/21', score: 76 },
  { week: '4/28', score: 73 },
  { week: '5/05', score: 78 },
  { week: '5/12', score: 80 },
  { week: '5/19', score: 79 },
  { week: '5/26', score: 82 },
  { week: '6/02', score: 82 },
]

function buildHistoryPath(data, w, h) {
  const scores = data.map(d => d.score)
  const min = Math.min(...scores) - 5
  const max = Math.max(...scores) + 5
  const range = max - min
  const n = data.length
  const pts = data.map((d, i) => {
    const x = (i / (n - 1)) * w
    const y = h - 16 - ((d.score - min) / range) * (h - 32)
    return { x: x.toFixed(1), y: y.toFixed(1) }
  })
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  const area = `${line} L${w},${h} L0,${h} Z`
  return { line, area, pts }
}

const histPath = computed(() => buildHistoryPath(scoreHistory, 220, 100))

// ===== 종목 관련 뉴스 =====
const stockNews = [
  {
    code: '000660', name: 'SK하이닉스', color: '#e94560',
    headline: 'HBM3E 12단 양산 본격화… NVIDIA Blackwell에 독점 공급',
    source: '한국경제', time: '2시간 전', positive: true,
  },
  {
    code: '005930', name: '삼성전자', color: '#1428A0',
    headline: '삼성전자, 2nm 파운드리 수율 개선 성공… 퀄컴 수주 임박',
    source: '매일경제', time: '4시간 전', positive: true,
  },
  {
    code: 'NVDA', name: 'NVIDIA', color: '#76b900',
    headline: 'Blackwell Ultra 출하 급증… 데이터센터 매출 Q2 가이던스 상향',
    source: 'Bloomberg', time: '6시간 전', positive: true,
  },
  {
    code: 'AAPL', name: 'Apple', color: '#555',
    headline: 'Apple Intelligence 2.0 공개… Siri 완전 재설계로 AI 경쟁력 강화',
    source: 'Reuters', time: '8시간 전', positive: true,
  },
  {
    code: '035420', name: 'NAVER', color: '#03c75a',
    headline: 'NAVER Clova X, 기업 고객 5만 돌파… B2B AI 시장 본격 공략',
    source: '조선일보', time: '1일 전', positive: true,
  },
  {
    code: '000660', name: 'SK하이닉스', color: '#e94560',
    headline: '외국인 투자자 20일 연속 순매도… 단기 변동성 확대 주의',
    source: '연합뉴스', time: '1일 전', positive: false,
  },
  {
    code: '005930', name: '삼성전자', color: '#1428A0',
    headline: '삼성전자 1분기 영업이익 6.7조… 전년비 3배 성장',
    source: '이데일리', time: '2일 전', positive: true,
  },
  {
    code: '035420', name: 'NAVER', color: '#03c75a',
    headline: '라인야후 경영권 분리 압박 지속… NAVER 일본 수익 기여 감소 우려',
    source: '한겨레', time: '2일 전', positive: false,
  },
  {
    code: 'NVDA', name: 'NVIDIA', color: '#76b900',
    headline: '中 수출 규제 완화 기대감에 NVDA 프리마켓 +3.2% 급등',
    source: 'CNBC', time: '3일 전', positive: true,
  },
]

// ===== 포트폴리오 종합 점수 =====
const portfolioAvgScore = computed(() => {
  const scores = holdings.map(h => h.scores.total.score)
  return Math.round(scores.reduce((s, v) => s + v, 0) / scores.length)
})

// ===== 유틸 =====
function fmtPrice(price, currency) {
  const isKrw = currency === 'KRW'
  return isKrw
    ? '₩' + price.toLocaleString('ko-KR')
    : '$' + price.toFixed(2)
}
</script>

<template>
  <div class="portfolio-page">

    <!-- ===== 헤더 ===== -->
    <header class="pt-header">
      <div>
        <p class="eyebrow">Long-term Investment Care</p>
        <h1>장투 케어</h1>
        <p class="pt-subtitle">AI가 보유 종목의 장기투자 적합성을 분석하고 점수를 산출합니다.</p>
      </div>

      <div class="pt-header-right">
        <!-- 포트폴리오 종합 점수 -->
        <div class="portfolio-score-pill">
          <span class="psp-label">포트폴리오 종합 점수</span>
          <strong class="psp-score" :style="{ color: getGradeColor(portfolioAvgScore) }">
            {{ portfolioAvgScore }}점
          </strong>
          <span class="psp-grade" :style="{ color: getGradeColor(portfolioAvgScore) }">
            {{ getGrade(portfolioAvgScore) }}
          </span>
        </div>
        <button class="report-gen-btn">
          <span>✦</span> LLM 리포트 재생성
        </button>
      </div>
    </header>

    <!-- ===== 종목 선택 탭 ===== -->
    <div class="stock-tab-bar">
      <button
        v-for="(h, i) in holdings"
        :key="h.code"
        class="stock-tab"
        :class="{ 'is-active': selectedIdx === i }"
        @click="selectedIdx = i"
      >
        <span class="tab-dot" :style="{ background: h.color }"></span>
        {{ h.name }}
        <span class="tab-score" :style="{ color: getGradeColor(h.scores.total.score) }">
          {{ h.scores.total.score }}
        </span>
      </button>
    </div>

    <!-- ===== 메인 그리드 ===== -->
    <div class="pt-main-grid">

      <!-- ===== 좌: LLM 리포트 ===== -->
      <div class="pt-col-main">

        <!-- 종목 요약 배너 -->
        <div class="stock-summary-banner panel" :style="{ '--h-color': selectedHolding.color }">
          <div class="ssb-info">
            <div class="ssb-dot" :style="{ background: selectedHolding.color }">
              {{ selectedHolding.name.slice(0, 1) }}
            </div>
            <div>
              <h2 class="ssb-name">{{ selectedHolding.name }}</h2>
              <span class="ssb-meta">{{ selectedHolding.market }} · {{ selectedHolding.code }} · {{ selectedHolding.sector }}</span>
            </div>
          </div>
          <div class="ssb-holding">
            <span>보유 {{ selectedHolding.qty }}주</span>
            <span>평균단가 {{ fmtPrice(selectedHolding.avgPrice, selectedHolding.currency) }}</span>
            <span>현재가 {{ fmtPrice(selectedHolding.currentPrice, selectedHolding.currency) }}</span>
            <span
              :class="selectedHolding.currentPrice >= selectedHolding.avgPrice ? 'is-up' : 'is-down'"
            >
              {{ selectedHolding.currentPrice >= selectedHolding.avgPrice ? '▲' : '▼' }}
              {{ Math.abs(((selectedHolding.currentPrice - selectedHolding.avgPrice) / selectedHolding.avgPrice) * 100).toFixed(2) }}%
            </span>
          </div>
          <div class="ssb-llm-badge">
            <span>✦</span> LLM 생성 보고서
          </div>
        </div>

        <!-- ===== 1. 기반 (Financial Score) ===== -->
        <div class="panel score-section">
          <div class="score-section-head">
            <div class="score-label-block">
              <span class="score-num-badge" :style="{ background: getGradeColor(selectedHolding.scores.financial.score) }">
                {{ selectedHolding.scores.financial.score }}
              </span>
              <div>
                <h3>기반 · Financial Score</h3>
                <span class="score-grade-text" :style="{ color: getGradeColor(selectedHolding.scores.financial.score) }">
                  {{ getGrade(selectedHolding.scores.financial.score) }}등급
                </span>
              </div>
            </div>
            <div class="score-bar-wrap">
              <div class="score-bar-track">
                <div
                  class="score-bar-fill"
                  :style="{
                    width: selectedHolding.scores.financial.score + '%',
                    background: getGradeColor(selectedHolding.scores.financial.score)
                  }"
                ></div>
              </div>
              <span class="score-bar-label">100점</span>
            </div>
          </div>

          <div class="score-items-grid">
            <div v-for="item in selectedHolding.scores.financial.items" :key="item.label" class="score-item">
              <span class="si-label">{{ item.label }}</span>
              <strong class="si-value">{{ item.value }}</strong>
              <span class="si-comment">{{ item.comment }}</span>
            </div>
          </div>

          <div class="score-summary-box">
            <span class="ssb-icon">✦</span>
            <p>{{ selectedHolding.scores.financial.summary }}</p>
          </div>
        </div>

        <!-- ===== 2. Growth Score ===== -->
        <div class="panel score-section">
          <div class="score-section-head">
            <div class="score-label-block">
              <span class="score-num-badge" :style="{ background: getGradeColor(selectedHolding.scores.growth.score) }">
                {{ selectedHolding.scores.growth.score }}
              </span>
              <div>
                <h3>성장성 · Growth Score</h3>
                <span class="score-grade-text" :style="{ color: getGradeColor(selectedHolding.scores.growth.score) }">
                  {{ getGrade(selectedHolding.scores.growth.score) }}등급
                </span>
              </div>
            </div>
            <div class="score-bar-wrap">
              <div class="score-bar-track">
                <div
                  class="score-bar-fill"
                  :style="{
                    width: selectedHolding.scores.growth.score + '%',
                    background: getGradeColor(selectedHolding.scores.growth.score)
                  }"
                ></div>
              </div>
              <span class="score-bar-label">100점</span>
            </div>
          </div>

          <div class="score-items-grid">
            <div v-for="item in selectedHolding.scores.growth.items" :key="item.label" class="score-item">
              <span class="si-label">{{ item.label }}</span>
              <strong class="si-value">{{ item.value }}</strong>
              <span class="si-comment">{{ item.comment }}</span>
            </div>
          </div>

          <div class="score-summary-box">
            <span class="ssb-icon">✦</span>
            <p>{{ selectedHolding.scores.growth.summary }}</p>
          </div>
        </div>

        <!-- ===== 3. Userfit Score ===== -->
        <div class="panel score-section">
          <div class="score-section-head">
            <div class="score-label-block">
              <span class="score-num-badge" :style="{ background: getGradeColor(selectedHolding.scores.userfit.score) }">
                {{ selectedHolding.scores.userfit.score }}
              </span>
              <div>
                <h3>적합도 · Userfit Score</h3>
                <span class="score-grade-text" :style="{ color: getGradeColor(selectedHolding.scores.userfit.score) }">
                  {{ getGrade(selectedHolding.scores.userfit.score) }}등급
                </span>
              </div>
            </div>
            <div class="score-bar-wrap">
              <div class="score-bar-track">
                <div
                  class="score-bar-fill"
                  :style="{
                    width: selectedHolding.scores.userfit.score + '%',
                    background: getGradeColor(selectedHolding.scores.userfit.score)
                  }"
                ></div>
              </div>
              <span class="score-bar-label">100점</span>
            </div>
          </div>

          <div class="score-items-grid">
            <div v-for="item in selectedHolding.scores.userfit.items" :key="item.label" class="score-item">
              <span class="si-label">{{ item.label }}</span>
              <strong class="si-value">{{ item.value }}</strong>
              <span class="si-comment">{{ item.comment }}</span>
            </div>
          </div>

          <div class="score-summary-box">
            <span class="ssb-icon">✦</span>
            <p>{{ selectedHolding.scores.userfit.summary }}</p>
          </div>
        </div>

        <!-- ===== 4. 최종 총점 ===== -->
        <div class="panel total-score-section">
          <h3 class="total-score-title">최종 Long-term Score (Total)</h3>

          <div class="total-score-body">
            <!-- 원형 게이지 -->
            <div class="gauge-wrap">
              <svg viewBox="0 0 120 120" class="gauge-svg">
                <!-- 배경 호 -->
                <circle cx="60" cy="60" r="48" fill="none"
                  stroke="rgba(180,200,255,0.25)" stroke-width="10"
                  stroke-dasharray="226 75" stroke-dashoffset="-38"
                  stroke-linecap="round" />
                <!-- 값 호 -->
                <circle cx="60" cy="60" r="48" fill="none"
                  :stroke="selectedHolding.scores.total.color"
                  stroke-width="10"
                  :stroke-dasharray="`${(selectedHolding.scores.total.score / 100) * 226} 301`"
                  stroke-dashoffset="-38"
                  stroke-linecap="round"
                  style="transition: stroke-dasharray 0.6s ease"
                />
                <!-- 중앙 텍스트 -->
                <text x="60" y="52" text-anchor="middle" class="gauge-num" font-size="26" font-weight="900">
                  {{ selectedHolding.scores.total.score }}
                </text>
                <text x="60" y="68" text-anchor="middle" class="gauge-grade" font-size="13" font-weight="900">
                  {{ selectedHolding.scores.total.grade }}등급
                </text>
                <text x="60" y="80" text-anchor="middle" class="gauge-sub" font-size="8">
                  / 100점
                </text>
              </svg>
            </div>

            <!-- 총점 설명 -->
            <div class="total-score-detail">
              <div class="total-score-label"
                :style="{ color: selectedHolding.scores.total.color }">
                {{ selectedHolding.scores.total.label }}
              </div>

              <div class="total-sub-scores">
                <div class="tss-row">
                  <span>기반 (Financial)</span>
                  <div class="tss-bar-track">
                    <div class="tss-bar-fill"
                      :style="{ width: selectedHolding.scores.financial.score + '%', background: getGradeColor(selectedHolding.scores.financial.score) }">
                    </div>
                  </div>
                  <span class="tss-val" :style="{ color: getGradeColor(selectedHolding.scores.financial.score) }">
                    {{ selectedHolding.scores.financial.score }}
                  </span>
                </div>
                <div class="tss-row">
                  <span>성장성 (Growth)</span>
                  <div class="tss-bar-track">
                    <div class="tss-bar-fill"
                      :style="{ width: selectedHolding.scores.growth.score + '%', background: getGradeColor(selectedHolding.scores.growth.score) }">
                    </div>
                  </div>
                  <span class="tss-val" :style="{ color: getGradeColor(selectedHolding.scores.growth.score) }">
                    {{ selectedHolding.scores.growth.score }}
                  </span>
                </div>
                <div class="tss-row">
                  <span>적합도 (Userfit)</span>
                  <div class="tss-bar-track">
                    <div class="tss-bar-fill"
                      :style="{ width: selectedHolding.scores.userfit.score + '%', background: getGradeColor(selectedHolding.scores.userfit.score) }">
                    </div>
                  </div>
                  <span class="tss-val" :style="{ color: getGradeColor(selectedHolding.scores.userfit.score) }">
                    {{ selectedHolding.scores.userfit.score }}
                  </span>
                </div>
              </div>

              <div class="total-llm-note">
                <span>✦</span> LLM API 연결 후 맞춤 종합 의견이 이 곳에 표시됩니다.
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- ===== 우: 매매일지 + 히스토리 ===== -->
      <div class="pt-col-side">

        <!-- 매매일지 -->
        <div class="panel journal-panel">
          <div class="side-panel-head">
            <div>
              <p class="eyebrow">Trade Journal</p>
              <h3>매매일지</h3>
            </div>
            <button class="text-btn">+ 추가</button>
          </div>

          <div class="journal-list">
            <div v-for="(trade, i) in tradeJournal" :key="i" class="journal-row">
              <div class="journal-dot" :class="trade.side === 'BUY' ? 'is-buy' : 'is-sell'"></div>
              <div class="journal-info">
                <div class="journal-top">
                  <strong class="journal-name">{{ trade.name }}</strong>
                  <span class="journal-side" :class="trade.side === 'BUY' ? 'is-buy-text' : 'is-sell-text'">
                    {{ trade.side === 'BUY' ? '매수' : '매도' }}
                  </span>
                </div>
                <div class="journal-detail">
                  <span>{{ trade.qty }}주</span>
                  <span>@{{ trade.price.toLocaleString() }}</span>
                </div>
                <span class="journal-date">{{ trade.date }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 총점 히스토리 -->
        <div class="panel history-panel">
          <div class="side-panel-head">
            <div>
              <p class="eyebrow">Score History</p>
              <h3>총점 히스토리</h3>
            </div>
          </div>

          <!-- 히스토리 라인 차트 -->
          <div class="history-chart-wrap">
            <svg viewBox="0 0 220 100" preserveAspectRatio="none" class="history-svg">
              <defs>
                <linearGradient id="histGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="rgba(49,93,255,0.22)" />
                  <stop offset="100%" stop-color="rgba(49,93,255,0)" />
                </linearGradient>
              </defs>
              <line v-for="y in [25,50,75]" :key="y" x1="0" :y1="y" x2="220" :y2="y"
                stroke="rgba(180,200,255,0.3)" stroke-width="1" />
              <path :d="histPath.area" fill="url(#histGrad)" />
              <path :d="histPath.line" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" />
              <!-- 데이터 포인트 -->
              <circle
                v-for="(pt, i) in histPath.pts"
                :key="i"
                :cx="pt.x"
                :cy="pt.y"
                r="3"
                fill="var(--accent)"
              />
            </svg>
          </div>

          <!-- 주별 점수 -->
          <div class="history-labels">
            <div v-for="item in scoreHistory" :key="item.week" class="history-label-item">
              <span class="hl-week">{{ item.week }}</span>
              <strong class="hl-score" :style="{ color: getGradeColor(item.score) }">{{ item.score }}</strong>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ===== 뉴스 섹션 ===== -->
    <section class="panel news-section">
      <div class="news-section-head">
        <div>
          <p class="eyebrow">Stock News</p>
          <h2>종목 관련 뉴스</h2>
        </div>
        <span class="news-meta">보유 종목 기반 · 실시간 수집</span>
      </div>

      <div class="news-grid">
        <article
          v-for="(news, i) in stockNews"
          :key="i"
          class="news-card"
          :class="{ 'is-negative': !news.positive }"
        >
          <div class="news-card-top">
            <span class="news-badge" :style="{ background: news.color }">{{ news.name }}</span>
            <span class="news-sentiment" :class="news.positive ? 'is-pos' : 'is-neg'">
              {{ news.positive ? '▲ 긍정' : '▼ 부정' }}
            </span>
          </div>
          <p class="news-headline">{{ news.headline }}</p>
          <div class="news-meta-row">
            <span class="news-source">{{ news.source }}</span>
            <span class="news-time">{{ news.time }}</span>
          </div>
        </article>
      </div>
    </section>

  </div>
</template>

<style scoped>
/* ===== 페이지 ===== */
.portfolio-page { display: flex; flex-direction: column; gap: 20px; }

/* ===== 헤더 ===== */
.pt-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.pt-header h1 {
  font-size: clamp(28px, 4vw, 42px);
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -1.5px;
  margin: 4px 0 0;
  line-height: 1;
}

.pt-subtitle { font-size: 14px; font-weight: 700; color: var(--muted); margin: 6px 0 0; }

.pt-header-right { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

.portfolio-score-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.62);
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
}

.psp-label { font-size: 12px; font-weight: 700; color: var(--muted); }
.psp-score { font-size: 24px; font-weight: 900; letter-spacing: -0.5px; }
.psp-grade { font-size: 14px; font-weight: 900; }

.report-gen-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 20px;
  border-radius: 999px;
  border: 0;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(49,93,255,0.3);
  transition: opacity 0.18s, transform 0.18s;
  white-space: nowrap;
}

.report-gen-btn:hover { opacity: 0.88; transform: translateY(-1px); }

/* ===== 종목 탭 ===== */
.stock-tab-bar {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.stock-tab {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.52);
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s, color 0.16s, border-color 0.16s;
}

.stock-tab:hover { background: rgba(255,255,255,0.72); color: var(--ink); }

.stock-tab.is-active {
  background: rgba(255,255,255,0.88);
  color: var(--ink);
  border-color: rgba(49,93,255,0.25);
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.tab-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}

.tab-score {
  font-size: 12px;
  font-weight: 900;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(0,0,0,0.06);
}

/* ===== 메인 그리드 ===== */
.pt-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) 280px;
  gap: 16px;
  align-items: start;
}

.pt-col-main { display: flex; flex-direction: column; gap: 14px; }
.pt-col-side { display: flex; flex-direction: column; gap: 14px; }

/* ===== 종목 배너 ===== */
.stock-summary-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  flex-wrap: wrap;
  border-left: 3px solid var(--h-color, var(--accent));
}

.ssb-info { display: flex; align-items: center; gap: 12px; }

.ssb-dot {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 900; color: #fff;
  flex-shrink: 0;
}

.ssb-name { font-size: 18px; font-weight: 900; color: var(--ink); margin: 0 0 2px; }
.ssb-meta { font-size: 12px; font-weight: 700; color: var(--faint); }

.ssb-holding {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
}

.ssb-llm-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(49,93,255,0.08);
  border: 1px solid rgba(49,93,255,0.2);
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  flex-shrink: 0;
}

/* ===== 점수 섹션 ===== */
.score-section { padding: 18px 20px; }

.score-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.score-label-block { display: flex; align-items: center; gap: 12px; }

.score-num-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px; height: 48px;
  border-radius: 50%;
  color: #fff;
  font-size: 18px;
  font-weight: 900;
  flex-shrink: 0;
}

.score-label-block h3 {
  font-size: 16px;
  font-weight: 900;
  color: var(--ink);
  margin: 0 0 3px;
}

.score-grade-text { font-size: 13px; font-weight: 900; }

.score-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 200px;
  flex: 1;
  max-width: 320px;
}

.score-bar-track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: rgba(0,0,0,0.08);
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.6s ease;
}

.score-bar-label { font-size: 11px; font-weight: 700; color: var(--faint); white-space: nowrap; }

/* 아이템 그리드 */
.score-items-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}

.score-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.42);
  border: 1px solid var(--glass-border);
}

.si-label { font-size: 11px; font-weight: 700; color: var(--faint); }
.si-value { font-size: 15px; font-weight: 900; color: var(--ink); }
.si-comment { font-size: 11px; font-weight: 700; color: var(--muted); }

/* AI 요약 박스 */
.score-summary-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  border-radius: var(--radius);
  background: rgba(49,93,255,0.05);
  border: 1px solid rgba(49,93,255,0.15);
}

.ssb-icon { color: var(--accent); font-size: 14px; flex-shrink: 0; margin-top: 1px; }

.score-summary-box p {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.6;
  word-break: keep-all;
}

/* ===== 총점 섹션 ===== */
.total-score-section { padding: 20px; }

.total-score-title {
  font-size: 16px;
  font-weight: 900;
  color: var(--ink);
  margin: 0 0 18px;
}

.total-score-body {
  display: flex;
  align-items: center;
  gap: 28px;
  flex-wrap: wrap;
}

/* 원형 게이지 */
.gauge-wrap { flex-shrink: 0; }
.gauge-svg { width: 130px; height: 130px; }

.gauge-num { fill: var(--ink); }
.gauge-grade { fill: var(--accent); }
.gauge-sub { fill: var(--faint); }

/* 총점 상세 */
.total-score-detail { flex: 1; min-width: 240px; }

.total-score-label {
  font-size: 18px;
  font-weight: 900;
  margin-bottom: 16px;
}

.total-sub-scores { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }

.tss-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tss-row > span:first-child { font-size: 12px; font-weight: 700; color: var(--muted); width: 120px; flex-shrink: 0; }

.tss-bar-track {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: rgba(0,0,0,0.07);
  overflow: hidden;
}

.tss-bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.5s ease;
}

.tss-val { font-size: 13px; font-weight: 900; width: 28px; text-align: right; flex-shrink: 0; }

.total-llm-note {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: var(--radius);
  background: rgba(49,93,255,0.05);
  border: 1px solid rgba(49,93,255,0.15);
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
}

.total-llm-note span { color: var(--accent); }

/* ===== 사이드: 매매일지 ===== */
.journal-panel { padding: 16px; }

.side-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.side-panel-head h3 { font-size: 14px; font-weight: 900; color: var(--ink); margin: 2px 0 0; }

.text-btn {
  border: 0; background: transparent;
  color: var(--accent); font-size: 12px; font-weight: 900; cursor: pointer;
}

.journal-list { display: flex; flex-direction: column; gap: 2px; }

.journal-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 6px;
  border-radius: var(--radius);
  transition: background 0.14s;
  cursor: pointer;
}

.journal-row:hover { background: rgba(255,255,255,0.48); }

.journal-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}

.journal-dot.is-buy { background: #0066CC; }
.journal-dot.is-sell { background: #FF3B5C; }

.journal-info { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }

.journal-top {
  display: flex;
  align-items: center;
  gap: 6px;
}

.journal-name { font-size: 13px; font-weight: 900; color: var(--ink); }

.journal-side {
  font-size: 10px;
  font-weight: 900;
  padding: 1px 6px;
  border-radius: 999px;
}

.is-buy-text { background: rgba(0,102,204,0.1); color: #0066CC; }
.is-sell-text { background: rgba(255,59,92,0.1); color: #FF3B5C; }

.journal-detail {
  display: flex;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
}

.journal-date { font-size: 10px; font-weight: 700; color: var(--faint); }

/* ===== 사이드: 히스토리 ===== */
.history-panel { padding: 16px; }

.history-chart-wrap {
  height: 100px;
  border-radius: var(--radius);
  overflow: hidden;
  background: rgba(255,255,255,0.28);
  border: 1px solid var(--glass-border);
  margin-bottom: 10px;
}

.history-svg { width: 100%; height: 100%; }

.history-labels {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
}

.history-label-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 5px 4px;
  border-radius: 6px;
  background: rgba(255,255,255,0.38);
}

.hl-week { font-size: 9px; font-weight: 700; color: var(--faint); }
.hl-score { font-size: 13px; font-weight: 900; }

/* ===== 뉴스 섹션 ===== */
.news-section { padding: 20px; }

.news-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.news-section-head h2 {
  font-size: 18px;
  font-weight: 900;
  color: var(--ink);
  margin: 2px 0 0;
}

.news-meta { font-size: 12px; font-weight: 700; color: var(--faint); align-self: flex-end; }

.news-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.news-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.45);
  border: 1px solid var(--glass-border);
  cursor: pointer;
  transition: background 0.16s, transform 0.16s, box-shadow 0.16s;
}

.news-card:hover {
  background: rgba(255,255,255,0.68);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0,0,0,0.08);
}

.news-card.is-negative { border-color: rgba(255,59,92,0.15); }

.news-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.news-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 999px;
  color: #fff;
  font-size: 11px;
  font-weight: 900;
}

.news-sentiment { font-size: 11px; font-weight: 900; }
.news-sentiment.is-pos { color: var(--positive); }
.news-sentiment.is-neg { color: var(--negative); }

.news-headline {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.5;
  word-break: keep-all;
  flex: 1;
}

.news-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.news-source { font-size: 11px; font-weight: 700; color: var(--faint); }
.news-time { font-size: 11px; font-weight: 700; color: var(--faint); }

/* ===== 색상 ===== */
.is-up   { color: var(--positive); }
.is-down { color: var(--negative); }

/* ===== 반응형 ===== */
@media (max-width: 1100px) {
  .pt-main-grid { grid-template-columns: 1fr; }
  .news-grid { grid-template-columns: repeat(2, 1fr); }
  .score-items-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 700px) {
  .news-grid { grid-template-columns: 1fr; }
  .score-items-grid { grid-template-columns: 1fr; }
  .total-score-body { flex-direction: column; align-items: flex-start; }
  .stock-summary-banner { flex-direction: column; align-items: flex-start; }
  .history-labels { grid-template-columns: repeat(4, 1fr); }
}
</style>
