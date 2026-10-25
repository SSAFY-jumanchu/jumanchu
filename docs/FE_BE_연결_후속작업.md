# FE↔BE 연결 — 후속 수정 작업 목록

> 작성 2026-06-23. `feature/semifinal` 통합 작업 중 발견된 **미완·미연결·정리 대상**.
> 연결 방식 본 명세: [FE_BE_연결_명세.md](FE_BE_연결_명세.md).
> 상태 범례: 🔴 막힘(BE 필요) · 🟡 FE 후속 · ⚪ 미착수 뷰

---

## 1. 백엔드가 막고 있는 것 (🔴 BE — 강재민)

| 항목 | 현재 | 필요 작업 | 영향 화면 |
|---|---|---|---|
| 호가창 | `GET /stocks/{code}/orderbook/` → **501 Not implemented** | 실제 호가 응답 구현 | StockDetailView 호가/체결 |
| 체결 내역(trades) | 엔드포인트 **없음** | 신규 엔드포인트 or orderbook에 최근 체결 포함 | StockDetailView 체결 탭 |
| 가격 포함 랭킹 리스트 | `GET /stocks/`는 **메타만** (price·rate·volume 없음) | 현재가·등락률·거래대금 포함한 목록/랭킹 엔드포인트 | StocksView 인기 종목 탭 |
| 분봉 차트 안정성 | `interval=5m`(KIS 라이브) → **503 간헐 실패** | 장중 분봉 캐시/리트라이 보강 | StockDetailView '3분' 탭 |
| 관심종목 목록 가격 | `GET /watchlist/`가 `current_price`·`change_rate`를 **null로 반환**(라이브 호출 생략). 단건 POST 추가 응답엔 가격 있음 | 목록에도 가격 채울지(캐시 활용) 정책 결정 | WatchlistView 관심종목 패널(현재 '—' 표시) |
| 보유목록 503 | `GET /portfolio/holdings/`가 종목별 KIS 라이브 현재가를 호출 → **1건이라도 KIS 실패 시 목록 전체 503**(간헐, 체감 1/3~2/3). | 현재가 캐시/last-price 폴백으로 목록은 항상 200 반환하도록 개선 | HoldingsView·PortfolioView (FE는 503에 한해 3회 재시도로 완화) |

> 참고: `stocks.js`에 `fetchStockOrderbook` 함수는 **이미 준비됨** — BE가 501만 풀면 FE는 매핑만 추가하면 됨.

---

## 2. 프론트 후속 정리 (🟡 FE — 송호영)

### 2.1 StockDetailView
- **차트 x축 라벨 불일치**: 일/주/월/년봉으로 교체됐는데 라벨이 아직 `09:00 ~ 15:30`(장중용) 고정. 기간에 맞는 날짜 라벨로 교체 필요.
- **종토방 미리보기**: `/posts/` 글이 0건이면 목업을 그대로 노출 중. 빈 상태(empty state) UI로 교체하거나, 실데이터만 표시하도록 정책 결정.
- ✅ **일반주문 패널 연결됨** (2026-06-23): `POST /orders/`(현재가 시장체결) + `GET /portfolio/balance/`(잔고). 실제 1억 가상매매 동작. 단 **지정가/주문가는 표시용**(서버는 현재가 시장체결, 수량·방향만 사용), `POST /orders/preview/`(수수료·세금 사전계산)는 미연결, **물타기 시뮬레이터는 여전히 로컬**.
- **회사 개황(stockInfo)**: 상장주식수·설립연도 등은 API 미제공 → 표시 항목 축소 또는 BE에 필드 요청.
- **분기 실적 차트(profitability)**: `/financials/`는 **연간(annual) summary만** 제공 → 분기 데이터 없으면 연간 기준으로 바꾸거나 BE에 분기 요청.

### 2.2 WatchlistView
- **추천 후보 브라우즈 리스트**: 좌측 "추천 후보와 관심종목" 목록은 아직 큐레이션 **목업 6종목**. 후보용 엔드포인트가 없어 유지. 대안: `/recommendations/`(궁합 스와이프, JWT)로 교체 검토.
- 관심종목 패널 가격은 1번(BE) 해결 전까지 `—` 표시.

