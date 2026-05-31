# 뉴스 RSS API 명세서 — 네이버 금융·국내 경제지 중심 (NEWS_RSS_API_SPEC)
- 작성일: 2026-06-01
- 대상 독자: 백엔드 팀원 (DBeaver + PostgreSQL 환경)
- 관련 문서: [`ERD.md`](./ERD.md) · [`DART_COLUMN.md`](./DART_COLUMN.md) · [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md) · [`DB_OPTIMIZATION_SPEC.md`](./DB_OPTIMIZATION_SPEC.md) · [`NEWS_API_SPEC.md`](./NEWS_API_SPEC.md) · [`RUNBOOK_DBeaver.md`](./RUNBOOK_DBeaver.md)
- 마지막 수정: 2026-06-01

> 목적: 추천(궁합)·장투 알고리즘의 **뉴스 시그널** 수집을 위해, **네이버 금융(종목별/시장/섹터)** 과 국내 경제 전문지(한국경제·연합인포맥스) RSS를 표준 파이프라인으로 정리.

---

## 0. 기존 문서와의 관계 (중복 방지)

이미 [`NEWS_API_SPEC.md`](./NEWS_API_SPEC.md)가 **글로벌 RSS(국내 종합지 + 해외 + 구글뉴스)** 를 폭넓게 다룬다. 본 문서는 그와 **상호 보완**이며 범위를 다음으로 좁힌다.

| 구분 | NEWS_API_SPEC.md (기존) | **NEWS_RSS_API_SPEC.md (본 문서)** |
|---|---|---|
| 초점 | 국내 종합 + 해외 + 구글뉴스 폭넓게 | **네이버 금융(종목/시장/섹터) + 국내 경제 전문지** |
| 종목 매핑 | 본문 텍스트 사전 매칭 위주 | **네이버 금융 URL 파라미터(`code`)로 종목코드 직접 추출** |
| 저장 스키마 | `stock_news` / `news_related_stock` (BIGSERIAL) | **동일 스키마 재사용**(아래 §3에서 정합 명시) |

> 두 문서의 DDL은 **동일한 `stock_news` / `news_related_stock` 테이블**을 가리킨다. 스키마를 새로 만들지 않고 §3에서 그대로 따른다.

> ⚠️ **가정 (PK 컨벤션)**: 팀 ERD 전체가 `int PK`(Django 기본 `BIGSERIAL`)이고 뉴스-종목 매핑이 `stock.id`(int)를 참조해야 정합하므로 PK는 **BIGSERIAL**로 통일한다. 중복 판정 자연키는 `url UNIQUE`.

> ⚠️ **가정 (피드 URL 가용성)**: 네이버 금융·연합인포맥스의 일부 RSS는 시점에 따라 경로가 바뀌거나 표준 RSS가 아닐 수 있다(네이버 금융 뉴스 목록은 HTML 기반인 경우가 있음). 본 문서 URL은 **알려진 패턴 기준**이며, 배치 등록 전 §5-2 헬스체크로 **가용성을 반드시 1차 검증**한다.

---

## 1. 대상 RSS 피드

### 1-1. 네이버 금융 RSS

네이버 금융 뉴스는 ① 시장 전체(증권 섹션) ② 섹터/카테고리 ③ 종목별 의 3계층으로 수집한다.

| 분류 | URL (패턴) | 언어 | 업데이트 주기 | 제공 항목 | 무료 |
|---|---|---|---|---|---|
| 시장 전체(증권) | `https://finance.naver.com/news/news_list.naver?mode=RSS&section_id=101&section_id2=258` | ko | ~수 분 | 제목·링크·발행시각·요약 | ✅ |
| 섹터/카테고리별 | `https://finance.naver.com/news/news_list.naver?mode=RSS&section_id=101&section_id2={code}` | ko | ~수 분 | 동일 | ✅ |
| 종목별 뉴스 | `https://finance.naver.com/item/news.naver?code={종목코드}` (HTML) → 기사 링크에 `?code=` 포함 | ko | ~수 분 | 제목·링크(종목코드 내장)·시각 | ✅ |

