# 작업 인수인계 — DART 통합 / 업종 분류 / 다음 작업

> 다른 PC에서 이어 받을 때 이 문서부터 읽으면 됩니다.
> 작성: 2026-05-20 자정 직전

---

## 1. 오늘까지 푸시된 작업 (origin/dev)

최근 커밋 (`git log --oneline -4`):
```
97b0c4f feat(api): drf-spectacular Swagger 문서화 + v1.1 스텁 뷰 25개  [SCRUM-48]
07befc8 feat(backend): 5개 도메인 모델 + 초기 마이그레이션 추가  [SCRUM-23]
689031c docs: 로컬 개발환경 셋업 가이드 추가
f5d004c model 설계 작업 중
```

추가로 이 PR(=followup 푸시)에 포함될 작업:
- `dart_test/dart_client.py` — DART OpenAPI 클라이언트 (corp_code 매핑 + 재무 조회)
- `dart_test/fetch_financials.py` — `FinancialSummary` 컬럼 가공 데모

---

## 2. DART 통합 현재 상태

### 2.1 코드 구조

`dart_test/` 폴더 ([kis_test/](../kis_test/) 패턴 그대로):
- `dart_client.py` — corp_code(8자리) ↔ stock_code(6자리) 매핑 + `fnlttSinglAcnt(All)` 호출
- `fetch_financials.py` — DART raw → `FinancialSummary` 컬럼 dict 변환

`.env`의 `DART_API_KEY`를 `python-dotenv`로 자동 로드 (스크립트 상단 `load_dotenv(dotenv_path="../.env")`).

캐시:
- corp_code 매핑은 `~/.dart_corp_code_cache.json`에 30일 캐싱
- 첫 실행만 ZIP 다운로드(수 초), 이후 즉시 로드

### 2.2 현재 뽑고 있는 11개 필드 (FinancialSummary 모델 대응)

| 필드 | 우선순위 |
|---|---|
| `revenue`, `operating_profit`, `net_profit` | 원본 |
| `operating_margin`, `net_margin` | 수익성 P0 |
| `revenue_yoy`, `operating_profit_yoy`, `net_profit_yoy` | 성장성 P0 |
| `debt_ratio` | 안정성 P0 |
| `equity_ratio`, `current_ratio` | 안정성 P1 |

`FinancialSummary` 모델에 `payout_ratio` 컬럼은 있는데 현재 코드는 안 채움 — 다음에 추가.

---

## 3. 다음에 할 일 (우선순위 순)

### 3.1 [P0] ROE 계산 추가 — DART에서 가능

`FinancialSummary`가 아니라 **`STOCK_INDICATOR`** 모델 적재용. `net_profit / total_equity`로 계산.
`build_financial_summary()`에서 이미 `np`와 `total_equity` 둘 다 추출하고 있으니 **한 줄 추가**면 끝:

```python
"roe": _safe_div(np, total_equity),   # STOCK_INDICATOR로 흘려보낼 값
```

> 단, FinancialSummary 모델엔 `roe` 컬럼이 없음. 따로 dict 키로만 두거나, STOCK_INDICATOR 적재 함수를 별도로 만드는 게 깔끔.

### 3.2 [P1] payout_ratio 계산 추가

`배당금 / 순이익`. DART 응답의 현금흐름표(CIS) 또는 자본변동표(SCE) 쪽에서 "배당금지급" 계정 추출.
계정명 후보가 정확치 않아서 응답 raw 한 번 까보고 확정해야 함:
```python
import json
rows = client.get_single_account_all(samsung_corp, 2024, "11011")
for r in rows:
    if "배당" in r.get("account_nm", ""):
        print(r["sj_div"], r["account_nm"], r["thstrm_amount"])
```

### 3.3 [P0] 업종(sector/industry) 채우기

**Stock 모델의 `sector`/`industry` 어떻게 채울지 결정 필요.** 둘 다 옵션 있음:

| 출처 | 형태 | 비고 |
|---|---|---|
| DART `company.json` → `induty_code` | 숫자 (KSIC) | "264" 같은 코드. 한글명 매핑 사전 별도 필요 |
| **KIS `inquire-price` → `bstp_kor_isnm`** | 한글 | "전기·전자" 처럼 바로 표시 가능. 현재가 호출 시 무료 끼워옴 |
| yfinance `.info['sector']/['industry']` | GICS (영문) | 미국 종목 전용 |

