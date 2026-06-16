<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// 상단 네비 메뉴 (와이어프레임-마이페이지.pptx 기준)
const navItems = [
  { to: '/', label: '홈' },
  { to: '/stocks', label: '주식 조회' },
  { to: '/discover', label: '관심 종목' },
  { to: '/portfolio', label: '보유 종목' },
  { to: '/diary', label: '매매일기' },
  { to: '/care', label: '장투 케어' },
  { to: '/community', label: '커뮤니티' },
]

// 현재 로그인 사용자(목업 — auth 연동 전)
const currentUser = { name: '김주만' }

const apiProbe = ref({ state: 'checking', detail: '백엔드 확인 중' })

onMounted(async () => {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 1600)
  try {
    const res = await fetch(`${API_BASE_URL}/markets/summary/`, { signal: controller.signal })
    apiProbe.value = res.ok
      ? { state: 'online', detail: 'API 연결됨' }
      : { state: 'stub', detail: `API ${res.status} · 샘플 표시` }
  } catch {
    apiProbe.value = { state: 'local', detail: '샘플 모드 (Django 연결 전)' }
  } finally {
    window.clearTimeout(timeoutId)
  }
})
</script>

<template>
  <header class="topnav">
    <div class="topnav-inner">
      <RouterLink class="brand" to="/">
        <strong class="brand-wordmark">주만추</strong>
        <span class="brand-status" :class="apiProbe.state" :title="apiProbe.detail"></span>
      </RouterLink>

      <nav class="topnav-menu" aria-label="주요 메뉴">
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

      <div class="topnav-user">
        <span class="welcome">환영합니다 <strong>{{ currentUser.name }}</strong></span>
        <RouterLink to="/login" class="user-link">로그아웃</RouterLink>
        <RouterLink to="/profile" class="user-link">회원정보수정</RouterLink>
        <RouterLink to="/profile" class="mypage-link">
          <span class="mypage-avatar">{{ currentUser.name.charAt(0) }}</span>
          마이페이지
        </RouterLink>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topnav {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: var(--glass-blur-sm);
  -webkit-backdrop-filter: var(--glass-blur-sm);
  border-bottom: 1px solid var(--glass-border);
}

.topnav-inner {
  width: min(1480px, 100%);
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.brand-wordmark {
  font-size: 22px;
  font-weight: 900;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--faint);
}
.brand-status.online { background: var(--positive); box-shadow: 0 0 0 3px rgba(15, 159, 110, 0.18); }
.brand-status.stub { background: var(--amber, #e58b10); }
.brand-status.local { background: var(--accent); }
.brand-status.checking { background: var(--faint); }

.topnav-menu {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.topnav-menu a {
  padding: 8px 14px;
  border-radius: 999px;
  color: var(--muted);
  font-size: 14px;
  font-weight: 900;
  white-space: nowrap;
  transition: background 0.16s ease, color 0.16s ease;
}

.topnav-menu a:hover {
  color: var(--ink);
  background: rgba(255, 255, 255, 0.6);
}

.topnav-menu a.is-active {
  color: var(--accent);
  background: rgba(49, 93, 255, 0.1);
}

.topnav-user {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.welcome {
  color: var(--muted);
  font-size: 13px;
}
.welcome strong { color: var(--ink); }

.user-link {
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
  transition: color 0.16s ease;
}
.user-link:hover { color: var(--ink); }

.mypage-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 14px 6px 6px;
  border-radius: 999px;
  background: rgba(49, 93, 255, 0.1);
  border: 1px solid rgba(49, 93, 255, 0.25);
  color: var(--accent);
  font-size: 13px;
  font-weight: 900;
  white-space: nowrap;
}

.mypage-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  font-weight: 900;
}

@media (max-width: 1180px) {
  .topnav-inner { flex-wrap: wrap; gap: 12px; }
  .topnav-menu { order: 3; width: 100%; overflow-x: auto; }
  .welcome, .user-link { display: none; }
}
</style>
