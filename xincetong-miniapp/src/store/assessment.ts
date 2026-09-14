/**
 * store/assessment.ts - 测评草稿（5 步填写跨步骤共享 + 持久化）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setStorage, getStorage, removeStorage } from '@/utils/storage'

export type AssessmentType = 'personal' | 'business'

export interface Step1 { age: number; education: string; marriage: string; city: string; city_tier: string; residence: string; cmb_zdl_score?: string | number }
export interface Step2 { company_type: string; work_years: string; monthly_income: string; social_security: string; housing_fund: string; payroll: string }
/**
 * v5 P0 补全：business 类型的企业变量（与后端 init_business_v5_rules.py 对齐）
 * 7 个 v4 字段 + 8 个 v5 新字段 = 15 个企业变量
 * type=business 时此步骤插入到 step2 之后、step3 之前
 */
export interface Step1B {
  // v4 字段（7 个，保留兼容）
  tax_grade: string
  annual_tax: string
  tax_continuity: string
  business_years: string
  annual_invoice: string
  invoice_continuity: string
  industry: string
  // v5 新字段（8 个：法人画像 2 + 企业画像 5 + 合规风险 1）
  legal_form: string
  legal_holding: string
  employee_count: string
  biz_balance: string
  biz_loan_count: string
  biz_overdue_2y: string
  biz_query_3m: string
  compliance_risk: string
}
export interface Step3 { house: string; car: string; insurance: string; deposit: string; mortgage_balance?: string }
export interface Step4 { credit_card_count: string; credit_card_usage: string; loan_count: string; loan_types: string[]; recent_3month_queries: string; recent_6month_queries: string; overdue_2year: string; serial_overdue: string; current_overdue: string; white_account: string; bad_status: string }
/**
 * v4 P0 补全：线下辅助资料（5 类全选填，不参与评分；仅用于人工对接参考）
 * 字段语义：
 *   - docs: 勾选的资料 key 列表（如 ['house_cert', 'car_cert']）
 *   - images: 每个 key 对应的本地临时路径（uni.chooseImage 返回）
 *   - note: 备注（最多 200 字）
 */
export interface Step4Docs { docs: string[]; images: Record<string, string>; note: string }

const STORE_KEY = 'assessment_draft'
const HISTORY_KEY = 'assessment_history'
const HISTORY_MAX = 50  // 本地最多保留 50 条历史记录

/**
 * 历史记录条目（提交成功后写入，mine/history 页面读取展示）
 */
export interface HistoryItem {
  id: number
  report_no: string
  type: AssessmentType
  bank_name: string | null
  product_name: string | null
  score: number
  level: string
  pass_probability: string
  limit_min: number
  limit_max: number
  is_paid: boolean
  created_at: string  // ISO 8601
}

interface Draft {
  type: AssessmentType
  bankCode: string | null
  bankName: string | null
  productId: number | null
  productName: string | null
  step1: Step1 | null
  step2: Step2 | null
  step1B: Step1B | null
  step3: Step3 | null
  step4: Step4 | null
  step4Docs: Step4Docs | null
  currentStep: number
}

const empty: Draft = {
  type: 'personal',
  bankCode: null, bankName: null,
  productId: null, productName: null,
  step1: null, step2: null, step1B: null, step3: null, step4: null, step4Docs: null,
  currentStep: 1,
}

