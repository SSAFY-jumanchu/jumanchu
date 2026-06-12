import axios from 'axios'

// Vite dev 프록시(/api → localhost:8000)를 타므로 상대 경로 사용.
// refresh 토큰은 HttpOnly 쿠키(path=/api/v1/auth/)로 관리되고,
// access 토큰만 메모리/localStorage에 들고 Authorization 헤더로 보낸다.
const client = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
})

const ACCESS_KEY = 'jmc_access'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY)
}

export function setAccessToken(token) {
  if (token) localStorage.setItem(ACCESS_KEY, token)
  else localStorage.removeItem(ACCESS_KEY)
}

client.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 → refresh 쿠키로 access 재발급 후 1회 재시도
let refreshPromise = null

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const { response, config } = error
    const isAuthPath = config?.url?.startsWith('/auth/')
    if (response?.status !== 401 || config._retried || isAuthPath) {
      return Promise.reject(error)
    }
    config._retried = true
    try {
      refreshPromise ??= client.post('/auth/token/refresh/')
      const { data } = await refreshPromise
      setAccessToken(data.access)
      return client(config)
    } catch {
      setAccessToken(null)
      return Promise.reject(error)
    } finally {
      refreshPromise = null
    }
  },
)

export default client
