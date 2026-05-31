# DB 최적화 명세서 — 추천/장투 알고리즘 운영 관점 (DB_OPTIMIZATION_SPEC)
- 작성일: 2026-06-01
- 대상 독자: 백엔드 팀원 (DBeaver + PostgreSQL 환경)
- 관련 문서: [`ERD.md`](./ERD.md) · [`DART_COLUMN.md`](./DART_COLUMN.md) · [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md) (신규 테이블/컬럼 **DDL 원본**) · [`NEWS_RSS_API_SPEC.md`](./NEWS_RSS_API_SPEC.md) · [`NEWS_API_SPEC.md`](./NEWS_API_SPEC.md) · [`RUNBOOK_DBeaver.md`](./RUNBOOK_DBeaver.md)
- 마지막 수정: 2026-06-01

> 목적: Phase 1에서 파악한 **현 DB 구조 + 추천(궁합)/장투 알고리즘**을 기준으로, ① 현재 스키마로 **불가능·비효율한 쿼리 패턴을 심각도와 함께 진단**하고 ② 알고리즘 구동에 필요한 테이블/컬럼을 **체크리스트로 점검**하며 ③ **공통 성능 최적화(인덱스·VACUUM·파티셔닝·풀링·진단)** 와 ④ **DBeaver 실행용 마이그레이션 런북**을 제공한다.

---

## 0. 기존 문서와의 관계 (중복 방지)

