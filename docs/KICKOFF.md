# 주만추 프로젝트 킥오프

> **일시**: 2026-05-18 (월) — 첫 정식 작업일 전 함께 보면서 정리하는 자리
> **팀**: 광주1반 6조 — 강재민(BE) / 송호영(FE) / 정율(추천 알고리즘)
> **이 문서**: 같이 화면 띄워놓고 같이 보면서 진행하는 회의용 가이드

---

## 0. 오늘 회의에서 얻고 갈 것

1. 누가 무엇을 언제까지 하는지 같은 그림 갖기
2. 협업 규칙 합의 (5번 체크리스트)
3. 내일(Day 1) 각자가 무엇을 시작할지 정하기

---

## 1. 앞으로의 계획 — Phase 5단계 / 약 6주

| Phase | 기간 | 핵심 산출물 | 주담당 |
|---|---|---|---|
| 1. 기획·설계 | Week 1 (5/11~5/17) | 사용자 스토리, ERD, API 명세, 와이어프레임 | 전원 |
| 2. 백엔드 개발 | Week 2~4 (5/18~6/7) | Django API, DB, 추천 엔진 | **강재민** |
| 3. 프론트엔드 개발 | Week 2~5 (5/18~6/12) | Vue SPA (10여 페이지) | **송호영** |
| 4. 통합·테스트 | Week 5~6 (6/8~6/18) | FE↔BE 연동, 시나리오 테스트, 안정화 | 전원 |
| 5. 발표 준비 | Week 6~7 (6/15~6/25) | 발표 자료, 시연 영상, 리허설 | 전원 |

**📌 마감 6/20 / 발표 6/25**

**Phase 1 현재 상태**:
- ✅ 사용자 스토리 11개 정리 완료 → `docs/USER_STORIES.md`
- ✅ ERD 1차 → `planning/모델_서비스flow/erd.png`
- ⏳ API 명세 (이번 주 안에 BE가 초안)
- ⏳ 와이어프레임 (이번 주 안에 FE가 초안)

---

## 2. Jira 사용법 — 처음 쓰는 사람을 위한 10분 가이드

### 매일 보는 곳 = "보드"

```
┌───────────┬─────────────┬───────────┬─────────┐
│ 해야 할 일│   진행 중   │  검토 중  │  완료   │
│  (To Do)  │(In Progress)│(In Review)│ (Done)  │
└───────────┴─────────────┴───────────┴─────────┘
```

매일 아침: 내 카드를 잡고 **드래그**로 옮기면 끝. 그게 전부.
- 시작할 때 → "진행 중"
- PR 올렸을 때 → "검토 중"
- 머지/완료 후 → "완료"

### 새 일이 생기면 = "+ 만들기"

5개 필드만 채우면 됩니다.
1. **유형** — 사용자 가치 있으면 스토리, 없으면 작업, 결함이면 버그
2. **요약(제목)** — 스토리는 사용자 관점 한 문장
3. **상위 항목** — 어느 Epic 아래인지 (예: 회원가입이면 Phase 2 > 2.1)
4. **라벨** — `backend` / `algo` / `frontend` 중 본인 영역
5. **담당자** — 본인

### 주 1회 (월 아침) = "백로그"에서 다음 스프린트 정리

백로그 화면에서 "이번 주에 할 카드"를 드래그로 현재 스프린트로 옮긴다.

### 더 자세히 알고 싶으면

| 문서 | 무엇 |
|---|---|
| `docs/JIRA_시작가이드.md` | "처음 쓰는 사람용 5분 가이드" — 그대로 따라하면 됨 |
| `docs/JIRA_관리구조.md` | 이슈 위계, 워크플로우, 라벨, 우선순위 등 전체 규칙 |
| `docs/JIRA_대시보드_가이드.md` | 보드를 어떻게 활용하는지 |

**오늘 회의 후 각자 5분만 `JIRA_시작가이드.md` 훑어보기 약속**

---

## 3. 협업 방법 및 규칙

