# 주만추 API 스키마 v1.5 (전 8모듈 — 구현 정합)

> SCRUM-46 (1.3.2 Request/Response 스키마 정의) 산출물
> 작성일: 2026-05-13 · 최신 갱신: 2026-06-23 (구현 대조 + 누락 모듈 추가)
> 범위: Auth · Stock · Order · Portfolio · **Recommend · Community · Diary · News** (전 46 엔드포인트)
> 전체 라우트 한눈에: **[URL_MAP.md](URL_MAP.md)** · 라이브 스키마: Swagger `/api/docs/`
>
> **v1.1 변경 요약**: `planning/모델_서비스flow/erd.html` 기준으로 명명·구조 통일.
> - `Transaction` → **`Order`** (DB 테이블명과 통일, `status`/`idempotency_key` 필드 보강)
> - `VirtualAccount` → **`Account`** (정식 도메인 모델로 추가)
> - `Financial` → **`FinancialSummary` + `StockIndicator`** 두 객체로 분리 (ERD 테이블 매칭)
> - `Stock` 필드 풍부화 (currency, kis_short_code, is_sp500, is_nasdaq100, is_active)
> - Trading 모듈 URL: `/trades/*` → **`/orders/*`** 로 변경

---

## 0. 공통 규약

### 0.1 표기 규칙

본 문서는 **TypeScript-like 타입 표기**를 사용. Django 구현 시:
- `number` → `IntegerField` 또는 `DecimalField`
- `string` → `CharField` / `TextField` / `EmailField`
- `ISODateTime` → `DateTimeField` (응답 시 ISO 8601 UTC 직렬화)
- `?` 접미사 → 선택(optional), 없거나 null 가능
- `enum` → `TextChoices`

### 0.2 표준 응답 envelope

```typescript
// 목록 응답
interface PaginatedResponse<T> {
  items: T[]
  page: number       // 1부터
  size: number       // 페이지 크기
  total: number      // 전체 개수
}

// 에러 응답 (공통)
interface ErrorResponse {
  error: {
    code: string     // ENUM (예: "INSUFFICIENT_BALANCE")
    message: string  // 한국어 사용자 메시지
    field?: string   // 폼 검증 실패 시
  }
}
```

### 0.3 공통 타입

```typescript
type ISODateTime = string   // "2026-05-13T09:30:00Z"
type DateString   = string   // "2026-05-13"
type StockCode    = string   // "005930", "NVDA"
type Money        = number   // KRW: 정수 원 / USD: 소수 4자리
type Quantity     = number   // 주식 수량, 정수
type Percent      = number   // 백분율, 소수 2자리 (예: 1.69)
```

---

## 1. 도메인 모델

엔드포인트들이 공통으로 참조하는 핵심 객체 정의. **ERD 테이블과 1:1 매핑**.

### 1.1 User

ERD: `USER` + `USER_INVESTMENT_PROFILE` (1:1 분리). API 응답에선 합쳐 내려보냄.

```typescript
interface User {
  id: number
  email: string
  nickname: string
  birth_year: number              // 1990
  profile: InvestmentProfile | null   // 온보딩 완료 시 (없으면 null)
  profile_stock_code?: StockCode    // 생년=상장연도 기반 프로필 종목
  created_at: ISODateTime
}

interface InvestmentProfile {       // ERD: USER_INVESTMENT_PROFILE
  investment_style?: string         // 성향 4유형 라벨: "가치 파트너형" | "성장 동반형" | "단기 승부형" | "신중 탐색형"
  preferred_period?: number         // 선호 보유 기간(개월)
  preferred_sector?: string         // "반도체", "2차전지" 등
  risk_tolerance?: number           // 온보딩 5벡터 (각 1~5)
  investment_term?: number
  experience?: number
  loss_aversion?: number
  behavior?: number
  profiled_at?: ISODateTime         // 온보딩 완료 시각
  updated_at: ISODateTime
}
```

### 1.2 Stock

ERD: `STOCK`. 종목 마스터 (pykrx로 일일 적재).

```typescript
interface Stock {
  code: StockCode             // "005930"
  name: string                // "삼성전자" (한국어 기본)
  market: Market              // "KOSPI"
  sector?: string             // "전기·전자"
  industry?: string           // "반도체 및 반도체장비"
  listed_at?: DateString      // "1975-06-11"
  market_cap?: Money          // 시가총액
  currency: Currency          // "KRW" | "USD"
  kis_short_code?: string     // KIS API 호출용 단축 코드 (해외 종목)
  is_active: boolean          // 상장 폐지 여부 (false면 거래 불가)
  is_sp500?: boolean          // S&P 500 편입
  is_nasdaq100?: boolean      // NASDAQ 100 편입
  updated_at: ISODateTime
}

type Market = "KOSPI" | "KOSDAQ" | "NASDAQ" | "NYSE"
type Currency = "KRW" | "USD"
```

### 1.3 StockPrice (실시간 현재가)

DB 저장 X (KIS API + Redis 캐시 3초). KIS 응답을 우리 도메인 언어로 정규화.

```typescript
interface StockPrice {
  stock_code: StockCode
  current: Money              // 현재가
  open: Money                 // 시가
  high: Money                 // 고가
  low: Money                  // 저가
  prev_close: Money           // 전일 종가
  change: Money               // 전일 대비 (부호 포함)
  change_rate: Percent        // 전일 대비율
  volume: number              // 누적 거래량
  trading_value: Money        // 누적 거래대금
  upper_limit: Money          // 상한가
  lower_limit: Money          // 하한가
  warnings: StockWarnings
  fetched_at: ISODateTime     // 캐시 시점
}

interface StockWarnings {
  is_management: boolean      // 관리종목
  is_short_overheated: boolean // 공매도 과열
  is_trading_halted: boolean   // 거래 정지
  is_vi_active: boolean        // VI 발동
  short_term_overheated: boolean // 단기 과열
  investment_caution: boolean  // 투자 유의
  warning_label?: string       // "투자유의" / "단기과열" 등 (UI 배지용)
}
```

