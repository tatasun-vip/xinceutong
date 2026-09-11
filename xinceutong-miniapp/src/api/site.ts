/**
 * api/site.ts - 站点配置（数字+文案+合规变量化）
 *
 * 拉取 site_config 表数据，前端用 config_key 取值做运行时替换。
 * 用途：所有数字（128,000+ / 50+ / 9.99 / 96.3%）+ 文案 + 合规都从这拉。
 */
import http from './request'

export interface SiteConfigGroup {
  number: Record<string, string>
  text: Record<string, string>
  compliance: Record<string, string>
  other: Record<string, string>
}

export type SiteConfig = Record<string, string>

/** 获取全部分组配置 */
export function getSiteConfig() {
  return http.get<SiteConfigGroup>('/api/site/config')
}

/** 刷新缓存（运营改 DB 后调用） */
export function refreshSiteConfig() {
  return http.post<{ message: string }>('/api/site/config/refresh', {})
}

// ============================================================================
// 便捷取值函数（前端组件直接用）
// ============================================================================

export const SITE = {
  userCount:         'site.user_count',
  testCount:         'site.test_count',
  caseCount:         'site.case_count',
  expertCount:       'site.expert_count',
  satisfaction:      'site.satisfaction',
  productCount:      'site.product_count',
  payPrice:          'pay.price',
  bankMentioned:     'site.bank_mentioned',
  brandName:         'site.brand_name',
  brandSlogan:       'site.brand_slogan',
  brandSubtitle:     'site.brand_subtitle',
  brandTagline:      'site.brand_tagline',
  brandOneLiner:     'site.brand_one_liner',
  ctaPersonal:       'site.cta_personal',
  ctaBusiness:       'site.cta_business',
  disclaimerShort:   'site.disclaimer_short',
  disclaimerLong:    'site.disclaimer_long',
  disclaimerFullReport: 'site.disclaimer_full_report',
  disclaimerPay:     'site.disclaimer_pay',
} as const

export type SiteKey = typeof SITE[keyof typeof SITE]

/** 从分组配置中取单个 key（前端 store 用） */
export function getConfigValue(config: SiteConfigGroup | null, key: string, fallback = ''): string {
  if (!config) return fallback
  return (
    config.number?.[key] ||
    config.text?.[key] ||
    config.compliance?.[key] ||
    config.other?.[key] ||
    fallback
  )
}

/** 数字格式化（128000 → "128,000+"） */
export function formatNumber(value: string, suffix = '+'): string {
  const n = parseInt(value, 10)
  if (isNaN(n)) return value
  return n.toLocaleString('en-US') + suffix
}
