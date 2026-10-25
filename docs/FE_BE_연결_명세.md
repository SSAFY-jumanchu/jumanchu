# 프론트엔드 ↔ 백엔드 연결 명세

> 작성 2026-06-23. `feature/semifinal` 통합 작업 기준.
> **목적**: 현재 와이어프레임(목 데이터) 모드인 프론트엔드를 실제 Django REST API에 연결한다.
> 진실의 원천: 엔드포인트는 [URL_MAP.md](URL_MAP.md), 스키마는 Swagger `GET /api/docs/`.

---

## 0. 현재 상태 (출발점)

| 영역 | 상태 |
|---|---|
| **백엔드** | ✅ 완성 — 46개 엔드포인트 8개 앱, JWT 인증, drf-spectacular 스키마 |
| **연결 인프라** | ✅ 준비됨 — Vite proxy(`/api`→`:8000`), CORS(`localhost:5173`+credentials) |
| **프론트엔드** | ❌ 미연결 — `axios` 설치만 됨, API 호출 레이어 없음, `stores/auth.js`는 `mockLogin`만 존재 |

→ **할 일**: FE에 ① axios 인스턴스 + 인터셉터, ② API 모듈, ③ 실제 인증 스토어, ④ 각 View의 목 데이터를 API 호출로 교체.

---

## 1. 통신 구조

```
[Vue dev :5173] --/api/*--> [Vite proxy] --> [Django runserver :8000]
                  (same-origin, 쿠키 자동 전달)
```

- 프론트는 **항상 상대경로 `/api/v1/...`** 로 호출한다. (절대 URL 금지 — proxy가 same-origin으로 처리해 쿠키 문제 없음)
- 모든 API 프리픽스: `/api/v1/`. 인증만 `/api/v1/auth/`.
- 운영 배포 시에는 `VITE_API_BASE_URL` 로 백엔드 도메인을 주입 (아래 6번).

---

## 2. 인증 방식 (가장 중요)

백엔드가 이미 구현한 토큰 정책 (`backend/config/settings.py` `SIMPLE_JWT`, `accounts/views.py`):

| 토큰 | 저장 위치 | 수명 | 전달 방법 |
|---|---|---|---|
| **access** | FE 메모리(Pinia store) | 30분 | 요청 헤더 `Authorization: Bearer <access>` |
| **refresh** | httpOnly 쿠키 `refresh_token` | 14일 | 브라우저 자동 전송 (path=`/api/v1/auth/`) |

**원칙**
- access 토큰은 **localStorage에 저장하지 않는다** (XSS 노출 방지) — Pinia state(메모리)에만 보관.
- refresh 토큰은 JS에서 못 읽는다 (httpOnly). 갱신은 `POST /auth/token/refresh/` 가 쿠키를 읽어 새 access를 발급.
- 새로고침 시 access는 사라지므로, 앱 부팅 때 `/auth/token/refresh/` 를 한 번 호출해 세션을 복원한다(쿠키가 살아 있으면 성공).

### 2.1 인증 플로우

```
[로그인]   POST /auth/login/  {email, password}
            ← 200 {access, user}  +  Set-Cookie: refresh_token (httpOnly)
            → store.access = access, store.user = user

[요청]     GET /portfolio/   (Authorization: Bearer <access>)

[만료]     ← 401  →  POST /auth/token/refresh/ (쿠키 자동)  ← 200 {access}
            → store.access 갱신 후 원래 요청 1회 재시도

[부팅]     앱 mount → POST /auth/token/refresh/ 시도
            성공 → 세션 복원 / 실패 → 비로그인 상태

[로그아웃] POST /auth/logout/  → 서버가 refresh 블랙리스트 + 쿠키 삭제
            → store 초기화
```

### 2.2 인증 응답 실제 필드 (Serializer 확정 — 추측 금지)

`backend/accounts/serializers.py` 기준.

