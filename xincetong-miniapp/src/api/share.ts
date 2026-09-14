/**
 * api/share.ts - 分享 / 免费体验
 */
import http from './request'

/** 生成分享码 + 海报 */
export function generateShare() {
  return http.post<{ share_code: string; poster_url: string }>('/api/share/generate')
}

/** 校验分享码 */
export function checkShare(code: string) {
  return http.get<{
    valid: boolean
    sharer_id: number
    sharer_name: string
    remaining_quota: number
  }>(`/api/share/check/${code}`)
}
