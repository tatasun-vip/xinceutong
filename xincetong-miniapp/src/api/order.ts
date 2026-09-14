/**
 * api/order.ts - 订单 / 支付（v3: mock 支付 + 9.99 解锁）
 */
import http from './request'

export interface CreateOrderReq {
  assessment_id: number
  promoter_code?: string
}
export interface CreateOrderRes {
  order_no: string
  amount: number
  status: 'pending' | 'paid' | 'refunded' | 'failed'
  base_price: number
  markup: number
}

/** 创建订单 */
export function createOrder(data: CreateOrderReq) {
  return http.post<CreateOrderRes>('/api/order/create', data)
}

/** 模拟支付（点解锁按钮直接调用，UI 联调阶段使用） */
export function mockPay(orderNo: string) {
  return http.post<{
    order_no: string
    status: 'paid'
    paid_at: string
    message: string
  }>(`/api/order/mock-pay/${orderNo}`, {})
}

/** 查询订单状态 */
export function getOrderStatus(orderNo: string) {
  return http.get<{
    order_no: string
    status: string
    amount: number
    paid_at: string | null
  }>(`/api/order/status/${orderNo}`)
}