### 2.3 HoldingsView
- **상세 패널 매수/매도 버튼**: 미연결 → `/orders/preview/` + `/orders/`. Portfolio 단계에서 주문 모달로 통합.
- **자산 구성(국내·해외)**: 클라이언트에서 USD×1380 하드코딩 환산. 정확히는 `/portfolio/allocation/` 사용 권장.
- **커뮤니티 한 줄**: 목업 유지(종목별 `/posts/` 연동은 후속).

### 2.4 HomeView (로그인 대시보드 잔여)
- ✅ **자산 현황**(totalAsset/totalReturn): `/portfolio/` 요약(`total_assets`·`total_profit_loss_rate`)으로 연결됨 (2026-06-23). 매매·가격변동이 총자산·수익률에 실시간 반영.
- **궁합 랭킹 티커**(compatRanking): 목업 → `/longterm/ranking/`.
- **매매일지 미리보기**(recentDiaries): 목업 → `/diaries/`.
- **관심 종목 뉴스**(watchlistNews): 목업 → `/news/watchlist/`.
- **달성 마일스톤**(achievedMilestones): 엔드포인트 불명 → BE 확인.

### 2.5 CommunityView (잔여)
- **글쓰기**: 백엔드는 `stock_code`(필수)+`category`(질문/후기/분석/공유)+`title`+`body` 요구. 현재 글쓰기 폼은 본문 텍스트만 → **종목 선택·제목·카테고리 입력 UI 추가** 후 `POST /posts/` 연결.
- **팔로우**: 백엔드는 `user_id` 기반(`/users/{id}/follow/`). FE `followedUsers`는 username 키 → user_id 매핑 필요. '팔로잉' 탭도 이에 의존.
- **댓글 좋아요**: `/comments/{id}/like/` 미연결(현재 로컬 토글).
- **인기글·종목 커뮤니티·최근 조회 위젯**: 대응 엔드포인트 없음 → 목업 유지.
- **'뉴스' 탭**: userType=channel 필터 → 채널 개념이 BE에 없어 빈 목록.

### 2.6 TradingDiaryView (잔여)
- **목표/손절가**: FE는 `+20%`/`-10%`(퍼센트), BE는 `target_price`/`stop_loss_price`(절대가). 기준가 입력 또는 절대가 입력 UI 필요 → 현재 미전송.
- **사유 다중선택**: BE `reason_category`는 단일 → 첫 매핑 사유만 전송. FE의 '배당 매력'·'분산 목적'은 BE enum에 없음.
- **작성 종목 고정**: `pendingTrade`(로보스타 090360) 하드코딩 → 실제 주문/보유에서 종목·`order_id` 연결 필요.
- **actual(실현 수익률)**: diary 응답에 없음 → '—'.

### 2.7 공통 인프라 (명세 7.1 — 미구현)
- **전역 토스트 미구축**: 결정 #4-A로 정했으나 `stores/toast.js` + `components/Toast.vue` 아직 없음. 현재 `client.js` 인터셉터는 토스트를 호출하지 않고, 각 화면이 로컬 에러 표시. → 토스트 도입 후 인터셉터(401 최종/5xx)·호출부에서 `toast.error(errMsg(e))` 연결.

---

## 3. 아직 연결 안 한 화면 (⚪ 미착수)

명세 9번 작업 순서 기준. 의존 엔드포인트는 [URL_MAP.md](URL_MAP.md) 참고.