export const useAssessmentStore = defineStore('assessment', () => {
  const type        = ref<AssessmentType>('personal')
  const bankCode    = ref<string | null>(null)
  const bankName    = ref<string | null>(null)
  const productId   = ref<number | null>(null)
  const productName = ref<string | null>(null)
  const step1       = ref<Step1 | null>(null)
  const step2       = ref<Step2 | null>(null)
  const step1B      = ref<Step1B | null>(null)
  const step3       = ref<Step3 | null>(null)
  const step4       = ref<Step4 | null>(null)
  const step4Docs   = ref<Step4Docs | null>(null)
  const currentStep = ref<number>(1)
  // 测评历史（提交成功后写入，本地存储，跨设备待后端 list 端点）
  const history     = ref<HistoryItem[]>([])

  const allInput = computed<Record<string, unknown>>(() => ({
    type: type.value,
    bank_code: bankCode.value,
    product_id: productId.value,
    ...(step1.value || {}),
    ...(step2.value || {}),
    ...(step1B.value || {}),
    ...(step3.value || {}),
    ...(step4.value || {}),
  }))

  const paidCount  = computed(() => history.value.filter(h => h.is_paid).length)
  const totalCount = computed(() => history.value.length)
  const latestItem = computed<HistoryItem | null>(() => history.value[0] || null)

  function setType(t: AssessmentType) { type.value = t; persist() }
  function setBank(code: string, name: string) { bankCode.value = code; bankName.value = name; persist() }
  function setProduct(id: number, name: string) { productId.value = id; productName.value = name; persist() }
  function clearBankProduct() { bankCode.value = null; bankName.value = null; productId.value = null; productName.value = null; persist() }
  function setStep1(d: Step1) { step1.value = d; persist() }
  function setStep2(d: Step2) { step2.value = d; persist() }
  function setStep1B(d: Step1B) { step1B.value = d; persist() }
  function setStep3(d: Step3) { step3.value = d; persist() }
  function setStep4(d: Step4) { step4.value = d; persist() }
  function setStep4Docs(d: Step4Docs) { step4Docs.value = d; persist() }
  function setStepNum(n: number) { currentStep.value = n; persist() }

  /**
   * 提交成功后写入历史（去重 + 截断 + 持久化）
   * 若 id 重复，更新该条；否则插到最前
   */
  function addHistory(item: HistoryItem) {
    const idx = history.value.findIndex(h => h.id === item.id)
    if (idx >= 0) {
      history.value[idx] = { ...history.value[idx], ...item }
    } else {
      history.value.unshift(item)
    }
    if (history.value.length > HISTORY_MAX) {
      history.value = history.value.slice(0, HISTORY_MAX)
    }
    setStorage(HISTORY_KEY, history.value)
  }

  /**
   * 更新历史条目（用于支付成功后刷新 is_paid）
   */
  function updateHistory(id: number, patch: Partial<HistoryItem>) {
    const idx = history.value.findIndex(h => h.id === id)
    if (idx >= 0) {
      history.value[idx] = { ...history.value[idx], ...patch }
      setStorage(HISTORY_KEY, history.value)
    }
  }

  /**
   * 读取单条历史（供结果页 / 报告页同步状态用）
   */
  function getHistoryById(id: number): HistoryItem | null {
    return history.value.find(h => h.id === id) || null
  }

  /**
   * 清空全部历史（设置 → 清除缓存）
   */
  function clearHistory() {
    history.value = []
    removeStorage(HISTORY_KEY)
  }

  function getAll() { return allInput.value }

  function persist() {
    setStorage(STORE_KEY, {
      type: type.value,
      bankCode: bankCode.value, bankName: bankName.value,
      productId: productId.value, productName: productName.value,
      // 关键修复：持久化 step1B（7 个企业字段）和 step4Docs（线下辅助资料），
      // 否则 business 用户刷新页面后会丢失企业数据
      step1: step1.value, step2: step2.value, step1B: step1B.value,
      step3: step3.value, step4: step4.value, step4Docs: step4Docs.value,
      currentStep: currentStep.value,
    })
  }

  function restoreFromStorage() {
    const d = getStorage<Draft>(STORE_KEY)
    if (d) {
      type.value = d.type || 'personal'
      bankCode.value = d.bankCode || null
      bankName.value = d.bankName || null
      productId.value = d.productId || null
      productName.value = d.productName || null
      step1.value = d.step1
      step2.value = d.step2
      // 关键修复：恢复 step1B（企业数据）和 step4Docs（线下辅助资料）
      step1B.value = d.step1B
      step3.value = d.step3
      step4.value = d.step4
      step4Docs.value = d.step4Docs
      currentStep.value = d.currentStep || 1
    }
    const h = getStorage<HistoryItem[]>(HISTORY_KEY, [])
    if (Array.isArray(h)) history.value = h
  }

  function reset() {
    type.value = 'personal'
    bankCode.value = null; bankName.value = null
    productId.value = null; productName.value = null
    // 关键修复：清空 step1B 和 step4Docs，否则切回 personal 时残留企业数据
    step1.value = null; step2.value = null; step1B.value = null
    step3.value = null; step4.value = null; step4Docs.value = null
    currentStep.value = 1
    persist()
  }

  return { type, bankCode, bankName, productId, productName,
           // 关键修复：return 漏了 step1B 和 setStep1B，外部 useStepGuard.ts:60 引用 store.step1B 编译报错
           // 之前漏了导致 useStepGuard 校验 business step1B 时 TypeScript 编译失败
           step1, step2, step1B, step3, step4, step4Docs, currentStep, allInput,
           history, paidCount, totalCount, latestItem,
           setType, setBank, setProduct, clearBankProduct,
           setStep1, setStep2, setStep1B, setStep3, setStep4, setStep4Docs, setStepNum,
           addHistory, updateHistory, getHistoryById, clearHistory,
           getAll, reset, restoreFromStorage }
})