[`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md)가 **신규 테이블·컬럼 설계의 DDL 원본**(갭 G1~G9, `stock_dna`/`recommendation_cache`/`user_behavior_log`/`long_term_score` 등)을 이미 보유한다. 본 문서는 그것을 대체하지 않고 **운영·성능 관점의 보완**이다.

| 구분 | ALGORITHM_DB_OPTIMIZATION_SPEC.md | **DB_OPTIMIZATION_SPEC.md (본 문서)** |
|---|---|---|
| 초점 | 알고리즘 구동에 필요한 **신규 테이블/컬럼 도출 + DDL** | **쿼리 패턴 진단(심각도) + 운영 최적화(VACUUM/풀링/진단) + 런북** |
| 신규 DDL | ✅ 원본 | 핵심만 재게시 + **원본 교차 참조** |
| 본 문서 고유 | — | §A 심각도 진단 · §D VACUUM/ANALYZE·pgBouncer·pg_stat · §E 번호 런북 |

> 신규 테이블/컬럼의 **전체 DDL은 ALGORITHM_DB_OPTIMIZATION_SPEC.md를 정본**으로 본다. 두 문서가 가리키는 테이블명·컬럼은 동일하다.
> ⚠️ **가정 (PK·테이블명)**: ERD 전체가 `BIGSERIAL int PK`/`snake_case`. Django 마이그레이션 시 테이블명은 `<app>_<model>`(예: `stocks_stock`)로 생성될 수 있어, FK 대상 테이블명은 실제 마이그레이션 시점에 맞춘다.

---

## 섹션 A. 현황 분석

### A-1. Phase 1에서 파악한 기존 테이블 구조 (그대로 명시)

실제 Django 모델 5개 앱 기준(마이그레이션 반영본).

| 도메인 | 테이블 | 주요 컬럼 |
|---|---|---|
| 사용자 | `user` | id, username, password, email, nickname, birth_year |
| 사용자 | `investment_profile` (1:1) | risk_type(CONSERVATIVE/MODERATE/AGGRESSIVE), investment_style, **preferred_period(개월)**, **preferred_sector(단일 문자열)**, updated_at |
| 종목 | `stock` | code, name, market, sector, industry, market_cap, listed_at, currency, kis_short_code, is_active, is_sp500, is_nasdaq100, description, homepage_url, ceo_name, employee_count |
| 종목 | `stock_price` (일봉) | stock_id, price_date, open/high/low/close, volume · `(stock,price_date)` unique |
| 종목 | `stock_indicator` | per, pbr, eps, roe, roa, dividend_yield, **beta, volatility, high_52w, low_52w**, calculated_date |
| 종목 | `financial_summary` | revenue, operating/net_profit, operating_margin, net_margin, **revenue_yoy, operating_profit_yoy, net_profit_yoy**, debt_ratio, equity_ratio, current_ratio, payout_ratio, fiscal_period |
| 종목 | `stock_news`, `news_related_stock` (실제명 `stocks_stocknews`/`stocks_newsrelatedstock`) | **이미 존재(최소 컬럼)**. 뉴스 파이프라인용 컬럼은 [`NEWS_RSS_API_SPEC.md`](./NEWS_RSS_API_SPEC.md) §3-2에서 **ALTER로 보강** |
| 거래 | `account`, `holding`, `order` | 가상 잔액 / 보유(quantity, average_price, first_acquired_at) / 매매기록(side, price, executed_at) |
| 일기 | `stock_diary`, `diary_review` | action_type(BUY/SELL/**WATCH**), reason, confidence, target/stop_loss, review |
| 추천 | `stock_recommendation` | ⏸️ **미생성(보류)** — "추천 트랙 1 완료 후 필드 확정" |
| 커뮤니티 | `shared_portfolio(_item)`, `community_post`, `comment`, `post_like` | — |

### A-2. 추천 알고리즘 구현 시 불가능·비효율한 쿼리 패턴 (심각도 표기)

> 심각도: **상** = 알고리즘 핵심 기능이 현재 스키마로 **불가능**하거나 매 추천마다 전종목 스캔 / **중** = 가능하나 비효율(반복 정규화·인덱스 부재) / **하** = 동작하나 운영상 개선 권장.

| # | 쿼리 패턴 / 요구 | 현재 문제 | 영향 알고리즘 | 심각도 |
|---|---|---|---|---|
| A1 | 유저 5차원 성향 벡터(`risk_tolerance` 등)로 궁합 계산 | `investment_profile`에 벡터 컬럼 **부재**(risk_type 3분류만) → 계산 입력 자체가 없음 | 온보딩 궁합 전체 | **상** |
| A2 | 복수 관심 섹터 매칭 (테마 궁합 20%) | `preferred_sector`가 **단일 문자열** → 2개 이상 선호/가중치 불가, `WHERE sector IN (...)` 불가 | 테마 궁합 | **상** |
| A3 | 종목별 Stock DNA(value/growth/stability 0~1) 조회 | 정규화 결과 **미저장** → 매 추천마다 전종목 `MIN/MAX` 재정규화(전체 스캔 반복) | 궁합 5요소 | **상** |
| A4 | 유저별 추천 결과/순위/근거 조회 | 추천 캐시 테이블 **부재** → 매 요청 전종목 재계산, 설명(reason) 보존 불가 | 추천 노출/재계산 | **상** |
| A5 | Like 종목 월 재검증의 "PBR Like대비 ±30%" | **Like 시점 PBR 스냅샷 부재** → 기준값이 없어 재검증 신호(🟢/🟡/🔴) 산출 불가 | 장투 재검증 | **상** |
| A6 | 사용자 행동(클릭/조회/스와이프) 기반 선호 학습 | 행동 이벤트 로그 **부재**(`stock_diary`는 회고용) → 행동 학습 불가 | 행동 학습 장투 | **상** |
| A7 | "이 종목의 최근 N일 뉴스 센티멘트" 집계 | `stock_news.sentiment_score`/매핑이 미확정·미적재 → 센티멘트 보정 불가 | 궁합 보정·장투 추세 | 중 |
| A8 | 종목별 최신 지표 1건 조회 (`stock_indicator`) | `(stock_id, calculated_date)` unique는 있으나 **"최신 1건"** 은 `MAX(calculated_date)` 서브쿼리 반복 → 종목수만큼 비효율 | 모든 지표 조회 | 중 |
| A9 | 종목별 최신 재무 1건 (`financial_summary`) | 동일 — `fiscal_period` 문자열 정렬("2025Q3")로 `MAX` 시 정렬 정확성·인덱스 활용 모두 약함 | 장투 재검증/성장 | 중 |
| A10 | 섹터 평균 ROE/PBR 비교("반도체 평균 대비") | 매 카드 노출마다 `GROUP BY sector` 집계 → MV 부재로 반복 비용 | 장투 업종 비교 | 중 |
| A11 | 보유일수 기반 마일스톤(30/90/180/365) | `holding.first_acquired_at`로 계산 가능하나 **도달 스냅샷 미저장** → 시점 지표 보존 불가 | 장투 넛지 | 하 |
| A12 | EPS 증가율 (재검증 4지표 중 하나) | `eps`(절대값)만 존재, **증가율 컬럼 없음** → `net_profit_yoy` 프록시 필요 | 장투 재검증 | 하 |

> A1~A6(심각도 **상**)은 **섹션 B/C의 신규 테이블·컬럼이 들어와야 비로소 가능**해지는 항목이다. A7~A12는 인덱스/MV/프록시로 완화 가능.

---

## 섹션 B. 온보딩 기반 초기 추천 알고리즘 최적화

### B-1. 알고리즘 로직 요약 (Phase 1 기반)

```
온보딩 8문항 → 5차원 벡터(risk_tolerance/investment_term/experience/loss_aversion/behavior + 관심섹터[])
→ 종목 Stock DNA(volatility=beta, value=norm(1/pbr), growth=norm(eps), stability=norm(1/beta))
→ 궁합점수 = (risk×0.35 + term×0.20 + exp×0.15 + sector×0.20 + style×0.10) × 100
```

### B-2. 구동에 필요한 테이블/컬럼 체크리스트

| 필요 항목 | 현재 보유? | 조치 | DDL 위치 |
|---|---|---|---|
| 유저 5차원 벡터 (`risk_tolerance`…`behavior`) | ❌ | `investment_profile` 컬럼 추가 | B-3 (A) |
| 투자금액/목표수익률/리스크허용 | ❌ | 동 ALTER | B-3 (A) |
| 온보딩 8문항 원답 보존 | ❌ | `onboarding_answers JSONB` | B-3 (A) |
| 복수 관심 섹터 + 가중치 | ❌ (단일 문자열만) | 신규 `user_preferred_sector` | B-3 (B) |
| Stock DNA 정규화 캐시 | ❌ (원천 지표만 존재) | 신규 `stock_dna` | B-3 (C) |
| 추천 결과/순위/근거 캐시 + TTL | ❌ (`stock_recommendation` 보류) | 신규 `recommendation_cache` | B-3 (D) |
| 원천 지표 (beta/pbr/eps/sector) | ✅ `stock_indicator`/`stock` | 그대로 입력 | — |

> 신규 테이블/컬럼의 **전체 DDL·CHECK·가정**은 [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md) §2가 정본. 아래는 본 문서 자족성을 위한 핵심 발췌.

### B-3. 누락 테이블/컬럼 DDL (PostgreSQL)

**(A) `investment_profile` 컬럼 보강 — ALTER (기존 행 보존 위해 DEFAULT 명시)**
```sql
ALTER TABLE investment_profile
    ADD COLUMN IF NOT EXISTS risk_tolerance     SMALLINT NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS investment_term    SMALLINT NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS experience         SMALLINT NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS loss_aversion      SMALLINT NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS behavior           SMALLINT NOT NULL DEFAULT 3,
    ADD COLUMN IF NOT EXISTS invest_amount_min  BIGINT,
    ADD COLUMN IF NOT EXISTS invest_amount_max  BIGINT,
    ADD COLUMN IF NOT EXISTS target_return_pct  DECIMAL(5,2),
    ADD COLUMN IF NOT EXISTS risk_band_pct      DECIMAL(5,2),
    ADD COLUMN IF NOT EXISTS onboarding_answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS profiled_at        TIMESTAMPTZ;

ALTER TABLE investment_profile
    ADD CONSTRAINT ck_ip_vector CHECK (
        risk_tolerance BETWEEN 1 AND 5 AND investment_term BETWEEN 1 AND 5 AND
        experience BETWEEN 1 AND 5 AND loss_aversion BETWEEN 1 AND 5 AND behavior BETWEEN 1 AND 5);
```

**(B) 복수 관심 섹터 — 신규**
```sql
CREATE TABLE IF NOT EXISTS user_preferred_sector (
    id         BIGSERIAL    PRIMARY KEY,
    user_id    BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    sector     VARCHAR(50)  NOT NULL,                  -- stock.sector 체계와 통일
    weight     DECIMAL(4,3) NOT NULL DEFAULT 1.0,      -- 1순위 1.0, 2순위 0.7…
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_sector UNIQUE (user_id, sector),
    CONSTRAINT ck_ups_weight  CHECK (weight BETWEEN 0 AND 1)
);
```

**(C) Stock DNA 정규화 캐시 — 신규 (일 1회 배치 적재, 추천은 이 테이블만 읽음)**
```sql
CREATE TABLE IF NOT EXISTS stock_dna (
    id              BIGSERIAL   PRIMARY KEY,
    stock_id        BIGINT      NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    volatility      DECIMAL(6,4),   -- = beta
    value_score     DECIMAL(5,4),   -- normalize(1/pbr) 0~1
    growth_score    DECIMAL(5,4),   -- normalize(eps)   0~1
    stability       DECIMAL(5,4),   -- normalize(1/beta) 0~1
    news_sentiment  DECIMAL(4,3),   -- 최근 7일 가중 센티멘트(-1~1)
    sector          VARCHAR(50),    -- 조인 절감용 비정규화 캐시
    calculated_date DATE        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_stock_dna UNIQUE (stock_id, calculated_date)
);
```

**(D) 추천 결과 캐시 + TTL + 근거 — 신규**
```sql
CREATE TABLE IF NOT EXISTS recommendation_cache (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    stock_id    BIGINT       NOT NULL REFERENCES stock(id)  ON DELETE CASCADE,
    rec_type    VARCHAR(20)  NOT NULL DEFAULT 'onboarding', -- 'onboarding'/'long_term'
    match_score DECIMAL(5,2) NOT NULL,
    rank        SMALLINT,
    reason      JSONB        NOT NULL DEFAULT '{}'::jsonb,   -- 요소별 기여+한줄설명
    expires_at  TIMESTAMPTZ  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reco UNIQUE (user_id, stock_id, rec_type),
    CONSTRAINT ck_reco_score CHECK (match_score BETWEEN 0 AND 100)
);
```

### B-4. 성능 인덱스 추가 DDL

```sql
CREATE INDEX IF NOT EXISTS idx_stock_dna_date   ON stock_dna (calculated_date);          -- 당일 DNA 일괄 로드
CREATE INDEX IF NOT EXISTS idx_stock_dna_sector ON stock_dna (sector);                   -- 테마 후보 필터
CREATE INDEX IF NOT EXISTS idx_reco_user_active ON recommendation_cache (user_id, expires_at); -- 유효 추천 조회
CREATE INDEX IF NOT EXISTS idx_reco_user_rank   ON recommendation_cache (user_id, rec_type, rank); -- 상위 N
CREATE INDEX IF NOT EXISTS idx_ups_user         ON user_preferred_sector (user_id);
-- A8 완화: 종목별 최신 지표 조회 가속(부분 인덱스 대안은 D-1 참조)
CREATE INDEX IF NOT EXISTS idx_indicator_stock_date ON stock_indicator (stock_id, calculated_date DESC);
```

### B-5. 핵심 추천 쿼리 (CTE/WITH절)

```sql
-- :user_id 의 궁합 점수 Top 10 (Stock DNA 캐시 + CASE 분기 + WINDOW 순위)
WITH prof AS (
    SELECT user_id, risk_tolerance, investment_term, experience
    FROM investment_profile WHERE user_id = :user_id
),
scored AS (
    SELECT
        s.id AS stock_id, s.name, s.sector,
        GREATEST(0, 1 - ABS(p.risk_tolerance / 2.5 - d.volatility)) AS risk_match,   -- 35%
        CASE WHEN p.investment_term >= 4 THEN (d.stability + d.value_score) / 2       -- 20%
             WHEN p.investment_term  = 3 THEN (d.stability + d.value_score + d.volatility) / 3
             ELSE d.volatility END AS term_match,
        CASE WHEN p.experience <= 2 THEN d.stability                                  -- 15%
             WHEN p.experience  = 3 THEN (d.stability + d.growth_score) / 2
             ELSE (d.growth_score + d.volatility) / 2 END AS exp_match,
        COALESCE(ups.weight, 0.5) AS sector_match,                                    -- 20%
        (d.value_score + d.growth_score) / 2 AS style_match                           -- 10%
    FROM prof p
    JOIN stock_dna d ON d.calculated_date = CURRENT_DATE
    JOIN stock s     ON s.id = d.stock_id AND s.is_active = TRUE
    LEFT JOIN user_preferred_sector ups ON ups.user_id = p.user_id AND ups.sector = s.sector
)
SELECT stock_id, name, sector,
       ROUND((risk_match*0.35 + term_match*0.20 + exp_match*0.15
            + sector_match*0.20 + style_match*0.10) * 100, 2) AS match_score,
       RANK() OVER (ORDER BY (risk_match*0.35 + term_match*0.20 + exp_match*0.15
            + sector_match*0.20 + style_match*0.10) DESC) AS rank
FROM scored
ORDER BY match_score DESC
LIMIT 10;
```
> 이 결과를 `recommendation_cache`에 upsert(`expires_at = NOW() + INTERVAL '1 day'`)하면 A4 해소. 순수 Python 알고리즘 함수(정율 담당)의 **검증·배치 사전계산용 참조 구현**이다.

---

## 섹션 C. 장투(장기투자) 추천 알고리즘 최적화

### C-1. 알고리즘 로직 요약 (Phase 1 기반)

월 1회 재검증(ROE≥10%, 부채비율≤200%, EPS증가율>0, PBR Like대비±30% → 🟢/🟡/🔴) + 하락 심리지원(-5%/-15%, 보유 30/90일) + 업종 평균 비교 + 보유 마일스톤 + **행동 학습**(평균 보유기간·손절·추매·수익실현).

### C-2. 사용자 행동 로그 테이블 (조회/관심/보유) + 파티셔닝

```sql
-- 행동 이벤트 원본(append-only). 날짜 RANGE 파티셔닝
CREATE TABLE IF NOT EXISTS user_behavior_log (
    id          BIGSERIAL   NOT NULL,
    user_id     BIGINT      NOT NULL,
    stock_id    BIGINT,                                       -- 종목 무관 이벤트는 NULL
    event_type  VARCHAR(30) NOT NULL,                         -- VIEW/CLICK/SWIPE_LIKE/SWIPE_PASS/WATCH/SEARCH
    event_value JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at),                             -- 파티션 키 포함 필수
    CONSTRAINT ck_ubl_event CHECK (event_type IN
        ('VIEW','CLICK','SWIPE_LIKE','SWIPE_PASS','WATCH','SEARCH'))
) PARTITION BY RANGE (created_at);

