# 주만추 (Jumanchu)

> **자연스러운 주식과의 만남 추구**. 건강한 투자 습관을 돕는 주린이용 모의 주식 투자 서비스
>
> *"주식은 연애처럼 오래가야 한다."*

SSAFY 광주 1반 6조 자율 프로젝트 (2026-05-11 ~ 2026-06-25, 발표 6/25)

---

## 서비스 소개

장기투자 실패 경험을 **연애·소개팅과의 유사성**에서 출발시켜, 취향을 담은 주식 투자 경험을 설계합니다.
판단 근거가 파편화되는 문제를 **뉴스 · 투자 일기 · 커뮤니티**로 보완해, 사용자가 자신의 판단 근거를 남기고 회고할 수 있게 합니다.

- **모의 투자**: 가입 시 1억 원 가상 잔고 지급, 실제 시세 기반 매수/매도
- **시세·재무 데이터**: 한국(코스피·코스닥 전체) + 미국(S&P500·나스닥100 구성종목) 약 4,090종목
- **궁합 추천**: 투자 성향 온보딩(4유형) → 종목 Stock DNA와 매칭한 스와이프 추천
- **장투 케어**: 보유 종목 장투 점수·개인 랭킹·AI 리포트
- **투자 일기 · 커뮤니티**: 매수/매도/관심 이유 기록, 게시글·댓글·좋아요·팔로우

## 기술 스택

| 영역 | 스택 |
|---|---|
| **Backend** | Django 5.2 · Django REST Framework 3.17 · PostgreSQL 16 · Redis 7 (django-redis) |
| **인증** | JWT (`djangorestframework-simplejwt`, refresh 블랙리스트) · `django-ratelimit` |
| **API 문서** | drf-spectacular (Swagger / ReDoc) |
| **Frontend** | Vue 3.5 · Pinia · vue-router · axios · Vite 8 |
| **외부 API** | KIS(한국투자증권) · DART OpenAPI · yfinance · 네이버 뉴스 검색 · RSS · OpenAI(SSAFY GMS) |
| **인프라** | Docker Compose (PostgreSQL + Redis) · cron / 작업 스케줄러 배치 |
| **CI** | GitHub Actions: 치명적 린트 · `manage.py check` · 마이그레이션 누락 검사 · 백엔드 테스트 · 프론트 빌드 |
| **이슈 관리** | Jira (`SCRUM` 프로젝트) |

> **종목 가격 데이터는 KIS API로 통일** (현재가·일봉·호가, 국내/해외 모두).
> yfinance는 `industry`·`homepage_url` 등 **메타데이터 보완용**으로만 사용합니다 (스크래핑 throttling으로 가격 적재엔 부적합).

## 구현 현황 (최종)

| 도메인 | 내용 |
|---|---|
| **인증 (`accounts`)** | 회원가입·로그인·로그아웃·토큰 재발급·내 정보·온보딩·비밀번호 재설정. JWT + 로그인/가입/재설정 rate limiting |
| **종목 (`stocks`)** | 목록·상세·현재가·호가창·캔들 차트(일/주/월봉=DB, 분봉=KIS, 장중 today 합성)·재무 요약·종목 언급 글·시장 요약·인기 랭킹·기간 통계·장 운영 상태·경제 캘린더 |
| **매매·포트폴리오 (`portfolio`)** | 주문 미리보기·매수/매도 체결·주문 내역, 보유 종목·잔고·자산 배분·자산 마일스톤 |
| **투자 일기 (`diary`)** | 매수/매도/관심 일기 CRUD |
| **커뮤니티 (`community`)** | 게시글·댓글 CRUD, 좋아요, 팔로우/팔로워 |
| **추천 (`recommend`)** | 워치리스트, 궁합 스와이프 추천, 장투 랭킹·장투 AI 리포트·점수 히스토리 |
| **뉴스 (`newses`)** | 종목 검색 뉴스, 경제·카테고리 피드, 섹터별·워치리스트·보유 종목·종목별 뉴스 |
| **데이터 파이프라인** | 종목 마스터 적재 + KIS·DART·yfinance enrichment + 일봉·재무·시장지표 적재, 배치 오케스트레이터(`run_batch`), Stock DNA·장투 점수 일배치 |
| **프론트엔드** | 로그인, 온보딩, 홈, 종목 목록·상세, 포트폴리오, 보유 종목, 매매일기, 뉴스, 커뮤니티, 마이페이지 (11개 화면) |
| **테스트** | 백엔드 앱 7개, 테스트 165개 |

### 핵심 설계

- **주문 멱등성 2단 방어**: `idempotency_key` 선검사 + DB `unique` 제약. 동시 요청이 먼저 커밋되면 `IntegrityError`를 잡아 기존 주문을 반환합니다 (`portfolio/services.py`).
- **잠금 순서 고정**: 매수·매도 모두 `select_for_update`로 account → holding 순서로 잠가 교착을 막고, 잔액 음수 방지 동시성 테스트를 둡니다.
- **시세 캐시 TTL 차등**: 현재가 장중 3초 / 장외 60초, 호가 장중 1초 / 장외 30초. 인기 랭킹 시세·체결강도는 워머가 30초 주기로 미리 채웁니다 (TTL 120초).
- **결정적 계산과 LLM 분리**: 점수·등급은 순수 함수가 계산하고, LLM은 종목당 1회 호출로 설명 문장 4개만 생성합니다. LLM 호출부는 주입식이라 가짜 LLM으로 오프라인 테스트가 가능합니다 (`recommend/longterm_report.py`).

