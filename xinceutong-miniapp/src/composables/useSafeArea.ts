/**
 * useSafeArea - 获取安全区信息（用于底部按钮 padding）
 *
 * 用法：
 *   const { safeAreaBottom, statusBarHeight } = useSafeArea()
 *
 * 跨端：H5 永远返回 0（桌面/移动浏览器都没刘海）
 *      小程序/App 通过 uni.getSystemInfoSync() 获取
 */
import { ref, onMounted } from 'vue'

export function useSafeArea() {
  const safeAreaBottom = ref(0)
  const statusBarHeight = ref(0)
  const screenWidth = ref(375)

  onMounted(() => {
    try {
      const sys = uni.getSystemInfoSync() as any
      // iOS safe area：safeAreaInsets.bottom 通常 = 34
      safeAreaBottom.value = (sys.safeAreaInsets?.bottom ?? 0)
      statusBarHeight.value = sys.statusBarHeight ?? 0
      screenWidth.value = sys.screenWidth ?? 375
    } catch (e) {
      console.warn('[useSafeArea] getSystemInfoSync failed', e)
    }
  })

  return { safeAreaBottom, statusBarHeight, screenWidth }
}
