<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useFavoritesStore } from '../stores/favorites'
import { fetchEconomyNews, fetchInterestNews } from '../api/news'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const favStore = useFavoritesStore()

const TABS = [
  { key: 'general', label: '종합 뉴스' },
  { key: 'watchlist', label: '관심 종목 뉴스' },
]
const tab = ref(route.query.tab === 'watchlist' ? 'watchlist' : 'general')

// 탭별 독립 상태 — 한쪽 로딩/에러가 다른 쪽에 새지 않게 분리
const state = reactive({
  general: { items: [], loaded: false, loading: false, error: '' },
  watchlist: { items: [], loaded: false, loading: false, error: '' },
})
const cur = computed(() => state[tab.value])

function timeAgo(iso) {
  if (!iso) return ''
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 3600) return `${Math.max(1, Math.round(diff / 60))}분 전`
  if (diff < 86400) return `${Math.round(diff / 3600)}시간 전`
  return `${Math.round(diff / 86400)}일 전`
}

async function loadGeneral() {
  const st = state.general
  st.loading = true
  st.error = ''
  try {
    const { items = [] } = await fetchEconomyNews({ limit: 30 })
    st.items = items.map((n) => ({
      title: n.title,
      source: n.source,
      url: n.url || '',
      time: timeAgo(n.published_at),
      label: (n.sectors?.[0]?.sector ?? n.sectors?.[0]) || n.categories?.[0] || '경제',
    }))
  } catch {
    st.error = '뉴스를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.'
  } finally {
    st.loading = false
    st.loaded = true
  }
}

// 관심 종목 뉴스 = 보유 종목 뉴스 + 선호(스와이핑 저장) 종목 뉴스
async function loadWatchlist() {
  const st = state.watchlist
  st.loading = true
  st.error = ''
  try {
    const codes = favStore.items.map((s) => s.code)
    const items = await fetchInterestNews(codes, { limit: 30, withHoldings: auth.isAuthenticated })
    st.items = items.map((n) => ({
      title: n.title,
      source: n.source,
      url: n.url || '',
      time: timeAgo(n.published_at),
      label: n.stock?.name ?? '',
    }))
  } catch {
    st.error = '관심 종목 뉴스를 불러오지 못했어요.'
  } finally {
    st.loading = false
    st.loaded = true
  }
}

function ensureLoaded(t) {
  const st = state[t]
  if (st.loaded || st.loading) return
  if (t === 'general') loadGeneral()
  else loadWatchlist()
}

function selectTab(key) {
  if (tab.value === key) return
  tab.value = key
  router.replace({ query: { tab: key } })
  ensureLoaded(key)
}

onMounted(() => ensureLoaded(tab.value))
</script>

<template>
  <div class="news-page">
    <header class="nv-header">
      <h1>뉴스</h1>
      <p class="nv-sub">관심 있는 소식을 한눈에 모아보세요.</p>
    </header>

    <!-- 종합 / 관심 종목 토글 -->
    <div class="nv-tabs" role="tablist" aria-label="뉴스 종류">
      <button
        v-for="t in TABS"
        :key="t.key"
        type="button"
        role="tab"
        class="nv-tab"
        :class="{ 'is-active': tab === t.key }"
        :aria-selected="tab === t.key"
        @click="selectTab(t.key)"
      >
        {{ t.label }}
      </button>
    </div>

    <section class="panel nv-panel" aria-live="polite">
      <p v-if="cur.loading" class="nv-empty">불러오는 중…</p>
      <p v-else-if="cur.error" class="nv-empty nv-error">{{ cur.error }}</p>
      <p v-else-if="!cur.items.length" class="nv-empty">
        {{ tab === 'watchlist' ? '보유 종목이나 관심 종목을 담으면 관련 뉴스를 모아드려요.' : '표시할 뉴스가 없어요.' }}
      </p>

      <div v-else class="nv-list">
        <a
          v-for="(item, i) in cur.items"
          :key="item.url || item.title + i"
          class="nv-item"
          :href="item.url || undefined"
          :target="item.url ? '_blank' : undefined"
          rel="noopener"
        >
          <div class="nv-meta">
            <span class="nv-chip" :class="{ 'is-ticker': tab === 'watchlist' }">{{ item.label }}</span>
            <span class="nv-time">{{ item.time }}</span>
          </div>
          <h3 class="nv-title">{{ item.title }}</h3>
          <span class="nv-src">{{ item.source }}</span>
        </a>
      </div>
    </section>
  </div>
</template>

<style scoped>
.news-page { display: flex; flex-direction: column; gap: 16px; }

/* 헤더 */
.nv-header { padding: 4px 2px; }
.nv-header h1 { font-size: 24px; font-weight: 900; color: var(--ink); margin: 0; letter-spacing: -0.5px; }
.nv-sub { margin: 6px 0 0; font-size: 14px; font-weight: 600; color: var(--muted); }

/* 토글 */
.nv-tabs {
  display: inline-flex;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: var(--surface-soft);
  border: 1px solid var(--glass-border);
  align-self: flex-start;
}
.nv-tab {
  min-height: 36px;
  padding: 0 18px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
}
.nv-tab:hover { color: var(--ink); }
.nv-tab.is-active {
  background: var(--accent);
  color: #fff;
}

/* 리스트 */
.nv-panel { padding: 8px 12px; }
.nv-list { display: grid; gap: 2px; }
.nv-item {
  display: block;
  padding: 16px 12px;
  border-radius: calc(var(--radius) - 2px);
  border-bottom: 1px solid var(--line);
  text-decoration: none;
  color: inherit;
  transition: background 0.15s ease;
}
.nv-item:last-child { border-bottom: 0; }
.nv-item:hover { background: var(--surface-soft); }

.nv-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.nv-chip {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 900;
  background: rgba(var(--accent-rgb), 0.1);
  color: var(--accent);
  border: 1px solid rgba(var(--accent-rgb), 0.2);
}
.nv-chip.is-ticker {
  background: rgba(var(--purple-rgb), 0.1);
  color: var(--purple);
  border-color: rgba(var(--purple-rgb), 0.2);
}
.nv-time { color: var(--faint); font-size: 11px; font-weight: 700; margin-left: auto; }
.nv-title {
  color: var(--ink);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
  margin: 0 0 5px;
  word-break: keep-all;
}
.nv-src { color: var(--faint); font-size: 12px; font-weight: 700; }

/* 빈 상태 */
.nv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--muted);
  font-size: 14px;
  font-weight: 700;
  text-align: center;
}
.nv-empty.nv-error { color: var(--negative); }
</style>
