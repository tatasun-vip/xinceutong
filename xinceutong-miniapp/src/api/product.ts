/**
 * api/product.ts - 6 大产品类型
 */
import http from './request'

export interface ProductType {
  id: number
  code: string
  name: string
  subtitle: string
  user_type: 'personal' | 'business'
  limit_formula: string
  rate_min: number
  rate_max: number
  default_pass: string
  focus_vars: string[]
  key_points: string[]
  description: string
  recommend: number
  sort_order: number
}

/** 获取所有产品类型（按 user_type 过滤可选） */
export function getProductTypes(userType?: 'personal' | 'business') {
  const url = userType
    ? `/api/product-types?user_type=${userType}`
    : '/api/product-types'
  return http.get<ProductType[]>(url)
}

/** 按 code 查单个产品类型 */
export function getProductTypeByCode(code: string) {
  return http.get<ProductType & { found: boolean }>(`/api/product-types/${code}`)
}
