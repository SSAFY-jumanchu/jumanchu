export function useFormat() {
  function formatNumber(value) {
    return new Intl.NumberFormat('ko-KR').format(value)
  }

  function formatMoney(value, currency) {
    const options =
      currency === 'KRW'
        ? { maximumFractionDigits: 0 }
        : { minimumFractionDigits: 2, maximumFractionDigits: 2 }
    return `${currency === 'KRW' ? '₩' : '$'}${new Intl.NumberFormat('ko-KR', options).format(value)}`
  }

  function formatCompact(value) {
    return new Intl.NumberFormat('ko-KR', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
  }

  function formatRate(value) {
    if (value === null || value === undefined) return '준비 중'
    return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  function signedClass(value) {
    if (value > 0) return 'is-up'
    if (value < 0) return 'is-down'
    return 'is-flat'
  }

  return { formatNumber, formatMoney, formatCompact, formatRate, signedClass }
}
