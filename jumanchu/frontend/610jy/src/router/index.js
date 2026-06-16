import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DiscoverView from '../views/DiscoverView.vue'
import StocksView from '../views/StocksView.vue'
import PortfolioView from '../views/PortfolioView.vue'
import CommunityView from '../views/CommunityView.vue'
import ProfileView from '../views/ProfileView.vue'
import DiaryView from '../views/DiaryView.vue'
import CareView from '../views/CareView.vue'
import LoginView from '../views/auth/LoginView.vue'
import SignupView from '../views/auth/SignupView.vue'
import OnboardingView from '../views/auth/OnboardingView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/discover', name: 'discover', component: DiscoverView },
  { path: '/stocks', name: 'stocks', component: StocksView },
  { path: '/stocks/:code', name: 'stock-detail', component: () => import('../views/StockDetailView.vue') },
  { path: '/portfolio', name: 'portfolio', component: PortfolioView },
  { path: '/diary', name: 'diary', component: DiaryView },
  { path: '/care', name: 'care', component: CareView },
  { path: '/community', name: 'community', component: CommunityView },
  { path: '/profile', name: 'profile', component: ProfileView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/signup', name: 'signup', component: SignupView },
  { path: '/onboarding', name: 'onboarding', component: OnboardingView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})
