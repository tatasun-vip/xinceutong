/**
 * utils/productConfig.ts
 *
 * v13 增量：icon 从 emoji 改 SVG 名称（与 miniapp 同源 SSOT）
 *
 * 设计原则：
 *  - 每产品一个独立色 + 浅色背景 + 线性 SVG icon，让 6 卡一眼看出区别
 *  - icon 名对应 ui-icon 里的 SVG（替代之前 emoji）
 *  - 颜色与 miniapp productConfig.ts 保持完全一致（双端同源）
 *  - levelColors 给 6 卡共享的 S/A/B/C/D/E 等级色
 *
 * 修改颜色：这里 + miniapp 同步
 * 修改 icon：这里 + 确认 ui-icon.vue 已加对应 name
 */

export type ProductIconName =
  | 'landmark' | 'gem' | 'briefcase' | 'house' | 'receipt' | 'chart'

// 6 大产品品牌色（与后端 product_types.code 一一对应）
export interface ProductColor {
  color: string         // 主色（边/数字/标题）
  bg: string            // 浅色背景（卡片底）
  text: string          // 深色文字（在浅色背景上读得清）
  icon: ProductIconName // SVG 图标名（替代 emoji）
}

export const PRODUCT_COLORS: Record<string, ProductColor> = {
  quality_unit: { color: '#2563EB', bg: '#EBF3FF', text: '#1E3A8A', icon: 'landmark' },
  housing_fund: { color: '#9333EA', bg: '#F3E8FF', text: '#6B21A8', icon: 'gem' },
  salary:       { color: '#EA580C', bg: '#FFF1E6', text: '#9A3412', icon: 'briefcase' },
  house_owner:  { color: '#DC2626', bg: '#FEE7E7', text: '#991B1B', icon: 'house' },
  tax:          { color: '#B89554', bg: '#FAF3E3', text: '#8C6F36', icon: 'receipt' },
  invoice:      { color: '#0891B2', bg: '#E0F4F8', text: '#155E75', icon: 'chart' },
}

// 兜底色（未知 product_code 时用）
export const DEFAULT_PRODUCT_COLOR: ProductColor = {
  color: '#5A6473', bg: '#ECEFF4', text: '#1A1A1A', icon: 'chart',
}

// 评分等级色（6 卡共享；v8 极简金色系，与 miniapp 一致）
export const LEVEL_COLORS: Record<string, { color: string; bg: string; label: string }> = {
  S: { color: '#B89554', bg: '#FAF3E3', label: '极佳' },
  A: { color: '#2C7A4B', bg: '#E5F2EB', label: '优秀' },
  B: { color: '#2563EB', bg: '#EBF3FF', label: '良好' },
  C: { color: '#B25E00', bg: '#FFF1E0', label: '一般' },
  D: { color: '#9B2226', bg: '#FCE7E7', label: '较弱' },
  E: { color: '#5A6473', bg: '#ECEFF4', label: '不推荐' },
}

export const DEFAULT_LEVEL_COLOR = { color: '#5A6473', bg: '#ECEFF4', label: '—' }

// 付费墙色（解锁按钮 + 模糊遮罩）
export const PAYWALL_COLORS = {
  gold:     '#B89554',
  goldBg:   '#FAF3E3',
  goldDark: '#8C6F36',
  lock:     '#5A6473',
}

// 通过率色（v8 极简：3 色金/中灰/暗棕）
export const PASS_PROB_COLOR: Record<string, string> = {
  '高':   '#C9A96E',
  '中高': '#B89554',
  '中':   '#8B7E5E',
  '低':   '#6B7280',
  '极低': '#4A4A4A',
}

// 工具函数：安全取产品色（未知 code 自动兜底）
export function getProductColor(code: string | null | undefined): ProductColor {
  if (!code) return DEFAULT_PRODUCT_COLOR
  return PRODUCT_COLORS[code] || DEFAULT_PRODUCT_COLOR
}

// 工具函数：安全取等级色
export function getLevelColor(level: string | null | undefined) {
  if (!level) return DEFAULT_LEVEL_COLOR
  return LEVEL_COLORS[level] || DEFAULT_LEVEL_COLOR
}

// 严重度色（v9 增量：M2 1/N 锁标用）
export const SEVERITY_COLORS: Record<string, string> = {
  high: '#9B2226',  // 高严重度 → 暗红
  mid:  '#B25E00',  // 中严重度 → 暗橙
  low:  '#B89554',  // 低严重度 → 金棕
}

// 严重度标签
export function severityLabel(sev?: string): string {
  if (sev === 'high') return '高严重度'
  if (sev === 'mid') return '中严重度'
  if (sev === 'low') return '低严重度'
  return '一般'
}
