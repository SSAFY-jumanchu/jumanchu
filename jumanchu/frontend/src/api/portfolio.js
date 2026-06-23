import client from './client'

// 포트폴리오 요약
export const fetchPortfolioSummary = () => client.get('/portfolio/').then((r) => r.data)

// 보유 종목 리스트. params: { sort, order } → { items, total_count, total_invested, total_current_value, total_profit_loss }
export const fetchHoldings = (params) =>
  client.get('/portfolio/holdings/', { params }).then((r) => r.data)

// 특정 보유 상세 (주문 내역 포함)
export const fetchHoldingDetail = (code) =>
  client.get(`/portfolio/holdings/${code}/`).then((r) => r.data)

// 가상 계좌 잔고
export const fetchBalance = () => client.get('/portfolio/balance/').then((r) => r.data)

// 자산 배분(섹터/종목 비중)
export const fetchAllocation = () => client.get('/portfolio/allocation/').then((r) => r.data)

// 주문 미리보기 (수수료·세금)
export const previewOrder = (payload) =>
  client.post('/orders/preview/', payload).then((r) => r.data)

// 주문 목록
export const fetchOrders = (params) => client.get('/orders/', { params }).then((r) => r.data)

// 매매 실행. payload: { stock_code, side: 'BUY'|'SELL', quantity, idempotency_key }
export const createOrder = (payload) =>
  client.post('/orders/', payload).then((r) => r.data)
