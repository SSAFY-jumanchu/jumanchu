import client from './client'

// 백엔드 계약: backend/{accounts,stocks,portfolio}/serializers.py 참고

export const authApi = {
  signup(payload) {
    // { email, password, password_confirm, username, nickname, birth_year, agree_terms }
    return client.post('/auth/signup/', payload)
  },
  login(email, password) {
    // 200 → { access, user } + refresh HttpOnly 쿠키
    return client.post('/auth/login/', { email, password })
  },
  logout() {
    return client.post('/auth/logout/')
  },
  me() {
    // 200 → { user, has_completed_onboarding }
    return client.get('/auth/me/')
  },
  submitOnboarding(payload) {
    // { risk_type, investment_style?, preferred_period?, preferred_sector? }
    return client.post('/auth/onboarding/', payload)
  },
}

export const stocksApi = {
  list(params) {
    // { items, page, size, total }
    return client.get('/stocks/', { params })
  },
  detail(code) {
    return client.get(`/stocks/${code}/`)
  },
  price(code) {
    return client.get(`/stocks/${code}/price/`)
  },
  orderbook(code) {
    return client.get(`/stocks/${code}/orderbook/`)
  },
  chart(code, params) {
    // params: { period, interval }
    return client.get(`/stocks/${code}/chart/`, { params })
  },
  financials(code, params) {
    return client.get(`/stocks/${code}/financials/`, { params })
  },
  posts(code, params) {
    return client.get(`/stocks/${code}/posts/`, { params })
  },
  marketSummary() {
    // { indices, top_gainers, top_losers, most_active, fetched_at }
    return client.get('/markets/summary/')
  },
}

export const portfolioApi = {
  summary() {
    return client.get('/portfolio/')
  },
  holdings() {
    return client.get('/portfolio/holdings/')
  },
  holdingDetail(code) {
    return client.get(`/portfolio/holdings/${code}/`)
  },
  balance() {
    return client.get('/portfolio/balance/')
  },
  allocation() {
    return client.get('/portfolio/allocation/')
  },
  previewOrder(payload) {
    // { stock_code, side, quantity }
    return client.post('/orders/preview/', payload)
  },
  createOrder(payload) {
    // { stock_code, side, quantity, idempotency_key }
    return client.post('/orders/', payload)
  },
  orders(params) {
    return client.get('/orders/', { params })
  },
}
