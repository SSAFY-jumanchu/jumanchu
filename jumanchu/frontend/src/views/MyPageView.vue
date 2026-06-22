<script setup>
import { ref, computed, reactive } from 'vue'
import { useCopy } from '../composables/useCopy'

const { t } = useCopy()

const activeSection = ref('invest')

const user = reactive({
  name: '김주만',
  nickname: '열정적인얼룩말37',
  email: 'kimjuman@example.com',
  phone: '010-1234-5678',
  birthdate: '1998.07.22',
  address: '서울특별시 강남구 테헤란로 123',
  investType: '안정성장형',
  joinDate: '2024.03.15',
  posts: 12,
  followers: 47,
  following: 31,
})

// 프로필 헤더 아이콘 (와이어프레임 slide 9/10/11 공통 헤더)
const headerBadges = [
  { id: 1, icon: '🌱', name: '첫 만남' },
  { id: 2, icon: '📈', name: '수익왕' },
  { id: 3, icon: '🔥', name: '연속 투자' },
]

const activities = [
  { id: 1, type: 'post', time: '2시간 전', content: '삼성전자 지금 매수 타이밍 맞나요? 제 생각엔...', likes: 24, comments: 8 },
  { id: 2, type: 'comment', time: '5시간 전', content: '→ "NVIDIA 실적 발표 분석" 에 댓글: "좋은 분석이네요. 저도 비슷한 생각이에요"', likes: 3, comments: null },
  { id: 3, type: 'like', time: '어제', content: '❤️ "고배당주 포트폴리오 구성 전략" 글을 좋아해요', likes: null, comments: null },
  { id: 4, type: 'post', time: '3일 전', content: '2025 상반기 포트폴리오 리뷰 — 수익률 +18.3% 달성 후기', likes: 67, comments: 22 },
  { id: 5, type: 'comment', time: '4일 전', content: '→ "달러 환율 전망" 에 댓글: "환율 리스크 헷징은 어떻게 하시나요?"', likes: 7, comments: null },
  { id: 6, type: 'like', time: '5일 전', content: '❤️ "SK하이닉스 HBM 수요 전망" 글을 좋아해요', likes: null, comments: null },
]

const myPosts = [
  { id: 1, time: '2시간 전', category: '질문', title: '삼성전자 지금 매수 타이밍 맞나요?', likes: 24, comments: 8, views: 183 },
  { id: 2, time: '3일 전', category: '후기', title: '2025 상반기 포트폴리오 리뷰 — 수익률 +18.3% 달성 후기', likes: 67, comments: 22, views: 1204 },
  { id: 3, time: '2주 전', category: '분석', title: 'NAVER vs 카카오 — 하반기 반등 가능성 비교', likes: 41, comments: 15, views: 876 },
  { id: 4, time: '1달 전', category: '공유', title: '주린이가 처음 1년 동안 배운 것들', likes: 132, comments: 44, views: 5321 },
]

const trades = ref([
  { id: 1, date: '2026.06.05', code: '005930', name: '삼성전자', side: 'buy',  qty: 20, price: 317000, total: 6340000, pnl: null },
  { id: 2, date: '2026.06.04', code: '000660', name: 'SK하이닉스', side: 'sell', qty: 5,  price: 243000, total: 1215000, pnl: +87500 },
  { id: 3, date: '2026.06.03', code: 'NVDA',   name: 'NVIDIA',    side: 'buy',  qty: 3,  price: 1285000,total: 3855000, pnl: null },
  { id: 4, date: '2026.06.02', code: '005930', name: '삼성전자', side: 'sell', qty: 10, price: 312000, total: 3120000, pnl: -35000 },
  { id: 5, date: '2026.05.30', code: '035420', name: 'NAVER',    side: 'buy',  qty: 8,  price: 189500, total: 1516000, pnl: null },
  { id: 6, date: '2026.05.28', code: 'AAPL',   name: 'APPLE',    side: 'buy',  qty: 2,  price: 248000, total: 496000,  pnl: null },
  { id: 7, date: '2026.05.25', code: '000660', name: 'SK하이닉스', side: 'buy',  qty: 10, price: 238000, total: 2380000, pnl: null },
  { id: 8, date: '2026.05.22', code: '005930', name: '삼성전자', side: 'sell', qty: 15, price: 308000, total: 4620000, pnl: +120000 },
  { id: 9, date: '2026.05.20', code: '035720', name: '카카오',   side: 'sell', qty: 20, price: 47500,  total: 950000,  pnl: -62000 },
  { id: 10,date: '2026.05.15', code: 'GOOGL',  name: 'ALPHABET', side: 'buy',  qty: 1,  price: 2180000,total: 2180000, pnl: null },
])
const tradeFilter = ref('all')
const filteredTrades = computed(() => {
  if (tradeFilter.value === 'all') return trades.value
  return trades.value.filter(t => t.side === tradeFilter.value)
})

