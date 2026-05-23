# 브랜치 전략 (Branch Strategy)

> 2~3인 SSAFY 팀을 위한 가벼운 Git Flow 변형.

## 1. 영구 브랜치

| 브랜치 | 역할 | push 권한 |
|---|---|---|
| `main` | 발표/시연용 안정 버전. 항상 동작해야 함. | PR 머지만 |
| `develop` | 통합 브랜치. 모든 feature가 여기로 머지됨. | PR 머지만 |

## 2. 작업 브랜치 (Short-lived)

| 접두어 | 용도 | 분기 위치 | 머지 대상 |
|---|---|---|---|
| `feature/` | 새 기능 (Story 단위) | `develop` | `develop` |
| `fix/` | 버그 수정 | `develop` | `develop` |
| `hotfix/` | 시연 직전 긴급 수정 | `main` | `main` + `develop` |
| `chore/` | 설정, 문서, 의존성 업데이트 | `develop` | `develop` |
| `refactor/` | 동작 변경 없는 리팩토링 | `develop` | `develop` |

## 3. 브랜치 명명 규칙

```
<type>/<JIRA-KEY>-<짧은-설명-kebab-case>
```

**예시**
```
feature/SCRUM-2-signup-api
fix/SCRUM-21-portfolio-cache
chore/SCRUM-3-ci-pipeline
```

규칙:
- Jira 이슈 키 필수 (없으면 만들고 시작)
- 설명은 영문 kebab-case, 4~6단어 이내
- 한 브랜치 = 한 Story 또는 Sub-task

## 4. 커밋 메시지 컨벤션

```
<type>(<scope>): <subject>  [JIRA-KEY]

<body (선택)>

<footer (선택)>
```

**type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

**예시**
```
feat(auth): 이메일/비밀번호 회원가입 API 추가  [SCRUM-4]

- 이메일 중복 체크 / 비밀번호 해시 저장
- 비밀번호 복잡도 검증 (8자 이상 + 영문/숫자)

Closes SCRUM-4
```

> Jira 이슈 키를 본문이나 브랜치명에 포함하면 GitHub for Jira 연동 시 자동으로 이슈와 PR/커밋이 연결됩니다.

## 5. PR 워크플로우

1. Jira에서 이슈를 **In Progress**로 옮긴다.
2. `develop`에서 `feature/SCRUM-XX-...` 브랜치를 만든다.
3. 작업 후 푸시 → PR 생성 (PR 템플릿 자동 적용).
4. Jira 이슈를 **In Review**로 옮기고 PR 링크를 코멘트에 단다.
5. 최소 1명 리뷰 + CI 통과 후 **Squash and merge**.
6. 머지되면 Jira 이슈를 **Done**으로 옮긴다 (DoD 체크리스트 통과).
7. 머지된 브랜치는 삭제한다.

## 6. main 머지 시점

- 스프린트 종료 시 `develop` → `main` PR
- 시연/발표 D-Day 직전에만 추가 머지
- main 머지는 태그(`v0.1.0`, `v0.2.0`...)와 함께

## 7. 보호 규칙 (GitHub Branch Protection 권장 설정)

`main` / `develop` 공통:
- [ ] PR 없이 직접 push 금지
- [ ] 최소 1명 리뷰 승인 필요
- [ ] CI 통과 필수
- [ ] 머지 전 최신 base 강제 (Require branches to be up to date)
- [ ] 자기 자신 리뷰 승인 금지

> 2인 팀이라 1명 승인이 부담이면 `develop`만 우선 보호하고 `main`은 수동 운영해도 됨.