**섹터/카테고리 `section_id2` 매핑 (증권 하위)**

| section_id2 | 카테고리 |
|---|---|
| `258` | 증권 일반(시황·전망) |
| `403` | 채권·외환 |
| `404` | 해외 증시 |
| `429` | 종목 분석 |

> ⚠️ **가정**: `section_id2` 코드 값은 네이버 뉴스 섹션 체계 기준의 알려진 값이며, 네이버가 섹션을 개편하면 달라질 수 있다. 등록 전 헬스체크로 실제 응답을 확인할 것.
>
> ⚠️ **종목별 피드 주의**: 네이버 금융 **종목별 뉴스(`item/news.naver`)는 표준 RSS가 아닌 HTML 목록**일 수 있다. 이 경우 (a) 시장/섹터 RSS에서 받은 기사 링크의 `code` 파라미터로 종목을 역매핑하거나(§2-3 권장), (b) 종목 단위가 꼭 필요하면 구글 뉴스 RSS(기존 `NEWS_API_SPEC.md` §2-3 동적 패턴)로 보완한다.

### 1-2. 한국경제신문 RSS

| 피드명 | URL (패턴) | 언어 | 업데이트 주기 | 제공 항목 | 무료 |
|---|---|---|---|---|---|
| 한국경제 전체 | `https://www.hankyung.com/feed/all-news` | ko | ~수 분 | 제목·링크·발행시각·요약 | ✅ |
| 한국경제 경제 | `https://www.hankyung.com/feed/economy` | ko | ~수 분 | 동일 | ✅ |
| 한국경제 증권 | `https://www.hankyung.com/feed/finance` | ko | ~수 분 | 동일 | ✅ |

> 한국경제 RSS는 본문 전문이 아닌 **요약(description)** 제공이 일반적. 본문은 링크로만 보관(저작권 §6-1).
> ⚠️ **가정**: `economy`/`finance` 카테고리 슬러그는 한국경제 피드 명명 패턴 기준 추정값. 헬스체크로 확정.

### 1-3. 연합인포맥스 RSS

연합인포맥스(einfomax)는 채권·외환·증시 등 **기관 투자 관점 속보**가 강해 장투 펀더멘털 신호에 유용하다. 다물/뉴스ML 계열 CMS의 표준 RSS 경로를 따른다.

| 피드명 | URL (패턴) | 언어 | 업데이트 주기 | 제공 항목 | 무료 |
|---|---|---|---|---|---|
| 전체 기사 | `https://news.einfomax.co.kr/rss/allArticle.xml` | ko | ~수 분 | 제목·링크·발행시각·요약 | ✅ |
| 섹션별 | `https://news.einfomax.co.kr/rss/S1N{n}.xml` | ko | ~수 분 | 동일 | ✅ |
| 클릭/인기 | `https://news.einfomax.co.kr/rss/clickTop.xml` | ko | ~수십 분 | 동일 | ✅ |

> ⚠️ **가정**: einfomax RSS 경로(`allArticle.xml`, `S1N{n}.xml`)는 동일 CMS(다물/뉴스ML) 표준 패턴 기준 추정값이다. 섹션 번호 `n`(증권·채권 등)은 헬스체크 + 실제 응답의 `<category>`로 확정할 것.

### 1-4. 무료 여부 / 약관 요약

세 출처 모두 **RSS 자체는 무료·무인증 GET**. 단 **본문 전문 저장·재배포는 제한**되며, 제목·링크·요약·메타데이터 보관이 안전선이다(§6-1).

---

## 2. 수집 방법 명세

### 2-1. feedparser 기반 샘플 코드 (동작 기준)

**설치**
```bash
pip install feedparser requests
# requirements.txt
# feedparser==6.0.11
# requests==2.32.3
```

