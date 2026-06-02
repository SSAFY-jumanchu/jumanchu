# SCRUM-22 와이어프레임 / 화면 설계 — 진행 현황

> 이 문서를 Jira 각 이슈의 코멘트로 붙여넣기 해주세요.

---

## SCRUM-50 [1.4.2] 주요 화면 와이어프레임 7종 — **완료**

**완료일**: 2026-06-02  
**담당**: 송호영 (FE)

### 구현된 화면 목록

| # | 화면 | 경로 | 파일 |
|---|---|---|---|
| 1 | 홈 (시장 요약 + 추천 미리보기) | `/` | `views/HomeView.vue` |
| 2 | 종목 발견 (스와이프 UI) | `/discover` | `views/DiscoverView.vue` |
| 3 | 종목 탐색 (목록 + 상세 + 주문) | `/stocks` | `views/StocksView.vue` |
| 4 | 포트폴리오 | `/portfolio` | `views/PortfolioView.vue` |
| 5 | 커뮤니티 | `/community` | `views/CommunityView.vue` |
| 6 | 프로필 / 투자 MBTI | `/profile` | `views/ProfileView.vue` |
| 7 | 로그인 | `/login` | `views/auth/LoginView.vue` |
| 8 | 회원가입 | `/signup` | `views/auth/SignupView.vue` |
| 9 | 온보딩 (3단계) | `/onboarding` | `views/auth/OnboardingView.vue` |

### 기술 구조
- **vue-router** 설치 완료, 각 화면이 독립 View 컴포넌트로 분리됨
- 공용 컴포넌트: `AppSidebar`, `SwipeCard`, `StockRow`, `StockWorkspace`, `SparklineChart`
- 공용 composable: `useFormat`, `useWatchlist`
- 공용 mock data: `data/stocks.js`
- 인증 페이지는 사이드바 없는 전용 레이아웃 적용

### 샘플 데이터
실제 백엔드 연결 전까지 `data/stocks.js`의 mock 데이터로 화면 확인 가능.  
`VITE_API_BASE_URL` 환경변수 설정 후 Django API 연결 예정.

---

## SCRUM-49 [1.4.1] 정보 구조(IA) / 사이트맵 설계 — **완료**

**완료일**: 2026-06-02

### 사이트맵 (라우터 기준)

```
주만추
├── / (홈) — 비로그인 접근 가능
├── /discover (발견/스와이프)
│   ├── 탭: 패턴 기반 (로그인 필요)
│   └── 탭: 뉴스 기반 (비로그인 가능)
├── /stocks (종목 탐색)
│   ├── 종목 목록 + 필터
│   ├── 관심종목 슬롯
│   └── 종목 상세 (차트 / 재무 / 커뮤니티 탭)
├── /portfolio (포트폴리오) — 로그인 필요
├── /community (커뮤니티)
│   ├── 게시글 목록 — 비로그인 조회 가능
│   └── 글쓰기 — 로그인 필요
├── /profile (프로필) — 로그인 필요
│   └── 투자 MBTI (일기 5개 이상 시 활성화)
├── /login
├── /signup
└── /onboarding (회원가입 완료 후 리다이렉트)
```

---

## 남은 작업 (SCRUM-22 하위)

| 서브태스크 | 상태 | 메모 |
|---|---|---|
| SCRUM-49 [1.4.1] 사이트맵 | ✅ 완료 | 위 문서 참고 |
| SCRUM-50 [1.4.2] 와이어프레임 7종 | ✅ 완료 | Vue 구현 완료 |
| [1.4.3] User Flow 흐름도 | ⬜ 미착수 | Figma 또는 docs 마크다운으로 작성 필요 |
| [1.4.4] 디자인 시스템 / 컴포넌트 정의 | ⬜ 미착수 | style.css CSS 변수 기반, 컴포넌트 카탈로그 정리 필요 |

---

## Jira 업데이트 가이드

1. **SCRUM-49** 이슈 → 상태를 **"완료"**로 변경
2. **SCRUM-50** 이슈 → 상태를 **"완료"**로 변경  
3. **SCRUM-22** 이슈 → 코멘트에 이 문서 내용 붙여넣기
4. 나머지 서브태스크(1.4.3, 1.4.4)는 새 이슈로 생성하거나 현재 스프린트에 추가
