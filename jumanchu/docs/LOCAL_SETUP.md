# 로컬 개발환경 셋업 가이드

> 새 PC에서 처음 클론하거나, 팀원이 합류할 때 이 순서대로 따라하면 됩니다.
> **현재 구성**: DB(PostgreSQL)는 **Neon**, Redis는 **Upstash** — 둘 다 **클라우드 공유**.
> 그래서 각자 로컬에선 **Django·Vue만** 띄우면 되고, **Docker는 필요 없습니다.**
> (완전 로컬(Docker)로 돌리고 싶으면 맨 아래 [대안 섹션](#대안-완전-로컬-구성--docker로-dbredis-직접-띄우기) 참고.)
> 브랜치/커밋 규칙은 [BRANCH_STRATEGY.md](./BRANCH_STRATEGY.md), Git 초기 셋업은 [GITHUB_SETUP.md](./GITHUB_SETUP.md) 참고.

---

## 0. 사전 설치

| 항목 | 버전 / 비고 |
|---|---|
| Git | https://git-scm.com/download/win |
| Python | **3.12** 권장 (`backend/.python-version`). 기존 팀 venv는 3.11.9로도 동작 |
| Node.js | **20.19+ 또는 22.12+** (`package.json` engines, Vite 8 호환) |

> Docker는 기본 경로(클라우드 공유)에선 **안 깔아도 됩니다.** 완전 로컬로 돌릴 때만 필요.

확인:
```powershell
git --version
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

`.env`는 깃에 안 올라갑니다(`.gitignore` 제외) → **직접 만들어야 하고, 실제 값은 팀에서 받아야** 합니다.
프로젝트 루트(`docker-compose.yml`이 있는 폴더)에 `.env`를 만들고 아래 형태로 채우세요:

```bash
# === Django ===
SECRET_KEY=아무-긴-랜덤-문자열
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# === DB — Neon (클라우드 공유) ===
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=<팀에서 받기>
DB_HOST=<...>.aws.neon.tech        # Neon pooler 엔드포인트 (팀 .env 그대로)
DB_PORT=5432
DB_SSLMODE=require                  # Neon은 require (로컬 Postgres면 prefer)

# === Redis — Upstash (클라우드 공유) ===
# settings.py가 REDIS_URL을 우선 사용. 이거 하나면 됨.
REDIS_URL="rediss://default:<팀에서 받기>@<...>.upstash.io:6379"

# === 외부 API 키 (팀 공유) ===
KIS_APP_KEY=<팀에서 받기>
KIS_APP_SECRET=<팀에서 받기>
KIS_ENV=prod                        # 시세 조회는 prod(실서버)
DART_API_KEY=<팀에서 받기>
NAVER_CLIENT_ID=<팀에서 받기>
NAVER_CLIENT_SECRET=<팀에서 받기>
GMS_API_KEY=<팀에서 받기>
GNews_API_KEY=<팀에서 받기>

# === Frontend ===
VITE_API_BASE_URL=http://localhost:8000/api/v1   # 생략 가능(아래 4번 프록시로 폴백)
```

> 💡 가장 쉬운 방법: **팀원의 `.env`를 통째로 복사**해 쓰는 것. (DB/Redis/키 값이 모두 거기 있음)
>
> ⚠️ **시크릿 공유 주의**: `DB_PASSWORD`, `REDIS_URL`, `KIS_APP_SECRET` 등은 카톡/슬랙/이메일 본문이나 깃에 그대로 붙이지 마세요. USB나 1Password/Bitwarden 같은 비밀 관리 도구로 전달하는 게 안전합니다.

---

## 3. Backend (Django) 셋업 + 실행

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate           # 아래 ⚠️ 먼저 읽기
python manage.py runserver         # http://localhost:8000
```

> ⚠️ **공유 DB라 `migrate`에 주의.** Neon엔 이미 스키마·데이터가 들어 있어서, 모델을 안 건드렸다면 `migrate`는 보통 *"No migrations to apply"*로 끝납니다. 이게 정상이에요. **본인이 모델을 바꾼 게 아니면 `makemigrations`를 돌리지 마세요** — 공유 스키마가 어긋납니다. (규칙: 마이그레이션은 한 사람만 → [CLAUDE.md](../CLAUDE.md))
>
> ⚠️ `runserver` 시 `stocks` 앱이 인기랭킹 워머(`warm_loop`)를 백그라운드 데몬으로 자동 기동합니다(KIS 시세를 Upstash 캐시에 워밍). 로그가 거슬리면 `$env:DISABLE_WARMER=1; python manage.py runserver` 로 끄세요.

Redis 연결만 빠르게 확인하고 싶으면:
```powershell
python manage.py shell -c "from django.core.cache import cache; cache.set('hc','ok',30); print('REDIS:', cache.get('hc'))"
# REDIS: ok 가 나오면 Upstash 연결 정상
```

> **데이터 적재(run_batch) 불필요**: Neon에 종목·시세가 이미 있으니 새 PC에서 따로 채울 필요 없습니다. (배치는 데이터 *갱신*용 — [BATCH_SCHEDULING.md](./BATCH_SCHEDULING.md))

---

## 4. Frontend (Vue) 셋업 + 실행

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173
```

> 프론트는 별도 `.env`가 필요 없습니다. `vite.config.js`가 `/api` 요청을 `http://127.0.0.1:8000`(로컬 Django)로 프록시하고, 백엔드가 공유 Neon·Upstash를 바라봅니다.

---

## 5. 접속 확인

- 화면: http://localhost:5173
- API 문서(Swagger): http://localhost:8000/api/v1/schema/swagger-ui/
- 관리자: http://localhost:8000/admin/

`npm install` → `npm run dev` + `runserver` 두 개만 떠 있으면 끝. (DB/Redis는 클라우드라 항상 켜져 있음)

---

## 자주 쓰는 명령 (셋업 끝난 뒤)

```powershell
# Backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
python manage.py test
python manage.py createsuperuser

# Frontend
npm run dev
npm run build && npm run preview
```

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `KeyError: 'DB_NAME'` | `.env`가 없거나 위치가 틀림 — `docker-compose.yml`과 같은 폴더에 둬야 함 |
| `psycopg.OperationalError ... could not connect` (Neon) | 인터넷 끊김, `DB_SSLMODE=require` 누락, 또는 Neon 자격증명 오타 — 팀 `.env` 값과 대조 |
| `redis ... ConnectionError` | `.env`의 `REDIS_URL`이 없거나 오타. `rediss://`(TLS)인지 확인. 위 3번 shell 명령으로 점검 |
| `.\venv\Scripts\Activate.ps1` 실행 정책 오류 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 한 번 실행 |
| 마이그레이션이 꼬임 / 남의 작업이 깨짐 | 공유 DB에 임의로 `makemigrations`/`migrate` 함 — 모델 변경자 한 명만 수행 |

---

## (대안) 완전 로컬 구성 — Docker로 DB·Redis 직접 띄우기

클라우드 공유가 부담되거나(예: 마이그레이션 실험), 오프라인/격리 환경이 필요할 때만.

**1) Docker Desktop 설치·실행** (WSL2 백엔드 권장)

**2) `.env`를 로컬용으로 전환**
```bash
# DB — 로컬 Postgres
DB_NAME=jumanchu
DB_USER=jumanchu
DB_PASSWORD=아무거나
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=prefer

# Redis — 로컬 (REDIS_URL을 비우면 아래 HOST/PORT 폴백)
REDIS_URL=
REDIS_HOST=localhost
REDIS_PORT=6379
```
> `REDIS_PORT`를 빼먹으면 컨테이너가 랜덤 포트로 떠서 연결이 안 됩니다 — 꼭 넣으세요.

**3) 컨테이너 기동 + 마이그레이션**
```powershell
docker compose up -d        # db + redis
cd backend
python manage.py migrate
```

**4) 데이터 채우기** — 로컬 DB는 비어 있으니 둘 중 하나:
- Neon 덤프를 복원: `Get-Content dump.sql | docker compose exec -T db psql -U jumanchu -d jumanchu`
- 또는 배치 실행: `python manage.py run_batch weekly` → `daily` → `hourly` (KIS·DART 키 필요, 무거움)

**자주 쓰는 컨테이너 명령**
```powershell
docker compose up -d         # 켜기
docker compose down          # 끄기 (데이터는 named volume 보존)
docker compose down -v       # ⚠️ 데이터까지 삭제
```