**피드 안전 파싱 (에러·인코딩 처리 포함)**
```python
import logging
from datetime import datetime, timezone
from time import mktime

import feedparser
import requests

logger = logging.getLogger(__name__)

# 네이버/일부 언론사는 기본 UA에 민감 → 브라우저 UA 위장
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0; +https://jumanchu.example)"
}


def fetch_feed(url: str, timeout: int = 10) -> "feedparser.FeedParserDict | None":
    """단일 RSS 피드 안전 파싱. 실패 시 None (배치 전체 중단 방지)."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("RSS fetch 실패 url=%s err=%s", url, e)
        return None

    # bytes 전달 → feedparser가 XML 선언 인코딩 자동 판별 (EUC-KR/CP949 포함)
    parsed = feedparser.parse(resp.content)
    if parsed.bozo:
        logger.info("RSS bozo 경고 url=%s reason=%s", url, parsed.bozo_exception)
    return parsed


def parse_published(entry) -> "datetime | None":
    """RSS pubDate(struct_time, UTC) → aware datetime."""
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    return datetime.fromtimestamp(mktime(t), tz=timezone.utc) if t else None
```

**XML 필드 → 표준 객체 매핑 + 전체 순회**
```python
NAVER_SECTOR_FEEDS = {
    "네이버증권-일반": "https://finance.naver.com/news/news_list.naver?mode=RSS&section_id=101&section_id2=258",
    "네이버증권-해외": "https://finance.naver.com/news/news_list.naver?mode=RSS&section_id=101&section_id2=404",
    "네이버증권-종목분석": "https://finance.naver.com/news/news_list.naver?mode=RSS&section_id=101&section_id2=429",
}
PRESS_FEEDS = {
    "한국경제-증권": "https://www.hankyung.com/feed/finance",
    "연합인포맥스-전체": "https://news.einfomax.co.kr/rss/allArticle.xml",
}


def to_standard_news(source: str, entry) -> dict:
    """RSS entry → 표준 뉴스 dict.
    title  ← entry.title
    url    ← entry.link        (중복 판정 자연키 + 네이버 종목코드 추출원)
    published_at ← entry.published(pubDate)
    summary ← entry.summary    (description)
    """
    return {
        "source": source,
        "title": entry.get("title", "").strip(),
        "url": entry.get("link", "").strip(),
        "published_at": parse_published(entry),
        "summary": entry.get("summary", "").strip(),
        "category": entry.get("category", "general"),
        "sentiment_score": None,        # 분석 전 None
        "related_tickers": [],          # §2-3에서 채움
    }


def collect_all(feeds: dict[str, str]) -> list[dict]:
    results: list[dict] = []
    for source, url in feeds.items():
        parsed = fetch_feed(url)
        if parsed is None:
            continue
        for entry in parsed.entries:
            results.append(to_standard_news(source, entry))
    logger.info("수집 완료 feeds=%d news=%d", len(feeds), len(results))
    return results
```

### 2-2. XML 파싱 구조 (RSS 2.0 필드 매핑)

| RSS/XML 태그 | feedparser 속성 | 표준 객체 컬럼 | 비고 |
|---|---|---|---|
| `<item><title>` | `entry.title` | `title` | 종목명 태깅 입력 |
| `<item><link>` | `entry.link` | `url` | **UNIQUE 키 + 네이버 `code` 추출원** |
| `<item><pubDate>` | `entry.published` / `published_parsed` | `published_at` | UTC aware로 변환 |
| `<item><description>` | `entry.summary` | `summary` | 본문 아님(요약) |
| `<item><category>` | `entry.category` | `category` | 섹터 분류 |
| `<channel><title>` | `parsed.feed.title` | (로깅용) | 피드 식별 |

### 2-3. 네이버 금융 종목코드 추출 (URL 파라미터 방식)

네이버 금융 기사 링크는 종목 관련 시 쿼리스트링에 **`code=<6자리>`** 를 포함한다. 본문 텍스트 매칭보다 **정확도가 높은 1차 매핑**이므로 우선 적용한다.

