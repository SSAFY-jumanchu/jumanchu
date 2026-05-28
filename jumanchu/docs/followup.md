# 작업 인수인계 — 다음에 할 일

> 다른 PC에서 이어 받을 때 이 문서부터 읽으면 됩니다.
> 갱신: 2026-05-28 (재무/일봉/시장지표 명령 작성 완료 — 전체 적재 실행만 남음)

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
- **US STOCK 마스터 적재 명령 (`sync_us_stock_master`)** — NASDAQ 3,906 + NYSE 2,036 = 미국 5,942종목
- **US enrichment 명령 (`enrich_us_stock_meta`)** — KIS price-detail(HHDFS76200200) + yfinance 하이브리드. 배치 결과: StockIndicator 100%, market_cap 99.8%, sector 45.6% (SPAC 다수 빈값 — 정상), industry 82.5%, homepage_url 78.9% [SCRUM-58]
- DB 덤프 `jumanchu_db_2026-05-27.sql` (1.4MB, 한국+미국 마스터 + 한국 enrichment 포함, 팀원 공유용 — git 제외)
- **Stock 조회 API foundations** (Step 1-3 / 11) — KIS_ENV=prod 전환, `settings.py CACHES` (LocMemCache), 전체 URL trailing slash 패치 (accounts/stocks/portfolio 23 path). Step 4-11(price_dispatch, views, tests)은 다음 세션 [SCRUM-60]
- **재무/일봉/시장지표 명령 3개 작성** (commit a28c73c, **전체 실행 전** — dry-run/소량만 검증):
  - `services/financials.py` — `build_financial_summary` 이전 + roe/roa/payout_ratio 확장
  - `kis_client.get_domestic_daily_price()` — 국내 일봉(FHKST03010100)
  - `enrich_financials` — KR(DART)/US(yfinance) → FinancialSummary + roe/roa/dividend_yield (단위 배수 통일)
  - `sync_stock_prices` — KR(KIS 페이징)/US(yfinance history) → StockPrice 일봉
  - `calc_market_indicators` — StockPrice + ^KS11/^GSPC → beta/volatility/high_52w/low_52w

---

## 2. 다음에 할 일 (우선순위 순)

### 2.1 [P0] Auth 실구현 (SCRUM-24)

Swagger 스텁만 있는 8개 Auth 엔드포인트에 실제 로직 채우기.
- `settings.py`에 `SIMPLE_JWT` 블록 + REST_FRAMEWORK auth class 추가
- signup: User 생성 + Account 자동 생성(balance=1억) — `transaction.atomic`
- login/logout: JWT 발급 + Cookie(HttpOnly) refresh
- 자세히 → `docs/인증_권한_정책.md`

### 2.2 [P0] Stock 조회 API 실구현 Step 4-11 (SCRUM-60)

Step 1-3 foundations 완료 (§1 참조). 남은 단계:
- Step 4: `backend/stocks/services/price_dispatch.py` — KR/US 매퍼 + `fetch_price(stock)` + `get_cache_ttl(stock)` 장중 3s/장외 60s 분기 (KST + ET)
- Step 5: `backend/stocks/pagination.py` — `{items, page, size, total}` envelope helper
- Step 6: `views.py` 3개 view 실구현 — `StockListView`/`StockDetailView`/`StockPriceView` (`is_in_watchlist` false 하드코딩)
- Step 7: `requirements.txt`에 `freezegun` 추가 (시간 의존 테스트용)
- Step 8: `stocks/tests.py` ~15개 케이스 (KIS mock)
- Step 9: 수동 curl + `manage.py spectacular --validate`
- Step 10: docs/API_스키마_v1.md 변경이력 + 이 §2.2 항목 제거
- Step 11: feature 브랜치 PR

> **종목 분류 표시 — serializer에 `display_category` computed field 추가 권장**
> 미국 종목은 `sector`(KIS 한글)가 ~46%만 채워짐 (KIS e_icod가 SPAC/소형주/ADR 미커버). 반면 `industry`(yfinance 영문)는 커버리지가 더 넓음. 단일 표시 필드를 serializer에서 만들어 FE가 분기 없이 쓰게:
> ```python
> # stocks/serializers.py
> display_category = serializers.SerializerMethodField()
> def get_display_category(self, obj):
>     return obj.sector or obj.industry or ""  # 한글 우선, 없으면 영문 fallback
> ```
> → FE는 `display_category` 하나만 사용. sector/industry 분기 로직이 FE에 흩어지지 않음.

세부 plan: `jumanchu/.claude-plans/stock-api.md` (workspace 내부, gitignore)

### 2.3 [P0] 재무 + 일봉 + 시장지표 **전체 적재 실행** (명령 작성 완료, 실행만 남음)

명령 3개 작성·검증 완료 (commit a28c73c, §1 참조). **데이터 전체 적재만 남음 (~5-7시간, 백그라운드)**. 다른 PC에서 돌리고 dump 공유 권장.

