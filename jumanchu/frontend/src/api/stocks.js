import client from './client'

// 목록·검색. params: { q, market, sector, sort, page, size } → { items, page, size, total }
export const fetchStocks = (params) =>
  client.get('/stocks/', { params }).then((r) => r.data)

// 종목 상세(식별·메타) → { stock }
export const fetchStockDetail = (code) =>
  client.get(`/stocks/${code}/`).then((r) => r.data)

// 실시간 현재가(KIS 라이브) → { price }
export const fetchStockPrice = (code) =>
  client.get(`/stocks/${code}/price/`).then((r) => r.data)

// 호가창 → { orderbook }
export const fetchStockOrderbook = (code) =>
  client.get(`/stocks/${code}/orderbook/`).then((r) => r.data)

// 차트 봉. params: { period } → { candles }
export const fetchStockChart = (code, params) =>
  client.get(`/stocks/${code}/chart/`, { params }).then((r) => r.data)

// 재무 요약·지표 → { financials, indicators }
export const fetchStockFinancials = (code) =>
  client.get(`/stocks/${code}/financials/`).then((r) => r.data)

// 이 종목의 커뮤니티 글
export const fetchStockPosts = (code, params) =>
  client.get(`/stocks/${code}/posts/`, { params }).then((r) => r.data)

// 마켓 요약(지수 등) → { indices, kr, ... }
export const fetchMarketSummary = () =>
  client.get('/markets/summary/').then((r) => r.data)

// 인기 종목 랭킹. params: { market: all|domestic|overseas, sort: value|volume|up|down, size } → { items, ... }
export const fetchPopularRanking = (params) =>
  client.get('/markets/popular/', { params }).then((r) => r.data)

// 경제 이벤트 캘린더
export const fetchEconomicEvents = (params) =>
  client.get('/economic-events/', { params }).then((r) => r.data)