### 3.1 역할 분담 (이미 정해진 것)

- **강재민 (BE)** — Django 코드 전부, 외부 API 연동, 추천 함수를 호출해 REST로 노출
- **정율 (Algo)** — 순수 Python 함수 (데이터 입력 → 추천 결과). Django 코드 안 짬
- **송호영 (FE)** — Vue.js 코드 전부, 스와이프 UI, API 호출

> 자세한 매트릭스는 (이전 세션에서 만든) `JIRA_역할분담.md` 참고 — 새 폴더로 옮겨와야 함 (5번 체크리스트)

### 3.2 BE ↔ Algo 인터페이스 — 가장 중요한 약속

**원칙**: 코드 짜기 전에 함수 시그니처 먼저 합의.

예시:
```python
# 정율(Algo)이 만들 함수
def recommend_by_trending_news(user_id: int, limit: int = 10) -> list[StockRecommendation]:
    ...

# 강재민(BE)이 호출해서 API로 노출
class TrendingRecommendView(APIView):
    def get(self, request):
        recs = recommend_by_trending_news(request.user.id, limit=10)
        return Response([r.to_dict() for r in recs])
```

함수명, 파라미터, 반환 타입을 Jira 이슈 본문이나 PR 머지 전에 정해둔다.

### 3.3 Git 워크플로우 (이미 `BRANCH_STRATEGY.md`에 정리됨)

**브랜치**: `<type>/<JIRA-KEY>-<짧은-설명>` 예) `feature/SCRUM-23-django-setup`
**커밋**: `<type>(<scope>): <subject>  [JIRA-KEY]` 예) `feat(auth): 회원가입 API 추가  [SCRUM-55]`
**PR**: `develop`으로. CI 통과 + 1명 리뷰 후 Squash merge.

### 3.4 데일리 스크럼 (제안 — 회의에서 결정)

- **시간**: 매일 10:00, 10분 이내
- **형식**: 어제 한 일 / 오늘 할 일 / 막힌 점
- **막힌 점**: 24시간 안에 공유 (Jira 이슈에 `blocked-external` 라벨 + 슬랙)

### 3.5 PR 리뷰 정책 (제안)

- **누가 리뷰?**
  - BE PR → Algo나 FE가 가볍게 훑기 (도메인 지식 전파용)
  - Algo PR → BE가 인터페이스 합의 확인
  - FE PR → BE가 API 호출 정확성 확인
- **승인**: 1명 이상 + CI 통과 → Squash merge
- **PR 크기**: 가능하면 PR 하나 = Story 하나 또는 Sub-task 하나 (300줄 미만 권장)

### 3.6 막혔을 때 (서로 답답해지지 않기 위한 3 step)

1. **30분 룰** — 혼자 30분 이상 막히면 슬랙에 질문 (혼자 끙끙 X)
2. **Jira 이슈 코멘트** — 무엇이 막혔는지, 어디까지 시도했는지 기록
3. **데일리에서 공유** — 다음 데일리에서 공식 블로커로 등록

### 3.7 모델 변경 시 충돌 방지 (중요)

**핵심 원칙**: 모델 변경은 — **가장 작게, 가장 빨리, 가장 명확하게 알리고**.

#### 5단계 워크플로우

**1. 작업 시작 전 (10초)** — Slack에 한 줄 공지
> "🛠️ User 모델에 phone 필드 추가합니다. 30분 안에 PR 올릴게요."

다른 사람이 같은 모델 만지고 있으면 → **여기서 멈추고 5분 합의**.

**2. PR을 작게** — "PR 하나 = 모델 변경 하나"
- 비즈니스 로직·뷰 변경과 섞지 말 것
- 모델 변경 + 마이그레이션 파일만 묶어서 작은 PR

**3. 머지 우선순위** — 모델 변경 PR을 먼저 머지
- 다른 사람들이 빨리 rebase할 수 있게
- 24시간 안에 머지 못 하면 draft로 내리고 더 작게 쪼개기