```python
from urllib.parse import urlparse, parse_qs
import re

KR_CODE_RE = re.compile(r"^\d{6}$")


def extract_naver_stock_code(url: str) -> "str | None":
    """네이버 금융 기사 URL의 ?code=XXXXXX 추출. 없으면 None.
    예) https://finance.naver.com/item/news_read.naver?...&code=005930&...
    """
    qs = parse_qs(urlparse(url).query)
    code = (qs.get("code") or [None])[0]
    return code if code and KR_CODE_RE.match(code) else None


def tag_tickers(news: dict, name_to_code: dict[str, str]) -> list[str]:
    """1) URL 파라미터 code(정확) → 2) 제목/요약 종목명 사전 매칭(보조)."""
    found: set[str] = set()

    code = extract_naver_stock_code(news["url"])
    if code:
        found.add(code)                       # relevance_score=1.0 대상

    text = f"{news['title']} {news['summary']}"
    for name, c in name_to_code.items():       # name_to_code: STOCK 테이블 1회 로드
        if len(name) >= 2 and name in text:    # 2글자 이하 종목명 오탐 방지
            found.add(c)

    return sorted(found)
```

> `name_to_code`는 `STOCK(name, code)`에서 1회 로드. 동음이의/짧은 이름(`DB`, `SK` 등) 오탐을 막기 위해 2글자 이하 종목명은 제외하거나 화이트리스트로만 사용.
> URL `code`로 잡힌 매핑은 `relevance_score=1.0`, 본문 텍스트 매칭만 잡힌 것은 `0.5`로 차등 저장(§3).

### 2-4. 수집 주기 권장값 (실시간성 ↔ 서버 부하)

| 시간대 | 권장 주기 | 트레이드오프 근거 |
|---|---|---|
| 국내 장중 (09:00~15:30 KST) | **10~15분** | 장중 재료 반영이 추천 신선도에 직접 영향. 5분 미만은 신규 기사 증가분 대비 호출 낭비 큼 |
| 국내 장 시작 전 (07:00~09:00) | **15분** | 전일 마감·해외 야간 재료 반영 |
| 국내 장외 | **1시간** | 발행량 급감 → 잦은 폴링은 동일 결과 반복 |
| 종목별(요청 시) | **lazy + 6시간 캐시** | 종목 상세/장투 카드 진입 시에만. 차단·부하 최소화 |

**부하 관리 원칙**
- 피드는 RSS 1건 = HTTP 1회. 시장/섹터 피드 묶음을 **순차 호출 + `time.sleep(0.5~1.0)`**.
- 모든 신규성은 `url UNIQUE` UPSERT로 흡수하므로, 주기를 줄여도 **중복 INSERT 비용은 0**(§3-3). 비용은 네트워크 호출뿐 → 주기는 "새 기사 발생률"에 맞춰 설정.

---

## 3. PostgreSQL 저장 구조

### 3-1. 스키마 정합 — ⚠️ 두 테이블은 **이미 존재**(ALTER로 보강)

**중요(충돌 주의)**: Phase 1 실제 Django 모델에 `StockNews` / `NewsRelatedStock`가 **이미 마이그레이션되어 존재**한다(테이블명 `stocks_stocknews` / `stocks_newsrelatedstock`). 다만 컬럼이 **최소 구성**뿐이다.

| 테이블(실제명) | 이미 있는 컬럼 | 본 파이프라인이 추가로 필요한 컬럼 |
|---|---|---|
| `stocks_stocknews` | id, title, url(unique), source, published_at | **summary, sentiment_score, category, lang, created_at, updated_at** |
| `stocks_newsrelatedstock` | id, news_id, stock_id, unique(news_id, stock_id) | **ticker_code, relevance_score, created_at** |

따라서 **신규 `CREATE TABLE`이 아니라 `ALTER TABLE`(컬럼 추가)** 가 정답이다. `DB_OPTIMIZATION_SPEC.md` §A-1도 이 두 테이블을 "기존 구조"로 명시하므로, 두 문서가 동일하게 **기존 테이블 + 컬럼 보강** 입장으로 정합한다.

> ⚠️ **가정 (테이블명)**: 위 실제명은 Django 기본 `db_table` 규칙(`<app>_<model>`) 기준. 팀이 `Meta.db_table`을 커스텀했다면 실제명에 맞춰 조정. **ORM 사용 시 아래 SQL은 청사진이며, 모델 필드 추가 후 `makemigrations`/`migrate`로 적용**한다.

### 3-2. DDL — 기존 테이블 컬럼 보강 (ALTER, DBeaver 실행 가능)

