// 디자인 프리뷰: 백엔드 없이 UI만 확인한다.
// 모든 요청은 조용히 실패하고, 각 뷰는 자체 목업 데이터를 그대로 유지한다.
const disabled = () =>
  Promise.reject(Object.assign(new Error('design preview: API disabled'), { __designPreview: true }))

const client = {
  get: disabled,
  post: disabled,
  put: disabled,
  patch: disabled,
  delete: disabled,
}

export function getAccessToken() {
  return null
}

export function setAccessToken() {}

export default client
