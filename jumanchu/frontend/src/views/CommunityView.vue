<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useFavoritesStore } from '../stores/favorites'
import { useRecentStocksStore } from '../stores/recentStocks'
import {
  fetchPosts, createPost, updatePost, deletePost, togglePostLike,
  fetchComments, createComment, toggleCommentLike as apiToggleCommentLike,
  followUser, unfollowUser, fetchFollowing,
} from '../api/community'
import { fetchStocks, fetchPopularRanking } from '../api/stocks'
import { fetchHoldings } from '../api/portfolio'

const router = useRouter()
const auth = useAuthStore()
const favStore = useFavoritesStore()
const recentStore = useRecentStocksStore()

// 현재 유저 이니셜(아바타) — 비로그인이면 '나'
const myInitial = computed(() => auth.user?.nickname?.slice(0, 1) || '나')

// 로그인 필요 액션 가드 — 비로그인이면 로그인으로
function requireAuth() {
  if (auth.isAuthenticated) return true
  router.push({ name: 'login', query: { redirect: '/community' } })
  return false
}

// 글 타입(enum) → 한글 라벨
const CATEGORY_LABEL = { QUESTION: '질문', REVIEW: '후기', ANALYSIS: '분석', SHARE: '공유' }
const CM_PALETTE = ['#315dff', '#7d4ee8', '#22c55e', '#f59e0b', '#06b6d4', '#ec4899']
function cmColor(id) {
  return CM_PALETTE[(Number(id) || 0) % CM_PALETTE.length]
}
function cmTimeAgo(iso) {
  if (!iso) return ''
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return '방금'
  if (diff < 3600) return `${Math.max(1, Math.round(diff / 60))}분전`
  if (diff < 86400) return `${Math.round(diff / 3600)}시간전`
  return `${Math.round(diff / 86400)}일전`
}
// 종목 코드(문자열) 기반 색상 — cmColor는 숫자 user_id용
function stockColor(code) {
  let h = 0
  for (const ch of String(code)) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return CM_PALETTE[h % CM_PALETTE.length]
}
function fmtRate(rate) {
  const up = Number(rate) >= 0
  return (up ? '+' : '') + Number(rate).toFixed(2) + '%'
}

// ===== 카테고리 탭 =====
const selectedCategory = ref('전체')
const categories = ['전체', '팔로잉', '관심 종목']

// 관심 종목 = 선호(favorite) 종목 + 보유 종목 코드
const holdingCodes = ref([])
const interestCodes = computed(() => {
  const set = new Set(favStore.items.map((s) => s.code))
  for (const c of holdingCodes.value) set.add(c)
  return set
})
const interestLoaded = ref(false)

async function loadHoldingCodes() {
  if (!auth.isAuthenticated) return
  try {
    const { items = [] } = await fetchHoldings()
    holdingCodes.value = items.map((it) => it.stock?.code).filter(Boolean)
  } catch {
    // 무시
  }
}

function selectTab(cat) {
  selectedCategory.value = cat
  if (cat === '관심 종목') loadInterestPosts()
}

// ===== 글쓰기 상태 (모든 글은 종목에 속함 → 종목 선택 필수) =====
const writeMode = ref(false)
const writeTitle = ref('')
const writeText = ref('')
const writeError = ref('')
const writing = ref(false)

// 종목 검색 드롭다운 (종목명 → 검색 → 선택)
const stockQuery = ref('')
const stockResults = ref([])
const selectedStock = ref(null)        // { code, name, market, sector }
const stockDropdownOpen = ref(false)
let stockSearchTimer = null
function onStockSearch() {
  selectedStock.value = null           // 다시 입력하면 선택 해제
  stockDropdownOpen.value = true
  clearTimeout(stockSearchTimer)
  const q = stockQuery.value.trim()
  if (!q) { stockResults.value = []; return }
  stockSearchTimer = setTimeout(async () => {
    try {
      const { items = [] } = await fetchStocks({ q, size: 8 })
      stockResults.value = items.map((s) => ({ code: s.code, name: s.name, market: s.market, sector: s.sector }))
    } catch {
      stockResults.value = []
    }
  }, 250)
}
function pickStock(s) {
  selectedStock.value = s
  stockQuery.value = s.name
  stockResults.value = []
  stockDropdownOpen.value = false
}

