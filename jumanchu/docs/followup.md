# 작업 인수인계 — 다음에 할 일

> 다른 PC에서 이어 받을 때 이 문서부터 읽으면 됩니다.
> 갱신: 2026-05-23

---

## 1. 현재 상태 (참고)

`origin/dev`에 머지된 핵심 작업:
- 5개 도메인 모델(`accounts`/`stocks`/`portfolio`/`diary`/`community`) + 마이그레이션
- Stock·Order 모델 필드 보강 (description/homepage_url/ceo_name/employee_count, fee/tax)
- drf-spectacular Swagger 스텁 25개 (`/api/docs/`)
- DART 클라이언트 + FinancialSummary 가공 (`dart_test/`)
- STOCK 마스터 적재 (3577 종목 code/name/market) — `sync_stock_master`
- KIS enrichment 명령 (`enrich_stock_meta_from_kis`) — 코드는 완성, **실제 DB엔 4건만 적재됨 (테스트)**

---

## 2. 다음에 할 일 (우선순위 순)

### 2.1 [P0] KIS enrichment 전체 실행 — 코드 있음, 실행만 안 했음

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py enrich_stock_meta_from_kis > _enrich.log 2>&1
# 약 50분 소요 (3577 × ~0.8s)
# 끝나면 일시 500 에러로 빠진 것 복구
python manage.py enrich_stock_meta_from_kis --only-empty
```

검증:
```sql
SELECT COUNT(*) FILTER (WHERE sector != '') AS with_sector,
       COUNT(*) FILTER (WHERE market_cap IS NOT NULL) AS with_cap
FROM stocks_stock WHERE currency='KRW' AND is_active=true;
-- 둘 다 3500+ 나오면 OK
```

### 2.2 [P0] DART enrichment 명령 작성 — `enrich_stock_meta_from_dart`

KIS에 없는 정적 메타를 DART `company.json`으로 채움:

| Stock 필드 | DART 출처 |
|---|---|
| `ceo_name` | `ceo_nm` |
| `homepage_url` | `hm_url` |
| `industry` (KSIC 코드) | `induty_code` ("264" 같은 숫자) |
| `listed_at` (근사) | `est_dt` (설립일) |

구현 가이드:
- `dart_test/dart_client.py`를 `backend/stocks/services/dart_client.py`로 옮기기 (KIS와 동일 패턴)
- `dart_client.get_company(corp_code)` 사용
- 호출 한도: 일 20,000건 / 3577종목 × 1회 = 안전
- 옵션: `--limit`, `--dry-run`, `--only-empty`

### 2.3 [P1] DART 재무 → FinancialSummary 적재 명령 작성

`dart_test/fetch_financials.py`의 `build_financial_summary()`를 활용. `backend/stocks/services/dart_client.py`로 같이 이전.

```python
class Command(BaseCommand):
    def handle(self, *args, **opts):
        client = DartClient(DartConfig.from_env())
        for stock in Stock.objects.filter(currency="KRW", is_active=True):
            try:
                corp = client.corp_code_of(stock.code)
            except KeyError:
                continue   # DART에 없는 종목 (비상장/스팩 등)
            data = build_financial_summary(client, corp, bsns_year=2024, reprt_code="11011")
            FinancialSummary.objects.update_or_create(
                stock=stock, fiscal_period=data["fiscal_period"], defaults=data
            )
