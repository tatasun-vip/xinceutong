import { request } from './request'

export type BankType = 'state_owned' | 'joint_stock' | 'internet' | 'policy' | 'city_commercial'

export interface Bank {
  id: number
  code: string
  name: string
  short_name: string
  en_name: string | null
  type: BankType
  logo_url: string | null
  short_desc: string | null
  slogan: string | null
  brand_color: string | null
  features: string[]
  description?: string
}

export interface FormFieldOption {
  value: string | number
  label: string
}

export interface FormField {
  key: string
  label: string
  type: 'text' | 'number' | 'select' | 'radio' | 'checkbox' | 'slider' | 'date' | 'textarea'
  required: boolean
  options?: FormFieldOption[]
  min?: number
  max?: number
  step?: number
  unit?: string
  placeholder?: string
  default?: unknown
}

export interface FormStep {
  step_no: number
  step_title: string
  step_subtitle: string | null
  step_label: string | null
  fields: FormField[]
}

export interface BankSchema {
  bank_code: string
  bank_name: string
  total_steps: number
  steps: FormStep[]
}

export interface BankProduct {
  id: number
  name: string
  subtitle: string | null
  limit_min: number   // 万元
  limit_max: number
  rate_min: number
  rate_max: number
  pass_score_min: number
  pass_score_max: number
  features: string[]
  requirement: string | null
  recommend: boolean
}

export const bankApi = {
  /** 银行列表 */
  list: (type?: BankType) => request<{ total: number; items: Bank[] }>({
    url: '/api/banks',
    params: type ? { type } : undefined,
  }),

  /** 银行详情 */
  detail: (code: string) => request<Bank>({
    url: `/api/banks/${code}`,
  }),

  /** 表单 schema */
  schema: (code: string) => request<BankSchema>({
    url: `/api/banks/${code}/schema`,
  }),

  /** 推荐产品 */
  products: (code: string) => request<{ total: number; items: BankProduct[]; bank_name: string; bank_code: string }>({
    url: `/api/banks/${code}/products`,
  }),
}
