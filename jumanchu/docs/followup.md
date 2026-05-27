# 작업 인수인계 — 다음에 할 일

> 다른 PC에서 이어 받을 때 이 문서부터 읽으면 됩니다.
> 갱신: 2026-05-27

---

## 1. 현재 상태 (참고)

`origin/dev`에 머지된 핵심 작업:
- 5개 도메인 모델(`accounts`/`stocks`/`portfolio`/`diary`/`community`) + 마이그레이션
- Stock·Order 모델 필드 보강 (description/homepage_url/ceo_name/employee_count, fee/tax)
- drf-spectacular Swagger 스텁 25개 (`/api/docs/`)
- DART 클라이언트 + FinancialSummary 가공 (`dart_test/`)
- STOCK 마스터 적재 (3577 한국 종목 code/name/market) — `sync_stock_master`
- KIS enrichment 명령 (`enrich_stock_meta_from_kis`) + **전체 실행 완료** (sector/market_cap/StockIndicator per/pbr/eps)
- DART 클라이언트 → `backend/stocks/services/dart_client.py` + `enrich_stock_meta_from_dart` 명령 (ceo_name/homepage_url/industry/listed_at) — 전체 적재 완료
- **US STOCK 마스터 적재 명령 (`sync_us_stock_master`)** — NASDAQ 3,906 + NYSE 2,036 = 미국 5,942종목 (2026-05-27)
- DB 덤프 `jumanchu_db_2026-05-27.sql` (1.4MB, 한국+미국 마스터 + 한국 enrichment 포함, 팀원 공유용 — git 제외)

---

## 2. 다음에 할 일 (우선순위 순)

### 2.1 [P0] Auth 실구현 (SCRUM-24)

Swagger 스텁만 있는 8개 Auth 엔드포인트에 실제 로직 채우기.
- `settings.py`에 `SIMPLE_JWT` 블록 + REST_FRAMEWORK auth class 추가
- signup: User 생성 + Account 자동 생성(balance=1억) — `transaction.atomic`
- login/logout: JWT 발급 + Cookie(HttpOnly) refresh
- 자세히 → `docs/인증_권한_정책.md`

### 2.2 [P0] Stock 조회 API 실구현 (SCRUM-?)

종목 상세 페이지에 필요한 데이터는 이제 다 DB에 있음 (Stock + StockIndicator):
- `GET /api/stocks/{code}/` — sector/market_cap/per/pbr/eps/ceo_name/homepage_url
- `GET /api/stocks/?market=KOSPI&search=` — 검색/필터
- `GET /api/stocks/{code}/price/` — 현재가 (KIS 실시간 호출)
- 캐싱 TTL: 장중 3초 / 장외 60초 (followup §3.4 미래이슈 참조)

### 2.3 [P1] DART 재무 → FinancialSummary 적재 명령 작성

`dart_test/fetch_financials.py`의 `build_financial_summary()` 함수를 `backend/stocks/services/dart_client.py` 옆으로 이전 후 명령 작성. dart_client.py 본체는 이미 backend에 있음.

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

### 2.6 [P1] 미국 종목 enrichment (yfinance)

KOSPI의 KIS+DART enrichment에 대응. 마스터 적재(`sync_us_stock_master`) 완료된 5,942종목에 메타 채우기.

- yfinance `.info` 사용 (인증 불필요, rate limit 약함)
- 매핑 표:

| Stock 필드 | yfinance .info 키 |
|---|---|
| `sector` | `sector` |
| `industry` | `industry` |
| `market_cap` | `marketCap` (USD) |
| `ceo_name` | (직접 키 없음 — `companyOfficers`에서 CEO 추출) |
| `homepage_url` | `website` |
| `description` | `longBusinessSummary` |

```python
import yfinance as yf
info = yf.Ticker("AAPL").info
# 5,942종목 × ~2s ≈ 약 3시간 (sleep 1.0s, 단발 실행 시)
# 시연용 핵심 종목만 우선 (--limit 500 등) 추천
```

- 명령: `enrich_us_stock_meta_from_yfinance` (KIS 명령 미러링)
- 옵션: `--limit`, `--dry-run`, `--only-empty`
- 의존성 추가: `yfinance` (requirements.txt — 현재 미설치)
- 발표 데모용으로는 시총 큰 종목 우선 적재 → `--sort market_cap` 옵션 검토

### 2.7 [P1] KSIC 매핑 테이블 (industry 코드 → 한글 이름)

DART의 `induty_code`는 KSIC 표준 산업 코드("212", "46712" 등). 현재는 코드만 저장돼서 DB browser/admin에서 알아보기 어려움.

- KOSIS에서 KSIC 마스터 다운로드 (~1,000건)
- `KSICCategory(code, name_kr, parent_code)` 모델 + 마이그레이션
- `load_ksic_master` 명령
- 옵션: `Stock.industry`를 `ForeignKey(KSICCategory)`로 변경 (admin에서 자동 표시) — 마이그레이션 주의

> **왜 P1인가**: 사용자에게 보여줄 한글 분류는 `Stock.sector`(KIS 출처)에 이미 있음. KSIC는 세부 필터링/통계용이라 급하지 않음.

### 2.8 [P2] KIS_ENV 정리 (소소)

`.env`에 `KIS_ENV=virtual`인데 `kis_test/kis_domestic_quote.py`는 `vts`만 받음.
→ `backend/stocks/services/kis_client.py`엔 이미 alias 추가됨 (운영용 OK).
→ `kis_test/`는 검증용으로만 남았으므로 굳이 손 안 봐도 됨. 정리할 거면 alias 추가하거나 `.env`를 `vts`로 통일.

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
DART enrichment(company) 한 번에 ~2,800회 사용 → 같은 날 추가로 재무 적재 돌리면 잔여 ~17,000회 (충분).

### 3.4 docker-compose 주의
`docker compose down -v`는 **DB volume까지 삭제** → migrate 다시 필요. 평소엔 `docker compose down`만.

### 3.5 브랜치 컨벤션
- 모델/마이그레이션/settings.py/config 등 공용 파일 만지면 → **feature 브랜치 + PR** 필수
- 본인 앱 내부 단발 작업 + 도메인 owner 본인 → dev 직접 push 허용
- 자세히 → `docs/BRANCH_STRATEGY.md`

### 3.6 DB 덤프 공유 정책
- enrichment 끝난 DB는 `pg_dump`로 `.sql` 파일 떨궈서 공유 (가장 최근: `jumanchu_db_2026-05-26.sql`)
- git에 올리지 말 것 (대용량 + DB 덤프는 코드 아님)
- USB/Google Drive로 공유 OK (시크릿 없음)
- 받는 사람: `docker compose exec -T db psql -U jumanchu -d jumanchu < jumanchu_db_2026-05-26.sql`

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

# 옵션 A: 최신 enrichment까지 끝난 DB 받기 (권장 — KIS+DART 70분 절약)
#   1) 팀원에게 jumanchu_db_YYYY-MM-DD.sql 받기 (USB/Drive)
#   2) cd ..
#   3) docker compose exec -T db psql -U jumanchu -d jumanchu < jumanchu_db_2026-05-26.sql
# 옵션 B: 처음부터 새로 받기
#   python manage.py sync_stock_master                  # 마스터 (~30초)
#   python manage.py enrich_stock_meta_from_kis         # 시세/PER (~50분)
#   python manage.py enrich_stock_meta_from_dart        # CEO/홈페이지/KSIC (~20분)

# 동작 확인
python manage.py runserver    # /api/docs/ 접속
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