const canSubmitPost = computed(
  () => selectedStock.value && writeTitle.value.trim() && writeText.value.trim(),
)
function openWrite() {
  if (!requireAuth()) return
  writeMode.value = true
}
function cancelWrite() {
  writeMode.value = false
  writeTitle.value = ''
  writeText.value = ''
  writeError.value = ''
  stockQuery.value = ''
  stockResults.value = []
  selectedStock.value = null
  stockDropdownOpen.value = false
}
async function submitPost() {
  if (!requireAuth() || !canSubmitPost.value || writing.value) return
  writing.value = true
  writeError.value = ''
  try {
    const created = await createPost({
      stock_code: selectedStock.value.code,
      title: writeTitle.value.trim(),
      body: writeText.value.trim(),
    })
    posts.value.unshift(mapPost(created))
    cancelWrite()
  } catch (e) {
    writeError.value =
      e?.response?.data?.detail ||
      e?.response?.data?.stock_code?.[0] ||
      '작성에 실패했어요. 잠시 후 다시 시도해 주세요.'
  } finally {
    writing.value = false
  }
}

// ===== 글 ··· 메뉴 + 수정/삭제 (본인 글만) =====
const openMenuId = ref(null)
const editingId = ref(null)
const editTitle = ref('')
const editBody = ref('')
const editError = ref('')
const editSaving = ref(false)
function toggleMenu(postId) { openMenuId.value = openMenuId.value === postId ? null : postId }
function startEdit(post) {
  openMenuId.value = null
  editingId.value = post.id
  editTitle.value = post.title
  editBody.value = post.content || ''
  editError.value = ''
}
function cancelEdit() { editingId.value = null; editError.value = '' }
async function saveEdit(post) {
  if (!editTitle.value.trim() || !editBody.value.trim() || editSaving.value) return
  editSaving.value = true
  editError.value = ''
  try {
    const updated = await updatePost(post.id, { title: editTitle.value.trim(), body: editBody.value.trim() })
    post.title = updated.title
    post.content = updated.body
    editingId.value = null
  } catch (e) {
    editError.value = e?.response?.data?.detail || '수정에 실패했어요.'
  } finally {
    editSaving.value = false
  }
}
async function removePost(post) {
  openMenuId.value = null
  if (!window.confirm('이 글을 삭제할까요?')) return
  try {
    await deletePost(post.id)
    posts.value = posts.value.filter((p) => p.id !== post.id)
  } catch {
    // 무시
  }
}

// ===== 반응형 상태 =====
const likedPosts = reactive({})        // postId → true
const followedUserIds = reactive({})   // userId → true (팔로우 중)
const expandedPost = ref(null)
const likedComments = reactive({})     // `${postId}-${commentId}` → true
const commentInputs = reactive({})

// ===== 포스트 데이터 (실데이터: GET /posts/) =====
const posts = ref([])

// ===== 주간 인기글 (실데이터: GET /posts?sort=popular) =====
const popularPosts = ref([])
async function loadPopularPosts() {
  try {
    const { items = [] } = await fetchPosts({ sort: 'popular', size: 9 })
    popularPosts.value = items.map((p, i) => ({
      rank: i + 1,
      id: p.id,
      title: p.title,
      likes: p.like_count,
      comments: p.comment_count,
      stockCode: p.stock_code || '',
    }))
  } catch {
    // 무시
  }
}

