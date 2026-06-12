<script setup>
import { ref, computed, reactive } from 'vue'

// ===== 카테고리 탭 =====
const selectedCategory = ref('전체')
const categories = ['전체', '팔로잉', '뉴스']

// ===== 글쓰기 상태 =====
const writeMode = ref(false)
const writeText = ref('')

// ===== 반응형 상태 =====
const likedPosts = reactive({})
const followedUsers = reactive({ '국내주식토론': true, '미국주식이야기': false, '따박배당': false })
const expandedPost = ref(null)
const likedComments = reactive({})
const commentInputs = reactive({})

// ===== 포스트 데이터 =====
const posts = ref([
  {
    id: 1,
    username: '국내주식토론', avatar: '국', userType: 'channel', color: '#315dff',
    time: '6시간전', category: '국내주식토론',
    title: '달러환율 금융위기수준까지상승',
    content: null,
    chart: 'exchange-rate',
    likes: 199, comments: 32, shares: 6,
    commentsList: [
      { id: 1, user: '투자자A', avatar: '투', time: '5시간전', content: '벌써 1500원을 넘었네요... 수입 기업들 큰일 났겠는데요.', likes: 12 },
      { id: 2, user: '환율걱정중', avatar: '환', time: '4시간전', content: '2009년 금융위기 수준이면 경제 전반에 큰 영향이 있겠죠?', likes: 8 },
      { id: 3, user: '달러매수자', avatar: '달', time: '3시간전', content: '달러 환전해놨더니 저절로 수익이 났습니다 ㅎㅎ', likes: 34 },
    ],
  },
  {
    id: 2,
    username: '국내주식토론', avatar: '국', userType: 'channel', color: '#315dff',
    time: '5시간전', category: '국내주식토론',
    title: '코스피 변동성이 커지는 건 당연한 사실',
    content: '삼성전자+닉스 집중된 삼성세\n외국인은 팔고 개인은 사고\n높아난 빚투에\n레버리지\n차발 선거 종료까지',
    chart: 'kospi-bar',
    likes: 150, comments: 34, shares: 4,
    commentsList: [
      { id: 1, user: '코스피투자자', avatar: '코', time: '4시간전', content: '외국인 매도세가 정말 장기화되고 있네요. 언제까지 갈까요.', likes: 15 },
      { id: 2, user: '개인투자자', avatar: '개', time: '3시간전', content: '변동성이 커질수록 오히려 기회가 생기는 것 같아요.', likes: 7 },
    ],
  },
  {
    id: 3,
    username: '짱짱맛플리', avatar: '짱', userType: 'user', color: '#7d4ee8',
    time: '6시간전(수정됨)', category: '뭐든해봐',
    title: '환율 1545원 돌파',
    content: '외국인 순매도 2008년 금융위기 62조\n2020년 코로나 25조\n현재 103조원 18일연속 순매도 역사적인 신기록중',
    chart: 'alert-box',
    likes: 89, comments: 18, shares: 12,
    commentsList: [
      { id: 1, user: '충격받음', avatar: '충', time: '5시간전', content: '103조?? 이게 실화인가요 진짜로??', likes: 34 },
      { id: 2, user: '역사적기록', avatar: '역', time: '4시간전', content: '역대 최장 순매도 기록이네요. 저도 기사 찾아봐야겠어요.', likes: 8 },
    ],
  },
  {
    id: 4,
    username: 'NVDA장기홀더', avatar: 'N', userType: 'user', color: '#76b900',
    time: '3시간전', category: '미국주식',
    title: 'NVIDIA Blackwell 수요 예상치 초과 — Q2 가이던스 대폭 상향',
    content: '방금 실적 발표 나왔습니다. 데이터센터 매출이 예상치를 30% 이상 초과했어요. EPS도 컨센서스 대비 크게 상회. 내일 프리마켓 올라갈 것 같습니다. 보유하시는 분들 축하드립니다!',
    chart: null,
    likes: 312, comments: 87, shares: 45,
    commentsList: [
      { id: 1, user: '엔비디아홀더', avatar: '엔', time: '2시간전', content: '드디어!!! 홀드한 보람이 있네요 ㅎㅎ 내일 기대됩니다', likes: 78 },
      { id: 2, user: '부러워요', avatar: '부', time: '2시간전', content: '저도 오늘 바로 매수해야겠어요. 지금 들어가도 늦지 않겠죠?', likes: 12 },
      { id: 3, user: 'AI투자자', avatar: 'A', time: '1시간전', content: 'Blackwell 수요가 이 정도면 내년 실적도 기대됩니다.', likes: 25 },
    ],
  },
  {
    id: 5,
    username: '삼전장기투자', avatar: '삼', userType: 'user', color: '#1428A0',
    time: '1시간전', category: '국내주식',
    title: '삼성전자 지금 추가 매수 타이밍일까요?',
    content: '317,000원인데... 52주 최저가 55,600원 기준으로 보면 아직 고점에 있는 것 같기도 하고. HBM 수주 기대감은 있는데 판단이 어렵습니다. 고수분들 의견 부탁드립니다!',
    chart: null,
    likes: 45, comments: 23, shares: 3,
    commentsList: [
      { id: 1, user: '전업투자자', avatar: '전', time: '50분전', content: 'PER 14배면 장기 관점에서 나쁘지 않은 가격입니다. 분할 매수 추천해요.', likes: 18 },
      { id: 2, user: '분산투자자', avatar: '분', time: '40분전', content: '분할 매수로 접근하는 게 리스크 관리 측면에서 좋습니다.', likes: 11 },
    ],
  },
  {
    id: 6,
    username: '따박배당', avatar: '배', userType: 'user', color: '#0f9f6e',
    time: '30분전', category: '배당투자',
    title: '고배당주 포트폴리오 올해 수익률 공개 (+18.4%)',
    content: '개인 포트폴리오 수익률 공개합니다.\n삼성전자 +2.4% (배당 포함)\nKB금융 +22.1%\nKT +15.8%\n한국전력 +31.2%\n미국 JEPI ETF +14.6%\n\n배당재투자 복리 효과가 정말 크네요!',
    chart: null,
    likes: 234, comments: 56, shares: 28,
    commentsList: [
      { id: 1, user: '배당초보', avatar: '배', time: '25분전', content: '대단하세요! 어떤 전략으로 종목 선정하셨나요?', likes: 22 },
      { id: 2, user: '배당고수', avatar: '고', time: '20분전', content: '한전이 이렇게 오를 줄은 몰랐어요. 좋은 성과 축하드려요!', likes: 15 },
    ],
  },
  {
    id: 7,
    username: '미국주식이야기', avatar: '미', userType: 'channel', color: '#e58b10',
    time: '2시간전', category: '미국주식이야기',
    title: '🇺🇸 오늘의 미국 시장 요약 (06/05)',
    content: '• S&P500 -0.8% / NASDAQ -1.2%\n• NVIDIA +3.1% (실적 서프라이즈)\n• Apple -0.5% (iPhone 수요 우려)\n• 공포탐욕지수: 45 → 48 (중립)\n• 달러인덱스: 103.2 (+0.4%)',
    chart: null,
    likes: 445, comments: 89, shares: 67,
    commentsList: [
      { id: 1, user: '미장투자자', avatar: '미', time: '1시간전', content: 'NVDA 실적 너무 좋네요! 내일 한국 반도체주도 기대됩니다.', likes: 45 },
    ],
  },
])

