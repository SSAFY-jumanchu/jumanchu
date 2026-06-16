# 610jy — 뉴스 로직 2종 (2026-06-10, 정율/Algo)

> 정율 개인 작업 폴더. **기존 팀 폴더(backend/docs/kis_test 등)는 건드리지 않음.**
> 오늘 작업: 방향이 반대인 **두 개의 뉴스 기능**을 만들고 실데이터로 검증.

## 0. 두 기능은 방향이 반대 (헷갈리기 쉬움)

| 기능 | 방향 | 화면 | 파일 |
|---|---|---|---|
| **A. 트렌딩 뉴스 → 종목 추천** | 뉴스 → 종목/섹터 | US-05 추천 스와이프 | `news_sector.py` |
| **B. 종목 → 그 종목 뉴스** | 종목 → 뉴스 | US-06 종목 상세 "뉴스 탭" | `stock_news.py` |

- **A**: 상위 뉴스를 종합해 그날 호재 있는 종목을 추천. 뉴스에서 종목을 태깅 →
  그 종목의 `Stock.sector`로 섹터 산출. (USER_STORIES US-05 §117 "뉴스→관련주
  매핑은 Algo 담당(키워드 매칭+종목 동의어 사전)" 에 해당)
- **B**: 사용자가 종목을 클릭하면 그 종목 상세에 들어갈 관련 뉴스를 가져옴.
  종목을 이미 아니까 섹터 추출 불필요 — 그 종목 뉴스를 fetch·필터·정렬.

아래 §1~5는 **A**, §6은 **B** 설명.

---

## 1. [A] 결론 — "종목 → 섹터" 방식 채택

뉴스 텍스트에서 **종목을 태깅**하고, 그 종목의 `Stock.sector`(DB)를 역산해
뉴스의 섹터를 만든다. (키워드 사전 방식은 보류)

### 왜 이게 모델 DB 기준으로 쉬운가 (점검 결과)

| 모델 | 섹터 관련 필드 | 시사점 |
|---|---|---|
| `Stock` | `sector`(50), `industry`(100) | **종목마다 섹터가 이미 DB에 있음** |
| `InvestmentProfile` | `preferred_sector`(50) | 추천이 매칭하는 사용자 선호 섹터 |
| `StockNews` | title/url/source/published_at | 섹터 컬럼 **없음** |
| `NewsRelatedStock` | news ↔ stock M:N | **뉴스–종목 매핑 테이블 이미 존재** |

1. **어휘 일치** — 종목의 `sector`를 그대로 쓰면 `preferred_sector`와 어휘가
   자동 일치 → 추천(궁합 점수)에 바로 사용. 키워드 사전은 라벨이 어긋남.
2. **기존 자산 재사용** — 종목 태깅은 `kis_test`에서 검증됨, `NewsRelatedStock`도 존재.
3. **모델 변경 불필요** — 뉴스 섹터는 `NewsRelatedStock → Stock.sector` 조인으로
   조회 시점 역산 가능. 새 컬럼/마이그레이션 없음.
4. **유지보수 0** — 섹터 사전을 사람이 관리할 필요 없음.

> 한계: 종목을 언급 안 하는 거시 뉴스(금리·환율)는 섹터가 안 나옴 → 추후 키워드
> fallback 영역으로 남김.

## 2. 파일

| 파일 | 기능 | 내용 |
|---|---|---|
| `news_sector.py` | A | **순수 함수 모듈**. `extract_sectors(text, stocks)` / `primary_sector(...)` + `COMMON_KR_ALIASES`. Django 무의존. |
| `demo_news_sector.py` | A | 실제 구글뉴스 RSS로 동작 검증. `python demo_news_sector.py` |
| `be_integration_stub.py` | A | BE view 호출 방법 더미. |
| `stock_news.py` | B | **종목별/테마 뉴스 수집**(헤드라인). `fetch_stock_news` · `fetch_theme_news` · `fetch_stock_detail_news`. 미장=Yahoo. |
| `demo_stock_news.py` | B | 종목 직접 뉴스 검증. `python demo_stock_news.py` |
| `demo_stock_detail.py` | B | **종목+테마 통합** 검증(국장/미장). `python demo_stock_detail.py` |
| `naver_news.py` | B+ | **국장 기사 본문 전체 추출**(네이버 검색 API → news.naver.com DOM 파싱). 키 필요. |
| `demo_naver_news.py` | B+ | 종목 클릭 → 본문 전체 출력. `python demo_naver_news.py` |
| `be_integration_stub.py` | BE가 view에서 호출하는 방법 더미. `python be_integration_stub.py` |

## 3. BE ↔ Algo 인터페이스 (합의 대상)

```python
# Algo 제공 (순수 함수)
def extract_sectors(text: str, stocks: list[StockRef], *, summary: str = "") -> list[SectorTag]: ...

# 입력: BE가 Stock 테이블에서 로드
StockRef(code: str, name: str, sector: str)
# 출력
SectorTag(sector: str, score: float, stock_codes: list[str])  # .to_dict() 제공

# BE 호출
stocks = [StockRef(c, n, s) for c, n, s in Stock.objects.values_list('code','name','sector')]
tags = extract_sectors(news.title, stocks)
payload = [t.to_dict() for t in tags]
```

- `score`: 제목 매칭 1.0 / 본문만 0.5 가중 후 최대값 정규화(0~1).
- 섹터 미검출 시 빈 리스트.

## 4. 실데이터 검증에서 나온 발견

`demo_news_sector.py`를 실제 뉴스에 돌린 결과:

- ✅ 정식 종목명("삼성전자", "LG에너지솔루션")은 정확히 섹터로 분류됨.
- ✅ 한 기사에 여러 섹터(현대차+삼성전자 → 자동차·반도체) 동시 태깅됨.
- ✅ **약어/별칭 대응 완료** (`COMMON_KR_ALIASES`): "삼전·하닉·엔솔·LG엔솔·네이버"
  등을 잡는다. 합성 별칭 "삼전닉스"는 삼성전자+SK하이닉스 두 종목으로 분해.

### 약어 사전 적용 Before / After (실데이터)

| 헤드라인 | 이전 | 이후 |
|---|---|---|
| "삼전닉스 주가까지 흔들려" | 미검출 | 반도체 |
| "삼전·하이닉스 변동성 확대" | 미검출 | 반도체 |
| "꽁꽁 묶인 90조 엔솔 주식" | 미검출 | 2차전지 |
| "삼전닉스·현대차·LG엔솔…" | 자동차 | 반도체+2차전지+자동차 |

> 별칭은 DB에 없는 큐레이션 사전이라 `news_sector.COMMON_KR_ALIASES`에 둔다.
> `extract_sectors(..., aliases=...)`로 주입/교체 가능, `None`이면 비활성.

## 5. 다음 할 일 (A)

- [x] 종목 별칭 사전(삼전/하닉/엔솔 등) → 매칭 커버리지 향상
- [ ] 별칭 사전 확대 — 시총 상위/관심 종목 위주로 큐레이션 보강
- [ ] BE와 시그니처 최종 합의 (Jira 코멘트) + Algo 모듈 위치 확정
- [ ] 섹터 → 추천 궁합 점수 반영 비중 설계 (`preferred_sector` 매칭 가산)

---

## 6. [B] 종목별 뉴스 수집 — US-06 종목 상세 "뉴스 탭"

종목 클릭 → 그 종목 관련 뉴스 리스트. 종목을 이미 알므로 섹터 추출이 아니라
**그 종목 뉴스를 fetch → 필터 → 정렬**한다.

### 파이프라인 (`fetch_stock_news`)
검색 URL 생성(국내=종목명, 해외=티커) → fetch → RSS 파싱 → **출처 화이트리스트
+ 최근 N일** 필터 → 제목 중복제거 → 최신순 → 상위 limit.

### 설계 — 순수 로직 / 네트워크 분리
외부 API 연동은 BE 담당(CLAUDE.md)이라, 순수 로직(`build_news_query`,
`is_whitelisted`, `is_recent`, `dedup_by_title`, `rank_news`)과 네트워크 `fetcher`를
분리했다. BE는 `fetch_stock_news(stock, fetcher=캐싱버전)`으로 주입 교체 가능.

```python
# Algo 제공
def fetch_stock_news(stock, *, days=4, limit=10, fetcher=...) -> list[StockNewsItem]: ...
StockNewsItem(title, source, url, published_at)  # .to_dict() 제공
# stock 은 code/name/market 가진 객체(StockLike) — BE의 Stock 모델 행 그대로 OK
```

### 뉴스 API 선택 — Google News RSS (`search?q=`)
| 후보 | 국장 전체 | 미장 | 키/쿼터 | 판정 |
|---|---|---|---|---|
| **Google News RSS search** | ✅ 종목명 검색=전 종목 | ✅ `hl=en&gl=US` | 무키·무쿼터 | **채택** |
| NewsData.io / Gnews | △ | △ | 일 200건 | 탈락 |
| 언론사 고정 RSS | ✗ 언급 종목만 | ✗ | 무키 | 탈락 |

검색 기반이라 **국장 전 종목·미장 티커 모두 커버**, 무료·무키. rate limit은 BE 캐싱.

### 테마 뉴스 (`fetch_theme_news` / `fetch_stock_detail_news`)
종목의 `Stock.sector`로 같은 섹터 관련주 뉴스를 검색(국내 `"{sector} 관련주"`,
해외 `"{sector} sector stocks"`). 직접 뉴스와 제목 중복 제거.
`fetch_stock_detail_news(stock) → {"stock_news":[...], "theme_news":[...]}`.

### 실데이터 검증 (`demo_stock_detail.py`, 국장+미장)
| 종목 | 시장 | 종목 뉴스 | 테마 뉴스 |
|---|---|---|---|
| 삼성전자 | 국장 대형 | 5 ✅ | 1(반도체) |
| 에코프로비엠 | 국장 중소형 | 1 ⚠️ | 2(2차전지) |
| Apple | 미장 | 5 ✅ | 5(Technology) ✅ |
| Tesla | 미장 | 5 ✅ | 5 ⚠️ |

- ✅ **국장 전체 + 미장 둘 다 동작**(검색 기반 → 중소형 코스닥·미장 티커 커버).
- ✅ `LG에너지솔루션` 0건 케이스 → 화이트리스트 0건이면 최근성만으로 **fallback**(탭 빔 방지).
- ⚠️ **미장 테마 노이즈**: `"Automobiles sector stocks"`가 인도 증시 종목(Maruti 등)을
  끌어옴 → 미장 테마 쿼리에 시장 맥락(US/Wall Street) 추가 필요. **다음 작업.**
- ⚠️ **중소형주 직접뉴스 빈약**(에코프로비엠 1건) → `days` 확대 또는 테마로 보완.

### 다음 할 일 (B)
- [x] 테마(섹터) 뉴스 — A의 sector와 합성한 `fetch_theme_news`
- [x] 국장 **기사 본문 전체** 추출 → §7 네이버 경로
- [ ] 미장 테마 쿼리 시장 맥락 보강(인도장 노이즈 제거)
- [ ] AI 한 줄 요약(헤드라인 종합) — US-06 카드 문구
- [ ] BE와 fetcher/캐싱 정책 합의 (장중 1분/장외 5분 — US-06 인수조건)

---

## 7. [B+] 국장 기사 **본문 전체** — 네이버 검색 API (`naver_news.py`)

"링크 말고 본문 전체"를 위해 KR은 네이버로 분리. (미장은 Yahoo 요약으로 충분)

### 왜 네이버 (헤드라인용 Google News와 별개)
Google News는 인코딩 URL이라 본문을 못 가져온다(저작권 link-only와도 일치). 본문
전체가 필요하면 **네이버 검색 API → `link`(news.naver.com) → 본문 DOM(#dic_area)**
이 가장 깔끔. 검색 기반이라 국장 전 종목 커버, 무료 키(하루 25,000건).

### 핵심 발견 — 호스팅 필터 필수
- 네이버 검색 결과 `link`이 **news.naver.com 호스팅일 때만** 본문 DOM이 일관 →
  본문 추출 가능. 군소 매체(원문 직접 호스팅)는 DOM 제각각 → 본문 불가, 요약 대체.
- `sort=date`는 30건 중 **호스팅 11건**, `sort=sim`은 **29건**. → display를 넉넉히(30)
  받아 **`is_naver_hosted` 필터** 후 상위 N개만 본문 추출(`hosted_only=True`).

### 실데이터 검증 (`demo_naver_news.py`, 본문 전체 출력 성공)
| 종목 | 본문 추출된 매체(예) | 본문 길이 |
|---|---|---|
| 삼성전자 | 이코노미스트 / 아시아경제 / 한국경제 / 이데일리 | 805~2,484자 |
| 에코프로비엠·로보스타 | 주요 매체 본문 정상 추출 | — |

```python
arts = fetch_stock_articles("삼성전자", display=30, sort="date", limit=8)
# NaverArticle(title, naver_link, origin_link, published_at, summary, body)
# body = 기사 본문 전체(호스팅 기사). .to_dict() 제공
```

### 키/보안
- `naver_keys.local`(env도 가능)에서 로드. `.gitignore`로 커밋 차단.
- 저작권: 본문 **영구 저장 지양**, 추천 신호·요약 가공 용도로만(NEWS_API_SPEC §7-1).

### 다음 할 일 (B+)
- [ ] 비호스팅(군소 매체) 본문 — 원문 og/article 파서 보강 or 요약 유지
- [ ] BE 연동: 키는 BE가 settings/secret으로 관리, Algo는 파서 로직 제공
- [ ] 본문 → 센티멘트/요약(A의 추천 신호)로 연결
