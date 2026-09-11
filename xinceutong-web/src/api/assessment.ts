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

export const assessmentApi = {
  submit: (payload: SubmitAssessmentPayload) => request<AssessmentResult>({
    url: '/api/assessment/submit',
    method: 'POST',
    data: payload,
  }),
}
