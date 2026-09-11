/**
 * utils/track.ts - 埋点统计
 */
type TrackEvent =
  | 'page_view'
  | 'button_click'
  | 'assessment_start'
  | 'assessment_complete'
  | 'payment_success'
  | 'share_click'
  | 'grant_to_promoter'

interface TrackPayload {
  event: TrackEvent
  page?: string
  data?: Record<string, unknown>
}

/**
 * 平台检测（H5 build 时 __PLATFORM__ 不会替换成字面量，
 * 所以改用 uni.getSystemInfoSync() 运行时检测；H5 下 platform === 'web'，统一映射为 'h5'）
 */
function detectPlatform(): string {
  try {
    const sysInfo =
      typeof uni !== 'undefined' && uni.getSystemInfoSync
        ? uni.getSystemInfoSync()
        : null
    const p = sysInfo?.platform
    if (typeof p === 'string' && p.length > 0) {
      return p === 'web' ? 'h5' : p
    }
  } catch {
    /* ignore */
  }
  return 'h5'
}

export function track(payload: TrackPayload): void {
  // 开发期：仅打 log；生产期：调后端 /api/track 上报
  if (import.meta.env.DEV) {
    console.log('[track]', payload)
    return
  }
  // 静默失败，不打扰用户
  uni.request({
    url: ((import.meta.env.VITE_API_BASE_URL as string) || '') + '/api/track',
    method: 'POST',
    data: {
      ...payload,
      timestamp: Date.now(),
      platform: detectPlatform(),
    },
    fail: () => { /* 静默 */ },
  })
}

/** 页面 PV（onShow 调用） */
export function pageView(pageName: string, data?: Record<string, unknown>) {
  track({ event: 'page_view', page: pageName, data })
}
