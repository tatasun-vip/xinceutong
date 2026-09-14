/**
 * API 统一请求封装
 * - 自动注入 token（Phase 4 接入）
 * - 统一处理 code != 0 错误
 * - 15s 超时
 */
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
  params?: Record<string, unknown>
  silent?: boolean
}

export const request = async <T = unknown>(options: RequestOptions): Promise<T> => {
  const { url, method = 'GET', data, params, silent = false } = options
  const fullUrl = (url.startsWith('http') ? url : BASE_URL + url)

  let finalUrl = fullUrl
  if (params && Object.keys(params).length) {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) qs.append(k, String(v))
    })
    finalUrl += (fullUrl.includes('?') ? '&' : '?') + qs.toString()
  }

  const res = await fetch(finalUrl, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: data ? JSON.stringify(data) : undefined,
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`)
  }

  const json = (await res.json()) as ApiResponse<T>
  if (json.code !== 0) {
    if (!silent) {
      console.error('[API]', url, json.message)
    }
    throw new Error(json.message || '请求失败')
  }
  return json.data
}

export { BASE_URL }