**4. 머지 직후 (10초)** — Slack에 다시 한 줄
> "✅ User 모델 변경 머지됨. 각자 develop pull 후 `python manage.py migrate` 부탁"

**5. 다른 사람의 행동** — 즉시 자기 브랜치에서 rebase
```bash
git fetch origin && git rebase origin/develop
# 마이그레이션 충돌 있으면 즉시 해결
```

#### 같은 모델을 동시에 두 명이 만져야 한다면

**방법 A (안전)** — 직렬화: 한 명 먼저 머지 → 다른 사람이 rebase 후 작업
**방법 B (빠름)** — 15분 페어 세션에서 두 변경을 한 PR로 묶음. 마이그레이션 하나만 생성

**🚫 금지**: 두 명이 각자 `makemigrations` 후 따로 PR. 마이그레이션 번호 충돌(`0002_user_phone.py` vs `0002_user_investor_type.py`)로 한쪽 무조건 재작업.

#### 모델 owner 매트릭스 (5/18 회의에서 확정)

| 모델 | Owner | 비고 |
|---|---|---|
| User / Profile | 강재민 | 인증 도메인 |
| Stock / StockPrice | 강재민 | 종목 도메인 |
| Portfolio / Transaction | 강재민 | 포트폴리오 |
| Diary | 강재민 | 일기 |
| Post / Comment | 강재민 | 커뮤니티 |
| Financial (DART) | 강재민 | 재무 |
| Recommendation / SwipeRecord | **TBD** | Algo 또는 BE — 회의에서 결정 |
| InvestorMBTI | **TBD** | 위와 동일 |

> Owner 외 사람이 수정하려면 owner와 사전 합의 필수.

#### 자동화 가드 (이미 적용됨)

- ✅ CI에 `makemigrations --check --dry-run` — 마이그레이션 누락 PR 차단
- ⏳ branch protection (오늘 켤 예정) — develop/main 직접 push 금지

---

## 4. 문서화 — 어디에 / 무엇을 / 어떻게

### 4.1 `docs/` 폴더 구조 (현재)

```
docs/
├── README.md                  ← 폴더 안내
├── BRANCH_STRATEGY.md         ← Git 브랜치/커밋 규칙
├── GITHUB_SETUP.md            ← GitHub 원격 연결 가이드
├── JIRA_관리구조.md           ← Jira 위계/워크플로우/라벨
├── JIRA_시작가이드.md         ← 처음 쓰는 사람용
├── JIRA_대시보드_가이드.md    ← 보드 활용
├── KICKOFF.md                 ← 지금 이 문서
├── PROJECT_SETUP_SUMMARY.md   ← 초기 세팅 요약
└── USER_STORIES.md            ← 사용자 스토리 11개
```

### 4.2 새 문서 추가 규칙

| 무엇 | 어디에 | 비고 |
|---|---|---|
| API 명세서 | `docs/API_SPEC.md` | BE가 작성. FE는 이것 보고 호출 |
| 와이어프레임 | `docs/WIREFRAMES.md` 또는 Figma 링크 | FE가 작성 |
| 회의록 | `docs/meetings/YYYY-MM-DD.md` | 매 회의 후 5분 |
| 의사결정 기록 (ADR) | `docs/decisions/NNNN-<제목>.md` | "왜 이 기술/방식?"이라는 질문이 나올 만한 결정만 |
| 트러블슈팅 | `docs/troubleshooting/` | 같은 문제 재발 방지용 |

### 4.3 문서 작성 원칙

- **짧게** — 한 문서 = 한 페이지 미만 권장. 길면 쪼개기.
- **최신화** — 결정이 바뀌면 문서를 바꾼다. 새 문서 추가가 답이 아닐 때 많음.
- **링크로 연결** — 같은 내용을 두 곳에 적지 않는다. 한 곳에 적고 링크.
- **이미지/다이어그램** — 글로 100줄보다 그림 한 장. 단, 출처 표기.

### 4.4 회의록 템플릿

