import client from './client'

// 모든 함수는 res.data만 반환 (명세 결정 #1).
export const login = (email, password) =>
  client.post('/auth/login/', { email, password }).then((r) => r.data)

export const signup = (payload) =>
  client.post('/auth/signup/', payload).then((r) => r.data)

export const logout = () =>
  client.post('/auth/logout/').then((r) => r.data)

// refresh_token(httpOnly 쿠키)로 새 access 발급. 응답은 { access } 뿐.
export const refresh = () =>
  client.post('/auth/token/refresh/').then((r) => r.data)

// { user, has_completed_onboarding }
export const me = () =>
  client.get('/auth/me/').then((r) => r.data)

// 내 정보 수정 (nickname, birth_year) → { user, has_completed_onboarding }
export const updateMe = (payload) =>
  client.patch('/auth/me/', payload).then((r) => r.data)

// 온보딩 제출 → { user, profile_stock, investor_type }
export const onboarding = (payload) =>
  client.post('/auth/onboarding/', payload).then((r) => r.data)
