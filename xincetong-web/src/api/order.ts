import { request } from './request'

export interface CreateOrderRes {
  order_no: string
  amount: number
  base_price: number
  markup: number
  status: string
}

export const orderApi = {
  create: (assessmentId: number, promoterCode?: string) =>
    request.post<any, CreateOrderRes>('/order/create', { assessment_id: assessmentId, promoter_code: promoterCode || undefined }),
  mockPay: (orderNo: string) => request.post<any, { order_no: string; status: string }>(`/order/mock-pay/${orderNo}`),
  status: (orderNo: string) => request.get<any, { order_no: string; status: string; amount: number }>(`/order/status/${orderNo}`),
  fullReport: (assessmentId: number) => request.get<any, any>(`/assessment/report/${assessmentId}`),
  // v6 一致性
  compareSnapshot: (assessmentId: number) => request.get<any, any>(`/assessment/compare-snapshot/${assessmentId}`),
}
