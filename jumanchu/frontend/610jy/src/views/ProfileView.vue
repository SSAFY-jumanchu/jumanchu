<script setup>
import { ref, computed } from 'vue'

// ── 마이페이지 (와이어프레임-마이페이지.pptx 기준) ───────────────────────────
// 백엔드 매핑 메모는 610jy/백엔드_격차_검토메모.md 참고 (팔로우/배당·이자/휴대폰·주소/
// 3축 성향점수/채우기·환전 등은 현재 백엔드에 없음 — 와이어프레임 표현용 목업)

const activeTab = ref('profile') // profile | activity

const user = {
  name: '김주만',
  nickname: '열정적인얼룩말37',
  email: 'kimjuman@example.com',
  phone: '010-1234-5678',
  birth: '1998.07.22',
  address: '서울특별시 강남구 테헤란로 123',
  joined: '2024.03.15',
  posts: 12,
  followers: 47,
  following: 31,
  likesReceived: 294,
  comments: 38,
}

// 기본계좌 · 주식
const account = {
  balance: 10532800,
  orderable: 1247800,
  krw: 1247800,
  usd: 6570.22,
  usdInKrw: 9089899,
  totalInvested: 9285000,
}

// 이달 수익
const monthlyProfit = {
  total: 318400,
  rate: 3.43,
  sale: 110500,
  dividend: 24800,
  interest: 3200,
}

// 월별 수익분석
const monthlyReturns = [
  { label: '1월', rate: 4.2 },
  { label: '2월', rate: -1.8 },
  { label: '3월', rate: 7.1 },
  { label: '4월', rate: 3.5 },
  { label: '5월', rate: 9.3 },
  { label: '6월', rate: 3.4 },
]
const maxAbsReturn = Math.max(...monthlyReturns.map((m) => Math.abs(m.rate)))

// 보유 종목 현황
const holdings = [
  { name: '삼성전자', qty: 20, rate: 2.1, color: '#315dff' },
  { name: 'SK하이닉스', qty: 10, rate: 2.1, color: '#7d4ee8' },
  { name: 'NVIDIA', qty: 3, rate: 2.7, color: '#0f9f6e' },
  { name: 'NAVER', qty: 8, rate: -2.9, color: '#e58b10' },
  { name: 'APPLE', qty: 2, rate: 5.2, color: '#38bdf8' },
]

// 투자 성향
const riskProfile = {
  type: '안정성장형',
  desc: '안정성을 추구하면서 꾸준한 성장을 원하는 투자 유형이에요. 배당주와 우량 성장주를 균형 있게 담는 것을 권장해요.',
  axes: [
    { label: '안정성', value: 62, color: '#315dff' },
    { label: '성장성', value: 78, color: '#7d4ee8' },
    { label: '리스크허용', value: 45, color: '#0f9f6e' },
  ],
}

