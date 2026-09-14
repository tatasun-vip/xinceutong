/**
 * api/promoter.ts - 推广员
 */
import http from './request'

/** 申请入驻 */
export function applyPromoter(data: {
  real_name: string
  id_card: string
  org_name?: string
  city: string
  years: number
}) {
  return http.post('/api/promoter/apply', data)
}

/** 工作台 */
export function getDashboard() {
  return http.get<{
    today: { clicks: number; assessments: number; payments: number; earnings: number }
    total: { customers: number; earnings: number }
    new_today: any[]
  }>('/api/promoter/dashboard')
}

/** 推广工具（链接/二维码/海报） */
export function getTools() {
  return http.get<{
    share_link: string
    qrcode_url: string
    poster_url: string
    moments_copy: string[]
    group_copy: string[]
  }>('/api/promoter/tools')
}

/** 设置专属价格（6.99 ~ 19.99） */
export function setPrice(custom_price: number) {
  return http.post('/api/promoter/price', { custom_price })
}

/** 客户列表 */
export function getCustomers(params?: { sort?: string; tag?: string; page?: number }) {
  return http.get<{ list: any[]; total: number }>('/api/promoter/customers', params)
}

/** 客户详情 */
export function getCustomerDetail(id: number) {
  return http.get<any>(`/api/promoter/customer/${id}`)
}

/** 分佣明细 */
export function getCommissions(params?: { status?: string; page?: number }) {
  return http.get<{ list: any[]; total: number }>('/api/promoter/commissions', params)
}

/** 提现申请 */
export function withdraw(data: { amount: number; channel: 'wxpay' | 'bank' }) {
  return http.post('/api/promoter/withdraw', data)
}

/** 跟进记录 */
export function followUp(data: {
  customer_id: number
  method: 'phone' | 'wechat' | 'meeting'
  content: string
  next_step: string
  status: 'pending' | 'contacted' | 'interested' | 'closed' | 'abandoned'
}) {
  return http.post('/api/promoter/follow-up', data)
}
