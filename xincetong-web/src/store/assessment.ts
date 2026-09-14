import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 测评状态：动态 5 步表单数据（key 是动态字段名，存到 allInput 后转 input_data）
 */
export const useAssessmentStore = defineStore('assessment', () => {
  const allInput = ref<Record<string, unknown>>({})
  const currentStep = ref(0) // 0-indexed
  const bankCode = ref<string>('')
  // 测评结果（submit 返回的完整 result，用于 /result/:id 页面渲染）
  // 用 sessionStorage 持久化（避免 SPA 路由切换后丢失）
  const RESULT_KEY = 'xct_last_result'
  const result = ref<any>(loadResult())

  function loadResult(): any {
    try {
      const raw = sessionStorage.getItem(RESULT_KEY)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  function setResult(r: any) {
    result.value = r
    try {
      if (r) sessionStorage.setItem(RESULT_KEY, JSON.stringify(r))
    } catch {
      // sessionStorage 写失败（quota 等）— 不阻塞业务
    }
  }

  function setField(key: string, value: unknown) {
    allInput.value[key] = value
  }

  function setStep(step: number) {
    currentStep.value = step
  }

  function setBank(code: string) {
    bankCode.value = code
  }

  function reset() {
    allInput.value = {}
    currentStep.value = 0
    bankCode.value = ''
    result.value = null
    try {
      sessionStorage.removeItem(RESULT_KEY)
    } catch {
      // ignore
    }
  }

  const progress = computed(() => currentStep.value + 1)

  return {
    allInput,
    currentStep,
    bankCode,
    result,
    progress,
    setField,
    setStep,
    setBank,
    setResult,
    reset,
  }
})