// ===== 인기 종목 커뮤니티 (실데이터: 인기 종목 top 5) =====
const popularStockCommunities = ref([])
async function loadPopularStockCommunities() {
  try {
    const { items = [] } = await fetchPopularRanking({ market: 'all', sort: 'value', size: 5 })
    popularStockCommunities.value = items.map((it, i) => ({
      code: it.code,
      name: it.name,
      logo: (it.name || '?').slice(0, 2),
      color: stockColor(it.code),
      rate: fmtRate(it.change_rate),
      up: Number(it.change_rate) >= 0,
      hot: i < 2,
    }))
  } catch {
    // 무시
  }
}

// ===== 최근 조회한 주식 (실데이터: recentStocks 스토어) =====
const recentStockCommunities = computed(() =>
  recentStore.items.map((s) => ({
    code: s.code,
    name: s.name,
    logo: (s.name || '?').slice(0, 2),
    color: stockColor(s.code),
    time: cmTimeAgo(s.viewedAt),
  })),
)

function goStockCommunity(code) {
  router.push(`/stocks/${code}`)
}

// ===== 필터링 =====
const filteredPosts = computed(() => {
  if (selectedCategory.value === '팔로잉') return posts.value.filter(p => followedUserIds[p.userId])
  if (selectedCategory.value === '관심 종목') return posts.value.filter(p => interestCodes.value.has(p.stockCode))
  return posts.value
})

const isMyPost = (post) => auth.user?.id != null && post.userId === auth.user.id

// ===== 좋아요 =====
async function toggleLike(postId) {
  if (!requireAuth()) return
  const post = posts.value.find(p => p.id === postId)
  if (!post) return
  // 낙관적 업데이트 후 서버 응답으로 보정
  const wasLiked = !!likedPosts[postId]
  if (wasLiked) { delete likedPosts[postId]; post.likes-- }
  else { likedPosts[postId] = true; post.likes++ }
  try {
    const res = await togglePostLike(postId)
    if (res.liked) likedPosts[postId] = true
    else delete likedPosts[postId]
    post.likes = res.like_count
  } catch {
    // 실패 → 롤백
    if (wasLiked) { likedPosts[postId] = true; post.likes++ }
    else { delete likedPosts[postId]; post.likes-- }
  }
}

// ===== 팔로우 (POST/DELETE /users/:id/follow/) =====
async function toggleFollow(post) {
  if (!requireAuth() || isMyPost(post)) return
  const uid = post.userId
  const wasFollowing = !!followedUserIds[uid]
  if (wasFollowing) delete followedUserIds[uid]
  else followedUserIds[uid] = true
  try {
    if (wasFollowing) await unfollowUser(uid)
    else await followUser(uid)
  } catch {
    // 실패 → 롤백
    if (wasFollowing) followedUserIds[uid] = true
    else delete followedUserIds[uid]
  }
}

// ===== 댓글 =====
function mapComment(c) {
  return {
    id: c.id,
    user: c.nickname,
    avatar: (c.nickname || '?').slice(0, 1),
    time: cmTimeAgo(c.created_at),
    content: c.body,
    likes: 0,   // 목록 응답엔 like_count가 없어 0에서 시작 → 토글 시 서버 값으로 보정
  }
}

async function toggleComments(postId) {
  expandedPost.value = expandedPost.value === postId ? null : postId
  if (expandedPost.value !== postId) return
  const post = posts.value.find(p => p.id === postId)
  if (!post || post._commentsLoaded) return
  try {
    const { items = [] } = await fetchComments(postId)
    post.commentsList = items.map(mapComment)
    post._commentsLoaded = true
  } catch {
    // 무시
  }
}

async function toggleCommentLike(postId, commentId) {
  if (!requireAuth()) return
  const key = `${postId}-${commentId}`
  const post = posts.value.find(p => p.id === postId)
  const comment = post?.commentsList.find(c => c.id === commentId)
  const wasLiked = !!likedComments[key]
  likedComments[key] = !wasLiked
  if (comment) comment.likes += wasLiked ? -1 : 1
  try {
    const res = await apiToggleCommentLike(commentId)
    likedComments[key] = res.liked
    if (comment) comment.likes = res.like_count
  } catch {
    likedComments[key] = wasLiked
    if (comment) comment.likes += wasLiked ? 1 : -1
  }
}