const account = reactive({
  balance: 10532800,
  totalInvested: 9285000,
  monthProfit: 318400,
  sellProfit: 110500,
  dividend: 24800,
  interest: 3200,
})

const profitPct = computed(() => ((account.monthProfit / account.totalInvested) * 100).toFixed(2))

const holdings = [
  { name:'삼성전자', qty:20, avg:310500, cur:317000, color:'#315dff' },
  { name:'SK하이닉스', qty:10, avg:238000, cur:243000, color:'#7d4ee8' },
  { name:'NVIDIA', qty:3, avg:1251000, cur:1285000, color:'#22c55e' },
  { name:'NAVER', qty:8, avg:189500, cur:184000, color:'#f59e0b' },
  { name:'APPLE', qty:2, avg:248000, cur:261000, color:'#06b6d4' },
]

const monthlyReturns = [
  { label:'1월', val: 4.2 }, { label:'2월', val: -1.8 }, { label:'3월', val: 7.1 },
  { label:'4월', val: 3.5 }, { label:'5월', val: 9.3 }, { label:'6월', val: 3.4 },
]

const tabs = [
  { key: 'invest',  label: '내 투자' },
  { key: 'profile', label: '프로필' },
  { key: 'activity',label: '활동 내역' },
]

function fmt(n) {
  return n.toLocaleString('ko-KR')
}
function signedFmt(n) {
  return (n >= 0 ? '+' : '') + n.toLocaleString('ko-KR')
}

const isEditingInfo = ref(false)
</script>

