<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { bankApi, type Bank } from '@/api/bank'
import { orderApi } from '@/api/order'
import { assessmentApi, type FreeResult, type ProductResult } from '@/api/assessment'
import { useAssessmentStore } from '@/store/assessment'
import { getProductColor, getLevelColor, severityLabel } from '@/utils/productConfig'
import UiIcon from '@/components/UiIcon.vue'

const route = useRoute()
const router = useRouter()
const store = useAssessmentStore()
const bank = ref<Bank | null>(null)
const result = ref<FreeResult | null>(null)
const loading = ref(true)

function formatLimit(min?: number, max?: number): string {
  if (!min && !max) return '—'
  const fmt = (n: number) => Math.round(n).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  if (min && max) return min === max ? `${fmt(min)} 元` : `${fmt(min)}~${fmt(max)} 元`
  return `${fmt(max || min || 0)} 元`
}

onMounted(async () => {
  if (store.result && route.params.id == String(store.result.assessment_id)) result.value = store.result as any
  else if (route.query.r) { try { result.value = JSON.parse(decodeURIComponent(route.query.r as string)) } catch {} }
  if (!result.value && route.params.id) {
    try {
      const apiData = (await assessmentApi.getFree(String(route.params.id)) as any)?.data || null
      if (apiData) { result.value = { ...apiData, ...(apiData.overall || {}) } as any; if (store.setResult) store.setResult(result.value) }
    } catch (e: any) { ElMessage.error('加载报告失败：' + (e?.message || '网络异常')) }
  }
  const bankCode = store.bankCode || (result.value as any)?.bank_code
  try { if (bankCode) bank.value = await bankApi.detail(bankCode) } catch (e: any) { ElMessage.error('加载结果失败：' + (e?.message || '网络异常')) } finally { loading.value = false }
  if (result.value?.data_hash) { try { const snap = await orderApi.compareSnapshot(result.value.assessment_id) as any; if (snap?.data_hash && snap.data_hash !== result.value.data_hash) ElMessage.warning('数据已更新') } catch {} }
  loadCompare()
})

const goBanks = () => router.push('/banks')
const goHome = () => router.push('/')

const LEVEL_COLORS_FB: Record<string, string> = { S: '#8E6F2C', A: '#2E7D32', B: '#0288D1', C: '#ED6C02', D: '#C62828', E: '#5C6B7C' }
const LEVEL_DESC_FB: Record<string, string> = { S: '极佳 · 优质客户', A: '优秀 · 良好准入', B: '良好 · 标准准入', C: '一般 · 准入边界', D: '较弱 · 谨慎准入', E: '极弱 · 暂缓申请' }
const LEVEL_COLORS = computed<Record<string, string>>(() => { const c = (result.value as any)?.ui_config?.level_config; return c ? Object.fromEntries(Object.entries(c).map(([k, v]: any) => [k, v.color])) : LEVEL_COLORS_FB })
const LEVEL_DESC = computed<Record<string, string>>(() => { const c = (result.value as any)?.ui_config?.level_config; return c ? Object.fromEntries(Object.entries(c).map(([k, v]: any) => [k, v.desc])) : LEVEL_DESC_FB })

const productResults = computed<ProductResult[]>(() => (result.value as any)?.product_results || [])
const productCardStyle = (code: string) => { const c = getProductColor(code); return { borderLeftColor: c.color, '--pc-color': c.color, '--pc-bg': c.bg, '--pc-text': c.text } as any }

// v23.2 增量：优先用 overall.verdict（SSOT 结构化字段），fallback 到 one_sentence
// verdict 是 LEVEL_NARRATIVE 6 等级 × 1 句 的银行客户经理口径
const oneSentence = computed(() => {
  const r: any = result.value
  if (!r) return '请先完成测评查看结论'
  return r.overall?.verdict || r.one_sentence || r.free_summary || '当前资质需进一步评估'
})

const paywallSub = computed(() => {
  const r: any = result.value; if (!r) return '命中规则 · 不推荐原因 · 提分建议 · 实际可贷金额'
  const lv = r.level || 'E', n = r.top_issues_total || 0, p = r.improvement_projection
  if (lv === 'S' || lv === 'A') return '命中规则 · 6 大产品准入对比 · 实际可贷金额'
  if (lv === 'B') return p && ['A','S'].includes(p.level) ? `修复 ${n} 个细节预计可达 ${p.level} 级 · 6 大产品准入差距` : '命中规则 · 不推荐原因 · 6 大产品准入差距'
  if (lv === 'C') return `修复 ${n} 个核心问题预计可升级 · 6 大产品准入差距`
  if (lv === 'D') return `仍有 ${n} 个核心问题待修复 · 不推荐产品清单`
  return '命中规则 · 不推荐原因 · 修复后预计等级'
})

const m1Class = computed(() => { const lv = (result.value as any)?.level || 'E'; return lv === 'S' || lv === 'A' ? 'good' : (lv === 'B' || lv === 'C' ? 'mid' : 'bad') })
const m1Color = computed(() => { const lv = (result.value as any)?.level || 'E'; return lv === 'S' || lv === 'A' ? '#C9A96E' : (lv === 'B' || lv === 'C' ? '#8B7E5E' : '#9B2226') })

const timeline = computed(() => {
  const r: any = result.value; if (!r) return []
  const how = r.top_issue_free?.how || ''
  const acts = (txt: string) => txt.split(/[；;。\n]/).map(s => s.trim()).filter(s => s && s.length > 2).slice(0, 3)
  return [
    { day: 'D+30', phase: 'd30', title: '止血期 · 控制变量', actions: acts(how).length ? acts(how) : ['整理近 6 个月银行流水', '核对征信报告无误', '暂停新增信贷申请'], outcome: '风险敞口初步收敛' },
    { day: 'D+60', phase: 'd60', title: '修复期 · 落地执行', actions: ['按 D30 建议逐项落地', '结清高息小额贷款', '保持信用卡使用率 < 70%'], outcome: '信用画像明显改善' },
    { day: 'D+90', phase: 'd90', title: '提升期 · 复测准入', actions: ['重新发起测评', '对比分数与等级变化', '选择通过率 > 60% 的产品提交'], outcome: '多数产品准入改善' },
  ]
})

