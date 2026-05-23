# 주만추 (Jumanchu) — Claude Code Context

> Claude Code는 모든 세션 시작 시 이 파일을 자동 로드합니다.
> 프로젝트 특화 컨텍스트는 위 섹션, 공통 LLM 행동 가이드는 아래 섹션입니다.

## 프로젝트 한 줄 소개

**주만추(자연스러운 주식과의 만남 추구)** — 건강한 투자 습관을 돕는 주린이용 주식 투자 서비스.
SSAFY 광주 1반 6조, 약 6주 (2026-05-11 ~ 2026-06-25, 발표 6/25).

## 기술 스택

- **Backend**: Django, Django REST Framework, PostgreSQL(예정)
- **Frontend**: Vue.js, Pinia, Vite
- **외부 API**: KIS / pykrx / yfinance / DART OpenAPI / NewsData·Gnews / OpenAI
- **CI/CD**: GitHub Actions (`.github/workflows/ci.yml`)
- **이슈 관리**: Jira (`SCRUM` 프로젝트, `SCRUM-NN` 키 사용)

## 팀 분담 (3인)

- **강재민 (BE)** — Django 코드 전부(모델/뷰/URL/마이그레이션), 외부 API 연동, 추천 함수 호출해 REST로 노출, CI/CD
- **정율 (Algo)** — 추천 도메인 기획 + 순수 Python 알고리즘 함수만 (Django는 안 짬)
- **송호영 (FE)** — Vue.js 코드 전부

자세한 매트릭스: `docs/USER_STORIES.md` 컴포넌트 컬럼 / `docs/KICKOFF.md` 3.1.

## 디렉토리 구조

```
jumanchu/
├── backend/              # Django (생성 예정)
├── frontend/             # Vue (생성 예정)
├── docs/                 # 모든 문서 (USER_STORIES, BRANCH_STRATEGY, JIRA_*, KICKOFF 등)
├── planning/             # 기획 자료 (기획서 docx, ERD, UCD, 화면 시안)
├── .github/              # PR/이슈 템플릿, CI 워크플로우
└── CLAUDE.md             # 이 파일
```

## 자주 쓰는 명령

```bash
# Backend
cd backend && python manage.py runserver
python manage.py makemigrations && python manage.py migrate
python manage.py test

# Frontend
cd frontend && npm run dev
npm run build && npm test
```

## 컨벤션

### Git
- **브랜치**: `<type>/<JIRA-KEY>-<짧은-설명>` 예) `feature/SCRUM-23-django-setup`
- **커밋**: `<type>(<scope>): <subject>  [JIRA-KEY]` 예) `feat(auth): 회원가입 API 추가  [SCRUM-55]`
- **PR**: `develop` 대상, CI 통과 + 1명 이상 리뷰 → Squash merge
- `main`/`develop` 직접 push 금지
- 자세히 → `docs/BRANCH_STRATEGY.md`

### Jira
- **모든 커밋·PR·브랜치명에 `[SCRUM-NN]` 포함** (GitHub for Jira 자동 연결)
- 작업 시작 = "진행 중", PR 올리면 = "검토 중", 머지 후 = "완료"
- 라벨: `backend` / `algo` / `frontend` + 도메인(`auth`, `stock-data`, `recommend` 등)
- 자세히 → `docs/JIRA_관리구조.md`

### 코드
- **Python**: PEP 8, type hint 권장, docstring(공개 API)
- **JS/Vue**: ESLint + Prettier, Composition API, `<script setup>`
- **테스트**: 새 API/Vue 컴포넌트에 최소 1개 단위 테스트
- **모델 변경 = 마이그레이션 같이 커밋**

## BE ↔ Algo 인터페이스 (중요)

추천 알고리즘 함수는 정율이 만들고, BE가 view에서 호출. **코드 작성 전 시그니처 합의 필수**.

```python
# Algo가 만드는 함수
def recommend_by_trending_news(user_id: int, limit: int = 10) -> list[StockRecommendation]:
    ...

# BE가 호출
class TrendingRecommendView(APIView):
    def get(self, request):
        recs = recommend_by_trending_news(request.user.id, limit=10)
        return Response([r.to_dict() for r in recs])
```

## 충돌 방지 방침

### Git 머지 충돌
- **작업 시작 전 `git pull origin develop`** 필수
- 한 브랜치 = 한 Story 또는 Sub-task (작게 자르기)
- PR은 24시간 안에 머지 (장수명 브랜치 금지)
- 브랜치가 develop과 24시간 이상 분기됐으면 **rebase**
- 같은 파일을 동시 수정할 가능성이 보이면 Slack에 미리 공지

### 인터페이스 충돌 (BE↔Algo↔FE)
- **코드 짜기 전에 시그니처 합의** (Jira 이슈 코멘트 또는 페어 세션 15분)
- API 명세 변경은 BE가 PR로 먼저 + Slack 공지
- 반환 타입은 dataclass/TypedDict 같이 **명시적 타입** 사용
- Algo는 더미(stub) 함수를 먼저 제공 → BE/FE는 그걸로 통합 시작

### 작업 영역 충돌
- 작업 시작 전 Jira에서 **담당자 본인 지정 + "진행 중" 이동** — 다른 사람은 보고 같은 카드 안 잡음
- 같은 도메인을 둘이 동시에 잡지 않기 — 도메인 owner 우선
- 도메인 owner가 모호한 작업은 Slack에서 먼저 합의

### Django 마이그레이션 충돌
- 마이그레이션 파일은 **한 사람만 만든다** — 다른 사람은 `git pull` 후 `migrate`만
- 두 사람이 동시에 `makemigrations` 했다면 → 나중 사람이 자기 파일 삭제 후 재생성
- **모델 변경 + 마이그레이션 = 같은 PR**에 묶기

### 컨벤션 충돌 방지
- 포맷터를 CI에서 강제 (Python: black, JS: prettier)
- 사람 손으로 스타일 다투지 않기 — 포맷터가 결정

## 주요 참고 문서 (작업 전 읽기)

| 작업 | 먼저 봐야 할 문서 |
|---|---|
| 새 API 만들기 | `docs/USER_STORIES.md` (해당 US-NN) + `planning/모델_서비스flow/erd.png` |
| 새 Vue 화면 만들기 | `docs/USER_STORIES.md` + `planning/화면예시/` |
| 추천 알고리즘 작업 | `docs/USER_STORIES.md` US-04/05/10 (기획은 정율 책임) |
| DB 모델 변경 | `planning/모델_서비스flow/erd.png` 먼저 확인 |
| PR 만들기 | `docs/BRANCH_STRATEGY.md` |
| Jira 이슈 만들기 | `docs/JIRA_관리구조.md` |

## Claude Code 프롬프트 패턴

작업 지시 시 **"산출 목표 + 참고 문서 + Jira 키"** 세트로:

```
docs/USER_STORIES.md US-02(회원가입)을 보고
Django 회원가입 API를 구현해줘. 인수 조건을 모두 충족해야 해.
ERD는 planning/모델_서비스flow/erd.png 참고.
커밋 메시지에 [SCRUM-2] 넣어줘.
```

---

# 일반 LLM 행동 가이드 (모든 프로젝트 공통)

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
