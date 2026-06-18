# 0618 newses 가이드 (BE 인계)

> 작성: 2026-06-18 / 대상: BE 담당자(강재민)
> 한 줄: **`newses` 앱 — 네이버 검색 API(종목 뉴스) + 언론사 RSS(섹터 뉴스) + 뉴스→섹터/관련주 태깅**. 전부 구현·실측 검증 완료(테스트 31개 통과).
> 주의: 아래 §8에 **내 로컬 환경(Docker/Postgres/Redis 없음) 대응 수정**과 **원 브랜치 머지 방법**을 정리했습니다. 꼭 읽어주세요.

---

## 1. 개요

`backend/newses/` 앱 하나로 다음을 제공합니다.

| 분류 | 소스 | 용도 |
|---|---|---|
| **종목 뉴스** | 네이버 검색 API(실시간) | 종목 상세·관심·보유 뉴스 카드. 전 종목·미장 커버 |
| **섹터/시장 뉴스** | 언론사 경제 RSS(적재형) | 경제/정치/세계 피드 + 뉴스→관련주/섹터 신호(추천용) |

- 외부 의존성 추가 **없음**(전부 Python stdlib + 기존 패키지). `requirements.txt` 변경 없음.
- 알고리즘(`news_sector` 엔티티 매칭)은 **정율님 모듈을 앱 안으로 이식**, 토픽 매칭은 신규 프로토타입.

---

## 2. 엔드포인트 (`/api/v1/` 하위, Swagger: `/api/docs/` "News" 태그)

| Method · Path | 인증 | 설명 |
|---|---|---|
| `GET /news/?query=삼성전자&display=&sort=&content=` | 공개 | 종목명/키워드 네이버 검색 |
| `GET /news/stocks/<code>/?content=` | 공개 | 종목코드 → `Stock.name`으로 검색 |
| `GET /news/economy/` | 공개 | 경제 RSS 피드(=`/news/feed/economy/`) |
| `GET /news/feed/<category>/` | 공개 | 카테고리 피드 (`economy`/`politics`/`world`) |
| `GET /news/by-sector/?sector=운송장비·부품` | 공개 | 섹터 신호(NewsSector) 기준 뉴스 |
| `GET /news/watchlist/` | **JWT** | 관심종목(UserLikedStock) 뉴스 집계 |
| `GET /news/holdings/` | **JWT** | 보유종목(Holding) 뉴스 집계 |
| `python manage.py ingest_rss [--category economy\|politics\|world\|all]` | — | RSS 수집·태깅(스케줄러로 주기 실행 대상) |

**공통 파라미터**: `display`(1~100), `sort`(`date`/`sim`), `content`(true면 본문 포함), `limit`.

---

## 3. 작업 1 — 네이버 Search API 연동 (호출 OK)

- `naver_news.py`: 검색 API 호출 → 기사 리스트. 키는 **환경변수 `NAVER_CLIENT_ID/SECRET` 또는 `CLIENT_ID/SECRET`**, 없으면 `backend/.env` 직접 로드(단독 스크립트도 동작).
- 응답 1건 필드:
  ```json
  { "title": "...", "url": "원문 링크(클릭 대상)", "source": "언론사명",
    "published_at": "ISO", "summary": "네이버 description 스니펫(짧음)",
    "content": "기사 본문(news.naver.com 호스팅분, 최대 2000자)" }
  ```
- **`summary`** = 네이버가 주는 요약 스니펫(우리가 자른 것 아님).
- **`content`** = `?content=true`일 때만 본문 추출(기사당 추가 HTTP라 느려서 옵트인). news.naver.com 호스팅 기사만 추출되고(삼성전자 기준 ~7/10), 비호스팅은 빈값 → `summary`로 대체. 2000자 초과 시 컷.
- **언론사명**: 네이버가 언론사명을 안 줘서 `originallink` 도메인 → 언론사 매핑(`_PRESS_BY_DOMAIN`, 약 62개 매체). 미등록은 호스트 그대로 노출.
- **캐싱** 적용(§5).

---

## 4. 작업 2 — 언론사 RSS / 경제 섹터 뉴스 (호출 OK)

- `rss.py`의 `FEEDS`: **카테고리 → [(언론사, URL), …]** 구조.
  - `economy`: **연합뉴스TV · JTBC · 동아일보 · 조선일보 · 한국경제 · SBS** (6개)
  - `politics`, `world`: 연합뉴스TV (※ '세계'는 연합뉴스 슬러그가 `international`)