| View | 주요 엔드포인트 | 비고 |
|---|---|---|
| ~~HomeView~~ | ✅ 시장지표 `/markets/summary/` + 경제뉴스 `/news/economy/`(공개) + 궁합추천 `/recommendations/` + 보유 `/portfolio/holdings/`(로그인) + 검색→`/stocks?q=`. **자산목표·궁합랭킹티커·마일스톤·매매일지·관심뉴스는 목업 유지** | 2026-06-23 |
| StocksView | ✅ **궁합 랭킹 탭** → `/longterm/ranking/`(개인별 장투점수, 로그인). **인기 종목 탭=목업**(BE 가격랭킹 엔드포인트 없음, 1번 참고), **선호 스와이프=목업**(Home이 `/recommendations/` 실연결). 랭킹표 가격·거래 컬럼은 '—'(랭킹 엔드포인트에 미포함) | 2026-06-23 부분 |
| ~~WatchlistView~~ | ✅ `/watchlist/` GET·POST·DELETE 연결 (관심목록·별 토글·상세 실데이터). 뉴스 `/news/watchlist/` 미연결 | 2026-06-23 |
| ~~HoldingsView~~ | ✅ `/portfolio/holdings/`(목록·합계·실시간가·종목별 스파크라인) + `/news/holdings/` 연결. 상세 매수/매도 버튼·종토방은 미연결 | 2026-06-23 |
| ~~PortfolioView~~ | ✅ 장투 페이지 — 보유종목별 `/longterm/{code}/report/`(총점·재무·성장·궁합 점수+AI리포트) + `/stocks/{code}/financials/`(세부 지표) + `/news/holdings/`. **매매일지·점수 히스토리는 빈 상태**(엔드포인트 없음). 궁합(userfit)은 온보딩 시에만 | 2026-06-23 |
| ~~CommunityView~~ | ✅ 글 목록 `/posts/`(latest) + 좋아요 토글 `/posts/{id}/like/` + 댓글 조회·작성 `/posts/{id}/comments/`. **글쓰기·팔로우·댓글좋아요·인기글/종목커뮤니티 위젯·팔로잉/뉴스 탭은 미연결** | 2026-06-23 |
| ~~TradingDiaryView~~ | ✅ 목록 `GET /diaries/` + 복기수정 `PATCH /diaries/{id}/`(부분 memo) + 작성 `POST /diaries/`. **목표/손절가는 %→절대가 변환 불가로 미전송, reasons는 단일 enum만, 작성 종목은 고정(pendingTrade)** | 2026-06-23 |
| ~~MyPageView~~ | ✅ 내정보 `/auth/me/` + 프로필수정 `PATCH /auth/me/`(닉네임·생년) + 매매내역 `/orders/` + 계좌·보유 `/portfolio/`(retry). **휴대폰·주소·성향바·활동내역·내가쓴글·월별수익률은 목업** | 2026-06-23 |

---

## 4. 열린 결정 (명세 10번 잔여)

- [ ] **#5 운영 배포 도메인 / CORS origin 확정** — 배포 단계에서. 현재 로컬(`localhost:5173` ↔ Vite proxy)만 검증됨.
- [ ] 종토방 빈 상태 정책 (2.1 참고)

---

## 5. 테스트 계정 (로컬 덤프 기준)

| 계정 | 비밀번호 | 상태 | 용도 |
|---|---|---|---|
| `demo@jumanchu.app` | `demo1234!` | **온보딩 완료 + 보유 3종목**(005930·000660·035420) | Portfolio/Holdings 풀데이터 데모 |
| `wl_test@test.com` | `test1234!` | 온보딩 미완료, 보유 1종목 | 관심종목/기본 플로우 |

> 궁합(userfit)·장투 랭킹은 **온보딩 완료 계정**에서만 채워짐 → 데모는 `demo@jumanchu.app` 사용 권장.

## 6. 환경/운영 메모

- 로컬 DB는 **BE 완성 덤프**(`jumanchu_db_full_20260623.sql`)로 적재 — KIS/DART enrich 재실행 불필요. 덤프 갱신 시 `public` 스키마 초기화 후 재restore.
- `.env`에 `REDIS_HOST`/`REDIS_PORT=6379` 추가돼야 redis가 고정 포트로 뜸(누락 시 랜덤 포트).
- 실시간 현재가(`/price/`)·분봉은 KIS 라이브라 DB와 무관하게 동작/실패 가능.