### 1.4 OrderBook (호가창)

DB 저장 X (KIS API + Redis 캐시 — 장중 1s / 장외 30s).

```typescript
interface OrderBook {
  stock_code: StockCode
  asks: OrderBookEntry[]      // 매도 호가 (낮은 가격부터)
  bids: OrderBookEntry[]      // 매수 호가 (높은 가격부터)
  total_ask_quantity: Quantity
  total_bid_quantity: Quantity
  fetched_at: ISODateTime
}

interface OrderBookEntry {
  price: Money
  quantity: Quantity
}
```

### 1.5 Candle (차트 봉)

ERD: `STOCK_PRICE` (일봉만 DB 저장). 분봉은 Redis 5분 캐시.

```typescript
interface Candle {
  time: ISODateTime           // 봉 시작 시각
  open: Money
  high: Money
  low: Money
  close: Money
  volume: number
}

type ChartPeriod = "1d" | "1w" | "1m" | "3m" | "1y" | "5y"
type ChartInterval = "1m" | "5m" | "15m" | "1h" | "1d" | "1w" | "1mo"
```

### 1.6 FinancialSummary (재무 요약)

ERD: `FINANCIAL_SUMMARY`. DART에서 분기마다 적재.

```typescript
interface FinancialSummary {
  stock_code: StockCode
  fiscal_period: string       // "2025Q3" 또는 "2025FY"
  revenue: Money              // 매출액
  op_profit: Money            // 영업이익
  net_profit: Money           // 당기순이익
  operating_margin?: Percent  // 영업이익률
  net_margin?: Percent        // 순이익률
  revenue_yoy?: Percent       // 매출 전년 동기 대비
  op_profit_yoy?: Percent     // 영업이익 YoY
  net_profit_yoy?: Percent    // 순이익 YoY
  debt_ratio?: Percent        // 부채비율
  equity_ratio?: Percent      // 자기자본비율
  current_ratio?: Percent     // 유동비율
  payout_ratio?: Percent      // 배당성향
  data_source: "DART" | "yfinance"
  fetched_at: ISODateTime
}
```

### 1.7 StockIndicator (투자 지표)

ERD: `STOCK_INDICATOR`. 시세 기반 지표와 자체 계산 지표.

```typescript
interface StockIndicator {
  stock_code: StockCode
  per?: number                // 주가수익비율
  pbr?: number                // 주가순자산비율
  eps?: Money                 // 주당순이익
  roe?: Percent               // 자기자본이익률
  roa?: Percent               // 총자산이익률
  dividend_yield?: Percent    // 배당수익률
  beta?: number               // 베타 (시장 대비 변동성, 자체 계산)
  volatility?: number         // 변동성 (자체 계산)
  high_52w?: Money            // 52주 최고가
  low_52w?: Money             // 52주 최저가
  calculated_date: DateString
}
```

### 1.8 Holding (보유 종목)

ERD: `HOLDING`. (user, stock) unique together.

```typescript
interface Holding {
  stock: Stock
  quantity: Quantity
  avg_price: Money            // 평균 매수가 = average_price
  total_invested: Money       // 매입 총액 = avg_price * quantity (계산)
  current_price: Money        // 현재가 (KIS 스냅샷)
  current_value: Money        // 평가 금액 = current_price * quantity (계산)
  profit_loss: Money          // 평가 손익 (계산)
  profit_loss_rate: Percent   // 평가 손익률 (계산)
  first_acquired_at: ISODateTime  // 첫 매수일
  updated_at: ISODateTime
}
```

### 1.9 Order (주문)

ERD: `ORDER` (트랜잭션 핵심). 모의 매매라 보통 즉시 FILLED.

```typescript
interface Order {
  id: number
  user_id: number
  account_id: number
  stock_code: StockCode
  stock_name: string          // 응답 시 JOIN
  side: OrderSide             // "BUY" | "SELL"
  quantity: Quantity
  price: Money                // 체결가
  total_amount: Money         // 체결 총액 = price * quantity
  status: OrderStatus         // 모의 매매: 보통 "FILLED"
  idempotency_key: string     // 중복 주문 방지 (UUID, unique)
  created_at: ISODateTime
  executed_at?: ISODateTime   // FILLED 된 시각
}

type OrderSide = "BUY" | "SELL"
type OrderStatus = "PENDING" | "FILLED" | "FAILED"
```

### 1.10 Account (가상 계좌)

ERD: `ACCOUNT`. USER와 1:1.

```typescript
interface Account {
  user_id: number
  balance: Money              // 현재 잔고
  initial_balance: Money      // 초기 자금 (1억 + 온보딩 보너스)
  created_at: ISODateTime
  updated_at: ISODateTime
}
```

---

## 2. Auth 모듈 (8개)

### 2.1 POST /api/v1/auth/signup

**Request**
```typescript
{
  email: string              // 형식 검증
  password: string           // 8자 이상, 영문+숫자 조합
  password_confirm: string   // password와 일치 검증
  username: string           // 로그인 ID (또는 email로 통일)
  nickname: string           // 2~20자, 중복 검증
  birth_year: number         // 1900 ~ 현재 연도 - 14 (만 14세 이상)
  agree_terms: boolean       // 필수 true
}
```

