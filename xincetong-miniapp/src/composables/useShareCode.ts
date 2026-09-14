/**
 * composables/useShareCode.ts - 解析分享码 / 推广码
 *
 * 用法：
 *   const { shareCode, promoterCode } = useShareCode()
 */
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getStorage, setStorage } from '@/utils/storage'

export function useShareCode() {
  const shareCode = ref<string>('')
  const promoterCode = ref<string>('')

  onLoad((options: Record<string, string> = {}) => {
    const sc = options.share_code || getStorage<string>('share_code', '')
    const pc = options.promoter_code || getStorage<string>('promoter_code', '')
    if (sc) {
      shareCode.value = sc
      setStorage('share_code', sc)
    }
    if (pc) {
      promoterCode.value = pc
      setStorage('promoter_code', pc)
    }
  })

  return { shareCode, promoterCode }
}
