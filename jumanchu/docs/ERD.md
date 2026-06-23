# 주만추 ERD (텍스트 정의)

> 작성일: 2026-05-17 — 회의 결정 반영본
> 시각적 ERD는 `planning/모델_서비스flow/erd.html` 갱신 필요. 이 문서가 진실의 원천(Source of Truth).

## 0. 변경 요약 (vs 초기 ERD)

| 구분 | 변경 |
|---|---|
| 🆕 신규 | `ACCOUNT` (가상 잔액), `ORDER` (시스템 매매 기록) |
| 🔄 변경 | `STOCK` (5개 필드 보강 + 메타 4개: description/homepage_url/ceo_name/employee_count — API_스키마_v1.5.md §3.2 정합), `ORDER` (fee/tax 보강), `FINANCIAL_STATEMENT` (원본 X, 가공 지표만), `STOCK_DIARY` (매매 정보 → ORDER 이관, 일기 책임만) |
| ⏸️ 보류 | `STOCK_RECOMMENDATION` — 추천 트랙 1 완료 후 재검토 |
| 📌 정책 | `STOCK_PRICE` 일봉만 DB, 실시간 시세는 Redis 캐싱 (DB 저장 X) |

---

## 1. 도메인 구조

```
사용자 ─── 추천 (Algo) ─── 종목 마스터 ─── 거래/보유 ─── 일기/회고
                                              │
                                              └─── 커뮤니티
```

5개 도메인 (기존과 동일).

---

## 2. 모델 정의

### 2.1 사용자 도메인

#### `USER` (변경 없음)
| 필드 | 타입 | 비고 |
|---|---|---|
| id | int PK | |
| username, password, email, nickname | string | |
| birth_year | int | US-02 "생년=상장연도" 프로필 추천에 활용 (신규 권장) |
| created_at | datetime | |

#### `USER_INVESTMENT_PROFILE`
1:1 USER. investment_style(성향 4유형 라벨), preferred_period, preferred_sector + 온보딩 5벡터(risk_tolerance·investment_term·experience·loss_aversion·behavior)·signature_stock. (상세 컬럼은 `erd.dbml`)

---

### 2.2 종목 도메인

#### `STOCK` 🔄 보강
| 필드 | 타입 | 비고 |
|---|---|---|
| id | int PK | |
| code | string | 종목 코드 (예: "005930") |
| name | string | |
| market | string | KOSPI/KOSDAQ/NASDAQ/S&P500 |
| sector, industry | string | |
| **market_cap** 🆕 | bigint | 시가총액 (원/달러, currency 따라) |
| **listed_at** 🆕 | date | 상장일 |
| **currency** 🆕 | string | "KRW" or "USD" |
| **kis_short_code** 🆕 | string | KIS API 호출용 코드 (한국 6자리, 미국 티커) |
| **is_active** 🆕 | bool | 상장폐지 여부 |
| **is_sp500** 🆕 | bool | S&P 500 구성 종목 여부 |
| **is_nasdaq100** 🆕 | bool | NASDAQ 100 구성 종목 여부 |
| **description** 🆕 | text | 회사 소개 (KIS 종목 기본정보 또는 yfinance) |
| **homepage_url** 🆕 | string | 홈페이지 URL |
| **ceo_name** 🆕 | string | 대표자명 |
| **employee_count** 🆕 | int | 종업원 수 |
| updated_at | datetime | KIS 마스터 갱신 시각 |

인덱스: `(code, market)` unique, `(market, is_active)` for filtering, `(is_sp500)`, `(is_nasdaq100)` for index 필터.

#### `STOCK_PRICE` (일봉만)
| 필드 | 타입 | 비고 |
|---|---|---|
| id | int PK | |
| stock_id | FK → STOCK | |
| price_date | date | 거래일 |
| open, high, low, close | int/decimal | OHLC |
| volume | bigint | |

**정책**: 일봉만 저장. 실시간 현재가는 **DB 저장 X, Redis 5~10초 캐싱**.
인덱스: `(stock_id, price_date)` unique.

#### `STOCK_INDICATOR` 🔄 보강 (시장 지표)
> 각 컬럼 상세는 [`docs/DART_COLUMN.md`](./DART_COLUMN.md)