**Response 201 Created**
```typescript
{
  user: User                 // profile은 null (온보딩 전)
  account: Account           // 회원가입 시 ACCOUNT 자동 생성 (balance: 1억)
}
```

**비즈니스 규칙**
- USER 생성 + ACCOUNT 생성이 한 트랜잭션 (`@transaction.atomic`)

**Errors**
- `400 INVALID_INPUT` — 형식 오류 (field에 어느 필드인지)
- `400 PASSWORD_MISMATCH` — password ≠ password_confirm
- `400 UNDERAGE` — birth_year로 만 14세 미만
- `409 DUPLICATE_EMAIL` — 이미 가입된 이메일
- `409 DUPLICATE_NICKNAME` — 닉네임 중복
- `429 TOO_MANY_REQUESTS` — Rate limit 초과

---

### 2.2 POST /api/v1/auth/login

**Request**
```typescript
{
  email: string
  password: string
}
```

**Response 200 OK**
```typescript
{
  access: string             // JWT access token (30분)
  user: User                 // 로그인 직후 정보 응답에 포함 (profile 포함)
}
// 추가: Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Strict
```

**Errors**
- `401 INVALID_CREDENTIALS` — 이메일/비밀번호 불일치
- `403 ACCOUNT_DISABLED` — 비활성 계정
- `429 TOO_MANY_REQUESTS` — 분당 5회 초과

---

### 2.3 POST /api/v1/auth/logout

**Request**: 본문 없음 (refresh는 Cookie로 자동 첨부)

**Response 204 No Content**
- refresh 토큰 블랙리스트 추가
- Set-Cookie: refresh_token=; Max-Age=0 (Cookie 삭제)

**Errors**
- `401 UNAUTHORIZED` — access token 없음/만료

---

### 2.4 POST /api/v1/auth/token/refresh

**Request**: 본문 없음 (refresh는 Cookie로 자동 첨부)

**Response 200 OK**
```typescript
{
  access: string             // 새 access token (30분)
}
// 추가: Set-Cookie: refresh_token=<new>; ... (rotation)
```

**Errors**
- `401 INVALID_REFRESH_TOKEN` — refresh Cookie 없음/만료/블랙리스트

---

### 2.5 GET /api/v1/auth/me

**Response 200 OK**
```typescript
{
  user: User & {
    has_completed_onboarding: boolean    // profile != null과 동일
  }
}
```

**Errors**: `401 UNAUTHORIZED`

---

### 2.6 PATCH /api/v1/auth/me

**Request** (모두 optional)
```typescript
{
  nickname?: string
  birth_year?: number
}
```

**Response 200 OK**
```typescript
{
  user: User
}
```

**Errors**
- `400 INVALID_INPUT`
- `409 DUPLICATE_NICKNAME`
- `401 UNAUTHORIZED`

---

### 2.7 POST /api/v1/auth/onboarding

**Request**
```typescript
{
  q1: 1 | 3 | 5                  // 투자 목적
  q2: 1 | 3 | 5                  // 투자 경험
  q3: 1 | 3 | 5                  // 손실 허용 범위
  q4: 1 | 3 | 5                  // 자금 의존도
  q5: 1 | 3 | 5                  // 투자 기간 (총점 가중 ×2)
  q6: 1 | 3 | 5                  // 시장 하락 반응
  preferred_sectors?: string[]   // 관심 섹터 우선순위 순 (상위 3개 가중 1.0/0.6/0.3)
  preferred_period?: number      // 선호 보유 기간(개월)
}
// 5벡터·성향 4유형(investment_style)은 서버에서 q1~q6으로 산출
```

**Response 200 OK**
```typescript
{
  user: User                     // profile이 채워진 상태
  profile_stock?: Stock          // 생년=상장연도 매칭 종목
  welcome_bonus: Money           // 2만원 가상 자금 보너스 (account.balance에 가산)
}
```

**Errors**
- `400 INVALID_INPUT`
- `409 ALREADY_ONBOARDED` — 이미 온보딩 완료

---

### 2.8 POST /api/v1/auth/password/reset

**Request**
```typescript
{
  email: string
}
```

**Response 204 No Content**
- 메일 발송 여부와 무관하게 204 (이메일 존재 노출 방지)

**Errors**
- `429 TOO_MANY_REQUESTS` — 분당 3회 초과

---

## 3. Stock 모듈 (9개)

### 3.1 GET /api/v1/stocks

**Query**
```
q?: string              // 종목명/코드 검색어
market?: Market         // "KOSPI" | "KOSDAQ" | "NASDAQ" | "NYSE"
sector?: string         // 업종
is_sp500?: boolean      // S&P 500만
is_nasdaq100?: boolean  // NASDAQ 100만
sort?: "name" | "market_cap" | "volume"
page?: number = 1
size?: number = 20      // 최대 100
```

**Response 200 OK**
```typescript
PaginatedResponse<Stock>
```

---

### 3.2 GET /api/v1/stocks/{code}

**Response 200 OK**
```typescript
{
  stock: Stock & {
    description?: string         // 회사 소개
    homepage_url?: string
    ceo_name?: string
    employee_count?: number
    is_in_watchlist: boolean     // 로그인 시: 내 워치리스트에 있는지
  }
}
```

**Errors**: `404 NOT_FOUND`

---

### 3.3 GET /api/v1/stocks/{code}/price

**Response 200 OK**
```typescript
{
  price: StockPrice
}
```

**Caching**: Redis 3초 TTL. 응답에 `Cache-Control: max-age=3` 헤더.

