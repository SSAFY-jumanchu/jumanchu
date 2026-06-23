import client from './client'

// 관심종목 목록 → { items, total }
export const fetchWatchlist = () => client.get('/watchlist/').then((r) => r.data)

// 관심종목 추가 → 201 item
export const addWatchlist = (stockCode) =>
  client.post('/watchlist/', { stock_code: stockCode }).then((r) => r.data)

// 관심종목 제거 → 204
export const removeWatchlist = (code) =>
  client.delete(`/watchlist/${code}/`).then((r) => r.data)

// 오늘의 궁합 추천(스와이프 카드)
export const fetchRecommendations = (params) =>
  client.get('/recommendations/', { params }).then((r) => r.data)

// 개인별 장투 랭킹
export const fetchLongtermRanking = (params) =>
  client.get('/longterm/ranking/', { params }).then((r) => r.data)

// 장투 케어 AI 리포트
export const fetchLongtermReport = (code) =>
  client.get(`/longterm/${code}/report/`).then((r) => r.data)