const payStep = ref<'idle' | 'creating' | 'paying' | 'done'>('idle')
const payOrderNo = ref('')
const payAmount = ref(9.99)
const payErr = ref('')
async function startUnlock() {
  if (!result.value) return
  payErr.value = ''; payStep.value = 'creating'
  try {
    const r = await orderApi.create(result.value.assessment_id)
    payOrderNo.value = r.order_no; payAmount.value = r.amount
    payStep.value = 'paying'
    const pay = await orderApi.mockPay(r.order_no)
    if (pay.status === 'paid') {
      payStep.value = 'done'
      result.value = { ...(result.value as any), is_paid: true }
      try { const full = await orderApi.fullReport(result.value.assessment_id) as any; const d = full?.data || full; if (d) result.value = { ...(result.value as any), ...d } } catch {}
      ElMessage.success('解锁成功！完整报告已开放')
    }
  } catch (e: any) { payErr.value = e?.message || '支付失败'; payStep.value = 'idle'; ElMessage.error(payErr.value) }
}

const m9HitCount = computed(() => productResults.value.reduce((s, p) => s + (p.hit_rules?.length || 0), 0))
const m9LowCount = computed(() => productResults.value.reduce((s, p) => s + (p.low_rules?.length || 0), 0))
const m9ImproveCount = computed(() => productResults.value.reduce((s, p) => s + (p.improve_vars?.length || 0), 0))

const compareBanks = ref<any[]>([])
const compareLoading = ref(false)
async function loadCompare() {
  if (compareBanks.value.length || !bank.value) return
  compareLoading.value = true
  try {
    const list = await (await import('@/api/bank')).bankApi.list() as any
    const others = (list.items || []).filter((b: any) => b.code !== bank.value!.code).slice(0, 2)
    const arr: any[] = []
    for (const b of others) { try { const ps = await (await import('@/api/bank')).bankApi.products(b.code); arr.push({ code: b.code, name: b.name, products: (ps as any).items || [] }) } catch {} }
    compareBanks.value = arr
  } catch {} finally { compareLoading.value = false }
}
const pickBank = (_c: string) => { ElMessage.info('已切换'); setTimeout(() => goBanks(), 600) }
const topProductMatch = (ps: any[]) => { if (!ps.length) return null; const s = (result.value as any)?.score || 0; return [...ps].sort((a, b) => Math.max(0, (a.pass_score_min || 0) - s) - Math.max(0, (b.pass_score_min || 0) - s))[0] }
</script>