```sql
-- =====================================================================
-- (A) 뉴스 본문: 기존 stocks_stocknews 에 수집/센티멘트 컬럼 추가
-- =====================================================================
ALTER TABLE stocks_stocknews
    ADD COLUMN IF NOT EXISTS summary         TEXT         NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS sentiment_score DECIMAL(4,3),                       -- -1.000~1.000, 분석 전 NULL
    ADD COLUMN IF NOT EXISTS category        VARCHAR(50)  NOT NULL DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS lang            VARCHAR(8)   NOT NULL DEFAULT 'ko',
    ADD COLUMN IF NOT EXISTS created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW();

-- url UNIQUE 는 기존 모델(url unique=True)에 이미 존재. 센티멘트 범위만 보강.
ALTER TABLE stocks_stocknews
    ADD CONSTRAINT ck_stock_news_sentiment
        CHECK (sentiment_score IS NULL OR sentiment_score BETWEEN -1 AND 1);

-- =====================================================================
-- (B) 뉴스 ↔ 종목 매핑: 기존 stocks_newsrelatedstock 에 가중치 컬럼 추가
-- =====================================================================
ALTER TABLE stocks_newsrelatedstock
    ADD COLUMN IF NOT EXISTS ticker_code     VARCHAR(20),                        -- 조회 편의용 비정규화 캐시
    ADD COLUMN IF NOT EXISTS relevance_score DECIMAL(4,3) NOT NULL DEFAULT 1.0,  -- URL code 매핑 1.0 / 본문 매칭 0.5
    ADD COLUMN IF NOT EXISTS created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW();

ALTER TABLE stocks_newsrelatedstock
    ADD CONSTRAINT ck_news_relevance CHECK (relevance_score BETWEEN 0 AND 1);
-- unique(news_id, stock_id) 는 기존 모델 제약으로 이미 존재.
```

> **참고 (그린필드 전용)**: 위 두 테이블이 아직 없는 환경(예: 별도 분석 DB)에서 처음부터 만들 때만 아래 `CREATE`를 쓴다. **팀 운영 DB에서는 위 ALTER만 실행**한다.
>
> ```sql
> -- ⚠️ 운영 DB에서는 실행 금지(이미 존재). 그린필드 참고용.
> CREATE TABLE IF NOT EXISTS stocks_stocknews (
>     id BIGSERIAL PRIMARY KEY, source VARCHAR(100) NOT NULL, title TEXT NOT NULL,
>     url TEXT NOT NULL, published_at TIMESTAMPTZ, summary TEXT NOT NULL DEFAULT '',
>     sentiment_score DECIMAL(4,3), category VARCHAR(50) NOT NULL DEFAULT 'general',
>     lang VARCHAR(8) NOT NULL DEFAULT 'ko',
>     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>     CONSTRAINT uq_stock_news_url UNIQUE (url),
>     CONSTRAINT ck_stock_news_sentiment CHECK (sentiment_score IS NULL OR sentiment_score BETWEEN -1 AND 1)
> );
> CREATE TABLE IF NOT EXISTS stocks_newsrelatedstock (
>     id BIGSERIAL PRIMARY KEY,
>     news_id BIGINT NOT NULL REFERENCES stocks_stocknews(id) ON DELETE CASCADE,
>     stock_id BIGINT NOT NULL REFERENCES stocks_stock(id) ON DELETE CASCADE,
>     ticker_code VARCHAR(20), relevance_score DECIMAL(4,3) NOT NULL DEFAULT 1.0,
>     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>     CONSTRAINT uq_news_stock UNIQUE (news_id, stock_id),
>     CONSTRAINT ck_news_relevance CHECK (relevance_score BETWEEN 0 AND 1)
> );
> ```

### 3-3. 인덱스 전략 (종목코드 · 발행시간 · 출처)