<template>
  <div class="mypage-wrap">

    <!-- Profile Header -->
    <div class="profile-header panel">
      <div class="ph-avatar">김</div>
      <div class="ph-info">
        <div class="ph-name">{{ user.name }}</div>
        <div class="ph-nick">@{{ user.nickname }}</div>
        <div class="ph-stats">
          <span><strong>{{ user.posts }}</strong> 글</span>
          <span><strong>{{ user.followers }}</strong> 팔로워</span>
          <span><strong>{{ user.following }}</strong> 팔로잉</span>
        </div>
      </div>
      <div class="ph-badges-preview">
        <span v-for="b in headerBadges" :key="b.id" class="badge-chip" :title="b.name">{{ b.icon }}</span>
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
            {{ t('mp.tab.' + tab.key, tab.label) }}
          </li>
        </ul>
      </aside>

      <!-- Content -->
      <div class="mp-content">

      <!-- ========== 내 투자 ========== -->
      <section v-if="activeSection === 'invest'" class="mp-section">

        <!-- 상단 3카드 -->
        <div class="invest-cards">
          <!-- 기본계좌 + 수익분석 (한 카드) -->
          <div class="panel acc-balance-card">
            <div class="acc-label">기본계좌 · 주식</div>
            <div class="acc-balance">{{ fmt(account.balance) }}<span class="acc-unit">원</span></div>
            <div class="acc-actions">
              <button class="acc-btn accent">채우기</button>
              <button class="acc-btn">보내기</button>
              <button class="acc-btn">환전</button>
            </div>

            <!-- 수익분석 -->
            <div class="acc-analysis">
              <div class="acc-label">{{ t('mp.invest.analysis', '수익분석') }}</div>
              <div class="analysis-bars">
                <div v-for="m in monthlyReturns" :key="m.label" class="ab-col">
                  <div class="ab-bar-wrap">
                    <div
                      class="ab-bar"
                      :class="m.val >= 0 ? 'pos-bar' : 'neg-bar'"
                      :style="{ height: Math.abs(m.val) * 5 + 'px' }"
                    ></div>
                  </div>
                  <div class="ab-val" :class="m.val >= 0 ? 'pos' : 'neg'">{{ m.val > 0 ? '+' : '' }}{{ m.val }}%</div>
                  <div class="ab-label">{{ m.label }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Profit Card -->
          <div class="panel acc-profit-card">
            <div class="acc-label">이달 수익</div>
            <div class="acc-profit-num pos">+{{ fmt(account.monthProfit) }}원</div>
            <div class="acc-profit-pct pos">+{{ profitPct }}%</div>
            <dl class="acc-dl mt16">
              <div class="acc-row">
                <dt>판매수익</dt>
                <dd :class="account.sellProfit >= 0 ? 'pos' : 'neg'">{{ signedFmt(account.sellProfit) }}원</dd>
              </div>
              <div class="acc-row">
                <dt>배당금</dt>
                <dd>{{ fmt(account.dividend) }}원</dd>
              </div>
              <div class="acc-row">
                <dt>이자</dt>
                <dd>{{ fmt(account.interest) }}원</dd>
              </div>
            </dl>
          </div>

          <!-- Holdings Summary -->
          <div class="panel acc-holdings-card">
            <div class="acc-label">{{ t('mp.invest.holdings', '보유 종목 현황') }}</div>
            <div class="holdings-list">
              <div v-for="h in holdings" :key="h.name" class="holding-row">
                <div class="hr-dot" :style="{ background: h.color }"></div>
                <div class="hr-name">{{ h.name }}</div>
                <div class="hr-qty">{{ h.qty }}주</div>
                <div class="hr-pnl" :class="(h.cur - h.avg) >= 0 ? 'pos' : 'neg'">
                  {{ ((h.cur - h.avg) / h.avg * 100).toFixed(1) }}%
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 내 거래 내역 -->
        <div class="section-header">
          <h2>{{ t('mp.invest.trades', '내 거래 내역') }}</h2>
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
              <tr v-for="t in filteredTrades" :key="t.id">
                <td class="trade-date">{{ t.date }}</td>
                <td>
                  <div class="trade-name">{{ t.name }}</div>
                  <div class="trade-code">{{ t.code }}</div>
                </td>
                <td>
                  <span class="side-badge" :class="t.side">
                    {{ t.side === 'buy' ? '매수' : '매도' }}
                  </span>
                </td>
                <td class="num">{{ t.qty }}주</td>
                <td class="num">{{ fmt(t.price) }}원</td>
                <td class="num">{{ fmt(t.total) }}원</td>
                <td class="num" :class="t.pnl !== null ? (t.pnl >= 0 ? 'pos' : 'neg') : ''">
                  <template v-if="t.pnl !== null">{{ signedFmt(t.pnl) }}원</template>
                  <template v-else>—</template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

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
            <div class="ts-value pos">
              +{{ fmt(trades.filter(t=>t.pnl!==null).reduce((a,t)=>a+t.pnl,0)) }}원
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
          <button class="edit-btn" @click="isEditingInfo = !isEditingInfo">
            {{ isEditingInfo ? '저장' : '정보 수정' }}
          </button>
        </div>

        <div class="info-grid">
          <!-- Invest Type Card -->
          <div class="panel info-card">
            <div class="info-card-title">{{ t('mp.profile.investType', '투자 성향') }}</div>
            <div class="invest-type-badge">{{ user.investType }}</div>
            <p class="invest-desc">안정성을 추구하면서 꾸준한 성장을 원하는 투자 유형이에요. 배당주와 우량 성장주를 균형 있게 담는 것을 권장해요.</p>
            <div class="invest-bars">
              <div class="ib-row"><span>안정성</span><div class="ib-track"><div class="ib-fill" style="width:62%; background:var(--accent)"></div></div><span>62</span></div>
              <div class="ib-row"><span>성장성</span><div class="ib-track"><div class="ib-fill" style="width:78%; background:var(--purple)"></div></div><span>78</span></div>
              <div class="ib-row"><span>리스크허용</span><div class="ib-track"><div class="ib-fill" style="width:45%; background:#22c55e"></div></div><span>45</span></div>
            </div>
            <button class="retest-btn">{{ t('mp.profile.retest', '투자 성향 재검사') }}</button>
          </div>

          <!-- Personal Info Card -->
          <div class="panel info-card">
            <div class="info-card-title">기본 정보</div>
            <dl class="info-dl">
              <div class="info-row">
                <dt>이름</dt>
                <dd>
                  <template v-if="!isEditingInfo">{{ user.name }}</template>
                  <input v-else v-model="user.name" class="info-input" />
                </dd>
              </div>
              <div class="info-row">
                <dt>닉네임</dt>
                <dd>
                  <template v-if="!isEditingInfo">{{ user.nickname }}</template>
                  <input v-else v-model="user.nickname" class="info-input" />
                </dd>
              </div>
              <div class="info-row">
                <dt>이메일</dt>
                <dd>
                  <template v-if="!isEditingInfo">{{ user.email }}</template>
                  <input v-else v-model="user.email" class="info-input" />
                </dd>
              </div>
              <div class="info-row">
                <dt>휴대폰</dt>
                <dd>
                  <template v-if="!isEditingInfo">{{ user.phone }}</template>
                  <input v-else v-model="user.phone" class="info-input" />
                </dd>
              </div>
              <div class="info-row">
                <dt>생년월일</dt>
                <dd>{{ user.birthdate }}</dd>
              </div>
              <div class="info-row">
                <dt>주소</dt>
                <dd>
                  <template v-if="!isEditingInfo">{{ user.address }}</template>
                  <input v-else v-model="user.address" class="info-input" />
                </dd>
              </div>
              <div class="info-row">
                <dt>가입일</dt>
                <dd>{{ user.joinDate }}</dd>
              </div>
            </dl>
          </div>

          <!-- Community Profile Card -->
          <div class="panel info-card span2">
            <div class="info-card-title">{{ t('mp.profile.community', '커뮤니티 프로필') }}</div>
            <div class="community-profile">
              <div class="cp-avatar">김</div>
              <div class="cp-details">
                <div class="cp-name">{{ user.nickname }}</div>
                <div class="cp-sub">주만추 멤버 · {{ user.joinDate }} 가입</div>
                <div class="cp-stats">
                  <span>글 <strong>{{ user.posts }}</strong></span>
                  <span>팔로워 <strong>{{ user.followers }}</strong></span>
                  <span>팔로잉 <strong>{{ user.following }}</strong></span>
                  <span>받은 좋아요 <strong>294</strong></span>
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
              <div class="act-block-title">{{ t('mp.act.posts', '작성한 글') }} ({{ myPosts.length }})</div>
              <div class="post-list">
                <div v-for="post in myPosts" :key="post.id" class="post-item">
                  <div class="post-item-left">
                    <span class="post-cat">{{ post.category }}</span>
                    <span class="post-title">{{ post.title }}</span>
                  </div>
                  <div class="post-item-right">
                    <span class="post-meta">♥ {{ post.likes }}</span>
                    <span class="post-meta">💬 {{ post.comments }}</span>
                    <span class="post-meta post-time">{{ post.time }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Activity Stream -->
            <div class="panel act-block">
              <div class="act-block-title">최근 활동</div>
              <div class="activity-list">
                <div v-for="act in activities" :key="act.id" class="act-item" :class="act.type">
                  <div class="act-icon">
                    <span v-if="act.type === 'post'">✏️</span>
                    <span v-else-if="act.type === 'comment'">💬</span>
                    <span v-else>❤️</span>
                  </div>
                  <div class="act-body">
                    <div class="act-content">{{ act.content }}</div>
                    <div class="act-time">{{ act.time }}</div>
                  </div>
                  <div v-if="act.likes !== null" class="act-stats">
                    <span>♥ {{ act.likes }}</span>
                    <span v-if="act.comments !== null">💬 {{ act.comments }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Stats Sidebar -->
          <div class="activity-side">
            <div class="panel act-stats-panel">
              <div class="act-block-title">활동 통계</div>
              <dl class="stats-dl">
                <div class="stats-row"><dt>총 게시글</dt><dd>{{ user.posts }}개</dd></div>
                <div class="stats-row"><dt>총 댓글</dt><dd>38개</dd></div>
                <div class="stats-row"><dt>받은 좋아요</dt><dd>294개</dd></div>
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
  box-shadow: 0 4px 16px rgba(49, 93, 255, 0.3);
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
  background: rgba(49,93,255,0.1);
  border-color: rgba(49,93,255,0.28);
  color: var(--accent);
}
.ph-btn.accent:hover { background: rgba(49,93,255,0.18); }

/* ---- Body Layout ---- */
.mypage-body {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 20px;
  align-items: start;
}

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
  background: rgba(49,93,255,0.1);
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
  border: 1px solid rgba(49,93,255,0.28);
  background: rgba(49,93,255,0.08);
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.edit-btn:hover { background: rgba(49,93,255,0.15); }

/* ---- 내 투자: 상단 3카드 ---- */
.invest-cards {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  align-items: start;
}

/* 기본계좌 카드 안에 들어간 수익분석 영역 */
.acc-analysis {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}
.acc-analysis .acc-label { margin-bottom: 12px; }

/* ---- 프로필 ---- */
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
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
  border: 1px solid rgba(49,93,255,0.3);
  border-radius: 6px;
  background: var(--glass);
  font-size: 14px;
  color: var(--ink);
  outline: none;
}
.info-input:focus { border-color: var(--accent); }

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

.invest-bars { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.ib-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted); }
.ib-row span:first-child { width: 64px; }
.ib-row span:last-child { width: 24px; text-align: right; font-weight: 700; color: var(--ink); }
.ib-track { flex: 1; height: 6px; background: var(--faint); border-radius: 999px; overflow: hidden; }
.ib-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }

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
  border-radius: 999px; background: rgba(49,93,255,0.1); color: var(--accent);
  white-space: nowrap; flex-shrink: 0;
}
.post-title { font-size: 13px; color: var(--ink); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.post-item-right { display: flex; gap: 10px; flex-shrink: 0; }
.post-meta { font-size: 12px; color: var(--muted); }
.post-time { font-size: 11px; }

.activity-list { display: flex; flex-direction: column; gap: 0; }
.act-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--faint);
}
.act-item:last-child { border-bottom: none; }
.act-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
.act-body { flex: 1; min-width: 0; }
.act-content { font-size: 13px; color: var(--ink); line-height: 1.5; }
.act-time { font-size: 11px; color: var(--muted); margin-top: 3px; }
.act-stats { font-size: 12px; color: var(--muted); display: flex; gap: 8px; flex-shrink: 0; padding-top: 2px; }

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
  background: rgba(49,93,255,0.1);
  border-color: rgba(49,93,255,0.28);
  color: var(--accent);
}