// ===== 인기글 =====
const popularPosts = [
  { rank: 1, title: '현시점', likes: 1328, comments: 319 },
  { rank: 2, title: '1~5차 신규 집입 6차 5,000주 추가 합계 30,0...', likes: 361, comments: 311 },
  { rank: 3, title: '고등학생입니다. 라버리지로 1억을 만들었는데 알...', likes: 512, comments: 302 },
  { rank: 4, title: '음... 그간 종목잡아 수익보계하고 글올리...', likes: 521, comments: 294 },
  { rank: 5, title: '나스닥 빠른 전체적으로 양호한 하루네요 나스닥도...', likes: 372, comments: 212 },
  { rank: 6, title: '"결혼하면 돈 못 모른다?" 커뮤니티 썰이 숨기는 부...', likes: 386, comments: 158 },
  { rank: 7, title: '저기...혹시', likes: 643, comments: 92 },
  { rank: 8, title: '삼성전자 적청가 5만원', likes: 643, comments: 345 },
  { rank: 9, title: '어딜감히 떨어진다고 입을 놀리나!!', likes: 764, comments: 78 },
]

// ===== 주제별 커뮤니티 =====
const topicCommunities = [
  { icon: '🇺🇸', name: '미국주식이야기', members: '234.5K' },
  { icon: '🇰🇷', name: '국내주식토론', members: '189.2K' },
  { icon: '💰', name: '따박따박배당투자', members: '87.3K' },
  { icon: '📈', name: '주린이 질문방', members: '56.1K' },
  { icon: '🔥', name: '코인이야기', members: '145.8K' },
]

// ===== 필터링 =====
const filteredPosts = computed(() => {
  if (selectedCategory.value === '팔로잉') return posts.value.filter(p => followedUsers[p.username])
  if (selectedCategory.value === '뉴스') return posts.value.filter(p => p.userType === 'channel')
  return posts.value
})