async function submitComment(postId) {
  if (!requireAuth()) return
  const text = (commentInputs[postId] || '').trim()
  if (!text) return
  const post = posts.value.find(p => p.id === postId)
  if (!post) return
  try {
    const c = await createComment(postId, text)
    post.commentsList.push(mapComment(c))
    post.comments++
    commentInputs[postId] = ''
  } catch {
    // 무시
  }
}

// ===== 글 목록 로딩 (실데이터) =====
const loadError = ref('')
function mapPost(p) {
  return {
    id: p.id,
    userId: p.user_id,
    username: p.nickname,
    avatar: (p.nickname || '?').slice(0, 1),
    color: cmColor(p.user_id),
    time: cmTimeAgo(p.created_at),
    createdAt: p.created_at,
    stockCode: p.stock_code || '',
    stockName: p.stock_name || '',
    category: CATEGORY_LABEL[p.category] || '',
    title: p.title,
    content: p.body,
    likes: p.like_count,
    comments: p.comment_count,
    commentsList: [],
    _commentsLoaded: false,
  }
}
// 새 글들을 posts에 병합(중복 id 제외) 후 최신순 정렬 — 좋아요/댓글 등이 단일 배열에서 동작
function mergePosts(items) {
  const existing = new Set(posts.value.map((p) => p.id))
  for (const it of items) {
    if (existing.has(it.id)) continue
    posts.value.push(mapPost(it))
    if (it.is_liked) likedPosts[it.id] = true
    existing.add(it.id)
  }
  posts.value.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
}
async function loadPosts() {
  try {
    const { items = [] } = await fetchPosts({ sort: 'latest', size: 20 })
    posts.value = items.map(mapPost)
    for (const it of items) if (it.is_liked) likedPosts[it.id] = true
  } catch (e) {
    loadError.value = e?.response?.data?.detail || '글을 불러오지 못했어요.'
  }
}
// 관심 종목(선호+보유) 종목별 글을 모아 병합 (탭 첫 진입 시 1회)
async function loadInterestPosts() {
  if (interestLoaded.value) return
  interestLoaded.value = true
  const codes = [...interestCodes.value].slice(0, 10)   // 외부 호출 폭주 방지
  if (!codes.length) return
  try {
    const results = await Promise.all(
      codes.map((code) =>
        fetchPosts({ stock_code: code, sort: 'latest', size: 10 }).catch(() => ({ items: [] })),
      ),
    )
    for (const r of results) mergePosts(r.items || [])
  } catch {
    // 무시
  }
}
// 내가 팔로우 중인 유저 id 집합 (팔로우 버튼 초기 상태)
async function loadFollowing() {
  if (!auth.isAuthenticated || auth.user?.id == null) return
  try {
    const { items = [] } = await fetchFollowing(auth.user.id)
    for (const u of items) followedUserIds[u.user_id] = true
  } catch {
    // 무시
  }
}
onMounted(() => {
  loadPosts()
  loadFollowing()
  loadHoldingCodes()
  loadPopularPosts()
  loadPopularStockCommunities()
})
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
        <button class="write-btn" @click="openWrite">
          <span>✏️</span> 글쓰기
        </button>
      </div>
    </header>

    <!-- ===== 글쓰기 바 (모든 글은 종목에 속함) ===== -->
    <div class="write-bar panel" :class="{ 'is-expanded': writeMode }">
      <div class="write-bar-inner">
        <div class="write-avatar">{{ myInitial }}</div>
        <input
          v-if="!writeMode"
          class="write-prompt"
          placeholder="오늘 시장 어떻게 보세요?"
          readonly
          @click="openWrite"
        />
        <div v-else class="write-form">
          <div class="write-fields">
            <!-- 종목명 검색 → 드롭다운에서 선택 -->
            <div class="stock-search-wrap">
              <input
                v-model="stockQuery"
                class="write-field"
                :class="{ 'is-picked': selectedStock }"
                placeholder="종목명 검색 (예: 삼성전자, NVIDIA)"
                @focus="stockDropdownOpen = true"
                @blur="stockDropdownOpen = false"
                @input="onStockSearch"
              />
              <span v-if="selectedStock" class="stock-pick-badge">{{ selectedStock.code }}</span>
              <div v-if="stockDropdownOpen && stockResults.length" class="stock-dropdown">
                <button
                  v-for="s in stockResults"
                  :key="s.code"
                  type="button"
                  class="stock-dd-row"
                  @mousedown.prevent="pickStock(s)"
                >
                  <span class="stock-dd-name">{{ s.name }}</span>
                  <span class="stock-dd-meta">{{ s.market }} · {{ s.code }}</span>
                </button>
              </div>
            </div>
            <input v-model="writeTitle" class="write-field" placeholder="제목" />
          </div>
          <textarea
            v-model="writeText"
            class="write-textarea"
            placeholder="투자 인사이트를 공유해보세요..."
            rows="3"
          ></textarea>
        </div>
      </div>
      <div class="write-bar-actions" v-if="writeMode">
        <span class="write-error">{{ writeError }}</span>
        <div class="write-submit-row">
          <button class="write-cancel-btn" @click="cancelWrite">취소</button>
          <button
            class="write-submit-btn"
            :disabled="!canSubmitPost || writing"
            @click="submitPost"
          >{{ writing ? '게시 중…' : '게시하기' }}</button>
        </div>
      </div>
      <button v-else class="write-cta-btn" @click="openWrite">의견 남기기</button>
    </div>

    <!-- ===== 카테고리 탭 ===== -->
    <div class="cm-tabs">
      <button
        v-for="cat in categories"
        :key="cat"
        class="cm-tab"
        :class="{ 'is-active': selectedCategory === cat }"
        @click="selectTab(cat)"
      >{{ cat }}</button>
    </div>

    <!-- ===== 메인 그리드 ===== -->
    <div class="cm-body">

      <!-- 피드 -->
      <div class="cm-feed">

        <!-- 비어 있을 때 -->
        <div v-if="filteredPosts.length === 0" class="empty-feed">
          <span>{{ selectedCategory === '팔로잉' ? '👤' : selectedCategory === '관심 종목' ? '⭐' : '📝' }}</span>
          <p v-if="loadError">{{ loadError }}</p>
          <p v-else-if="selectedCategory === '팔로잉'">팔로우한 사람의 글이 없습니다.<br>관심 있는 작성자를 팔로우해보세요.</p>
          <p v-else-if="selectedCategory === '관심 종목'">선호·보유 종목에 대한 글이 없습니다.<br>종목을 담거나 보유하면 관련 글이 모여요.</p>
          <p v-else>아직 글이 없습니다.<br>첫 글을 남겨보세요!</p>
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
                </div>
                <div class="post-meta-row">
                  <button
                    v-if="post.stockName"
                    type="button"
                    class="post-stock-chip"
                    @click="goStockCommunity(post.stockCode)"
                  >📈 {{ post.stockName }}</button>
                  <span class="post-time">{{ post.time }}</span>
                  <template v-if="post.category">
                    <span class="post-dot">·</span>
                    <span class="post-category">{{ post.category }}</span>
                  </template>
                </div>
              </div>
            </div>
            <div class="post-header-actions">
              <button
                v-if="!isMyPost(post)"
                class="follow-btn"
                :class="{ 'is-following': followedUserIds[post.userId] }"
                @click="toggleFollow(post)"
              >
                {{ followedUserIds[post.userId] ? '팔로잉' : '팔로우' }}
              </button>
              <!-- ··· 메뉴: 본인 글에만 (수정/삭제) -->
              <div v-if="isMyPost(post)" class="post-menu-wrap">
                <button class="more-btn" @click.stop="toggleMenu(post.id)">···</button>
                <template v-if="openMenuId === post.id">
                  <div class="menu-backdrop" @click="openMenuId = null"></div>
                  <div class="post-menu">
                    <button class="post-menu-item" @click="startEdit(post)">✏️ 수정</button>
                    <button class="post-menu-item is-danger" @click="removePost(post)">🗑️ 삭제</button>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- 포스트 내용 -->
          <div class="post-body">
            <template v-if="editingId === post.id">
              <input v-model="editTitle" class="edit-field" placeholder="제목" />
              <textarea v-model="editBody" class="edit-textarea" rows="4" placeholder="내용"></textarea>
              <span v-if="editError" class="write-error">{{ editError }}</span>
              <div class="edit-actions">
                <button class="write-cancel-btn" @click="cancelEdit">취소</button>
                <button
                  class="write-submit-btn"
                  :disabled="!editTitle.trim() || !editBody.trim() || editSaving"
                  @click="saveEdit(post)"
                >{{ editSaving ? '저장 중…' : '저장' }}</button>
              </div>
            </template>
            <template v-else>
              <h3 class="post-title">{{ post.title }}</h3>
              <p v-if="post.content" class="post-content" style="white-space: pre-line">{{ post.content }}</p>
            </template>
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
            </div>
            <button class="bookmark-btn">🔖</button>
          </div>

          <!-- ===== 댓글 섹션 ===== -->
          <Transition name="slide-down">
            <div v-if="expandedPost === post.id" class="comments-section">

              <!-- 댓글 입력 -->
              <div class="comment-input-row">
                <div class="comment-avatar cm-me">{{ myInitial }}</div>
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
                        {{ comment.likes }}
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
              :key="item.id"
              class="popular-item"
              @click="item.stockCode && goStockCommunity(item.stockCode)"
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
            <p v-if="!popularPosts.length" class="sidebar-empty">아직 인기글이 없어요.</p>
          </div>
        </div>

        <!-- 현재 인기 종목 커뮤니티 -->
        <div class="panel sidebar-panel">
          <div class="sidebar-head">
            <span>🔥</span>
            <h3>인기 종목 커뮤니티</h3>
          </div>
          <div class="stock-comm-list">
            <button
              v-for="s in popularStockCommunities"
              :key="s.code"
              type="button"
              class="stock-comm-item"
              @click="goStockCommunity(s.code)"
            >
              <span class="stock-comm-logo" :style="{ background: s.color }">{{ s.logo }}</span>
              <div class="stock-comm-info">
                <strong>{{ s.name }}<span v-if="s.hot" class="hot-tag">HOT</span></strong>
                <span class="sc-rate" :class="s.up ? 'sc-up' : 'sc-down'">{{ s.rate }}</span>
              </div>
              <span class="stock-comm-go">→</span>
            </button>
            <p v-if="!popularStockCommunities.length" class="sidebar-empty">불러오는 중…</p>
          </div>
        </div>

        <!-- 최근 조회한 주식 커뮤니티 -->
        <div class="panel sidebar-panel">
          <div class="sidebar-head">
            <span>🕘</span>
            <h3>최근 조회한 주식</h3>
          </div>
          <div class="stock-comm-list">
            <button
              v-for="s in recentStockCommunities"
              :key="s.code + s.time"
              type="button"
              class="stock-comm-item"
              @click="goStockCommunity(s.code)"
            >
              <span class="stock-comm-logo" :style="{ background: s.color }">{{ s.logo }}</span>
              <div class="stock-comm-info">
                <strong>{{ s.name }}</strong>
                <span>{{ s.time }} 조회 · 토론방 가기</span>
              </div>
              <span class="stock-comm-go">→</span>
            </button>
            <p v-if="!recentStockCommunities.length" class="sidebar-empty">최근 조회한 종목이 없어요.</p>
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
  background: var(--glass);
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
  box-shadow: 0 4px 12px rgba(var(--accent-rgb),0.28);
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
  background: var(--surface-soft);
  color: var(--faint);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  outline: none;
}

