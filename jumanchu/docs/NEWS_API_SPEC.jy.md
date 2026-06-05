# 뉴스 RSS API 명세서 (NEWS_API_SPEC)

> 작성일: 2026-05-31
> 목적: 추천 알고리즘(궁합 점수·장투 재검증)의 **뉴스 시그널** 수집을 위한 RSS 기반 뉴스 파이프라인 설계.
> 관련 문서: [`ERD.md`](./ERD.md) (진실의 원천) · [`DART_COLUMN.md`](./DART_COLUMN.md) · [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md)

---

## ⚠️ 선행 분석 결과 (작성 전 읽은 파일)

| 항목 | 결과 |
|---|---|
| DB 스키마(ERD) 읽기 | ✅ `docs/ERD.md` 읽음 — `STOCK`, `STOCK_INDICATOR`, `STOCK_NEWS`, `NEWS_RELATED_STOCK` 등 확인 |
| 실제 DDL/마이그레이션 | ⚠️ 없음. `backend/`는 `config/`만 셋업됨(도메인 앱 미생성). **`ERD.md`가 스키마 진실의 원천**이며, 본 문서 DDL은 ERD 컨벤션을 따른다 |
| 기존 뉴스 테이블 | ⚠️ ERD에 `STOCK_NEWS`, `NEWS_RELATED_STOCK`가 **이름만 정의**됨("변경 없음, 추천 트랙 1.4에서 사용 여부 결정"). 컬럼 DDL은 미확정 → 본 문서에서 제안 |

