# 주만추 REST API 명세 초안

> ⚠️ **DEPRECATED (초기 드래프트).** 미구현 기능(MBTI 분석, 일지 AI 분석 등)이 섞여 있어 현행과 불일치.
> **현행 API는 → [URL_MAP.md](URL_MAP.md)(전체 라우트) · [API_스키마_v1.5.md](API_스키마_v1.5.md)(요청/응답) · Swagger `/api/docs/`** 참고.
> 이 문서는 초기 설계 기록용으로만 보존.

> SCRUM-45 (1.3.1 RESTful 엔드포인트 정의) 산출물
> 작성일: 2026-05-13 · 갱신: ERD 정합성 패치 (v1 → v1.1)
> 다음 단계: SCRUM-46 (request/response 스키마 정의)
>
> **v1.1 변경 요약**: ERD `ORDER` 테이블과 통일.
> - Trading 모듈 URL `/trades/*` → **`/orders/*`** 로 변경
> - 응답 객체 `transaction` → `order`, 필드 `type` → `side`
> - 알림(Notification) / 홈 BFF는 v2+에서 다룸

---

## 0. 개요

| 항목 | 값 |
|---|---|
| Base URL | `https://api.jumanchu.com/api/v1` (배포 시) / `http://localhost:8000/api/v1` (개발) |
| 버전 | v1 |
| 인증 | JWT Bearer Token (access + refresh) |
| 콘텐츠 타입 | `application/json; charset=utf-8` |
| 날짜 형식 | ISO 8601 UTC |
| 페이지네이션 | offset 방식 (`page`, `size`) |

---

## 1. 설계 원칙

1. `/api/v1/` 베이스 + 자원 명사 복수형 + 소문자
2. HTTP 메서드가 동작을 표현 — URL에 동사 금지
3. 하위 자원은 1단계까지 — `/posts/{id}/comments` ✅
4. 모든 보호된 엔드포인트에 `Authorization: Bearer <token>` 필수
5. 상태 코드 의미 지키기 — 200/201/204/400/401/403/404/409/422/500
6. 응답 envelope 일관성
7. **DB 테이블명과 URL 자원명을 일치시킨다** (예: `ORDER` ↔ `/orders`)

---

## 2. 공통 표준

### 2.1 페이지네이션

```
GET /api/v1/posts?page=1&size=20

{
  "items": [...],
  "page": 1,
  "size": 20,
  "total": 137
}
```

### 2.2 에러 응답

```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "잔고가 부족합니다. 필요: 7,240,000, 보유: 5,000,000",
    "field": null
  }
}
```

**대표 에러 코드**

| code | HTTP | 의미 |
|---|---|---|
| `INVALID_INPUT` | 400 | 요청 형식 오류 |
| `UNAUTHORIZED` | 401 | 토큰 없음/만료 |
| `FORBIDDEN` | 403 | 권한 없음 |
| `NOT_FOUND` | 404 | 리소스 없음 |
| `DUPLICATE_EMAIL` | 409 | 이메일 중복 |
| `DUPLICATE_REQUEST` | 409 | idempotency_key 중복 |
| `INSUFFICIENT_BALANCE` | 422 | 잔고 부족 |
| `INSUFFICIENT_QUANTITY` | 422 | 보유 수량 부족 (매도 시) |
| `MARKET_CLOSED` | 422 | 장 마감 시 매매 |
| `TRADING_HALTED` | 422 | 거래정지 종목 |
| `PRICE_LIMIT_REACHED` | 422 | 상/하한가 도달 |
| `INTERNAL_ERROR` | 500 | 서버 에러 |

### 2.3 인증 헤더

```
Authorization: Bearer <access_token>
```

access 만료 시 401 → 프론트가 `/auth/token/refresh` 호출 → 원 요청 재시도.

### 2.4 표시 규약

- ⚪ 인증 불필요
- 🔒 인증 필요
- 👤 본인만 접근 가능

---

## 3. 권한 매트릭스