- `fetch_feed(category)`: 그 카테고리 **모든 매체를 받아 병합**, 한 매체 실패는 건너뜀(나머지 유지).
- `ingest_rss` 실행 시: RSS 파싱 → `StockNews` 저장(url 기준 중복 제거) → 카테고리(`FeedNews`)·관련주(`NewsRelatedStock`)·섹터(`NewsSector`) 태깅. **idempotent**(재실행 안전).
- 실측: 경제 1회 수집 시 조선100·한경50·동아50·SBS29·연합25·JTBC9 등 ≈250건.
- 참고: **한국경제 피드는 `description`이 없어** `summary`가 빔(제목은 있음 → 태깅·표시엔 무방).
- 매체/카테고리 추가는 `FEEDS`에 한 줄(튜플)이면 끝.

---

## 5. 작업 3 — 섹터 저장 / 중복제거 / 캐싱 등

### 섹터 저장 (뉴스 → 섹터/관련주)
- **엔티티 매칭** `news_sector.extract_sectors`(정율님): 기사에서 기업명/코드/별칭 → 그 종목 + `Stock.sector`. → `NewsRelatedStock`(news↔stock) 저장.
- **토픽 매칭** `topic_sector.extract_topic_sectors`(신규 프로토타입): 회사명 없는 주제형 기사(전쟁/금리/유가 등) → **정본 22 섹터** 키워드 매핑. 예) 전쟁/방위→`운송장비·부품`(정본화상 우주항공·국방), 금리→`금융`, 유가→`화학`+`전기·가스`.
- 두 결과를 **병합해 `NewsSector`(news→sector+score)** 저장 → 추천에서 `preferred_sector`와 매칭하는 단일 소스. `GET /news/by-sector/`로 조회.
  > ⚠️ `topic_sector.TOPIC_KEYWORDS`/`CANONICAL_SECTORS`는 출발점 — 도메인 튜닝 필요(정율님 협의). 섹터 어휘는 `normalize_sectors.py` 정본 22종과 일치해야 함.

### 중복 제거
- 관심/보유 집계(`stocks_news`)에서 **시장 전체 기사가 여러 종목에 겹쳐 나오면 url 기준 1건만** 유지(배지는 먼저 매칭된 종목).

### 캐싱
- 외부 호출 단일 지점 `search_stock_news`에 캐시 → 종목상세·검색·관심/보유 집계가 **공유**.
- **TTL: 장중(평일 09:00–15:30 KST) 60초 / 장외 300초**.
- 캐시 백엔드 장애 시 try/except로 **캐시 미사용 폴백**(요청은 죽지 않음). 운영 Redis엔 `SOCKET_CONNECT_TIMEOUT/SOCKET_TIMEOUT=1` 적용(장애 시 빠른 폴백).

---

## 6. 데이터 모델

**newses 소유(신규 2테이블, 마이그레이션 `0001`/`0002`)** — `StockNews`를 변형하지 않으려고 별도 테이블로 둠:
- `FeedNews(news FK→stocks.StockNews, category)` — 뉴스의 카테고리(economy/politics/world), `(news, category)` 유니크(다중 카테고리 허용).
- `NewsSector(news FK→stocks.StockNews, sector, score)` — 뉴스 섹터 신호, `(news, sector)` 유니크.

**기존(강재민) 모델에 쓰기만 함(스키마 변경 없음)**:
- `stocks.StockNews`(get_or_create, url 유니크), `stocks.NewsRelatedStock`(news↔stock, relevance_score).

---

## 7. 교차 도메인 / 의존성

- **읽기**: `stocks.Stock`, `recommend.UserLikedStock`(관심), `portfolio.Holding`(보유).
- **쓰기**: `stocks.StockNews`, `stocks.NewsRelatedStock`(스키마 변경 X).
- **알고리즘**: `news_sector`(정율) 이식본 사용.
- **신규 pip 패키지 없음** — `requirements.txt` 그대로.

---

## 8. ⭐ 로컬 환경 수정 + 원 브랜치 머지 방법

### 무엇을 왜 고쳤나
내 작업 PC엔 **Docker/Postgres/Redis가 없어서**, 처음에 `settings.py`가 import 시점에 `os.environ['DB_NAME']` **KeyError로 부팅 실패**했습니다. 인프라 없이 돌리려고 `config/settings.py`에 **env 토글 2개**를 넣었습니다(둘 다 **env 미설정 시 기존 동작=Postgres/Redis 그대로** — 하위호환).

