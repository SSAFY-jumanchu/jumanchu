<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

const navItems = [
  { to: '/', label: '홈' },
  { to: '/community', label: '커뮤니티' },
  { to: '/stocks', label: '주식 조회' },
  { to: '/holdings', label: '보유 종목' },
  { to: '/trading-diary', label: '매매일기' },
  { to: '/portfolio', label: '장투 케어' },
]

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const theme = useThemeStore()

// 비로그인 홈에는 풀스크린 배너가 네비 뒤로 깔린다 → 최상단에선 글자를 흰색으로
const overBanner = computed(() => route.name === 'home' && !auth.isAuthenticated)

const user = computed(() => {
  const name = auth.user?.nickname || '게스트'
  return { name, initial: name.charAt(0) }
})

// 스크롤 최상단에서는 네비를 투명하게, 내리면 glass 배경 노출
const scrolled = ref(false)
function onScroll() {
  scrolled.value = window.scrollY > 8
}
onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))

// 모바일 햄버거 메뉴
const menuOpen = ref(false)
function closeMenu() { menuOpen.value = false }
watch(() => route.fullPath, closeMenu)

// 스크롤됐거나 모바일 메뉴가 열려 있으면 불투명 glass 배경(드로어 가독성 확보)
const solid = computed(() => scrolled.value || menuOpen.value)

async function handleLogout() {
  closeMenu()
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="topnav" :class="{ 'is-scrolled': solid, 'over-white': overBanner && !solid }">
    <!-- 모바일 메뉴 열렸을 때 바깥 클릭 → 닫기 -->
    <div v-if="menuOpen" class="nav-backdrop" @click="closeMenu"></div>

    <div class="topnav-inner">
      <RouterLink class="brand" to="/" @click="closeMenu">
        <strong class="brand-wordmark">주만추</strong>
      </RouterLink>

      <!-- 모바일 햄버거 토글 -->
      <button
        class="nav-toggle"
        :class="{ open: menuOpen }"
        type="button"
        :aria-expanded="menuOpen"
        aria-label="메뉴"
        @click="menuOpen = !menuOpen"
      >
        <span></span><span></span><span></span>
      </button>

      <!-- 데스크탑: 가로 배치 / 모바일: 햄버거 드로어 -->
      <div class="nav-collapse" :class="{ open: menuOpen }">
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
            <button
              class="theme-toggle"
              type="button"
              role="switch"
              :aria-checked="theme.isDark"
              :aria-label="theme.isDark ? '라이트 모드로 전환' : '다크 모드로 전환'"
              :title="theme.isDark ? '라이트 모드로 전환' : '다크 모드로 전환'"
              @click="theme.toggle()"
            >
              <span class="theme-toggle-track" :class="{ 'is-dark': theme.isDark }">
                <span class="theme-toggle-thumb">{{ theme.isDark ? '🌙' : '☀️' }}</span>
              </span>
            </button>
            <button v-if="auth.isAuthenticated" class="user-btn" @click="handleLogout">로그아웃</button>
            <RouterLink v-else to="/login" class="user-btn">로그인</RouterLink>
            <RouterLink to="/mypage" class="user-btn accent">마이페이지</RouterLink>
          </div>
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
  background: transparent;
  border-bottom: 1px solid transparent;
  box-shadow: none;
  transition: background 0.25s ease, border-color 0.25s ease,
    box-shadow 0.25s ease, backdrop-filter 0.25s ease;
}

/* 스크롤을 내리면 glass 배경 노출 (최상단에서는 투명) */
.topnav.is-scrolled {
  background: var(--glass-strong);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-bottom-color: var(--glass-border);
  box-shadow: 0 2px 20px rgba(60, 80, 200, 0.07), var(--glass-inset);
}