| 자원 | 본인 | 타인 | 비로그인 |
|---|---|---|---|
| `/auth/me`, `/portfolio`, `/diaries`, `/watchlist`, `/orders`, `/notifications` | 모두 가능 | ❌ | 401 |
| `/posts`, `/comments` | 작성/수정/삭제 | 조회만 | 조회만 |
| `/stocks`, `/news`, `/markets` | 조회 | 조회 | 조회 |
| `/recommendations` | 본인 | ❌ | 401 |

---

## 4. 모듈별 엔드포인트

### 🔐 4.1 Auth

| Method | URL | 설명 | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/signup` | 이메일/비밀번호 가입 (ACCOUNT 자동 생성) | ⚪ |
| POST | `/api/v1/auth/login` | 로그인 → 토큰 발급 | ⚪ |
| POST | `/api/v1/auth/logout` | 로그아웃 | 🔒 |
| POST | `/api/v1/auth/token/refresh` | access 재발급 | ⚪ (refresh) |
| GET | `/api/v1/auth/me` | 내 정보 조회 (User + InvestmentProfile) | 🔒 |
| PATCH | `/api/v1/auth/me` | 내 정보 수정 | 🔒 |
| POST | `/api/v1/auth/onboarding` | 투자 성향 설정 (InvestmentProfile 생성/갱신) | 🔒 |
| POST | `/api/v1/auth/password/reset` | 비밀번호 재설정 요청 | ⚪ |

### 📈 4.2 Stock

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/stocks?q=&market=&page=` | 검색·필터·페이징 | ⚪ |
| GET | `/api/v1/stocks/{code}` | 종목 상세 메타 | ⚪ |
| GET | `/api/v1/stocks/{code}/price` | 현재가 (Redis 캐시 3초) | ⚪ |
| GET | `/api/v1/stocks/{code}/orderbook` | 호가창 | ⚪ |
| GET | `/api/v1/stocks/{code}/chart?period=&interval=` | 캔들 데이터 | ⚪ |
| GET | `/api/v1/stocks/{code}/financials` | DART 재무 (FinancialSummary + StockIndicator 합쳐 응답) | ⚪ |
| GET | `/api/v1/stocks/{code}/posts` | 이 종목 언급한 커뮤니티 글 | ⚪ |
| GET | `/api/v1/markets/summary` | 시장 요약 (홈 상단) | ⚪ |

### 💰 4.3 Order (매매 주문)

> v1에서 `Trading` / `/trades` 였으나 v1.1에서 ERD `ORDER` 테이블과 통일.

| Method | URL | 설명 | Auth |
|---|---|---|---|
| POST | `/api/v1/orders/preview` | 매수/매도 시뮬레이션 | 🔒 |
| POST | `/api/v1/orders` | 매수/매도 주문 실행 (idempotency_key 필수) | 🔒 |
| GET | `/api/v1/orders?side=&from=&page=` | 주문 내역 | 🔒 👤 |
| GET | `/api/v1/orders/{id}` | 주문 상세 | 🔒 👤 |

**주문 요청 페이로드**

```json
POST /api/v1/orders
{
  "stock_code": "005930",
  "side": "BUY",
  "quantity": 100,
  "idempotency_key": "uuid-v4-string"
}
```

**주문 응답**

```json
{
  "order": {
    "id": 123,
    "side": "BUY",
    "status": "FILLED",
    "quantity": 100,
    "price": 72400,
    "total_amount": 7240000,
    "executed_at": "2026-05-13T09:31:00Z",
    ...
  },
  "balance_after": 92760000,
  "holding_after": { ... }
}
```

