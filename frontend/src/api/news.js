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

// 관심 종목 뉴스 = 보유 종목 뉴스(JWT) + 선호(스와이핑 저장) 종목별 뉴스(공개)를 병합.
// url(없으면 title) 기준 중복 제거 후 최신순으로 limit개 반환.
// withHoldings=false면 보유 뉴스 호출을 건너뛴다(비로그인 시 401 요청 방지).
export async function fetchInterestNews(favCodes = [], { limit = 6, withHoldings = true } = {}) {
  const tasks = []
  if (withHoldings) {
    tasks.push(fetchHoldingsNews().catch(() => ({ items: [] })))
  }
  // 선호 종목이 많아도 외부(네이버) 호출 폭주를 막기 위해 상위 8종목까지만
  for (const code of favCodes.slice(0, 8)) {
    tasks.push(
      fetchStockNews(code, { display: 5 })
        // 개별 종목 뉴스 항목엔 종목 정보가 없으므로 배지용으로 붙여준다
        .then((r) => ({ items: (r.items || []).map((it) => ({ ...it, stock: r.stock })) }))
        .catch(() => ({ items: [] })),
    )
  }
  const merged = (await Promise.all(tasks)).flatMap((r) => r.items || [])

  const seen = new Set()
  const unique = merged.filter((n) => {
    const key = n.url || n.title
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
  unique.sort((a, b) => new Date(b.published_at || 0) - new Date(a.published_at || 0))
  return unique.slice(0, limit)
}
