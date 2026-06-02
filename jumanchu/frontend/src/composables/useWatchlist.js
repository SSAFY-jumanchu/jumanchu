import { ref } from 'vue'

const watchedCodes = ref(['005930', 'NVDA'])

export function useWatchlist() {
  function toggleWatch(code) {
    const i = watchedCodes.value.indexOf(code)
    if (i >= 0) watchedCodes.value.splice(i, 1)
    else watchedCodes.value.push(code)
  }

  return { watchedCodes, toggleWatch }
}