// 거래 내역
const tradeFilters = [
  { key: 'ALL', label: '전체' },
  { key: 'BUY', label: '매수' },
  { key: 'SELL', label: '매도' },
]
const activeTrade = ref('ALL')
const trades = [
  { date: '2026.06.05', name: '삼성전자', code: '005930', side: 'BUY', qty: 20, price: 317000, total: 6340000, pnl: null },
  { date: '2026.06.04', name: 'SK하이닉스', code: '000660', side: 'SELL', qty: 5, price: 243000, total: 1215000, pnl: 87500 },
  { date: '2026.06.03', name: 'NVIDIA', code: 'NVDA', side: 'BUY', qty: 3, price: 1285000, total: 3855000, pnl: null },
  { date: '2026.06.02', name: '삼성전자', code: '005930', side: 'SELL', qty: 10, price: 312000, total: 3120000, pnl: -35000 },
  { date: '2026.05.30', name: 'NAVER', code: '035420', side: 'BUY', qty: 8, price: 189500, total: 1516000, pnl: null },
  { date: '2026.05.28', name: 'APPLE', code: 'AAPL', side: 'BUY', qty: 2, price: 248000, total: 496000, pnl: null },
  { date: '2026.05.25', name: 'SK하이닉스', code: '000660', side: 'BUY', qty: 10, price: 238000, total: 2380000, pnl: null },
  { date: '2026.05.22', name: '삼성전자', code: '005930', side: 'SELL', qty: 15, price: 308000, total: 4620000, pnl: 120000 },
  { date: '2026.05.20', name: '카카오', code: '035720', side: 'SELL', qty: 20, price: 47500, total: 950000, pnl: -62000 },
  { date: '2026.05.15', name: 'ALPHABET', code: 'GOOGL', side: 'BUY', qty: 1, price: 2180000, total: 2180000, pnl: null },
]
const filteredTrades = computed(() =>
  activeTrade.value === 'ALL' ? trades : trades.filter((t) => t.side === activeTrade.value),
)
const tradeSummary = {
  totalBuy: 16767000,
  totalSell: 9905000,
  realizedPnl: 110500,
  count: 10,
}

// 작성한 글
const myPosts = [
  { type: '질문', title: '삼성전자 지금 매수 타이밍 맞나요?', likes: 24, comments: 8, time: '2시간 전' },
  { type: '후기', title: '2025 상반기 포트폴리오 리뷰 — 수익률 +18.3% 달성 후기', likes: 67, comments: 22, time: '3일 전' },
  { type: '분석', title: 'NAVER vs 카카오 — 하반기 반등 가능성 비교', likes: 41, comments: 15, time: '2주 전' },
  { type: '공유', title: '주린이가 처음 1년 동안 배운 것들', likes: 132, comments: 44, time: '1달 전' },
]

// 최근 활동
const recentActivity = [
  { kind: 'post', text: '삼성전자 지금 매수 타이밍 맞나요? 제 생각엔...', time: '2시간 전', likes: 24, comments: 8 },
  { kind: 'comment', text: '“NVIDIA 실적 발표 분석”에 댓글: "좋은 분석이네요. 저도 비슷한 생각이에요"', time: '5시간 전', likes: 3, comments: null },
  { kind: 'like', text: '“고배당주 포트폴리오 구성 전략” 글을 좋아요', time: '어제', likes: null, comments: null },
  { kind: 'post', text: '2025 상반기 포트폴리오 리뷰 — 수익률 +18.3% 달성 후기', time: '3일 전', likes: 67, comments: 22 },
  { kind: 'comment', text: '“달러 환율 전망”에 댓글: "환율 리스크 헷징은 어떻게 하시나요?"', time: '4일 전', likes: 7, comments: null },
  { kind: 'like', text: '“SK하이닉스 HBM 수요 전망” 글을 좋아요', time: '5일 전', likes: null, comments: null },
]
const activityIcons = { post: '✏️', comment: '💬', like: '❤️' }

function won(n) {
  return `${Math.round(n).toLocaleString('ko-KR')}원`
}
function signed(n) {
  const s = n > 0 ? '+' : ''
  return `${s}${Math.round(n).toLocaleString('ko-KR')}`
}
function signClass(n) {
  return n > 0 ? 'is-up' : n < 0 ? 'is-down' : 'is-flat'
}
</script>

