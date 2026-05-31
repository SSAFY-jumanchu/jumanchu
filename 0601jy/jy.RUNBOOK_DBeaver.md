# RUNBOOK_DBeaver
- 작성일: 2026-06-01
- 대상 독자: 백엔드 팀원 (DBeaver + PostgreSQL 환경)
- 관련 문서: [`DB_OPTIMIZATION_SPEC.md`](./DB_OPTIMIZATION_SPEC.md) · [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md) · [`NEWS_RSS_API_SPEC.md`](./NEWS_RSS_API_SPEC.md)
- 마지막 수정: 2026-06-01

```sql
-- 전제: Django 기본 db_table 명명(<app>_<model>) 기준. Meta.db_table 커스텀 시 테이블명만 조정.
-- 전제: 01~09 순서대로 실행. 각 블록은 멱등(IF [NOT] EXISTS). ORM 사용 시에는 모델 반영 후 makemigrations/migrate 권장.
```

```sql
-- 01. accounts_investmentprofile : 5차원 성향 벡터 + 투자금액/목표/리스크 + 온보딩 원답
ALTER TABLE accounts_investmentprofile
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

ALTER TABLE accounts_investmentprofile
    ADD CONSTRAINT ck_ip_vector CHECK (
        risk_tolerance BETWEEN 1 AND 5 AND investment_term BETWEEN 1 AND 5 AND
        experience BETWEEN 1 AND 5 AND loss_aversion BETWEEN 1 AND 5 AND behavior BETWEEN 1 AND 5);
```

```sql
-- 02. user_preferred_sector : 복수 관심 섹터 + 가중치
CREATE TABLE IF NOT EXISTS user_preferred_sector (
    id         BIGSERIAL    PRIMARY KEY,
    user_id    BIGINT       NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    sector     VARCHAR(50)  NOT NULL,
    weight     DECIMAL(4,3) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_sector UNIQUE (user_id, sector),
    CONSTRAINT ck_ups_weight  CHECK (weight BETWEEN 0 AND 1)
);
CREATE INDEX IF NOT EXISTS idx_ups_user ON user_preferred_sector (user_id);
```

```sql
-- 03. stock_dna : Stock DNA 정규화 캐시(일 1회 배치 적재)
CREATE TABLE IF NOT EXISTS stock_dna (
    id              BIGSERIAL   PRIMARY KEY,
    stock_id        BIGINT      NOT NULL REFERENCES stocks_stock(id) ON DELETE CASCADE,
    volatility      DECIMAL(6,4),
    value_score     DECIMAL(5,4),
    growth_score    DECIMAL(5,4),
    stability       DECIMAL(5,4),
    news_sentiment  DECIMAL(4,3),
    sector          VARCHAR(50),
    calculated_date DATE        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_stock_dna UNIQUE (stock_id, calculated_date)
);
CREATE INDEX IF NOT EXISTS idx_stock_dna_date   ON stock_dna (calculated_date);
CREATE INDEX IF NOT EXISTS idx_stock_dna_sector ON stock_dna (sector);
```

```sql
-- 04. recommendation_cache : 추천 결과 + TTL + 근거 JSON
CREATE TABLE IF NOT EXISTS recommendation_cache (
    id          BIGSERIAL    PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    stock_id    BIGINT       NOT NULL REFERENCES stocks_stock(id)  ON DELETE CASCADE,
    rec_type    VARCHAR(20)  NOT NULL DEFAULT 'onboarding',
    match_score DECIMAL(5,2) NOT NULL,
    rank        SMALLINT,
    reason      JSONB        NOT NULL DEFAULT '{}'::jsonb,
    expires_at  TIMESTAMPTZ  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reco UNIQUE (user_id, stock_id, rec_type),
    CONSTRAINT ck_reco_score CHECK (match_score BETWEEN 0 AND 100)
);
CREATE INDEX IF NOT EXISTS idx_reco_user_active ON recommendation_cache (user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_reco_user_rank   ON recommendation_cache (user_id, rec_type, rank);
```