```sql
-- 발행시간: 최근 N일 집계(추천/장투 윈도우 쿼리)의 핵심
CREATE INDEX IF NOT EXISTS idx_stock_news_published ON stocks_stocknews (published_at DESC);

-- 출처: 특정 피드 품질 점검·소스별 필터링
CREATE INDEX IF NOT EXISTS idx_stock_news_source ON stocks_stocknews (source);

-- 종목코드: 종목별 뉴스/센티멘트 조회(가장 빈번)
CREATE INDEX IF NOT EXISTS idx_nrs_stock  ON stocks_newsrelatedstock (stock_id);
CREATE INDEX IF NOT EXISTS idx_nrs_ticker ON stocks_newsrelatedstock (ticker_code);
CREATE INDEX IF NOT EXISTS idx_nrs_news   ON stocks_newsrelatedstock (news_id);
```

| 인덱스 | 대상 | 사용 쿼리 | 필요 이유 |
|---|---|---|---|
| `idx_stock_news_published` | `stocks_stocknews(published_at DESC)` | 최근 7/30/90일 센티멘트 집계(§4) | 시간 범위 스캔 + 정렬 제거 |
| `idx_stock_news_source` | `stocks_stocknews(source)` | 출처별 발행량·헬스 점검 | 죽은 피드/품질 모니터링 |
| `idx_nrs_stock` | `stocks_newsrelatedstock(stock_id)` | "이 종목의 뉴스" 조회 | 추천/장투 카드 핵심 경로 |
| `idx_nrs_ticker` | `stocks_newsrelatedstock(ticker_code)` | 코드 문자열 직접 조회 | JOIN 없이 빠른 필터 |

### 3-4. 중복 방지 (URL 기준 UPSERT)

```sql
-- 본문: url 충돌 시 무시(이미 수집됨). 스케줄러가 매 주기 호출.
INSERT INTO stocks_stocknews (source, title, url, published_at, summary, category, lang)
VALUES (:source, :title, :url, :published_at, :summary, :category, :lang)
ON CONFLICT (url) DO NOTHING
RETURNING id;

-- 매핑: (news_id, stock_id) 충돌 시 신뢰도만 갱신(더 높은 값 유지)
INSERT INTO stocks_newsrelatedstock (news_id, stock_id, ticker_code, relevance_score)
VALUES (:news_id, :stock_id, :ticker_code, :relevance_score)
ON CONFLICT (news_id, stock_id)
DO UPDATE SET relevance_score = GREATEST(stocks_newsrelatedstock.relevance_score, EXCLUDED.relevance_score);
```

> `ON CONFLICT (url) DO NOTHING`이 반환행 없으면 이미 존재 → 매핑 INSERT도 skip해 불필요한 작업 차단.
> (선택) DB 왕복 자체를 줄이려면 수집 직전 Redis `SET news:url:{md5(url)} 1 EX 86400`로 사전 차단.

---

## 4. 추천 알고리즘 연동 포인트

> 알고리즘 로직 출처(Phase 1): `recommend_algorithm/before0525.md`, `기존알고리즘에_추가할장투로직.md`. DB 설계 상세는 [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md).

### 4-1. 추천(궁합) 알고리즘과의 연결 지점

Phase 1의 궁합 점수는 **5개 요소(리스크·기간·경험·테마·스타일)** 가중합으로, 입력은 `stock_indicator`(beta/pbr/eps 등)와 `financial_summary`다. 뉴스는 이 점수 위에 얹는 **보조 신호(센티멘트 보정)** 로 연결한다.

- **테마 궁합(20%) 보강**: 종목별 최근 뉴스 `category`/키워드 빈도로 "지금 시장이 주목하는 테마"를 파악 → `user_preferred_sector`와 교차해 트렌딩 가산.
- **궁합 점수 보정**: 최근 7일 가중 평균 센티멘트를 ±보정값으로 환산(아래 §4-3 가중치). 뉴스는 주축이 아니라 보조이므로 영향폭을 제한.
- **README의 "트렌딩 뉴스 기반 관련주 추천"** 트랙과 직접 연결: `stocks_newsrelatedstock`에서 최근 기사 수·센티멘트 상위 종목을 후보로 추출.