<template>
  <div>
    <!-- 프로필 헤더 -->
    <section class="panel profile-header">
      <div class="ph-left">
        <div class="ph-avatar">{{ user.name.charAt(0) }}</div>
        <div class="ph-info">
          <h1 class="ph-name">{{ user.name }}</h1>
          <p class="ph-handle">@{{ user.nickname }}</p>
          <div class="ph-stats">
            <span><strong>{{ user.posts }}</strong> 글</span>
            <span><strong>{{ user.followers }}</strong> 팔로워</span>
            <span><strong>{{ user.following }}</strong> 팔로잉</span>
          </div>
        </div>
      </div>
      <div class="ph-right">
        <div class="ph-badges">
          <span class="ph-badge" title="새싹 투자자">🌱</span>
          <span class="ph-badge" title="수익 달성">📈</span>
          <span class="ph-badge" title="열정 멤버">🔥</span>
        </div>
        <button class="ph-btn ghost" type="button">프로필 편집</button>
        <button class="ph-btn" type="button">내 계좌</button>
      </div>
    </section>

    <!-- 탭 -->
    <div class="segmented profile-tabs" aria-label="마이페이지 탭">
      <button type="button" :class="{ 'is-selected': activeTab === 'profile' }" @click="activeTab = 'profile'">내 투자 프로필</button>
      <button type="button" :class="{ 'is-selected': activeTab === 'activity' }" @click="activeTab = 'activity'">활동 내역</button>
    </div>

    <!-- ============ 탭 1: 내 투자 프로필 ============ -->
    <div v-if="activeTab === 'profile'">
      <!-- 계좌 요약 3카드 -->
      <div class="account-grid">
        <section class="panel acct-card">
          <p class="eyebrow">기본계좌 · 주식</p>
          <strong class="acct-balance">{{ won(account.balance) }}</strong>
          <div class="acct-actions">
            <button type="button" class="acct-action primary">채우기</button>
            <button type="button" class="acct-action">보내기</button>
            <button type="button" class="acct-action">환전</button>
          </div>
          <dl class="acct-list">
            <div><dt>총 주문 가능 금액</dt><dd>{{ won(account.orderable) }}</dd></div>
            <div class="sub"><dt>KR 원화</dt><dd>{{ won(account.krw) }}</dd></div>
            <div class="sub"><dt>US 달러</dt><dd>${{ account.usd.toLocaleString('en-US') }} ≈ {{ won(account.usdInKrw) }}</dd></div>
            <div><dt>총 투자 금액</dt><dd>{{ won(account.totalInvested) }}</dd></div>
          </dl>
        </section>

        <section class="panel acct-card">
          <p class="eyebrow">이달 수익</p>
          <strong class="acct-profit is-up">{{ signed(monthlyProfit.total) }}원</strong>
          <span class="acct-profit-rate is-up">+{{ monthlyProfit.rate }}%</span>
          <dl class="acct-list">
            <div><dt>판매수익</dt><dd class="is-up">{{ signed(monthlyProfit.sale) }}원</dd></div>
            <div><dt>배당금</dt><dd>{{ won(monthlyProfit.dividend) }}</dd></div>
            <div><dt>이자</dt><dd>{{ won(monthlyProfit.interest) }}</dd></div>
          </dl>
        </section>

        <section class="panel acct-card">
          <p class="eyebrow">보유 종목 현황</p>
          <ul class="holding-list">
            <li v-for="h in holdings" :key="h.name">
              <span class="holding-dot" :style="{ background: h.color }"></span>
              <span class="holding-name">{{ h.name }}</span>
              <span class="holding-qty">{{ h.qty }}주</span>
              <span class="holding-rate" :class="signClass(h.rate)">{{ h.rate > 0 ? '+' : '' }}{{ h.rate }}%</span>
            </li>
          </ul>
        </section>
      </div>

      <!-- 수익분석 + 투자성향 -->
      <div class="analysis-grid">
        <section class="panel">
          <div class="panel-head"><div><p class="eyebrow">Performance</p><h2>수익분석</h2></div></div>
          <div class="bar-chart">
            <div v-for="m in monthlyReturns" :key="m.label" class="bar-col">
              <span class="bar-val" :class="signClass(m.rate)">{{ m.rate > 0 ? '+' : '' }}{{ m.rate }}%</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :class="signClass(m.rate)"
                  :style="{ height: `${(Math.abs(m.rate) / maxAbsReturn) * 100}%` }"
                ></div>
              </div>
              <span class="bar-label">{{ m.label }}</span>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><div><p class="eyebrow">Risk Profile</p><h2>투자 성향</h2></div></div>
          <span class="risk-type-pill">{{ riskProfile.type }}</span>
          <p class="risk-desc">{{ riskProfile.desc }}</p>
          <div class="risk-axes">
            <div v-for="a in riskProfile.axes" :key="a.label" class="risk-axis">
              <span class="risk-axis-label">{{ a.label }}</span>
              <div class="risk-axis-track">
                <div class="risk-axis-fill" :style="{ width: `${a.value}%`, background: a.color }"></div>
              </div>
              <span class="risk-axis-val">{{ a.value }}</span>
            </div>
          </div>
          <button type="button" class="risk-retest">투자 성향 재검사</button>
        </section>
      </div>

      <!-- 거래 내역 -->
      <section class="panel trade-history">
        <div class="panel-head">
          <div><p class="eyebrow">Transactions</p><h2>내 거래 내역</h2></div>
          <div class="segmented" aria-label="거래 구분 필터">
            <button
              v-for="f in tradeFilters"
              :key="f.key"
              type="button"
              :class="{ 'is-selected': activeTrade === f.key }"
              @click="activeTrade = f.key"
            >{{ f.label }}</button>
          </div>
        </div>

        <div class="trade-table-wrap">
          <table class="trade-table">
            <thead>
              <tr>
                <th>날짜</th><th>종목</th><th>구분</th>
                <th class="num">수량</th><th class="num">체결 단가</th>
                <th class="num">총 금액</th><th class="num">손익</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(t, i) in filteredTrades" :key="i">
                <td class="t-date">{{ t.date }}</td>
                <td><span class="t-name">{{ t.name }}</span><span class="t-code">{{ t.code }}</span></td>
                <td><span class="t-side" :class="t.side === 'BUY' ? 'side-buy' : 'side-sell'">{{ t.side === 'BUY' ? '매수' : '매도' }}</span></td>
                <td class="num">{{ t.qty }}주</td>
                <td class="num">{{ won(t.price) }}</td>
                <td class="num">{{ won(t.total) }}</td>
                <td class="num" :class="t.pnl === null ? '' : signClass(t.pnl)">
                  {{ t.pnl === null ? '—' : `${signed(t.pnl)}원` }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="trade-summary">
          <div><span>총 매수 금액</span><strong>{{ won(tradeSummary.totalBuy) }}</strong></div>
          <div><span>총 매도 금액</span><strong>{{ won(tradeSummary.totalSell) }}</strong></div>
          <div><span>실현 손익</span><strong class="is-up">{{ signed(tradeSummary.realizedPnl) }}원</strong></div>
          <div><span>총 거래 횟수</span><strong>{{ tradeSummary.count }}회</strong></div>
        </div>
        <p class="fine-print">실현 손익 = (매도 체결가 − 매도 시점 평균매입가) × 매도수량</p>
      </section>
    </div>

    <!-- ============ 탭 2: 활동 내역 ============ -->
    <div v-else>
      <div class="activity-grid">
        <!-- 커뮤니티 프로필 -->
        <section class="panel">
          <p class="eyebrow">커뮤니티 프로필</p>
          <div class="cp-row">
            <div class="cp-avatar">{{ user.name.charAt(0) }}</div>
            <div>
              <h2 class="cp-name">{{ user.nickname }}</h2>
              <p class="cp-meta">주만추 멤버 · {{ user.joined }} 가입</p>
              <div class="cp-stats">
                <span>글 <strong>{{ user.posts }}</strong></span>
                <span>팔로워 <strong>{{ user.followers }}</strong></span>
                <span>팔로잉 <strong>{{ user.following }}</strong></span>
                <span>받은 좋아요 <strong>{{ user.likesReceived }}</strong></span>
              </div>
            </div>
          </div>
        </section>

        <!-- 활동 통계 -->
        <section class="panel">
          <p class="eyebrow">활동 통계</p>
          <dl class="stat-list">
            <div><dt>총 게시글</dt><dd>{{ user.posts }}개</dd></div>
            <div><dt>총 댓글</dt><dd>{{ user.comments }}개</dd></div>
            <div><dt>받은 좋아요</dt><dd>{{ user.likesReceived }}개</dd></div>
            <div><dt>팔로워</dt><dd>{{ user.followers }}명</dd></div>
            <div><dt>팔로잉</dt><dd>{{ user.following }}명</dd></div>
          </dl>
        </section>
      </div>

      <!-- 기본 정보 -->
      <section class="panel">
        <div class="panel-head"><div><p class="eyebrow">Account Info</p><h2>기본 정보</h2></div></div>
        <dl class="info-list">
          <div><dt>이름</dt><dd>{{ user.name }}</dd></div>
          <div><dt>닉네임</dt><dd>{{ user.nickname }}</dd></div>
          <div><dt>이메일</dt><dd>{{ user.email }}</dd></div>
          <div><dt>휴대폰</dt><dd>{{ user.phone }}</dd></div>
          <div><dt>생년월일</dt><dd>{{ user.birth }}</dd></div>
          <div><dt>주소</dt><dd>{{ user.address }}</dd></div>
          <div><dt>가입일</dt><dd>{{ user.joined }}</dd></div>
        </dl>
      </section>

      <!-- 내 활동 내역 -->
      <div class="activity-grid">
        <section class="panel">
          <div class="panel-head"><div><p class="eyebrow">My Posts</p><h2>작성한 글 ({{ myPosts.length }})</h2></div></div>
          <div class="mypost-list">
            <article v-for="(p, i) in myPosts" :key="i" class="mypost-item">
              <span class="mypost-type">{{ p.type }}</span>
              <span class="mypost-title">{{ p.title }}</span>
              <span class="mypost-stats">♥ {{ p.likes }} 💬 {{ p.comments }} · {{ p.time }}</span>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="panel-head"><div><p class="eyebrow">Recent</p><h2>최근 활동</h2></div></div>
          <ul class="feed-list">
            <li v-for="(a, i) in recentActivity" :key="i" class="feed-item">
              <span class="feed-icon">{{ activityIcons[a.kind] }}</span>
              <div class="feed-body">
                <p class="feed-text">{{ a.text }}</p>
                <span class="feed-time">{{ a.time }}</span>
              </div>
              <span v-if="a.likes !== null" class="feed-stats">
                ♥ {{ a.likes }}<template v-if="a.comments !== null"> 💬 {{ a.comments }}</template>
              </span>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.is-up { color: var(--positive); }
.is-down { color: var(--negative); }
.is-flat { color: var(--muted); }

/* ── 헤더 ── */
.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.ph-left { display: flex; align-items: center; gap: 16px; }

.ph-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 900;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(49, 93, 255, 0.3);
}