| 필드 | 타입 | 우선순위 | 출처 |
|---|---|---|---|
| stock_id | FK | — | |
| **가치 평가** | | | |
| per | float | P0 | KIS / 자체 |
| pbr | float | P0 | KIS / 자체 |
| eps | int | P0 | KIS / DART 계산 |
| roe | float | P0 | DART 기반 자체 계산 |
| roa | float | P1 | 순이익 / 총자산 |
| **배당** | | | |
| dividend_yield | float | P0 | KIS / 자체 |
| **시장 변동성** (일봉 기반 자체 계산) | | | |
| beta | float | P1 | KOSPI/S&P500 대비 변동성. 60일 이상 데이터 필요 |
| volatility | float | P1 | 일별 수익률 표준편차 (연환산) |
| high_52w | int | P1 | 52주 최고가 |
| low_52w | int | P1 | 52주 최저가 |
| **메타** | | | |
| calculated_date | date | — | |

**정책**: 일 1회 배치 갱신 (장 종료 후). beta·volatility는 STOCK_PRICE 일봉 데이터 누적 후 의미 있는 값. 초기 60일은 NULL 허용.

#### `FINANCIAL_SUMMARY` 🔄 재정의 (구 FINANCIAL_STATEMENT)
> "재무제표 자체가 아닌, 유용한 지표만 뽑아서 저장" — 각 컬럼 상세는 [`docs/DART_COLUMN.md`](./DART_COLUMN.md)

| 필드 | 타입 | 우선순위 | 비고 |
|---|---|---|---|
| id | int PK | — | |
| stock_id | FK | — | |
| fiscal_period | string | — | "2025Q3", "2025A" |
| **원본 (DART/yfinance)** | | | |
| revenue | bigint | — | 매출액 |
| operating_profit | bigint | — | 영업이익 |
| net_profit | bigint | — | 당기순이익 |
| **수익성** | | | |
| operating_margin | float | P0 | 영업이익 / 매출 |
| net_margin | float | P0 | 순이익 / 매출 |
| **성장성** | | | |
| revenue_yoy | float | P0 | 전년 동기 매출 성장률 |
| operating_profit_yoy | float | P0 | 전년 동기 영업이익 성장률 |
| net_profit_yoy | float | P0 | 전년 동기 순이익 성장률 |
| **안정성** | | | |
| debt_ratio | float | P0 | 부채 / 자기자본 |
| equity_ratio | float | P1 | 자기자본 / 총자산 |
| current_ratio | float | P1 | 유동자산 / 유동부채 |
| **배당** | | | |
| payout_ratio | float | P1 | 배당금 / 순이익 |
| **메타** | | | |
| data_source | string | — | "DART" / "yfinance" |
| fetched_at | datetime | — | 마지막 갱신 |

**정책**: Lazy + 영구 캐싱. 분기 단위(3개월)로 stale 판정 → 재갱신.
**인덱스**: `(stock_id, fiscal_period)` unique.
**컬럼 상세 설명·계산식·활용**: → `docs/DART_COLUMN.md`

#### `STOCK_NEWS`, `NEWS_RELATED_STOCK` (변경 없음, 추천 트랙 1.4에서 사용 여부 결정)

---

### 2.3 거래/보유 도메인 (재구성)

#### `ACCOUNT` 🆕 (가상 잔액)
| 필드 | 타입 | 비고 |
|---|---|---|
| id | int PK | |
| user_id | FK → USER (1:1) | |
| balance | decimal(15,0) | 잔액 (원). 시드 100_000_000 |
| initial_balance | decimal(15,0) | 초기 원금 (시드 100_000_000 + 온보딩 보너스 누적). 수익률 기준점 |
| created_at, updated_at | datetime | |

**제약**: `CHECK (balance >= 0)`.
**Signal**: User 생성 시 ACCOUNT 자동 생성 + balance=100_000_000.

#### `HOLDING` (변경 없음)
user_id, stock_id, quantity, average_price, first_acquired_at, updated_at.
`(user_id, stock_id)` unique. `CHECK (quantity >= 0)`.

