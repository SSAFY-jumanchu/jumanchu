# Jira 대시보드 가이드 (10분 컷)

> 매일 아침 한 번만 열면 프로젝트 전체가 한눈에 보이는 대시보드를 직접 만드는 가이드.
> Jira Cloud 무료 플랜 기준. 모든 가젯이 무료에서 사용 가능.

---

## 0. 두 가지 단계로 진행

1. **필터 먼저 저장** (5분) — 자주 쓸 JQL 7개를 "내 필터"에 저장
2. **대시보드 구성** (5분) — 가젯 7개를 배치, 각 가젯이 위 필터를 사용

---

## 1단계. 필터 저장하기

Jira 좌측 사이드바 → **필터** → **고급 검색** 또는 https://jmkang21212-1778486604767.atlassian.net/issues/?jql= 로 이동.

아래 JQL을 하나씩 붙여넣고 검색 → **저장** 클릭 → 이름 입력 → 저장.

| 필터 이름 | JQL | 용도 |
|---|---|---|
| `🔴 내가 진행 중` | `project = SCRUM AND assignee = currentUser() AND statusCategory != Done` | 매일 아침 가장 먼저 보는 것 |
| `🟡 검토 대기 (PR 리뷰 필요)` | `project = SCRUM AND status = "In Review"` | 팀의 PR 리뷰 큐 |
| `⚫ Blocked` | `project = SCRUM AND status = Blocked` | 막힌 작업 즉시 조치 |
| `🟢 이번 스프린트 전체` | `project = SCRUM AND sprint in openSprints()` | 보드와 동일 범위 |
| `📦 Phase 1 (기획·설계)` | `project = SCRUM AND parent = SCRUM-14` | Phase 1 진행 현황 |
| `📦 Phase 2 (백엔드)` | `project = SCRUM AND parent = SCRUM-15` | Phase 2 진행 현황 |
| `🐛 모든 버그` | `project = SCRUM AND issuetype = 버그 AND statusCategory != Done` | 누적 버그 추적 |

> 팁: 저장된 필터는 다른 팀원에게도 공유 가능. 저장 후 우측 상단 "공유" → 프로젝트 멤버에게 보기 권한.

---

## 2단계. 대시보드 만들기

### 2.1 대시보드 생성

1. 좌측 사이드바 → **대시보드** → **대시보드 만들기** 클릭
2. 이름: `주만추 진행 현황`
3. 설명: `매일 아침 확인용 — Phase별 진행 / 내 작업 / 블록 / 리뷰 큐`
4. 권한 보기: **프로젝트 SCRUM 멤버 전체**
5. **만들기**

생성 직후 빈 대시보드가 열립니다. 우측 상단의 **+ 가젯 추가** 버튼을 클릭하면 가젯 목록이 뜹니다.

