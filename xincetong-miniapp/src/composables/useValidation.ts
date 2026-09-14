/**
 * useValidation - 实时纠错（防抖调 /api/assessment/validate）
 *
 * 用法：
 *   const { items, hasError, hasWarning, validating, runValidation } = useValidation()
 *   watch(formData, () => runValidation({ step: 1, data: formData, type: 'personal' }))
 *
 * 后端返回：
 *   { valid, items: [{rule_name, level, message}], has_warning, has_error }
 */
import { ref } from 'vue'
import { assessmentApi } from '@/api'
import { useDebounce } from './useDebounce'

export interface ValidationItem {
  rule_name: string
  level: 'info' | 'warning' | 'error'
  message: string
}

export function useValidation() {
  const items = ref<ValidationItem[]>([])
  const hasError = ref(false)
  const hasWarning = ref(false)
  const validating = ref(false)

  /** 同步执行纠错（内部用） */
  async function doValidate(payload: {
    step: number
    data: Record<string, unknown>
    type: 'personal' | 'business'
    prevData?: Record<string, unknown>
  }) {
    if (validating.value) return
    validating.value = true
    try {
      const res = await assessmentApi.validateAssessment({
        step: payload.step,
        data: payload.data,
        prevData: payload.prevData,
        type: payload.type,
      })
      items.value = res.items || []
      hasError.value = res.has_error
      hasWarning.value = res.has_warning
    } catch (e) {
      // 静默失败（断网时只清空，不弹 toast）
      items.value = []
      hasError.value = false
      hasWarning.value = false
    } finally {
      validating.value = false
    }
  }

  /** 对外暴露的防抖版本（400ms） */
  const runValidation = useDebounce(doValidate, 400)

  /** 清空纠错结果（用户切走 / 跳页时调用） */
  function clear() {
    items.value = []
    hasError.value = false
    hasWarning.value = false
  }

  return { items, hasError, hasWarning, validating, runValidation, clear }
}
