import { useAssessmentStore } from '@/store/assessment'

/**
 * "返回首页/退出测评"通用逻辑
 * - 弹确认（防误触）
 * - 二次确认：保留草稿 or 清空重填
 * - 跳回首页（reLaunch 而不是 redirectTo —— 防止被 stepGuard 守卫回原地）
 */
export function useExitConfirm() {
  const store = useAssessmentStore()

  function exit() {
    uni.showActionSheet({
      itemList: ['保存草稿并返回首页', '清空全部数据并返回首页', '继续填写'],
      success: (r) => {
        if (r.tapIndex === 0) {
          // 保存草稿（已经在 watch 里持续 setStep4，store 是最新的）
          uni.reLaunch({ url: '/pages/index/index' })
        } else if (r.tapIndex === 1) {
          uni.showModal({
            title: '清空草稿',
            content: '本次已填写的内容将全部清空，确定吗？',
            confirmText: '清空',
            confirmColor: '#c0392b',
            success: (m) => {
              if (m.confirm) {
                try { store.reset() } catch (e) { console.error('[exit] reset err', e) }
                uni.reLaunch({ url: '/pages/index/index' })
              }
            }
          })
        }
        // r.tapIndex === 2: 继续填写，啥也不做
      }
    })
  }

  return { exit }
}
