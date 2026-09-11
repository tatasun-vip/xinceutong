/**
 * store/user.ts - Pinia 用户 store（持久化到 uni.storage）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setStorage, getStorage, removeStorage } from '@/utils/storage'

export type UserRole = 'user' | 'promoter' | 'admin'

export interface UserInfo {
  id: number
  openid: string
  nickname?: string
  avatar?: string
  role: UserRole
  promoter_id?: number
}

const TOKEN_KEY = 'token'
const USER_INFO_KEY = 'userInfo'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)

  const role = computed<UserRole>(() => userInfo.value?.role || 'user')
  const isLogin = computed(() => !!token.value)

  function setLogin(t: string, user?: UserInfo) {
    token.value = t
    userInfo.value = user || null
    setStorage(TOKEN_KEY, t)
    if (user) setStorage(USER_INFO_KEY, user)
  }

  function setUserInfo(user: UserInfo) {
    userInfo.value = user
    setStorage(USER_INFO_KEY, user)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    removeStorage(TOKEN_KEY)
    removeStorage(USER_INFO_KEY)
  }

  function restoreFromStorage() {
    const t = getStorage<string>(TOKEN_KEY)
    const u = getStorage<UserInfo>(USER_INFO_KEY)
    if (t) token.value = t
    if (u) userInfo.value = u
  }

  function isPromoter() { return role.value === 'promoter' }
  function isAdmin()    { return role.value === 'admin' }

  return { token, userInfo, role, isLogin,
           setLogin, setUserInfo, logout, restoreFromStorage,
           isPromoter, isAdmin }
})