.ph-name { margin: 0; font-size: 22px; color: var(--ink); }
.ph-handle { margin: 2px 0 8px; color: var(--muted); font-size: 13px; }
.ph-stats { display: flex; gap: 16px; color: var(--muted); font-size: 13px; }
.ph-stats strong { color: var(--ink); }

.ph-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.ph-badges { display: flex; gap: 6px; margin-right: 4px; }
.ph-badge {
  width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--glass-border);
  font-size: 16px;
}
.ph-btn {
  min-height: 38px; padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #fff;
  font-size: 13px; font-weight: 900;
  transition: opacity 0.18s ease;
}
.ph-btn:hover { opacity: 0.88; }
.ph-btn.ghost {
  background: rgba(49, 93, 255, 0.08);
  color: var(--accent);
}

/* ── 탭 ── */
.profile-tabs { margin-bottom: 16px; }

/* ── 계좌 3카드 ── */
.account-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.acct-card { display: flex; flex-direction: column; }
.acct-balance { font-size: 26px; color: var(--ink); margin: 6px 0 12px; letter-spacing: -0.5px; }
.acct-profit { font-size: 26px; margin: 6px 0 2px; letter-spacing: -0.5px; }
.acct-profit-rate { font-size: 14px; font-weight: 900; margin-bottom: 12px; }