```markdown
# YYYY-MM-DD 회의록

- 참석: 강재민, 송호영, 정율
- 시간: 10:00-10:15

## 어제 한 일 / 오늘 할 일
- 강재민: ...
- 송호영: ...
- 정율: ...

## 막힌 점
- ...

## 결정 사항
- [ ] ...

## 다음 회의에서 이어볼 것
- ...
```

---

## 5. 오늘 회의에서 결정해야 할 것 — 체크리스트

회의 끝나면 모두 체크되어 있어야 합니다.

- [ ] **데일리 스크럼 시간 확정** — 제안: 매일 10:00 / 10분. 다른 시간이 좋으면 합의.
- [ ] **스프린트 길이 확정** — 제안: 1주 (월요일 시작, 금요일 회고). Phase 2/3가 3주짜리라 1주가 적절.
- [ ] **PR 리뷰 정책 확정** — 제안: 1명 승인 + CI 통과 + Squash merge. 본인 PR 셀프 머지 금지.
- [ ] **커뮤니케이션 채널 정리** — 슬랙/디스코드/카카오톡 중 어디? 채널/방 어떻게 나눌지.
- [ ] **회의록 위치 결정** — 제안: `docs/meetings/YYYY-MM-DD.md`. 매일 데일리 후 작성자 로테이션.
- [ ] **Jira 첫 5분 학습 약속** — 회의 후 각자 `JIRA_시작가이드.md`를 5분 읽고 보드에서 카드 하나 옮겨보기.
- [ ] **GitHub 원격 연결** — `docs/GITHUB_SETUP.md` 따라 강재민이 오늘 안에 완료.
- [ ] **GitHub for Jira 앱 설치** — 한 명이 설치하면 팀 전체 적용. 커밋/PR이 Jira 이슈에 자동 연결됨.
- [ ] **모델 owner 매트릭스 확정** — 3.7 표의 TBD 두 칸(Recommendation, InvestorMBTI) 결정. 어떤 모델은 누가 변경 권한을 가지는지 5분 합의.

---

## 6. 내일(Day 1, 5/19 화)부터 — 각자 무엇을 시작?

### 강재민 (BE)
1. **SCRUM-23** Django 세팅 시작 — `backend/` 폴더 생성, settings, User 모델
2. **API 명세서 초안** 작성 시작 — `docs/API_SPEC.md` (USER_STORIES.md 기반)
3. **PR 첫 머지로 워크플로우 검증** — 작은 PR이라도 정율/송호영이 리뷰 → 머지 한 사이클

### 송호영 (FE)
1. **SCRUM-27** Vue 세팅 시작 — `frontend/` 폴더 생성, 라우터, Pinia
2. **와이어프레임 초안** — Figma 또는 펜으로라도 11페이지 골격 (USER_STORIES.md의 "관련 화면" 참고)

### 정율 (Algo)
1. **샘플 데이터셋 조사** — pykrx, yfinance로 종목 메타 + 시세 데이터 어떻게 받아오는지 직접 실행
2. **추천 함수 시그니처 합의** — 강재민과 30분 페어 — `recommend_by_user_pattern`, `recommend_by_trending_news`의 입출력 확정 후 USER_STORIES.md US-04, US-05에 반영

---

## 7. 자주 보게 될 링크

- **Jira 보드**: https://jmkang21212-1778486604767.atlassian.net/jira/software/projects/SCRUM/boards/1
- **Jira 백로그**: https://jmkang21212-1778486604767.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog
- **Jira 타임라인**: https://jmkang21212-1778486604767.atlassian.net/jira/software/projects/SCRUM/boards/1/timeline

---

## 8. 마지막 한 마디

기획서·ERD·문서가 완벽해질 때까지 기다리지 마세요. 작은 PR 하나 머지하는 게 큰 문서 한 권보다 팀의 흐름을 빠르게 만듭니다.

내일 Day 1, **각자 PR 하나씩 만들기**를 목표로 갑시다.