.write-form { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.write-fields { display: flex; gap: 8px; flex-wrap: wrap; }
.write-field {
  flex: 1;
  min-width: 140px;
  height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  color: var(--ink);
  font-size: 13px;
  font-weight: 700;
  outline: none;
  transition: border-color 0.18s;
}
.write-field:focus { border-color: var(--accent); }
.write-field::placeholder { color: var(--faint); }

/* 종목명 검색 드롭다운 */
.stock-search-wrap { position: relative; flex: 1; min-width: 140px; display: flex; }
.stock-search-wrap .write-field { flex: 1; padding-right: 64px; }
.write-field.is-picked { border-color: var(--accent); }
.stock-pick-badge {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  pointer-events: none;
}
.stock-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 30;
  padding: 6px;
  border-radius: var(--radius);
  background: var(--glass);
  border: 1px solid var(--glass-border);
  box-shadow: 0 16px 40px rgba(17, 24, 39, 0.16);
  max-height: 280px;
  overflow-y: auto;
}
.stock-dd-row {
  display: flex;
  flex-direction: column;
  gap: 1px;
  width: 100%;
  padding: 9px 10px;
  border: 0;
  border-radius: calc(var(--radius) - 2px);
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background 0.14s;
}
.stock-dd-row:hover { background: var(--surface-soft); }
.stock-dd-name { font-size: 13px; font-weight: 900; color: var(--ink); }
.stock-dd-meta { font-size: 11px; font-weight: 700; color: var(--faint); }