.acct-actions { display: flex; gap: 8px; margin-bottom: 14px; }
.acct-action {
  flex: 1; min-height: 36px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.5);
  color: var(--muted); font-size: 13px; font-weight: 900;
  transition: background 0.18s ease;
}
.acct-action:hover { background: rgba(255, 255, 255, 0.75); }
.acct-action.primary { background: rgba(49, 93, 255, 0.1); border-color: rgba(49, 93, 255, 0.3); color: var(--accent); }

.acct-list { display: grid; gap: 8px; margin: 0; }
.acct-list > div { display: flex; justify-content: space-between; gap: 10px; }
.acct-list dt { color: var(--muted); font-size: 13px; }
.acct-list dd { margin: 0; color: var(--ink); font-size: 13px; font-weight: 900; }
.acct-list .sub dt { padding-left: 12px; color: var(--faint); font-size: 12px; }
.acct-list .sub dd { color: var(--muted); font-weight: 700; }

.holding-list { display: grid; gap: 12px; margin: 6px 0 0; padding: 0; list-style: none; }
.holding-list li { display: flex; align-items: center; gap: 8px; }
.holding-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.holding-name { color: var(--ink); font-size: 14px; font-weight: 900; }
.holding-qty { margin-left: auto; color: var(--muted); font-size: 13px; }
.holding-rate { font-size: 13px; font-weight: 900; min-width: 48px; text-align: right; }