#### `ORDER` 🆕 (시스템 자동 매매 기록)
| 필드 | 타입 | 비고 |
|---|---|---|
| id | int PK | |
| user_id | FK → USER | |
| account_id | FK → ACCOUNT | 잔액 영향 추적 |
| stock_id | FK → STOCK | |
| side | enum | BUY / SELL |
| quantity | int | |
| price | decimal | 체결가 |
| total_amount | decimal | quantity × price (감사용) |
| **fee** 🆕 | decimal | 수수료 (모의 매매 기본 0, 추후 정책에 따라 부과) |
| **tax** 🆕 | decimal | 매도 거래세 (모의 매매 기본 0) |
| status | enum | PENDING / FILLED / FAILED (비동기 대비) |
| idempotency_key | string unique | 중복 매수/매도 차단 |
| created_at | datetime | 요청 시각 |
| executed_at | datetime nullable | 체결 시각 |

인덱스: `(user_id, created_at desc)` 매매 이력 조회.

#### `STOCK_DIARY` 🔄 단순화 (매매 정보 → ORDER 이관)
| 필드 | 타입 | 비고 |
|---|---|---|
| id | int PK | |
| user_id | FK → USER | |
| stock_id | FK → STOCK | |
| **order_id** 🆕 | FK → ORDER nullable | 관련 거래 (없으면 관심 종목 일기) |
| action_type | enum | BUY/SELL/WATCH (WATCH = 관심) |
| reason_category | string | |
| reason_text | text | |
| confidence | int 1~5 | |
| target_price, stop_loss_price | decimal nullable | |
| related_news_id | FK → STOCK_NEWS nullable | |
| diary_date | date | |

> 매매 정보(price/quantity)는 ORDER에서 조회. 일기는 "왜 샀나, 어떤 마음이었나"에 집중.

#### `DIARY_REVIEW` (변경 없음)
1:1 STOCK_DIARY. actual_return, judgment, lesson, reviewed_at.

---

### 2.4 추천 도메인 ⏸️ 보류

#### `STOCK_RECOMMENDATION` (기존 유지, 트랙 1 후 재검토)
> 추천 트랙 1.1 "추천 종류 정의" + 1.2 "입력 변수 매핑" 완료 후 필드 확정. 현재는 기존 구조 그대로.

---

### 2.5 커뮤니티 도메인 (변경 없음)

`SHARED_PORTFOLIO`, `SHARED_PORTFOLIO_ITEM`, `COMMUNITY_POST`, `COMMENT`, `POST_LIKE`.

---

## 3. 데이터 소스 매트릭스

| 모델 | 출처 | 적재 방식 | 갱신 주기 |
|---|---|---|---|
| `STOCK` (마스터) | KIS 마스터 + yfinance | 1회성 배치 | 월 1회 또는 분기 |
| `STOCK_PRICE` (일봉) | KIS / yfinance | 배치 | 일 1회 (장 종료 후) |
| **실시간 시세** | KIS API | **Redis 캐싱**, DB 저장 X | 요청 시 5~10초 캐싱 |
| `STOCK_INDICATOR` | KIS or 자체 계산 | 배치 | 일 1회 |
| `FINANCIAL_SUMMARY` | DART / yfinance | **Lazy + 영구 캐싱** | 첫 조회 시 + 분기 stale |
| `STOCK_NEWS` | NewsData / Gnews | 추천 트랙 1.4에서 결정 | TBD |
| `ACCOUNT`, `HOLDING`, `ORDER` | 자체 (사용자 행위) | 실시간 (atomic transaction) | — |
| `STOCK_DIARY`, `DIARY_REVIEW` | 자체 | 실시간 | — |
| `STOCK_RECOMMENDATION` | Algo | 트랙 2 완료 후 결정 | TBD |
| 커뮤니티 모델 | 자체 | 실시간 | — |

---

## 4. 적재·갱신 전략 상세

### 4.1 종목 마스터 (STOCK)

**적재 범위 (회의 확정)**:

| 마켓 | 종목 수 | 데이터 소스 (하이브리드 전략) |
|---|---|---|
| KOSPI 전체 | ~800 | **pykrx** (코드 리스트) + **KIS API** (종목별 상세) |
| KOSDAQ 전체 | ~1600 | **pykrx** (코드 리스트) + **KIS API** (종목별 상세) |
| S&P 500 | 500 | **Wikipedia/Slickcharts** (구성종목 리스트) + **yfinance** (종목별 상세) |
| NASDAQ 100 | 100 | **Wikipedia/Slickcharts** (구성종목 리스트) + **yfinance** (종목별 상세) |
| **합계 (unique)** | **약 ~3000** | (S&P 500과 NASDAQ 100은 약 80개 중복) |