**Errors**: `404 NOT_FOUND` · `503 EXTERNAL_API_ERROR` (KIS 장애 시)

---

### 3.4 GET /api/v1/stocks/{code}/orderbook

**Response 200 OK**
```typescript
{
  orderbook: OrderBook
}
```

**Caching**: Redis 1초 TTL.

**Errors**: `404 NOT_FOUND` · `503 EXTERNAL_API_ERROR`

---

### 3.5 GET /api/v1/stocks/{code}/chart

**Query**
```
period: ChartPeriod = "1d"        // 1d/1w/1m/3m/1y/5y
interval: ChartInterval = "5m"     // 1m/5m/15m/1h/1d/1w/1mo
```

period × interval 조합 검증:
- `period=1d`: interval ∈ {1m, 5m, 15m, 1h}
- `period=1w`: interval ∈ {15m, 1h, 1d}
- `period=1m~5y`: interval ∈ {1d, 1w, 1mo}

**Response 200 OK**
```typescript
{
  stock_code: StockCode
  period: ChartPeriod
  interval: ChartInterval
  candles: Candle[]              // 오래된 것부터 최신 순
  generated_at: ISODateTime
}
```

**Caching**: 일봉은 1일, 분봉은 5분 TTL.

**Errors**: `400 INVALID_INTERVAL_FOR_PERIOD` · `404 NOT_FOUND`

---

### 3.6 GET /api/v1/stocks/{code}/financials

ERD의 `FINANCIAL_SUMMARY` + `STOCK_INDICATOR` 두 테이블을 합쳐 응답.

**Query**
```
type?: "quarterly" | "annual" = "quarterly"
limit?: number = 8              // 최근 N개 (분기 8개 = 2년치)
```

**Response 200 OK**
```typescript
{
  stock_code: StockCode
  type: "quarterly" | "annual"
  summaries: FinancialSummary[]  // 시간 역순 (최신 분기 먼저)
  indicator: StockIndicator      // 최신 1건 (현재 시점 지표)
  last_updated: ISODateTime
}
```

**Caching**: DB 영구 저장 + 응답 캐시 1시간.

**Errors**: `404 NOT_FOUND` · `503 EXTERNAL_API_ERROR` (DART 장애)

---

### 3.7 GET /api/v1/stocks/{code}/posts

**Query**
```
page?: number = 1
size?: number = 20
```

**Response 200 OK**
```typescript
PaginatedResponse<PostSummary>
// PostSummary는 Community 모듈에서 정의 (다음 차분)
// 미리 정의: id, title, author_nickname, created_at, comment_count, like_count
```

---

### 3.8 GET /api/v1/markets/summary

**Response 200 OK**
```typescript
{
  indices: {                      // 대표 지수
    code: string                  // "KOSPI", "KOSDAQ", "NASDAQ"
    name: string                  // "코스피"
    current: number
    change: number
    change_rate: Percent
  }[]
  top_gainers: StockSummary[]    // 상승 상위 5
  top_losers: StockSummary[]     // 하락 상위 5
  most_active: StockSummary[]    // 거래량 상위 5
  fetched_at: ISODateTime
}

interface StockSummary {          // Stock + 가격 간략 (홈에서 카드로 표시)
  code: StockCode
  name: string
  current: Money
  change: Money
  change_rate: Percent
}
```

**Caching**: Redis 10초 TTL.

---

### 3.9 GET /api/v1/economic-events/

경제 이벤트 캘린더. 공개(AllowAny).

**Response 200** — `{ items: EconomicEvent[], total: number }`

```typescript
interface EconomicEvent {
  id: number
  event_date: ISODate
  title: string
  importance: "HIGH" | "MEDIUM" | "LOW"
  country: "US" | "KR"
}
```

---

## 4. Order 모듈 (4개) — 매매 주문

> v1에서 `Trading`/`/trades` 였으나 v1.1에서 ERD `ORDER` 테이블과 통일.
> URL은 `/api/v1/orders/*`, 자원 명은 `Order`.

### 4.1 POST /api/v1/orders/preview

매매 시뮬레이션. 잔고/보유/평균단가 검증 결과를 미리 보여줌.

**Request**
```typescript
{
  stock_code: StockCode
  side: OrderSide                 // "BUY" | "SELL"
  quantity: Quantity              // 양수 정수
}
```

**Response 200 OK**
```typescript
{
  is_valid: boolean               // false면 errors에 사유
  errors?: string[]               // ["INSUFFICIENT_BALANCE", "TRADING_HALTED"]
  preview: {
    stock_code: StockCode
    stock_name: string
    side: OrderSide
    quantity: Quantity
    current_price: Money          // 현재가 기준
    estimated_total: Money        // 예상 체결 금액
    estimated_fee: Money          // 수수료 (모의 0)
    balance_after: Money          // 매매 후 예상 잔고 (BUY)
    holding_after: Holding | null // 매매 후 예상 보유 상태
    avg_price_after?: Money       // BUY 시 평균 매수가 변화
    realized_profit?: Money       // SELL 시 실현 손익
    realized_profit_rate?: Percent
  }
}
```

**비즈니스 규칙**
- BUY: `is_valid=false` 조건 → 잔고 부족, 장 마감, 거래정지, 상한가 도달
- SELL: `is_valid=false` 조건 → 보유 수량 부족, 거래정지, 하한가 도달

**Errors**: `404 NOT_FOUND` (종목) · `401 UNAUTHORIZED`

---

### 4.2 POST /api/v1/orders

매매 주문 실행. 모의 매매라 보통 즉시 FILLED.

