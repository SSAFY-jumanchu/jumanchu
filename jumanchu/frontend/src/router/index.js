import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StocksView from '../views/StocksView.vue'
import WatchlistView from '../views/WatchlistView.vue'
import PortfolioView from '../views/PortfolioView.vue'
import CommunityView from '../views/CommunityView.vue'
import OnboardingView from '../views/OnboardingView.vue'
import HoldingsView from '../views/HoldingsView.vue'
import StockDetailView from '../views/StockDetailView.vue'
import MyPageView from '../views/MyPageView.vue'
import TradingDiaryView from '../views/TradingDiaryView.vue'
import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/stocks', name: 'stocks', component: StocksView },
  { path: '/stocks/:code', name: 'stock-detail', component: StockDetailView },
  { path: '/watchlist', name: 'watchlist', component: WatchlistView },
  { path: '/holdings', name: 'holdings', component: HoldingsView },
  { path: '/portfolio', name: 'portfolio', component: PortfolioView },
  { path: '/community', name: 'community', component: CommunityView },
  { path: '/mypage', name: 'mypage', component: MyPageView },
  { path: '/trading-diary', name: 'trading-diary', component: TradingDiaryView },
  { path: '/onboarding', name: 'onboarding', component: OnboardingView },
  { path: '/login', name: 'login', component: LoginView },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// 프로토타입 모드: 로그인 강제 없음 — 남아 있는 세션이 있으면 복원만 한다.
router.beforeEach(async () => {
  const auth = useAuthStore()
  await auth.init()
})

export default router
