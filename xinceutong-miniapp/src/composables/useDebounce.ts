/**
 * useDebounce - 防抖（用于实时纠错：用户选完停 400ms 再调接口）
 *
 * 用法：
 *   const debounced = useDebounce(myFn, 400)
 *   debounced(args)   // 自动防抖
 */
export function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay = 400,
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null
  return function debounced(...args: Parameters<T>) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      try { fn(...args) } catch (e) { console.error('[debounce] callback error', e) }
    }, delay)
  }
}

/**
 * 简易 throttle（用于按钮防重点击）
 */
export function useThrottle<T extends (...args: any[]) => any>(
  fn: T,
  delay = 1000,
): (...args: Parameters<T>) => void {
  let last = 0
  return function throttled(...args: Parameters<T>) {
    const now = Date.now()
    if (now - last >= delay) {
      last = now
      try { fn(...args) } catch (e) { console.error('[throttle] callback error', e) }
    }
  }
}
