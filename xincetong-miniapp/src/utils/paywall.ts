/**
 * 付费墙 token 管理工具
 *
 * v22 决策：进入测评前先弹 9.9 付费墙（付完才进入答题）
 * - paid_token 存 localStorage，存的是 ISO 时间戳
 * - 默认 24 小时有效（每次成功支付刷新）
 * - 进入入口（index/history/type）时校验
 * - 过期/无 token → 跳 pay.vue?mode=pre-asses 付完再回主流程
 */

const STORAGE_KEY = 'xincetong_paid_token'
const VALID_HOURS = 24

/**
 * 检查 paid_token 是否有效（24h 内）
 */
export function hasPaidToken(): boolean {
  try {
    const token = uni.getStorageSync(STORAGE_KEY)
    if (!token) return false
    const paidAt = new Date(token).getTime()
    if (isNaN(paidAt)) return false
    const now = Date.now()
    const elapsedHours = (now - paidAt) / 1000 / 3600
    return elapsedHours < VALID_HOURS
  } catch {
    return false
  }
}

/**
 * 设置 paid_token（支付成功时调用）
 */
export function setPaidToken(): void {
  try {
    uni.setStorageSync(STORAGE_KEY, new Date().toISOString())
  } catch (e) {
    console.error('[paywall] setPaidToken failed:', e)
  }
}

/**
 * 清除 paid_token（极少用，目前保留出口）
 */
export function clearPaidToken(): void {
  try {
    uni.removeStorageSync(STORAGE_KEY)
  } catch {}
}

/**
 * 获取付费墙跳转 URL（pre-asses 模式）
 * @param from 来源标识，用于埋点（index/history/type）
 * @param type 测评类型
 */
export function getPaywallUrl(from: string, type: 'personal' | 'business' = 'personal'): string {
  return `/pages/result/pay?mode=pre-asses&from=${from}&type=${type}`
}
