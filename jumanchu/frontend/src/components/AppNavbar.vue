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
const paletteOptions = [
  { value: 'default', label: '기본', caption: 'Blue Finance' },
  { value: 'love', label: '연애', caption: 'Tinder Pink' },
]
const activePalette = computed(() => paletteOptions.find((item) => item.value === theme.palette) || paletteOptions[0])
const paletteOpen = ref(false)
const palettePicker = ref(null)

function choosePalette(value) {
  theme.setPalette(value)
  paletteOpen.value = false
}

function onDocumentPointerDown(event) {
  if (paletteOpen.value && !palettePicker.value?.contains(event.target)) paletteOpen.value = false
}

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
  document.addEventListener('pointerdown', onDocumentPointerDown)
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  document.removeEventListener('pointerdown', onDocumentPointerDown)
})

// 모바일 햄버거 메뉴
const menuOpen = ref(false)
function closeMenu() { menuOpen.value = false; paletteOpen.value = false }
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
  <header class="topnav" :class="{ 'is-scrolled': solid, 'over-hero': overBanner && !solid }">
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
            <div ref="palettePicker" class="palette-picker">
              <button
                class="palette-trigger"
                type="button"
                :class="`is-${theme.palette}`"
                :aria-expanded="paletteOpen"
                aria-haspopup="menu"
                :aria-label="`색상 테마 선택, 현재 ${activePalette.label}`"
                @click="paletteOpen = !paletteOpen"
              >
                <span class="palette-trigger-swatch" aria-hidden="true"></span>
                <span class="palette-trigger-label">{{ activePalette.label }}</span>
                <span class="palette-chevron" aria-hidden="true">▾</span>
              </button>

              <div v-if="paletteOpen" class="palette-menu" role="menu" aria-label="색상 테마">
                <p class="palette-menu-title">메인 색상</p>
                <button
                  v-for="option in paletteOptions"
                  :key="option.value"
                  class="palette-option"
                  :class="[`is-${option.value}`, { 'is-active': theme.palette === option.value }]"
                  type="button"
                  role="menuitemradio"
                  :aria-checked="theme.palette === option.value"
                  @click="choosePalette(option.value)"
                >
                  <span class="palette-option-swatch" aria-hidden="true"></span>
                  <span class="palette-option-copy">
                    <strong>{{ option.label }}</strong>
                    <small>{{ option.caption }}</small>
                  </span>
                  <span v-if="theme.palette === option.value" class="palette-check" aria-hidden="true">✓</span>
                </button>
              </div>
            </div>

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
  background: var(--glass-strong);
  border-bottom: 1px solid var(--glass-border);
  box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);
  transition: background 0.25s ease, border-color 0.25s ease,
    box-shadow 0.25s ease;
}

/* 스크롤 이후에도 불투명한 단색 헤더를 유지한다. */
.topnav.is-scrolled {
  background: var(--glass-strong);
  border-bottom-color: var(--glass-border);
  box-shadow: 0 5px 16px rgba(17, 24, 39, 0.07);
}
html[data-theme='dark'] .topnav { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.32); }
html[data-theme='dark'] .topnav.is-scrolled { box-shadow: 0 5px 16px rgba(0, 0, 0, 0.3); }

/* 비로그인 홈 배너 위(최상단)에서는 투명 배경 + 흰색 텍스트 */
.topnav.over-hero {
  background: transparent;
  border-bottom-color: transparent;
  box-shadow: none;
}
.topnav.over-hero .brand-wordmark {
  background: none;
  -webkit-text-fill-color: #fff;
  color: #fff;
}
.topnav.over-hero .nav-links a { color: rgba(255, 255, 255, 0.82); }
.topnav.over-hero .nav-links a:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}
.topnav.over-hero .nav-links a.is-active {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.45);
  color: #fff;
}
.topnav.over-hero .user-welcome { color: rgba(255, 255, 255, 0.78); }
.topnav.over-hero .user-welcome strong { color: #fff; }
.topnav.over-hero .user-btn {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.12);
}
.topnav.over-hero .user-btn:hover { background: rgba(255, 255, 255, 0.24); }
.topnav.over-hero .user-btn.accent {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.16);
}
.topnav.over-hero .user-btn.accent:hover { background: rgba(255, 255, 255, 0.26); }

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
  color: var(--ink);
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
  background: rgba(var(--accent-rgb), 0.12);
  color: var(--accent);
  border: 1px solid rgba(var(--accent-rgb), 0.2);
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
  box-shadow: 0 2px 8px rgba(var(--accent-rgb), 0.3);
}