**Request**
```typescript
{
  stock_code: StockCode
  side: OrderSide
  quantity: Quantity
  idempotency_key: string         // 필수: UUID 권장, 중복 매매 방지
}
```

**Response 201 Created**
```typescript
{
  order: Order                    // status="FILLED", executed_at 채워짐
  balance_after: Money            // 매매 후 가상 잔고
  holding_after: Holding | null   // SELL로 전량 매도 시 null
}
```

**Errors**
- `422 INSUFFICIENT_BALANCE` — BUY 시 잔고 부족
- `422 INSUFFICIENT_QUANTITY` — SELL 시 보유 부족
- `422 MARKET_CLOSED` — 장 마감 (선택적 검증)
- `422 TRADING_HALTED` — 거래 정지 종목
- `422 PRICE_LIMIT_REACHED` — 상/하한가 도달
- `409 DUPLICATE_REQUEST` — idempotency_key 중복
- `429 TOO_MANY_REQUESTS` — 분당 30회 초과

**트랜잭션 보장**: ACCOUNT.balance 차감/증가 + HOLDING 업데이트 + ORDER 기록이 하나의 DB 트랜잭션 (`@transaction.atomic`).

---

### 4.3 GET /api/v1/orders

**Query**
```
side?: OrderSide
stock_code?: StockCode
status?: OrderStatus
from?: DateString
to?: DateString
page?: number = 1
size?: number = 20
```

**Response 200 OK**
```typescript
PaginatedResponse<Order>
```

---

### 4.4 GET /api/v1/orders/{id}

**Response 200 OK**
```typescript
{
  order: Order & {
    stock: Stock                  // 상세 화면용 종목 정보 포함
    related_diary_id?: number     // 연결된 일기 (있으면)
  }
}
```

**Errors**
- `404 NOT_FOUND`
- `403 FORBIDDEN` — 타인 주문 조회 시도

---

## 5. Portfolio 모듈 (5개)

### 5.1 GET /api/v1/portfolio

**Response 200 OK**
```typescript
{
  account: Account                // 잔고 정보
  total_invested: Money           // 매입 총액 합계
  total_current_value: Money      // 평가 금액 합계
  total_profit_loss: Money        // 총 평가 손익
  total_profit_loss_rate: Percent
  total_assets: Money             // = account.balance + total_current_value
  holdings_count: number
  holdings_preview: Holding[]     // 상위 5개 (가치 큰 순)
  generated_at: ISODateTime
}
```

> 통합 응답 — 홈 화면 포트폴리오 위젯에서 단일 호출로 사용.

---

### 5.2 GET /api/v1/portfolio/holdings

**Query**
```
sort?: "value" | "profit_loss" | "profit_loss_rate" | "code" = "value"
order?: "asc" | "desc" = "desc"
```

**Response 200 OK**
```typescript
{
  items: Holding[]
  total_count: number
  total_invested: Money
  total_current_value: Money
  total_profit_loss: Money
  generated_at: ISODateTime
}
```

---

### 5.3 GET /api/v1/portfolio/holdings/{code}

**Response 200 OK**
```typescript
{
  holding: Holding & {
    transaction_count: number     // 누적 매매 횟수
  }
  recent_orders: Order[]          // 최근 10건
  related_diaries_count: number
}
```

**Errors**
- `404 NOT_FOUND` — 해당 종목 보유 안 함

---

### 5.4 GET /api/v1/portfolio/balance

**Response 200 OK**
```typescript
{
  account: Account
}
```

---

### 5.5 GET /api/v1/portfolio/allocation

**Response 200 OK**
```typescript
{
  total_value: Money
  by_sector: {
    sector: string
    value: Money
    rate: Percent
  }[]
  by_stock: {                     // 종목별 비중 (상위 10 + 기타)
    stock_code: StockCode
    stock_name: string
    value: Money
    rate: Percent
  }[]
  cash_rate: Percent              // 현금 비중 (= account.balance / total_assets)
}
```

---

## 6. Recommend 모듈 (5 라우트) — 추천·관심·장투

전부 JWT 필요. 상세 동작은 `docs/투자자유형_기획안.md`, `616jy/장투케어_AI리포트_명세.md` 참고.

| Method · Path | 요청 | 응답(주요 필드) |
|---|---|---|
| GET `/api/v1/recommendations/` | `?limit` (기본 30, 최대 50) | `{ items: SwipeCard[], total, generated_at }` · 온보딩 미완 시 **409** |
| GET `/api/v1/watchlist/` | — | `{ items: WatchlistItem[], total }` |
| POST `/api/v1/watchlist/` | `{ stock_code }` | `WatchlistItem` · 없는 종목 **404** |
| DELETE `/api/v1/watchlist/{code}/` | — | **204** · 미보유 **404** |
| GET `/api/v1/longterm/ranking/` | `?limit` (기본 30, 최대 100) `?offset` | `{ items: RankItem[], total, limit, offset, generated_at }` · 온보딩 미완 **409** |
| GET `/api/v1/longterm/{code}/report/` | `?refresh=1` (캐시 무시·재생성) | `LongTermReport` · GMS 키 없으면 **503** · 없는 종목 **404** |