```python
# DB: DB_ENGINE=sqlite 면 sqlite3 파일 DB, 아니면 기존 postgresql
if os.environ.get('DB_ENGINE') == 'sqlite': ...sqlite3...
else: ...postgresql (기존과 동일)...

# 캐시: CACHE_BACKEND=locmem 이면 LocMem, 아니면 기존 Redis(+소켓 타임아웃)
if os.environ.get('CACHE_BACKEND') == 'locmem':
    ...LocMemCache...
    SILENCED_SYSTEM_CHECKS = ['django_ratelimit.E003', 'django_ratelimit.W001']  # LocMem은 공유 캐시 아님 → 로컬 한정 무음
else: ...Redis...
```

그리고 로컬 `jumanchu/.env`에 `DB_ENGINE=sqlite`, `CACHE_BACKEND=locmem`을 넣어 씀.

### 핵심: 머지해도 BE 환경은 안 바뀜
- **`.env` 파일들은 `.gitignore`라 머지되지 않습니다.** 즉 내 `DB_ENGINE=sqlite`/`CACHE_BACKEND=locmem`은 **내 PC에만** 존재. BE는 본인 `.env`(Postgres/Redis, 토글 없음)를 그대로 씀.
- `settings.py`의 토글은 **env 미설정이면 기존 Postgres/Redis로 분기** → BE(도커로 인프라 띄움)는 **아무것도 안 건드려도 기존과 100% 동일**하게 동작합니다.
- 따라서 `settings.py` 변경은 **그대로 머지해도 안전**합니다(권장). 인프라 없는 다른 팀원에게도 도움.

### 머지 절차 (권장: 토글 유지)
1. `feature/dev/news` 리뷰 — `newses/` 앱(18파일) + `config/settings.py`(토글) + `config/urls.py`(이미 `include('newses.urls')` 연결됨).
2. 본인 환경 변수에 **네이버 키** 추가: `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`(또는 `CLIENT_ID`/`CLIENT_SECRET`). 운영은 settings/secret로 관리 권장.
3. `docker compose up -d` (Postgres+Redis) → `python manage.py migrate` (newses `0001`,`0002` 테이블 생성).
4. `python manage.py ingest_rss` 로 RSS 적재(이후 **cron/스케줄러 주기 실행** 등록 권장 — §9).
5. `python manage.py test newses` (31개) → PR `dev`, Squash. 커밋/PR에 `[SCRUM-NN]`.

### (대안) 토글 없이 깔끔하게 가져가려면
`settings.py`에서 **아래만 남기고** DB/CACHE 토글 블록은 원래대로 되돌려도 됩니다:
- `INSTALLED_APPS += ['newses']`
- `load_dotenv(BASE_DIR / '.env')` (backend/.env의 네이버 키 로드용 — 키를 다른 곳에 두면 생략 가능)
- (`config/urls.py`) `path('', include('newses.urls'))`

newses 앱 코드 자체는 토글과 무관하게 동작합니다(캐시는 백엔드가 Redis든 LocMem든 OK).

---

## 9. 남은 작업 / TODO

- [ ] **ingest 스케줄링**: `ingest_rss`를 cron/Windows 작업 스케줄러/(운영) Celery beat로 주기 실행.
- [ ] **공시(DART)**: 종목 상세 "공시" 탭은 별도 소스(DART OpenAPI) — 미구현.
- [ ] **AI 요약(OpenAI)**: 기사 종합 요약 — 보류(현재는 네이버 스니펫 `summary`).
- [ ] **토픽 사전 튜닝**: `topic_sector.TOPIC_KEYWORDS` 도메인 보강(정율님).
- [ ] **언론사 사전 보강**: `naver_news._PRESS_BY_DOMAIN` 누락 매체 추가.
- [ ] **본문 전 매체 추출**: 비호스팅 기사 본문까지 원하면 범용 추출 라이브러리(예: trafilatura) 도입 검토 — 신규 의존성.
- [ ] **종목 정규화 의존**: `NewsSector`의 섹터 정합성은 `Stock.sector`가 `normalize_sectors`(SCRUM-146) 적용돼 있어야 함.

---

## 10. 빠른 점검 (BE가 바로 확인)

```bash
# 1) 서버
python manage.py runserver
# 2) 공개 엔드포인트 (브라우저/Swagger 권장 — 한글 파라미터 인코딩 안전)
#    http://localhost:8000/api/docs/  → News 태그 → Try it out
#    http://localhost:8000/api/v1/news/?query=삼성전자&content=true
# 3) RSS 적재 후 피드 확인
python manage.py ingest_rss
#    http://localhost:8000/api/v1/news/economy/
#    http://localhost:8000/api/v1/news/by-sector/?sector=운송장비·부품
```
성공 판단: HTTP 200 + `count>0`, 각 기사에 `title/url/source/published_at`.
