/**
 * store/promoter.ts - 推广员 store
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { setStorage, getStorage } from '@/utils/storage'

export interface PromoterInfo {
  id: number
  user_id: number
  real_name: string
  org_name?: string
  city: string
  status: 'pending' | 'approved' | 'rejected' | 'banned'
  commission_rate: number
  custom_price: number
  total_earnings: number
  balance: number
}

const KEY = 'promoter_info'

export const usePromoterStore = defineStore('promoter', () => {
  const info = ref<PromoterInfo | null>(null)

  function setInfo(p: PromoterInfo | null) {
    info.value = p
    if (p) setStorage(KEY, p)
  }

  function restoreFromStorage() {
    const p = getStorage<PromoterInfo>(KEY)
    if (p) info.value = p
  }

  function isApproved() { return info.value?.status === 'approved' }

  return { info, setInfo, restoreFromStorage, isApproved }
})
