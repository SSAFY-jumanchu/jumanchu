# 📚 주만추 문서

> 프로젝트의 모든 가이드 문서가 여기에 있습니다.
> 처음 보는 분은 **PROJECT_SETUP_SUMMARY.md** 부터 읽으세요.

---

## 🚀 셋업 / 협업 규칙

| 문서 | 언제 보나 |
|---|---|
| [PROJECT_SETUP_SUMMARY.md](./PROJECT_SETUP_SUMMARY.md) | **가장 먼저.** 지금 어디까지 셋업됐는지, 내가 뭘 해야 하는지 한 페이지 요약 |
| [LOCAL_SETUP.md](./LOCAL_SETUP.md) | **새 PC에서 처음 클론할 때.** Docker/Python/Node 설치 → `.env` → DB → migrate → 서버 실행 |
| [GITHUB_SETUP.md](./GITHUB_SETUP.md) | 로컬 git 초기화 → GitHub 원격 연결 → 첫 push 까지 단계별 명령 |
| [BRANCH_STRATEGY.md](./BRANCH_STRATEGY.md) | 브랜치 명명 규칙 + 커밋 컨벤션 + PR 워크플로우 |

---

## 📋 Jira (업무 관리)

처음 → 매일 → 한눈에 보기 순서로 읽으면 됩니다.

| 문서 | 언제 보나 |
|---|---|
| [JIRA_시작가이드.md](./JIRA_시작가이드.md) | **처음.** 5분 컷 — 어디 보고 뭘 누르면 되는지 |
| [JIRA_관리구조.md](./JIRA_관리구조.md) | **매주.** 이슈 유형 / 워크플로우 / 입도 / 명명 / 라벨 / 우선순위 규칙 |
| [JIRA_대시보드_가이드.md](./JIRA_대시보드_가이드.md) | **한 번만.** 진행 현황을 한눈에 보는 대시보드 만들기 (10분) |

---

## 📦 어디에 뭐가 있나

```
jumanchu/
├── README.md                    ← 프로젝트 소개
├── CLAUDE.md                    ← Claude/LLM 협업 가이드라인
├── .gitignore / .gitattributes / .env.example
├── .github/                     ← PR/이슈 템플릿, CI 워크플로우
│
├── docs/                        ← 👋 지금 여기 (모든 가이드)
│   └── (위 표 참고)
│
└── planning/                    ← 기획·설계 산출물
    ├── 광주1반_6조_주만추.docx    (기획서)
    ├── 주만주_WBS_분해도.docx     (WBS 분해)
    ├── 주만추_간트차트_WBS.xlsx   (간트차트)
    ├── (26_0508) 관통템플릿_Python_15기_7회차.pdf
    ├── ERD_UCD/                  (ERD, UCD 다이어그램)
    └── 화면예시/                  (스와이프, 커뮤니티, 추천 화면)
```

---

## 🔗 외부 링크

- [Jira 보드](https://jmkang21212-1778486604767.atlassian.net/jira/software/projects/SCRUM/boards/)
- [Jira 백로그](https://jmkang21212-1778486604767.atlassian.net/jira/software/projects/SCRUM/backlog)
- [Jira 대시보드](https://jmkang21212-1778486604767.atlassian.net/jira/dashboards)
