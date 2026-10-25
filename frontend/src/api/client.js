import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// 모든 API 호출의 단일 진입점. 컴포넌트에서 axios를 직접 쓰지 말고 이 client만 사용한다.
// baseURL을 비우면 '/api/v1' 상대경로 → Vite proxy가 same-origin으로 백엔드에 전달(쿠키 OK).
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  withCredentials: true, // refresh_token(httpOnly 쿠키) 송수신
  headers: { 'Content-Type': 'application/json' },
})

// 요청: access 토큰이 있으면 Authorization 헤더 주입
client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.access) config.headers.Authorization = `Bearer ${auth.access}`
  return config
})

// 응답: 401이면 refresh 1회 시도 후 원요청 재시도. 동시 다발 401은 갱신 1회로 합친다.
let refreshing = null
client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { response, config } = error
    const auth = useAuthStore()
    // 로그인/회원가입/refresh의 401은 "access 만료"가 아니라 인증 실패 그 자체다.
    // 여기서 refresh를 재시도하면 (refresh 쿠키가 없어) "refresh 토큰이 없습니다" 에러가
    // 원래의 "이메일 또는 비밀번호가 올바르지 않습니다"를 덮어버린다 → 재시도 금지.
    const url = config?.url || ''
    const skipRefreshRetry =
      url.includes('/auth/login') ||
      url.includes('/auth/signup') ||
      url.includes('/auth/token/refresh')
    if (response?.status === 401 && config && !config._retried && !skipRefreshRetry) {
      config._retried = true
      try {
        refreshing ??= auth.refresh()
        await refreshing
        return client(config)
      } catch (e) {
        auth.clear()
        return Promise.reject(e)
      } finally {
        refreshing = null
      }
    }
    return Promise.reject(error)
  },
)

// 백엔드 에러 응답({ detail })에서 사용자 표시용 메시지를 뽑는 공통 헬퍼.
export const errMsg = (e) =>
  e.response?.data?.detail || '문제가 발생했어요. 잠시 후 다시 시도해주세요.'

// KIS 라이브 의존 엔드포인트(현재가·보유목록 등)는 간헐 5xx가 나므로 짧게 재시도.
export async function retry(fn, { attempts = 3, delayMs = 400, on = [502, 503, 504] } = {}) {
  let lastErr
  for (let i = 0; i < attempts; i += 1) {
    try {
      return await fn()
    } catch (e) {
      lastErr = e
      if (i < attempts - 1 && on.includes(e.response?.status)) {
        await new Promise((r) => setTimeout(r, delayMs))
        continue
      }
      throw e
    }
  }
  throw lastErr
}

export default client