**권장**: 한국 종목은 KIS `bstp_kor_isnm`, 미국 종목은 yfinance. DART의 KSIC는 보조.

확인 명령 (KIS 응답에 진짜 들어있는지 1초컷 검증):
```powershell
cd kis_test
python -c "import os, json, dotenv; dotenv.load_dotenv('../.env'); from kis_domestic_quote import KISDomesticQuote, KISConfig; c = KISDomesticQuote(KISConfig(app_key=os.environ['KIS_APP_KEY'], app_secret=os.environ['KIS_APP_SECRET'], env='vts')); print(json.dumps(c.get_current_price('005930')['output'], ensure_ascii=False, indent=2))"
```
→ `bstp_kor_isnm` 줄 보이면 확정.

### 3.4 [P0] STOCK 마스터 적재 배치 — 1차 완료, sector enrich 미완

**현재 상태 (SCRUM-58 1차 PR)**:
- `backend/stocks/management/commands/sync_stock_master.py` 작성됨
- KIS 종목코드 마스터 zip 파일(`kospi_code.mst.zip` / `kosdaq_code.mst.zip`) 직접 다운로드 + 고정폭 파싱
- KOSPI 1797건 + KOSDAQ 1780건 = **3577 종목 적재 완료** (ETF/펀드/스팩 제외)
- 채워진 필드: `code`, `name`, `market`, `currency='KRW'`, `kis_short_code`, `is_active`

**⚠️ KRX 접근 차단 이슈** (중요)
- `pykrx` / `FinanceDataReader` 둘 다 KRX 정보데이터시스템에 Akamai 봇 차단 걸려서 ticker_list / StockListing 호출 실패
- 우회: KIS 정적 마스터 zip 사용 (인증 불필요)
- 향후 일봉(STOCK_PRICE) 수집 시에도 같은 문제 — pykrx OHLCV는 동작 확인됐으나 KOSDAQ 일부에서 막힐 가능성. yfinance/KIS API 등 대체 출처 필요할 수 있음

**다음 단계 (별도 PR)**
- `enrich_stock_sector` 명령 — KIS `inquire-price` 호출로 `sector`(=bstp_kor_isnm) 채우기
- `enrich_stock_meta` 명령 — KIS 종목 기본정보(`CTPF1604R`)로 market_cap / listed_at / ceo_name / description 등 보강
- 미국 종목(S&P500 / NASDAQ100) — Wikipedia/Slickcharts + yfinance 별도 PR

### 3.4.1 [P1] DART 재무 → Django 적재 management command

ERD §4.1에 적재 흐름 정리돼 있음. 약 3000 종목 (KOSPI ~800 + KOSDAQ ~1600 + S&P500 + NASDAQ100):
- 한국: **pykrx** (코드 리스트) + **KIS** (종목별 상세)
- 미국: Wikipedia/Slickcharts (구성종목) + **yfinance** (메타)

Django management command로 구현:
```bash
python manage.py sync_stock_master --market KOSPI,KOSDAQ
python manage.py sync_stock_master --market US
```

이 시점에 위 3.3의 업종 결정이 필요함.

### 3.5 [P1] 피드백 누적 — 구현 단계에서 처리할 미래 이슈

Gemini 피드백 ([docs/table and api feedback](table%20and%20api%20feedback)) 중 명세대로(계획됨)거나 미래 이슈로 분류된 항목들:

| # | 이슈 | 처리 시점 |
|---|---|---|
| 1.2 | **USD 잔고/환율 처리** — `Account.balance`는 KRW 단일. 해외 주식 매매 시 KRW 잔고에서 환전 차감(고정/실시간 환율)할지, 통화별 잔고 분리할지 결정 필요 | 미국 종목 매매 활성화 직전 |
| 1.4 | **SharedPortfolioItem weight 합계 검증** — 동일 포트폴리오 내 weight 합이 100% 되도록 모델 `clean()` 또는 API 단 validator | 공유 포트폴리오 작성 API 실구현 시 |
| 2.3 | **view_count 락 회피** — Redis `INCR` 버퍼 + Celery 배치(5~10분 주기)로 DB 동기화. 좋아요 카운트도 `CommunityPost.likes_count` 캐싱 컬럼으로 비정규화 | 커뮤니티 API 트래픽 확인 후 또는 초기 구현 시 |
| 2.4 | **캐싱 TTL 유동화** — 장중(09:00~15:30) 3초/1초, 장외 60초+로 분기. KIS TPS 절약 | StockPriceView 실구현 시 |