<template>
  <div class="rs" v-loading="loading">
    <div class="rs-inner container" v-if="bank">
      <div class="rs-empty" v-if="!result"><div class="rs-empty-title">暂无测评结果</div><div class="rs-empty-sub">请先选择银行完成测评</div></div>

      <!-- v9 · M0 顶部付费引导 banner -->
      <div v-if="!result?.is_paid" class="rs-paywall-banner" @click="startUnlock">
        <div class="rs-pwbg"></div>
        <div class="rs-pwcontent">
          <div class="rs-pwleft">
            <div class="rs-pweye text-mono">UNLOCK · 完整报告</div>
            <div class="rs-pwtitle">6 大产品深度证据链<span class="rs-pwamount">¥{{ payAmount.toFixed(2) }}</span></div>
            <div class="rs-pwsub">{{ paywallSub }}</div>
          </div>
          <div class="rs-pwbtn"><span>立即解锁</span><span class="rs-pwarrow">→</span></div>
        </div>
        <div class="rs-pwtip">7 天内不满意全额退款 · 支付即视为同意《付费服务协议》</div>
      </div>

      <div class="rs-head">
        <div class="text-eyebrow">ASSESSMENT RESULT · 测评结果</div>
        <h1 class="rs-title">{{ bank.name }} · 您的专属画像</h1>
        <div class="divider-line"></div>
        <p class="rs-sub">基于您填写的信息和该行评分卡模型，本次为模拟运算结果，不查征信、不读取任何银行数据。</p>
      </div>

      <!-- M1 一句话结论（按 level 染色） -->
      <div class="rs-m1">
        <div class="rs-m1-head"><span class="text-eyebrow">01</span><span>一句话结论</span></div>
        <div :class="['rs-m1-verdict', 'v--'+m1Class]" :style="{ color: m1Color }">{{ oneSentence }}</div>
      </div>

      <!-- M3 评分卡 -->
      <div class="rs-card">
        <div class="rs-card-left">
          <div class="rs-eyebrow text-eyebrow">CREDIT LEVEL</div>
          <div class="rs-level" :style="{ color: LEVEL_COLORS[(result as any)?.level || 'E'] }">
            <span class="rs-level-letter text-num">{{ (result as any)?.level || '—' }}</span>
            <span class="rs-level-desc">{{ LEVEL_DESC[(result as any)?.level || 'E'] }}</span>
          </div>
          <div class="rs-score"><div class="rs-score-label">SCORE</div><div class="rs-score-num text-num">{{ (result as any)?.score ?? 0 }}</div><div class="rs-score-bar"><div class="rs-score-bar-fill" :style="{ width: ((result as any)?.score ?? 0) + '%' }"></div></div></div>
          <div class="rs-pass"><span class="rs-pass-label">通过概率</span><span class="rs-pass-val text-num">{{ (result as any)?.pass_probability || '—' }}</span></div>
          <div class="rs-summary">{{ (result as any)?.free_summary || '请完成测评查看结果' }}</div>
        </div>
        <div class="rs-card-right">
          <div class="rs-stat"><div class="rs-stat-label">参考额度</div><div class="rs-stat-val text-num">{{ formatLimit((result as any)?.limit_min, (result as any)?.limit_max) }}</div></div>
          <div class="rs-stat"><div class="rs-stat-label">参考利率</div><div class="rs-stat-val text-num">{{ (result as any)?.rate_min || 0 }} ~ {{ (result as any)?.rate_max || 0 }} %</div></div>
          <div class="rs-stat rs-stat-veto" v-if="(result as any)?.veto"><div class="rs-stat-label">触发一票否决</div><div class="rs-stat-val rs-veto-text">{{ (result as any).veto.message }}</div></div>
        </div>
      </div>

      <!-- v9 · M2 核心问题 1/N 锁 -->
      <div v-if="(result as any)?.top_issue_free" class="rs-m2">
        <div class="rs-issue-progress">
          <span class="rs-issue-progress-eyebrow text-mono">CORE ISSUE</span>
          <span class="rs-issue-progress-text">第 <b>1</b> / {{ (result as any).top_issues_total || 1 }} 个核心问题</span>
        </div>
        <div class="rs-issue-progress-bar"><div class="rs-issue-progress-fill" :style="{ width: (100 / ((result as any).top_issues_total || 1)) + '%', background: (result as any).top_issue_free.severity_color || '#9B2226' }"></div></div>
        <div class="rs-m2-head">
          <div class="rs-issue-tag" :style="{ background: (result as any).top_issue_free.severity_color || '#9B2226' }">{{ severityLabel((result as any).top_issue_free.severity) }} · 核心问题</div>
          <div class="rs-issue-cat">{{ (result as any).top_issue_free.category }}</div>
        </div>
        <h3 class="rs-m2-title">{{ (result as any).top_issue_free.title }}</h3>
        <p class="rs-m2-what">{{ (result as any).top_issue_free.what }}</p>
        <div class="rs-m2-5w">
          <div class="rs-m2-w"><b>WHY：</b>{{ (result as any).top_issue_free.why }}</div>
          <div class="rs-m2-w"><b>IMPACT：</b><span class="rs-m2-imp">{{ (result as any).top_issue_free.impact_prob }}</span><span v-if="(result as any).top_issue_free.impact_amount && (result as any).top_issue_free.impact_amount !== '—'" class="rs-m2-imp">{{ (result as any).top_issue_free.impact_amount }}</span><span v-if="(result as any).top_issue_free.impact_rate" class="rs-m2-imp">{{ (result as any).top_issue_free.impact_rate }}</span></div>
          <div class="rs-m2-w"><b>HOW：</b>{{ (result as any).top_issue_free.how || '请查看完整报告了解详细改善路径' }}</div>
        </div>
        <div v-if="((result as any).top_issues_total || 1) > 1" class="rs-issue-locked">
          <div class="rs-issue-locked-fade"></div>
          <div class="rs-issue-locked-overlay" @click.stop="startUnlock">
            <div class="rs-issue-locked-row"><span class="rs-issue-locked-icon"><UiIcon name="lock" :size="18" color="#8C6F36" /></span><span class="rs-issue-locked-title">解锁完整报告</span></div>
            <span class="rs-issue-locked-sub">查看其余 {{ ((result as any).top_issues_total || 1) - 1 }} 个核心问题深度分析 + 改善路径</span>
          </div>
        </div>
      </div>

      <!-- v9 · M3.5 改善后推演 blur 锁 -->
      <div v-if="(result as any)?.improvement_projection" class="rs-m35">
        <div class="rs-m35-content">
          <div class="rs-m35-eyebrow text-mono">AFTER 90 DAYS · 改善后预计</div>
          <div class="rs-m35-arrow">
            <div class="rs-m35-col"><div class="rs-m35-label">当前</div><div class="rs-m35-val" :style="{ color: LEVEL_COLORS[(result as any)?.level || 'E'] }">{{ (result as any)?.level }} · {{ (result as any)?.score }}分</div><div class="rs-m35-meta">通过率 {{ (result as any)?.pass_probability }}</div></div>
            <div class="rs-m35-arrow-icon">→</div>
            <div class="rs-m35-col rs-m35-col-after"><div class="rs-m35-label">改善后</div><div class="rs-m35-val" :style="{ color: LEVEL_COLORS[(result as any).improvement_projection.level] || '#5A6473' }">{{ (result as any).improvement_projection.level }} · {{ (result as any).improvement_projection.score }}分</div><div class="rs-m35-meta">通过率 {{ (result as any).improvement_projection.pass_probability }}</div></div>
          </div>
          <div class="rs-m35-foot"><UiIcon name="lightbulb" :size="14" color="#B89554" /> 修复 {{ (result as any).improvement_projection.fixed_count }} 个核心问题后预计可达</div>
        </div>
        <div v-if="!result?.is_paid" class="rs-m35-overlay" @click.stop="startUnlock"><div class="rs-m35-lock-card"><div class="rs-m35-lock-icon"><UiIcon name="lock" :size="32" color="#8C6F36" /></div><div class="rs-m35-lock-title">解锁 30/60/90 天完整路径</div><div class="rs-m35-lock-sub">查看完整改善推演 + 分阶段动作</div></div></div>
      </div>

      <!-- M4 时间轴 -->
      <div class="rs-m4" v-if="timeline.length">
        <div class="rs-sec-title"><span class="text-mono">04 / TIMELINE</span><span>30 / 60 / 90 天行动建议</span><div class="divider-line"></div></div>
        <div class="rs-timeline">
          <div v-for="(t, i) in timeline" :key="i" class="rs-tl-item" :class="'rs-tl-'+t.phase">
            <div class="rs-tl-node">{{ t.day }}</div>
            <div class="rs-tl-body"><div class="rs-tl-title">{{ t.title }}</div><ul class="rs-tl-list"><li v-for="(a, j) in t.actions" :key="j">{{ a }}</li></ul><div class="rs-tl-outcome" v-if="t.outcome">预期结果：{{ t.outcome }}</div></div>
          </div>
        </div>
      </div>

      <!-- M5 预测 -->
      <div class="rs-m5" v-if="(result as any)?.projection_table?.length">
        <div class="rs-sec-title"><span class="text-mono">05 / PROJECTION</span><span>30 / 60 / 90 天额度·利率预测</span><div class="divider-line"></div></div>
        <div class="rs-pred">
          <div v-for="(p, i) in (result as any).projection_table" :key="i" :class="['rs-pred-col', p.current ? 'rs-pred-cur' : '']">
            <div class="rs-pred-day">{{ p.day }}</div>
            <div class="rs-pred-lv" :style="{ color: LEVEL_COLORS[p.level] }">{{ p.level }}</div>
            <div class="rs-pred-score">{{ p.score }} <span>分</span></div>
            <div class="rs-pred-bar"><div class="rs-pred-bar-fill" :style="{ width: p.score + '%' }"></div></div>
            <div class="rs-pred-meta"><div class="rs-pred-row"><span>额度</span><b>{{ formatLimit(p.limit_min, p.limit_max) }}</b></div><div class="rs-pred-row"><span>利率</span><b>{{ p.rate_min }}~{{ p.rate_max }}%</b></div></div>
            <div class="rs-pred-tag" v-if="!p.current">+{{ p.growth }}%</div>
          </div>
        </div>
        <div class="rs-pred-note">估算规则：按等级提升幅度线性外推 + 利率随等级下调，每 30 天 +1 等级为上限。</div>
      </div>

      <!-- v9 架构级改造 · M6 6 大产品类型 evidence blur 卡 -->
      <div class="rs-section" v-if="productResults.length">
        <div class="rs-sec-title"><span class="text-mono">03 / PRODUCTS</span><span>6 大产品独立模拟结果</span><div class="divider-line"></div></div>
        <div class="rs-products">
          <div v-for="p in productResults" :key="p.product_code" :class="['rs-product-wrap', p.product_code, !result?.is_paid ? 'rs-product-locked' : '']" :style="productCardStyle(p.product_code)">
            <div class="rs-product-head">
              <span class="rs-product-icon"><UiIcon :name="getProductColor(p.product_code).icon" :size="22" :color="getProductColor(p.product_code).color" /></span>
              <div class="rs-product-head-body"><div class="rs-product-name">{{ p.product_name }}</div><div v-if="p.product_subtitle" class="rs-product-sub">{{ p.product_subtitle }}</div></div>
              <span v-if="p.level" class="rs-product-level-chip" :style="{ color: getLevelColor(p.level).color, background: getLevelColor(p.level).bg, borderColor: getLevelColor(p.level).color }">{{ p.level }} · {{ getLevelColor(p.level).label }}</span>
            </div>
            <div class="rs-product-score">
              <div class="rs-product-score-num" :style="{ color: getProductColor(p.product_code).color }">{{ p.score }}</div>
              <div class="rs-product-score-unit">基础分</div>
              <div v-if="p.pass_probability" class="rs-product-score-pass">通过率 {{ p.pass_probability }}</div>
            </div>
            <div class="rs-product-limit"><span class="rs-product-limit-label">模拟额度</span><span class="rs-product-limit-val" :style="{ color: getProductColor(p.product_code).color }">{{ formatLimit(p.realistic_limit_min || p.limit_min, p.realistic_limit_max || p.limit_max) }}</span></div>
            <div class="rs-product-evidence" v-if="result?.is_paid">
              <div v-if="p.hit_rules?.length" class="rs-ev-block"><div class="rs-ev-label"><UiIcon name="check-circle" :size="14" :color="getProductColor(p.product_code).color" /> 命中加分</div><div v-for="(r, k) in p.hit_rules" :key="k" class="rs-ev-row"><span class="rs-ev-rule">{{ r.rule }}</span><span class="rs-ev-score" :style="{ color: getProductColor(p.product_code).color }">+{{ r.score }}</span></div></div>
              <div v-if="p.low_rules?.length" class="rs-ev-block"><div class="rs-ev-label"><UiIcon name="x-circle" :size="14" color="#9B2226" /> 扣分项</div><div v-for="(r, k) in p.low_rules" :key="k" class="rs-ev-row"><span class="rs-ev-rule">{{ r.rule }}</span><span class="rs-ev-score rs-ev-score-neg">{{ r.score }}</span></div></div>
              <div v-if="p.not_recommend_reason" class="rs-ev-block"><div class="rs-ev-label"><UiIcon name="warning" :size="14" color="#B25E00" /> 不推荐原因</div><div class="rs-ev-reason">{{ p.not_recommend_reason }}</div></div>
              <!-- v22+ 改善建议 hint（SSOT 派生：improve_vars top1 口语化总结） -->
              <div v-if="p.improve_hint" class="rs-ev-block rs-ev-hint"><div class="rs-ev-label"><UiIcon name="arrow-up" :size="14" color="#2A9D8F" /> 如何改善</div><div class="rs-ev-reason">{{ p.improve_hint }}</div></div>
              <div v-if="p.improve_vars?.length" class="rs-ev-block"><div class="rs-ev-label"><UiIcon name="arrow-up" :size="14" :color="getProductColor(p.product_code).color" /> 提分建议</div><div v-for="(v, k) in p.improve_vars" :key="k" class="rs-ev-row"><span class="rs-ev-rule">{{ v.current }} → {{ v.best }}</span><span class="rs-ev-score" :style="{ color: getProductColor(p.product_code).color }">+{{ v.delta }}</span></div></div>
            </div>
            <div v-if="!result?.is_paid" class="rs-product-locked-overlay" @click.stop="startUnlock">
              <span class="rs-product-locked-icon"><UiIcon name="lock" :size="20" color="#8C6F36" /></span>
              <span class="rs-product-locked-text">解锁查看 {{ p.product_name }} 完整证据链</span>
              <span class="rs-product-locked-sub">¥{{ payAmount.toFixed(2) }} · 一次解锁全部 6 大产品</span>
            </div>
          </div>
        </div>
      </div>

      <!-- M9 v9 增量：动态钩子 -->
      <div class="rs-m9" v-if="!result?.is_paid">
        <div class="rs-m9-eyebrow text-mono">PRO · UNLOCK</div>
        <h3 class="rs-m9-title">解锁 6 大产品完整证据链</h3>
        <div class="rs-m9-dynamic">
          <div class="rs-m9-stat"><div class="rs-m9-stat-num">{{ m9HitCount }}</div><div class="rs-m9-stat-lbl">命中加分规则</div></div>
          <div class="rs-m9-stat"><div class="rs-m9-stat-num">{{ m9LowCount }}</div><div class="rs-m9-stat-lbl">扣分项</div></div>
          <div class="rs-m9-stat"><div class="rs-m9-stat-num">{{ m9ImproveCount }}</div><div class="rs-m9-stat-lbl">提分建议</div></div>
        </div>
        <div class="rs-m9-grid">
          <div class="rs-m9-free"><div class="rs-m9-col-title">免费版 <span>当前</span></div><ul><li>等级 / 分数 / 通过率</li><li>一句话结论</li><li>1 / {{ (result as any).top_issues_total || 1 }} 核心问题</li><li>30/60/90 行动建议</li><li class="off">6 大产品完整证据链</li><li class="off">5 大维度细分拆解</li><li class="off">PDF 报告下载</li></ul></div>
          <div class="rs-m9-pro"><div class="rs-m9-badge">PRO · 推荐</div><div class="rs-m9-col-title">完整报告 <span>¥{{ payAmount.toFixed(2) }}</span></div><ul><li>{{ (result as any).top_issues_total || 1 }} 个核心问题深度分析</li><li>6 大产品命中/扣分/提分完整证据链</li><li>5 大维度细分拆解</li><li>30/60/90 行动 + 改善后额度预测</li><li>完整银行模型权重 + 拒绝原因排序</li><li>PDF 报告下载 + 90 天复测提醒</li></ul><el-button type="primary" size="large" class="rs-m9-btn" :loading="payStep==='creating'||payStep==='paying'" @click="startUnlock">{{ payStep==='idle' ? '立即解锁 ¥'+payAmount.toFixed(2) : (payStep==='creating' ? '创建订单…' : (payStep==='paying' ? '支付中…' : '已解锁')) }}</el-button><div class="rs-m9-err" v-if="payErr">{{ payErr }}</div><div class="rs-m9-tip">支付后立即开放，1 年内可重复查看</div></div>
        </div>
      </div>

      <div class="rs-m9-done" v-else><div class="rs-m9-done-icon"><UiIcon name="check-circle" :size="48" color="#2E7D32" /></div><div class="rs-m9-done-title">完整报告已解锁</div><div class="rs-m9-done-sub">可点击「PDF 报告」下载</div></div>

      <!-- M10 跨行快选 -->
      <div class="rs-m10" v-if="result && !compareLoading && compareBanks.length">
        <div class="rs-sec-title"><span class="text-mono">06 / COMPARE</span><span>其他银行快选</span><div class="divider-line"></div></div>
        <div class="rs-cmp">
          <div v-for="b in compareBanks" :key="b.code" class="rs-cmp-card" @click="pickBank(b.code)">
            <div class="rs-cmp-head"><div class="rs-cmp-name">{{ b.name }}</div><div class="rs-cmp-arrow">→</div></div>
            <div class="rs-cmp-top" v-if="topProductMatch(b.products)">推荐：{{ topProductMatch(b.products)!.name }}<span class="rs-cmp-gap">· 您的分数比准入分低 {{ Math.max(0, ((topProductMatch(b.products)!.pass_score_min || 0) - ((result as any)?.score || 0))) }} 分</span></div>
            <div class="rs-cmp-actions"><el-button size="small" plain>选这家</el-button></div>
          </div>
        </div>
      </div>

      <div class="rs-foot">
        <el-button @click="goBanks" size="large" plain>选择其他银行</el-button>
        <el-button @click="goHome" size="large" plain>返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============================================
 * 公共类（与 miniapp v9 同源 token）
 * ============================================ */