> **왜 하이브리드?** pykrx는 인증 없이 종목 코드를 일괄 조회하기 좋고, KIS는 종목별 상세 정보(시가총액·섹터)가 풍부. 한 도구로 다 하면 어느 한쪽이 약점이 됨. 미국은 KIS의 해외주식 종목 정보도 가능하지만, yfinance + 공개 구성종목 리스트가 더 빠르고 메타 정보 풍부.

**적재 흐름**:
1. **한국**: pykrx `get_market_ticker_list(market='KOSPI'|'KOSDAQ')` → 종목 코드 리스트 일괄 확보 → 종목코드 하나씩 KIS API 호출하여 상세 메타(이름·시가총액·섹터·업종·상장일) 수집 → STOCK 행 생성 (`currency='KRW'`, `kis_short_code=종목코드`)
2. **미국**: Wikipedia/Slickcharts에서 S&P 500, NASDAQ 100 구성종목 티커 리스트 확보 → 티커별 yfinance 호출 → STOCK 행 생성 (`currency='USD'`, `market='NYSE'|'NASDAQ'`, `is_sp500=True` 또는 `is_nasdaq100=True`)
3. S&P 500과 NASDAQ 100에 둘 다 포함되는 종목(예: AAPL, MSFT)은 두 bool 컬럼 모두 True

**갱신 주기**:
- 종목 마스터 자체 (신규 상장/폐지/시가총액): **월 1회 배치**
- 지수 구성종목 변동 (S&P 500/NASDAQ 100 리밸런싱): **분기 1회 점검** — 새로 편입/제외된 종목 is_sp500/is_nasdaq100 갱신

**관리 명령**:
```bash
# 전체 종목 마스터 동기화 (초기 + 월간)
python manage.py sync_stock_master --market all

# 특정 마켓만
python manage.py sync_stock_master --market KOSPI,KOSDAQ
python manage.py sync_stock_master --market US  # S&P 500 + NASDAQ 100

# 지수 구성종목만 (분기)
python manage.py sync_index_membership --index sp500,nasdaq100
```

**예외 처리**:
- pykrx/yfinance 한 호출 실패 → 해당 종목만 skip 후 로그, 나머지 계속 진행
- 기존 DB에 있던 종목이 마스터에서 빠짐 → `is_active=False` 처리 (삭제 X, 이력 보존)

### 4.2 일봉 시세 (STOCK_PRICE)
- **초기 적재**: 종목당 최근 3년치 일봉 (차트용)
- **일일 갱신**: 매일 16:30 (장 종료 후) Celery beat로 KIS 배치 호출
- **누락 보정**: 휴장일/장애 시 다음 날 누락분 자동 백필

### 4.3 실시간 현재가 (DB 저장 X)
- **요청 시 흐름**: API 호출 → Redis `GET stock:price:{ticker}` → cache miss면 KIS API 호출 → Redis `SETEX stock:price:{ticker} 10 {price}` → 응답
- **TTL**: 장중 5~10초, 장외 60초

### 4.4 재무 요약 (FINANCIAL_SUMMARY) — Lazy + 영구 캐싱
- 사용자가 종목 상세 진입 시:
  1. `FINANCIAL_SUMMARY.fetched_at`이 90일 이내면 → DB에서 즉시 반환
  2. 90일 초과 또는 데이터 없음 → DART/yfinance 호출 → 가공 → upsert → 반환
- 가공 로직 예시:
  - `revenue_yoy = (current_revenue - prev_year_revenue) / prev_year_revenue`
  - `operating_margin = operating_profit / revenue`
  - `debt_ratio = liabilities / total_assets`
- **첫 사용자만 약간 느림** (1~3초), 이후 모두 빠름.

### 4.5 거래 데이터 (ACCOUNT/HOLDING/ORDER)
- **항상 atomic transaction** (`with transaction.atomic():`)
- `select_for_update()`로 동시성 보호
- `ORDER.idempotency_key`로 중복 매수 차단
- 자세히 → US-12, US-13 인수 조건

---

## 5. 트랜잭션 경계 (매수 예시)