### 💼 4.4 Portfolio

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/portfolio` | 잔고(Account) + 보유 + 손익 통합 | 🔒 👤 |
| GET | `/api/v1/portfolio/holdings` | 보유 종목 리스트 | 🔒 👤 |
| GET | `/api/v1/portfolio/holdings/{code}` | 특정 종목 보유 상세 (Order 내역 포함) | 🔒 👤 |
| GET | `/api/v1/portfolio/balance` | Account (가상 자금 잔고) | 🔒 👤 |
| GET | `/api/v1/portfolio/allocation` | 자산 배분 | 🔒 👤 |

### ⭐ 4.5 Watchlist

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/watchlist` | 관심 종목 목록 | 🔒 👤 |
| POST | `/api/v1/watchlist` | 관심 종목 추가 | 🔒 👤 |
| DELETE | `/api/v1/watchlist/{stock_code}` | 관심 종목 제거 | 🔒 👤 |

### 🎯 4.6 Recommend

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/recommendations/swipe?size=` | 스와이프 카드 큐 | 🔒 |
| POST | `/api/v1/recommendations/swipe/{stock_code}/action` | 좋아요/패스/관심 액션 | 🔒 |
| GET | `/api/v1/recommendations/roulette` | 오늘의 룰렛 (일 1회) | 🔒 |
| POST | `/api/v1/recommendations/mbti/analyze` | MBTI 분석 시작 (비동기, 202) | 🔒 |
| GET | `/api/v1/recommendations/mbti/result` | MBTI 결과 조회 | 🔒 👤 |
| GET | `/api/v1/recommendations/profile-stock` | 프로필 종목 (생년=상장연도) | 🔒 |

### 📰 4.7 News

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/news?q=&page=` | 종목/키워드 뉴스 검색 | ⚪ |
| GET | `/api/v1/news/trending` | 트렌딩 뉴스 + 매칭 종목 | ⚪ |
| GET | `/api/v1/news/{news_id}` | 뉴스 상세 | ⚪ |
| POST | `/api/v1/news/{news_id}/scrap` | 뉴스 스크랩 | 🔒 |
| DELETE | `/api/v1/news/{news_id}/scrap` | 스크랩 해제 | 🔒 |

### 📔 4.8 Diary

ERD: `STOCK_DIARY` + `DIARY_REVIEW` (1:1).

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/diaries?stock_code=&action_type=` | 내 일기 목록 | 🔒 👤 |
| POST | `/api/v1/diaries` | 일기 작성 (order_id 연결 가능) | 🔒 |
| GET | `/api/v1/diaries/{id}` | 일기 상세 (Review 포함) | 🔒 👤 |
| PATCH | `/api/v1/diaries/{id}` | 일기 수정 | 🔒 👤 |
| DELETE | `/api/v1/diaries/{id}` | 일기 삭제 | 🔒 👤 |
| POST | `/api/v1/diaries/{id}/review` | 사후 회고 작성 (DIARY_REVIEW) | 🔒 👤 |
| GET | `/api/v1/diaries/stats` | 일기 통계 | 🔒 👤 |

### 💬 4.9 Community

ERD: `COMMUNITY_POST`, `COMMENT`, `POST_LIKE`, `SHARED_PORTFOLIO`, `SHARED_PORTFOLIO_ITEM`.

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/posts?page=&sort=&type=` | 게시글 목록 (free/stock/pf 필터) | ⚪ |
| POST | `/api/v1/posts` | 게시글 작성 | 🔒 |
| GET | `/api/v1/posts/{id}` | 게시글 상세 | ⚪ |
| PATCH | `/api/v1/posts/{id}` | 수정 | 🔒 👤 |
| DELETE | `/api/v1/posts/{id}` | 삭제 | 🔒 👤 |
| GET | `/api/v1/posts/{id}/comments` | 댓글 목록 | ⚪ |
| POST | `/api/v1/posts/{id}/comments` | 댓글 작성 | 🔒 |
| PATCH | `/api/v1/comments/{id}` | 댓글 수정 | 🔒 👤 |
| DELETE | `/api/v1/comments/{id}` | 댓글 삭제 | 🔒 👤 |
| POST | `/api/v1/posts/{id}/likes` | 좋아요 토글 | 🔒 |
| GET | `/api/v1/portfolios?is_public=true` | 공유 포트폴리오 목록 | ⚪ |
| POST | `/api/v1/portfolios` | 공유 포트폴리오 작성 (items 포함) | 🔒 |
| GET | `/api/v1/portfolios/{id}` | 공유 포트폴리오 상세 (items 포함) | ⚪ |

