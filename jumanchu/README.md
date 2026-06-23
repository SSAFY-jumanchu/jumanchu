# 주만추 (Jumanchu)

> **자연스러운 주식과의 만남 추구** — 건강한 투자 습관 정립을 돕는 주린이용 모의 주식 투자 서비스
>
> *"주식은 연애처럼 오래가야 한다."*

SSAFY 광주 1반 6조 자율 프로젝트 (2026-05-11 ~ 2026-06-25)

---

## 서비스 소개

장기투자 실패 경험을 **연애·소개팅과의 유사성**에서 출발시켜, 취향을 담은 주식 투자 경험을 설계합니다.
판단 근거가 파편화되는 문제를 **종목별 뉴스 스크랩 · 투자 일기 · 포트폴리오 커뮤니티**로 보완해, 사용자가 자신의 판단 근거를 가시화하고 회고할 수 있게 합니다.

- **모의 투자** — 가입 시 1억 원 가상 잔고 지급, 실제 시세 기반 매수/매도
- **시세·재무 데이터** — 한국(코스피·코스닥) + 미국(S&P500·나스닥100) 약 4,000여 종목
- **투자 일기** — 매수/매도/관심 이유 기록 → 회고 → 투자 성향 데이터화
- **커뮤니티** — 종목·포트폴리오 공유 및 리뷰

## 기술 스택

| 영역 | 스택 |
|---|---|
| **Backend** | Django 5.2 · Django REST Framework 3.17 · PostgreSQL 16 · Redis 7 |
| **인증** | JWT (`djangorestframework-simplejwt`, refresh 블랙리스트) · `django-ratelimit` |
| **API 문서** | drf-spectacular (Swagger / ReDoc) |
| **Frontend** | Vue 3.5 · Pinia · vue-router · axios · Vite 8 |
| **외부 API** | KIS(한국투자증권) · DART OpenAPI · yfinance · NewsData·Gnews · OpenAI |
| **인프라** | Docker Compose (PostgreSQL + Redis) · GitHub Actions CI |
| **이슈 관리** | Jira (`SCRUM` 프로젝트) |

> **종목 가격 데이터는 KIS API로 통일** (현재가·일봉·호가 — 국내/해외 모두).
> yfinance는 `industry`·`homepage_url` 등 **메타데이터 보완용**으로만 사용 (스크래핑 throttling으로 가격 적재엔 부적합).

## 구현 현황

### ✅ 구현 완료

| 도메인 | 내용 |
|---|---|
| **인증 (`accounts`)** | 회원가입·로그인·로그아웃·토큰 재발급·내 정보·온보딩·비밀번호 재설정 (7개 엔드포인트). JWT + 로그인/가입/재설정 rate limiting |
| **종목 조회 (`stocks`)** | 종목 목록·상세·현재가·캔들 차트(일/주/월봉=DB, 분봉=KIS, 장중 today 합성). Redis 시세 캐싱(장중 3s / 장외 60s) |
| **데이터 파이프라인** | 마스터 적재 + KIS·DART·yfinance enrichment + 일봉·재무·시장지표 적재 (관리 명령 9개). 한국 전체 + 미국 인덱스 구성종목 약 4,090종목, 일봉 1년치 적재 완료 |
| **API 문서** | drf-spectacular 스키마 25종 (`/api/docs/`, `/api/redoc/`) |

### 🚧 개발 예정

| 도메인 | 내용 | 상태 |
|---|---|---|
| **매매·포트폴리오 (`portfolio`)** | 주문 미리보기·체결, 보유 종목·잔고·자산 배분 조회 | 모델·시리얼라이저·URL 완료, **뷰 미구현(501)** |
| **종목 조회 잔여 (`stocks`)** | 호가창 · 재무 요약 · 종목 언급 글 · 시장 요약(홈 상단) | 스텁(501) |
| **투자 일기 (`diary`)** | 매수/매도/관심 일기 작성, 회고(`DiaryReview`), 투자 성향 데이터화 | 모델만 |
| **커뮤니티 (`community`)** | 공유 포트폴리오, 게시글·댓글·좋아요 | 모델만 |
| **추천 알고리즘 (Algo)** | 트렌딩 뉴스 기반 / 재무 기반 / 투자 성향 기반 종목 추천. BE는 함수 호출 후 REST로 노출 | 인터페이스 협의 단계 |
| **뉴스 연동** | NewsData·Gnews 수집 → 종목 매핑(`NewsRelatedStock`) → 스크랩/폴더화 | 모델만 |
| **투자 MBTI · 리포트** | 일기·매매 데이터 기반 투자 성향 요약, 개인화 리포트 발행 | 기획 |
| **프론트엔드** | 회원/온보딩, 홈(시장 요약·포트폴리오·커뮤니티), Tinder 스와이프형 종목 추천 UI 등 전 화면 | Vite 스캐폴드 단계 |

## 디렉토리 구조

```
jumanchu/
├── backend/                # Django 5.2 + DRF
│   ├── config/             # settings, urls, wsgi/asgi
│   ├── accounts/           # 인증 / 사용자 / 투자 성향   (구현)
│   ├── stocks/             # 종목·시세·재무·뉴스          (조회 일부 구현 + 데이터 파이프라인)
│   │   ├── services/       #   kis_client / dart_client / financials / price_dispatch
│   │   └── management/     #   데이터 적재·enrichment 명령 9개
│   ├── portfolio/          # 계좌·보유·주문               (모델·URL 완료, 뷰 예정)
│   ├── diary/              # 투자 일기                    (모델만)
│   ├── community/          # 공유 포트폴리오·게시글       (모델만)
│   ├── postman/            # Postman 컬렉션
│   └── requirements.txt
├── frontend/               # Vue 3.5 + Pinia + vue-router + Vite 8
├── docs/                   # 설계·운영 문서 (ERD/API/인증/Jira/브랜치 등)
├── planning/               # 기획 자료 (기획서·ERD·UCD·화면 시안·아키텍처)
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

데이터(종목 마스터·시세·재무)는 팀 공유 DB 덤프(`jumanchu_db_*.sql`)를 복원하거나, 적재 명령을 직접 실행해 채웁니다 — 절차는 [docs/followup.md](docs/followup.md) §4 참고.

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
| [docs/ERD.md](docs/ERD.md) | DB 스키마 (진실의 원천) |
| [docs/API_명세_초안.md](docs/API_명세_초안.md) · [docs/API_스키마_v1.5.md](docs/API_스키마_v1.5.md) | API 모듈·스키마 |
| [docs/인증_권한_정책.md](docs/인증_권한_정책.md) | JWT / 권한 정책 |
| [docs/DART_COLUMN.md](docs/DART_COLUMN.md) | 재무 지표 컬럼 사전 |
| [docs/USER_STORIES.md](docs/USER_STORIES.md) | 유저 스토리 / 인수 조건 |
| [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) · [docs/followup.md](docs/followup.md) | 로컬 셋업 / 작업 인수인계 |

## 팀

| 이름 | 역할 |
|---|---|
| 강재민 | Backend — Django(모델/뷰/URL/마이그레이션), 외부 API 연동, CI/CD |
| 정율 | Algorithm — 추천 도메인 기획 + 순수 Python 추천 알고리즘 |
| 송호영 | Frontend — Vue.js 전반 |