### 3.6 [P1] DART 재무 → Django 적재 management command (3.4.1과 중복 — 통합 예정)

`backend/stocks/management/commands/sync_financials.py`:
```python
class Command(BaseCommand):
    def handle(self, *args, **opts):
        client = DartClient(DartConfig(api_key=os.environ["DART_API_KEY"]))
        for stock in Stock.objects.filter(currency="KRW", is_active=True):
            corp_code = client.corp_code_of(stock.code)
            data = build_financial_summary(client, corp_code, 2024, "11011")
            FinancialSummary.objects.update_or_create(
                stock=stock, fiscal_period=data["fiscal_period"], defaults=data
            )
```

단, 약 2400 종목 × 분기 4건 = 9600 호출 → DART 일일 한도 20000 안 넘게 페이스 조절.
**Lazy 캐싱 정책** (사용자가 종목 상세 들어올 때 갱신) — ERD §4.4 — 도 같이 고려.

---

## 4. 결정/주의 사항

### 4.1 API 키는 절대 코드에 하드코딩 X

`.env`에만 두고 `dotenv`로 로드. 시크릿 공유는 USB / 비밀 매니저 (절대 카톡·이메일 본문 금지). `LOCAL_SETUP.md` 2단계 참고.

### 4.2 DART 호출 한도

개인 키 1일 20,000건. 매핑 ZIP은 별도 카운트, 재무 조회만 카운트.
- 종목 마스터 일괄 적재(2400개) 시 페이스 조절 (time.sleep 0.05s 정도)
- 분기·연간 합쳐서 한 종목당 보통 4~5건 호출

### 4.3 모델 ↔ DART 응답 필드 불일치 처리

DART 응답의 `account_nm`은 회사마다 다를 수 있음 (예: "매출액" vs "수익(매출액)" vs "영업수익"). 현재 코드는 후보 리스트로 매칭 — 새 회사에서 안 잡히면 raw 까서 후보 추가.

### 4.4 docker-compose / .env

`docker compose down -v`는 **DB volume까지 삭제** → migrate 다시 해야 함. 평소엔 `docker compose down`만 사용.

새 PC 셋업은 [docs/LOCAL_SETUP.md](LOCAL_SETUP.md)에 다 정리돼 있음.

---

## 5. 다른 PC에서 이어받기 체크리스트

```powershell
# 1. 최신 pull
cd jumanchu
git switch dev
git pull origin dev

# 2. .env 준비 (없으면 .env.example 복사 후 KIS·DART 키 채우기)
# .env는 git에 없으므로 USB나 비밀매니저로 옮겨야 함

# 3. backend 셋업
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 4. DB 띄우기 + 마이그레이션
cd ..
docker compose up -d db
cd backend
python manage.py migrate

# 5. DART 테스트 동작 확인
cd ../dart_test
python dart_client.py
python fetch_financials.py

# 6. Swagger UI 확인
cd ../backend
python manage.py runserver
# 브라우저: http://localhost:8000/api/docs/
```

자세한 트러블슈팅은 [docs/LOCAL_SETUP.md §트러블슈팅](LOCAL_SETUP.md) 참고.

---

## 6. 참고 문서

- [docs/ERD.md](ERD.md) — 진실의 원천 (모델 변경 시 먼저 봄)
- [docs/DART_COLUMN.md](DART_COLUMN.md) — 재무 지표 컬럼 사전 (P0/P1/P2)
- [docs/API_명세_초안.md](API_명세_초안.md) — 11개 모듈 엔드포인트 목록
- [docs/API_스키마_v1.md](API_스키마_v1.md) — v1.1 스키마 (Auth/Stock/Order/Portfolio)
- [docs/인증_권한_정책.md](인증_권한_정책.md) — JWT/IsOwner 정책
- [docs/LOCAL_SETUP.md](LOCAL_SETUP.md) — 새 PC 셋업 가이드