### 🔔 4.10 Notification

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/notifications?unread=&page=` | 알림 목록 | 🔒 👤 |
| POST | `/api/v1/notifications/{id}/read` | 단건 읽음 | 🔒 👤 |
| PATCH | `/api/v1/notifications/read-all` | 전체 읽음 | 🔒 👤 |
| DELETE | `/api/v1/notifications/{id}` | 알림 삭제 | 🔒 👤 |
| GET | `/api/v1/notifications/settings` | 알림 설정 조회 | 🔒 👤 |
| PATCH | `/api/v1/notifications/settings` | 알림 설정 변경 | 🔒 👤 |

### 🏠 4.11 Home (BFF — 화면 단위 통합)

| Method | URL | 설명 | Auth |
|---|---|---|---|
| GET | `/api/v1/home/summary` | 시장+포트폴리오+추천+트렌딩 통합 | 🔒 |

**BFF 동작 방식**: Home view는 자체 캐시 없이 내부에서 각 모듈 호출 → 각 모듈은 자기 캐시(Redis 시세 3초, DB 트렌딩 1시간 등) 활용 → 응답 조립. 첫 페인트는 BFF로 한 번, 화면 유지 동안 시세는 `/stocks/{code}/price` 폴링으로 갱신.

---

## 5. 캐싱·실시간성 정책

| 자원 | 캐시 위치 | TTL | 갱신 트리거 |
|---|---|---|---|
| 종목 현재가 | Redis | 3초 | 만료 시 KIS 재호출 |
| 호가창 | Redis | 1초 | 만료 시 KIS 재호출 |
| 일봉 차트 | Redis | 1일 | 매 영업일 장 마감 후 |
| 재무제표 (FinancialSummary) | DB 영구 | — | 분기 배치 |
| 투자 지표 (StockIndicator) | DB 일 단위 | — | 일일 계산 배치 |
| 트렌딩 뉴스 | DB | 1시간 | Celery 배치 |
| 종목 마스터 | DB | 1일 | pykrx 일일 배치 |
| MBTI 결과 | DB | 7일 | 사용자 요청 시 갱신 |

> BFF (`/home/summary`)는 별도 캐시 안 함. 내부 호출이 위 캐시를 그대로 활용.

---

## 6. 비동기 처리 대상

다음 작업은 `202 Accepted` + 결과 폴링 패턴.

| 엔드포인트 | 이유 |
|---|---|
| `POST /recommendations/mbti/analyze` | LLM 호출 5~10초 |
| `POST /diaries/{id}/analyze` (예정) | LLM 일기 분석 |

비동기 응답 형식:

```json
{
  "task_id": "uuid",
  "status": "PENDING",
  "result_url": "/api/v1/recommendations/mbti/result"
}
```

클라이언트는 `result_url`을 2~5초 간격으로 폴링하다 `status: "DONE"`이면 결과 사용.

---

## 7. 다음 단계

- **SCRUM-46 (스키마 정의)** — 각 엔드포인트의 request/response 필드 타입 명세 → `API_스키마_v1.5.md` 참조
- **SCRUM-47 (인증/권한 정책)** — JWT TTL, refresh 정책, RBAC 상세 → `인증_권한_정책.md` 참조
- **SCRUM-48 (Swagger 문서화)** — OpenAPI 3.0 yaml, `drf-spectacular` 권장

---

## 8. 변경 이력

| 일자 | 변경 | 담당 |
|---|---|---|
| 2026-05-13 | 초안 작성 (11개 모듈, 약 70개 엔드포인트) | 강재민 |
| 2026-05-13 | **v1.1 ERD 정합성 패치** — Trading → Order 통일 (URL `/trades`→`/orders`, 응답 객체 `transaction`→`order`, 필드 `type`→`side`), Diary에 review 엔드포인트 추가, Community에 shared_portfolio 엔드포인트 추가 | 강재민 |