```python
with transaction.atomic():
    account = Account.objects.select_for_update().get(user=user)
    if account.balance < total:
        raise InsufficientBalance
    account.balance -= total
    account.save()

    holding, _ = Holding.objects.select_for_update().get_or_create(
        user=user, stock=stock, defaults={'quantity': 0, 'average_price': 0}
    )
    new_qty = holding.quantity + quantity
    holding.average_price = (holding.quantity * holding.average_price + quantity * price) / new_qty
    holding.quantity = new_qty
    holding.save()

    order = Order.objects.create(
        user=user, account=account, stock=stock,
        side='BUY', quantity=quantity, price=price, total_amount=total,
        status='FILLED', idempotency_key=key, executed_at=now()
    )
```

---

## 6. 정규화·인덱스 설계 (SCRUM-43)

### 6.1 정규화 수준 — 3NF 기반 + 의도적 비정규화

ERD는 **3NF(3차 정규형)을 기본**으로 하되, 성능·트랜잭션 단순화를 위해 일부 컬럼을 **의도적으로 비정규화**한다.

| 모델 | 비정규화 컬럼 | 원본 계산 가능 출처 | 이유 |
|---|---|---|---|
| `HOLDING` | `average_price` | ORDER 합산 평균 | 자주 조회되므로 캐싱 |
| `ACCOUNT` | `balance` | ORDER 합산 (BUY −, SELL +) | 락 단순화 — 잔액 변경마다 select_for_update |
| `ORDER` | `total_amount` | `quantity × price` | 감사·통계 조회용 |
| `COMMUNITY_POST` | `view_count` | 조회 이벤트 합 | 캐시 |
| `SHARED_PORTFOLIO` | `view_count` | 동일 | 캐시 |

> 비정규화 컬럼은 **트랜잭션 안에서 일관성을 직접 유지**해야 한다. 예) 매수 시 `balance·quantity·average_price`를 한 `atomic` 블록에서 모두 갱신.

### 6.2 인덱스 명세

#### 사용자 도메인
- `USER`: `(email)` unique, `(username)` unique
- `USER_INVESTMENT_PROFILE`: `(user_id)` unique (1:1)

#### 종목 도메인
- `STOCK`:
  - `(code, market)` unique
  - `(kis_short_code)` unique
  - `(market, is_active)` — 활성 종목 필터
  - `(is_sp500)`, `(is_nasdaq100)` — 지수 종목 필터
- `STOCK_PRICE`: `(stock_id, price_date)` unique — 차트 조회 시 `(stock_id, price_date DESC)` 활용
- `STOCK_INDICATOR`: `(stock_id, calculated_date)` unique
- `FINANCIAL_SUMMARY`: `(stock_id, fiscal_period)` unique
- `STOCK_NEWS`: `(published_at DESC)` — 최근 뉴스
- `NEWS_RELATED_STOCK`: `(news_id, stock_id)` unique, `(stock_id)` — 종목별 뉴스

#### 거래 도메인 ⭐
- `ACCOUNT`: `(user_id)` unique (1:1)
- `HOLDING`: `(user_id, stock_id)` unique
- `ORDER` (트랜잭션 핵심 — 인덱스가 성능 좌우):
  - `(idempotency_key)` unique — **중복 매매 차단**
  - `(user_id, created_at DESC)` — 거래 이력 조회
  - `(account_id, status)` — pending 주문 조회 (비동기 매매 [2.7])
  - `(stock_id, executed_at DESC)` — 종목별 거래량 조회
- `STOCK_DIARY`: `(user_id, diary_date DESC)`, `(order_id)`
- `DIARY_REVIEW`: `(diary_id)` unique (1:1)

#### 추천 도메인
- `STOCK_RECOMMENDATION`: `(user_id, recommended_at DESC)`, `(recommendation_type)` — 정율 트랙 1 후 재설계

#### 커뮤니티 도메인
- `SHARED_PORTFOLIO`: `(user_id)`, `(is_public, view_count DESC)` — 공개 인기 포트폴리오
- `SHARED_PORTFOLIO_ITEM`: `(portfolio_id)`
- `COMMUNITY_POST`: `(user_id, created_at DESC)`, `(post_type, created_at DESC)`, `(stock_id)` — 종목별 글
- `COMMENT`: `(post_id, created_at)`
- `POST_LIKE`: `(user_id, post_id)` unique — 중복 좋아요 차단

### 6.3 CHECK 제약 (DB 레벨 이중 안전망)

애플리케이션 트랜잭션 안에서도 검증하지만, **DB CHECK를 같이 두어 잘못된 데이터 직접 INSERT 차단**.

