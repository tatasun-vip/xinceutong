/**
 * api/bank.ts - 银行 + 银行产品 API
 */
import http from './request'

// ============ 类型 ============

export type BankType = 'state_owned' | 'joint_stock' | 'internet' | 'policy' | 'city_commercial'

export interface Bank {
  id: number
  code: string
  name: string
  short_name: string
  en_name?: string
  type: BankType
  logo_url?: string
  short_desc?: string
  slogan?: string
  brand_color?: string
  features: string[]
  description?: string
}

export interface BankProduct {
  id: number
  name: string
  subtitle?: string
  limit_min: number   // 万元
  limit_max: number
  rate_min: number    // 利率参考（%）
  rate_max: number
  pass_score_min: number
  pass_score_max: number
  features: string[]
  requirement?: string
  recommend: boolean
  /**
   * 适用用户类型：personal / business（v5 增量字段）
   * 当前后端 BankProduct 表未持久化此字段，前端会传 ?user_type= 过滤参数
   * 后端后续会加 alembic 迁移 + 重新 seed（独立 feature，单独立项）
   */
  user_type?: 'personal' | 'business'
}

export interface FormField {
  key: string
  label: string
  type: 'number' | 'select' | 'radio' | 'slider' | 'text'
  required: boolean
  hint?: string
  options?: Array<{ value: string; label: string; desc?: string }>
  min?: number
  max?: number
  step?: number
  unit?: string
  placeholder?: string
}

export interface FormStep {
  step_no: number
  step_title: string
  step_subtitle?: string
  step_label?: string
  fields: FormField[]
}

export interface FormSchema {
  bank_code: string
  bank_name: string
  total_steps: number
  steps: FormStep[]
}

// ============ API ============

/** 银行列表（可选按 type 过滤） */
export function listBanks(type?: BankType) {
  const url = type ? `/api/banks?type=${type}` : '/api/banks'
  return http.get<{ total: number; items: Bank[] }>(url)
}

/** 银行详情 */
export function getBank(code: string) {
  return http.get<Bank>(`/api/banks/${code}`)
}

/** 银行表单 schema（5 步） */
export function getBankSchema(code: string) {
  return http.get<FormSchema>(`/api/banks/${code}/schema`)
}

/** 银行推荐产品（可选按 user_type 过滤：personal / business） */
export function getBankProducts(code: string, userType?: 'personal' | 'business') {
  const url = userType
    ? `/api/banks/${code}/products?user_type=${userType}`
    : `/api/banks/${code}/products`
  return http.get<{ bank_code: string; bank_name: string; total: number; items: BankProduct[] }>(url)
}