.write-textarea {
  flex: 1;
  padding: 12px 14px;
  border-radius: var(--radius);
  border: 1px solid rgba(var(--accent-rgb),0.3);
  background: var(--surface-soft);
  color: var(--ink);
  font-size: 14px;
  font-weight: 700;
  outline: none;
  resize: none;
  line-height: 1.6;
}

.write-error { font-size: 12px; font-weight: 800; color: var(--negative); }

.write-bar-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-left: 48px;
  flex-wrap: wrap;
  gap: 10px;
}

.write-submit-row { display: flex; gap: 8px; }

.write-cancel-btn {
  padding: 7px 16px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
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
  background: rgba(var(--accent-rgb),0.1);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.16s;
  display: block;
  margin-top: 8px;
}

.write-cta-btn:hover { background: rgba(var(--accent-rgb),0.18); }

/* ===== 카테고리 탭 ===== */
.cm-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: var(--glass-subtle);
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
  background: var(--chip-active);
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

.post-meta-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.post-time, .post-category { font-size: 11px; font-weight: 700; color: var(--faint); }
.post-dot { font-size: 11px; color: var(--faint); }

/* 종목 칩 (작성 글의 종목 정보) */
.post-stock-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 9px;
  border-radius: 999px;
  border: 1px solid rgba(var(--accent-rgb), 0.2);
  background: rgba(var(--accent-rgb), 0.08);
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.14s;
}
.post-stock-chip:hover { background: rgba(var(--accent-rgb), 0.16); }