```sql
-- 종목별 최근 7일 가중 평균 센티멘트 (온보딩 추천 보정 입력 → stock_dna.news_sentiment 적재)
SELECT nrs.stock_id,
       SUM(sn.sentiment_score * nrs.relevance_score)
         / NULLIF(SUM(nrs.relevance_score), 0) AS weighted_sentiment_7d,
       COUNT(*)                                AS news_cnt_7d
FROM stocks_newsrelatedstock nrs
JOIN stocks_stocknews sn ON sn.id = nrs.news_id
WHERE sn.published_at >= NOW() - INTERVAL '7 days'
  AND sn.sentiment_score IS NOT NULL
GROUP BY nrs.stock_id;
```

### 4-2. 감성분석 결과 저장 컬럼 제안

| 컬럼 | 위치 | 의미 | 채움 시점 |
|---|---|---|---|
| `stocks_stocknews.sentiment_score` | DECIMAL(4,3), `-1.0 ~ +1.0` | 개별 기사 감성 | 수집 후 분석 배치 |
| (집계) `weighted_sentiment_7d` | 쿼리/뷰 산출 | 종목별 단기 분위기 | 추천 시 on-the-fly 또는 캐시 |
| `stock_dna.news_sentiment` | 종목 일배치 캐시 컬럼 (DECIMAL(4,3)) | 추천 입력으로 영속화 | 일 1회 배치 — **DB_OPTIMIZATION_SPEC §B-3(C) 정본** |
| `long_term_score.news_sentiment_score` | 장투 스코어 구성요소 | 장투 점수의 뉴스 축 | 일 1회 배치 — DB_OPTIMIZATION_SPEC §C-3 |

- **1차(무키)**: 한글 금융 감성 사전 기반 룰(호재/악재 키워드) → `+1/0/-1` 이산값.
- **2차(정밀)**: OpenAI 분류(`POSITIVE/NEUTRAL/NEGATIVE`) → `+1/0/-1` 매핑 후 평균.
- 분석 전에는 `NULL`로 두고 집계 쿼리에서 `IS NOT NULL`로 제외(노이즈 차단).

### 4-3. 장투 알고리즘에서의 뉴스 활용

Phase 1 장투 로직은 **월 1회 재검증(ROE/부채비율/EPS증가율/PBR)** + **하락 시 심리 지원**이 핵심. 뉴스는 "펀더멘털 흔들림"을 재무 지표보다 **먼저 잡는 조기 신호**로 연동한다.

- **장투 재검증 보강**: 30일 평균 센티멘트가 90일 평균보다 유의하게 낮으면(분위기 악화) 🟡주의 신호에 가산.
- **하락 시 근거 카드**: 주가 −5%/−15% 트리거 시, 최근 뉴스 센티멘트가 양호하면 "단기 노이즈" 메시지를 강화하고, 악화면 "재검증 카드"를 우선 노출.
- **메시지 근거 소스**: 카드에 노출하는 최근 헤드라인은 `stocks_newsrelatedstock` JOIN으로 종목·최신순 추출.

```sql
-- 종목 30일 vs 90일 센티멘트 비교(추세 악화 감지 → 장투 '주의' 가산)
SELECT nrs.stock_id,
       AVG(sn.sentiment_score) FILTER (WHERE sn.published_at >= NOW() - INTERVAL '30 days') AS sent_30d,
       AVG(sn.sentiment_score) FILTER (WHERE sn.published_at >= NOW() - INTERVAL '90 days') AS sent_90d
FROM stocks_newsrelatedstock nrs
JOIN stocks_stocknews sn ON sn.id = nrs.news_id
WHERE sn.published_at >= NOW() - INTERVAL '90 days'
  AND sn.sentiment_score IS NOT NULL
GROUP BY nrs.stock_id;
-- sent_30d < sent_90d → 최근 분위기 악화
```

**뉴스 가중치 가이드**
| 항목 | 권장 |
|---|---|
| 센티멘트 범위 | `-1.0 ~ +1.0` |
| 궁합/장투 점수 반영폭 | 최대 ±5점 (뉴스는 보조, 재무·시장 지표가 주축) |
| 최소 뉴스 수 | 윈도우 내 3건 미만이면 미반영(노이즈) |
| 신뢰도 가중 | `relevance_score` 곱(URL code 매핑 1.0 우선) |

---

## 5. 주의사항 / 제약