CREATE TABLE IF NOT EXISTS user_behavior_log_2026_06 PARTITION OF user_behavior_log
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
CREATE TABLE IF NOT EXISTS user_behavior_log_2026_07 PARTITION OF user_behavior_log
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

CREATE INDEX IF NOT EXISTS idx_ubl_user_time ON user_behavior_log (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ubl_stock     ON user_behavior_log (stock_id);
```

**시계열 저장 최적화 / 파티셔닝 전략**
- **RANGE(created_at) 월별 파티션** — 행동 로그는 append-heavy + 시간범위 조회(최근 90일)가 대부분. 월 파티션이면 오래된 달은 스캔에서 제외(파티션 프루닝).
- 파티션 사전 생성: 운영은 `pg_partman` 또는 월초 배치. 6주 프로젝트는 **1~2개월분만 미리** 만들어도 충분.
- FK는 파티션 특성상 제약 → `user_id/stock_id` 정합은 **앱 레벨 보장**(ERD §6.5 P2 전략과 정합).
- 동일 전략을 `stock_price`(일봉, 대량)·`order`(거래 누적)에도 확장 가능 → §D-3.

### C-3. 투자 성향 점수화 컬럼 설계 (행동 집계 + Like 스냅샷)

```sql
-- 행동 집계(유저 1행, 일 1회 배치). 설문 성향을 행동으로 보정
CREATE TABLE IF NOT EXISTS user_investment_pattern (
    id                   BIGSERIAL    PRIMARY KEY,
    user_id              BIGINT       NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    avg_holding_days     DECIMAL(8,2),                    -- 평균 보유 기간
    stop_loss_ratio      DECIMAL(5,4),                    -- 손절 비율
    add_buy_ratio        DECIMAL(5,4),                    -- 추매 패턴
    profit_realize_ratio DECIMAL(5,4),                    -- 수익 실현 패턴
    sector_pref_scores   JSONB NOT NULL DEFAULT '{}'::jsonb, -- {"반도체":0.42,…}
    behavior_inferred    SMALLINT,                        -- 행동기반 재추정 behavior(1~5)
    last_aggregated_at   TIMESTAMPTZ,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Like(=매수 간주) 시점 스냅샷 — 재검증 "PBR ±30%" 기준점(A5 해소)
CREATE TABLE IF NOT EXISTS user_liked_stock (
    id                 BIGSERIAL    PRIMARY KEY,
    user_id            BIGINT       NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    stock_id           BIGINT       NOT NULL REFERENCES stock(id)  ON DELETE CASCADE,
    liked_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    base_pbr           DECIMAL(8,3),                       -- Like 시점 PBR
    base_match_score   DECIMAL(5,2),
    last_review_status VARCHAR(10),                        -- GREEN/YELLOW/RED
    last_reviewed_at   TIMESTAMPTZ,
    is_active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_liked UNIQUE (user_id, stock_id),
    CONSTRAINT ck_review_status CHECK (last_review_status IS NULL OR last_review_status IN ('GREEN','YELLOW','RED'))
);

-- 종목별 장투 종합 점수(5요소) + 이력
CREATE TABLE IF NOT EXISTS long_term_score (
    id                   BIGSERIAL    PRIMARY KEY,
    stock_id             BIGINT       NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    financial_score      DECIMAL(5,2),
    growth_score         DECIMAL(5,2),
    news_sentiment_score DECIMAL(5,2),
    technical_score      DECIMAL(5,2),
    user_fit_score       DECIMAL(5,2),
    total_score          DECIMAL(5,2) NOT NULL,
    calculated_date      DATE         NOT NULL,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_lts UNIQUE (stock_id, calculated_date),
    CONSTRAINT ck_lts_total CHECK (total_score BETWEEN 0 AND 100)
);
CREATE INDEX IF NOT EXISTS idx_lts_total       ON long_term_score (calculated_date, total_score DESC);
CREATE INDEX IF NOT EXISTS idx_uls_user_active ON user_liked_stock (user_id, is_active);
```
> `holding_milestone`(30/90/180/365 스냅샷)·`long_term_score_history`(추세) 전체 DDL은 [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md) §3-3·§3-4 참조.

### C-4. 장투 추천 쿼리 (윈도우 함수)

**① Like 종목 월 재검증 — 4지표 위반 카운트 → 신호**
```sql
WITH latest_ind AS (   -- A8/A9 완화: 종목별 최신 지표/재무 1건만
    SELECT DISTINCT ON (stock_id) stock_id, roe, pbr
    FROM stock_indicator ORDER BY stock_id, calculated_date DESC
),
latest_fin AS (
    SELECT DISTINCT ON (stock_id) stock_id, debt_ratio, net_profit_yoy
    FROM financial_summary ORDER BY stock_id, fiscal_period DESC
)
SELECT uls.stock_id, s.name,
    ( (li.roe < 10)::int
    + (lf.debt_ratio > 200)::int
    + (lf.net_profit_yoy <= 0)::int                                   -- EPS증가율 프록시(A12)
    + (ABS(li.pbr - uls.base_pbr)/NULLIF(uls.base_pbr,0) > 0.30)::int ) AS broken_cnt,
    CASE WHEN ( (li.roe<10)::int + (lf.debt_ratio>200)::int + (lf.net_profit_yoy<=0)::int
              + (ABS(li.pbr-uls.base_pbr)/NULLIF(uls.base_pbr,0)>0.30)::int ) >= 3 THEN 'RED'
         WHEN ( (li.roe<10)::int + (lf.debt_ratio>200)::int + (lf.net_profit_yoy<=0)::int
              + (ABS(li.pbr-uls.base_pbr)/NULLIF(uls.base_pbr,0)>0.30)::int ) >= 1 THEN 'YELLOW'
         ELSE 'GREEN' END AS review_status
FROM user_liked_stock uls
JOIN stock s        ON s.id = uls.stock_id
JOIN latest_ind li  ON li.stock_id = uls.stock_id
JOIN latest_fin lf  ON lf.stock_id = uls.stock_id
WHERE uls.user_id = :user_id AND uls.is_active = TRUE;
```

**② 장투 점수 30일 추세 (LAG + 이동평균 WINDOW)**
```sql
SELECT stock_id, recorded_date, total_score,
       total_score - LAG(total_score) OVER (PARTITION BY stock_id ORDER BY recorded_date) AS daily_delta,
       AVG(total_score) OVER (PARTITION BY stock_id ORDER BY recorded_date
                              ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma7_score
FROM long_term_score_history
WHERE stock_id = :stock_id AND recorded_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY recorded_date;
```

**③ 행동 기반 선호 섹터 (이벤트 가중 집계)**
```sql
SELECT s.sector,
       COUNT(*) FILTER (WHERE b.event_type='SWIPE_LIKE') * 1.0
     + COUNT(*) FILTER (WHERE b.event_type='VIEW')       * 0.3 AS sector_affinity
FROM user_behavior_log b JOIN stock s ON s.id = b.stock_id
WHERE b.user_id = :user_id AND b.created_at >= NOW() - INTERVAL '90 days' AND b.stock_id IS NOT NULL
GROUP BY s.sector ORDER BY sector_affinity DESC;
```

---

## 섹션 D. 공통 최적화 사항

### D-1. 자주 JOIN되는 조합 인덱스 전략

| JOIN 조합 (빈번 경로) | 권장 인덱스 | 비고 |
|---|---|---|
| `stock ⋈ stock_dna (당일)` | `stock_dna(calculated_date)` + `(stock_id, calculated_date)` unique | 추천 메인 경로 |
| `stock ⋈ stock_indicator (최신)` | `stock_indicator(stock_id, calculated_date DESC)` | `DISTINCT ON`/`MAX` 가속(A8) |
| `stock ⋈ financial_summary (최신)` | `financial_summary(stock_id, fiscal_period DESC)` | A9 완화 |
| `recommendation_cache ⋈ user (유효)` | `(user_id, expires_at)`, `(user_id, rec_type, rank)` | TTL 필터+정렬 |
| `user_liked_stock ⋈ user (활성)` | `(user_id, is_active)` | 재검증 대상 |
| `news_related_stock ⋈ stock` | `(stock_id)`, `(ticker_code)` | 종목 뉴스 |
| `holding ⋈ user ⋈ stock` | 기존 `(user_id, stock_id)` unique 활용 | 추가 불필요 |

```sql
-- "최신 1건" 패턴을 부분/복합 인덱스로 가속 (A8/A9)
CREATE INDEX IF NOT EXISTS idx_indicator_stock_date ON stock_indicator (stock_id, calculated_date DESC);
CREATE INDEX IF NOT EXISTS idx_fin_stock_period     ON financial_summary (stock_id, fiscal_period DESC);
```
> **인덱스 과다 주의**: 쓰기(배치 적재)가 잦은 `stock_price`/`stock_indicator`는 인덱스가 많을수록 INSERT 비용↑. 위 목록은 **읽기 경로가 검증된 것만** 추렸다.

### D-2. VACUUM / ANALYZE 권장 주기

| 대상 | 작업 | 권장 주기 | 이유 |
|---|---|---|---|
| `recommendation_cache` | `VACUUM (ANALYZE)` | **일 1회**(만료 DELETE 직후) | TTL 삭제로 dead tuple 다수 → 부풀음 방지 |
| `user_behavior_log` 활성 파티션 | `ANALYZE` | **일 1회** | append 폭증 → 통계 갱신해야 플래너 정확 |
| `stock_dna`, `long_term_score` | `ANALYZE` | **일 1회**(배치 적재 후) | 일배치 전량 갱신 → 통계 즉시 최신화 |
| `stock_price`(일봉 대량 적재) | `VACUUM (ANALYZE)` | **적재 배치 후** | 대량 INSERT 후 통계/가시성 맵 갱신 |
| 전체 DB | autovacuum 유지 | 상시 | 기본 autovacuum ON. 아래 임계만 조정 |

```sql
-- 갱신이 잦은 테이블은 autovacuum을 더 공격적으로 (기본 0.2 → 0.05)
ALTER TABLE recommendation_cache SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.02);
ALTER TABLE user_behavior_log    SET (autovacuum_vacuum_scale_factor = 0.05);

-- 수동 점검(배치 직후 권장)
VACUUM (ANALYZE) recommendation_cache;
ANALYZE stock_dna;
```
> ⚠️ 6주 프로젝트 규모에선 **기본 autovacuum으로 충분**. 위 튜닝은 발표 "확장 가능성" 근거 + 대량 적재 후 수동 `ANALYZE` 정도만 실무 적용 권장.

### D-3. 파티셔닝 대상 (날짜 기반)

| 테이블 | 키 | 전략 | 우선순위 |
|---|---|---|---|
| `user_behavior_log` | `created_at` | 월별 RANGE (C-2 구현) | **지금 적용** |
| `long_term_score_history` | `recorded_date` | 월별 RANGE | 데이터 누적 시 |
| `stock_price` | `price_date` | 월별 RANGE (수백만 행 누적 시) | P2 (ERD §6.5) |
| `order` | `created_at` | 월별 RANGE (거래 급증 시) | P2 |
> 학생 프로젝트 데이터량에선 `stock_price`/`order` 파티셔닝은 **불필요** — 발표 자료에 언급만(ERD §6.5와 동일 톤).

### D-4. Connection pooling (pgBouncer 권장 설정)

도입 시점: **배치(점수/DNA 갱신)와 실시간 추천 조회가 동시에 커넥션을 점유**해 `max_connections` 압박이 보일 때. 6주 규모는 보통 불필요(언급용).

```ini
[databases]
jumanchu = host=127.0.0.1 port=5432 dbname=jumanchu

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
; 웹앱(짧은 트랜잭션) → transaction 모드가 커넥션 효율 최적
pool_mode = transaction
max_client_conn = 200      ; 앱이 여는 최대 클라이언트 커넥션
default_pool_size = 20      ; 실제 PG로 가는 풀 크기(= Django CONN 합과 균형)
reserve_pool_size = 5
server_idle_timeout = 60
```
> `pool_mode = transaction` 사용 시 Django는 **세션 레벨 기능(prepared statement, advisory lock 등)** 주의. Django `CONN_MAX_AGE`와 풀 크기를 함께 조율.

### D-5. DBeaver 성능 점검 쿼리

```sql
-- ① 테이블별 dead tuple / 마지막 (auto)vacuum·analyze 시각
SELECT relname, n_live_tup, n_dead_tup,
       round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
       last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- ② Seq Scan이 많은(인덱스가 아쉬운) 테이블 — 인덱스 후보 발굴
SELECT relname, seq_scan, idx_scan,
       seq_tup_read, idx_tup_fetch
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_scan DESC;

-- ③ 사용되지 않는 인덱스(쓰기 비용만 발생) — 제거 후보
SELECT s.relname AS table, s.indexrelname AS index, s.idx_scan,
       pg_size_pretty(pg_relation_size(s.indexrelid)) AS size
FROM pg_stat_user_indexes s
WHERE s.idx_scan = 0
ORDER BY pg_relation_size(s.indexrelid) DESC;

-- ④ 테이블/인덱스 용량 Top 20 (파티셔닝/아카이빙 판단)
SELECT relname,
       pg_size_pretty(pg_total_relation_size(relid)) AS total,
       pg_size_pretty(pg_relation_size(relid))       AS table_only
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;

-- ⑤ 느린 쿼리 추적 (확장 설치 시): CREATE EXTENSION pg_stat_statements;
SELECT round(total_exec_time::numeric, 1) AS total_ms, calls,
       round(mean_exec_time::numeric, 2) AS mean_ms, query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- ⑥ 특정 추천 쿼리 실행계획 점검
EXPLAIN (ANALYZE, BUFFERS) /* 섹션 B-5 추천 쿼리 붙여넣기 */ SELECT 1;
```

---

## 섹션 E. 마이그레이션 실행 순서

> DBeaver에서 **번호 순서대로** 실행. FK 의존(부모→자식)을 지키며, 모든 스크립트는 멱등(`IF NOT EXISTS`/`IF EXISTS`)이라 재실행 안전.
> ⚠️ 팀이 Django ORM을 쓰면 아래 SQL은 **참조용 청사진**이고, 실제로는 모델/`Meta`에 1:1 반영 후 `makemigrations`/`migrate`로 적용(ERD §0 "마이그레이션 한 사람만" 규칙).

### E-1. 실행 순서 (번호 스크립트)

| # | 스크립트 | 작업 | 의존 | 다운타임 주의 |
|---|---|---|---|---|
| 1 | `01_alter_investment_profile.sql` | B-3(A) 벡터/금액/목표 컬럼 + CHECK | `investment_profile` | 기존 행에 DEFAULT 적용(짧은 락) |
| 2 | `02_create_user_preferred_sector.sql` | B-3(B) | `user` | — |
| 3 | `03_create_stock_dna.sql` | B-3(C) + B-4 인덱스 | `stock` | — |
| 4 | `04_create_recommendation_cache.sql` | B-3(D) + B-4 인덱스 | `user`,`stock` | — |
| 5 | `05_create_user_behavior_log.sql` | C-2 파티션 + 인덱스 + 파티션 1~2개 | `user`,`stock` | — |
| 6 | `06_create_pattern_milestone.sql` | C-3 패턴 + 마일스톤 | `user`,`stock` | — |
| 7 | `07_create_long_term_score.sql` | C-3 장투 점수/이력/Like 스냅샷 + 인덱스 | `user`,`stock` | — |
| 8 | `08_alter_news_tables.sql` | NEWS_RSS_API_SPEC §3-2 — 기존 `stocks_stocknews`/`stocks_newsrelatedstock`에 **컬럼 ALTER 추가**(create 아님) + 인덱스 | 두 뉴스 테이블 이미 존재 | — |
| 9 | `09_common_indexes_mv.sql` | D-1 최신지표 인덱스 + D-2 autovacuum + MV(`mv_sector_avg`) | 위 전부 | MV 최초 생성 비용 |

**실행 전 주의**
1. **개발/스테이징에서 먼저** 1→9 순서로 검증 후 운영 적용.
2. 1번(ALTER)은 운영 데이터가 있으면 `NOT NULL DEFAULT`가 테이블 재작성 락을 유발할 수 있음 → 데이터 적은 현 시점에 먼저 적용 권장.
3. 5번 파티션 테이블은 **월초마다 다음 달 파티션 사전 생성** 배치를 함께 등록(누락 시 INSERT 실패).
4. 각 스크립트 실행 후 `\d <table>` 또는 D-5 ①④로 결과 확인.

### E-2. 롤백 (역순, 개발 환경 한정 — 데이터 손실 주의)

```sql
-- 09 → 01 역순
DROP MATERIALIZED VIEW IF EXISTS mv_sector_avg;                                            -- 09
-- 08: 뉴스 테이블은 기존 모델이므로 DROP 금지 → 추가한 컬럼만 제거
ALTER TABLE stocks_newsrelatedstock
    DROP CONSTRAINT IF EXISTS ck_news_relevance,
    DROP COLUMN IF EXISTS ticker_code, DROP COLUMN IF EXISTS relevance_score, DROP COLUMN IF EXISTS created_at;
ALTER TABLE stocks_stocknews
    DROP CONSTRAINT IF EXISTS ck_stock_news_sentiment,
    DROP COLUMN IF EXISTS summary, DROP COLUMN IF EXISTS sentiment_score, DROP COLUMN IF EXISTS category,
    DROP COLUMN IF EXISTS lang, DROP COLUMN IF EXISTS created_at, DROP COLUMN IF EXISTS updated_at;
DROP TABLE IF EXISTS long_term_score_history, long_term_score, user_liked_stock CASCADE;   -- 07
DROP TABLE IF EXISTS holding_milestone, user_investment_pattern CASCADE;                    -- 06
DROP TABLE IF EXISTS user_behavior_log CASCADE;   -- 05 (자식 파티션 함께 삭제)
DROP TABLE IF EXISTS recommendation_cache CASCADE;                                          -- 04
DROP TABLE IF EXISTS stock_dna CASCADE;                                                     -- 03
DROP TABLE IF EXISTS user_preferred_sector CASCADE;                                         -- 02
ALTER TABLE investment_profile                                                              -- 01
    DROP CONSTRAINT IF EXISTS ck_ip_vector,
    DROP COLUMN IF EXISTS risk_tolerance,  DROP COLUMN IF EXISTS investment_term,
    DROP COLUMN IF EXISTS experience,      DROP COLUMN IF EXISTS loss_aversion,
    DROP COLUMN IF EXISTS behavior,        DROP COLUMN IF EXISTS invest_amount_min,
    DROP COLUMN IF EXISTS invest_amount_max, DROP COLUMN IF EXISTS target_return_pct,
    DROP COLUMN IF EXISTS risk_band_pct,   DROP COLUMN IF EXISTS onboarding_answers,
    DROP COLUMN IF EXISTS profiled_at;
```
> **트랜잭션 권장**: 각 스크립트를 `BEGIN; … COMMIT;`로 감싸 부분 실패 시 `ROLLBACK`. (단, `CREATE INDEX CONCURRENTLY`/MV `REFRESH … CONCURRENTLY`는 트랜잭션 밖에서 실행.)
> **Django 롤백**은 SQL `DROP`이 아니라 `python manage.py migrate <app> <직전_migration>`을 사용.

---

## ✅ 산출물 자체 체크
- [x] A. 기존 테이블 명시 + 불가능/비효율 쿼리 12종 **심각도(상/중/하)** 진단
- [x] B. 온보딩 — **체크리스트** + 누락 ALTER/CREATE DDL + 인덱스 + **CTE 추천 쿼리**
- [x] C. 장투 — 행동 로그 + **파티셔닝** + 성향 점수화 컬럼 + **윈도우 함수 쿼리**
- [x] D. 공통 — JOIN 인덱스 전략 + **VACUUM/ANALYZE 주기** + 파티셔닝 대상 + **pgBouncer 설정** + **pg_stat_user_tables 진단**
- [x] E. **번호 스크립트** 실행 순서 + 주의 + 롤백
- [x] 모든 DDL PostgreSQL 문법 · `BIGSERIAL` PK · `created_at/updated_at` · DEFAULT 명시 · 코드펜스
- [x] 기존 `ALGORITHM_DB_OPTIMIZATION_SPEC.md`와 중복 DDL은 교차 참조 · 가정 `⚠️` 명시