| 모델 | 제약 | 이유 |
|---|---|---|
| `ACCOUNT` | `balance >= 0` | 잔액 음수 방지 — 트랜잭션 + DB 이중 안전망 |
| `HOLDING` | `quantity >= 0` | 보유 음수 방지 |
| `ORDER` | `quantity > 0` | 0 또는 음수 주문 차단 |
| `ORDER` | `price > 0`, `total_amount > 0` | 비정상 주문 차단 |
| `ORDER` | `side IN ('BUY','SELL')` | 잘못된 side 값 차단 |
| `ORDER` | `status IN ('PENDING','FILLED','FAILED')` | 잘못된 상태 차단 |
| `STOCK_DIARY` | `confidence BETWEEN 1 AND 5` | 신뢰도 범위 |
| `STOCK_DIARY` | `action_type IN ('BUY','SELL','WATCH')` | enum 값 |
| `FINANCIAL_SUMMARY` | (제약 없음 — 적자/마이너스 가능) | |

### 6.4 외래키 ON DELETE 정책

| FK | 정책 | 이유 |
|---|---|---|
| `HOLDING.user_id → USER` | CASCADE | 회원 탈퇴 시 보유 데이터 같이 삭제 |
| `ACCOUNT.user_id → USER` | CASCADE | 동일 |
| `STOCK_DIARY.user_id → USER` | CASCADE | 일기는 본인 소유 |
| `ORDER.user_id → USER` | **SET NULL** | **거래 이력은 보존**, 익명화 처리 (탈퇴자 표시) |
| `ORDER.account_id → ACCOUNT` | RESTRICT | 거래 기록 있는 계좌는 삭제 차단 |
| `ORDER.stock_id → STOCK` | RESTRICT | 상장폐지된 종목 거래 기록도 보존 (STOCK은 `is_active=False`로만) |
| `STOCK_DIARY.order_id → ORDER` | SET NULL | 거래 없이도 일기(WATCH) 가능 |
| `HOLDING.stock_id → STOCK` | RESTRICT | 상장폐지 종목 보유 이력 보존 |
| `COMMUNITY_POST.user_id → USER` | CASCADE | 회원 탈퇴 시 글 삭제 (정책 선택, 필요 시 SET NULL) |
| `COMMENT.post_id → POST` | CASCADE | 글 삭제 시 댓글 같이 |
| `POST_LIKE.user_id → USER`, `post_id → POST` | CASCADE | 정리용 |

### 6.5 파티셔닝·확장 (P2 — 시간 되면)

- `STOCK_PRICE` 일봉이 수백만 행 누적되면 → `price_date` 월별 파티셔닝
- `ORDER` 거래량이 많아지면 → `created_at` 월별 파티셔닝
- **6주 학생 프로젝트엔 불필요**. 발표 자료의 "확장 가능성"에 언급만.

---

## 7. 시각적 ERD 갱신 안내

`planning/모델_서비스flow/erd.html`은 위 내용을 반영해 직접 수정 또는 dbdiagram.io / drawSQL / erdcloud.com 같은 도구로 새로 그리시면 됩니다. 이 텍스트 정의가 진실의 원천이고, 시각적 ERD는 그 표현입니다.

**추가/변경되는 박스 (시각화 시 참고)**:
- 🆕 ACCOUNT (거래 도메인, 핵심)
- 🆕 ORDER (거래 도메인, 핵심)
- 🔄 STOCK (필드 5개 추가)
- 🔄 STOCK_DIARY (order_id FK 추가, price/quantity 제거)
- 🔄 FINANCIAL_STATEMENT → FINANCIAL_SUMMARY (이름 변경 + 가공 필드 추가)
- 🟡 STOCK_RECOMMENDATION (보류 표시)

---

## 8. 다음 단계

1. 이 ERD 문서로 회의 합의 (5/18)
2. **모델 owner 매트릭스** (KICKOFF §3.7)에 ACCOUNT/ORDER 추가 — 강재민
3. Phase 2 첫 작업 (SCRUM-23 Django 세팅) 후 첫 마이그레이션으로 USER/ACCOUNT/STOCK 모델 생성 — §6.2 인덱스 / §6.3 CHECK / §6.4 ON DELETE 정책을 마이그레이션에 그대로 반영
4. 시각적 ERD 갱신 (planning/erd.html) — Phase 1 마무리 시점에 한 번 더 검토