```typescript
interface SwipeCard {
  stock_code: string; stock_name: string; market: string; sector: string
  match_score: number; rank: number
  dna: { volatility: number|null; value_score: number|null; growth_score: number|null; stability: number|null }
  reason: string
  current_price: number|null; change_rate: number|null; like_count: number
}
interface WatchlistItem {
  stock_code: string; stock_name: string; market: string; sector: string
  current_price: number|null; change_rate: number|null; liked_at: ISODateTime; is_active: boolean
}
interface RankItem {  // 장투 총점 = 소계×0.7 + 궁합×0.3
  rank: number; stock_code: string; stock_name: string; market: string; sector: string
  longterm_total: number; subtotal: number; userfit: number
  financial: number|null; growth: number|null
}
interface LongTermReport {  // 장투 케어 AI 리포트 (GMS GPT-4o, rec_type='long_term' 캐시 TTL 1일)
  stock_code: string
  financial: Section; growth: Section; userfit: Section | null
  total: { score: number; grade: string; label: string; opinion: string }
}
interface Section { section: string; score: number; grade: string; summary: string }
```

---

## 7. Community 모듈 (9 라우트) — 게시글·댓글·팔로우

읽기는 공개, 쓰기는 JWT (`IsAuthenticatedOrReadOnly`). 좋아요·댓글 수정/삭제·팔로우는 JWT. 수정/삭제는 **작성자 본인만**.

| Method · Path | 요청 | 응답(주요 필드) |
|---|---|---|
| GET `/api/v1/posts/` | `?stock_code ?category ?page ?size` (size 기본20·최대100) | `{ items: Post[], page, size, total }` |
| POST `/api/v1/posts/` | `{ stock_code, category?, title, body }` | `Post` |
| GET `/api/v1/posts/{id}/` | — | `Post` (조회수 증가) |
| PATCH `/api/v1/posts/{id}/` | `{ title?, body?, category? }` | `Post` |
| DELETE `/api/v1/posts/{id}/` | — | **204** |
| POST `/api/v1/posts/{id}/like/` | — | `{ liked, like_count }` (토글) |
| GET `/api/v1/posts/{post_id}/comments/` | — | `{ items: Comment[], total }` |
| POST `/api/v1/posts/{post_id}/comments/` | `{ body }` | `Comment` |
| PATCH `/api/v1/comments/{id}/` | `{ body }` | `Comment` |
| DELETE `/api/v1/comments/{id}/` | — | **204** |
| POST `/api/v1/comments/{id}/like/` | — | `{ liked, like_count }` (토글) |
| POST `/api/v1/users/{user_id}/follow/` | — | 팔로우 |
| DELETE `/api/v1/users/{user_id}/follow/` | — | 언팔로우 |
| GET `/api/v1/users/{user_id}/followers/` | — | `{ items: {user_id,nickname}[], total }` (공개) |
| GET `/api/v1/users/{user_id}/following/` | — | `{ items: {user_id,nickname}[], total }` (공개) |

```typescript
interface Post {
  id: number; user_id: number; nickname: string
  stock_code: string|null; stock_name: string|null
  category: string; title: string; body: string
  view_count: number; like_count: number; comment_count: number
  is_liked: boolean; created_at: ISODateTime
}
interface Comment { id: number; post_id: number; user_id: number; nickname: string; body: string; created_at: ISODateTime }
```

---

## 8. Diary 모듈 (2 라우트) — 투자 일지

전부 JWT, 본인 일지만 조회/수정/삭제.

| Method · Path | 요청 | 응답(주요 필드) |
|---|---|---|
| GET `/api/v1/diaries/` | `?stock_code ?action_type(BUY/SELL/WATCH) ?page ?size` | `{ items: Diary[], page, size, total }` |
| POST `/api/v1/diaries/` | `DiaryWrite` | `Diary` |
| GET `/api/v1/diaries/{id}/` | — | `Diary` |
| PATCH `/api/v1/diaries/{id}/` | `DiaryWrite` (부분) | `Diary` |
| DELETE `/api/v1/diaries/{id}/` | — | **204** |

```typescript
interface DiaryWrite {
  stock_code: string; order_id?: number|null
  action_type: "BUY" | "SELL" | "WATCH"
  reason_category?: string; confidence: number  // 1~5
  target_price?: number|null; stop_loss_price?: number|null; memo?: string
}
interface Diary extends DiaryWrite {
  id: number; stock_name: string; created_at: ISODateTime; updated_at: ISODateTime
}
```

---

## 9. News 모듈 (7 라우트) — 뉴스

> 상세 명세(요청/응답 필드)는 **[NEWS_API_SPEC.jy.md](NEWS_API_SPEC.jy.md)**. 여기선 라우트 요약만.

| Method · Path | 권한 | 설명 |
|---|---|---|
| GET `/api/v1/news/` | 공개 | 뉴스 검색 |
| GET `/api/v1/news/economy/` | 공개 | 경제 뉴스 피드 |
| GET `/api/v1/news/feed/{category}/` | 공개 | 카테고리별 피드 |
| GET `/api/v1/news/by-sector/` | 공개 | 섹터별 뉴스 |
| GET `/api/v1/news/stocks/{code}/` | 공개 | 특정 종목 뉴스 |
| GET `/api/v1/news/holdings/` | JWT | 내 보유 종목 뉴스 |
| GET `/api/v1/news/watchlist/` | JWT | 내 관심 종목 뉴스 |

---

## 10. 권한 · 캐싱 · 배치(cron) 요약

### 10.1 권한 정책별 엔드포인트