```

페이스: 3577종목 × 1회(연간 보고서) = 약 30분 (sleep 0.3s).
분기 4건 다 받으면 ×4 = 약 2시간. **시연용은 연간만 권장.**

### 2.4 [P1] ROE 계산 추가 (DART)

`fetch_financials.py`의 `build_financial_summary()`에 한 줄:
```python
"roe": _safe_div(np, total_equity),
```
FinancialSummary에 컬럼 없으니 → StockIndicator 적재 함수로 따로 빼거나, 별도 enrich 명령에서.

### 2.5 [P1] payout_ratio 계산 추가 (DART)

DART 응답의 자본변동표(SCE) 또는 현금흐름표(CIS)에 "배당금지급" 계정 추출.
계정명 후보가 회사마다 다르므로 raw 확인 후 후보 리스트:
```python
dividend_row = _find_account(rows, sj_div="CIS", names=["배당금지급", "배당금의 지급"])
```

### 2.6 [P1] KIS_ENV 정리 (소소)

`.env`에 `KIS_ENV=virtual`인데 `kis_test/kis_domestic_quote.py`는 `vts`만 받음.
→ `backend/stocks/services/kis_client.py`엔 이미 alias 추가됨.
→ `kis_test/`의 옛 클라이언트도 동일 alias 추가하거나 `.env`를 `vts`로 통일.

### 2.7 [P1] 미국 종목 적재 (S&P500 / NASDAQ100)

- Wikipedia/Slickcharts에서 구성종목 ticker 리스트
- yfinance `.info`로 메타 (sector/industry/market_cap/listed_at)
- `Stock.currency='USD'`, `is_sp500=True` / `is_nasdaq100=True` 플래그

```python
# 의사 코드
import yfinance as yf
ticker_obj = yf.Ticker("AAPL")
info = ticker_obj.info
# info['sector'], info['industry'], info['marketCap'], info['city'], info['website']
```

### 2.8 [P0] Auth 실구현 (SCRUM-24)

Swagger 스텁만 있는 8개 Auth 엔드포인트에 실제 로직 채우기.
- `settings.py`에 `SIMPLE_JWT` 블록 + REST_FRAMEWORK auth class 추가
- signup: User 생성 + Account 자동 생성(balance=1억) — `transaction.atomic`
- login/logout: JWT 발급 + Cookie(HttpOnly) refresh
- 자세히 → `docs/인증_권한_정책.md`

### 2.9 [P2] 미래 이슈 (Gemini 피드백 carryover)

구현 단계 진입 시 처리:

| 이슈 | 처리 시점 |
|---|---|
| **USD 잔고/환율 처리** — `Account.balance`는 KRW 단일. 환전 정책 결정 | 미국 종목 매매 활성화 전 |
| **SharedPortfolioItem weight 합계 검증** — 100% 합산 validator | 공유 포트폴리오 API 실구현 시 |
| **view_count 락 회피** — Redis INCR 버퍼 + Celery 배치 동기화 | 커뮤니티 API 트래픽 시 |
| **캐싱 TTL 유동화** — 장중 3초, 장외 60초+ 분기 | StockPriceView 실구현 시 |

---

## 3. 결정/주의 사항

### 3.1 API 키는 절대 코드에 하드코딩 X
`.env`에만 두고 `dotenv`로 로드. 시크릿 공유는 USB 또는 비밀 매니저 (카톡/이메일 본문 금지).

### 3.2 KRX 정보데이터시스템 봇 차단 우회
- `pykrx`/`FinanceDataReader` 둘 다 ticker_list / StockListing 호출 실패 (Akamai)
- 우회 채택: **KIS 정적 마스터 zip** (인증 불필요)
- 향후 일봉(STOCK_PRICE) 수집 시에도 KRX 의존 X — KIS API 또는 yfinance 권장

### 3.3 DART 호출 한도
개인 키 1일 20,000건. 재무 조회만 카운트(corp_code zip은 별도).

### 3.4 docker-compose 주의
`docker compose down -v`는 **DB volume까지 삭제** → migrate 다시 필요. 평소엔 `docker compose down`만.

### 3.5 브랜치 컨벤션 (방금 합의)
- 모델/마이그레이션/settings.py/config 등 공용 파일 만지면 → **feature 브랜치 + PR** 필수
- 본인 앱 내부 단발 작업 + 도메인 owner 본인 → dev 직접 push 허용
- 자세히 → 슬랙 합의 또는 `docs/BRANCH_STRATEGY.md`

---

## 4. 다른 PC에서 이어받기 체크리스트

```powershell
cd jumanchu
git switch dev
git pull origin dev

# .env 준비 (git에 없음 — USB로 옮기거나 .env.example 복사 후 키 채우기)

cd backend
python -m venv venv          # 처음일 때만
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd ..
docker compose up -d db
cd backend
python manage.py migrate

# 동작 확인
python manage.py runserver    # /api/docs/ 접속
python manage.py sync_stock_master --limit 5 --dry-run
python manage.py enrich_stock_meta_from_kis --limit 5 --dry-run
```

자세한 트러블슈팅은 [docs/LOCAL_SETUP.md](LOCAL_SETUP.md) 참고.

---

## 5. 참고 문서

- [docs/ERD.md](ERD.md) — 진실의 원천
- [docs/DART_COLUMN.md](DART_COLUMN.md) — 재무 지표 컬럼 사전
- [docs/API_명세_초안.md](API_명세_초안.md) — 11개 모듈 엔드포인트
- [docs/API_스키마_v1.md](API_스키마_v1.md) — v1.1 스키마 (Auth/Stock/Order/Portfolio)
- [docs/인증_권한_정책.md](인증_권한_정책.md) — JWT/IsOwner 정책
- [docs/LOCAL_SETUP.md](LOCAL_SETUP.md) — 새 PC 셋업