```jsonc
// POST /auth/login/  → 200
{
  "access": "<jwt>",
  "user": {
    "id": 1, "email": "...", "nickname": "...", "birth_year": 1998,
    "profile": null | { investment_style, preferred_period, risk_tolerance, ... },  // 온보딩 전 null
    "profile_stock_code": "005930",   // signature 종목
    "date_joined": "..."
  }
}
// ⚠️ 로그인 응답엔 온보딩 완료 플래그 없음 → user.profile != null 로 판별

// GET /auth/me/  → 200
{
  "user": { /* 위 user와 동일 구조 */ },
  "has_completed_onboarding": true     // ← 최상위 boolean (snake_case). = InvestmentProfile 존재 여부
}

// POST /auth/token/refresh/  → 200
{ "access": "<jwt>" }                   // user 없음
```

> 필드 키는 **`has_completed_onboarding`** (snake_case). `onboarding_completed` 아님. user 객체 안이 아니라 **/me 응답 최상위**에 있다.

---

## 3. axios 인스턴스 설계 (`src/api/client.js`)

```js
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  withCredentials: true,            // refresh 쿠키 송수신
  headers: { 'Content-Type': 'application/json' },
})

// 요청: access 토큰 주입
client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.access) config.headers.Authorization = `Bearer ${auth.access}`
  return config
})

// 응답: 401 → refresh 1회 → 원요청 재시도 (무한루프 방지 플래그)
let refreshing = null
client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { response, config } = error
    const auth = useAuthStore()
    const isRefreshCall = config.url?.includes('/auth/token/refresh')
    if (response?.status === 401 && !config._retried && !isRefreshCall) {
      config._retried = true
      try {
        refreshing ??= auth.refresh()      // 동시 401 시 갱신 1회로 합침
        await refreshing
        refreshing = null
        return client(config)
      } catch (e) {
        refreshing = null
        auth.clear()
        // 라우터로 /login 리다이렉트 (아래 5번)
        return Promise.reject(e)
      }
    }
    return Promise.reject(error)
  },
)

export default client
```

**규칙**
- 모든 API 모듈은 이 `client` 만 사용한다. 컴포넌트에서 `axios` 직접 호출 금지.
- 공개 엔드포인트(종목 목록·뉴스 등)도 같은 client 사용 — access 없으면 헤더 미부착될 뿐.

---

## 4. API 모듈 구조 (`src/api/`)

도메인별 파일 1개. 컴포넌트는 raw URL을 모르고 함수만 호출한다.

```
src/api/
├── client.js        # axios 인스턴스 (3번)
├── auth.js          # login, signup, logout, refresh, me, onboarding
├── stocks.js        # list, detail, price, orderbook, chart, financials
├── portfolio.js     # summary, holdings, balance, allocation, orders
├── recommend.js     # recommendations, watchlist, longterm
├── community.js     # posts, comments, like, follow
├── diary.js         # diaries
└── news.js          # news feed/search/by-sector
```

**반환 형태 규칙 (결정됨)**: 모든 API 함수는 **`res.data` 만 반환**한다 — 호출부에서 `.data`를 다시 벗기지 않도록 모듈에서 처리. 컴포넌트는 axios 응답 구조를 몰라도 된다.

예시 (`src/api/stocks.js`):

```js
import client from './client'

export const fetchStocks = (params) => client.get('/stocks/', { params }).then((r) => r.data)
export const fetchStockDetail = (code) => client.get(`/stocks/${code}/`).then((r) => r.data)
export const fetchStockPrice = (code) => client.get(`/stocks/${code}/price/`).then((r) => r.data)
```

호출부:

```js
const stocks = await fetchStocks({ q: '삼성' })   // 바로 데이터 사용
```

> 헤더/상태코드가 필요한 드문 경우(페이지네이션 헤더 등)는 해당 함수만 예외적으로 `res` 전체를 반환하고 주석으로 명시.

---

## 5. 인증 스토어 교체 (`src/stores/auth.js`)

현재 `mockLogin` 기반 → 실제 토큰 스토어로 교체. 시그니처(필드명)는 유지해 라우터/뷰 영향 최소화.

