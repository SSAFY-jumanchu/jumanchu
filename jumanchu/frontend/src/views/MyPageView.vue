<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { me as fetchMe, updateMe } from '../api/auth'
import { fetchPortfolioSummary, fetchOrders, fetchHoldings, fetchMilestones } from '../api/portfolio'
import { fetchPosts, fetchFollowers, fetchFollowing } from '../api/community'
import { errMsg, retry } from '../api/client'

const router = useRouter()
const activeSection = ref('invest')

// BE UserSerializer는 nickname/email/birth_year/date_joined/profile만 제공(name·phone·address 필드 없음).
const user = reactive({
  id: null,
  nickname: '',
  email: '',
  birthYear: '',
  investType: '',
  joinDate: '',
  posts: 0,
  followers: 0,
  following: 0,
})

// 아바타 이니셜 — 닉네임 첫 글자(하드코딩 '김' 제거)
const avatarChar = computed(() => (user.nickname || '?').slice(0, 1))
// 받은 좋아요 — 내 글들의 like_count 합(하드코딩 294 제거)
const likesReceived = computed(() => myPosts.value.reduce((a, p) => a + (p.likes || 0), 0))

// 현재 자산 마일스톤 — 달성한 목표 뱃지 (GET /portfolio/milestones/, 하드코딩 아이콘 제거)
const milestones = ref([])
async function loadMilestones() {
  try {
    const d = await fetchMilestones()
    milestones.value = (d.achieved || []).map((g) => ({ icon: g.icon, name: g.name }))
  } catch {
    // 실패 → 빈 목록
  }
}

