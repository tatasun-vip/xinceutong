import { request } from './request'

export interface SubmitAssessmentPayload {
  type?: 'personal' | 'business'
  input_data: Record<string, unknown>
  bank_code?: string
  share_code?: string
  promoter_code?: string
}

/** v9 增量：单产品独立结果（6 大产品类型） */
export interface ProductResult {
  product_code: string
  product_name: string
  product_subtitle?: string
  level: 'S' | 'A' | 'B' | 'C' | 'D' | 'E'
  score: number
  pass_probability?: string
  limit_min?: number
  limit_max?: number
  /** 实际可贷金额（按本产品等级折扣后） */
  realistic_limit_min?: number
  realistic_limit_max?: number
  /** 命中加分规则 top 3 */
  hit_rules?: Array<{ rule: string; score: number }>
  /** 命中扣分规则 top 3 */
  low_rules?: Array<{ rule: string; score: number }>
  /** 不推荐原因（1-2 句） */
  not_recommend_reason?: string
  /** 提分变量 top 3 */
  improve_vars?: Array<{ current: string; best: string; delta: number }>
  /**
   * v22+ 增量：基于 narrative SSOT 派生的"改善建议 hint"
   *   - 来源：improve_vars top 1 → 口语化总结
   *   - 与 not_recommend_reason 互补：前者"为什么不能办"，后者"如何能办"
   *   - D/C 级会填充；S/A/B 级留空（无需给改善建议）
   */
  improve_hint?: string
}

export interface AssessmentResult {
  assessment_id: number
  report_no: string
  score: number
  level: 'S' | 'A' | 'B' | 'C' | 'D' | 'E'
  limit_min: number
  limit_max: number
  rate_min: number
  rate_max: number
  pass_probability: string
  free_summary: string
  is_paid: boolean
  risk_tags: string[]
  advantages: string[]
  weak_points: string[]
  products_preview: Array<{ name: string; recommend: boolean }>
  veto: { rule_variable: string; rule_label: string; message: string } | null
}

/**
 * v9 增量：直接 URL /result/:id 访问需要
 * 1) 拉取 free 视图（带 bank_code）
 * 2) 已付费时拉取 report 视图（含完整证据链）
 * 兜底：分享链接/直接刷新场景
 */
export interface TopIssue {
  severity?: 'high' | 'mid' | 'low'
  severity_color?: string
  category?: string
  title: string
  what?: string
  why?: string
  impact_prob?: string
  impact_amount?: string
  impact_rate?: string
  how?: string
}

export interface ImprovementProjection {
  level: string
  score: number
  pass_probability?: string
  fixed_count?: number
  limit_min?: number
  limit_max?: number
}

export interface FreeResult {
  assessment_id: number
  report_no: string
  bank_code?: string
  bank_name?: string
  bank_focus?: string
  bank_key_tags?: string[]
  overall: {
    score: number
    level: string
    limit_min?: number
    limit_max?: number
    rate_min?: number
    rate_max?: number
    pass_probability?: string
    // v23.2 增量：LEVEL_NARRATIVE SSOT 结构化字段
    verdict?: string
    recommendation?: string
    cta?: string
    pass_probability_desc?: string
    rate_description?: string
  }
  free_summary?: string
  is_paid: boolean
  one_sentence?: string
  /** 最高严重度问题（免费版只露 1 个） */
  top_issue_free?: TopIssue
  /** top_issues 总数（用于 1/N 锁） */
  top_issues_total?: number
  /** 改善后推演（修复后可达等级） */
  improvement_projection?: ImprovementProjection
  /** 6 大产品独立结果（v9 增量） */
  product_results?: ProductResult[]
  /** 6 大产品 evidence 索引（v9 增量，O(1) 取值） */
  product_breakdown?: Record<string, ProductResult>
  projection_table?: any[]
  product_matches?: any[]
  ui_config?: any
  data_hash?: string
  created_at?: string
}

export const assessmentApi = {
  submit: (payload: SubmitAssessmentPayload) => request<AssessmentResult>({
    url: '/api/assessment/submit',
    method: 'POST',
    data: payload,
  }),
  /** 拉取 free 视图（含 bank_code，供 Result.vue 反查银行详情用） */
  getFree: (id: number | string) => request<{ data: FreeResult }>({
    url: `/api/assessment/free/${id}`,
    method: 'GET',
  }),
  /** 已付费时拉取 report 视图（含完整证据链 hit_rules/low_rules/improve_vars 等） */
  getReport: (id: number | string) => request<{ data: any }>({
    url: `/api/assessment/report/${id}`,
    method: 'GET',
  }),
}
