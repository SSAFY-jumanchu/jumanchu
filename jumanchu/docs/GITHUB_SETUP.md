# GitHub 연동 가이드

> Cowork 환경의 권한 제약으로 git init과 원격 push는 직접 실행해야 합니다.
> 아래 순서대로 한 번만 따라하면 됩니다.

---

## 0. 사전 준비

- Git 설치 (https://git-scm.com/download/win)
- GitHub 계정 + Personal Access Token 또는 SSH 키 등록

확인:
```powershell
git --version
```

---

## 1. 로컬 git 저장소 정리 + 초기화

PowerShell 또는 Git Bash에서:

```powershell
cd C:\Users\SSAFY\Desktop\jaemin-git\Project\project-jaemin\ssafy-pjt\jumanchu\jumanchu

# 이전 시도로 남은 빈 .git 폴더 제거
Remove-Item -Recurse -Force .git -ErrorAction SilentlyContinue

# git 초기화 (기본 브랜치를 main 으로)
git init -b main

# 사용자 정보 설정 (전역으로 이미 했다면 생략 가능)
git config user.name "강재민"
git config user.email "jmkang21212@gmail.com"
```

> Git Bash 쓰는 경우 `Remove-Item ...` 대신 `rm -rf .git` 사용.

---

## 2. 첫 커밋

```powershell
# 어떤 파일이 추적될지 미리 확인
git status

# .gitignore 가 의도대로 동작하는지 확인
git check-ignore -v __pycache__ node_modules .env 2>$null

# 전체 추가 후 첫 커밋
git add .
git commit -m "chore: 프로젝트 초기 세팅 (gitignore, PR/이슈 템플릿, CI, 문서)  [SCRUM-5]"
```

---

## 3. GitHub 원격 저장소 만들기

GitHub 웹에서:

1. https://github.com/new 접속
2. Repository name: `jumanchu` (또는 팀 합의 이름)
3. **Private** 선택 권장 (SSAFY 자율 PJT)
4. **README / .gitignore / license 모두 체크 해제** (이미 로컬에 있음)
5. Create repository

생성 직후 페이지에 `git remote add ...` 명령이 나옵니다.

---

## 4. 원격 연결 + 첫 push

GitHub가 알려준 URL을 그대로 복사해서 사용:

```powershell
# HTTPS 방식 (PAT 사용)
git remote add origin https://github.com/<YOUR_ORG_OR_USER>/jumanchu.git

# 또는 SSH 방식
# git remote add origin git@github.com:<YOUR_ORG_OR_USER>/jumanchu.git

git push -u origin main
```

처음 push 시 인증 창이 뜨면 GitHub PAT를 비밀번호 자리에 붙여넣으세요.

---

## 5. develop 브랜치 만들기

```powershell
git switch -c develop
git push -u origin develop
```

이후 모든 feature 브랜치는 `develop`에서 분기합니다 (`BRANCH_STRATEGY.md` 참고).

---

## 6. 브랜치 보호 규칙 적용 (GitHub 웹)

`Settings → Branches → Add rule`

`main`, `develop` 각각에:
- [x] Require a pull request before merging
- [x] Require approvals (1명)
- [x] Require status checks to pass before merging
  - `Backend (Django)` / `Frontend (Vue.js)` 체크 (CI가 한 번 돌고 나면 옵션에 뜸)
- [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings

> 2인 팀이라 1명 승인이 부담이면 `develop` 만 우선 보호하고 `main` 은 수동 운영해도 OK.

---

## 7. Jira ↔ GitHub 연동 (선택)

GitHub for Jira 앱을 설치하면 커밋·PR이 Jira 이슈에 자동으로 연결됩니다.

1. https://github.com/marketplace/jira-software-github 에서 Install
2. 본인의 Jira 사이트(`jmkang21212-1778486604767.atlassian.net`) 선택
3. 연결할 GitHub repo 선택

연동 후엔:
- 커밋 메시지·브랜치명·PR 제목에 `SCRUM-XX` 가 있으면 자동으로 해당 이슈에 링크
- PR을 열면 Jira 이슈가 자동으로 **In Review** 로 이동 (워크플로우 설정 시)
- `Closes SCRUM-XX` 포함된 PR 머지 시 자동으로 **Done** 이동

---

## 8. 다음 단계

- [ ] 팀원 GitHub 계정 Collaborator 초대
- [ ] 첫 feature 브랜치 만들어보기:
  ```
  git switch develop
  git switch -c feature/SCRUM-1-erd-finalize
  ```
- [ ] PR 한 번 올려서 템플릿/CI 동작 확인
