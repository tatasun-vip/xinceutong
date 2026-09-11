/**
 * api/auth.ts - 认证相关
 */
import http from './request'
import { useUserStore } from '@/store/user'

/** 微信登录：code 换 token */
export function loginByWechat(code: string) {
  return http.post<{ token: string; user: any }>('/api/auth/wechat-login', { code })
}

/** 获取当前用户 */
export function getProfile() {
  return http.get<any>('/api/auth/profile')
}

/** 用户授权推广员查看报告 */
export function grantToPromoter(promoterId: number) {
  return http.post('/api/auth/grant', { promoter_id: promoterId })
}

/** 查询授权状态 */
export function getGrantStatus(promoterId: number) {
  return http.get('/api/auth/grant-status', { promoter_id: promoterId })
}

/** 申请删除用户数据（合规） */
export function deleteUserData() {
  return http.post('/api/user/delete-data')
}

/** 调用 wx.login 走完整登录流程 */
export function doLogin(silent = false): Promise<{ token: string; user: any }> {
  return new Promise((resolve, reject) => {
    uni.login({
      success: async ({ code }) => {
        if (!code) return reject(new Error('uni.login 未拿到 code'))
        try {
          const data = await loginByWechat(code)
          if (data?.token) {
            const userStore = useUserStore()
            userStore.setLogin(data.token, data.user)
            resolve(data)
          } else {
            reject(new Error('登录响应异常'))
          }
        } catch (e) {
          if (!silent) console.error('登录失败', e)
          reject(e)
        }
      },
      fail: reject,
    })
  })
}

/** 自动确保登录 */
export async function ensureLogin(): Promise<string> {
  const userStore = useUserStore()
  if (userStore.token) return userStore.token
  return (await doLogin(true)).token
}
