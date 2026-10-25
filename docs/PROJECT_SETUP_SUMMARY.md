# 프로젝트 셋업 결과 요약

> 작성일: 2026-05-13
> Jira 사이트: https://jmkang21212-1778486604767.atlassian.net/jira/software/projects/SCRUM/boards/

---

## 1. 생성된 파일 (로컬)

| 파일 | 용도 |
|---|---|
| `.gitignore` | Python/Django/Vue/IDE/OS 등 추적 제외 규칙 |
| `.gitattributes` | 줄바꿈/바이너리 정책 (Windows 팀 권장) |
| `.env.example` | 환경변수 템플릿. 실제 `.env`는 절대 커밋 금지 |
| `BRANCH_STRATEGY.md` | 영구 브랜치(`main`/`develop`) + 작업 브랜치 명명 규칙 + 커밋 컨벤션 |
| `GITHUB_SETUP.md` | GitHub 원격 연결을 직접 수행하기 위한 가이드 |
| `.github/PULL_REQUEST_TEMPLATE.md` | PR 자동 템플릿 (Jira 키 + DoD 체크리스트) |
| `.github/ISSUE_TEMPLATE/bug_report.md` | GitHub 이슈 — 버그 |
| `.github/ISSUE_TEMPLATE/feature_request.md` | GitHub 이슈 — 기능 요청 |
| `.github/workflows/ci.yml` | Backend(Django) + Frontend(Vue) CI 골격 — `backend/`, `frontend/` 폴더 생기면 자동 동작 |

---

## 2. Jira 이슈 구조

**Epic 체계: Phase로 통일** (도메인 Epic 9개는 일단 유지 → 필요 시 archive)

```
🟦 SCRUM-14  Phase 1. 기획·설계
   ├ [1.1] 문제 정의 / 사용자 스토리       SCRUM-19  + 1.1.1~1.1.4 (SCRUM-37~40)
   ├ [1.2] ERD 설계                       SCRUM-20  + 1.2.1~1.2.4 (SCRUM-41~44)
   ├ [1.3] API 명세서 작성                 SCRUM-21  + 1.3.1~1.3.4 (SCRUM-45~48)
   └ [1.4] 와이어프레임 / 화면 설계         SCRUM-22  + 1.4.1~1.4.4 (SCRUM-49~52)

🟩 SCRUM-15  Phase 2. 백엔드 개발
   ├ [2.1] Django 세팅 + User 인증         SCRUM-23  + 2.1.1~2.1.4 (SCRUM-53~56)
   ├ [2.2] 종목 조회 API (KIS+DART)        SCRUM-24  + 2.2.1~2.2.5 (SCRUM-57~61)
   ├ [2.3] 종목 추천 로직                   SCRUM-25  + 2.3.1~2.3.5 (SCRUM-62~66)
   └ [2.4] 커뮤니티/일기/워치리스트 API     SCRUM-26  + 2.4.1~2.4.4 (SCRUM-67~70)

🟧 SCRUM-16  Phase 3. 프론트엔드 개발
   ├ [3.1] Vue 세팅 + 인증/홈              SCRUM-27  + 3.1.1~3.1.4 (SCRUM-71~74)
   ├ [3.2] 종목 목록/상세                   SCRUM-28  + 3.2.1~3.2.4 (SCRUM-75~78)
   ├ [3.3] 추천 스와이프 UI                 SCRUM-29  + 3.3.1~3.3.4 (SCRUM-79~82)
   └ [3.4] 커뮤니티/일기장/프로필           SCRUM-30  + 3.4.1~3.4.4 (SCRUM-83~86)

🟪 SCRUM-17  Phase 4. 통합·테스트
   ├ [4.1] FE↔BE 통합                     SCRUM-31  + 4.1.1~4.1.4 (SCRUM-87~90)
   ├ [4.2] 시나리오 통합 테스트             SCRUM-32  + 4.2.1~4.2.4 (SCRUM-91~94)
   └ [4.3] 버그픽스/리팩토링/성능           SCRUM-33  + 4.3.1~4.3.4 (SCRUM-95~98)

🟥 SCRUM-18  Phase 5. 발표 준비
   ├ [5.1] 발표 자료/시연 영상              SCRUM-34  + 5.1.1~5.1.4 (SCRUM-99~102)
   ├ [5.2] 리허설                          SCRUM-35  + 5.2.1~5.2.4 (SCRUM-103~106)
   └ [5.3] 최종 발표 (D-Day)               SCRUM-36  + 5.3.1~5.3.4 (SCRUM-107~110)
```