// 활동 내역: 본인이 작성한 글(GET /posts/?mine=true) — 하드코딩 목업 제거.
const CAT_LABEL = { QUESTION: '질문', REVIEW: '후기', ANALYSIS: '분석', SHARE: '공유' }
const myPosts = ref([])
function relTime(iso) {
  if (!iso) return ''
  const diff = Math.max(0, Date.now() - new Date(iso).getTime())
  const m = Math.floor(diff / 60000)
  if (m < 1) return '방금'
  if (m < 60) return `${m}분 전`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}시간 전`
  return `${Math.floor(h / 24)}일 전`
}
function mapPost(p) {
  return {
    id: p.id,
    category: CAT_LABEL[p.category] || p.category,
    title: p.title,
    likes: p.like_count,
    comments: p.comment_count,
    time: relTime(p.created_at),
  }
}

// 통화 헬퍼 — KRW=국내(원), 그 외=해외($)
const isKR = (cur) => cur === 'KRW'
const curUnit = (cur) => (isKR(cur) ? '원' : '$')

// 매매 내역(실데이터: GET /orders/) — 목업 fallback 제거(실패/빈응답 시 가짜 노출 방지)
const trades = ref([])
const tradesError = ref('')
const tradeFilter = ref('all')
const filteredTrades = computed(() => {
  if (tradeFilter.value === 'all') return trades.value
  return trades.value.filter(t => t.side === tradeFilter.value)
})
const domesticTrades = computed(() => filteredTrades.value.filter(t => isKR(t.currency)))
const overseasTrades = computed(() => filteredTrades.value.filter(t => !isKR(t.currency)))

// 계좌 요약 — 전부 BE GET /portfolio/ 제공값(하드코딩 제거)
const account = reactive({
  balance: 0,        // 예수금(현금성자산)
  totalInvested: 0,  // 매수 총액
  totalValue: 0,     // 현재 평가액
  totalAssets: 0,    // 총자산(예수금 + 주식 평가액)
  profitLoss: 0,     // 총손익
  profitRate: 0,     // 총손익률(%)
})
// 실현 손익 합계(음수 가능) — 리터럴 '+' 이중부호 방지용
const realizedPnl = computed(() => trades.value.filter(t => t.pnl !== null).reduce((a, t) => a + t.pnl, 0))

// 보유 목록(BE GET /portfolio/holdings/) — 국내/해외 분리, 목업 fallback 제거
const holdings = ref([])
const domesticHoldings = computed(() => holdings.value.filter(h => isKR(h.currency)))
const overseasHoldings = computed(() => holdings.value.filter(h => !isKR(h.currency)))

const tabs = [
  { key: 'invest',  label: '내 투자' },
  { key: 'profile', label: '프로필' },
  { key: 'activity',label: '활동 내역' },
]

// 활동 내역 글 제목 클릭 → 커뮤니티의 해당 글로 이동
function goPost(id) {
  router.push({ path: '/community', query: { post: id } })
}

function fmt(n) {
  return n.toLocaleString('ko-KR')
}
function signedFmt(n) {
  return (n >= 0 ? '+' : '') + n.toLocaleString('ko-KR')
}
// 계좌 합계는 모두 원화 — 해외 환산분 소수점 제거(정수 표시). USD가 섞이는 거래내역은 fmt/signedFmt 유지.
function fmtKrw(n) {
  return Math.round(n).toLocaleString('ko-KR')
}
function signedFmtKrw(n) {
  return (n >= 0 ? '+' : '') + Math.round(n).toLocaleString('ko-KR')
}

const isEditingInfo = ref(false)
const profileError = ref('')

const HOLD_PALETTE = ['#315dff', '#7d4ee8', '#22c55e', '#f59e0b', '#06b6d4', '#ec4899']
function holdColor(code) {
  let h = 0
  for (const ch of String(code)) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return HOLD_PALETTE[h % HOLD_PALETTE.length]
}

// 내 정보 (GET /auth/me/)
async function loadMe() {
  try {
    const { user: u } = await fetchMe()
    user.id = u.id
    user.nickname = u.nickname
    user.email = u.email
    user.birthYear = String(u.birth_year ?? '')
    user.joinDate = (u.date_joined || '').slice(0, 10).replace(/-/g, '.')
    if (u.profile?.investment_style) user.investType = u.profile.investment_style
    loadActivity() // user.id 확보 후 활동(내 글·팔로워·팔로잉)
  } catch {
    // 실패 → 빈 값 유지
  }
}

// 활동: 본인 글 목록 + 팔로워/팔로잉 수 (전부 실데이터, 없으면 0/빈 목록)
async function loadActivity() {
  try {
    const { items = [], total = 0 } = await fetchPosts({ mine: true, size: 50 })
    myPosts.value = items.map(mapPost)
    user.posts = total
  } catch {
    myPosts.value = []
  }
  if (!user.id) return
  try { user.followers = (await fetchFollowers(user.id)).total ?? 0 } catch { /* 0 유지 */ }
  try { user.following = (await fetchFollowing(user.id)).total ?? 0 } catch { /* 0 유지 */ }
}

// 매매 내역 (GET /orders/)
async function loadOrders() {
  tradesError.value = ''
  try {
    const { items = [] } = await fetchOrders({ size: 30 })
    // 항상 실데이터로 교체(빈 응답이면 빈 목록). catch는 에러 노출 — 가짜 폴백/에러 삼킴 제거.
    trades.value = items.map((o) => ({
      id: o.id,
      date: (o.created_at || '').slice(0, 10).replace(/-/g, '.'),
      code: o.stock_code,
      name: o.stock_name,
      currency: o.currency || 'KRW', // 국내/해외 구분
      side: String(o.side).toLowerCase(), // BUY → buy
      qty: o.quantity,
      price: Number(o.price),
      total: Number(o.total_amount),
      pnl: o.realized_pnl != null ? Number(o.realized_pnl) : null,
    }))
  } catch (e) {
    trades.value = []
    tradesError.value = errMsg(e)
  }
}

function mapHolding(it) {
  return {
    code: it.stock.code,
    name: it.stock.name,
    currency: it.stock.currency,
    market: it.stock.market,
    qty: Number(it.quantity),
    avg: Number(it.average_price),
    cur: Number(it.current_price),
    value: Number(it.current_value),
    pnl: Number(it.profit_loss),
    pnlRate: Number(it.profit_loss_rate),
    color: holdColor(it.stock.code),
  }
}

// 계좌 요약 + 보유 목록 (GET /portfolio/, /portfolio/holdings/, KIS 503 재시도)
async function loadPortfolio() {
  try {
    const d = await retry(() => fetchPortfolioSummary(), { attempts: 5, delayMs: 500 })
    account.balance = Number(d.account?.balance ?? 0)
    account.totalInvested = Number(d.total_invested ?? 0)
    account.totalValue = Number(d.total_current_value ?? 0)
    account.totalAssets = Number(d.total_assets ?? 0)
    account.profitLoss = Number(d.total_profit_loss ?? 0)
    account.profitRate = Number(d.total_profit_loss_rate ?? 0)
  } catch {
    // 실패 → 0 유지
  }
  try {
    const { items = [] } = await retry(() => fetchHoldings(), { attempts: 5, delayMs: 500 })
    holdings.value = items.map(mapHolding)
  } catch {
    holdings.value = []
  }
}

// 프로필 저장 (PATCH /auth/me/) — 백엔드는 nickname/birth_year만 수정
async function onEditToggle() {
  if (!isEditingInfo.value) {
    isEditingInfo.value = true
    return
  }
  profileError.value = ''
  try {
    const payload = { nickname: user.nickname }
    const by = parseInt(user.birthYear, 10)
    if (!Number.isNaN(by)) payload.birth_year = by
    await updateMe(payload)
    isEditingInfo.value = false
  } catch (e) {
    profileError.value = errMsg(e)
  }
}

onMounted(() => {
  loadMe()
  loadOrders()
  loadPortfolio()
  loadMilestones()
})
</script>

<template>
  <div class="mypage-wrap">

    <!-- Profile Header -->
    <div class="profile-header panel">
      <div class="ph-avatar">{{ avatarChar }}</div>
      <div class="ph-info">
        <div class="ph-name">{{ user.nickname }}</div>
        <div class="ph-nick">@{{ user.nickname }}</div>
        <div class="ph-stats">
          <span><strong>{{ user.posts }}</strong> 글</span>
          <span><strong>{{ user.followers }}</strong> 팔로워</span>
          <span><strong>{{ user.following }}</strong> 팔로잉</span>
        </div>
      </div>
      <div v-if="milestones.length" class="ph-badges-preview" aria-label="달성 자산 마일스톤">
        <span v-for="(b, i) in milestones.slice(0, 6)" :key="i" class="badge-chip" :title="b.name">{{ b.icon }}</span>
      </div>
      <div class="ph-actions">
        <button class="ph-btn accent" @click="isEditingInfo = true; activeSection = 'profile'">프로필 편집</button>
        <button class="ph-btn" @click="activeSection = 'invest'">내 계좌</button>
      </div>
    </div>

    <!-- Body -->
    <div class="mypage-body">

      <!-- Side Tab Box -->
      <aside class="mp-sidebar panel">
        <ul class="mp-menu">
          <li
            v-for="tab in tabs"
            :key="tab.key"
            class="mp-menu-item"
            :class="{ active: activeSection === tab.key }"
            @click="activeSection = tab.key"
          >
            {{ tab.label }}
          </li>
        </ul>
      </aside>

      <!-- Content -->
      <div class="mp-content">

      <!-- ========== 내 투자 ========== -->
      <section v-if="activeSection === 'invest'" class="mp-section">

        <!-- 상단 3카드 -->
        <div class="invest-cards">
          <!-- 기본계좌: 총자산(예수금 + 주식 평가액) -->
          <div class="panel acc-balance-card">
            <div class="acc-label">기본계좌 · 총자산</div>
            <div class="acc-balance">{{ fmtKrw(account.totalAssets) }}<span class="acc-unit">원</span></div>
            <dl class="acc-breakdown">
              <div><dt>예수금</dt><dd>{{ fmtKrw(account.balance) }}원</dd></div>
              <div><dt>주식 평가액</dt><dd>{{ fmtKrw(account.totalValue) }}원</dd></div>
            </dl>
          </div>

          <!-- 총손익: 매수금액 → 평가금액 -->
          <div class="panel acc-profit-card">
            <div class="acc-label">총 손익</div>
            <div class="acc-profit-num" :class="account.profitLoss >= 0 ? 'pos' : 'neg'">{{ signedFmtKrw(account.profitLoss) }}원</div>
            <div class="acc-profit-pct" :class="account.profitLoss >= 0 ? 'pos' : 'neg'">{{ account.profitLoss >= 0 ? '+' : '' }}{{ account.profitRate.toFixed(2) }}%</div>
            <dl class="acc-breakdown">
              <div><dt>매수 금액</dt><dd>{{ fmtKrw(account.totalInvested) }}원</dd></div>
              <div><dt>평가 금액</dt><dd>{{ fmtKrw(account.totalValue) }}원</dd></div>
            </dl>
          </div>

          <!-- 보유 종목 현황 (국내/해외 분리) -->
          <div class="panel acc-holdings-card">
            <div class="acc-label">보유 종목 현황</div>
            <template v-for="g in [{ label: '🇰🇷 국내', rows: domesticHoldings }, { label: '🇺🇸 해외', rows: overseasHoldings }]" :key="g.label">
              <template v-if="g.rows.length">
                <div class="hold-group-label">{{ g.label }}</div>
                <div class="holdings-list">
                  <div v-for="h in g.rows" :key="h.code" class="holding-row">
                    <div class="hr-dot" :style="{ background: h.color }"></div>
                    <div class="hr-name">{{ h.name }}</div>
                    <div class="hr-qty">{{ h.qty }}주</div>
                    <div class="hr-pnl" :class="h.pnl >= 0 ? 'pos' : 'neg'">{{ h.pnl >= 0 ? '+' : '' }}{{ h.pnlRate.toFixed(1) }}%</div>
                  </div>
                </div>
              </template>
            </template>
            <p v-if="!holdings.length" class="holdings-empty">보유 중인 종목이 없어요.</p>
          </div>
        </div>

        <!-- 내 거래 내역 -->
        <div class="section-header">
          <h2>내 거래 내역</h2>
          <div class="trade-filter-tabs">
            <button
              v-for="f in [{k:'all',l:'전체'},{k:'buy',l:'매수'},{k:'sell',l:'매도'}]"
              :key="f.k"
              class="filter-tab"
              :class="{ active: tradeFilter === f.k }"
              @click="tradeFilter = f.k"
            >{{ f.l }}</button>
          </div>
        </div>

        <template v-for="g in [{ label: '🇰🇷 국내', rows: domesticTrades }, { label: '🇺🇸 해외', rows: overseasTrades }]" :key="g.label">
          <div class="trade-group-head">{{ g.label }} 거래내역 <span class="tgh-count">{{ g.rows.length }}</span></div>
          <div class="panel trade-table-wrap">
            <table class="trade-table">
              <thead>
                <tr>
                  <th>날짜</th>
                  <th>종목</th>
                  <th>구분</th>
                  <th class="num">수량</th>
                  <th class="num">체결 단가</th>
                  <th class="num">총 금액</th>
                  <th class="num">손익</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!g.rows.length">
                  <td colspan="7" class="trade-empty">
                    {{ tradesError ? '거래 내역을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.' : '거래 내역이 없어요.' }}
                  </td>
                </tr>
                <tr v-for="t in g.rows" :key="t.id">
                  <td class="trade-date">{{ t.date }}</td>
                  <td>
                    <div class="trade-name">{{ t.name }}</div>
                    <div class="trade-code">{{ t.code }}</div>
                  </td>
                  <td>
                    <span class="side-badge" :class="t.side">{{ t.side === 'buy' ? '매수' : '매도' }}</span>
                  </td>
                  <td class="num">{{ t.qty }}주</td>
                  <td class="num">{{ fmt(t.price) }}{{ curUnit(t.currency) }}</td>
                  <td class="num">{{ fmt(t.total) }}{{ curUnit(t.currency) }}</td>
                  <td class="num" :class="t.pnl !== null ? (t.pnl >= 0 ? 'pos' : 'neg') : ''">
                    <template v-if="t.pnl !== null">{{ signedFmt(t.pnl) }}{{ curUnit(t.currency) }}</template>
                    <template v-else>—</template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- Summary Row -->
        <div class="trade-summary">
          <div class="panel ts-card">
            <div class="ts-label">총 매수 금액</div>
            <div class="ts-value">{{ fmt(trades.filter(t=>t.side==='buy').reduce((a,t)=>a+t.total,0)) }}원</div>
          </div>
          <div class="panel ts-card">
            <div class="ts-label">총 매도 금액</div>
            <div class="ts-value">{{ fmt(trades.filter(t=>t.side==='sell').reduce((a,t)=>a+t.total,0)) }}원</div>
          </div>
          <div class="panel ts-card">
            <div class="ts-label">실현 손익</div>
            <div class="ts-value" :class="realizedPnl >= 0 ? 'pos' : 'neg'">
              {{ signedFmt(realizedPnl) }}원
            </div>
          </div>
          <div class="panel ts-card">
            <div class="ts-label">총 거래 횟수</div>
            <div class="ts-value">{{ trades.length }}회</div>
          </div>
        </div>
      </section>

      <!-- ========== 프로필 ========== -->
      <section v-else-if="activeSection === 'profile'" class="mp-section">
        <div class="section-header">
          <h2>프로필</h2>
          <button class="edit-btn" @click="onEditToggle">
            {{ isEditingInfo ? '저장' : '정보 수정' }}
          </button>
        </div>

        <p v-if="profileError" class="mp-error">{{ profileError }}</p>

        <div class="info-grid">
          <!-- Invest Type Card -->
          <div class="panel info-card">
            <div class="info-card-title">투자 성향</div>
            <template v-if="user.investType">
              <div class="invest-type-badge">{{ user.investType }}</div>
              <p class="invest-desc">온보딩 설문 응답을 바탕으로 분석된 나의 투자 성향이에요.</p>
            </template>
            <p v-else class="invest-desc">아직 투자 성향 검사를 하지 않았어요. 검사하면 맞춤 추천이 정확해져요.</p>
            <button class="retest-btn" type="button" @click="router.push('/onboarding')">투자 성향 재검사</button>
          </div>

          <!-- Personal Info Card -->
          <div class="panel info-card">
            <div class="info-card-title">기본 정보</div>
            <dl class="info-dl">
              <div class="info-row">
                <dt>닉네임</dt>
                <dd>
                  <template v-if="!isEditingInfo">{{ user.nickname }}</template>
                  <input v-else v-model="user.nickname" class="info-input" />
                </dd>
              </div>
              <div class="info-row">
                <dt>이메일</dt>
                <dd>{{ user.email }}</dd>
              </div>
              <div class="info-row">
                <dt>출생연도</dt>
                <dd>
                  <template v-if="!isEditingInfo">{{ user.birthYear }}</template>
                  <input v-else v-model="user.birthYear" class="info-input" type="number" inputmode="numeric" />
                </dd>
              </div>
              <div class="info-row">
                <dt>가입일</dt>
                <dd>{{ user.joinDate }}</dd>
              </div>
            </dl>
            <p class="info-note">이메일·가입일은 변경할 수 없어요.</p>
          </div>

          <!-- Community Profile Card -->
          <div class="panel info-card span2">
            <div class="info-card-title">커뮤니티 프로필</div>
            <div class="community-profile">
              <div class="cp-avatar">{{ avatarChar }}</div>
              <div class="cp-details">
                <div class="cp-name">{{ user.nickname }}</div>
                <div class="cp-sub">주만추 멤버 · {{ user.joinDate }} 가입</div>
                <div class="cp-stats">
                  <span>글 <strong>{{ user.posts }}</strong></span>
                  <span>팔로워 <strong>{{ user.followers }}</strong></span>
                  <span>팔로잉 <strong>{{ user.following }}</strong></span>
                  <span>받은 좋아요 <strong>{{ likesReceived }}</strong></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ========== 활동 내역 ========== -->
      <section v-else-if="activeSection === 'activity'" class="mp-section">
        <div class="section-header"><h2>활동 내역</h2></div>

        <div class="activity-layout">
          <div class="activity-main">
            <!-- Posts -->
            <div class="panel act-block">
              <div class="act-block-title">작성한 글 ({{ myPosts.length }})</div>
              <div class="post-list">
                <div v-for="post in myPosts" :key="post.id" class="post-item">
                  <div class="post-item-left">
                    <span class="post-cat">{{ post.category }}</span>
                    <span class="post-title post-title-link" @click="goPost(post.id)" :title="post.title">{{ post.title }}</span>
                  </div>
                  <div class="post-item-right">
                    <span class="post-meta">♥ {{ post.likes }}</span>
                    <span class="post-meta">💬 {{ post.comments }}</span>
                    <span class="post-meta post-time">{{ post.time }}</span>
                  </div>
                </div>
                <p v-if="!myPosts.length" class="act-empty">아직 작성한 글이 없어요.</p>
              </div>
            </div>
          </div>

          <!-- Stats Sidebar -->
          <div class="activity-side">
            <div class="panel act-stats-panel">
              <div class="act-block-title">활동 통계</div>
              <dl class="stats-dl">
                <div class="stats-row"><dt>총 게시글</dt><dd>{{ user.posts }}개</dd></div>
                <div class="stats-row"><dt>팔로워</dt><dd>{{ user.followers }}명</dd></div>
                <div class="stats-row"><dt>팔로잉</dt><dd>{{ user.following }}명</dd></div>
              </dl>
            </div>
          </div>
        </div>
      </section>

      </div><!-- /mp-content -->
    </div><!-- /mypage-body -->
  </div>
</template>

<style scoped>
.mypage-wrap {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 64px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ---- Profile Header ---- */
.profile-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  padding: 24px 28px;
}

.ph-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  font-size: 24px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(var(--accent-rgb), 0.3);
}

.ph-info { flex: 1; }
.ph-name { font-size: 20px; font-weight: 900; color: var(--ink); }
.ph-nick { font-size: 13px; color: var(--muted); margin-top: 2px; }
.ph-stats {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 13px;
  color: var(--muted);
}
.ph-stats strong { color: var(--ink); }

.ph-badges-preview {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.badge-chip {
  font-size: 22px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--glass);
  border: 1px solid var(--glass-border);
  border-radius: 50%;
  cursor: default;
}

.ph-actions { display: flex; gap: 8px; flex-shrink: 0; }
.ph-btn {
  height: 36px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  cursor: pointer;
  transition: background 0.15s;
}
.ph-btn:hover { background: var(--glass-strong); }
.ph-btn.accent {
  background: rgba(var(--accent-rgb),0.1);
  border-color: rgba(var(--accent-rgb),0.28);
  color: var(--accent);
}
.ph-btn.accent:hover { background: rgba(var(--accent-rgb),0.18); }

/* ---- Body Layout ---- */
.mypage-body {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 20px;
  align-items: start;
}
/* 그리드 아이템이 내부 min-content(표·고정폭 그리드)에 밀려 트랙을 넓히지 않도록 — 가로 넘침 방지 */
.mp-sidebar, .mp-content { min-width: 0; }

/* ---- Side Tab Box ---- */
.mp-sidebar { padding: 12px 0; position: sticky; top: 80px; }
.mp-menu { list-style: none; padding: 0; margin: 0; }
.mp-menu-item {
  padding: 11px 20px;
  font-size: 14px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  border-radius: var(--radius);
  margin: 2px 8px;
  transition: background 0.15s, color 0.15s;
}
.mp-menu-item:hover { background: var(--glass); color: var(--ink); }
.mp-menu-item.active {
  background: rgba(var(--accent-rgb),0.1);
  color: var(--accent);
}

/* ---- Section ---- */
.mp-section { display: flex; flex-direction: column; gap: 16px; }
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.section-header h2 { font-size: 18px; font-weight: 900; color: var(--ink); margin: 0; }

.edit-btn {
  height: 32px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgba(var(--accent-rgb),0.28);
  background: rgba(var(--accent-rgb),0.08);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.edit-btn:hover { background: rgba(var(--accent-rgb),0.15); }

/* ---- 내 투자: 상단 3카드 ---- */
.invest-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
  align-items: start;
}

/* ---- 프로필 ---- */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.info-card { padding: 20px 24px; }
.info-card.span2 { grid-column: 1 / -1; }
.info-card-title { font-size: 13px; font-weight: 800; color: var(--muted); margin-bottom: 14px; letter-spacing: 0.05em; text-transform: uppercase; }

.info-dl { display: flex; flex-direction: column; gap: 0; }
.info-row {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--faint);
  gap: 12px;
}
.info-row:last-child { border-bottom: none; }
.info-row dt { font-size: 13px; color: var(--muted); width: 110px; flex-shrink: 0; }
.info-row dd { font-size: 14px; color: var(--ink); font-weight: 600; flex: 1; margin: 0; }
.info-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid rgba(var(--accent-rgb),0.3);
  border-radius: 6px;
  background: var(--glass);
  font-size: 14px;
  color: var(--ink);
  outline: none;
}
.info-input:focus { border-color: var(--accent); }
.info-note { margin: 12px 0 0; font-size: 11px; font-weight: 700; color: var(--faint); }
.mp-error { margin: 0; padding: 10px 14px; border-radius: var(--radius); border: 1px solid rgba(207,61,61,0.3); background: rgba(207,61,61,0.08); color: #cf3d3d; font-size: 13px; font-weight: 800; }
.trade-empty { padding: 28px 16px !important; text-align: center; color: var(--muted); font-weight: 700; font-size: 13px; }

.invest-type-badge {
  display: inline-block;
  padding: 5px 14px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  font-size: 13px;
  font-weight: 800;
  margin-bottom: 10px;
}
.invest-desc { font-size: 13px; color: var(--muted); line-height: 1.6; margin-bottom: 14px; }

.retest-btn {
  width: 100%;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  font-size: 13px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
}
.retest-btn:hover { background: var(--glass-strong); color: var(--ink); }

.community-profile { display: flex; align-items: center; gap: 16px; }
.cp-avatar {
  width: 52px; height: 52px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff; font-size: 20px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.cp-name { font-size: 16px; font-weight: 900; color: var(--ink); }
.cp-sub { font-size: 12px; color: var(--muted); margin-top: 2px; }
.cp-stats { display: flex; gap: 16px; margin-top: 8px; font-size: 13px; color: var(--muted); }
.cp-stats strong { color: var(--ink); }

/* ---- 활동 내역 ---- */
.activity-layout { display: grid; grid-template-columns: 1fr 240px; gap: 16px; align-items: start; }
.activity-main { display: flex; flex-direction: column; gap: 16px; }
.activity-side { display: flex; flex-direction: column; gap: 16px; }

.act-block { padding: 20px 24px; }
.act-block-title { font-size: 13px; font-weight: 800; color: var(--muted); margin-bottom: 14px; }

.post-list { display: flex; flex-direction: column; gap: 0; }
.post-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--faint);
  gap: 8px;
}
.post-item:last-child { border-bottom: none; }
.post-item-left { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.post-cat {
  font-size: 11px; font-weight: 700; padding: 2px 7px;
  border-radius: 999px; background: rgba(var(--accent-rgb),0.1); color: var(--accent);
  white-space: nowrap; flex-shrink: 0;
}
.post-title { font-size: 13px; color: var(--ink); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.post-title-link { cursor: pointer; transition: color 0.14s; }
.post-title-link:hover { color: var(--accent); text-decoration: underline; }
.post-item-right { display: flex; gap: 10px; flex-shrink: 0; }
.post-meta { font-size: 12px; color: var(--muted); }
.post-time { font-size: 11px; }
.act-empty { margin: 8px 0 2px; font-size: 13px; font-weight: 700; color: var(--muted); }

.act-stats-panel { padding: 20px; }
.stats-dl { display: flex; flex-direction: column; gap: 0; }
.stats-row {
  display: flex; justify-content: space-between;
  padding: 8px 0; border-bottom: 1px solid var(--faint);
  font-size: 13px;
}
.stats-row:last-child { border-bottom: none; }
.stats-row dt { color: var(--muted); }
.stats-row dd { color: var(--ink); font-weight: 700; margin: 0; }

/* ---- 내 거래 내역 ---- */
.trade-filter-tabs { display: flex; gap: 4px; }
.filter-tab {
  height: 30px; padding: 0 12px; border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--glass-subtle);
  font-size: 12px; font-weight: 700; color: var(--muted);
  cursor: pointer; transition: all 0.15s;
}
.filter-tab.active {
  background: rgba(var(--accent-rgb),0.1);
  border-color: rgba(var(--accent-rgb),0.28);
  color: var(--accent);
}

.trade-table-wrap { padding: 0; overflow-x: auto; }
.trade-table { width: 100%; min-width: 560px; border-collapse: collapse; font-size: 13px; }
.trade-table thead tr { background: var(--glass-subtle); }
.trade-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 800;
  color: var(--muted);
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
.trade-table th.num { text-align: right; }
.trade-table td {
  padding: 11px 16px;
  border-bottom: 1px solid var(--faint);
  color: var(--ink);
  vertical-align: middle;
}
.trade-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.trade-table tr:last-child td { border-bottom: none; }
.trade-table tr:hover td { background: var(--surface-faint); }

.trade-date { color: var(--muted); font-size: 12px; }
.trade-name { font-weight: 700; }
.trade-code { font-size: 11px; color: var(--muted); margin-top: 2px; }

.side-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px;
  font-size: 11px; font-weight: 800;
}
.side-badge.buy { background: rgba(var(--accent-rgb),0.12); color: var(--accent); }
.side-badge.sell { background: rgba(239,68,68,0.1); color: var(--negative); }

.pos { color: var(--positive); }
.neg { color: var(--negative); }

.trade-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.ts-card { padding: 16px 20px; }
.ts-label { font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 700; }
.ts-value { font-size: 16px; font-weight: 900; color: var(--ink); white-space: nowrap; }
.ts-value.pos { color: var(--positive); }

/* ---- 계좌 카드 (내 투자 탭) ---- */
.acc-balance-card,
.acc-profit-card,
.acc-holdings-card { padding: 20px 24px; }

.acc-label { font-size: 12px; font-weight: 800; color: var(--muted); margin-bottom: 8px; }
.acc-balance {
  font-size: 28px; font-weight: 900; color: var(--ink);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  margin-bottom: 14px;
}
.acc-unit { font-size: 16px; font-weight: 700; margin-left: 2px; }

.acc-profit-num { font-size: 26px; font-weight: 900; font-variant-numeric: tabular-nums; white-space: nowrap; margin-bottom: 4px; }
.acc-profit-pct { font-size: 14px; font-weight: 700; margin-bottom: 8px; }

/* 계좌 카드 내역(예수금/주식평가액, 매수/평가금액) */
.acc-breakdown { display: flex; flex-direction: column; gap: 4px; margin: 10px 0 0; }
.acc-breakdown > div { display: flex; justify-content: space-between; font-size: 12px; }
.acc-breakdown dt { color: var(--muted); white-space: nowrap; }
.acc-breakdown dd { margin: 0; font-weight: 800; color: var(--ink); font-variant-numeric: tabular-nums; }

/* 보유 종목 국내/해외 그룹 라벨 */
.hold-group-label { font-size: 11px; font-weight: 900; color: var(--muted); margin: 10px 0 2px; }
.hold-group-label:first-of-type { margin-top: 4px; }

/* 거래내역 국내/해외 헤더 */
.trade-group-head { font-size: 14px; font-weight: 900; color: var(--ink); margin: 14px 0 8px; }
.tgh-count { font-size: 12px; font-weight: 800; color: var(--muted); margin-left: 4px; }

.holdings-list { display: flex; flex-direction: column; gap: 0; }
.holdings-empty { margin: 4px 0; font-size: 13px; font-weight: 700; color: var(--muted); }
.holding-row {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 0; border-bottom: 1px solid var(--faint);
  font-size: 13px;
}
.holding-row:last-child { border-bottom: none; }
.hr-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.hr-name { flex: 1; font-weight: 700; color: var(--ink); }
.hr-qty { color: var(--muted); font-size: 12px; }
.hr-pnl { font-weight: 800; font-size: 13px; min-width: 52px; text-align: right; }

/* ---- 반응형 (모바일/태블릿) ---- */
@media (max-width: 768px) {
  /* 사이드바 → 상단 가로 탭바, 본문 1열 */
  .mypage-body { grid-template-columns: 1fr; }
  .mp-sidebar { position: static; top: auto; padding: 6px; }
  .mp-menu { display: flex; gap: 4px; }
  .mp-menu-item { flex: 1; margin: 0; text-align: center; }
  /* 카드 그리드 단일 열로 — 위 프로필 카드 폭에 맞춤 */
  .invest-cards,
  .info-grid,
  .activity-layout { grid-template-columns: 1fr; }
  /* 거래 요약 4칸 → 2열 */
  .trade-summary { grid-template-columns: 1fr 1fr; }
}
</style>
