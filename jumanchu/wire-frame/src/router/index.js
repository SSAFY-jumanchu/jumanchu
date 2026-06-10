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
  { path: '/onboarding', name: 'onboarding', component: OnboardingView, meta: { skipGuard: true } },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// 회원가입 후 최초 로그인 시 온보딩 필수 진행
router.beforeEach((to) => {
  const hasOnboarded = localStorage.getItem('wf_onboarded')
  if (!hasOnboarded && !to.meta.skipGuard) {
    return { name: 'onboarding' }
  }
})

export default router