/* 비로그인 홈: 상단이 흰 영역 → 네비는 흰 배경 + 검정 글씨 (테마 무관 고정) */
.topnav.over-white { background: #fff; border-bottom-color: var(--glass-border); }
.topnav.over-white .nav-links a { color: #3a4256; }
.topnav.over-white .nav-links a:hover {
  background: rgba(20, 30, 60, 0.07);
  color: #11161f;
}
.topnav.over-white .nav-links a.is-active {
  background: rgba(49, 93, 255, 0.12);
  border-color: rgba(49, 93, 255, 0.2);
  color: var(--accent);
}
.topnav.over-white .user-welcome { color: #5a6273; }
.topnav.over-white .user-welcome strong { color: #11161f; }
.topnav.over-white .user-btn {
  color: #2a3346;
  border-color: rgba(20, 30, 60, 0.2);
  background: #fff;
}
.topnav.over-white .user-btn:hover { background: rgba(20, 30, 60, 0.06); }
.topnav.over-white .user-btn.accent {
  color: var(--accent);
  border-color: rgba(49, 93, 255, 0.3);
  background: rgba(49, 93, 255, 0.08);
}
.topnav.over-white .user-btn.accent:hover { background: rgba(49, 93, 255, 0.16); }
.topnav.over-white .nav-toggle span { background: #11161f; }

.topnav-inner {
  position: relative;
  z-index: 1; /* nav-backdrop(z:-1) 위로 */
  max-width: 1480px;
  margin: 0 auto;
  padding: 0 28px;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 28px;
}

/* 데스크탑: 네비 링크 + 유저영역을 한 줄로 (모바일에선 드로어) */
.nav-collapse {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 28px;
}

/* 모바일 햄버거 버튼 (데스크탑 숨김) */
.nav-toggle {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 40px;
  height: 40px;
  margin-left: auto;
  padding: 0;
  border: 0;
  background: none;
  flex-shrink: 0;
}
.nav-toggle span {
  display: block;
  width: 22px;
  height: 2px;
  margin: 0 auto;
  border-radius: 2px;
  background: var(--ink);
  transition: transform 0.25s ease, opacity 0.2s ease;
}
.nav-toggle.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
.nav-toggle.open span:nth-child(2) { opacity: 0; }
.nav-toggle.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }
.topnav.over-hero .nav-toggle span { background: #fff; }

/* 모바일 메뉴 바깥 클릭용 백드롭 */
.nav-backdrop {
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
  background: rgba(8, 12, 24, 0.18);
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
  background: var(--surface-hover);
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

.user-actions { display: flex; align-items: center; gap: 5px; }

.theme-toggle {
  padding: 0;
  border: 0;
  background: none;
  display: inline-flex;
  align-items: center;
  margin-right: 4px;
}

.theme-toggle-track {
  width: 52px;
  height: 28px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  box-shadow: var(--glass-inset);
  display: flex;
  align-items: center;
  padding: 2px;
  transition: background 0.25s ease;
}

.theme-toggle-track.is-dark {
  background: rgba(125, 155, 255, 0.18);
}

.theme-toggle-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--glass-strong);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  line-height: 1;
  transition: transform 0.25s ease;
}

.theme-toggle-track.is-dark .theme-toggle-thumb {
  transform: translateX(24px);
}

.user-btn {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 11px;
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  transition: background 0.18s ease, color 0.18s ease;
  white-space: nowrap;
  text-decoration: none;
}

.user-btn:hover {
  background: var(--surface-hover);
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

/* 좁은 데스크탑/태블릿: 인사 문구 숨겨 공간 확보 */
@media (max-width: 1100px) and (min-width: 821px) {
  .user-welcome { display: none; }
}

@media (max-width: 980px) and (min-width: 821px) {
  .topnav-inner { gap: 16px; }
  .nav-links a { padding: 0 10px; font-size: 13px; }
}

/* ===== 모바일: 햄버거 드로어 ===== */
@media (max-width: 820px) {
  .topnav-inner { gap: 12px; padding: 0 16px; }

  .nav-toggle { display: inline-flex; }

  .nav-collapse {
    position: absolute;
    top: calc(100% + 1px);
    left: 0;
    right: 0;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    padding: 10px 14px 16px;
    /* 배너 위에서도 메뉴가 비치지 않도록 불투명 시트 */
    background: #ffffff;
    border-bottom: 1px solid var(--glass-border);
    box-shadow: 0 16px 34px rgba(60, 80, 200, 0.16), var(--glass-inset);
    transform: translateY(-8px);
    opacity: 0;
    pointer-events: none;
    transition: transform 0.2s ease, opacity 0.2s ease;
  }
  html[data-theme='dark'] .nav-collapse { background: #161c2e; }
  .nav-collapse.open {
    transform: translateY(0);
    opacity: 1;
    pointer-events: auto;
  }

  .nav-links {
    flex-direction: column;
    gap: 2px;
  }
  .nav-links a {
    min-height: 46px;
    padding: 0 14px;
    font-size: 15px;
  }
  /* 드로어는 항상 흰/glass 시트 → 기본 텍스트 색 사용 */
  .topnav.over-white .nav-collapse .nav-links a { color: var(--muted); }
  .topnav.over-white .nav-collapse .user-welcome,
  .topnav.over-white .nav-collapse .user-welcome strong { color: var(--ink); }

  .user-area {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    margin-top: 8px;
    padding-top: 14px;
    border-top: 1px solid var(--line);
  }
  .user-greeting { justify-content: flex-start; }
  .user-welcome { display: inline; font-size: 14px; } /* 1100px 숨김 해제 */
  .user-actions { flex-wrap: wrap; gap: 8px; }
  .theme-toggle { margin-right: auto; }
  .user-btn {
    flex: 1;
    min-width: 96px;
    min-height: 40px;
    justify-content: center;
    font-size: 13px;
  }
}
</style>