### 2.2 추천 레이아웃 (3열 × 2~3행)

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ ① 내가 진행 중       │ ② Phase별 진행률    │ ③ 검토 대기 큐       │
│ (Filter Results)    │ (2D Filter Stats)   │ (Filter Results)    │
├─────────────────────┼─────────────────────┼─────────────────────┤
│ ④ 상태별 분포       │ ⑤ 우선순위별 분포    │ ⑥ Blocked 카드      │
│ (Pie Chart)         │ (Pie Chart)         │ (Filter Results)    │
├─────────────────────┴─────────────────────┴─────────────────────┤
│ ⑦ 생성 vs 해결 추세 (Created vs Resolved Chart)                  │
└────────────────────────────────────────────────────────────────┘
```

### 2.3 가젯 설정 (하나씩)

#### ① Filter Results — 내가 진행 중

- 가젯 추가 → **Filter Results**
- Saved Filter: `🔴 내가 진행 중`
- Columns: `Key`, `Summary`, `Priority`, `Status`
- Number of results: `10`

#### ② Two Dimensional Filter Statistics — Phase별 진행률

- 가젯 추가 → **Two Dimensional Filter Statistics**
- Saved Filter: `🟢 이번 스프린트 전체` (또는 `project = SCRUM` 전체 보고 싶으면 새 필터)
- X-Axis (Stat Type): `Status` (상태)
- Y-Axis (Stat Type): `Parent` (상위 항목 — 즉 Phase Epic)
- Sort by: Total
- Show: Numbers + Percentages

> 결과: 행에 Phase 1~5, 열에 To Do / In Progress / In Review / Done이 떠서 어느 Phase가 얼마나 진행됐는지 한눈에.

#### ③ Filter Results — 검토 대기 큐

- Saved Filter: `🟡 검토 대기 (PR 리뷰 필요)`
- Columns: `Key`, `Summary`, `Assignee`
- Number of results: `8`

#### ④ Pie Chart — 상태별 분포

- 가젯 추가 → **Pie Chart**
- Saved Filter: `project = SCRUM AND issuetype != Subtask` (Subtask 빼고. 새 필터로 저장해도 OK)
- Statistic Type: `Status`

#### ⑤ Pie Chart — 우선순위별 분포

- Saved Filter: 위와 동일
- Statistic Type: `Priority`

> 결과: P0가 1~2개를 넘지 않는지 시각적으로 확인. 빨강(Highest)이 너무 많으면 우선순위 재조정 신호.

#### ⑥ Filter Results — Blocked 카드

- Saved Filter: `⚫ Blocked`
- Columns: `Key`, `Summary`, `Assignee`, `Updated`
- Number of results: `5`

> 결과: 비어있으면 좋고, 24시간 이상 머무는 카드가 있으면 데일리에서 즉시 공유.

#### ⑦ Created vs Resolved Chart — 주간 추세

- 가젯 추가 → **Created vs Resolved Chart**
- Project: `SCRUM`
- Period: `Daily`
- Days previously: `14`
- Cumulative totals: 체크 해제 (일별 비교가 더 직관적)

> 결과: 매일 새로 만든 이슈와 끝낸 이슈를 두 막대로. 끝내는 속도가 만드는 속도보다 빠르면 건강한 추세.

---

## 3. 매일 보는 방법

1. 아침에 대시보드 열기
2. ①(내가 진행 중) 먼저 보고 오늘 할 카드 결정
3. ⑥(Blocked) 확인 — 있으면 데일리에서 언급
4. ③(검토 대기) 확인 — 팀원 PR 리뷰
5. 데일리 끝나면 보드(③ 또는 별도 보드 화면)에서 드래그로 상태 갱신

---

## 4. 스프린트 시작 후 추가하면 좋은 가젯

스프린트를 한 번 시작하면 아래 가젯들이 의미를 갖습니다.

- **Sprint Burndown Gadget** — 스프린트 잔여 작업 곡선
- **Sprint Health Gadget** — 현재 스프린트 진행률 / 변경 횟수 / 블록 비율
- **Workload Pie Chart** — 담당자별 부하 분산

스프린트 시작 직후 위 가젯들을 대시보드 빈 자리에 추가하세요.

---

## 5. 한 줄 요약

> **필터 7개 저장 → 대시보드 만들고 가젯 7개 배치 → 매일 아침 30초 훑기.**

대시보드를 만들고 나면 URL을 즐겨찾기에 추가해두는 것이 좋습니다. 형태:
`https://jmkang21212-1778486604767.atlassian.net/jira/dashboards/<번호>`

---

## 6. 자주 막히는 지점

**Q. 가젯이 안 보여요 / 찾을 수 없어요.**
→ 무료 플랜에서 일부 가젯은 안 보입니다 (예: Issue Age, Resolution Time). 위 7개는 모두 무료에서 동작 확인됨.

**Q. Pie Chart에서 Status로 그룹핑했더니 한국어가 깨져요.**
→ 한국어 상태("해야 할 일", "진행 중" 등)는 정상 표시됩니다. 깨지면 브라우저 캐시 비우기.

**Q. 2D Filter Stats에서 Parent로 그룹핑이 안 돼요.**
→ 일부 무료 플랜은 Parent 그룹핑 옵션이 없을 수 있음. 그 경우 Y축을 `Labels`로 바꾸고 `phase-1`, `phase-2` 등의 라벨로 그룹핑 (우리 이슈에 이미 phase-N 라벨이 붙어있음).

**Q. 모바일에서 대시보드가 잘 안 보여요.**
→ Jira 대시보드는 데스크톱 우선. 모바일에선 보드 화면이 더 적합.
