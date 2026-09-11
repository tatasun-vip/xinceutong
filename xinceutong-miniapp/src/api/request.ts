/**
 * api/request.ts - 统一请求封装
 * - 自动注入 JWT（Authorization: Bearer <token>）
 * - 401 自动登出
 * - 统一处理 code != 0
 * - 15s 超时
 * - TypeScript 泛型
 */
import { useUserStore } from '@/store/user'

// 同源部署：留空，浏览器自动用当前域名拼 /api/banks
// 如需跨域，在 vite.config.ts 的 define 中注入 VITE_API_BASE_URL
const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || ''

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: unknown
  showLoading?: boolean
  silent?: boolean
}

export const request = <T = unknown>(options: RequestOptions): Promise<T> => {
  const userStore = useUserStore()
  return new Promise((resolve, reject) => {
    if (options.showLoading) uni.showLoading({ title: '加载中' })

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        'Authorization': userStore.token ? `Bearer ${userStore.token}` : '',
      },
      timeout: 15000,
      success: (res: any) => {
        const { statusCode, data } = res
        if (statusCode === 401) {
          userStore.logout()
          // 不强制跳转首页（部分公开 API 误判 401 也会跳走，破坏用户体验）
          // 改为抛出错误让调用方决定
          uni.showToast({ title: '请先登录', icon: 'none' })
          reject(Object.assign(new Error('未登录'), { statusCode: 401, needLogin: true }))
          return
        }
        if (statusCode !== 200) {
          if (!options.silent) uni.showToast({ title: `请求失败 (${statusCode})`, icon: 'none' })
          reject(Object.assign(new Error(`HTTP ${statusCode}`), { statusCode }))
          return
        }
        const body = data as ApiResponse<T>
        if (body.code !== 0) {
          if (!options.silent) uni.showToast({ title: body.message || '请求失败', icon: 'none' })
          reject(Object.assign(new Error(body.message || '请求失败'), { code: body.code, body }))
          return
        }
        resolve(body.data)
      },
      fail: (err) => {
        const msg = (err && (err.errMsg || err.message)) || '网络异常'
        // 常见：request:fail abort（被 HMR 打断）、request:fail timeout（15s）、request:fail CORS
        const short = msg.length > 24 ? msg.slice(0, 24) + '…' : msg
        if (!options.silent) uni.showToast({ title: `网络异常（${short}）`, icon: 'none', duration: 3000 })
        // err 在 h5 中可能是 TypeError（fetch 跨域/CORS 失败）
        reject(Object.assign(new Error('网络异常'), { networkError: true, original: err }))
      },
      complete: () => {
        if (options.showLoading) uni.hideLoading()
      },
    })
  })
}

export const http = {
  get:    <T = unknown>(url: string, data?: unknown, opts?: Partial<RequestOptions>) => request<T>({ url, method: 'GET',    data, ...opts }),
  post:   <T = unknown>(url: string, data?: unknown, opts?: Partial<RequestOptions>) => request<T>({ url, method: 'POST',   data, ...opts }),
  put:    <T = unknown>(url: string, data?: unknown, opts?: Partial<RequestOptions>) => request<T>({ url, method: 'PUT',    data, ...opts }),
  delete: <T = unknown>(url: string, data?: unknown, opts?: Partial<RequestOptions>) => request<T>({ url, method: 'DELETE', data, ...opts }),
}

export { BASE_URL }
export default http