**집계**
- Phase Epic: 5개 (SCRUM-14, 15 기존 / SCRUM-16, 17, 18 신규)
- Story(작업): 18개 (SCRUM-19~36)
- Subtask: 74개 (SCRUM-37~110)
- 신규 등록 총 95개

**기존(중첩) Epic — 처리 보류**
- 도메인 Epic 9개: SCRUM-5~13 (`[기반]`, `[인증]`, `[종목]`, `[포트폴리오]`, `[추천]`×2, `[커뮤니티]`, `[재무]`, `[일기]`)
- 기존 작업/스토리: SCRUM-1(ERD 작업), SCRUM-2(회원가입 스토리), SCRUM-3(CI/CD Feature), SCRUM-4(BE Subtask)

> 사용자 결정 필요: 도메인 Epic 9개를 **archive**하거나 그대로 두기. archive는 Jira UI에서 한 번에 가능.

---

## 3. 사용자가 직접 해야 할 일 (순서대로)

### 3.1 GitHub 원격 연결 (필수)

`GITHUB_SETUP.md` 참고. 핵심 명령:

```powershell
cd C:\Users\SSAFY\Desktop\jaemin-git\Project\project-jaemin\ssafy-pjt\jumanchu\jumanchu
Remove-Item -Recurse -Force .git -ErrorAction SilentlyContinue
git init -b main
git add .
git commit -m "chore: 프로젝트 초기 세팅 (gitignore, PR/이슈 템플릿, CI, 문서)  [SCRUM-5]"
# GitHub에서 빈 repo 만든 뒤
git remote add origin https://github.com/<USER>/jumanchu.git
git push -u origin main
git switch -c develop
git push -u origin develop
```

### 3.2 GitHub for Jira 연동 (커밋·PR ↔ Jira 자동 연결)

`GITHUB_SETUP.md` 7번 섹션 참조. 설치만 하면 됨.

### 3.3 Jira 정리 (선택)

도메인 Epic 9개(SCRUM-5~13) archive를 권장:
1. 해당 Epic 열기 → 우측 상단 `⋯` → **Archive**
2. 또는 단순히 description 맨 위에 `[DEPRECATED]` 표기 후 유지

기존 SCRUM-1, 2, 3, 4의 Parent 재설정(선택):
- SCRUM-1 → Parent를 SCRUM-20(1.2)로 변경
- SCRUM-2 → Parent를 SCRUM-23(2.1)로 변경 (Subtask SCRUM-4도 자동 따라감)
- SCRUM-3 → Parent를 SCRUM-15(Phase 2) 또는 SCRUM-23(2.1)로 변경

### 3.4 첫 스프린트 시작

1. Jira 백로그 화면 → Sprint 1 만들기
2. 1주차 작업 드래그 (예: 1.1, 1.2, 1.3, 1.4 Story들 = Phase 1 전체)
3. Sprint 시작
4. 매일 보드 열고 Subtask 드래그로 진행 상태 갱신

---

## 4. 커밋 메시지 예시

```
feat(auth): Custom User 모델 + 회원가입 API 추가  [SCRUM-55]

- accounts/models.py: AbstractUser 확장
- accounts/views.py: SignupView
- 이메일 형식 / 비밀번호 복잡도 검증

Closes SCRUM-55
```

GitHub for Jira 앱 설치 후엔 `[SCRUM-55]`만 있어도 자동 링크됩니다.

---

## 5. 도움이 될 만한 Jira JQL

| 목적 | JQL |
|---|---|
| 내 담당 진행 중 | `project = SCRUM AND assignee = currentUser() AND status = "In Progress"` |
| Phase 1 진행 상황 | `project = SCRUM AND parent = SCRUM-14` |
| 이번 스프린트 + 미할당 | `project = SCRUM AND sprint in openSprints() AND assignee is EMPTY` |
| 블록된 작업 | `project = SCRUM AND status = Blocked` |