### 5-1. 이용약관 / 크롤링 허용 범위 요약

| 출처 | RSS 접근 | 본문 전문 | 권장 정책 |
|---|---|---|---|
| 네이버 금융 | 무인증 RSS/HTML GET 가능 | ❌ 전문 저장·재배포 제한 | **제목·링크·요약·`code`만** 저장, 본문은 링크 |
| 한국경제 | 무인증 RSS GET 가능 | ❌ 제한 | 요약(description)까지만 보관 |
| 연합인포맥스 | 무인증 RSS GET 가능 | ❌ 제한(통신사 기사) | 제목·링크·요약만, 전문 금지 |

- 공통: **`raw_content`(본문 전문) 미저장**을 기본값으로(저작권 안전선). 본 문서 DDL도 `raw_content` 컬럼을 제외했다.
- 상업적 재배포·대량 아카이빙은 각 사 약관 위반 소지 → 학생 프로젝트 시연/분석 용도로 한정.

### 5-2. Rate limit 대응 + 피드 헬스체크

```python
import time


def collect_with_throttle(feeds: dict[str, str], delay: float = 0.8) -> list[dict]:
    out: list[dict] = []
    for source, url in feeds.items():
        parsed = fetch_feed(url)
        if parsed and parsed.entries:
            out.extend(to_standard_news(source, e) for e in parsed.entries)
        time.sleep(delay)            # 피드 간 간격 → 차단 회피
    return out


def healthcheck(feeds: dict[str, str]) -> dict[str, bool]:
    """배치 등록 전 1회 실행. 죽은/비표준 피드(네이버·einfomax 경로 변동) 걸러내기."""
    return {name: bool((p := fetch_feed(url)) and p.entries) for name, url in feeds.items()}
```

- 네이버는 짧은 간격 반복 호출 시 일시 차단 가능 → 장중 10~15분 주기 + UA 지정 + 피드 간 sleep.
- 종목별 수집은 lazy + 6h 캐시로 호출량 자체를 억제.

### 5-3. 인코딩 처리 (EUC-KR vs UTF-8)

- **권장**: `feedparser.parse(resp.content)`처럼 **bytes 전달** → XML 선언(`<?xml encoding=...?>`)을 보고 feedparser가 EUC-KR/CP949/UTF-8 자동 판별. 대부분 자동 해결.
- 그래도 깨지면 명시 디코딩:
```python
text = resp.content.decode(resp.apparent_encoding or "utf-8", errors="replace")
parsed = feedparser.parse(text)
```
- 국내 일부 레거시 피드는 EUC-KR일 수 있으니, **절대 `resp.text`(requests 추정 인코딩)를 무비판 사용하지 말 것** — 한글 깨짐의 주원인.

### 5-4. SSL / 기타
- 기본 `verify=True` 유지. 특정 피드만 인증서 문제 시 해당 피드 한정 처리 + 경고 로그(전체 비활성화 금지).
- 비표준 응답(HTML이 RSS인 척) 대비: `parsed.entries`가 비면 해당 피드를 §5-2 헬스체크에서 비활성화하고 대체 경로(구글 뉴스 RSS) 사용.

---

## ✅ 산출물 자체 체크
- [x] 네이버 금융 RSS — 시장/섹터/종목별 3계층 + `section_id2` 매핑 표
- [x] 한국경제 / 연합인포맥스 RSS — URL·주기·제공항목·무료여부
- [x] feedparser 동작 샘플(파싱·순회·인코딩·throttle·헬스체크)
- [x] XML 필드 매핑표(title/link/pubDate/description)
- [x] 네이버 종목코드 URL 파라미터(`code`) 추출 코드
- [x] 수집 주기 권장값 + 실시간성↔부하 트레이드오프 근거
- [x] PostgreSQL DDL(BIGSERIAL, 인덱스 3종, URL UPSERT)
- [x] 추천/장투 알고리즘 연동(센티멘트 컬럼·집계 SQL·가중치)
- [x] 약관/Rate limit/인코딩/SSL 주의사항
- [x] 불확실 항목 `⚠️ 가정` 명시 + 헬스체크 절차
