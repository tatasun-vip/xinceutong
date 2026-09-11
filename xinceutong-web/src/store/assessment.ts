import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 测评状态：动态 5 步表单数据（key 是动态字段名，存到 allInput 后转 input_data）
 */
export const useAssessmentStore = defineStore('assessment', () => {
  const allInput = ref<Record<string, unknown>>({})
  const currentStep = ref(0) // 0-indexed
  const bankCode = ref<string>('')

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
  }

  const progress = computed(() => currentStep.value + 1)

  return {
    allInput,
    currentStep,
    bankCode,
    progress,
    setField,
    setStep,
    setBank,
    reset,
  }
})
