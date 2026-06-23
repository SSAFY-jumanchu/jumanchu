# URL 맵 — 실제 구현된 REST API 전수 (진실의 원천)

> Django URL 리졸버에서 자동 추출. 작성 2026-06-23. **코드가 바뀌면 이 표도 갱신**.
> 추출 방법: `config.urls` → 각 앱 `urls.py`. 전부 `/api/v1/` 프리픽스 (auth만 `/api/v1/auth/`).
> 라이브 스키마(자동 생성): **Swagger `GET /api/docs/`**, **ReDoc `GET /api/redoc/`**.
>
> 권한 범례: **공개**=AllowAny · **JWT**=IsAuthenticated · **읽기공개/쓰기JWT**=IsAuthenticatedOrReadOnly
> 총 46개 엔드포인트 (8개 앱).

---

## 인증 — accounts (`/api/v1/auth/`) · 7

| Method | Path | 권한 | View | 설명 |
|---|---|---|---|---|
| POST | `/auth/signup/` | 공개 | SignupView | 회원가입 (+ 가상계좌 생성) |
| POST | `/auth/login/` | 공개 | LoginView | 로그인 (JWT access 발급) |
| POST | `/auth/logout/` | JWT | LogoutView | 로그아웃 (refresh 블랙리스트) |
| POST | `/auth/token/refresh/` | 공개 | TokenRefreshView | access 토큰 재발급 |
| GET·PATCH | `/auth/me/` | JWT | MeView | 내 정보 조회 / 수정 |
| POST | `/auth/onboarding/` | JWT | OnboardingView | 투자성향 온보딩 (5벡터·4유형·signature 종목) |
| POST | `/auth/password/reset/` | 공개 | PasswordResetView | 비밀번호 재설정 |

## 종목 — stocks · 9

| Method | Path | 권한 | View | 설명 |
|---|---|---|---|---|
| GET | `/stocks/` | 공개 | StockListView | 종목 목록 / 검색 |
| GET | `/stocks/{code}/` | 공개 | StockDetailView | 종목 상세 |
| GET | `/stocks/{code}/price/` | 공개 | StockPriceView | 현재가 (KIS, Redis 단기 캐시) |
| GET | `/stocks/{code}/orderbook/` | 공개 | StockOrderBookView | 호가창 |
| GET | `/stocks/{code}/chart/` | 공개 | StockChartView | 차트 봉(캔들) |
| GET | `/stocks/{code}/financials/` | 공개 | StockFinancialsView | 재무 요약 |
| GET | `/stocks/{code}/posts/` | 공개 | StockPostsView | 이 종목의 커뮤니티 글 |
| GET | `/markets/summary/` | 공개 | MarketSummaryView | 마켓 요약 (지수 등, 5s 캐시) |
| GET | `/economic-events/` | 공개 | EconomicEventListView | 경제 이벤트 캘린더 |

## 뉴스 — newses (`/api/v1/news/`) · 7

> 상세 명세: [NEWS_API_SPEC.jy.md](NEWS_API_SPEC.jy.md)

| Method | Path | 권한 | View | 설명 |
|---|---|---|---|---|
| GET | `/news/` | 공개 | StockNewsSearchView | 뉴스 검색 |
| GET | `/news/economy/` | 공개 | FeedNewsView | 경제 뉴스 피드 |
| GET | `/news/feed/{category}/` | 공개 | FeedNewsView | 카테고리별 뉴스 피드 |
| GET | `/news/by-sector/` | 공개 | SectorNewsView | 섹터별 뉴스 |
| GET | `/news/stocks/{code}/` | 공개 | StockNewsView | 특정 종목 뉴스 |
| GET | `/news/holdings/` | JWT | HoldingsNewsView | 내 보유 종목 뉴스 |
| GET | `/news/watchlist/` | JWT | WatchlistNewsView | 내 관심 종목 뉴스 |

## 주문·포트폴리오 — portfolio · 9

| Method | Path | 권한 | View | 설명 |
|---|---|---|---|---|
| POST | `/orders/preview/` | JWT | OrderPreviewView | 주문 미리보기 (수수료·세금 계산) |
| GET·POST | `/orders/` | JWT | OrderListCreateView | 주문 목록 / 매매 실행 |
| GET | `/orders/{id}/` | JWT | OrderDetailView | 주문 상세 |
| GET | `/portfolio/` | JWT | PortfolioSummaryView | 포트폴리오 요약 |
| GET | `/portfolio/holdings/` | JWT | HoldingsListView | 보유 종목 목록 |
| GET | `/portfolio/holdings/{code}/` | JWT | HoldingDetailView | 보유 종목 상세 |
| GET | `/portfolio/balance/` | JWT | BalanceView | 가상 계좌 잔고 |
| GET | `/portfolio/allocation/` | JWT | AllocationView | 자산 배분(섹터/종목 비중) |

## 추천·관심·장투 — recommend · 5

| Method | Path | 권한 | View | 설명 |
|---|---|---|---|---|
| GET | `/recommendations/` | JWT | RecommendSwipeView | 오늘의 궁합 추천 (스와이프 카드) |
| GET·POST | `/watchlist/` | JWT | WatchlistView | 관심종목 목록 / 추가 |
| DELETE | `/watchlist/{code}/` | JWT | WatchlistItemView | 관심종목 제거 |
| GET | `/longterm/ranking/` | JWT | LongTermRankingView | 개인별 장투 랭킹 (소계70%+궁합30%) |
| GET | `/longterm/{code}/report/` | JWT | LongTermReportView | 장투 케어 AI 리포트 (GMS GPT-4o, 캐시) |

## 커뮤니티 — community · 9

| Method | Path | 권한 | View | 설명 |
|---|---|---|---|---|
| GET·POST | `/posts/` | 읽기공개/쓰기JWT | PostListCreateView | 글 목록 / 작성 |
| GET·PATCH·DELETE | `/posts/{id}/` | 읽기공개/수정JWT | PostDetailView | 글 상세 / 수정 / 삭제 |
| POST | `/posts/{id}/like/` | JWT | PostLikeView | 글 좋아요(토글) |
| GET·POST | `/posts/{post_id}/comments/` | 읽기공개/쓰기JWT | CommentListCreateView | 댓글 목록 / 작성 |
| PATCH·DELETE | `/comments/{id}/` | JWT | CommentDetailView | 댓글 수정 / 삭제 |
| POST | `/comments/{id}/like/` | JWT | CommentLikeView | 댓글 좋아요(토글) |
| POST·DELETE | `/users/{user_id}/follow/` | JWT | FollowView | 팔로우 / 언팔로우 |
| GET | `/users/{user_id}/followers/` | 공개 | FollowersView | 팔로워 목록 |
| GET | `/users/{user_id}/following/` | 공개 | FollowingView | 팔로잉 목록 |

## 투자 일지 — diary · 2

| Method | Path | 권한 | View | 설명 |
|---|---|---|---|---|
| GET·POST | `/diaries/` | JWT | DiaryListCreateView | 일지 목록 / 작성 |
| GET·PATCH·DELETE | `/diaries/{id}/` | JWT | DiaryDetailView | 일지 상세 / 수정 / 삭제 |

## API 문서 (자동 생성)

| Method | Path | View | 설명 |
|---|---|---|---|
| GET | `/api/docs/` | SpectacularSwaggerView | Swagger UI |
| GET | `/api/redoc/` | SpectacularRedocView | ReDoc |