> ⚠️ **가정 (PK 컨벤션)**: 작업 지시서 예시 DDL은 `news_id UUID`를 사용했으나, **팀 ERD 전체가 `int PK`(SERIAL/BIGSERIAL)** 를 사용하고, 뉴스-종목 매핑이 `stock.id`(int)를 참조해야 정합하므로 **본 문서는 `BIGSERIAL` PK로 통일**한다. (작업 규칙 #4 "기존 팀원 스키마의 PK 방식을 따를 것" 준수)

> ⚠️ **가정 (테이블 네이밍)**: 작업 지시서는 `news_articles` / `news_ticker_mapping`을 제안했으나, ERD에 이미 `STOCK_NEWS` / `NEWS_RELATED_STOCK`가 존재하므로 **ERD 네이밍을 채택**한다(작업 규칙 #1 "기존 테이블명 규칙을 따를 것"). 아래 §4에 필드 매핑을 명시한다.

---

## 1. 개요

### 1-1. 서비스 목적
추천 도메인은 두 군데에서 뉴스 시그널을 소비한다.

| 소비처 | 사용 방식 | 관련 알고리즘 |
|---|---|---|
| **온보딩 추천** | 추천 후보 종목의 최근 7일 뉴스 센티멘트를 가중치로 반영 | 궁합 점수 보정 |
| **장투 재검증/심리지원** | Like 종목의 30/90일 뉴스 트렌드로 "펀더멘털 흔들림" 조기 신호 | 장투 점수 + 하락 시 근거 카드 |

즉 뉴스는 **재무 지표(DART/KIS) + 시장 지표(Beta/PBR)** 에 더해지는 **세 번째 입력 축(센티멘트)** 이다. `STOCK_INDICATOR.news_sentiment_score`(신규)와 장투 스코어링 테이블의 `news_sentiment_score` 컬럼으로 흘러간다 → [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md) §3-4.

### 1-2. RSS 방식 선택 이유
- **무료**: NewsData.io / Gnews 같은 유료 쿼터(일 200건 등) 제약 없음. 6주 학생 프로젝트 예산에 적합.
- **실시간성**: 주요 언론사 RSS는 발행 직후 수 분 내 반영.
- **API 키 불필요**: 대부분의 RSS는 인증 없이 GET 가능 → 비밀키 관리/유출 위험 없음.
- **표준 포맷**: RSS 2.0 / Atom → `feedparser` 단일 라이브러리로 통합 파싱.

> CLAUDE.md상 뉴스 소스는 "NewsData/Gnews, 추천 트랙 1.4에서 결정"으로 보류 상태. 본 RSS 방식은 그 결정을 **무료·무키 RSS 우선**으로 구체화한 제안이다.

### 1-3. 수집 주기 권장사항
| 시간대 | 주기 | 근거 |
|---|---|---|
| 국내 장중 (09:00~15:30 KST) | **15분** | 장중 재료 반영 속도 ↑ |
| 국내 장외 | **1시간** | 발행량 감소 |
| 미국 장중 (22:30~05:00 KST, 서머타임 23:30~06:00) | **15분** | 해외 종목 뉴스 |
| 종목별 구글 뉴스(동적) | **요청 시 + 6시간 캐시** | 종목 상세/장투 카드 진입 시 lazy 수집 |

---

## 2. RSS 피드 목록

> ⚠️ **가정**: 아래 URL은 작업 지시서에 명시된 값을 그대로 채택했다. 일부 피드(네이버 금융, Reuters businessNews 레거시 경로 등)는 RSS 표준이 아니거나 deprecated 가능성이 있어 **§7 주의사항의 헬스체크로 가용성을 1차 검증**해야 한다.

### 2-1. 국내 증권/경제

| 피드명 | URL | 언어 | 업데이트 주기 | 주요 카테고리 | 비고 |
|---|---|---|---|---|---|
| 네이버 금융 뉴스 | `https://finance.naver.com/news/news_list.nhn?mode=LSS2D&section_id=101&section_id2=258` | ko | ~수 분 | 증권 일반 | ⚠️ 표준 RSS 아님(HTML 목록). 스크래핑/별도 파서 필요 가능성 → §7 |
| 한국경제 | `https://www.hankyung.com/feed/all-news` | ko | ~수 분 | 종합/경제 | 전체 뉴스, 증권 외 포함 → 카테고리 필터 권장 |
| 매일경제 | `https://www.mk.co.kr/rss/30000001/` | ko | ~수 분 | 경제 | 섹션 코드별 다수 피드 존재 |
| 연합뉴스TV 경제 | `https://www.yonhapnewstv.co.kr/RSS/20.xml` | ko | ~수십 분 | 경제 | 방송사 피드 |
| 조선비즈 | `https://biz.chosun.com/site/data/rss/rss.xml` | ko | ~수 분 | 경제/산업 | EUC-KR 인코딩 가능성 → §7 |

### 2-2. 해외 증권/경제

| 피드명 | URL | 언어 | 업데이트 주기 | 주요 카테고리 | 비고 |
|---|---|---|---|---|---|
| Reuters Business | `https://feeds.reuters.com/reuters/businessNews` | en | ~수 분 | 비즈니스 | ⚠️ 레거시 경로, 2023년경 변경 이력 → 헬스체크 필수 |
| Yahoo Finance | `https://finance.yahoo.com/news/rssindex` | en | ~수 분 | 마켓 종합 | 안정적 |
| MarketWatch | `https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines` | en | ~분 단위 | 실시간 헤드라인 | 발행량 많음 |
| Investing.com | `https://www.investing.com/rss/news.rss` | en | ~수 분 | 종합 | User-Agent 요구 가능 → §7 |
| Seeking Alpha | `https://seekingalpha.com/feed.xml` | en | ~수십 분 | 분석/리서치 | 일부 본문 요약만 |

### 2-3. 종목별 구글 뉴스 RSS (동적 생성 패턴)

종목 상세/장투 카드 진입 시 종목 단위로 동적 생성한다.

| 대상 | 패턴 | 예시 |
|---|---|---|
| 국내(종목명) | `https://news.google.com/rss/search?q={종목명}+주식&hl=ko&gl=KR&ceid=KR:ko` | `q=삼성전자+주식` |
| 해외(티커) | `https://news.google.com/rss/search?q={TICKER}+stock&hl=en-US&gl=US&ceid=US:en` | `q=AAPL+stock` |

```python
from urllib.parse import quote

def build_google_news_rss(keyword: str, lang: str = "ko") -> str:
    """종목명/티커로 구글 뉴스 RSS URL 생성."""
    if lang == "ko":
        q = quote(f"{keyword} 주식")
        return f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    q = quote(f"{keyword} stock")
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
```

---

## 3. RSS 파싱 방법

### 3-1. Python 파싱 예제 (feedparser)

**설치**
```bash
pip install feedparser requests
# requirements.txt 에 추가
# feedparser==6.0.11
# requests==2.32.3
```

**기본 파싱 (title, link, published, summary 추출 + 에러 처리)**
```python
import logging
from datetime import datetime, timezone
from time import mktime

import feedparser
import requests

logger = logging.getLogger(__name__)

# 일부 피드(Investing.com 등)는 UA 없으면 403 → 브라우저 UA 위장
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JumanchuNewsBot/1.0; +https://jumanchu.example)"
}


def fetch_feed(url: str, timeout: int = 10) -> feedparser.FeedParserDict | None:
    """단일 RSS 피드 안전 파싱. 실패 시 None 반환(전체 배치 중단 방지)."""
    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("RSS fetch 실패 url=%s err=%s", url, e)
        return None

    parsed = feedparser.parse(resp.content)  # bytes 전달 → feedparser가 인코딩 자동 판별
    if parsed.bozo:  # 파싱 경고(인코딩/형식 오류)
        logger.info("RSS bozo 경고 url=%s reason=%s", url, parsed.bozo_exception)
    return parsed


def parse_published(entry) -> datetime | None:
    """published_parsed(struct_time, UTC) → aware datetime."""
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not t:
        return None
    return datetime.fromtimestamp(mktime(t), tz=timezone.utc)
```

**전체 피드 순회 예제**
```python
NATIONAL_FEEDS = {
    "한국경제": "https://www.hankyung.com/feed/all-news",
    "매일경제": "https://www.mk.co.kr/rss/30000001/",
    "연합뉴스TV": "https://www.yonhapnewstv.co.kr/RSS/20.xml",
    "조선비즈": "https://biz.chosun.com/site/data/rss/rss.xml",
}


def collect_all(feeds: dict[str, str]) -> list[dict]:
    """피드 dict를 순회하여 표준화 뉴스 객체 리스트 반환."""
    results: list[dict] = []
    for source, url in feeds.items():
        parsed = fetch_feed(url)
        if parsed is None:
            continue
        for entry in parsed.entries:
            results.append(to_standard_news(source, entry))  # §3-2 참고
    logger.info("수집 완료 source_cnt=%d news_cnt=%d", len(feeds), len(results))
    return results
```

### 3-2. 파싱된 데이터 구조 (표준 뉴스 객체)

```python
import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StandardNews:
    source: str                          # 피드명 (예: "한국경제")
    title: str
    url: str                             # 원문 링크 (DB UNIQUE 키 + 중복 판정)
    published_at: datetime | None
    summary: str = ""
    raw_content: str = ""
    related_tickers: list[str] = field(default_factory=list)  # 종목코드 태깅 결과
    sentiment_score: float | None = None  # 분석 전 None (이후 OpenAI/사전 기반 채움)
    category: str = "general"
    # 앱 레벨 임시 식별자. DB PK는 BIGSERIAL이 부여(아래 ⚠️ 참고)
    news_uid: str = field(default_factory=lambda: str(uuid.uuid4()))


def to_standard_news(source: str, entry) -> dict:
    return StandardNews(
        source=source,
        title=entry.get("title", "").strip(),
        url=entry.get("link", "").strip(),
        published_at=parse_published(entry),
        summary=entry.get("summary", "").strip(),
        raw_content=entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
        category=entry.get("category", "general"),
    ).__dict__
```

> ⚠️ **가정**: 작업 지시서의 표준 객체는 `news_id: str(UUID)`였다. 본 문서는 **앱 레벨 임시 ID는 `news_uid`(UUID 문자열)로 유지**하되, **DB 영구 저장 시 PK는 `BIGSERIAL`(§4)** 가 부여하고 **중복 판정은 `url UNIQUE`** 로 처리한다(URL이 자연키 역할). UUID를 PK로 쓰지 않는 이유는 §선행분석의 PK 컨벤션 참고.

### 3-3. 종목 연관 태깅 로직

뉴스 제목/요약에서 종목명·코드를 추출해 `related_tickers`(종목코드 리스트)로 채운다. 종목 사전은 `STOCK` 테이블(`code`, `name`)에서 1회 로드.

```python
import re

# STOCK 테이블에서 1회 로드: {"삼성전자": "005930", "AAPL": "AAPL", ...}
# 동음이의·짧은 이름 오탐 방지를 위해 2글자 이하 종목명은 제외 권장
def build_stock_dict(stock_rows: list[tuple[str, str]]) -> dict[str, str]:
    """stock_rows = [(name, code), ...] → {name: code}"""
    return {name: code for name, code in stock_rows if len(name) >= 2}


# 한국 6자리 코드 / 미국 티커 정규식
KR_CODE_RE = re.compile(r"\b(\d{6})\b")
US_TICKER_RE = re.compile(r"\b([A-Z]{1,5})\b")  # 본문 영문 대문자 토큰(오탐 많음 → 사전 교차검증)


def tag_related_tickers(text: str, stock_dict: dict[str, str]) -> list[str]:
    """제목+요약 텍스트에서 종목코드 추출.
    1) 종목명 사전 매칭(부분 문자열) 2) 6자리 코드 정규식 3) 사전에 있는 티커만 채택.
    """
    found: set[str] = set()

    # 1) 종목명 매칭
    for name, code in stock_dict.items():
        if name in text:
            found.add(code)

    # 2) 한국 6자리 코드 직접 노출
    for m in KR_CODE_RE.findall(text):
        if m in stock_dict.values():
            found.add(m)

    # 3) 미국 티커 — 사전(values)에 존재하는 것만 채택해 오탐 차단
    valid_tickers = set(stock_dict.values())
    for m in US_TICKER_RE.findall(text):
        if m in valid_tickers:
            found.add(m)

    return sorted(found)
```

**오탐 방지 가이드**
- 2글자 이하 종목명("DB", "SK" 등)은 사전에서 제외하거나 화이트리스트로만.
- 미국 티커는 영문 일반 단어("IT", "CEO", "USA")와 충돌 → **반드시 STOCK 사전 교차검증**.
- 매칭 신뢰도는 `news_related_stock.relevance_score`에 반영(제목 매칭 1.0, 본문만 0.5 등).

---

## 4. PostgreSQL 저장 구조

### 4-1. ERD 정합 및 필드 매핑

ERD의 `STOCK_NEWS` / `NEWS_RELATED_STOCK`를 실 테이블로 채택하고, 작업 지시서의 제안 필드를 흡수한다.

| 작업 지시서 제안 | 본 문서 채택(ERD 정합) | 비고 |
|---|---|---|
| `news_articles` | `stock_news` | ERD 네이밍 |
| `news_ticker_mapping` | `news_related_stock` | ERD 네이밍 |
| `news_id UUID` | `id BIGSERIAL` | PK 컨벤션 |
| `ticker_code VARCHAR` | `stock_id BIGINT FK` + `ticker_code` 캐시 | `STOCK.id` 정합 |

### 4-2. DDL (DBeaver 복사-붙여넣기 실행 가능)

```sql
-- =====================================================================
-- 뉴스 본문 테이블
-- =====================================================================
CREATE TABLE IF NOT EXISTS stock_news (
    id              BIGSERIAL    PRIMARY KEY,
    source          VARCHAR(100) NOT NULL,                 -- 피드명
    title           TEXT         NOT NULL,
    url             TEXT         NOT NULL,                  -- 원문 링크(중복 판정 자연키)
    published_at    TIMESTAMPTZ,                           -- 발행 시각(UTC)
    summary         TEXT         NOT NULL DEFAULT '',
    raw_content     TEXT         NOT NULL DEFAULT '',
    sentiment_score DECIMAL(4,3),                          -- -1.000 ~ 1.000, 분석 전 NULL
    category        VARCHAR(50)  NOT NULL DEFAULT 'general',
    lang            VARCHAR(8)   NOT NULL DEFAULT 'ko',     -- 'ko' / 'en'
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_stock_news_url UNIQUE (url),              -- 중복 수집 차단
    CONSTRAINT ck_stock_news_sentiment CHECK (sentiment_score IS NULL OR sentiment_score BETWEEN -1 AND 1)
);

-- =====================================================================
-- 뉴스 ↔ 종목 매핑 테이블 (N:M)
-- =====================================================================
CREATE TABLE IF NOT EXISTS news_related_stock (
    id              BIGSERIAL    PRIMARY KEY,
    news_id         BIGINT       NOT NULL REFERENCES stock_news(id) ON DELETE CASCADE,
    stock_id        BIGINT       NOT NULL REFERENCES stock(id)      ON DELETE CASCADE,
    ticker_code     VARCHAR(20)  NOT NULL,                 -- 조회 편의용 비정규화 캐시
    relevance_score DECIMAL(4,3) NOT NULL DEFAULT 1.0,     -- 제목매칭 1.0 / 본문만 0.5 등
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_news_stock UNIQUE (news_id, stock_id),
    CONSTRAINT ck_news_relevance CHECK (relevance_score BETWEEN 0 AND 1)
);

-- =====================================================================
-- 인덱스
-- =====================================================================
CREATE INDEX IF NOT EXISTS idx_stock_news_published ON stock_news (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_related_stock   ON news_related_stock (stock_id);
CREATE INDEX IF NOT EXISTS idx_news_related_news    ON news_related_stock (news_id);
```

> ⚠️ **가정**: `stock(id)` 참조는 ERD의 `STOCK` 테이블이 실제 마이그레이션될 때 테이블명이 Django 기본 규칙(`<app>_stock`)으로 생성될 수 있다. 마이그레이션 시점에 실제 테이블명으로 FK 대상을 맞출 것. 기존 데이터가 없는 신규 테이블이므로 DEFAULT/제약을 처음부터 부여했다.

**updated_at 자동 갱신 트리거 (선택)**
```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_stock_news_updated ON stock_news;
CREATE TRIGGER trg_stock_news_updated
    BEFORE UPDATE ON stock_news
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

### 4-3. UPSERT(중복 방지) DML

```sql
-- url 충돌 시 무시(이미 수집됨). 스케줄러가 매 주기 호출.
INSERT INTO stock_news (source, title, url, published_at, summary, raw_content, category, lang)
VALUES (:source, :title, :url, :published_at, :summary, :raw_content, :category, :lang)
ON CONFLICT (url) DO NOTHING;
```

---

## 5. 수집 스케줄러 설계

### 5-1. APScheduler 기반 (단순, 단일 프로세스 — 학생 프로젝트 권장)

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone="Asia/Seoul")

# 국내 장중: 평일 09:00~15:30, 15분 간격
scheduler.add_job(collect_national, "cron", day_of_week="mon-fri",
                  hour="9-15", minute="*/15", id="news_kr_intraday")

# 국내 장외 + 종합: 1시간 간격
scheduler.add_job(collect_national, "cron", minute="0", id="news_kr_offhour")

# 미국 장중(KST 22:30~05:00): 15분 간격
scheduler.add_job(collect_overseas, "cron", hour="22-23,0-5", minute="*/15",
                  id="news_us_intraday")

scheduler.start()
```

### 5-2. Celery beat 기반 (BE가 이미 Celery 도입 시 — ERD §4.2 일봉 배치와 통일)

```python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    "news-kr-intraday": {
        "task": "news.tasks.collect_national",
        "schedule": crontab(minute="*/15", hour="9-15", day_of_week="mon-fri"),
    },
    "news-us-intraday": {
        "task": "news.tasks.collect_overseas",
        "schedule": crontab(minute="*/15", hour="22-23,0-5"),
    },
}
```

> ERD §4.2가 "일일 갱신 매일 16:30 Celery beat"를 이미 사용하므로, **Celery 통일을 권장**(스케줄러 이중화 방지). APScheduler는 Celery 미도입 단계의 임시 대안.

### 5-3. 중복 방지
- 1차: `stock_news.url UNIQUE` + `ON CONFLICT DO NOTHING` (§4-3).
- 2차(선택): 수집 직전 Redis `SET news:url:{md5(url)}` 24h TTL로 DB 왕복 없이 사전 차단.

---

## 6. 추천 알고리즘 연동 포인트

> 알고리즘 로직 출처: `recommend_algorithm/before0525.md`, `기존알고리즘에_추가할장투로직.md`. DB 설계 상세는 [`ALGORITHM_DB_OPTIMIZATION_SPEC.md`](./ALGORITHM_DB_OPTIMIZATION_SPEC.md).

### 6-1. 온보딩 추천 — 최근 7일 센티멘트 집계
종목별 최근 7일 뉴스의 가중 평균 센티멘트를 산출해 궁합 점수에 보정값으로 더한다.

```sql
-- 종목별 최근 7일 가중 평균 센티멘트 (relevance_score 가중)
SELECT nrs.stock_id,
       SUM(sn.sentiment_score * nrs.relevance_score)
         / NULLIF(SUM(nrs.relevance_score), 0) AS weighted_sentiment_7d,
       COUNT(*)                                AS news_cnt_7d
FROM news_related_stock nrs
JOIN stock_news sn ON sn.id = nrs.news_id
WHERE sn.published_at >= NOW() - INTERVAL '7 days'
  AND sn.sentiment_score IS NOT NULL
GROUP BY nrs.stock_id;
```

### 6-2. 장투 추천 — 30/90일 트렌드
Like 종목의 센티멘트 추세(악화/개선)를 장투 재검증 신호에 더한다.

```sql
-- 종목의 30일 vs 90일 센티멘트 비교(추세 악화 감지)
SELECT nrs.stock_id,
       AVG(sn.sentiment_score) FILTER (WHERE sn.published_at >= NOW() - INTERVAL '30 days') AS sent_30d,
       AVG(sn.sentiment_score) FILTER (WHERE sn.published_at >= NOW() - INTERVAL '90 days') AS sent_90d
FROM news_related_stock nrs
JOIN stock_news sn ON sn.id = nrs.news_id
WHERE sn.published_at >= NOW() - INTERVAL '90 days'
  AND sn.sentiment_score IS NOT NULL
GROUP BY nrs.stock_id;
-- sent_30d < sent_90d 이면 최근 분위기 악화 → 장투 '주의' 신호 가산
```

### 6-3. 뉴스 가중치 설정 가이드
| 항목 | 권장 |
|---|---|
| 센티멘트 점수 범위 | `-1.0 ~ +1.0` (DECIMAL(4,3)) |
| 궁합 점수 반영 비중 | 최대 ±5점 (뉴스는 보조 신호, 재무/시장 지표가 주축) |
| 최소 뉴스 수 | 7일 내 3건 미만이면 센티멘트 미반영(노이즈) |
| 센티멘트 산출 | 1차: 한글 금융 사전 기반 룰 / 2차: OpenAI 분류(`POSITIVE/NEUTRAL/NEGATIVE` → `+1/0/-1`) |

---

## 7. 주의사항 및 제한

### 7-1. robots.txt / 이용약관 준수
- RSS는 통상 공개·재배포 허용이나, **본문 전문 저장은 저작권 이슈** → `raw_content`는 요약/메타 위주로 보관, 전문은 링크 제공.
- 네이버 금융, Seeking Alpha 등은 약관 확인 필요. **`raw_content` 미저장 + 링크만** 정책을 기본값으로 권장.

### 7-2. 피드 헬스체크(가용성 검증)
일부 URL은 표준 RSS가 아니거나 deprecated일 수 있음(네이버 금융 HTML 목록, Reuters 레거시 경로).
```python
def healthcheck(feeds: dict[str, str]) -> dict[str, bool]:
    """배치 등록 전 1회 실행해 죽은 피드 골라내기."""
    status = {}
    for name, url in feeds.items():
        parsed = fetch_feed(url)
        status[name] = bool(parsed and parsed.entries)
    return status  # False인 피드는 대체 URL 탐색 또는 비활성화
```

### 7-3. Rate limiting
- 구글 뉴스 RSS는 과도한 호출 시 일시 차단 가능 → 종목별 **요청 시 lazy 수집 + Redis 6h 캐시**.
- 피드 간 호출에 `time.sleep(0.5~1.0)` 간격, 동시 요청 수 제한.

### 7-4. 인코딩 이슈 (EUC-KR → UTF-8)
- `feedparser.parse(resp.content)` 처럼 **bytes를 전달**하면 feedparser가 선언 인코딩을 자동 판별(EUC-KR/CP949 포함).
- 깨질 경우 명시 디코딩:
```python
text = resp.content.decode(resp.apparent_encoding or "utf-8", errors="replace")
parsed = feedparser.parse(text)
```

### 7-5. SSL 인증서 오류
- 기본은 **검증 유지**. 특정 피드만 인증서 문제 시 해당 피드 한정 처리 + 로그(전체 비활성화 금지).
```python
resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=10, verify=True)
# 불가피한 경우에만(보안 위험 인지): verify=False + 경고 로그
```

---

## ✅ 산출물 자체 체크
- [x] RSS 피드 목록 표(국내 5 / 해외 5 / 구글 동적 2패턴)
- [x] feedparser 설치·파싱·순회·에러처리 예제
- [x] 표준 뉴스 객체 + 종목 태깅 정규식
- [x] PostgreSQL DDL(ERD 정합, BIGSERIAL, 인덱스, UNIQUE, CHECK) — DBeaver 실행 가능
- [x] APScheduler/Celery 스케줄러 + 중복 방지
- [x] 추천/장투 연동 SQL + 가중치 가이드
- [x] 주의사항(robots/rate limit/인코딩/SSL)
- [x] 가정 사항 `⚠️` 명시