| 정책 | 엔드포인트 |
|---|---|
| **공개** (AllowAny) | `auth: signup·login·token/refresh·password/reset` · `GET /stocks/*` · `/markets/summary` · `/economic-events/` · `news: /·economy·feed/{cat}·by-sector·stocks/{code}` · `GET /users/{id}/followers·following` |
| **읽기공개·쓰기JWT** (IsAuthenticatedOrReadOnly) | `/posts/` · `/posts/{id}/` · `/posts/{post_id}/comments/` (GET 공개, 작성·수정·삭제 JWT) |
| **JWT** (IsAuthenticated) | `auth me·logout·onboarding` · `orders/*` · `portfolio/*` · `recommendations` · `watchlist/*` · `longterm/*` · `diaries/*` · 좋아요·팔로우 · `news/holdings·watchlist` |
| **JWT + 본인만** | `orders/*`·`portfolio/*`(계정 소유자) · `diaries/*`(작성자) · `posts·comments` 수정/삭제(작성자) |

> Rate Limit(django-ratelimit, Redis 백엔드, 설정상): `signup·password/reset` 3/m·IP · `login` 5/m·IP · `token/refresh` 30/m·IP · `stocks` 100/m(비로그인)·1000/m(로그인) · `orders/preview` 60/m · `orders` 30/m. 그 외 미적용.

### 10.2 캐싱 (응답/결과)

| 엔드포인트 | 저장소 | TTL |
|---|---|---|
| `GET /stocks/{code}/price/` | Redis | 장중 3s / 장외 60s |
| `GET /stocks/{code}/chart/` | Redis | 분봉 5분 / 일봉 1시간 |
| `GET /markets/summary/` | Redis | **5s** |
| `GET /stocks/{code}/orderbook/` | Redis | 장중 **1s** / 장외 **30s** |
| `GET /longterm/{code}/report/` | DB `recommendation_cache` (rec_type=`long_term`) | **1일** — LLM 재호출 방지, `?refresh=1`로 무효화 |
| `GET /recommendations/` | DB `recommendation_cache` (rec_type=`onboarding`) 부수 기록 | 1일 |

> 그 외(community·diary·news·portfolio·orders 등)는 응답 캐시 없음.

### 10.3 배치 (management command)

> 데이터 적재 배치는 오케스트레이터 **`python manage.py run_batch {daily|weekly|hourly}`** 로 의존 순서대로 묶어 실행(`stocks/management/commands/run_batch.py`). 스케줄러(cron 등) **미등록** — 권장 주기는 아래.
> 의존 순서: 마스터 → 메타·플래그 → 가격 → 지표 → 재무 → DNA·장투점수.

| 커맨드 | 목적 | run_batch 묶음 | 권장 주기 |
|---|---|---|---|
| `sync_stock_master` · `sync_us_stock_master` | KIS 마스터로 KR/US 종목 적재 | weekly | 주 1회 |
| `enrich_stock_meta_from_dart` · `_from_kis` · `enrich_us_stock_meta` | 섹터·시총·CEO·PER/PBR 등 메타 보강 | weekly | 주 1회 / 수시 |
| `sync_us_index_flags` | S&P500·NASDAQ100 플래그 + 비인덱스 비활성화 | weekly | 주 1회 |
| `normalize_sectors` | 섹터명 KR 기준 정규화 (Stock·StockDna) | weekly | 마스터/메타 갱신 후 |
| `enrich_financials` | DART/yfinance 재무 + roe/roa/배당 | weekly | 분기 (공시 후) |
| `sync_stock_prices` | KIS(KR)/yfinance(US) 일봉 수집 | daily | **매일** (장 마감 후) |
| `calc_market_indicators` | beta·volatility·52주 고저 계산 | daily | **매일** (가격 후) |
| `calc_stock_dna` | 4축 DNA 분위수 정규화 | daily | **매일** (지표·재무 후) |
| `calc_longterm_scores` | 장투 소계(재무·성장) 적재 | daily | **매일** (지표·재무 후) |
| `ingest_rss` | 연합뉴스 RSS 수집·태깅 | hourly | 시간별 |
| `seed_economic_events` | 경제 캘린더 목업 시드 | — | 1회 / 수시 |

**🔴 실시간 워머 (run_batch 묶음과 별개 — 의존성 없음, 장중에만 짧은 주기로 반복):**

| 커맨드 | 목적 | 주기 |
|---|---|---|
| `warm_volume_power` | 인기 top-N(기본 120) 체결강도를 KIS 페이싱(초당 ≤chunk) 조회 → Redis `stock:volpower:*` 워밍 (TTL 60s). 랭킹 API는 이 캐시만 읽음(라이브 KIS 0콜), 미스 종목만 요청 경로서 ≤8개 즉석 채움 | **장중 ~30초** |

> ⚠️ `warm_volume_power`는 **cron(분 단위)로 부족** — 30초 루프 래퍼(`while; sleep 30`)·systemd timer·전용 워커로 돌리고, **시장시간(KR 09:00–15:30 / US 23:30–06:00 KST)에만** 실행. 데이터 파이프라인이 아니라 §10.2 캐시(`stock:volpower:*`)를 채우는 워머라 `run_batch`에 안 들어감.

---

## 11. Django 구현 노트

### 11.1 모델 매핑 가이드 (ERD 1:1 매칭)

