# 주만추 API 스키마 v1.1 (핵심 4모듈 — ERD 정합)

> SCRUM-46 (1.3.2 Request/Response 스키마 정의) 산출물 — 1차분
> 작성일: 2026-05-13 · 갱신: ERD 정합성 패치 (v1 → v1.1)
> 범위: Auth · Stock · Trading(Order) · Portfolio (25개 엔드포인트)
> 다음 차분: Recommend·Watchlist (1주 후), News·Community·Diary (2주 후)
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
  risk_type: RiskType
  investment_style?: string         // "장기 투자", "단기 트레이딩" 등
  preferred_period?: number         // 선호 보유 기간(개월)
  preferred_sector?: string         // "반도체", "2차전지" 등
  updated_at: ISODateTime
}

type RiskType = "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE"
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

DB 저장 X (KIS API + Redis 캐시 1초).

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
  risk_type: RiskType
  investment_style?: string
  preferred_period?: number      // 보유 기간(개월)
  preferred_sector?: string
}
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

## 3. Stock 모듈 (8개)

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

## 6. 엔드포인트별 권한·캐싱 요약

| 엔드포인트 | 권한 | 캐시 | Rate Limit |
|---|---|---|---|
| POST /auth/signup | ⚪ | — | 3/m IP |
| POST /auth/login | ⚪ | — | 5/m IP |
| POST /auth/logout | 🔒 | — | — |
| POST /auth/token/refresh | refresh Cookie | — | 30/m IP |
| GET/PATCH /auth/me | 🔒 | — | — |
| POST /auth/onboarding | 🔒 | — | — |
| POST /auth/password/reset | ⚪ | — | 3/m IP |
| GET /stocks* (조회) | ⚪ | 종류별 | 100/m anon · 1000/m user |
| GET /markets/summary | ⚪ | 10초 | — |
| POST /orders/preview | 🔒 | — | 60/m user |
| POST /orders | 🔒 👤 | — | 30/m user |
| GET /orders* | 🔒 👤 | — | — |
| GET /portfolio* | 🔒 👤 | — | — |

---

## 7. Django 구현 노트

### 7.1 모델 매핑 가이드 (ERD 1:1 매칭)

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

### 7.2 핵심 트랜잭션 패턴 (주문 실행)

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

### 7.3 권장 라이브러리

- `djangorestframework-simplejwt` — JWT
- `drf-spectacular` — Swagger 자동 생성 (SCRUM-48)
- `django-cors-headers` — CORS
- `django-ratelimit` — Rate limiting
- `django-environ` — 환경변수 관리
- `psycopg[binary]` — PostgreSQL
- `redis` + `django-redis` — 캐시

---

## 8. 다음 차분 안내

| 차분 | 시점 | 모듈 |
|---|---|---|
| **v1.1 (이 문서)** | 2026-05-13 | Auth · Stock · Order · Portfolio (ERD 정합) |
| v2 | 약 1주 후 (SCRUM-25 시작 전) | Recommend · Watchlist |
| v3 | 약 2주 후 (SCRUM-26 시작 전) | News · Community · Diary |
| v4 | Phase 3 시작 즈음 | Notification · Home BFF |

각 차분은 v(N)으로 versioning. v(N+1)는 v(N)의 도메인 타입을 재사용·확장.

---

## 9. 변경 이력

| 일자 | 변경 | 담당 |
|---|---|---|
| 2026-05-13 | v1 초안 — 핵심 4모듈 25 엔드포인트 + 8개 도메인 타입 | 강재민 |
| 2026-05-13 | **v1.1 ERD 정합성 패치** — `Transaction`→`Order`, `VirtualAccount`→`Account`, `Financial`→`FinancialSummary`+`StockIndicator` 분리, Stock 필드 풍부화, Trading URL `/trades`→`/orders` | 강재민 |
| 2026-06-01 | **v1.2** — URL trailing slash 전면 통일(Auth/Stock/Order/Portfolio), Stock 조회 API `GET /stocks/`·`/{code}/`·`/{code}/price/` 실구현(KIS 분기 + 장중3s·장외60s 캐시) | 강재민 |
| 2026-06-01 | **v1.3** — 캔들 차트 API `GET /stocks/{code}/chart/` 실구현. 일봉/주봉/월봉=DB(StockPrice resample), 분봉=KIS(KR FHKST03010200 1m + 클라이언트 _resample / US HHDFS76950200 NMIN). 장중 today 한 칸 합성(B 패턴, 일봉 한정). 캐싱: 분봉 5분 / 일봉 1시간. period×interval 유효성 400 | 강재민 |