```js
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    access: null,                 // 메모리에만
    hasCompletedOnboarding: false,
    initialized: false,
  }),
  getters: {
    isAuthenticated: (s) => !!s.access,
  },
  actions: {
    async login(email, password) {
      const data = await authApi.login(email, password)   // { access, user }
      this.access = data.access
      this.user = data.user
      // 로그인 응답엔 플래그가 없음 → profile 존재로 온보딩 완료 판별
      this.hasCompletedOnboarding = data.user?.profile != null
    },
    async refresh() {                       // 인터셉터/부팅이 호출 — access만 갱신
      const data = await authApi.refresh()  // 응답은 { access } 뿐, user 없음
      this.access = data.access
      return data.access
    },
    async fetchMe() {                       // { user, has_completed_onboarding }
      const data = await authApi.me()
      this.user = data.user
      this.hasCompletedOnboarding = data.has_completed_onboarding
      return data.user
    },
    async logout() {
      try { await authApi.logout() } finally { this.clear() }
    },
    clear() { this.user = null; this.access = null; this.hasCompletedOnboarding = false },
    async init() {                          // 앱 부팅 1회: 쿠키로 세션 복원
      if (this.initialized) return
      try {
        await this.refresh()                // 쿠키 → 새 access
        await this.fetchMe()                // refresh엔 user가 없으므로 /auth/me/ 로 복원 (결정 #2-A)
      } catch { this.clear() }
      finally { this.initialized = true }
    },
  },
})
```

> 필드 매핑 근거는 2.2절 참조. 핵심: 온보딩 플래그는 `/me`의 `has_completed_onboarding`, 로그인 직후엔 `user.profile`로 판별.

**라우터 가드** (`src/router/index.js`): 현재 강제 없음 → JWT 필요한 라우트에 `meta: { requiresAuth: true }` 부여하고, 미인증 시 `/login` 리다이렉트하도록 `beforeEach` 보강.

---

## 6. 환경 변수

`frontend/.env.development` (커밋), `frontend/.env.local`(개인, gitignore):

```
# 비우면 '/api/v1' 상대경로 사용 (Vite proxy 경유) — 로컬 개발 기본값
VITE_API_BASE_URL=

# 백엔드를 다른 포트로 띄웠을 때만
VITE_BACKEND_URL=http://localhost:8000
```

운영 빌드는 `VITE_API_BASE_URL=https://api.도메인/api/v1` 주입.

---

## 7. 에러 처리 컨벤션

백엔드 에러 응답은 `{ "detail": "메시지" }` 형태가 표준 (일부 검증 에러는 필드별 dict).

| 상태 | 의미 | FE 처리 |
|---|---|---|
| 400 | 검증 실패 | 폼 필드/토스트에 `detail` 또는 필드 에러 표시 |
| 401 | 인증 만료/없음 | 인터셉터가 refresh 시도 → 실패 시 `/login` |
| 403 | 권한 없음 | "권한이 없습니다" 토스트 |
| 404 | 리소스 없음 | 빈 상태 UI |
| 409 | 중복(가입 등) | `detail` 메시지 폼 표시 |
| 429 | 레이트리밋 | `detail` 메시지 + 재시도 안내 |
| 5xx | 서버 오류 | 공통 에러 토스트 |

공통 에러 메시지 추출 헬퍼 1개를 두고 재사용:
```js
export const errMsg = (e) => e.response?.data?.detail || '문제가 발생했어요. 잠시 후 다시 시도해주세요.'
```

### 7.1 피드백 UI 방침 (결정 #4-A)

- **토스트(에러·성공 알림)는 전역 1개로 통일**. 로딩 스피너는 화면별 로컬 처리.

```
src/stores/toast.js      # { items: [] } + show/error/success 액션
src/components/Toast.vue  # App.vue 최상단에 1번 마운트, store 구독
```

- 호출부/인터셉터 공통:
  ```js
  import { useToastStore } from '@/stores/toast'
  const toast = useToastStore()
  try { ... } catch (e) { toast.error(errMsg(e)) }
  ```