| 도메인 타입 | Django 모델 (앱.Model) | ERD 테이블 | 비고 |
|---|---|---|---|
| User | `accounts.User` (AbstractUser 확장) | `USER` | username, email, nickname, birth_year |
| InvestmentProfile | `accounts.InvestmentProfile` | `USER_INVESTMENT_PROFILE` | User와 OneToOne |
| Account | `portfolio.Account` | `ACCOUNT` | User와 OneToOne, balance |
| Stock | `stocks.Stock` | `STOCK` | code unique, pykrx 마스터 |
| StockPrice | DB 모델 X | — | KIS API + Redis 캐시 |
| OrderBook | DB 모델 X | — | KIS API + Redis 캐시 |
| Candle (일봉) | `stocks.StockPrice` | `STOCK_PRICE` | 일봉 OHLCV 저장 |
| Candle (분봉) | DB 모델 X | — | Redis 5분 캐시 |
| FinancialSummary | `stocks.FinancialSummary` | `FINANCIAL_SUMMARY` | DART 분기 적재 |
| StockIndicator | `stocks.StockIndicator` | `STOCK_INDICATOR` | 일일 계산 배치 |
| Holding | `portfolio.Holding` | `HOLDING` | (user, stock) unique |
| Order | `portfolio.Order` | `ORDER` | DB 트랜잭션 필수, idempotency_key unique |

### 11.2 핵심 트랜잭션 패턴 (주문 실행)

```python
@transaction.atomic
def execute_order(user, stock_code, side, quantity, idempotency_key):
    # 0. 중복 체크
    if Order.objects.filter(idempotency_key=idempotency_key).exists():
        raise DuplicateRequestError()

    # 1. 현재가 조회 (KIS, Redis 캐시 활용)
    current_price = stock_service.get_price(stock_code)

    # 2. 검증 (잔고/보유/거래정지 등)
    validate_order(user, stock_code, side, quantity, current_price)

    # 3. ACCOUNT 차감/증가 + HOLDING 갱신 + ORDER 기록
    account = user.account
    stock = Stock.objects.get(code=stock_code)

    if side == "BUY":
        account.deduct(current_price * quantity)
        holding, _ = Holding.objects.get_or_create(
            user=user, stock=stock,
            defaults={"quantity": 0, "average_price": 0}
        )
        holding.add(quantity, current_price)
    else:  # SELL
        holding = Holding.objects.select_for_update().get(user=user, stock=stock)
        realized = holding.subtract(quantity, current_price)
        account.add(current_price * quantity)

    order = Order.objects.create(
        user=user, account=account, stock=stock,
        side=side, quantity=quantity, price=current_price,
        total_amount=current_price * quantity,
        status="FILLED",
        idempotency_key=idempotency_key,
        executed_at=timezone.now(),
    )
    return order
```

`@transaction.atomic`이 모든 DB 변경을 묶어서 중간 실패 시 전체 롤백.

### 11.3 권장 라이브러리

- `djangorestframework-simplejwt` — JWT
- `drf-spectacular` — Swagger 자동 생성 (SCRUM-48)
- `django-cors-headers` — CORS
- `django-ratelimit` — Rate limiting
- `django-environ` — 환경변수 관리
- `psycopg[binary]` — PostgreSQL
- `redis` + `django-redis` — 캐시

---

## 12. 다음 차분 안내

| 차분 | 시점 | 모듈 |
|---|---|---|
| **v1.1 (이 문서)** | 2026-05-13 | Auth · Stock · Order · Portfolio (ERD 정합) |
| ~~v2~~ ✅ | 2026-06-23 구현·문서화 완료 | Recommend · Watchlist (§6) |
| ~~v3~~ ✅ | 2026-06-23 구현·문서화 완료 | News(§9) · Community(§7) · Diary(§8) |
| v4 | Phase 3 시작 즈음 | Notification · Home BFF |

각 차분은 v(N)으로 versioning. v(N+1)는 v(N)의 도메인 타입을 재사용·확장.

---

## 13. 변경 이력

| 일자 | 변경 | 담당 |
|---|---|---|
| 2026-05-13 | v1 초안 — 핵심 4모듈 25 엔드포인트 + 8개 도메인 타입 | 강재민 |
| 2026-05-13 | **v1.1 ERD 정합성 패치** — `Transaction`→`Order`, `VirtualAccount`→`Account`, `Financial`→`FinancialSummary`+`StockIndicator` 분리, Stock 필드 풍부화, Trading URL `/trades`→`/orders` | 강재민 |
| 2026-06-01 | **v1.2** — URL trailing slash 전면 통일(Auth/Stock/Order/Portfolio), Stock 조회 API `GET /stocks/`·`/{code}/`·`/{code}/price/` 실구현(KIS 분기 + 장중3s·장외60s 캐시) | 강재민 |
| 2026-06-01 | **v1.3** — 캔들 차트 API `GET /stocks/{code}/chart/` 실구현. 일봉/주봉/월봉=DB(StockPrice resample), 분봉=KIS(KR FHKST03010200 1m + 클라이언트 _resample / US HHDFS76950200 NMIN). 장중 today 한 칸 합성(B 패턴, 일봉 한정). 캐싱: 분봉 5분 / 일봉 1시간. period×interval 유효성 400 | 강재민 |
| 2026-06-22 | **v1.4** — `risk_type` 제거 → `investment_style`(성향 4유형), onboarding 요청 스키마를 q1~q6로 정정 | 강재민 |
| 2026-06-23 | **v1.5** — 누락 모듈 문서화: Recommend(§6)·Community(§7)·Diary(§8)·News(§9 요약)·economic-events(§3.9). [URL_MAP.md](URL_MAP.md) 신설, 섹션 재번호(기존 6~9 → 10~13). §10 권한·캐싱·배치(cron) 3표 정리(markets TTL 10초→**5s** 정정). 파일명 `API_스키마_v1.md` → `API_스키마_v1.5.md` 동기화 | 강재민 |
| 2026-06-24 | §10.3에 `warm_volume_power`(장중 체결강도 Redis 워머, run_batch 묶음과 별개) 추가 + 데이터 배치를 `run_batch {daily/weekly/hourly}` 오케스트레이터로 묶음 매핑 | 강재민 |