/* ── 수익분석 + 성향 ── */
.analysis-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.bar-chart {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
  align-items: end;
  height: 200px;
  padding-top: 10px;
}
.bar-col { display: flex; flex-direction: column; align-items: center; gap: 6px; height: 100%; justify-content: flex-end; }
.bar-val { font-size: 12px; font-weight: 900; }
.bar-track { width: 60%; flex: 1; display: flex; align-items: flex-end; }
.bar-fill { width: 100%; border-radius: 6px 6px 0 0; min-height: 4px; }
.bar-fill.is-up { background: var(--positive); }
.bar-fill.is-down { background: var(--negative); }
.bar-label { color: var(--muted); font-size: 12px; font-weight: 900; }

.risk-type-pill {
  display: inline-flex; align-items: center;
  padding: 6px 16px; border-radius: 999px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff; font-size: 14px; font-weight: 900;
  margin-bottom: 12px;
}
.risk-desc { margin: 0 0 16px; color: var(--muted); font-size: 13px; line-height: 1.55; word-break: keep-all; }
.risk-axes { display: grid; gap: 12px; margin-bottom: 16px; }
.risk-axis { display: grid; grid-template-columns: 70px 1fr 32px; align-items: center; gap: 10px; }
.risk-axis-label { color: var(--muted); font-size: 13px; font-weight: 900; }
.risk-axis-track { height: 8px; border-radius: 999px; background: rgba(180, 200, 255, 0.35); overflow: hidden; }
.risk-axis-fill { height: 100%; border-radius: 999px; }
.risk-axis-val { color: var(--ink); font-size: 13px; font-weight: 900; text-align: right; }
.risk-retest {
  width: 100%; min-height: 42px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.5);
  color: var(--ink); font-size: 14px; font-weight: 900;
  transition: background 0.18s ease;
}
.risk-retest:hover { background: rgba(255, 255, 255, 0.75); }