// ===== 상호작용 함수 =====
function toggleLike(postId) {
  const post = posts.value.find(p => p.id === postId)
  if (!post) return
  if (likedPosts[postId]) {
    delete likedPosts[postId]
    post.likes--
  } else {
    likedPosts[postId] = true
    post.likes++
  }
}

function toggleFollow(username) {
  followedUsers[username] = !followedUsers[username]
}

function toggleComments(postId) {
  expandedPost.value = expandedPost.value === postId ? null : postId
}

function toggleCommentLike(postId, commentId) {
  const key = `${postId}-${commentId}`
  likedComments[key] = !likedComments[key]
}

function submitComment(postId) {
  const text = (commentInputs[postId] || '').trim()
  if (!text) return
  const post = posts.value.find(p => p.id === postId)
  if (!post) return
  post.commentsList.push({
    id: Date.now(),
    user: '김주만', avatar: '김',
    time: '방금', content: text, likes: 0,
  })
  post.comments++
  commentInputs[postId] = ''
}

// ===== 차트 SVG 헬퍼 =====
// 달러/원 환율 라인 차트 포인트
function exchangeRatePath(w, h) {
  const vals = [1200,1230,1210,1260,1290,1270,1310,1350,1330,1390,1420,1410,1460,1490,1520,1510,1545]
  const min = 1180, max = 1560, range = max - min, n = vals.length
  const pts = vals.map((v, i) => {
    const x = (i / (n - 1)) * w
    const y = h - 12 - ((v - min) / range) * (h - 28)
    return [x.toFixed(1), y.toFixed(1)]
  })
  const line = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x},${y}`).join(' ')
  const area = `${line} L${w},${h} L0,${h} Z`
  return { line, area }
}

// 코스피 외국인 순매도 막대 데이터
const koBarData = [
  -5174, -5100, 14000, -5100, -7221, 6002, -2225, -9210, 2460, -5222, 4214, -1342, 6219, -6195,
]
function koBarRect(vals, idx, w, h) {
  const maxAbs = Math.max(...vals.map(Math.abs))
  const barW = w / vals.length - 2
  const x = (idx / vals.length) * w + 1
  const v = vals[idx]
  const barH = (Math.abs(v) / maxAbs) * (h / 2 - 8)
  const y = v >= 0 ? h / 2 - barH : h / 2
  return { x, y, barW, barH, pos: v >= 0 }
}
</script>

<template>
  <div class="community-page">

    <!-- ===== 헤더 ===== -->
    <header class="cm-header">
      <h1>커뮤니티</h1>
      <div class="cm-header-right">
        <label class="cm-search">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="2"/>
            <path d="M13.5 13.5L17 17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <input type="search" placeholder="커뮤니티 검색" />
        </label>
        <button class="write-btn" @click="writeMode = !writeMode">
          <span>✏️</span> 글쓰기
        </button>
      </div>
    </header>

    <!-- ===== 글쓰기 바 ===== -->
    <div class="write-bar panel" :class="{ 'is-expanded': writeMode }">
      <div class="write-bar-inner">
        <div class="write-avatar">김</div>
        <input
          v-if="!writeMode"
          class="write-prompt"
          placeholder="오늘 시장 어떻게 보세요?"
          readonly
          @click="writeMode = true"
        />
        <textarea
          v-else
          v-model="writeText"
          class="write-textarea"
          placeholder="투자 인사이트를 공유해보세요..."
          rows="3"
          autofocus
        ></textarea>
      </div>
      <div class="write-bar-actions" v-if="writeMode">
        <div class="write-options">
          <button class="write-opt-btn">📷 사진</button>
          <button class="write-opt-btn">📊 차트</button>
          <button class="write-opt-btn">🏷️ 태그</button>
        </div>
        <div class="write-submit-row">
          <button class="write-cancel-btn" @click="writeMode = false; writeText = ''">취소</button>
          <button class="write-submit-btn" :disabled="!writeText.trim()">의견 남기기</button>
        </div>
      </div>
      <button v-else class="write-cta-btn">의견 남기기</button>
    </div>

    <!-- ===== 카테고리 탭 ===== -->
    <div class="cm-tabs">
      <button
        v-for="cat in categories"
        :key="cat"
        class="cm-tab"
        :class="{ 'is-active': selectedCategory === cat }"
        @click="selectedCategory = cat"
      >{{ cat }}</button>
    </div>

    <!-- ===== 메인 그리드 ===== -->
    <div class="cm-body">

      <!-- 피드 -->
      <div class="cm-feed">

        <!-- 팔로잉 탭에서 아무것도 없을 때 -->
        <div v-if="filteredPosts.length === 0" class="empty-feed">
          <span>👤</span>
          <p>팔로우한 채널의 글이 없습니다.<br>관심 있는 채널을 팔로우해보세요.</p>
        </div>

        <!-- 포스트 카드 -->
        <article
          v-for="post in filteredPosts"
          :key="post.id"
          class="post-card panel"
        >
          <!-- 포스트 헤더 -->
          <div class="post-header">
            <div class="post-author">
              <div class="post-avatar" :style="{ background: post.color }">{{ post.avatar }}</div>
              <div class="post-author-info">
                <div class="post-author-name-row">
                  <strong>{{ post.username }}</strong>
                  <span v-if="post.userType === 'channel'" class="channel-badge">채널</span>
                </div>
                <div class="post-meta-row">
                  <span class="post-time">{{ post.time }}</span>
                  <span class="post-dot">·</span>
                  <span class="post-category">{{ post.category }}</span>
                </div>
              </div>
            </div>
            <div class="post-header-actions">
              <button
                class="follow-btn"
                :class="{ 'is-following': followedUsers[post.username] }"
                @click="toggleFollow(post.username)"
              >
                {{ followedUsers[post.username] ? '팔로잉' : '팔로우' }}
              </button>
              <button class="more-btn">···</button>
            </div>
          </div>

          <!-- 포스트 내용 -->
          <div class="post-body">
            <h3 class="post-title">{{ post.title }}</h3>
            <p v-if="post.content" class="post-content" style="white-space: pre-line">{{ post.content }}</p>

            <!-- 달러환율 라인 차트 -->
            <div v-if="post.chart === 'exchange-rate'" class="post-chart-wrap">
              <div class="chart-label-row">
                <span class="chart-source">Bloomberg</span>
                <span class="chart-tag">달러/원 환율 추이</span>
              </div>
              <svg viewBox="0 0 480 180" preserveAspectRatio="none" class="post-chart-svg">
                <defs>
                  <linearGradient id="erGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="rgba(255,59,92,0.2)"/>
                    <stop offset="100%" stop-color="rgba(255,59,92,0)"/>
                  </linearGradient>
                </defs>
                <line v-for="y in [40,80,120,160]" :key="y" x1="0" :y1="y" x2="480" :y2="y"
                  stroke="rgba(180,200,255,0.2)" stroke-width="1" />
                <path :d="exchangeRatePath(480,180).area" fill="url(#erGrad)" />
                <path :d="exchangeRatePath(480,180).line" fill="none" stroke="#FF3B5C" stroke-width="2.5"
                  stroke-linecap="round" stroke-linejoin="round" />
                <!-- Y축 레이블 -->
                <text x="8" y="20" fill="rgba(150,170,200,0.8)" font-size="11">1,600</text>
                <text x="8" y="90" fill="rgba(150,170,200,0.8)" font-size="11">1,400</text>
                <text x="8" y="165" fill="rgba(150,170,200,0.8)" font-size="11">1,200</text>
                <!-- 현재가 라벨 -->
                <text x="420" y="22" fill="#FF3B5C" font-size="12" font-weight="900">1,545</text>
                <!-- 2009 표시 -->
                <text x="60" y="120" fill="rgba(255,255,255,0.5)" font-size="10">2009 금융위기</text>
                <line x1="80" y1="108" x2="80" y2="180" stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="3 3"/>
              </svg>
              <div class="chart-x-labels">
                <span>'98</span><span>'02</span><span>'06</span><span>'10</span>
                <span>'14</span><span>'18</span><span>'22</span><span>'25</span>
              </div>
            </div>

            <!-- 코스피 순매도 막대 차트 -->
            <div v-if="post.chart === 'kospi-bar'" class="post-chart-wrap">
              <div class="chart-label-row">
                <span class="chart-tag">외국인 코스피 순매도 추이</span>
                <span class="chart-source">단위: 억원</span>
              </div>
              <svg viewBox="0 0 480 160" preserveAspectRatio="none" class="post-chart-svg">
                <line x1="0" y1="80" x2="480" y2="80" stroke="rgba(180,200,255,0.4)" stroke-width="1"/>
                <g v-for="(val, i) in koBarData" :key="i">
                  <rect
                    :x="koBarRect(koBarData, i, 480, 160).x"
                    :y="koBarRect(koBarData, i, 480, 160).y"
                    :width="koBarRect(koBarData, i, 480, 160).barW"
                    :height="koBarRect(koBarData, i, 480, 160).barH"
                    :fill="koBarRect(koBarData, i, 480, 160).pos ? 'rgba(0,102,204,0.75)' : 'rgba(255,59,92,0.75)'"
                    rx="2"
                  />
                </g>
              </svg>
            </div>

            <!-- 알림 박스 차트 -->
            <div v-if="post.chart === 'alert-box'" class="alert-box">
              <div class="alert-row is-neg">
                <span class="alert-label">🚨 외국인 순매도</span>
                <strong>18일 연속 · -103조원</strong>
              </div>
              <div class="alert-row">
                <span class="alert-label">📊 2008 금융위기 당시</span>
                <strong>62조원</strong>
              </div>
              <div class="alert-row">
                <span class="alert-label">😷 2020년 코로나</span>
                <strong>25조원</strong>
              </div>
              <div class="alert-row is-warn">
                <span class="alert-label">⚠️ 현재 기록</span>
                <strong>역사적 신기록 진행중</strong>
              </div>
            </div>
          </div>

          <!-- 반응 바 -->
          <div class="post-reactions">
            <div class="reaction-left">
              <button
                class="reaction-btn like-btn"
                :class="{ 'is-liked': likedPosts[post.id] }"
                @click="toggleLike(post.id)"
              >
                <span class="like-icon">{{ likedPosts[post.id] ? '♥' : '♡' }}</span>
                <span class="reaction-count">{{ post.likes.toLocaleString() }}</span>
              </button>

              <button
                class="reaction-btn comment-btn"
                :class="{ 'is-active': expandedPost === post.id }"
                @click="toggleComments(post.id)"
              >
                <span>💬</span>
                <span class="reaction-count">{{ post.comments }}</span>
              </button>

              <button class="reaction-btn share-btn" @click="">
                <span>🔗</span>
                <span class="reaction-count">{{ post.shares }}</span>
              </button>
            </div>
            <button class="bookmark-btn">🔖</button>
          </div>

          <!-- ===== 댓글 섹션 ===== -->
          <Transition name="slide-down">
            <div v-if="expandedPost === post.id" class="comments-section">

              <!-- 댓글 입력 -->
              <div class="comment-input-row">
                <div class="comment-avatar cm-me">김</div>
                <div class="comment-input-wrap">
                  <input
                    :value="commentInputs[post.id]"
                    @input="commentInputs[post.id] = $event.target.value"
                    type="text"
                    class="comment-input"
                    placeholder="댓글을 입력하세요..."
                    @keydown.enter="submitComment(post.id)"
                  />
                  <button
                    class="comment-send-btn"
                    @click="submitComment(post.id)"
                    :disabled="!commentInputs[post.id]"
                  >전송</button>
                </div>
              </div>

              <!-- 댓글 목록 -->
              <div class="comments-list">
                <div
                  v-for="comment in post.commentsList"
                  :key="comment.id"
                  class="comment-item"
                >
                  <div class="comment-avatar">{{ comment.avatar }}</div>
                  <div class="comment-body">
                    <div class="comment-head">
                      <strong class="comment-user">{{ comment.user }}</strong>
                      <span class="comment-time">{{ comment.time }}</span>
                    </div>
                    <p class="comment-text">{{ comment.content }}</p>
                    <div class="comment-actions">
                      <button
                        class="comment-like-btn"
                        :class="{ 'is-liked': likedComments[`${post.id}-${comment.id}`] }"
                        @click="toggleCommentLike(post.id, comment.id)"
                      >
                        {{ likedComments[`${post.id}-${comment.id}`] ? '♥' : '♡' }}
                        {{ comment.likes + (likedComments[`${post.id}-${comment.id}`] ? 1 : 0) }}
                      </button>
                      <button class="comment-reply-btn">답글</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </article>
      </div>

      <!-- ===== 우측 사이드바 ===== -->
      <aside class="cm-sidebar">

        <!-- 주간 인기글 -->
        <div class="panel sidebar-panel">
          <div class="sidebar-head">
            <span>🔥</span>
            <h3>주간 인기글</h3>
          </div>

          <div class="popular-list">
            <div
              v-for="item in popularPosts"
              :key="item.rank"
              class="popular-item"
            >
              <span class="popular-rank" :class="item.rank <= 3 ? 'is-top' : ''">
                {{ item.rank }}
              </span>
              <div class="popular-info">
                <p class="popular-title">{{ item.title }}</p>
                <div class="popular-stats">
                  <span>♥ {{ item.likes.toLocaleString() }}</span>
                  <span>💬 {{ item.comments }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 주제별 커뮤니티 -->
        <div class="panel sidebar-panel">
          <div class="sidebar-head">
            <h3>주제별 커뮤니티</h3>
            <button class="text-btn">더보기 ›</button>
          </div>

          <div class="topic-list">
            <div
              v-for="topic in topicCommunities"
              :key="topic.name"
              class="topic-item"
            >
              <span class="topic-icon">{{ topic.icon }}</span>
              <div class="topic-info">
                <strong>{{ topic.name }}</strong>
                <span>멤버 {{ topic.members }}</span>
              </div>
              <button
                class="topic-join-btn"
                :class="{ 'is-joined': followedUsers[topic.name] }"
                @click="toggleFollow(topic.name)"
              >
                {{ followedUsers[topic.name] ? '참여중' : '참여' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 실시간 태그 -->
        <div class="panel sidebar-panel">
          <div class="sidebar-head">
            <h3>실시간 태그</h3>
          </div>
          <div class="tag-cloud">
            <span v-for="tag in ['#환율', '#달러', '#삼성전자', '#NVIDIA', '#코스피폭락', '#외국인순매도', '#HBM', '#배당주', '#반도체', '#AI주식']"
              :key="tag" class="tag-chip">{{ tag }}</span>
          </div>
        </div>

      </aside>
    </div>

  </div>
</template>

<style scoped>
/* ===== 페이지 ===== */
.community-page { display: flex; flex-direction: column; gap: 16px; }

/* ===== 헤더 ===== */
.cm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.cm-header h1 {
  font-size: clamp(28px, 4vw, 42px);
  font-weight: 900;
  color: var(--ink);
  letter-spacing: -1.5px;
  margin: 0;
}

.cm-header-right { display: flex; align-items: center; gap: 10px; }

.cm-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  height: 36px;
  border-radius: 999px;
  background: rgba(255,255,255,0.62);
  border: 1px solid var(--glass-border);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  color: var(--faint);
  cursor: text;
}

.cm-search input {
  border: 0;
  background: transparent;
  outline: none;
  color: var(--ink);
  font-size: 13px;
  font-weight: 700;
  width: 160px;
}

.cm-search input::placeholder { color: var(--faint); }

.write-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 999px;
  border: 0;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(49,93,255,0.28);
  transition: opacity 0.18s, transform 0.18s;
}

.write-btn:hover { opacity: 0.88; transform: translateY(-1px); }

/* ===== 글쓰기 바 ===== */
.write-bar {
  padding: 14px 18px;
  transition: padding 0.2s;
}

.write-bar.is-expanded { padding: 18px 20px; }

.write-bar-inner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.write-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff; font-size: 14px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.write-prompt {
  flex: 1;
  height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.48);
  color: var(--faint);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  outline: none;
}

.write-textarea {
  flex: 1;
  padding: 12px 14px;
  border-radius: var(--radius);
  border: 1px solid rgba(49,93,255,0.3);
  background: rgba(255,255,255,0.55);
  color: var(--ink);
  font-size: 14px;
  font-weight: 700;
  outline: none;
  resize: none;
  line-height: 1.6;
}

.write-bar-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-left: 48px;
  flex-wrap: wrap;
  gap: 10px;
}

.write-options { display: flex; gap: 6px; }

.write-opt-btn {
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s;
}

.write-opt-btn:hover { background: rgba(255,255,255,0.75); color: var(--ink); }

.write-submit-row { display: flex; gap: 8px; }

.write-cancel-btn {
  padding: 7px 16px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.5);
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.write-submit-btn {
  padding: 7px 18px;
  border-radius: 999px;
  border: 0;
  background: var(--accent);
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: opacity 0.18s;
}

.write-submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.write-cta-btn {
  margin-left: auto;
  padding: 7px 18px;
  border-radius: 999px;
  border: 0;
  background: rgba(49,93,255,0.1);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s;
  display: block;
  margin-top: 8px;
}

.write-cta-btn:hover { background: rgba(49,93,255,0.18); }

/* ===== 카테고리 탭 ===== */
.cm-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(255,255,255,0.42);
  border: 1px solid var(--glass-border);
  width: fit-content;
}

.cm-tab {
  padding: 7px 22px;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.cm-tab.is-active {
  background: rgba(255,255,255,0.88);
  color: var(--ink);
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

/* ===== 메인 그리드 ===== */
.cm-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
  align-items: start;
}

/* ===== 빈 피드 ===== */
.empty-feed {
  padding: 60px 20px;
  text-align: center;
  color: var(--faint);
}

.empty-feed span { font-size: 36px; display: block; margin-bottom: 12px; }
.empty-feed p { font-size: 14px; font-weight: 700; line-height: 1.6; }

/* ===== 피드 ===== */
.cm-feed { display: flex; flex-direction: column; gap: 12px; }

/* ===== 포스트 카드 ===== */
.post-card { padding: 18px 20px; }

/* 포스트 헤더 */
.post-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.post-author { display: flex; align-items: center; gap: 10px; }

.post-avatar {
  width: 38px; height: 38px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 900; color: #fff;
  flex-shrink: 0;
}

.post-author-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.post-author-name-row strong {
  font-size: 14px;
  font-weight: 900;
  color: var(--ink);
}

.channel-badge {
  font-size: 10px;
  font-weight: 900;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(49,93,255,0.1);
  color: var(--accent);
}

.post-meta-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.post-time, .post-category { font-size: 11px; font-weight: 700; color: var(--faint); }
.post-dot { font-size: 11px; color: var(--faint); }

.post-header-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

/* 팔로우 버튼 */
.follow-btn {
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(49,93,255,0.3);
  background: rgba(49,93,255,0.07);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.18s, border-color 0.18s, color 0.18s;
  white-space: nowrap;
}

.follow-btn:hover { background: rgba(49,93,255,0.14); }

.follow-btn.is-following {
  background: rgba(255,255,255,0.62);
  border-color: var(--glass-border);
  color: var(--muted);
}

.more-btn {
  width: 28px; height: 28px;
  border: 0; background: transparent;
  color: var(--faint); font-size: 16px;
  cursor: pointer; border-radius: 50%;
  transition: background 0.14s;
}

.more-btn:hover { background: rgba(255,255,255,0.6); color: var(--ink); }

/* 포스트 바디 */
.post-body { margin-bottom: 14px; }

.post-title {
  font-size: 16px;
  font-weight: 900;
  color: var(--ink);
  margin: 0 0 8px;
  line-height: 1.4;
}

.post-content {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.6;
  word-break: keep-all;
}

/* 차트 */
.post-chart-wrap {
  border-radius: var(--radius);
  overflow: hidden;
  background: rgba(10,15,30,0.75);
  border: 1px solid rgba(255,255,255,0.08);
  padding: 10px 10px 4px;
  margin-top: 10px;
}

.chart-label-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 0 2px;
}

.chart-tag { font-size: 11px; font-weight: 700; color: rgba(200,220,255,0.7); }
.chart-source { font-size: 10px; font-weight: 700; color: rgba(200,220,255,0.4); }

.post-chart-svg {
  width: 100%;
  height: 150px;
}

.chart-x-labels {
  display: flex;
  justify-content: space-between;
  padding: 4px 2px 2px;
  font-size: 10px;
  font-weight: 700;
  color: rgba(150,170,200,0.6);
}

/* 알림 박스 */
.alert-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid var(--glass-border);
}

.alert-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(255,255,255,0.38);
  font-size: 13px;
  font-weight: 700;
}

.alert-row.is-neg { background: rgba(255,59,92,0.08); }
.alert-row.is-warn { background: rgba(229,139,16,0.08); }

.alert-label { color: var(--muted); }
.alert-row strong { color: var(--ink); font-size: 14px; }
.alert-row.is-neg strong { color: #FF3B5C; }
.alert-row.is-warn strong { color: #e58b10; }

/* ===== 반응 바 ===== */
.post-reactions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.reaction-left { display: flex; gap: 4px; }

.reaction-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.reaction-btn:hover { background: rgba(255,255,255,0.55); color: var(--ink); }

.reaction-btn.is-liked .like-icon { color: #FF3B5C; }
.reaction-btn.is-liked .reaction-count { color: #FF3B5C; }
.like-btn.is-liked { background: rgba(255,59,92,0.08); }
.like-btn.is-liked:hover { background: rgba(255,59,92,0.14); }

.reaction-btn.is-active { background: rgba(49,93,255,0.08); color: var(--accent); }

.like-icon { font-size: 16px; line-height: 1; }

.reaction-count { font-size: 13px; }

.bookmark-btn {
  width: 32px; height: 32px;
  border: 0; background: transparent;
  color: var(--faint); font-size: 16px;
  cursor: pointer; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.15s, color 0.15s;
}

.bookmark-btn:hover { background: rgba(255,255,255,0.55); color: var(--ink); }

/* ===== 댓글 섹션 ===== */
.comments-section {
  padding-top: 14px;
  border-top: 1px solid var(--line);
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.comment-avatar {
  width: 30px; height: 30px; border-radius: 50%;
  background: linear-gradient(135deg, #98a1b2, #7d8fa0);
  color: #fff; font-size: 12px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}

.comment-avatar.cm-me {
  background: linear-gradient(135deg, var(--accent), var(--purple));
}

.comment-input-wrap {
  display: flex;
  flex: 1;
  gap: 6px;
}

.comment-input {
  flex: 1;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255,255,255,0.52);
  color: var(--ink);
  font-size: 13px;
  font-weight: 700;
  outline: none;
  transition: border-color 0.18s;
}

.comment-input:focus { border-color: var(--accent); }

.comment-send-btn {
  padding: 0 14px;
  height: 36px;
  border-radius: 999px;
  border: 0;
  background: var(--accent);
  color: #fff;
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: opacity 0.18s;
}

.comment-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.comments-list { display: flex; flex-direction: column; gap: 10px; }

.comment-item { display: flex; gap: 10px; }

.comment-body { flex: 1; min-width: 0; }

.comment-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.comment-user { font-size: 13px; font-weight: 900; color: var(--ink); }
.comment-time { font-size: 11px; font-weight: 700; color: var(--faint); }

.comment-text {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.5;
  word-break: keep-all;
}

.comment-actions { display: flex; gap: 8px; align-items: center; }

.comment-like-btn {
  border: 0; background: transparent;
  color: var(--faint); font-size: 12px; font-weight: 900;
  cursor: pointer; padding: 3px 8px; border-radius: 999px;
  transition: background 0.14s, color 0.14s;
}

.comment-like-btn:hover { background: rgba(255,59,92,0.08); color: #FF3B5C; }
.comment-like-btn.is-liked { color: #FF3B5C; background: rgba(255,59,92,0.08); }

.comment-reply-btn {
  border: 0; background: transparent;
  color: var(--faint); font-size: 12px; font-weight: 900;
  cursor: pointer; padding: 3px 8px; border-radius: 999px;
  transition: background 0.14s, color 0.14s;
}

.comment-reply-btn:hover { background: rgba(255,255,255,0.5); color: var(--muted); }

/* ===== 댓글 애니메이션 ===== */
.slide-down-enter-active { transition: all 0.2s ease; }
.slide-down-leave-active { transition: all 0.16s ease; }
.slide-down-enter-from { opacity: 0; transform: translateY(-6px); }
.slide-down-leave-to { opacity: 0; transform: translateY(-4px); }

/* ===== 사이드바 ===== */
.cm-sidebar { display: flex; flex-direction: column; gap: 14px; position: sticky; top: 80px; }

.sidebar-panel { padding: 16px; }

.sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.sidebar-head span { font-size: 16px; }
.sidebar-head h3 { font-size: 14px; font-weight: 900; color: var(--ink); margin: 0; flex: 1; }

.text-btn {
  border: 0; background: transparent;
  color: var(--accent); font-size: 12px; font-weight: 900; cursor: pointer;
}

/* 인기글 */
.popular-list { display: flex; flex-direction: column; gap: 2px; }

.popular-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 7px 6px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.14s;
}

.popular-item:hover { background: rgba(255,255,255,0.48); }

.popular-rank {
  font-size: 13px;
  font-weight: 900;
  color: var(--faint);
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  margin-top: 1px;
}

.popular-rank.is-top { color: var(--accent); }

.popular-info { flex: 1; min-width: 0; }

.popular-title {
  margin: 0 0 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.popular-stats {
  display: flex;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  color: var(--faint);
}

/* 주제별 커뮤니티 */
.topic-list { display: flex; flex-direction: column; gap: 6px; }

.topic-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 6px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.14s;
}

.topic-item:hover { background: rgba(255,255,255,0.48); }

.topic-icon { font-size: 18px; flex-shrink: 0; }

.topic-info { flex: 1; min-width: 0; }
.topic-info strong { display: block; font-size: 13px; font-weight: 900; color: var(--ink); }
.topic-info span { font-size: 11px; font-weight: 700; color: var(--faint); }

.topic-join-btn {
  padding: 4px 12px;
  border-radius: 999px;
  border: 1px solid rgba(49,93,255,0.3);
  background: rgba(49,93,255,0.07);
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s;
  white-space: nowrap;
}

.topic-join-btn:hover { background: rgba(49,93,255,0.14); }

.topic-join-btn.is-joined {
  background: rgba(255,255,255,0.55);
  border-color: var(--glass-border);
  color: var(--muted);
}

/* 태그 클라우드 */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.48);
  border: 1px solid var(--glass-border);
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.14s, color 0.14s;
}

.tag-chip:hover {
  background: rgba(49,93,255,0.08);
  border-color: rgba(49,93,255,0.22);
  color: var(--accent);
}

/* ===== 반응형 ===== */
@media (max-width: 1100px) {
  .cm-body { grid-template-columns: 1fr; }
  .cm-sidebar { position: static; }
}

@media (max-width: 700px) {
  .write-bar-actions { flex-direction: column; align-items: flex-start; }
}
</style>
