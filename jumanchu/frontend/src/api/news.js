import client from './client'

// 경제 뉴스 피드
export const fetchEconomyNews = (params) =>
  client.get('/news/economy/', { params }).then((r) => r.data)

// 카테고리별 피드
export const fetchFeedNews = (category, params) =>
  client.get(`/news/feed/${category}/`, { params }).then((r) => r.data)

// 특정 종목 뉴스
export const fetchStockNews = (code, params) =>
  client.get(`/news/stocks/${code}/`, { params }).then((r) => r.data)

// 내 보유 종목 뉴스 (JWT)
export const fetchHoldingsNews = () => client.get('/news/holdings/').then((r) => r.data)

// 내 관심 종목 뉴스 (JWT)
export const fetchWatchlistNews = () => client.get('/news/watchlist/').then((r) => r.data)