```sql
-- 05. user_behavior_log : 행동 이벤트 로그(월별 RANGE 파티셔닝) + 파티션 2개 + 인덱스
CREATE TABLE IF NOT EXISTS user_behavior_log (
    id          BIGSERIAL   NOT NULL,
    user_id     BIGINT      NOT NULL,
    stock_id    BIGINT,
    event_type  VARCHAR(30) NOT NULL,
    event_value JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at),
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

```sql
-- 06. user_investment_pattern (행동 집계, 1:1) + holding_milestone (보유 마일스톤 스냅샷)
CREATE TABLE IF NOT EXISTS user_investment_pattern (
    id                   BIGSERIAL    PRIMARY KEY,
    user_id              BIGINT       NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE,
    avg_holding_days     DECIMAL(8,2),
    stop_loss_ratio      DECIMAL(5,4),
    add_buy_ratio        DECIMAL(5,4),
    profit_realize_ratio DECIMAL(5,4),
    sector_pref_scores   JSONB NOT NULL DEFAULT '{}'::jsonb,
    behavior_inferred    SMALLINT,
    last_aggregated_at   TIMESTAMPTZ,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS holding_milestone (
    id              BIGSERIAL   PRIMARY KEY,
    user_id         BIGINT      NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    stock_id        BIGINT      NOT NULL REFERENCES stocks_stock(id)  ON DELETE CASCADE,
    milestone_days  SMALLINT    NOT NULL,
    snapshot        JSONB       NOT NULL DEFAULT '{}'::jsonb,
    reached_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_milestone UNIQUE (user_id, stock_id, milestone_days),
    CONSTRAINT ck_milestone_days CHECK (milestone_days IN (30,90,180,365))
);
```

```sql
-- 07. long_term_score / long_term_score_history / user_liked_stock + 인덱스
CREATE TABLE IF NOT EXISTS long_term_score (
    id                   BIGSERIAL    PRIMARY KEY,
    stock_id             BIGINT       NOT NULL REFERENCES stocks_stock(id) ON DELETE CASCADE,
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

CREATE TABLE IF NOT EXISTS long_term_score_history (
    id            BIGSERIAL    PRIMARY KEY,
    stock_id      BIGINT       NOT NULL REFERENCES stocks_stock(id) ON DELETE CASCADE,
    total_score   DECIMAL(5,2) NOT NULL,
    components    JSONB        NOT NULL DEFAULT '{}'::jsonb,
    recorded_date DATE         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_liked_stock (
    id                 BIGSERIAL    PRIMARY KEY,
    user_id            BIGINT       NOT NULL REFERENCES accounts_user(id) ON DELETE CASCADE,
    stock_id           BIGINT       NOT NULL REFERENCES stocks_stock(id)  ON DELETE CASCADE,
    liked_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    base_pbr           DECIMAL(8,3),
    base_match_score   DECIMAL(5,2),
    last_review_status VARCHAR(10),
    last_reviewed_at   TIMESTAMPTZ,
    is_active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_liked UNIQUE (user_id, stock_id),
    CONSTRAINT ck_review_status CHECK (last_review_status IS NULL OR last_review_status IN ('GREEN','YELLOW','RED'))
);

CREATE INDEX IF NOT EXISTS idx_lts_total          ON long_term_score (calculated_date, total_score DESC);
CREATE INDEX IF NOT EXISTS idx_lts_hist_stock_date ON long_term_score_history (stock_id, recorded_date DESC);
CREATE INDEX IF NOT EXISTS idx_uls_user_active    ON user_liked_stock (user_id, is_active);
```

```sql
-- 08. 뉴스 테이블 컬럼 보강 (이미 존재하는 stocks_stocknews / stocks_newsrelatedstock)
ALTER TABLE stocks_stocknews
    ADD COLUMN IF NOT EXISTS summary         TEXT         NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(4,3),
    ADD COLUMN IF NOT EXISTS category        VARCHAR(50)  NOT NULL DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS lang            VARCHAR(8)   NOT NULL DEFAULT 'ko',
    ADD COLUMN IF NOT EXISTS created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW();

ALTER TABLE stocks_stocknews
    ADD CONSTRAINT ck_stock_news_sentiment
        CHECK (sentiment_score IS NULL OR sentiment_score BETWEEN -1 AND 1);

ALTER TABLE stocks_newsrelatedstock
    ADD COLUMN IF NOT EXISTS ticker_code     VARCHAR(20),
    ADD COLUMN IF NOT EXISTS relevance_score DECIMAL(4,3) NOT NULL DEFAULT 1.0,
    ADD COLUMN IF NOT EXISTS created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW();

ALTER TABLE stocks_newsrelatedstock
    ADD CONSTRAINT ck_news_relevance CHECK (relevance_score BETWEEN 0 AND 1);

CREATE INDEX IF NOT EXISTS idx_stock_news_published ON stocks_stocknews (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_stock_news_source    ON stocks_stocknews (source);
CREATE INDEX IF NOT EXISTS idx_nrs_stock  ON stocks_newsrelatedstock (stock_id);
CREATE INDEX IF NOT EXISTS idx_nrs_ticker ON stocks_newsrelatedstock (ticker_code);
CREATE INDEX IF NOT EXISTS idx_nrs_news   ON stocks_newsrelatedstock (news_id);
```

```sql
-- 09. 공통: 최신지표 인덱스 + autovacuum 튜닝 + 섹터평균 MV
CREATE INDEX IF NOT EXISTS idx_indicator_stock_date ON stocks_stockindicator (stock_id, calculated_date DESC);
CREATE INDEX IF NOT EXISTS idx_fin_stock_period     ON stocks_financialsummary (stock_id, fiscal_period DESC);

ALTER TABLE recommendation_cache SET (autovacuum_vacuum_scale_factor = 0.05, autovacuum_analyze_scale_factor = 0.02);
ALTER TABLE user_behavior_log    SET (autovacuum_vacuum_scale_factor = 0.05);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_sector_avg AS
SELECT s.sector,
       AVG(si.roe) AS avg_roe,
       AVG(si.pbr) AS avg_pbr,
       AVG(si.per) AS avg_per,
       COUNT(*)    AS stock_cnt
FROM stocks_stock s
JOIN stocks_stockindicator si ON si.stock_id = s.id
    AND si.calculated_date = (SELECT MAX(calculated_date) FROM stocks_stockindicator WHERE stock_id = s.id)
WHERE s.is_active = TRUE
GROUP BY s.sector;

CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_sector_avg ON mv_sector_avg (sector);
```

```sql
-- 10. (배치 직후 수동) 통계 갱신
VACUUM (ANALYZE) recommendation_cache;
ANALYZE stock_dna;
ANALYZE long_term_score;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_sector_avg;
```

```sql
-- 99. 롤백 (개발 환경 한정, 역순). 뉴스 테이블은 기존 모델이므로 DROP 금지 → 컬럼만 제거.
DROP MATERIALIZED VIEW IF EXISTS mv_sector_avg;
ALTER TABLE stocks_newsrelatedstock
    DROP CONSTRAINT IF EXISTS ck_news_relevance,
    DROP COLUMN IF EXISTS ticker_code, DROP COLUMN IF EXISTS relevance_score, DROP COLUMN IF EXISTS created_at;
ALTER TABLE stocks_stocknews
    DROP CONSTRAINT IF EXISTS ck_stock_news_sentiment,
    DROP COLUMN IF EXISTS summary, DROP COLUMN IF EXISTS sentiment_score, DROP COLUMN IF EXISTS category,
    DROP COLUMN IF EXISTS lang, DROP COLUMN IF EXISTS created_at, DROP COLUMN IF EXISTS updated_at;
DROP TABLE IF EXISTS long_term_score_history, long_term_score, user_liked_stock CASCADE;
DROP TABLE IF EXISTS holding_milestone, user_investment_pattern CASCADE;
DROP TABLE IF EXISTS user_behavior_log CASCADE;
DROP TABLE IF EXISTS recommendation_cache CASCADE;
DROP TABLE IF EXISTS stock_dna CASCADE;
DROP TABLE IF EXISTS user_preferred_sector CASCADE;
ALTER TABLE accounts_investmentprofile
    DROP CONSTRAINT IF EXISTS ck_ip_vector,
    DROP COLUMN IF EXISTS risk_tolerance,  DROP COLUMN IF EXISTS investment_term,
    DROP COLUMN IF EXISTS experience,      DROP COLUMN IF EXISTS loss_aversion,
    DROP COLUMN IF EXISTS behavior,        DROP COLUMN IF EXISTS invest_amount_min,
    DROP COLUMN IF EXISTS invest_amount_max, DROP COLUMN IF EXISTS target_return_pct,
    DROP COLUMN IF EXISTS risk_band_pct,   DROP COLUMN IF EXISTS onboarding_answers,
    DROP COLUMN IF EXISTS profiled_at;
```
