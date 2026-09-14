/**
 * types/index.ts - 全局 TypeScript 类型
 */

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export type UserRole = 'user' | 'promoter' | 'admin'
export type AssessmentType = 'personal' | 'business'
export type Level = 'S' | 'A' | 'B' | 'C' | 'D' | 'E'

export interface Product {
  name: string
  limit: string
  rate: string
  pass: '高' | '中高' | '中' | '低'
  recommend?: boolean
}

export interface FullReport {
  report_no: string
  score: number
  level: Level
  products: Product[]
  advantages: string[]
  weak_points: string[]
  suggestions: Array<{ period: string; action: string }>
  apply_strategy: string
  disclaimer: string
}
