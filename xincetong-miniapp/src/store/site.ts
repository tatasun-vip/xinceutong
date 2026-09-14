/**
 * store/site.ts - 站点配置 store（数字/文案/合规变量化）
 *
 * 所有数字（128,000+ / 50+ / 9.99 / 96.3%）+ 文案 + 合规都从这取。
 * 运营改 DB 后，refresh() 拉一次最新即可全站生效。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getSiteConfig, SITE, getConfigValue, formatNumber, type SiteConfigGroup } from '@/api/site'
import { setStorage, getStorage } from '@/utils/storage'

const STORE_KEY = 'site_config_cache'
const CACHE_TTL = 5 * 60 * 1000  // 5 分钟

interface CachedConfig {
  data: SiteConfigGroup
  timestamp: number
}

export const useSiteStore = defineStore('site', () => {
  const config = ref<SiteConfigGroup | null>(null)
  const loaded = ref<boolean>(false)

  // 通用取值（带 fallback）
  function get(key: string, fallback: string = ''): string {
    return getConfigValue(config.value, key, fallback)
  }

  // 数字格式化（"128000" → "128,000+"）
  function num(key: string, suffix = '+', fallback = '0'): string {
    return formatNumber(get(key, fallback), suffix)
  }

  // 数字直接取（不格式化）
  function raw(key: string, fallback: string = ''): string {
    return get(key, fallback)
  }

  // ============================================================================
  // 便捷读取
  // ============================================================================

  const brandName = computed(() => get(SITE.brandName, '信测通'))
  const brandSlogan = computed(() => get(SITE.brandSlogan, '别再用征信试错'))
  const brandSubtitle = computed(() => get(SITE.brandSubtitle, '一次模拟测评，看清你在不同产品下的可贷资质'))
  const brandTagline = computed(() => get(SITE.brandTagline, '信用贷模拟评审系统'))
  const brandOneLiner = computed(() => get(SITE.brandOneLiner, '不查征信的信用贷模拟评审系统'))

  // 数字
  const userCount = computed(() => num(SITE.userCount, '+', '128000'))
  const testCount = computed(() => num(SITE.testCount, '+', '356000'))
  // 真实案例回测/专家数：DB 值为 0 时不再 fallback 20000/50，避免与「模拟评审」表述冲突
  const caseCount = computed(() => num(SITE.caseCount, '+', '0'))
  const expertCount = computed(() => num(SITE.expertCount, '+', '0'))
  const satisfaction = computed(() => num(SITE.satisfaction, '%', '96.3'))
  const productCount = computed(() => num(SITE.productCount, '', '6'))
  const payPrice = computed(() => num(SITE.payPrice, ' 元', '9.99'))

  // CTA
  const ctaPersonal = computed(() => get(SITE.ctaPersonal, '开始模拟测评（个人）'))
  const ctaBusiness = computed(() => get(SITE.ctaBusiness, '开始模拟测评（企业）'))

  // 合规
  const disclaimerShort = computed(() => get(SITE.disclaimerShort, '本工具为模拟测评，不查询您的征信，不构成贷款承诺。'))
  const disclaimerLong = computed(() => get(SITE.disclaimerLong, '实际审批结果以金融机构正式审批为准。'))
  const disclaimerFullReport = computed(() => get(SITE.disclaimerFullReport, ''))
  const disclaimerPay = computed(() => get(SITE.disclaimerPay, '虚拟服务，一经解锁，原则上不退款。'))

  // ============================================================================
  // 加载
  // ============================================================================

  async function load(force = false): Promise<void> {
    if (loaded.value && !force) return

    // 1. 先看本地缓存
    if (!force) {
      const cached = getStorage<CachedConfig>(STORE_KEY)
      if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        config.value = cached.data
        loaded.value = true
        return
      }
    }

    // 2. 拉后端
    try {
      const data = await getSiteConfig()
      config.value = data
      loaded.value = true
      // 3. 写本地缓存
      setStorage(STORE_KEY, { data, timestamp: Date.now() } as CachedConfig)
    } catch (e) {
      // 失败：用本地缓存（如果有时）
      const cached = getStorage<CachedConfig>(STORE_KEY)
      if (cached) {
        config.value = cached.data
        loaded.value = true
      }
    }
  }

  async function refresh(): Promise<void> {
    await load(true)
  }

  return {
    config, loaded,
    get, num, raw,
    // 便捷 computed
    brandName, brandSlogan, brandSubtitle, brandTagline, brandOneLiner,
    userCount, testCount, caseCount, expertCount, satisfaction, productCount, payPrice,
    ctaPersonal, ctaBusiness,
    disclaimerShort, disclaimerLong, disclaimerFullReport, disclaimerPay,
    load, refresh,
  }
})