/* ── 거래 내역 테이블 ── */
.trade-table-wrap { overflow-x: auto; }
.trade-table { width: 100%; border-collapse: collapse; }
.trade-table th {
  text-align: left; padding: 10px 12px;
  color: var(--muted); font-size: 12px; font-weight: 900;
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
.trade-table th.num, .trade-table td.num { text-align: right; }
.trade-table td { padding: 12px; border-bottom: 1px solid var(--line); font-size: 13px; color: var(--ink); white-space: nowrap; }
.t-date { color: var(--muted); }
.t-name { font-weight: 900; }
.t-code { display: block; color: var(--faint); font-size: 11px; }
.t-side { padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 900; }
.side-buy { background: rgba(49, 93, 255, 0.1); color: var(--accent); }
.side-sell { background: rgba(207, 61, 61, 0.1); color: var(--negative); }

.trade-summary {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
  margin-top: 16px; border-radius: var(--radius); overflow: hidden;
  background: rgba(180, 200, 255, 0.3); border: 1px solid var(--glass-border);
}
.trade-summary > div {
  background: rgba(255, 255, 255, 0.55);
  padding: 14px; display: flex; flex-direction: column; gap: 4px;
}
.trade-summary span { color: var(--muted); font-size: 12px; font-weight: 900; }
.trade-summary strong { color: var(--ink); font-size: 16px; }
.fine-print { margin: 10px 0 0; color: var(--faint); font-size: 12px; }

/* ── 활동 내역 ── */
.activity-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.cp-row { display: flex; gap: 14px; align-items: center; }
.cp-avatar {
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 20px; font-weight: 900; flex-shrink: 0;
}
.cp-name { margin: 0; font-size: 17px; color: var(--ink); }
.cp-meta { margin: 2px 0 8px; color: var(--muted); font-size: 12px; }
.cp-stats { display: flex; flex-wrap: wrap; gap: 12px; color: var(--muted); font-size: 12px; }
.cp-stats strong { color: var(--ink); }

.stat-list { display: grid; gap: 10px; margin: 6px 0 0; }
.stat-list > div { display: flex; justify-content: space-between; }
.stat-list dt { color: var(--muted); font-size: 13px; }
.stat-list dd { margin: 0; color: var(--ink); font-size: 14px; font-weight: 900; }

.info-list { display: grid; gap: 0; margin: 0; }
.info-list > div { display: grid; grid-template-columns: 100px 1fr; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line); }
.info-list > div:last-child { border-bottom: 0; }
.info-list dt { color: var(--muted); font-size: 13px; font-weight: 900; }
.info-list dd { margin: 0; color: var(--ink); font-size: 14px; font-weight: 900; }

.mypost-list { display: grid; gap: 10px; }
.mypost-item { display: flex; align-items: center; gap: 10px; padding: 12px; border-radius: var(--radius); background: rgba(255, 255, 255, 0.48); border: 1px solid var(--glass-border); }
.mypost-type { padding: 2px 9px; border-radius: 999px; background: rgba(49, 93, 255, 0.1); color: var(--accent); font-size: 11px; font-weight: 900; flex-shrink: 0; }
.mypost-title { flex: 1; color: var(--ink); font-size: 13px; font-weight: 900; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mypost-stats { color: var(--faint); font-size: 12px; font-weight: 900; flex-shrink: 0; }

.feed-list { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; }
.feed-item { display: flex; gap: 12px; align-items: flex-start; padding: 12px 0; border-bottom: 1px solid var(--line); }
.feed-item:last-child { border-bottom: 0; }
.feed-icon { font-size: 16px; flex-shrink: 0; }
.feed-body { flex: 1; min-width: 0; }
.feed-text { margin: 0 0 3px; color: var(--text); font-size: 13px; line-height: 1.5; word-break: keep-all; }
.feed-time { color: var(--faint); font-size: 12px; }
.feed-stats { color: var(--negative); font-size: 12px; font-weight: 900; flex-shrink: 0; white-space: nowrap; }

@media (max-width: 1080px) {
  .account-grid, .analysis-grid, .activity-grid { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .trade-summary { grid-template-columns: repeat(2, 1fr); }
}
</style>
