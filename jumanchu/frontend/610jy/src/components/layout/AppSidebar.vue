<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink, useLink } from 'vue-router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const apiProbe = ref({ state: 'checking', label: '백엔드 확인 중', detail: `${API_BASE_URL}/markets/summary/` })

const navItems = [
  { to: '/', label: '홈' },
  { to: '/discover', label: '발견' },
  { to: '/stocks', label: '종목' },
  { to: '/portfolio', label: '포트폴리오' },
  { to: '/community', label: '커뮤니티' },
  { to: '/profile', label: '프로필' },
]

onMounted(async () => {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 1600)
  try {
    const res = await fetch(`${API_BASE_URL}/markets/summary/`, { signal: controller.signal })
    apiProbe.value = res.ok
      ? { state: 'online', label: 'API 연결됨', detail: '시장 요약 응답을 받았습니다.' }
      : { state: 'stub', label: `API ${res.status}`, detail: '스텁 응답. 샘플 데이터로 표시합니다.' }
  } catch {
    apiProbe.value = { state: 'local', label: '샘플 모드', detail: 'Django 연결 전 SQL 덤프 기반 샘플 데이터로 확인합니다.' }
  } finally {
    window.clearTimeout(timeoutId)
  }
})
</script>

<template>
  <aside class="sidebar" aria-label="주요 메뉴">
    <RouterLink class="brand" to="/">
      <strong class="brand-wordmark">주만추</strong>
    </RouterLink>

    <nav class="nav-list">
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

    <div class="sidebar-auth">
      <RouterLink to="/login" class="auth-link">로그인</RouterLink>
      <RouterLink to="/signup" class="auth-link primary">회원가입</RouterLink>
    </div>

    <section class="side-status" aria-label="데이터 준비 상태">
      <span class="status-dot" :class="apiProbe.state"></span>
      <strong>{{ apiProbe.label }}</strong>
      <p>{{ apiProbe.detail }}</p>
    </section>
  </aside>
</template>

<style scoped>
.sidebar-auth {
  display: grid;
  gap: 6px;
}

.auth-link {
  min-height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.48);
  color: var(--muted);
  font-size: 13px;
  font-weight: 900;
  transition: background 0.18s ease, color 0.18s ease;
}

.auth-link:hover {
  background: rgba(255, 255, 255, 0.68);
  color: var(--ink);
}

.auth-link.primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--purple) 100%);
  border: 0;
  color: #fff;
  box-shadow: 0 4px 16px rgba(49, 93, 255, 0.3);
}

.auth-link.primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(49, 93, 255, 0.4);
}
</style>
