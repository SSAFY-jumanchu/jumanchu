import { useThemeStore } from '../stores/theme'
import { datingCopy } from '../copy/dating'

// 연애모드(=love 팔레트) 문구 치환 헬퍼.
// t('키', '기본문구') → love 팔레트면 사전의 연애 문구, 아니면 기본문구(팀원 것).
// 사전에 키가 없으면 항상 기본문구가 나오므로, 연애 문구를 안 넣은 텍스트는 자동으로 기본 모드와 동일.
export function useCopy() {
  const theme = useThemeStore()
  function t(key, fallback) {
    // theme.isLove 접근으로 렌더 추적 → 팔레트 토글 시 자동 갱신
    if (theme.isLove && key in datingCopy) return datingCopy[key]
    return fallback
  }
  return { t }
}