.rs { min-height: 100vh; background: #F7F5F1; padding: 32px 0 80px; }
.rs-inner { max-width: 1100px; margin: 0 auto; padding: 0 24px; }
.rs-empty { padding: 80px 0; text-align: center; }
.rs-empty-title { font-size: 22px; color: #1A1A1A; }
.rs-empty-sub { color: #5A6473; margin-top: 8px; }
.text-eyebrow { font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600; letter-spacing: 0.18em; color: #8E6F2C; text-transform: uppercase; }
.text-mono { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.1em; color: #8B7E5E; }
.text-num { font-family: 'JetBrains Mono', monospace; font-variant-numeric: tabular-nums; }
.divider-line { height: 1px; background: linear-gradient(90deg, transparent, #D4C8A8 30%, #D4C8A8 70%, transparent); margin: 16px 0; flex: 1; }

/* ============================================
 * v9 增量 · M0 顶部付费引导 banner
 * ============================================ */
.rs-paywall-banner { position: relative; overflow: hidden; border-radius: 16px; padding: 24px 28px 20px; margin-bottom: 28px; cursor: pointer; transition: transform 0.2s; box-shadow: 0 8px 24px rgba(184, 149, 84, 0.18); }
.rs-paywall-banner:hover { transform: translateY(-2px); box-shadow: 0 12px 32px rgba(184, 149, 84, 0.28); }
.rs-pwbg { position: absolute; inset: 0; background: linear-gradient(135deg, #8E6F2C 0%, #B89554 50%, #D4A847 100%); }
.rs-pwcontent { position: relative; z-index: 1; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
.rs-pwleft { flex: 1; }
.rs-pweye { color: #FAF3E3; opacity: 0.85; font-size: 11px; }
.rs-pwtitle { color: #FAF3E3; font-size: 24px; font-weight: 700; margin-top: 6px; line-height: 1.3; }
.rs-pwamount { display: inline-block; margin-left: 12px; padding: 4px 12px; background: #FAF3E3; color: #8C6F36; border-radius: 6px; font-size: 16px; font-weight: 700; }
.rs-pwsub { color: #FAF3E3; font-size: 13px; margin-top: 8px; opacity: 0.92; }
.rs-pwbtn { background: #FAF3E3; color: #8C6F36; padding: 14px 24px; border-radius: 10px; font-weight: 700; font-size: 15px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; transition: all 0.2s; }
.rs-paywall-banner:hover .rs-pwbtn { background: #fff; }
.rs-pwarrow { transition: transform 0.2s; }
.rs-paywall-banner:hover .rs-pwarrow { transform: translateX(4px); }
.rs-pwtip { position: relative; z-index: 1; color: #FAF3E3; font-size: 11px; opacity: 0.7; margin-top: 12px; text-align: center; }

/* ============================================
 * 报告头
 * ============================================ */
.rs-head { padding: 32px 0 24px; }
.rs-title { font-size: 32px; font-weight: 700; color: #1A1A1A; margin: 12px 0 0; }
.rs-sub { color: #5A6473; margin: 12px 0 0; font-size: 14px; line-height: 1.7; max-width: 720px; }

/* ============================================
 * v9 升级 · M1 一句话结论（按 level 染色）
 * ============================================ */
.rs-m1 { background: #fff; border-radius: 12px; padding: 24px 28px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); border-left: 4px solid #D4C8A8; }
.rs-m1-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.rs-m1-head .text-eyebrow { color: #8E6F2C; }
.rs-m1-head > span:last-child { font-size: 15px; color: #1A1A1A; font-weight: 600; }
.rs-m1-verdict { font-size: 22px; font-weight: 600; line-height: 1.5; padding: 4px 0; }
.rs-m1-verdict.v--good { color: #C9A96E; }
.rs-m1-verdict.v--mid { color: #8B7E5E; }
.rs-m1-verdict.v--bad { color: #9B2226; }

/* ============================================
 * M3 评分卡
 * ============================================ */
.rs-card { display: flex; background: #fff; border-radius: 12px; padding: 32px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.rs-card-left { flex: 1; padding-right: 32px; border-right: 1px solid #ECEFF4; }
.rs-eyebrow { margin-bottom: 12px; }
.rs-level { display: flex; align-items: baseline; gap: 12px; }
.rs-level-letter { font-size: 64px; font-weight: 700; line-height: 1; }
.rs-level-desc { font-size: 14px; color: #5A6473; }
.rs-score { margin-top: 24px; }
.rs-score-label { font-size: 11px; color: #8E6F2C; font-weight: 600; letter-spacing: 0.18em; }
.rs-score-num { font-size: 36px; color: #1A1A1A; font-weight: 700; margin: 4px 0 8px; }
.rs-score-bar { height: 6px; background: #ECEFF4; border-radius: 3px; overflow: hidden; }
.rs-score-bar-fill { height: 100%; background: linear-gradient(90deg, #B89554, #D4A847); transition: width 0.6s; }
.rs-pass { margin-top: 16px; display: flex; align-items: baseline; gap: 12px; }
.rs-pass-label { color: #5A6473; font-size: 13px; }
.rs-pass-val { color: #1A1A1A; font-size: 20px; font-weight: 600; }
.rs-summary { margin-top: 16px; color: #4A4A4A; font-size: 14px; line-height: 1.7; padding: 12px 16px; background: #F7F5F1; border-radius: 8px; }
.rs-card-right { width: 320px; padding-left: 32px; display: flex; flex-direction: column; gap: 20px; }
.rs-stat { padding: 16px 20px; background: #F7F5F1; border-radius: 8px; }
.rs-stat-label { font-size: 12px; color: #5A6473; }
.rs-stat-val { font-size: 22px; font-weight: 600; color: #1A1A1A; margin-top: 4px; }
.rs-veto-text { color: #9B2226; font-size: 13px; line-height: 1.5; margin-top: 4px; }
.rs-stat-veto { background: #FCE7E7; border: 1px solid #F4C7C7; }

/* ============================================
 * v9 增量 · M2 核心问题 1/N 锁
 * ============================================ */
.rs-m2 { background: #fff; border-radius: 12px; padding: 24px 28px 28px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); position: relative; }
.rs-issue-progress { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.rs-issue-progress-eyebrow { color: #8E6F2C; }
.rs-issue-progress-text { color: #5A6473; font-size: 13px; }
.rs-issue-progress-text b { color: #1A1A1A; font-size: 15px; }
.rs-issue-progress-bar { height: 4px; background: #ECEFF4; border-radius: 2px; overflow: hidden; margin-bottom: 20px; }
.rs-issue-progress-fill { height: 100%; transition: width 0.6s; }
.rs-m2-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.rs-issue-tag { color: #fff; padding: 5px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.rs-issue-cat { color: #5A6473; font-size: 12px; }
.rs-m2-title { font-size: 20px; font-weight: 600; color: #1A1A1A; margin: 0 0 12px; line-height: 1.4; }
.rs-m2-what { color: #4A4A4A; font-size: 14px; line-height: 1.7; margin: 0 0 16px; }
.rs-m2-5w { display: flex; flex-direction: column; gap: 10px; padding: 16px; background: #F7F5F1; border-radius: 8px; }
.rs-m2-w { color: #4A4A4A; font-size: 13px; line-height: 1.6; }
.rs-m2-w b { color: #1A1A1A; font-weight: 600; margin-right: 4px; }
.rs-m2-imp { display: inline-block; padding: 2px 8px; background: #fff; border: 1px solid #D4C8A8; border-radius: 4px; color: #8C6F36; font-size: 12px; margin-right: 6px; font-weight: 600; }
.rs-issue-locked { position: relative; margin-top: 16px; min-height: 80px; }
.rs-issue-locked-fade { position: absolute; inset: -40px 0 0; background: linear-gradient(180deg, rgba(255,255,255,0) 0%, #fff 70%, #fff 100%); pointer-events: none; }
.rs-issue-locked-overlay { position: relative; z-index: 1; padding: 24px; background: linear-gradient(135deg, #F7F5F1, #FAF3E3); border-radius: 8px; border: 1px dashed #B89554; text-align: center; cursor: pointer; transition: all 0.2s; }
.rs-issue-locked-overlay:hover { background: linear-gradient(135deg, #FAF3E3, #F0E5C8); transform: translateY(-1px); }
.rs-issue-locked-row { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 6px; }
.rs-issue-locked-icon { display: inline-flex; align-items: center; }
.rs-issue-locked-title { color: #8C6F36; font-weight: 600; font-size: 15px; }
.rs-issue-locked-sub { color: #5A6473; font-size: 12px; }

/* ============================================
 * v9 增量 · M3.5 改善后推演（未付费整张虚化）
 * ============================================ */
.rs-m35 { position: relative; background: #fff; border-radius: 12px; padding: 28px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); overflow: hidden; }
.rs-m35-content { position: relative; }
.rs-m35-eyebrow { color: #8E6F2C; margin-bottom: 16px; }
.rs-m35-arrow { display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 20px 0; }
.rs-m35-col { flex: 1; text-align: center; padding: 16px; background: #F7F5F1; border-radius: 8px; }
.rs-m35-col-after { background: linear-gradient(135deg, #FAF3E3, #F0E5C8); }
.rs-m35-label { font-size: 11px; color: #5A6473; letter-spacing: 0.18em; }
.rs-m35-val { font-size: 32px; font-weight: 700; margin: 6px 0 4px; }
.rs-m35-meta { font-size: 12px; color: #5A6473; }
.rs-m35-arrow-icon { font-size: 32px; color: #B89554; font-weight: 300; }
.rs-m35-foot { text-align: center; color: #5A6473; font-size: 13px; padding-top: 12px; border-top: 1px dashed #D4C8A8; display: flex; align-items: center; justify-content: center; gap: 6px; }
.rs-m35-overlay { position: absolute; inset: 0; background: rgba(255, 255, 255, 0.55); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.2s; }
.rs-m35-overlay:hover { background: rgba(255, 255, 255, 0.7); }
.rs-m35-lock-card { text-align: center; padding: 28px 40px; background: rgba(255, 255, 255, 0.95); border-radius: 12px; box-shadow: 0 8px 24px rgba(184, 149, 84, 0.25); }
.rs-m35-lock-icon { display: inline-flex; align-items: center; justify-content: center; width: 40px; height: 40px; margin: 0 auto; }
.rs-m35-lock-title { color: #8C6F36; font-size: 17px; font-weight: 600; margin: 8px 0 4px; }
.rs-m35-lock-sub { color: #5A6473; font-size: 12px; }

/* ============================================
 * v8 保留 · M4 时间轴
 * ============================================ */
.rs-m4 { background: #fff; border-radius: 12px; padding: 28px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.rs-sec-title { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.rs-sec-title > span:nth-child(2) { font-size: 18px; font-weight: 600; color: #1A1A1A; }
.rs-timeline { display: flex; flex-direction: column; gap: 0; position: relative; padding-left: 24px; }
.rs-timeline::before { content: ''; position: absolute; left: 8px; top: 24px; bottom: 24px; width: 2px; background: linear-gradient(180deg, #D4C8A8 0%, #D4C8A8 100%); }
.rs-tl-item { position: relative; padding: 0 0 28px 24px; }
.rs-tl-item:last-child { padding-bottom: 0; }
.rs-tl-item::before { content: ''; position: absolute; left: -20px; top: 8px; width: 12px; height: 12px; border-radius: 50%; background: #fff; border: 3px solid #B89554; }
.rs-tl-d30::before { border-color: #B25E00; }
.rs-tl-d60::before { border-color: #B89554; }
.rs-tl-d90::before { border-color: #2E7D32; }
.rs-tl-node { display: inline-block; padding: 3px 10px; background: #F7F5F1; color: #5A6473; font-size: 12px; font-weight: 600; border-radius: 4px; margin-bottom: 8px; }
.rs-tl-title { font-size: 16px; font-weight: 600; color: #1A1A1A; margin-bottom: 10px; }
.rs-tl-list { margin: 0 0 12px; padding-left: 20px; color: #4A4A4A; font-size: 13px; line-height: 1.8; }
.rs-tl-outcome { font-size: 12px; color: #5A6473; padding: 6px 12px; background: #F7F5F1; border-radius: 4px; display: inline-block; }

/* ============================================
 * v8 保留 · M5 预测
 * ============================================ */
.rs-m5 { background: #fff; border-radius: 12px; padding: 28px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.rs-pred { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.rs-pred-col { position: relative; padding: 20px 16px; background: #F7F5F1; border-radius: 8px; text-align: center; transition: all 0.2s; }
.rs-pred-cur { background: #fff; border: 1px solid #D4C8A8; }
.rs-pred-day { font-size: 11px; color: #5A6473; letter-spacing: 0.18em; font-weight: 600; }
.rs-pred-lv { font-size: 40px; font-weight: 700; line-height: 1.2; margin: 8px 0 4px; }
.rs-pred-score { font-size: 13px; color: #4A4A4A; margin-bottom: 10px; }
.rs-pred-score span { font-size: 11px; color: #5A6473; }
.rs-pred-bar { height: 4px; background: #ECEFF4; border-radius: 2px; overflow: hidden; margin: 12px 0; }
.rs-pred-bar-fill { height: 100%; background: linear-gradient(90deg, #B89554, #D4A847); }
.rs-pred-meta { display: flex; flex-direction: column; gap: 4px; margin-top: 12px; }
.rs-pred-row { display: flex; justify-content: space-between; font-size: 12px; color: #5A6473; }
.rs-pred-row b { color: #1A1A1A; }
.rs-pred-tag { position: absolute; top: 12px; right: 12px; padding: 2px 8px; background: #FAF3E3; color: #8C6F36; font-size: 10px; font-weight: 700; border-radius: 4px; }
.rs-pred-note { margin-top: 16px; font-size: 11px; color: #5A6473; line-height: 1.6; }

/* ============================================
 * v9 架构级改造 · M6 6 大产品类型卡（独立色+icon+等级+evidence blur）
 * ============================================ */
.rs-section { background: #fff; border-radius: 12px; padding: 28px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.rs-products { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.rs-product-wrap { position: relative; padding: 18px 20px 20px; background: var(--pc-bg, #F7F5F1); border-radius: 10px; border-left: 4px solid var(--pc-color, #B89554); overflow: hidden; }
.rs-product-head { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.rs-product-icon { display: inline-flex; align-items: center; flex-shrink: 0; }
.rs-product-head-body { flex: 1; min-width: 0; }
.rs-product-name { color: var(--pc-text, #1A1A1A); font-size: 15px; font-weight: 600; line-height: 1.3; }
.rs-product-sub { color: var(--pc-text, #5A6473); opacity: 0.7; font-size: 11px; margin-top: 2px; }
.rs-product-level-chip { padding: 3px 10px; border: 1px solid; border-radius: 4px; font-size: 11px; font-weight: 600; flex-shrink: 0; }
.rs-product-score { display: flex; align-items: baseline; gap: 10px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.5); }
.rs-product-score-num { font-size: 36px; font-weight: 700; line-height: 1; }
.rs-product-score-unit { color: var(--pc-text, #5A6473); opacity: 0.7; font-size: 12px; }
.rs-product-score-pass { margin-left: auto; color: var(--pc-text, #5A6473); opacity: 0.85; font-size: 11px; padding: 2px 8px; background: rgba(255,255,255,0.6); border-radius: 3px; }
.rs-product-limit { display: flex; align-items: baseline; justify-content: space-between; padding: 10px 0; }
.rs-product-limit-label { color: var(--pc-text, #5A6473); opacity: 0.7; font-size: 12px; }
.rs-product-limit-val { font-size: 16px; font-weight: 600; }
.rs-product-evidence { margin-top: 10px; padding-top: 10px; border-top: 1px dashed rgba(255,255,255,0.5); }
.rs-ev-block { margin-bottom: 10px; }
.rs-ev-block:last-child { margin-bottom: 0; }
/* v22+ 改善建议 hint 块（SSOT 派生：与 not_recommend_reason 互补，绿色调） */
.rs-ev-hint .rs-ev-reason { color: #1F4D47; background: rgba(42, 157, 143, 0.06); border-left: 3px solid #2A9D8F; }
.rs-ev-label { color: var(--pc-text, #1A1A1A); font-size: 11px; font-weight: 600; letter-spacing: 0.1em; margin-bottom: 6px; opacity: 0.85; display: flex; align-items: center; gap: 4px; }
.rs-ev-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 4px 0; font-size: 12px; color: var(--pc-text, #4A4A4A); }
.rs-ev-rule { flex: 1; line-height: 1.4; }
.rs-ev-score { font-weight: 700; }
.rs-ev-score-neg { color: #9B2226; }
.rs-ev-reason { color: var(--pc-text, #4A4A4A); font-size: 12px; line-height: 1.6; padding: 6px 10px; background: rgba(255,255,255,0.5); border-radius: 4px; }
.rs-product-locked-overlay { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 16px 16px; background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.85) 30%, rgba(255,255,255,0.95) 100%); display: flex; flex-direction: column; align-items: center; gap: 4px; cursor: pointer; transition: background 0.2s; }
.rs-product-locked-overlay:hover { background: linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.7) 30%, rgba(255,255,255,0.9) 100%); }
.rs-product-locked-icon { display: inline-flex; align-items: center; }
.rs-product-locked-text { color: var(--pc-text, #1A1A1A); font-size: 13px; font-weight: 600; }
.rs-product-locked-sub { color: var(--pc-text, #5A6473); font-size: 11px; opacity: 0.85; }
.rs-product-wrap.rs-product-locked .rs-product-evidence { filter: blur(2px); pointer-events: none; }
.rs-product-wrap.rs-product-locked .rs-product-limit-val { filter: blur(0.5px); }

/* ============================================
 * v9 增量 · M9 付费解锁（动态钩子）
 * ============================================ */
.rs-m9 { background: #fff; border-radius: 12px; padding: 32px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.rs-m9-eyebrow { color: #8E6F2C; }
.rs-m9-title { font-size: 22px; font-weight: 600; color: #1A1A1A; margin: 8px 0 24px; }
.rs-m9-dynamic { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; padding: 20px; background: linear-gradient(135deg, #FAF3E3, #F0E5C8); border-radius: 10px; margin-bottom: 24px; }
.rs-m9-stat { text-align: center; }
.rs-m9-stat-num { font-size: 32px; font-weight: 700; color: #8C6F36; line-height: 1; }
.rs-m9-stat-lbl { color: #8C6F36; font-size: 12px; margin-top: 4px; opacity: 0.85; }
.rs-m9-grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 20px; }
.rs-m9-free, .rs-m9-pro { padding: 24px; border-radius: 10px; position: relative; }
.rs-m9-free { background: #F7F5F1; }
.rs-m9-pro { background: linear-gradient(135deg, #fff, #FAF3E3); border: 1px solid #B89554; }
.rs-m9-badge { position: absolute; top: -10px; right: 16px; background: #B89554; color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; }
.rs-m9-col-title { font-size: 16px; font-weight: 600; color: #1A1A1A; display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #ECEFF4; }
.rs-m9-col-title span { color: #8C6F36; font-size: 14px; font-weight: 500; }
.rs-m9-free ul, .rs-m9-pro ul { list-style: none; margin: 0; padding: 0; }
.rs-m9-free li, .rs-m9-pro li { font-size: 13px; color: #4A4A4A; padding: 7px 0 7px 22px; position: relative; line-height: 1.5; }
.rs-m9-free li::before, .rs-m9-pro li::before { content: '✓'; position: absolute; left: 0; top: 7px; color: #2E7D32; font-weight: 700; }
.rs-m9-free li.off { color: #9CA3AF; }
.rs-m9-free li.off::before { content: '✕'; color: #9CA3AF; }
.rs-m9-pro li::before { color: #B89554; }
.rs-m9-btn { width: 100%; margin-top: 20px; height: 48px; font-size: 15px; font-weight: 600; background: linear-gradient(135deg, #B89554, #8E6F2C); border: none; }
.rs-m9-btn:hover { background: linear-gradient(135deg, #C9A96E, #B89554); }
.rs-m9-err { color: #9B2226; font-size: 12px; margin-top: 8px; text-align: center; }
.rs-m9-tip { color: #5A6473; font-size: 11px; margin-top: 8px; text-align: center; }

.rs-m9-done { background: linear-gradient(135deg, #E5F2EB, #C9E5D5); border-radius: 12px; padding: 32px; text-align: center; margin: 24px 0; }
.rs-m9-done-icon { width: 48px; height: 48px; margin: 0 auto 12px; border-radius: 50%; background: #2E7D32; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 24px; }
.rs-m9-done-title { font-size: 18px; font-weight: 600; color: #1A1A1A; }
.rs-m9-done-sub { color: #5A6473; font-size: 13px; margin-top: 4px; }

/* ============================================
 * v8 保留 · M10 跨行快选 + footer
 * ============================================ */
.rs-m10 { background: #fff; border-radius: 12px; padding: 28px; margin: 24px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.rs-cmp { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.rs-cmp-card { padding: 20px; background: #F7F5F1; border-radius: 8px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
.rs-cmp-card:hover { background: #ECEFF4; border-color: #B89554; transform: translateY(-2px); }
.rs-cmp-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.rs-cmp-name { font-size: 15px; font-weight: 600; color: #1A1A1A; }
.rs-cmp-arrow { color: #B89554; font-size: 20px; }
.rs-cmp-top { font-size: 12px; color: #4A4A4A; margin-bottom: 12px; line-height: 1.5; }
.rs-cmp-gap { color: #5A6473; }

.rs-foot { display: flex; gap: 16px; justify-content: center; padding: 32px 0 0; }

/* ============================================
 * 响应式（mobile 适配）
 * ============================================ */
@media (max-width: 768px) {
  .rs-inner { padding: 0 16px; }
  .rs-title { font-size: 24px; }
  .rs-card { flex-direction: column; }
  .rs-card-left { padding-right: 0; border-right: none; border-bottom: 1px solid #ECEFF4; padding-bottom: 24px; margin-bottom: 24px; }
  .rs-card-right { width: 100%; padding-left: 0; }
  .rs-m35-arrow { flex-direction: column; gap: 12px; }
  .rs-m35-arrow-icon { transform: rotate(90deg); }
  .rs-products { grid-template-columns: 1fr; }
  .rs-m9-grid { grid-template-columns: 1fr; }
  .rs-cmp { grid-template-columns: 1fr; }
  .rs-pred { grid-template-columns: 1fr 1fr; }
  .rs-pwcontent { flex-direction: column; align-items: flex-start; gap: 16px; }
  .rs-pwbtn { width: 100%; justify-content: center; }
}
</style>