## 디렉토리 구조

```
.
├── backend/                # Django 5.2 + DRF
│   ├── config/             # settings, urls, wsgi/asgi
│   ├── accounts/           # 인증 / 사용자 / 투자 성향
│   ├── stocks/             # 종목·시세·재무·시장 요약
│   │   ├── services/       #   kis_client / dart_client / financials / price_dispatch
│   │   └── management/     #   데이터 적재·enrichment·배치·워머 명령
│   ├── portfolio/          # 계좌·보유·주문
│   ├── diary/              # 투자 일기
│   ├── community/          # 게시글·댓글·좋아요·팔로우
│   ├── recommend/          # 워치리스트·궁합 추천·장투 케어
│   ├── newses/             # 뉴스 수집·피드
│   ├── postman/            # Postman 컬렉션
│   └── requirements.txt
├── frontend/               # Vue 3.5 + Pinia + vue-router + Vite 8
├── deploy/                 # 배치 스케줄(cron, Windows 작업 스케줄러, compose)
├── docs/                   # 설계·운영 문서 (ERD/API/인증/Jira/브랜치 등)
├── planning/               # 기획 자료 (기획서·ERD·UCD·화면 시안·아키텍처)
├── presentation/           # 발표 자료
├── 616jy/                 # 장투 케어 알고리즘 원본·명세 (Algo 담당)
├── docker-compose.yml      # PostgreSQL 16 + Redis 7
├── .env.example            # 환경 변수 템플릿
└── CLAUDE.md               # 프로젝트 컨텍스트 / 작업 컨벤션
```

## 빠른 시작

> 새 PC 셋업 · 트러블슈팅 상세는 [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md), 작업 인수인계는 [docs/followup.md](docs/followup.md) 참고.

```powershell
# 0) 환경 변수
cp .env.example .env          # SECRET_KEY / DB_PASSWORD / KIS·DART 키 등 채우기

# 1) 인프라 (PostgreSQL + Redis)
docker compose up -d          # 데이터는 named volume에 보존. down -v 는 DB 삭제이므로 주의

# 2) Backend
cd backend
python -m venv venv           # 최초 1회
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver    # http://localhost:8000/api/docs/

# 3) Frontend
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

데이터(종목 마스터·시세·재무)는 팀 공유 DB 덤프(`jumanchu_db_*.sql`)를 복원하거나, 적재 명령을 직접 실행해 채웁니다. 절차는 [docs/followup.md](docs/followup.md) §4, 배치 운영은 [docs/BATCH_SCHEDULING.md](docs/BATCH_SCHEDULING.md)를 참고하세요.

## 데이터 범위

- **한국**: 코스피 + 코스닥 전체
- **미국**: S&P500 + 나스닥100 구성종목 (비인덱스 USD 종목은 `is_active=False`)
- **시세**: KIS 일봉 약 1년치 (5년 차트 버튼은 1년치만 표시)
- **재무**: DART(한국) / yfinance(미국) → `FinancialSummary` + ROE·ROA·배당수익률 등 투자 지표

## 컨벤션 (요약)

- **브랜치**: `<type>/<JIRA-KEY>-<설명>` · **커밋**: `<type>(<scope>): <subject>  [SCRUM-NN]`
- PR은 `dev` 대상, CI 통과 + 1명 이상 리뷰 → Squash merge. `main`/`dev` 직접 push 금지
- 모델 변경 = 마이그레이션 같이 커밋 / 마이그레이션 파일은 한 사람만 생성
- 상세 → [CLAUDE.md](CLAUDE.md) · [docs/BRANCH_STRATEGY.md](docs/BRANCH_STRATEGY.md)

## 문서

| 문서 | 내용 |
|---|---|
| [docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md) | 팀원·업무 분담, 개발 일정, 발표 직전 구현 정도 (프로젝트 산출물) |
| [docs/ERD.md](docs/ERD.md) | DB 스키마 (진실의 원천) |
| [docs/API_명세_초안.md](docs/API_명세_초안.md) · [docs/API_스키마_v1.5.md](docs/API_스키마_v1.5.md) | API 모듈·스키마 |
| [docs/인증_권한_정책.md](docs/인증_권한_정책.md) | JWT / 권한 정책 |
| [docs/DART_COLUMN.md](docs/DART_COLUMN.md) | 재무 지표 컬럼 사전 |
| [docs/USER_STORIES.md](docs/USER_STORIES.md) | 유저 스토리 / 인수 조건 |
| [docs/BATCH_SCHEDULING.md](docs/BATCH_SCHEDULING.md) | 배치 스케줄 운영 |
| [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) · [docs/followup.md](docs/followup.md) | 로컬 셋업 / 작업 인수인계 |

## 팀

| 이름 | 역할 |
|---|---|
| 강재민 | Backend / 팀 리딩: Django(모델/뷰/URL/마이그레이션), 외부 API 연동, 데이터 파이프라인, 추천 함수 REST 노출 |
| 정율 | Algorithm: 추천 도메인 기획 + 순수 Python 추천 알고리즘 (Stock DNA·궁합 매칭·장투 점수·AI 리포트) |
| 송호영 | Frontend: Vue.js 전반 |
