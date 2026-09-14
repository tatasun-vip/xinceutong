import { request } from './request'

export interface SubmitAssessmentPayload {
  type?: 'personal' | 'business'
  input_data: Record<string, unknown>
  bank_code?: string
  share_code?: string
  promoter_code?: string
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
export interface FreeResult {
  assessment_id: number
  report_no: string
  bank_code?: string
  bank_name?: string
  bank_focus?: string
  bank_key_tags?: string[]
  overall: { score: number; level: string; limit_min?: number; limit_max?: number; rate_min?: number; rate_max?: number; pass_probability?: string }
  free_summary?: string
  is_paid: boolean
  one_sentence?: string
  top_issue_free?: any
  top_issues_total?: number
  improvement_projection?: any
  product_results?: any[]
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
