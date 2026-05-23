# 로컬 개발환경 셋업 가이드

> 새 PC에서 처음 클론해 받은 뒤 — 또는 팀원이 합류해 처음 셋업할 때 — 이 순서대로 따라하면 됩니다.
> 브랜치/커밋 규칙은 [BRANCH_STRATEGY.md](./BRANCH_STRATEGY.md), Git 초기 셋업은 [GITHUB_SETUP.md](./GITHUB_SETUP.md) 참고.

---

## 0. 사전 설치

| 항목 | 버전 / 비고 |
|---|---|
| Git | https://git-scm.com/download/win |
| Docker Desktop | 실행 중이어야 함. WSL2 백엔드 권장 |
| Python | **3.11.x** (현재 venv 기준) |
| Node.js | **LTS 22.x** 권장 (Vite 8 호환) |

확인:
```powershell
git --version
docker --version
python --version
node --version
```

---

## 1. 코드 받기

```powershell
git clone <repo-url> jumanchu
cd jumanchu
```

---

## 2. `.env` 파일 만들기 (가장 중요)

`.env`는 깃에 안 올라갑니다 (`.gitignore`에 제외). 직접 만들어야 합니다.

```powershell
Copy-Item .env.example .env
```

그 다음 `.env`를 열어서 **각자 발급받은 값**으로 채워야 할 항목:

| 변수 | 어디서 받나 / 어떻게 설정 |
|---|---|
| `SECRET_KEY` | Django용. 아무 긴 랜덤 문자열 (50자 이상) |
| `KIS_APP_KEY`, `KIS_APP_SECRET` | [한국투자증권 KIS Open API](https://apiportal.koreainvestment.com/) 신청 후 발급 |
| `KIS_ACCOUNT_NO`, `KIS_ACCOUNT_PRODUCT_CODE` | KIS 모의투자 계좌 번호 앞 8자리 / 상품코드(보통 `01`) |
| `KIS_BASE_URL` | 모의: `https://openapivts.koreainvestment.com:29443` / 실전: `https://openapi.koreainvestment.com:9443` |
| `KIS_ENV` | `virtual` 또는 `real` |
| `DART_API_KEY` | [DART OpenAPI](https://opendart.fss.or.kr/) 신청 |
| `OPENAI_API_KEY` | (사용 시) OpenAI 콘솔에서 발급 |
| `GNews_API_KEY`, `BIGKINDS_API_KEY` | (사용 시) 각 서비스 콘솔 |

DB 관련 (`DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT`)는 `.env.example` 기본값을 그대로 두면 됩니다.

> ⚠️ **시크릿 공유 주의**: `KIS_APP_SECRET`, `DART_API_KEY` 등은 카톡/슬랙/이메일 본문에 그대로 붙이지 마세요. 본인이 다른 본인 PC에서 쓰는 경우라면 USB나 1Password/Bitwarden 같은 비밀 관리 도구로 옮기는 게 안전합니다.

---

## 3. Backend (Django) 셋업

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> macOS/Linux는 `source venv/bin/activate`.

---

## 4. DB 컨테이너 띄우기 + 마이그레이션

프로젝트 루트(`jumanchu/`)에서:

```powershell
docker compose up -d db
```

→ `docker compose ps`에서 `jumanchu-pg`가 `Up (healthy)`로 뜨면 OK (10초 안에).

이어서 마이그레이션:

```powershell
cd backend
.\venv\Scripts\Activate.ps1   # 이미 활성화된 상태면 생략
python manage.py migrate
```

검증:
```powershell
python manage.py showmigrations
# 모든 항목 [X] 로 표시되면 성공

# 또는 직접 테이블 확인
docker compose exec db psql -U jumanchu -d jumanchu -c "\dt"
```

`auth_user`, `django_session`, `django_migrations` 등이 보이면 정상.

---

## 5. Frontend (Vue) 셋업

```powershell
cd frontend
npm install
npm run dev
```

브라우저에서 Vite가 띄운 주소(보통 `http://localhost:5173`) 접속.

---

## 6. Backend 서버 실행

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

기본 `http://localhost:8000` 에서 동작.

---

## 자주 쓰는 명령 (셋업 끝난 뒤)

```powershell
# DB 컨테이너
docker compose up -d db          # 켜기
docker compose down              # 끄기 (데이터는 named volume에 보존)
docker compose down -v           # ⚠️ 데이터까지 삭제

# Backend
python manage.py makemigrations && python manage.py migrate
python manage.py test
python manage.py createsuperuser

# Frontend
npm run dev
npm run build && npm run preview
```

---

## 데이터 옮기기 (선택)

기존 PC의 DB 내용을 새 PC로 그대로 가져가고 싶을 때만:

**기존 PC에서 백업**
```powershell
docker compose exec -T db pg_dump -U jumanchu jumanchu > dump.sql
```

**새 PC에서 복원** (`docker compose up -d db` 직후)
```powershell
Get-Content dump.sql | docker compose exec -T db psql -U jumanchu -d jumanchu
```

> Django 기본 테이블만 있는 초기 상태라면 그냥 `migrate`를 다시 돌리는 게 훨씬 간단합니다.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `docker compose up` 했는데 `Cannot connect to the Docker daemon` | Docker Desktop이 안 켜져 있음 |
| `python manage.py migrate` 시 `KeyError: 'DB_NAME'` | `.env`가 없거나 DB 변수가 빠짐 — `.env.example` 다시 확인 |
| `psycopg.OperationalError: connection refused` | 컨테이너가 아직 안 떴거나 죽음 — `docker compose ps`로 상태 확인 |
| `.\venv\Scripts\Activate.ps1` 시 실행 정책 오류 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 한 번 실행 |
| 포트 5432 충돌 | 다른 PostgreSQL이 떠 있음 — 끄거나, `.env`의 `DB_PORT`를 5433 등으로 바꾸고 `docker compose up -d db` 다시 |