.post-header-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

/* ··· 메뉴 (본인 글) */
.post-menu-wrap { position: relative; }
.menu-backdrop { position: fixed; inset: 0; z-index: 40; }
.post-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 41;
  min-width: 120px;
  padding: 6px;
  border-radius: var(--radius);
  background: var(--glass);
  border: 1px solid var(--glass-border);
  box-shadow: 0 14px 36px rgba(17, 24, 39, 0.18);
}
.post-menu-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  border: 0;
  border-radius: calc(var(--radius) - 2px);
  background: transparent;
  color: var(--ink);
  font-size: 13px;
  font-weight: 800;
  text-align: left;
  cursor: pointer;
  transition: background 0.14s;
}
.post-menu-item:hover { background: var(--surface-soft); }
.post-menu-item.is-danger { color: var(--negative); }
.post-menu-item.is-danger:hover { background: rgba(207, 61, 61, 0.08); }

/* 인라인 수정 폼 */
.edit-field {
  width: 100%;
  height: 40px;
  padding: 0 14px;
  margin-bottom: 8px;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  color: var(--ink);
  font-size: 15px;
  font-weight: 800;
  outline: none;
}
.edit-textarea {
  width: 100%;
  padding: 12px 14px;
  border-radius: var(--radius);
  border: 1px solid rgba(var(--accent-rgb), 0.3);
  background: var(--surface-soft);
  color: var(--ink);
  font-size: 14px;
  font-weight: 700;
  line-height: 1.6;
  outline: none;
  resize: vertical;
}
.edit-field:focus, .edit-textarea:focus { border-color: var(--accent); }
.edit-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 10px; }