.user-welcome {
  color: var(--muted);
  font-size: 13px;
}

.user-welcome strong { color: var(--ink); }

.user-actions { display: flex; align-items: center; gap: 5px; }

.palette-picker { position: relative; }

.palette-trigger {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 9px 0 7px;
  border: 1px solid var(--glass-border);
  border-radius: 999px;
  background: var(--surface-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 900;
  box-shadow: var(--glass-inset);
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}
.palette-trigger:hover,
.palette-trigger[aria-expanded='true'] { background: var(--surface-hover); color: var(--ink); }
.palette-trigger-swatch,
.palette-option-swatch {
  flex-shrink: 0;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.48), 0 2px 7px rgba(20, 24, 50, 0.16);
}
.palette-trigger-swatch { width: 19px; height: 19px; }
.palette-trigger.is-default .palette-trigger-swatch,
.palette-option.is-default .palette-option-swatch {
  background: linear-gradient(135deg, #315dff, #7d4ee8);
}
.palette-trigger.is-love .palette-trigger-swatch,
.palette-option.is-love .palette-option-swatch {
  background: linear-gradient(135deg, #ff6036 0%, #ff385c 48%, #fd267a 100%);
}
.palette-chevron { color: var(--faint); font-size: 10px; transition: transform 0.18s ease; }
.palette-trigger[aria-expanded='true'] .palette-chevron { transform: rotate(180deg); }

.palette-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 130;
  width: 224px;
  padding: 10px;
  border: 1px solid var(--glass-border);
  border-radius: 18px;
  background: var(--glass-strong);
  box-shadow: 0 10px 28px rgba(17, 24, 39, 0.12);
  transform-origin: top right;
  animation: paletteMenuIn 0.18s ease-out;
}
@keyframes paletteMenuIn {
  from { opacity: 0; transform: translateY(-5px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.palette-menu-title {
  margin: 2px 4px 8px;
  color: var(--faint);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.02em;
}
.palette-option {
  width: 100%;
  min-height: 54px;
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 7px 9px;
  border: 1px solid transparent;
  border-radius: 13px;
  background: transparent;
  color: var(--ink);
  text-align: left;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.palette-option:hover { background: var(--surface-soft); }
.palette-option.is-active {
  border-color: rgba(var(--accent-rgb), 0.24);
  background: rgba(var(--accent-rgb), 0.1);
}
.palette-option-swatch { width: 32px; height: 32px; }
.palette-option-copy { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.palette-option-copy strong { color: var(--ink); font-size: 13px; font-weight: 900; }
.palette-option-copy small { color: var(--muted); font-size: 10px; font-weight: 700; }
.palette-check {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  font-size: 11px;
  font-weight: 900;
}

.topnav.over-hero .palette-trigger {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}
.topnav.over-hero .palette-trigger:hover,
.topnav.over-hero .palette-trigger[aria-expanded='true'] { background: rgba(255, 255, 255, 0.24); }

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
  background: rgba(var(--accent-rgb), 0.1);
  border-color: rgba(var(--accent-rgb), 0.28);
  color: var(--accent);
}

.user-btn.accent:hover {
  background: rgba(var(--accent-rgb), 0.18);
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
  /* 드로어는 항상 glass 배경 → over-hero 흰색 글자 무효화 */
  .topnav.over-hero .nav-collapse .nav-links a { color: var(--muted); }
  .topnav.over-hero .nav-collapse .user-welcome,
  .topnav.over-hero .nav-collapse .user-welcome strong { color: var(--ink); }

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
  .palette-trigger { min-height: 40px; padding: 0 12px 0 9px; }
  .palette-menu { left: 0; right: auto; }
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
