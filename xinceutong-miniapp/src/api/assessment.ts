/**
 * api/assessment.ts - 测评相关（v3: 6 大产品独立建模）
 */
import http from './request'

// ============================================================================
// 实时纠错
// ============================================================================

export interface ValidationReq {
  step: number
  data: Record<string, unknown>
  type: 'personal' | 'business'
  prevData?: Record<string, unknown>
}
export interface ValidationItem {
  rule_name: string
  level: 'info' | 'warning' | 'error'
  message: string
}
export interface ValidationRes {
  valid: boolean
  items: ValidationItem[]
  has_warning: boolean
  has_error: boolean
}

export function validateAssessment(data: ValidationReq) {
  return http.post<ValidationRes>('/api/assessment/validate', data)
}

// ============================================================================
// 提交测评（v3: 6 大产品独立测算）
// ============================================================================

export interface SubmitReq {
  type: 'personal' | 'business'
  input_data: Record<string, unknown>
  share_code?: string
  promoter_code?: string
}

export interface OverallScore {
  score: number
  level: string
  limit_min: number
  limit_max: number
  rate_min: number
  rate_max: number
  pass_probability: string
}

export interface ProductResult {
  product_code: string
  product_name: string
  product_subtitle: string
  limit_min: number
  limit_max: number
  rate_min: number
  rate_max: number
  pass_probability: string
  level: string
  /**
   * P2 渠道合规字段（线上/线下硬上限）
   *   - channel_online_max:  线上渠道最高可申请额度（元）
   *   - channel_offline_max: 线下渠道最高可申请额度（元）
   *   - limit_capped:        测算值是否被渠道 cap 了
   *   - limit_reason:        cap 原因（生成给用户看）
   */
  channel_online_max?: number
  channel_offline_max?: number
  limit_capped?: boolean
  limit_reason?: string
  /**
   * 产品维度的"是否推荐展示"标志（DB 静态配置，用于产品介绍页/营销高亮）
   */
  recommend: boolean
  /**
   * 用户维度的"当前最适合该用户"标志（动态计算：score 最高且非 E/极低）
   * 报告页 ⭐ 标签用这个，避免出现"⭐ + 通过率极低"这种自相矛盾
   */
  best_for_user?: boolean
}

/**
 * v3.2 核心问题（按严重度排序，最多 3 个）
 * 5 维度展开：是什么/为什么/影响/怎么改/预期
 */
export interface TopIssue {
  id: number
  title: string
  category: '征信' | '收入' | '资产' | '基础' | '申请策略'
  severity: 'high' | 'mid' | 'low'
  severity_color: string
  impact_prob: string     // 通过概率影响
  impact_amount: string   // 额度影响
  impact_rate: string     // 利率影响
  what: string            // 是什么
  why: string             // 为什么是问题
  how: string             // 怎么改善
  when: string            // 多久见效
  result: string          // 改善后预期
  fixable_in_90d: boolean // 90 天内能否改善
}

/**
 * v3.2 改善后推演
 * 按建议执行 90 天后的预测评分/额度/通过率
 */
export interface ImprovementProjection {
  score: number
  level: string
  limit_min: number
  limit_max: number
  pass_probability: string
  pass_rank: number
  period_days: number
  fixed_count: number     // 修复了多少个问题
}

export interface SubmitRes {
  assessment_id: number
  report_no: string
  overall: OverallScore
  free_summary: string
  product_results: ProductResult[]   // 免费版 6 个产品摘要
  is_paid: boolean
  paid_at: string | null
  veto_count: number
  // v3.2 新增
  one_sentence: string
  top_issue_free: TopIssue | null
  top_issues_total: number
  projection: ImprovementProjection | null
}

export function submitAssessment(data: SubmitReq) {
  return http.post<SubmitRes>('/api/assessment/submit', data)
}

// ============================================================================
// 免费结果
// ============================================================================

export interface FreeResultRes {
  assessment_id: number
  report_no: string
  overall: OverallScore
  free_summary: string
  product_results: ProductResult[]
  is_paid: boolean
  created_at: string
  // v3.2 新增
  one_sentence?: string
  top_issue_free?: TopIssue | null
  top_issues_total?: number
  improvement_projection?: ImprovementProjection | null
}

export function getFreeResult(id: number) {
  return http.get<FreeResultRes>(`/api/assessment/free/${id}`)
}

// ============================================================================
// 完整报告（付费后）
// ============================================================================

export interface ProductResultDetail extends ProductResult {
  formula_used: string
  focus_vars: string[]
  key_points: string[]
  description: string
  matched_items: Array<{ category: string; variable: string; option_label: string; score: number }>
  risk_tags: string[]
  advantages: string[]
  weak_points: string[]
}

/**
 * 5 大维度评分（基础/职业/收入/资产/征信）
 * ratio 0-100 的完成度，level: strong/mid/weak，low: 是否需要重点改善
 */
export interface CategoryScore {
  label: string
  raw: number
  max: number
  ratio: number
  level: 'strong' | 'mid' | 'weak'
  low: boolean
  items: number
}

export interface FullReportRes {
  report_no: string
  is_paid: boolean
  paid_at: string | null
  overall: OverallScore
  category_scores?: Record<string, CategoryScore>
  product_results: ProductResultDetail[]
  product_results_preview?: ProductResultDetail[]
  product_results_locked?: ProductResultDetail[]
  advantages: string[]
  weak_points: string[]
  risk_tags: string[]
  /**
   * 改善建议（基于该银行模型 + 用户实际数据生成）
   * period: 立即 / 1-3 个月 / 3-6 个月 / 6 个月+ / 持续
   * action: 具体行动
   * reason: 为什么这样做（基于该行模型）
   * source: 所属维度（征信修复 / 收入证明 / 资产配置 / 申请策略 / 日常习惯）
   */
  suggestions: Array<{ period: string; action: string; reason: string; source: string }>
  /**
   * 付费页用的"建议预览"：第 1 条完整 + 2 条占位
   */
  suggestions_preview?: Array<{ period: string; action: string; source: string }>
  suggestions_locked_count?: number
  suggestions_total_count?: number
  apply_strategy: string
  disclaimer: string
  message?: string
  // v3.2 新增
  one_sentence?: string
  top_issues?: TopIssue[]
  improvement_projection?: ImprovementProjection | null
}

export function getFullReport(id: number) {
  return http.get<FullReportRes>(`/api/assessment/report/${id}`)
}