/* 팔로우 버튼 */
.follow-btn {
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(var(--accent-rgb),0.3);
  background: rgba(var(--accent-rgb),0.07);
  color: var(--accent);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
  transition: background 0.18s, border-color 0.18s, color 0.18s;
  white-space: nowrap;
}

.follow-btn:hover { background: rgba(var(--accent-rgb),0.14); }

.follow-btn.is-following {
  background: var(--glass);
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

.more-btn:hover { background: var(--glass); color: var(--ink); }

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

.reaction-btn:hover { background: var(--surface-soft); color: var(--ink); }

.reaction-btn.is-liked .like-icon { color: #FF3B5C; }
.reaction-btn.is-liked .reaction-count { color: #FF3B5C; }
.like-btn.is-liked { background: rgba(255,59,92,0.08); }
.like-btn.is-liked:hover { background: rgba(255,59,92,0.14); }

.reaction-btn.is-active { background: rgba(var(--accent-rgb),0.08); color: var(--accent); }

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

.bookmark-btn:hover { background: var(--surface-soft); color: var(--ink); }

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
  background: var(--surface-soft);
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

.comment-reply-btn:hover { background: var(--surface-soft); color: var(--muted); }

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

.popular-item:hover { background: var(--surface-soft); }

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

/* 종목 커뮤니티 바로가기 */
.stock-comm-list { display: flex; flex-direction: column; gap: 4px; }

.stock-comm-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 6px;
  border: 0;
  background: transparent;
  border-radius: var(--radius);
  cursor: pointer;
  text-align: left;
  transition: background 0.14s;
}

.stock-comm-item:hover { background: var(--surface-soft); }

.stock-comm-logo {
  width: 32px; height: 32px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 12px; font-weight: 900; flex-shrink: 0;
}

.stock-comm-info { flex: 1; min-width: 0; }
.stock-comm-info strong {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 900; color: var(--ink);
}
.stock-comm-info span { font-size: 11px; font-weight: 700; color: var(--faint); }

.hot-tag {
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255,59,92,0.12);
  color: #ff3b5c;
  font-size: 9px;
  font-weight: 900;
}

.stock-comm-go { color: var(--faint); font-size: 15px; font-weight: 900; flex-shrink: 0; }
.stock-comm-item:hover .stock-comm-go { color: var(--accent); }

/* 인기 종목 등락률 (상승=빨강/하락=파랑) */
.sc-rate.sc-up { color: var(--krx-up); }
.sc-rate.sc-down { color: var(--krx-down); }

/* 사이드바 빈 상태 */
.sidebar-empty { margin: 6px; padding: 12px 6px; text-align: center; font-size: 12px; font-weight: 700; color: var(--faint); }

/* ===== 반응형 ===== */
@media (max-width: 1100px) {
  .cm-body { grid-template-columns: 1fr; }
  .cm-sidebar { position: static; }
}

@media (max-width: 700px) {
  .write-bar-actions { flex-direction: column; align-items: flex-start; }
}
</style>
