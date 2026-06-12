<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useTheme, THEMES } from '../composables/useTheme'

const navItems = [
  { to: '/', label: '홈' },
  { to: '/stocks', label: '주식 조회' },
  { to: '/watchlist', label: '관심 종목' },
  { to: '/holdings', label: '보유 종목' },
  { to: '/portfolio', label: '장투 케어' },
  { to: '/trading-diary', label: '매매 일기' },
  { to: '/community', label: '커뮤니티' },
]

const router = useRouter()
const auth = useAuthStore()
const { theme, setTheme } = useTheme()

const user = computed(() => {
  const name = auth.user?.nickname || '게스트'
  return { name, initial: name.charAt(0) }
})

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="topnav">
    <div class="topnav-inner">
      <RouterLink class="brand" to="/">
        <strong class="brand-wordmark">주만추</strong>
        <span class="brand-sub">Design Preview</span>
      </RouterLink>

      <nav class="nav-links" aria-label="주요 메뉴">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          active-class="is-active"
          exact-active-class="is-active"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="user-area">
        <div class="theme-switch" role="group" aria-label="테마 선택">
          <button
            v-for="t in THEMES"
            :key="t.id"
            class="theme-btn"
            :class="{ 'is-on': theme === t.id }"
            :title="t.label + ' 테마'"
            @click="setTheme(t.id)"
          >
            {{ t.icon }}
          </button>
        </div>

        <div class="user-actions">
          <button v-if="auth.isAuthenticated" class="user-btn" @click="handleLogout">로그아웃</button>
          <RouterLink v-else to="/login" class="user-btn">로그인</RouterLink>
          <RouterLink to="/mypage" class="user-btn accent">마이페이지</RouterLink>
        </div>
        <RouterLink to="/mypage" class="user-avatar" :title="user.name">{{ user.initial }}</RouterLink>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topnav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg);
  border-bottom: 1px solid var(--glass-border);
}

.topnav-inner {
  max-width: 1480px;
  margin: 0 auto;
  padding: 0 28px;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.brand {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1.1;
}

.brand-wordmark {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.brand-sub {
  font-size: 10px;
  color: var(--faint);
  letter-spacing: 0.04em;
}

.nav-links {
  display: flex;
  gap: 2px;
  flex: 1;
}

.nav-links a {
  min-height: 32px;
  display: flex;
  align-items: center;
  padding: 0 13px;
  border-radius: 999px;
  color: var(--muted);
  font-size: 13.5px;
  font-weight: 600;
  transition: background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
}

.nav-links a:hover {
  background: var(--glass-subtle);
  color: var(--ink);
}

/* Claude Design의 "Recent" 칩 — 활성 탭은 잉크색 필 */
.nav-links a.is-active {
  background: var(--ink);
  color: var(--bg);
}

.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.theme-switch {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--card);
}

.theme-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 0;
  background: transparent;
  font-size: 14px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.45;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.theme-btn:hover { opacity: 0.85; }

.theme-btn.is-on {
  background: var(--glass-subtle);
  opacity: 1;
  box-shadow: inset 0 0 0 1px var(--glass-border);
}

.user-actions { display: flex; gap: 5px; }

.user-btn {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--card);
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  transition: background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
  text-decoration: none;
}

.user-btn:hover {
  background: var(--glass-subtle);
  color: var(--ink);
}

.user-btn.accent {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.user-btn.accent:hover { filter: brightness(0.94); }

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--glass-subtle);
  border: 1px solid var(--glass-border);
  color: var(--ink);
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

@media (max-width: 1100px) {
  .user-actions { display: none; }
}

@media (max-width: 900px) {
  .topnav-inner { gap: 14px; padding: 0 16px; }
  .nav-links a { padding: 0 10px; font-size: 13px; }
  .brand-sub { display: none; }
}
</style>
