import { useModeStore } from '../stores/mode'
import { datingCopy } from '../copy/dating'

// 연애모드 카피 치환 헬퍼.
// t(key, normal): 연애모드 + 사전에 key가 있으면 연애 문구, 아니면 normal(기본 문구)을 반환.
// mode 스토어가 반응형이라 토글 시 템플릿이 자동 갱신된다.
export function useCopy() {
  const mode = useModeStore()
  function t(key, normal) {
    if (mode.isDating && key in datingCopy) return datingCopy[key]
    return normal
  }
  return { t }
}