```powershell
cd backend
.\venv\Scripts\Activate.ps1
# 순차 실행 (각 명령 --only-empty라 중단 시 재개 가능)
python manage.py enrich_financials --market all --sleep 1.0     *>  ..\_data_fill.log
python manage.py sync_stock_prices --market all --sleep 0.4     *>> ..\_data_fill.log
python manage.py calc_market_indicators                          *>> ..\_data_fill.log
# 끝나면 pg_dump로 jumanchu_db_YYYY-MM-DD.sql 갱신 + 팀 공유 (§3.6)
```

| 단계 | 명령 | 예상 |
|---|---|---|
| 1 | enrich_financials KR (DART) | 25-35분 |
| 2 | enrich_financials US (yfinance) | 1.5-2시간 |
| 3 | sync_stock_prices KR (KIS 페이징) | 1-1.5시간 |
| 4 | sync_stock_prices US (yfinance) | 1.5-2시간 |
| 5 | calc_market_indicators | 10-20분 |

**출처 매핑 (구현됨)**:

| 데이터 | 한국 | 미국 |
|---|---|---|
| FinancialSummary (매출/이익/부채/마진/성장률) | DART `build_financial_summary` | yfinance financials/info |
| roe / roa | DART (순이익/자본·자산) | yfinance returnOnEquity/Assets |
| payout_ratio | DART CF 배당금의지급/순이익 | yfinance payoutRatio |
| dividend_yield | **보류(None)** | yfinance dividendYield (÷100 배수화) |
| 일봉 StockPrice | KIS FHKST03010100 (페이징) | yfinance history 1년 |
| beta/volatility/52주 | StockPrice + ^KS11 | StockPrice + ^GSPC |

**검증된 단위** (모두 배수): 삼성 debt 0.28·payout 0.32·roe 0.086 / AAPL debt 0.795·roe 1.41·div_yld 0.0035.

**알려진 한계 (후속 P1/P2)**:
- 한국 `dividend_yield` 보류(None) — 발행주식수 경로 복잡
- 한국 일부 소형주: 연결재무(CFS) 미제출 → 별도재무(OFS) fallback 미구현, skip됨. 필요 시 `build_financial_summary` fs_div="OFS" 재시도 추가
- `debt_ratio` 정의 차: DART=총부채/자본, yfinance debtToEquity=유이자부채 기준 → 한·미 의미 약간 다름 (통일 검토)
- KIS 모의 일봉 일부 종목 일시 500 → `--only-empty` 재실행으로 복구

### 2.4 [P2] 미국 enrichment yfinance 누락분 보완 (~20%)

1차 배치 도중 yfinance throttling → `--only-empty --no-yfinance` 재실행으로 KIS는 100% 채움. 다만 yfinance(`industry`/`homepage_url`)은 약 80%만 채움. 남은 ~20%는:
- 시연 영향 작음 (대부분 마이너 종목 + SPAC)
- 필요 시 시간 두고 `--only-empty` 한 번 더 (yfinance throttle 해제 후)

### 2.5 [P1] KSIC 매핑 테이블 (industry 코드 → 한글 이름)

DART의 `induty_code`는 KSIC 표준 산업 코드("212", "46712" 등). 현재는 코드만 저장돼서 DB browser/admin에서 알아보기 어려움.

- KOSIS에서 KSIC 마스터 다운로드 (~1,000건)
- `KSICCategory(code, name_kr, parent_code)` 모델 + 마이그레이션
- `load_ksic_master` 명령
- 옵션: `Stock.industry`를 `ForeignKey(KSICCategory)`로 변경 (admin에서 자동 표시) — 마이그레이션 주의

> **왜 P1인가**: 사용자에게 보여줄 한글 분류는 `Stock.sector`(KIS 출처)에 이미 있음. KSIC는 세부 필터링/통계용이라 급하지 않음.

### 2.6 [P2] KIS_ENV 정리 (소소)

현재 `.env`는 `KIS_ENV=prod` (Stock API 실시간 시세용). `kis_test/` 검증 스크립트는 `vts`만 받지만 운영 코드(`backend/stocks/services/kis_client.py`)는 `prod`/`real`/`vts`/`virtual` alias 모두 지원. `kis_test/`는 검증용으로만 남았으므로 굳이 손 안 대도 OK.

### 2.7 [P2] 미래 이슈 (Gemini 피드백 carryover)

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
#   python manage.py sync_stock_master                  # 한국 마스터 (~30초)
#   python manage.py sync_us_stock_master               # 미국 마스터 (~1분)
#   python manage.py enrich_stock_meta_from_kis         # 한국 시세/PER (~50분)
#   python manage.py enrich_stock_meta_from_dart        # 한국 CEO/홈페이지/KSIC (~20분)
#   python manage.py enrich_us_stock_meta               # 미국 sector/PER/industry (~1.5h)

# 옵션 C: 재무/일봉/시장지표까지 전체 (§2.3 — 위 마스터/enrich 끝난 뒤, ~5-7h 추가)
#   python manage.py enrich_financials --market all --sleep 1.0
#   python manage.py sync_stock_prices --market all --sleep 0.4
#   python manage.py calc_market_indicators

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