- 인터셉터에서 refresh 실패(401 최종)·5xx는 토스트로 공통 노출. 폼 검증(400/409)은 해당 화면이 필드 옆에 표시.
- **로딩은 각 View의 로컬 `ref`**로 처리 — 목록은 스켈레톤, 버튼 액션은 버튼 내 스피너:
  ```js
  const loading = ref(false)
  loading.value = true
  try { stocks.value = await fetchStocks() } finally { loading.value = false }
  ```
  전역 로딩 오버레이는 두지 않는다.

---

## 8. 화면 ↔ 엔드포인트 매핑

| View | 사용 엔드포인트 | 권한 |
|---|---|---|
| `LoginView` | `POST /auth/login/`, `POST /auth/signup/` | 공개 |
| `OnboardingView` | `POST /auth/onboarding/` | JWT |
| `HomeView` | `GET /markets/summary/`, `GET /news/economy/`, `GET /recommendations/` | 공개/JWT |
| `StocksView` | `GET /stocks/` (검색·목록) | 공개 |
| `StockDetailView` | `/stocks/{code}/` `/price/` `/chart/` `/orderbook/` `/financials/` `/posts/`, `/news/stocks/{code}/` | 공개 |
| `WatchlistView` | `GET·POST /watchlist/`, `DELETE /watchlist/{code}/`, `/news/watchlist/` | JWT |
| `HoldingsView` | `GET /portfolio/holdings/`, `/news/holdings/` | JWT |
| `PortfolioView` | `/portfolio/` `/balance/` `/allocation/`, `/orders/` | JWT |
| `StockDetailView`(주문) | `POST /orders/preview/`, `POST /orders/` | JWT |
| `CommunityView` | `/posts/`, `/posts/{id}/`, `/comments/`, `/like/`, `/follow/` | 읽기공개/쓰기JWT |
| `TradingDiaryView` | `GET·POST /diaries/`, `/diaries/{id}/` | JWT |
| `MyPageView` | `GET·PATCH /auth/me/`, 장투 `/longterm/ranking/` `/longterm/{code}/report/` | JWT |

> 정확한 요청/응답 필드는 화면 작업 직전 Swagger에서 해당 Serializer를 열어 확정.

---

## 9. 작업 순서 (권장)

1. **인프라**: `src/api/client.js` + `.env.development` → 인터셉터 동작 확인 (verify: 공개 `GET /stocks/` 호출 성공)
2. **인증**: `src/api/auth.js` + `stores/auth.js` 교체 + 라우터 가드 → 로그인→토큰→보호 API 호출→새로고침 세션복원→로그아웃 전 구간 검증
3. **도메인 교체**: View별로 목 데이터 → API 모듈 호출로 1개씩 교체 (의존도 낮은 `StocksView`부터). 한 View = 한 PR/커밋.
4. 각 단계 후 `npm run dev` + 백엔드 `runserver`로 실제 호출 검증.

**선행 조건**: 백엔드 기동 (`docker compose up -d db redis` → `python manage.py migrate` → `runserver`). 시드 데이터/테스트 계정 필요 여부는 BE와 확인.

---

## 10. 열린 결정 사항 (작업 전 합의)

- [x] ~~API 모듈 함수 반환 형태~~ → **`res.data` 반환으로 결정** (2026-06-23). 헤더가 필요한 함수만 예외.
- [x] ~~부팅 세션 복원 시 `user` 채우는 법~~ → **A: refresh로 access 받은 뒤 `GET /auth/me/` 추가 호출**로 결정 (2026-06-23). BE 수정 없이 FE 단독 해결.
- [x] ~~온보딩 플래그 실제 키 이름~~ → **`has_completed_onboarding`** (`/auth/me/` 최상위). 로그인 응답엔 없음 → `user.profile != null`로 판별. 2.2절에 전체 필드 확정 (2026-06-23).
- [x] ~~전역 로딩/토스트 UI~~ → **A: 토스트만 전역(1개), 로딩은 화면별 로컬**로 결정 (2026-06-23). 상세 7.1절.
- [ ] 운영 배포 도메인/CORS origin 확정
