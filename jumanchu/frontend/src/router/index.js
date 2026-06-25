import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StocksView from '../views/StocksView.vue'
import PortfolioView from '../views/PortfolioView.vue'
import CommunityView from '../views/CommunityView.vue'
import OnboardingView from '../views/OnboardingView.vue'
import HoldingsView from '../views/HoldingsView.vue'
import StockDetailView from '../views/StockDetailView.vue'
import MyPageView from '../views/MyPageView.vue'
import TradingDiaryView from '../views/TradingDiaryView.vue'
import NewsView from '../views/NewsView.vue'
import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/stocks', name: 'stocks', component: StocksView },
  { path: '/stocks/:code', name: 'stock-detail', component: StockDetailView },
  { path: '/holdings', name: 'holdings', component: HoldingsView, meta: { requiresAuth: true } },
  { path: '/portfolio', name: 'portfolio', component: PortfolioView, meta: { requiresAuth: true } },
  { path: '/community', name: 'community', component: CommunityView },
  { path: '/news', name: 'news', component: NewsView },
  { path: '/mypage', name: 'mypage', component: MyPageView, meta: { requiresAuth: true } },
  { path: '/trading-diary', name: 'trading-diary', component: TradingDiaryView, meta: { requiresAuth: true } },
  { path: '/onboarding', name: 'onboarding', component: OnboardingView, meta: { requiresAuth: true } },
  { path: '/login', name: 'login', component: LoginView },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// 앱 부팅 시 세션 복원 후, 보호 라우트는 미인증이면 /login으로 (원래 경로는 redirect 쿼리로 보존).
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  await auth.init()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
})

export default router