.trade-table-wrap { padding: 0; overflow: hidden; }
.trade-table { width: 100%; border-collapse: collapse; font-size: 13px; }
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
.side-badge.buy { background: rgba(49,93,255,0.12); color: var(--accent); }
.side-badge.sell { background: rgba(239,68,68,0.1); color: var(--negative); }

.pos { color: var(--positive); }
.neg { color: var(--negative); }

.trade-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.ts-card { padding: 16px 20px; }
.ts-label { font-size: 12px; color: var(--muted); margin-bottom: 6px; font-weight: 700; }
.ts-value { font-size: 16px; font-weight: 900; color: var(--ink); }
.ts-value.pos { color: var(--positive); }

/* ---- 계좌 카드 (내 투자 탭) ---- */
.acc-balance-card,
.acc-profit-card,
.acc-holdings-card { padding: 20px 24px; }

.acc-label { font-size: 12px; font-weight: 800; color: var(--muted); margin-bottom: 8px; }
.acc-balance {
  font-size: 28px; font-weight: 900; color: var(--ink);
  font-variant-numeric: tabular-nums;
  margin-bottom: 14px;
}
.acc-unit { font-size: 16px; font-weight: 700; margin-left: 2px; }

.acc-actions { display: flex; gap: 8px; margin-bottom: 16px; }
.acc-btn {
  height: 34px; padding: 0 14px; border-radius: 8px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  font-size: 13px; font-weight: 700; color: var(--muted);
  cursor: pointer; transition: all 0.15s;
}
.acc-btn:hover { background: var(--glass-strong); color: var(--ink); }
.acc-btn.accent {
  background: rgba(49,93,255,0.1);
  border-color: rgba(49,93,255,0.28);
  color: var(--accent);
}
.acc-btn.accent:hover { background: rgba(49,93,255,0.18); }

