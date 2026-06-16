# 뉴스 기능 작업요약 & BE 연동 가이드 (정율→재민, 2026-06-10)

> 위치: `610jy/` (정율 개인 폴더, 기존 팀 폴더 안 건드림).
> 한 줄: **종목·뉴스 관련 Algo 로직 2종을 만들고 실데이터로 검증 완료.** BE는 아래
> 함수를 view에서 호출만 하면 됨. 함수 입력 규격이 재민님 `Stock` 모델과 정확히 일치.

---

## 0. 무엇을 만들었나 (방향이 반대인 2종)

| | 방향 | 화면(US) | 모듈 |
|---|---|---|---|
| **A** 트렌딩 뉴스 → 종목/섹터 추천 | 뉴스 → 종목 | US-05 추천 스와이프 | `news_sector.py` |
| **B** 종목 → 그 종목/섹터 뉴스 | 종목 → 뉴스 | US-06 종목 상세 뉴스 탭 | `stock_news.py`, `naver_news.py` |

- **A**: 상위 뉴스에서 종목을 태깅 → 그 종목 `sector`로 섹터 산출 (US-05 §117 "뉴스→관련주 매핑 Algo 담당" 그대로).
- **B**: 종목 클릭 → ① 그 회사 뉴스(국장 **본문 전체**/미장 요약) + ② 같은 섹터 뉴스.

---

## 1. 입력 규격이 `Stock` 모델과 1:1 (변환 불필요)

우리 함수는 `StockLike`(code·name·market·sector)를 받는데, 재민님 `Stock`과 동일:

| 함수 입력 | `Stock` 필드 | 비고 |
|---|---|---|
| `code` | `Stock.code` | 미장 티커 검색에 사용 |
| `name` | `Stock.name` | 국장 종목명 검색에 사용 |
| `market` | `Stock.market` | KOSPI/KOSDAQ→국장, NASDAQ/NYSE→미장 자동 분기 |
| `sector` | `Stock.sector` | 테마 뉴스 검색어 |

→ **`Stock` 객체를 그대로 넘기면 됨.** (어댑터 X)

---

## 2. BE가 호출할 함수 (시그니처)

### A. 추천용 — `news_sector.py`
```python
from news_sector import StockRef, extract_sectors

# 뉴스 텍스트 + 종목목록 → 섹터 태그
def extract_sectors(text, stocks, *, summary="") -> list[SectorTag]: ...
#   stocks: list[StockRef(code, name, sector)]  ← Stock.objects.values_list(...)
#   반환  : SectorTag(sector, score, stock_codes)  + .to_dict()

stocks = [StockRef(c, n, s) for c, n, s
          in Stock.objects.values_list("code", "name", "sector")]
tags = extract_sectors(news.title, stocks)
payload = [t.to_dict() for t in tags]
```

### B. 종목 상세 뉴스 — `stock_news.py` (헤드라인, 국장+미장)
```python
from stock_news import fetch_stock_news, fetch_theme_news, fetch_stock_detail_news

fetch_stock_news(stock, *, days=4, limit=10) -> list[StockNewsItem]
fetch_theme_news(sector, *, domestic, days=7, limit=10) -> list[StockNewsItem]
fetch_stock_detail_news(stock, *, days=7, limit=8) -> {"stock_news":[...], "theme_news":[...]}
#   StockNewsItem(title, source, url, published_at, summary)  + .to_dict()
```

### B+. 국장 기사 **본문 전체** — `naver_news.py` (네이버, KR 전용)
```python
from naver_news import fetch_stock_articles

fetch_stock_articles(stock_name, *, display=30, sort="date", limit=8) -> list[NaverArticle]
#   NaverArticle(title, naver_link, origin_link, published_at, summary, body)  + .to_dict()
#   body = 기사 본문 전체(news.naver.com 호스팅 기사). 비호스팅은 body="" → summary 사용
```

---

## 3. 권장 view 로직 (종목 상세 뉴스 탭)

```python
def stock_detail_news(stock):              # stock = Stock 행
    is_kr = stock.market in ("KOSPI", "KOSDAQ")

    if is_kr:
        # 국장: 회사 뉴스는 본문 전체(네이버), 테마는 stock_news
        company = [a.to_dict() for a in fetch_stock_articles(stock.name, limit=8)]
    else:
        # 미장: Yahoo 요약
        company = [it.to_dict() for it in fetch_stock_news(stock, limit=8)]

    theme = [it.to_dict() for it in
             fetch_theme_news(stock.sector, domestic=is_kr, limit=8)]

    return {"company_news": company, "theme_news": theme}
```

---

## 4. 의존성 / 키 / 캐싱 (BE가 챙길 것)

- **패키지**: `requests`(이미 backend venv에 있음). 그 외 stdlib만.
- **네이버 키**: 검색 API Client ID/Secret(무료, 하루 25,000건).
  - 현재 개발용은 `610jy/naver_keys.local`(gitignore됨)에서 로드.
  - **운영은 BE가 Django settings/env로 관리** 권장 → `naver_news`는 환경변수
    `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`도 자동으로 읽음.
- **캐싱(중요)**: 외부 호출이라 US-06 인수조건대로 **장중 1분 / 장외 5분** 캐시 권장.
  구글뉴스·네이버 모두 과호출 시 차단 가능 → BE 캐시로 방어.
- **외부 API 연동은 BE 담당**이라 `stock_news`는 `fetcher` 주입구를 열어둠
  (`fetch_stock_news(stock, fetcher=캐싱버전)`).

---

## 5. 검증 결과 (실데이터)

- ✅ **국장 본문 전체**: 삼성전자→한국경제 2,484자 / 이데일리 1,488자 / 이코노미스트 1,817자 등 추출 성공.
- ✅ **미장**: Apple·Tesla 종목·테마 뉴스 정상(Yahoo).
- ✅ **국장+미장 전 종목 커버**: 검색 기반(종목명/티커)이라 중소형 코스닥도 됨.
- ⚠️ 네이버 본문은 **news.naver.com 호스팅 기사만** 가능 → `display` 넉넉히 받아 호스팅 필터(`hosted_only`).
- ⚠️ 미장 테마 쿼리는 인도장 노이즈 약간 → 시장 맥락 보강 예정.

---

## 6. 합의 필요 / 다음 단계

- [ ] **Algo 모듈 최종 위치** (예: `backend/news/algo/`?) — BE/Algo 합의.
- [ ] view 응답 스키마 확정(위 §3 형태 OK?) → `API_스키마_v1.md` 반영.
- [ ] 네이버 키 운영 관리 주체(BE settings).
- [ ] 캐싱 정책(장중 1분/장외 5분) 적용.
- [ ] (보류) 본문 → 센티멘트로 A 추천 신호 연결 — 오늘은 제외.

> 저작권: 기사 **본문 영구 저장 지양**, 추천 신호·요약 가공 용도로만 (NEWS_API_SPEC §7-1).

---

## 부록. 파일 목록 (`610jy/`)

| 파일 | 역할 |
|---|---|
| `news_sector.py` | A 추천: 뉴스→종목/섹터 (+별칭 사전) |
| `stock_news.py` | B: 종목→뉴스(헤드라인), 테마, 미장 Yahoo |
| `naver_news.py` | B+: 국장 기사 본문 전체(네이버) |
| `demo_*.py` | 각 모듈 독립 실행 검증 |
| `README.md` | 상세 설계·의사결정 기록 |
| `작업요약_BE연동.md` | (이 문서) |
