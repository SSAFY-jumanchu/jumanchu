<script setup>
import { computed } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

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
        <div class="user-greeting">
          <div class="user-avatar">{{ user.initial }}</div>
          <span class="user-welcome">환영합니다 <strong>{{ user.name }}</strong></span>
        </div>
        <div class="user-actions">
          <button v-if="auth.isAuthenticated" class="user-btn" @click="handleLogout">로그아웃</button>
          <RouterLink v-else to="/login" class="user-btn">로그인</RouterLink>
          <button class="user-btn">회원정보수정</button>
          <RouterLink to="/mypage" class="user-btn accent">마이페이지</RouterLink>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topnav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-bottom: 1px solid var(--glass-border);
  box-shadow: 0 2px 20px rgba(60, 80, 200, 0.07), var(--glass-inset);
}

.topnav-inner {
  max-width: 1480px;
  margin: 0 auto;
  padding: 0 28px;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 28px;
}

.brand { display: flex; align-items: center; flex-shrink: 0; }

.brand-wordmark {
  font-size: 22px;
  font-weight: 900;
  letter-spacing: -1px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-links {
  display: flex;
  gap: 2px;
  flex: 1;
}

.nav-links a {
  min-height: 36px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  border-radius: var(--radius);
  color: var(--muted);
  font-size: 14px;
  font-weight: 800;
  transition: background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
}

.nav-links a:hover {
  background: rgba(255, 255, 255, 0.58);
  color: var(--ink);
}

.nav-links a.is-active {
  background: rgba(49, 93, 255, 0.12);
  color: var(--accent);
  border: 1px solid rgba(49, 93, 255, 0.2);
}

.user-area {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.user-greeting {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  color: #fff;
  font-size: 13px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(49, 93, 255, 0.3);
}

.user-welcome {
  color: var(--muted);
  font-size: 13px;
}

.user-welcome strong { color: var(--ink); }

.user-actions { display: flex; gap: 5px; }

.user-btn {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 11px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.52);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  transition: background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
  text-decoration: none;
}

.user-btn:hover {
  background: rgba(255, 255, 255, 0.78);
  color: var(--ink);
}

.user-btn.accent {
  background: rgba(49, 93, 255, 0.1);
  border-color: rgba(49, 93, 255, 0.28);
  color: var(--accent);
}

.user-btn.accent:hover {
  background: rgba(49, 93, 255, 0.18);
}

@media (max-width: 1100px) {
  .user-welcome { display: none; }
}

@media (max-width: 900px) {
  .topnav-inner { gap: 14px; padding: 0 16px; }
  .nav-links a { padding: 0 10px; font-size: 13px; }
}
</style>