.acc-dl { display: flex; flex-direction: column; gap: 0; }
.acc-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid var(--faint);
  font-size: 13px;
}
.acc-row:last-child { border-bottom: none; }
.acc-row dt { color: var(--muted); }
.acc-row dd { font-weight: 700; color: var(--ink); margin: 0; }

.acc-profit-num { font-size: 26px; font-weight: 900; font-variant-numeric: tabular-nums; margin-bottom: 4px; }
.acc-profit-pct { font-size: 14px; font-weight: 700; margin-bottom: 0; }
.mt16 { margin-top: 16px; }

.holdings-list { display: flex; flex-direction: column; gap: 0; }
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

.analysis-bars {
  display: flex; align-items: flex-end; gap: 8px;
  padding-top: 8px; height: 120px;
}
.ab-col {
  flex: 1; display: flex; flex-direction: column; align-items: center;
  justify-content: flex-end; gap: 3px;
}
.ab-bar-wrap {
  display: flex; align-items: flex-end; justify-content: center;
  height: 60px; width: 100%;
}
.ab-bar { width: 100%; max-width: 28px; border-radius: 4px 4px 0 0; min-height: 4px; }
.pos-bar { background: var(--positive); }
.neg-bar { background: var(--negative); border-radius: 0 0 4px 4px; }
.ab-val { font-size: 10px; font-weight: 700; }
.ab-label { font-size: 11px; color: var(--muted); }
</style>
