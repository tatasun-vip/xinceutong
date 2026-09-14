/**
 * useStepGuard - 5 步填写流程的路由守卫
 *
 * 规则：
 *  - type 页可自由进入
 *  - step1 进入：必无（直接进入）
 *  - step2 进入：必填完 step1
 *  - step3 进入：必填完 step1+2
 *  - step4 进入：必填完 step1+2+3
 *  - step5 进入：必填完 step1+2+3+4
 *  - loading 进入：必填完 5 步
 *
 * 用法（在 onLoad 顶部）：
 *   useStepGuard(2)   // 进入 step2 前先校验 step1
 *   useStepGuard(5, { requiresAll: true })  // step5 需要 4 步都填完
 */
import { onLoad } from '@dcloudio/uni-app'
import { useAssessmentStore } from '@/store/assessment'

export interface StepGuardOptions {
  /** true 表示所有前置步骤都必填 */
  requiresAll?: boolean
}

export function useStepGuard(targetStep: number, options: StepGuardOptions = {}) {
  const store = useAssessmentStore()
  const requiresAll = options.requiresAll ?? true

  onLoad(() => {
    if (targetStep <= 1) return

    if (requiresAll) {
      for (let i = 1; i < targetStep; i++) {
        if (!isStepCompleted(store, i)) {
          // 软提示：toast 一下，不强制跳回
          // 原因：全链都是 redirectTo，栈里没有首页，强制跳回会让用户感觉"莫名返回"
          // 真正落地由各步 goNext 在跳转前同步 setStepX（修竞态）+ canNext 守卫（防漏填）
          uni.showToast({ title: `请补完第 ${i} 步`, icon: 'none' })
          return
        }
      }
    } else {
      // 非必填：只检查紧邻上一步
      if (!isStepCompleted(store, targetStep - 1)) {
        uni.showToast({ title: `请补完第 ${targetStep - 1} 步`, icon: 'none' })
        // 不强制 redirectTo：让用户在当前页补完（与 requiresAll 策略一致）
      }
    }
  })
}

function isStepCompleted(store: ReturnType<typeof useAssessmentStore>, step: number): boolean {
  switch (step) {
    case 1: return !!store.step1 && Object.keys(store.step1).length >= 4
    case 2: return !!store.step2 && Object.keys(store.step2).length >= 6
    case 3:
      // 关键修复：business 时 case 3 检查的是企业专属 step1B（v5: 15 个字段），不是 step3 资产
      // 否则 business 用户手动改 URL 跳过 step1b-business 后，前置校验完全失效
      if (store.type === 'business') {
        return !!store.step1B && Object.keys(store.step1B).length >= 15
      }
      return !!store.step3 && Object.keys(store.step3).length >= 4
    case 4: return !!store.step4 && Object.keys(store.step4).length >= 9
    case 5: return isStepCompleted(store, 4)
    default: return false
  }
}

export function stepPageUrl(step: number): string {
  switch (step) {
    case 1: return '/pages/assess/step1-basic'
    case 2: return '/pages/assess/step2-career'
    case 3: return '/pages/assess/step3-asset'
    case 4: return '/pages/assess/step4-credit'
    case 5: return '/pages/assess/step5-confirm'
    default: return '/pages/assess/type'
  }
}
