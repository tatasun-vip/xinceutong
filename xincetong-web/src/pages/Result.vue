<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'
import { bankApi, type Bank, type BankProduct } from '@/api/bank'
import { orderApi } from '@/api/order'
import { assessmentApi } from '@/api/assessment'
import { useAssessmentStore } from '@/store/assessment'

const route = useRoute()
const router = useRouter()
const store = useAssessmentStore()

const bank = ref<Bank | null>(null)
const products = ref<BankProduct[]>([])
const result = ref<any>(null)
const loading = ref(true)

// v11 增量：额度格式化（千分位 + 元，去"X.X 万"格式）
function formatLimit(min?: number, max?: number): string {
  if (!min && !max) return '—'
  const fmt = (n: number) => Math.round(n).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  if (min && max) {
    if (min === max) return `${fmt(min)} 元`
    return `${fmt(min)}~${fmt(max)} 元`
  }
  if (max) return `${fmt(max)} 元`
  return `${fmt(min || 0)} 元`
}

onMounted(async () => {
  // 1) 先从 store / sessionStorage 取结果（Loading 页面 setResult 写入）
  if (store.result && route.params.id == String(store.result.assessment_id)) {
    result.value = store.result
  } else if (route.query.r) {
    // 兜底：URL query 传过来（分享场景）
    try { result.value = JSON.parse(decodeURIComponent(route.query.r as string)) } catch {}
  }
  // 2) 兜底：直接 URL 访问（分享链接 / 浏览器刷新 / 新标签页）→ 调 API 拉取
  //    v9 增量：必须先有 result 才能拿到 bank_code 加载银行详情
  if (!result.value && route.params.id) {
    try {
      const id = String(route.params.id)
      const free = await assessmentApi.getFree(id) as any
      const apiData = free?.data || free
      // v9 增量：把 overall.{score,level,limit_min,...} 展平到 result.value 顶层
      // 模板按 r.score / r.level / r.limit_min 直接访问，API 返回在 r.overall.*
      result.value = { ...apiData, ...(apiData?.overall || {}) }
      // 兜底写回 store，方便其他组件（BankSelect / 历史记录）使用
      if (result.value && store.setResult) {
        store.setResult(result.value)
      }
    } catch (e: any) {
      ElMessage.error('加载报告失败：' + (e?.message || '网络异常'))
    }
  }
  // 3) 加载银行详情 + 产品
  //    优先用 store.bankCode（自然流程），否则用 result.bank_code（直接 URL 访问）
  const bankCode = store.bankCode || (result.value as any)?.bank_code
  try {
    if (bankCode) {
      const [bRes, pRes] = await Promise.all([
        bankApi.detail(bankCode),
        bankApi.products(bankCode),
      ])
      bank.value = bRes
      products.value = pRes.items
    }
  } catch (e: any) {
    ElMessage.error('加载结果失败：' + (e?.message || '网络异常'))
  } finally {
    loading.value = false
  }
  // v6 一致性：与 H5 端校验 data_hash
  if (result.value?.data_hash) {
    try {
      const snap = await orderApi.compareSnapshot(result.value.assessment_id) as any
      if (snap?.data_hash && snap.data_hash !== result.value.data_hash) {
        ElMessage.warning('数据已更新，建议刷新页面')
      }
    } catch {}
  }
  // M10 异步加载对比银行
  loadCompare()
})

function goBanks() { router.push('/banks') }
function goHome() { router.push('/') }

const LEVEL_COLORS_FALLBACK: Record<string, string> = {
  S: '#8E6F2C',
  A: '#2E7D32',
  B: '#0288D1',
  C: '#ED6C02',
  D: '#C62828',
  E: '#5C6B7C',
}

const LEVEL_DESC_FALLBACK: Record<string, string> = {
  S: '极佳 · 优质客户',
  A: '优秀 · 良好准入',
  B: '良好 · 标准准入',
  C: '一般 · 准入边界',
  D: '较弱 · 谨慎准入',
  E: '极弱 · 暂缓申请',
}

// v6 一致性：等级色/描述读后端 ui_config，无则 fallback
const LEVEL_COLORS = computed<Record<string, string>>(() => {
  const cfg = (result.value as any)?.ui_config?.level_config
  if (cfg) return Object.fromEntries(Object.entries(cfg).map(([k, v]: any) => [k, v.color]))
  return LEVEL_COLORS_FALLBACK
})
const LEVEL_DESC = computed<Record<string, string>>(() => {
  const cfg = (result.value as any)?.ui_config?.level_config
  if (cfg) return Object.fromEntries(Object.entries(cfg).map(([k, v]: any) => [k, v.desc]))
  return LEVEL_DESC_FALLBACK
})

import { computed } from 'vue'  // duplicate safe
const oneSentence = computed(() => {
  const r: any = result.value
  if (!r) return '请先完成测评查看结论'
  return r.one_sentence || r.free_summary || '当前资质需进一步评估'
})

// M4 30/60/90 时间轴（前端模板生成，依据 top_issue_free + level）
const timeline = computed(() => {
  const r: any = result.value
  if (!r) return []
  const level = r.level || 'E'
  const issue = r.top_issue_free
  const how = issue?.how || ''
  const title = issue?.title || '当前核心问题'
  const baseActions = (txt: string) =>
    txt.split(/[；;。\n]/).map(s => s.trim()).filter(s => s && s.length > 2).slice(0, 3)

  const phase30 = {
    day: 'D+30', phase: 'd30', title: '止血期 · 控制变量',
    actions: baseActions(how).length ? baseActions(how) : ['整理近 6 个月银行流水', '核对征信报告无误', '暂停新增信贷申请'],
    outcome: level <= 'B' ? '风险敞口初步收敛' : '完成问题项归因',
  }
  const phase60 = {
    day: 'D+60', phase: 'd60', title: '修复期 · 落地执行',
    actions: ['按 D30 建议逐项落地', '结清高息小额贷款', '保持信用卡使用率 < 70%'],
    outcome: '信用画像明显改善',
  }
  const phase90 = {
    day: 'D+90', phase: 'd90', title: '提升期 · 复测准入',
    actions: ['重新发起测评', '对比分数与等级变化', '选择通过概率 > 60% 的产品提交'],
    outcome: level <= 'B' ? '可进入正式申请流程' : '多数产品准入改善',
  }
  return [phase30, phase60, phase90]
})

// M7 图片分享卡
const shareCardRef = ref<HTMLElement | null>(null)
const generating = ref(false)
async function genShare() {
  const el = shareCardRef.value
  if (!el || !bank.value || !result.value) {
    ElMessage.warning('数据未就绪')
    return
  }
  generating.value = true
  try {
    const canvas = await html2canvas(el, {
      backgroundColor: '#0B2545',
      scale: 2,
      useCORS: true,
      logging: false,
    })
    const dataUrl = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = `测评报告-${bank.value.name}-${result.value.level || ''}.png`
    a.click()
    ElMessage.success('图片已下载，长按/转发给朋友')
  } catch (e: any) {
    ElMessage.error('生成失败：' + (e?.message || '未知错误'))
  } finally {
    generating.value = false
  }
}

// M8 AI 咨询入口（基于报告数据本地回答）
const chatOpen = ref(false)
const chatMsgs = ref<{ role: 'user' | 'ai'; text: string }[]>([])
const chatInput = ref('')
const chatThinking = ref(false)
const QUICK_QS = ['如何提高通过率？', '我现在能申请哪个产品？', 'D+90 后能改善多少？', '该不该现在申请？']

function aiAnswer(q: string): string {
  const r: any = result.value
  if (!r) return '请先完成测评'
  const lv = r.level || 'E'
  const issue = r.top_issue_free
  const bankName = bank.value?.name || '该行'
  if (/通过率|提高|怎么|如何/.test(q)) {
    if (issue) return `当前等级 ${lv}，${bankName} 重点关注：${issue.title}。${issue.how || ''}按 30/60/90 节奏落地，3 个月内可升至下一档，通过率会同步抬升。`
    return `当前等级 ${lv}，建议先修复主要风险项，再发起申请。`
  }
  if (/申请|产品|哪个|合适/.test(q)) {
    const top = products.value.find(p => p.recommend) || products.value[0]
    if (!top) return '当前没有匹配产品，建议先优化资质。'
    const m = productMatch(top)
    return `${bankName} 的「${top.name}」匹配度 ${m.idx}/100。${m.tips.join('；')}。`
  }
  if (/90|改善|提升|预测/.test(q)) {
    const p90 = prediction.value.find(p => p.day === 'D+90')
    if (!p90) return '数据不足'
    return `按当前修复节奏，90 天后等级预计从 ${lv} 升至 ${p90.level}，参考额度可达 ${formatLimit(p90.limit_min, p90.limit_max)}，利率 ${p90.rate_min}~${p90.rate_max}%。`
  }
  if (/现在|该不该|立刻/.test(q)) {
    if (['S','A','B'].includes(lv)) return `${lv} 级属于准入优秀，可立即提交申请，建议优先选 ${bankName} 主推产品。`
    return `${lv} 级建议先修复 top issue 再申请，强行申请会留硬查询记录，得不偿失。`
  }
  return '关于这份报告还有其他问题吗？'
}

async function sendChat(q?: string) {
  const text = (q || chatInput.value).trim()
  if (!text) return
  chatMsgs.value.push({ role: 'user', text })
  chatInput.value = ''
  chatThinking.value = true
  await new Promise(r => setTimeout(r, 600))
  chatMsgs.value.push({ role: 'ai', text: aiAnswer(text) })
  chatThinking.value = false
  // 滚动到底
  setTimeout(() => {
    const el = document.querySelector('.rs-chat-body')
    if (el) el.scrollTop = el.scrollHeight
  }, 50)
}

// M9 付费解锁
const payStep = ref<'idle' | 'creating' | 'paying' | 'done'>('idle')
const payOrderNo = ref('')
const payAmount = ref(9.99)
const payErr = ref('')

async function startUnlock() {
  if (!result.value) return
  payErr.value = ''
  payStep.value = 'creating'
  try {
    const r = await orderApi.create(result.value.assessment_id)
    payOrderNo.value = r.order_no
    payAmount.value = r.amount
    payStep.value = 'paying'
    const pay = await orderApi.mockPay(r.order_no)
    if (pay.status === 'paid') {
      payStep.value = 'done'
      // 标记已付费，刷新报告
      result.value = { ...result.value, is_paid: true }
      try {
        const full = await orderApi.fullReport(result.value.assessment_id)
        if (full?.full_report_md || full?.data) {
          result.value = { ...result.value, ...(full.data || full), full_report_md: full.full_report_md || full.data?.full_report_md }
        }
      } catch {}
      ElMessage.success('解锁成功！完整报告已开放')
    }
  } catch (e: any) {
    payErr.value = e?.message || '支付失败'
    payStep.value = 'idle'
    ElMessage.error(payErr.value)
  }
}

// M10 跨行快选
const compareBanks = ref<{ code: string; name: string; products: BankProduct[] }[]>([])
const compareLoading = ref(false)
const compareBankCode = ref<string | null>(null)

async function loadCompare() {
  if (compareBanks.value.length || !bank.value) return
  compareLoading.value = true
  try {
    const list = await bankApi.list()
    const others = list.items.filter((b: any) => b.code !== bank.value!.code).slice(0, 2)
    const arr: any[] = []
    for (const b of others) {
      try {
        const ps = await bankApi.products(b.code)
        arr.push({ code: b.code, name: b.name, products: ps.items || [] })
      } catch {}
    }
    compareBanks.value = arr
  } catch (e) {
    // 静默失败
  } finally {
    compareLoading.value = false
  }
}

function pickBank(code: string) {
  compareBankCode.value = code
  ElMessage.info('已切换：可点击下方"选择其他银行"重测')
  setTimeout(() => goBanks(), 600)
}

function topProductMatch(ps: BankProduct[]) {
  // v6 一致性：候选银行产品（无后端 matches 字段）退化为按准入分差额近似计算
  if (!ps.length) return null
  const r: any = result.value
  const score = r?.score || 0
  return ps.map(p => {
    const gap = Math.max(0, (p.pass_score_min || 0) - score)
    return { ...p, _gap: gap, _idx: Math.max(0, 100 - gap * 1.2) }
  }).sort((a, b) => b._idx - a._idx)[0]
}

// v6 一致性：产品匹配度直接读后端 product_matches（双端共用 SSOT）
const productMatch = (p: any) => {
  const r: any = result.value
  if (!r) return { idx: 0, gap: 0, tips: ['数据未就绪'] }
  const matches: any[] = r.product_matches || []
  const m = matches.find((x: any) => x.product_code === (p.code || p.product_code))
  if (m) return { idx: m.match_idx, gap: m.gap, tips: m.tips || [] }
  // 兜底：本地计算（数据未更新时）
  const score = r.score || 0
  const minReq = p.pass_score_min || 0
  const gap = Math.max(0, minReq - score)
  const idx = Math.max(0, Math.min(100, 100 - gap * 1.2))
  return { idx: Math.round(idx), gap, tips: gap > 0 ? [`分数差 ${gap} 分`] : ['当前资质可直接申请'] }
}
// v6 一致性：30/60/90 预测直接读后端 projection_table（双端共用 SSOT）
const prediction = computed<any[]>(() => {
  const r: any = result.value
  if (!r) return []
  if (Array.isArray(r.projection_table) && r.projection_table.length) return r.projection_table
  // 兜底空表，避免模板渲染崩溃
  return []
})
</script>

<template>
  <div class="rs" v-loading="loading">
    <div class="rs-inner container" v-if="bank">
      <div class="rs-empty" v-if="!result">
        <div class="rs-empty-title">暂无测评结果</div>
        <div class="rs-empty-sub">请先选择银行完成测评</div>
      </div>
      <div class="rs-head">
        <div class="text-eyebrow">ASSESSMENT RESULT · 测评结果</div>
        <h1 class="rs-title">{{ bank.name }} · 您的专属画像</h1>
        <div class="divider-line"></div>
        <p class="rs-sub">基于您填写的信息和该行评分卡模型，本次为模拟运算结果，不查征信、不读取任何银行数据。</p>
      </div>

      <div class="rs-m1">
        <div class="rs-m1-head"><span class="text-eyebrow">01</span><span>一句话结论</span></div>
        <div :class="['rs-m1-verdict','v--'+(result?.level||'E').toLowerCase()]">{{ oneSentence }}</div>
      </div>

      <!-- M2 占位 -->
      <div class="rs-m2" v-if="result?.top_issue_free"><h3 class="rs-m2-title">{{ result.top_issue_free.title }}</h3>
<p class="rs-m2-what">{{ result.top_issue_free.what }}</p>
<div class="rs-m2-5w">
<div class="rs-m2-w"><b>WHY：</b>{{ result.top_issue_free.why }}</div>
<div class="rs-m2-w"><b>IMPACT：</b>{{ result.top_issue_free.impact_prob }} · {{ result.top_issue_free.impact_amount }} · {{ result.top_issue_free.impact_rate }}</div>
<div class="rs-m2-w"><b>HOW：</b>{{ result.top_issue_free.how }}</div>
</div></div>

      <div class="rs-card">
        <div class="rs-card-left">
          <div class="rs-eyebrow text-eyebrow">CREDIT LEVEL</div>
          <div class="rs-level" :style="{ color: LEVEL_COLORS[result?.level || 'E'] }">
            <span class="rs-level-letter text-num">{{ result?.level || '—' }}</span>
            <span class="rs-level-desc">{{ LEVEL_DESC[result?.level || 'E'] }}</span>
          </div>
          <div class="rs-score">
            <div class="rs-score-label">SCORE</div>
            <div class="rs-score-num text-num">{{ result?.score ?? 0 }}</div>
            <div class="rs-score-bar">
              <div class="rs-score-bar-fill" :style="{ width: (result?.score ?? 0) + '%' }"></div>
            </div>
          </div>
          <div class="rs-pass">
            <span class="rs-pass-label">通过概率</span>
            <span class="rs-pass-val text-num">{{ result?.pass_probability || '—' }}</span>
          </div>
          <div class="rs-summary">{{ result?.free_summary || '请完成测评查看结果' }}</div>
        </div>

        <div class="rs-card-right">
          <div class="rs-stat">
            <div class="rs-stat-label">参考额度</div>
            <div class="rs-stat-val text-num">
              {{ formatLimit(result?.limit_min, result?.limit_max) }}
            </div>
          </div>
          <div class="rs-stat">
            <div class="rs-stat-label">参考利率</div>
            <div class="rs-stat-val text-num">{{ result?.rate_min || 0 }} ~ {{ result?.rate_max || 0 }} %</div>
          </div>
          <div class="rs-stat rs-stat-veto" v-if="result?.veto">
            <div class="rs-stat-label">触发一票否决</div>
            <div class="rs-stat-val" style="font-size: 14px; color: $danger">{{ result.veto.message }}</div>
          </div>
        </div>
      </div>

      <div class="rs-section" v-if="result?.risk_tags?.length || result?.advantages?.length || result?.weak_points?.length">
        <div class="rs-sec-title">
          <span class="text-mono">02 / DETAIL</span>
          <span>详细解读</span>
          <div class="divider-line"></div>
        </div>
        <div class="rs-tags-grid">
          <div class="rs-tag-col" v-if="result?.risk_tags?.length">
            <div class="rs-tag-col-title">风险标签</div>
            <div class="rs-tag-list">
              <span v-for="t in result.risk_tags" :key="t" class="rs-tag rs-tag-risk">{{ t }}</span>
            </div>
          </div>
          <div class="rs-tag-col" v-if="result?.advantages?.length">
            <div class="rs-tag-col-title">您的优势</div>
            <div class="rs-tag-list">
              <span v-for="t in result.advantages" :key="t" class="rs-tag rs-tag-adv">{{ t }}</span>
            </div>
          </div>
          <div class="rs-tag-col" v-if="result?.weak_points?.length">
            <div class="rs-tag-col-title">待优化</div>
            <div class="rs-tag-list">
              <span v-for="t in result.weak_points" :key="t" class="rs-tag rs-tag-weak">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- M4 30/60/90 时间轴 -->
      <div class="rs-m4" v-if="timeline.length">
        <div class="rs-sec-title">
          <span class="text-mono">04 / TIMELINE</span>
          <span>30 / 60 / 90 天行动建议</span>
          <div class="divider-line"></div>
        </div>
        <div class="rs-timeline">
          <div class="rs-tl-item" v-for="(t, i) in timeline" :key="i" :class="'rs-tl-'+t.phase">
            <div class="rs-tl-node">{{ t.day }}</div>
            <div class="rs-tl-body">
              <div class="rs-tl-title">{{ t.title }}</div>
              <ul class="rs-tl-list">
                <li v-for="(a, j) in t.actions" :key="j">{{ a }}</li>
              </ul>
              <div class="rs-tl-outcome" v-if="t.outcome">预期结果：{{ t.outcome }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- M5 额度/利率预测 -->
      <div class="rs-m5" v-if="prediction.length">
        <div class="rs-sec-title">
          <span class="text-mono">05 / PROJECTION</span>
          <span>30 / 60 / 90 天额度·利率预测</span>
          <div class="divider-line"></div>
        </div>
        <div class="rs-pred">
          <div v-for="(p, i) in prediction" :key="i" :class="['rs-pred-col', p.current ? 'rs-pred-cur' : '']">
            <div class="rs-pred-day">{{ p.day }}</div>
            <div class="rs-pred-lv" :style="{ color: LEVEL_COLORS[p.level] }">{{ p.level }}</div>
            <div class="rs-pred-score">{{ p.score }} <span>分</span></div>
            <div class="rs-pred-bar">
              <div class="rs-pred-bar-fill" :style="{ width: p.score + '%' }"></div>
            </div>
            <div class="rs-pred-meta">
              <div class="rs-pred-row"><span>额度</span><b>{{ formatLimit(p.limit_min, p.limit_max) }}</b></div>
              <div class="rs-pred-row"><span>利率</span><b>{{ p.rate_min }}~{{ p.rate_max }}%</b></div>
            </div>
            <div class="rs-pred-tag" v-if="!p.current">+{{ p.growth }}%</div>
          </div>
        </div>
        <div class="rs-pred-note">估算规则：按等级提升幅度线性外推 + 利率随等级下调，每 30 天 +1 等级为上限。</div>
      </div>

      <div class="rs-section">
        <div class="rs-sec-title">
          <span class="text-mono">03 / PRODUCTS</span>
          <span>{{ bank.name }} · 推荐产品</span>
          <div class="divider-line"></div>
        </div>
        <div class="rs-products">
          <div
            v-for="p in products"
            :key="p.id"
            :class="['rs-product', p.recommend ? 'rs-product-rec' : '']"
          >
            <div class="rs-m6-bar">
              <div class="rs-m6-bar-lbl">匹配度 <b>{{ productMatch(p).idx }}</b> / 100</div>
              <div class="rs-m6-bar-bg"><div class="rs-m6-bar-fill" :style="{ width: productMatch(p).idx + '%' }"></div></div>
            </div>
            <div class="rs-product-head">
              <div>
                <div class="rs-product-name">{{ p.name }}</div>
                <div class="rs-product-sub">{{ p.subtitle }}</div>
              </div>
              <span v-if="p.recommend" class="rs-product-badge">推荐</span>
            </div>
            <div class="divider-line" style="margin: 12px 0"></div>
            <div class="rs-product-meta">
              <div class="rs-product-stat">
                <div class="rs-product-stat-label">额度</div>
                <div class="rs-product-stat-val text-num">{{ p.limit_min }}-{{ p.limit_max }} 万</div>
              </div>
              <div class="rs-product-stat">
                <div class="rs-product-stat-label">利率</div>
                <div class="rs-product-stat-val text-num">{{ p.rate_min }}-{{ p.rate_max }} %</div>
              </div>
              <div class="rs-product-stat">
                <div class="rs-product-stat-label">准入分数</div>
                <div class="rs-product-stat-val text-num">≥ {{ p.pass_score_min }}</div>
              </div>
            </div>
            <div class="rs-product-features" v-if="p.features?.length">
              <span v-for="f in p.features" :key="f" class="rs-product-tag">{{ f }}</span>
            </div>
            <div class="rs-product-req" v-if="p.requirement">准入：{{ p.requirement }}</div>
            <div class="rs-m6-tips">
              <div v-for="(t, k) in productMatch(p).tips" :key="k" class="rs-m6-tip">{{ t }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="rs-foot">
        <el-button size="large" @click="goBanks">选择其他银行</el-button>
        <el-button size="large" :loading="generating" @click="genShare">生成分享图片</el-button>
        <el-button type="primary" size="large" @click="goHome">返回首页</el-button>
      </div>

      <!-- M9 付费解锁 -->
      <div class="rs-m9" v-if="!result?.is_paid">
        <div class="rs-m9-head">
          <div class="rs-m9-eyebrow text-mono">06 / PRO UNLOCK</div>
          <h3 class="rs-m9-title">解锁完整报告 · 一份钱看清所有隐藏风险</h3>
          <div class="divider-line" style="margin: 12px 0 24px"></div>
        </div>
        <div class="rs-m9-grid">
          <div class="rs-m9-free">
            <div class="rs-m9-col-title">免费版 <span>当前</span></div>
            <ul>
              <li>等级 / 分数 / 通过率</li>
              <li>一句话结论</li>
              <li>核心问题诊断</li>
              <li>30/60/90 行动建议</li>
              <li class="off">完整银行模型权重</li>
              <li class="off">5 大维度细分拆解</li>
              <li class="off">全部产品准入差距表</li>
              <li class="off">可下载 PDF 报告</li>
            </ul>
          </div>
          <div class="rs-m9-pro">
            <div class="rs-m9-badge">PRO · 推荐</div>
            <div class="rs-m9-col-title">完整报告 <span>¥{{ payAmount.toFixed(2) }}</span></div>
            <ul>
              <li>等级 / 分数 / 通过率</li>
              <li>一句话结论 + 详细解读</li>
              <li>核心问题 5 要素完整版</li>
              <li>30/60/90 行动 + 额度预测</li>
              <li>5 大维度细分拆解（负债/收入/信用/资产/查询）</li>
              <li>全部产品准入差距 + 优化路径</li>
              <li>完整银行模型权重 + 拒绝原因排序</li>
              <li>PDF 报告下载 + 90 天复测提醒</li>
            </ul>
            <el-button type="primary" size="large" class="rs-m9-btn" :loading="payStep==='creating'||payStep==='paying'" @click="startUnlock">
              {{ payStep==='idle' ? '立即解锁 ¥'+payAmount.toFixed(2) : payStep==='creating' ? '创建订单…' : payStep==='paying' ? '支付中…' : '已解锁' }}
            </el-button>
            <div class="rs-m9-err" v-if="payErr">{{ payErr }}</div>
            <div class="rs-m9-tip">支付后立即开放，1 年内可重复查看</div>
          </div>
        </div>
      </div>
      <div class="rs-m9-done" v-else>
        <div class="rs-m9-done-eyebrow text-mono">PRO · UNLOCKED</div>
        <div class="rs-m9-done-title">完整报告已开放 · 感谢您的支持</div>
        <div v-if="result?.full_report_md" class="rs-m9-md" v-html="result.full_report_md"></div>
      </div>

      <!-- M10 跨行快选 -->
      <div class="rs-m10" v-if="result">
        <div class="rs-sec-title">
          <span class="text-mono">07 / COMPARE</span>
          <span>换家银行试试 · 1v1 快速对比</span>
          <div class="divider-line"></div>
        </div>
        <div v-if="compareLoading" class="rs-m10-loading">加载其他银行…</div>
        <div v-else-if="!compareBanks.length" class="rs-m10-loading">暂无其他银行</div>
        <div v-else class="rs-m10-grid">
          <div class="rs-m10-cur">
            <div class="rs-m10-tag">当前</div>
            <div class="rs-m10-name">{{ bank.name }}</div>
            <div class="rs-m10-top" v-if="products[0]">
              <div class="rs-m10-row"><span>推荐产品</span><b>{{ products[0].name }}</b></div>
              <div class="rs-m10-row"><span>额度</span><b>{{ products[0].limit_min }}-{{ products[0].limit_max }} 万</b></div>
              <div class="rs-m10-row"><span>利率</span><b>{{ products[0].rate_min }}-{{ products[0].rate_max }}%</b></div>
              <div class="rs-m10-row"><span>准入分</span><b>≥{{ products[0].pass_score_min }}</b></div>
              <div class="rs-m10-idx">匹配度 <b>{{ Math.round(Math.max(0, Math.min(100, 100 - Math.max(0,(products[0].pass_score_min||0)-(result?.score||0))*1.2))) }}</b>/100</div>
            </div>
          </div>
          <div v-for="b in compareBanks" :key="b.code" class="rs-m10-cand" @click="pickBank(b.code)">
            <div class="rs-m10-tag alt">候选</div>
            <div class="rs-m10-name">{{ b.name }}</div>
            <div v-if="topProductMatch(b.products)" class="rs-m10-top">
              <div class="rs-m10-row"><span>推荐产品</span><b>{{ topProductMatch(b.products)!.name }}</b></div>
              <div class="rs-m10-row"><span>额度</span><b>{{ topProductMatch(b.products)!.limit_min }}-{{ topProductMatch(b.products)!.limit_max }} 万</b></div>
              <div class="rs-m10-row"><span>利率</span><b>{{ topProductMatch(b.products)!.rate_min }}-{{ topProductMatch(b.products)!.rate_max }}%</b></div>
              <div class="rs-m10-row"><span>准入分</span><b>≥{{ topProductMatch(b.products)!.pass_score_min }}</b></div>
              <div class="rs-m10-idx">预估匹配度 <b>{{ Math.round(topProductMatch(b.products)!._idx) }}</b>/100</div>
            </div>
            <div class="rs-m10-go">→ 用这家重测</div>
          </div>
        </div>
      </div>

      <!-- M8 AI 咨询入口 -->
      <div class="rs-ai-fab" @click="chatOpen = !chatOpen">
        <span class="rs-ai-fab-icon">AI</span>
        <span class="rs-ai-fab-txt">智能咨询</span>
      </div>
      <div class="rs-ai-mask" v-if="chatOpen" @click="chatOpen = false"></div>
      <div class="rs-ai-panel" v-if="chatOpen">
        <div class="rs-ai-head">
          <div>
            <div class="rs-ai-eyebrow">AI · ASSESSMENT COPILOT</div>
            <div class="rs-ai-title">报告解读助手</div>
          </div>
          <span class="rs-ai-close" @click="chatOpen = false">×</span>
        </div>
        <div class="rs-chat-body">
          <div v-if="!chatMsgs.length" class="rs-chat-empty">
            <div class="rs-chat-empty-t">试试问我</div>
            <div class="rs-chat-quick">
              <span v-for="(q, i) in QUICK_QS" :key="i" class="rs-chat-q" @click="sendChat(q)">{{ q }}</span>
            </div>
          </div>
          <div v-for="(m, i) in chatMsgs" :key="i" :class="['rs-chat-msg','rs-chat-'+m.role]">
            <div class="rs-chat-bubble">{{ m.text }}</div>
          </div>
          <div v-if="chatThinking" class="rs-chat-msg rs-chat-ai">
            <div class="rs-chat-bubble rs-chat-dot"><span></span><span></span><span></span></div>
          </div>
        </div>
        <div class="rs-ai-foot">
          <input v-model="chatInput" class="rs-ai-input" placeholder="输入你的问题…" @keydown.enter="sendChat()" />
          <button class="rs-ai-send" @click="sendChat()">发送</button>
        </div>
      </div>

      <!-- M7 分享卡（屏幕外渲染） -->
      <div class="rs-share-stage">
        <div ref="shareCardRef" class="rs-share">
          <div class="rs-share-bg"></div>
          <div class="rs-share-inner">
            <div class="rs-share-head">
              <div class="rs-share-logo">{{ bank.name.slice(0, 2) }}</div>
              <div>
                <div class="rs-share-eyebrow">CREDIT ASSESSMENT</div>
                <div class="rs-share-name">{{ bank.name }} · 专属画像</div>
              </div>
            </div>
            <div class="rs-share-divider"></div>
            <div class="rs-share-verdict">{{ oneSentence }}</div>
            <div class="rs-share-grid">
              <div class="rs-share-cell">
                <div class="rs-share-lbl">等级</div>
                <div class="rs-share-val" :style="{ color: LEVEL_COLORS[result?.level || 'E'] }">{{ result?.level || '—' }}</div>
              </div>
              <div class="rs-share-cell">
                <div class="rs-share-lbl">分数</div>
                <div class="rs-share-val">{{ result?.score || 0 }}</div>
              </div>
              <div class="rs-share-cell">
                <div class="rs-share-lbl">通过率</div>
                <div class="rs-share-val">{{ result?.pass_probability || '—' }}</div>
              </div>
            </div>
            <div class="rs-share-meta">
              参考额度 {{ formatLimit(result?.limit_min, result?.limit_max) }}
              · 利率 {{ result?.rate_min || 0 }}~{{ result?.rate_max || 0 }}%
            </div>
            <div class="rs-share-foot">
              <div class="rs-share-cta">扫码测一测你的专属画像</div>
              <div class="rs-share-qr">信策通 · 银行画像</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.rs {
  background: $bg;
  padding: $space-12 0 $space-20;
  min-height: calc(100vh - #{$header-height} - 28px);
}

.rs-inner {
  max-width: 1080px;
}

.rs-head {
  text-align: center;
  margin-bottom: $space-10;
  .divider-line { margin: $space-3 auto; }
}

.rs-title {
  font-family: $ff-serif;
  font-size: 32px;
  color: $primary;
  font-weight: 600;
  margin: $space-3 0;
  letter-spacing: 1px;
}

.rs-sub {
  font-size: $font-sm;
  color: $text-secondary;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.7;
}

/* ========== M1 一句话结论 ========== */
.rs-m1 { background: linear-gradient(135deg, $primary 0%, $primary-dark 100%); color: #fff; padding: 40px 32px; margin-bottom: 32px; border-left: 4px solid $accent; }
.rs-m1-head { display:flex; gap:12px; align-items:center; margin-bottom:16px; color: $accent-light; font-size:13px; letter-spacing:1px; }
.rs-m1-verdict { font-size: 24px; font-weight:600; line-height:1.5; color: #fff; font-family: $ff-serif; }

/* ========== 顶部大卡 ========== */
.rs-card {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  background: $bg-card;
  border: 1px solid $border-light;
  border-top: 3px solid $primary;
  margin-bottom: $space-8;
}

.rs-card-left {
  padding: $space-8 $space-6;
  border-right: 1px solid $border-light;
}

.rs-eyebrow {
  margin-bottom: $space-3;
}

.rs-level {
  display: flex;
  align-items: baseline;
  gap: $space-3;
  margin-bottom: $space-6;
}

.rs-level-letter {
  font-family: $ff-serif;
  font-size: 96px;
  font-weight: 700;
  line-height: 1;
}

.rs-level-desc {
  font-size: $font-lg;
  color: $text-secondary;
  letter-spacing: 1px;
}

.rs-score {
  margin-bottom: $space-5;
}

.rs-score-label {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.rs-score-num {
  font-family: $ff-serif;
  font-size: 48px;
  color: $primary;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 8px;
}

.rs-score-bar {
  height: 6px;
  background: $border-light;
  position: relative;
}

.rs-score-bar-fill {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, $primary 0%, $accent 100%);
  transition: width 0.6s ease;
}

.rs-pass {
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: $space-3 $space-4;
  background: $primary-tint;
  border-left: 3px solid $accent;
  margin-bottom: $space-5;
}

.rs-pass-label {
  font-size: $font-sm;
  color: $text-secondary;
  letter-spacing: 0.5px;
}

.rs-pass-val {
  font-size: $font-lg;
  color: $accent-dark;
  font-weight: 600;
}

.rs-summary {
  font-size: $font-sm;
  color: $text-secondary;
  line-height: 1.8;
  padding: $space-3 $space-4;
  background: $bg-soft;
  border-left: 2px solid $border-regular;
}

.rs-card-right {
  padding: $space-8 $space-6;
  display: flex;
  flex-direction: column;
  gap: $space-5;
}

.rs-stat-label {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.rs-stat-val {
  font-family: $ff-serif;
  font-size: 24px;
  color: $primary;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.rs-stat-veto .rs-stat-val { color: $danger !important; }

/* ========== 标签 ========== */
.rs-section {
  background: $bg-card;
  border: 1px solid $border-light;
  padding: $space-6;
  margin-bottom: $space-6;
}

.rs-sec-title {
  display: flex;
  align-items: center;
  gap: $space-3;
  font-family: $ff-serif;
  font-size: $font-lg;
  color: $primary;
  font-weight: 600;
  margin-bottom: $space-4;
  .divider-line { margin: 0; }
}

.rs-tags-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-5;
}

.rs-tag-col-title {
  font-size: $font-sm;
  color: $text-secondary;
  margin-bottom: $space-2;
  letter-spacing: 0.5px;
}

.rs-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.rs-tag {
  font-size: $font-xs;
  padding: 4px 10px;
  border: 1px solid;
  letter-spacing: 0.5px;
}

.rs-tag-risk { color: $danger; border-color: $danger; background: rgba(198, 40, 40, 0.06); }
.rs-tag-adv   { color: $success; border-color: $success; background: rgba(46, 125, 50, 0.06); }
.rs-tag-weak  { color: $warning; border-color: $warning; background: rgba(237, 108, 2, 0.06); }

/* ========== M4 时间轴 ========== */
.rs-m4 {
  background: $bg-card;
  border: 1px solid $border-light;
  border-left: 3px solid $primary;
  padding: $space-6;
  margin-bottom: $space-6;
}
.rs-timeline {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-4;
  position: relative;
}
.rs-tl-item {
  background: $bg-soft;
  border: 1px solid $border-light;
  border-top: 3px solid $primary;
  padding: $space-5;
  position: relative;
  display: flex;
  flex-direction: column;
}
.rs-tl-d30 { border-top-color: $danger; }
.rs-tl-d60 { border-top-color: $warning; }
.rs-tl-d90 { border-top-color: $success; }
.rs-tl-node {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $accent-dark;
  letter-spacing: 1px;
  margin-bottom: $space-2;
}
.rs-tl-title {
  font-family: $ff-serif;
  font-size: 18px;
  color: $primary;
  font-weight: 700;
  margin-bottom: $space-3;
  letter-spacing: 0.5px;
}
.rs-tl-list {
  list-style: none;
  padding: 0;
  margin: 0 0 $space-3 0;
  flex: 1;
}
.rs-tl-list li {
  font-size: $font-sm;
  color: $text-secondary;
  line-height: 1.7;
  padding-left: 16px;
  position: relative;
  margin-bottom: 6px;
}
.rs-tl-list li::before {
  content: '·';
  color: $accent;
  position: absolute;
  left: 4px;
  font-weight: 700;
  font-size: 18px;
  line-height: 1.2;
}
.rs-tl-outcome {
  font-size: $font-xs;
  color: $success;
  padding: 6px 10px;
  background: rgba(46, 125, 50, 0.06);
  border-left: 2px solid $success;
  margin-top: auto;
}
@media (max-width: 900px) {
  .rs-timeline { grid-template-columns: 1fr; }
}

/* ========== M5 预测表 ========== */
.rs-m5 {
  background: $bg-card;
  border: 1px solid $border-light;
  border-left: 3px solid $accent;
  padding: $space-6;
  margin-bottom: $space-6;
}
.rs-pred { display: grid; grid-template-columns: repeat(4, 1fr); gap: $space-3; }
.rs-pred-col {
  background: $bg-soft;
  border: 1px solid $border-light;
  border-top: 3px solid $border-regular;
  padding: $space-4;
  position: relative;
}
.rs-pred-cur { border-top-color: $primary; background: $primary-tint; }
.rs-pred-day {
  font-family: $ff-mono; font-size: $font-xs; color: $text-weak; letter-spacing: 1px; margin-bottom: 4px;
}
.rs-pred-lv {
  font-family: $ff-serif; font-size: 36px; font-weight: 700; line-height: 1; margin-bottom: 4px;
}
.rs-pred-score {
  font-family: $ff-serif; font-size: 14px; color: $primary; font-weight: 600; margin-bottom: 6px;
  span { font-size: 11px; color: $text-weak; font-weight: 400; }
}
.rs-pred-bar { height: 4px; background: $border-light; margin-bottom: $space-3; }
.rs-pred-bar-fill { height: 100%; background: linear-gradient(90deg, $primary, $accent); }
.rs-pred-row {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: $font-xs; padding: 4px 0; border-bottom: 1px dashed $border-light;
  span { color: $text-weak; }
  b { font-family: $ff-serif; color: $primary; font-weight: 600; }
}
.rs-pred-row:last-child { border-bottom: none; }
.rs-pred-tag {
  position: absolute; top: 8px; right: 8px;
  font-size: 11px; color: $success; background: rgba(46,125,50,0.1);
  border: 1px solid $success; padding: 1px 6px; font-family: $ff-mono;
}
.rs-pred-note {
  font-size: 12px; color: $text-weak; margin-top: $space-3; text-align: right; letter-spacing: 0.5px;
}
@media (max-width: 900px) { .rs-pred { grid-template-columns: repeat(2, 1fr); } }

/* ========== 产品 ========== */
.rs-products {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $space-4;
}

.rs-product {
  background: $bg-soft;
  border: 1px solid $border-light;
  border-left: 3px solid $primary;
  padding: $space-5;
  position: relative;
}

.rs-product-rec {
  border-left-color: $accent;
  background: $accent-bg;
}

.rs-product-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.rs-product-name {
  font-family: $ff-serif;
  font-size: 20px;
  color: $primary;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.rs-product-sub {
  font-size: $font-sm;
  color: $text-secondary;
}

.rs-product-badge {
  font-size: $font-xs;
  color: $accent-dark;
  border: 1px solid $accent;
  background: $bg-card;
  padding: 2px 8px;
  letter-spacing: 0.5px;
}

.rs-product-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-3;
  margin-bottom: $space-3;
}

.rs-product-stat-label {
  font-size: $font-xs;
  color: $text-weak;
  margin-bottom: 2px;
}

.rs-product-stat-val {
  font-family: $ff-serif;
  font-size: $font-md;
  color: $primary;
  font-weight: 600;
}

.rs-product-features {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.rs-product-tag {
  font-size: $font-xs;
  color: $primary;
  background: $bg-card;
  border: 1px solid $primary-tint;
  padding: 2px 6px;
}

.rs-product-req {
  font-size: $font-xs;
  color: $text-weak;
  margin-top: 4px;
  letter-spacing: 0.5px;
}

/* M6 产品匹配度 */
.rs-m6-bar { margin-bottom: $space-3; }
.rs-m6-bar-lbl {
  font-family: $ff-mono; font-size: 11px; color: $text-weak;
  display: flex; justify-content: space-between; margin-bottom: 4px; letter-spacing: 0.5px;
  b { color: $accent-dark; font-size: 13px; font-family: $ff-serif; }
}
.rs-m6-bar-bg { height: 4px; background: $border-light; }
.rs-m6-bar-fill { height: 100%; background: linear-gradient(90deg, $danger 0%, $warning 50%, $success 100%); transition: width 0.6s ease; }
.rs-m6-tips { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
.rs-m6-tip {
  font-size: 11px; color: $text-secondary; padding: 4px 8px;
  background: $bg-card; border-left: 2px solid $accent; letter-spacing: 0.3px;
}

/* ========== M7 分享卡 ========== */
.rs-share-stage {
  position: fixed;
  left: -9999px;
  top: 0;
  width: 750px;
}
.rs-share {
  width: 750px;
  height: 1000px;
  position: relative;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #fff;
  overflow: hidden;
}
.rs-share-bg {
  position: absolute; inset: 0;
  background: linear-gradient(135deg, #0B2545 0%, #13315C 60%, #1B3A6B 100%);
}
.rs-share-inner {
  position: relative; z-index: 1; padding: 60px 50px; height: 100%;
  display: flex; flex-direction: column;
}
.rs-share-head { display: flex; align-items: center; gap: 18px; }
.rs-share-logo {
  width: 64px; height: 64px; background: #C5A572; color: #0B2545;
  display: flex; align-items: center; justify-content: center;
  font-size: 28px; font-weight: 700; letter-spacing: 2px;
  border: 2px solid #E8C68C;
}
.rs-share-eyebrow { font-size: 12px; color: #C5A572; letter-spacing: 2px; }
.rs-share-name { font-size: 22px; color: #fff; font-weight: 600; margin-top: 4px; }
.rs-share-divider { height: 1px; background: linear-gradient(90deg, transparent, #C5A572, transparent); margin: 30px 0; }
.rs-share-verdict { font-size: 32px; line-height: 1.5; font-weight: 600; color: #fff; margin-bottom: 40px; }
.rs-share-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.rs-share-cell {
  background: rgba(255,255,255,0.06); border: 1px solid rgba(197,165,114,0.4);
  padding: 18px; text-align: center;
}
.rs-share-lbl { font-size: 12px; color: #C5A572; letter-spacing: 1.5px; margin-bottom: 8px; }
.rs-share-val { font-size: 36px; font-weight: 700; color: #fff; }
.rs-share-meta { font-size: 16px; color: rgba(255,255,255,0.85); padding: 14px 18px; background: rgba(255,255,255,0.05); border-left: 3px solid #C5A572; margin-bottom: 30px; }
.rs-share-foot { margin-top: auto; display: flex; justify-content: space-between; align-items: center; }
.rs-share-cta { font-size: 18px; color: #C5A572; font-weight: 600; letter-spacing: 1px; }
.rs-share-qr { font-size: 12px; color: rgba(255,255,255,0.5); border: 1px solid rgba(255,255,255,0.3); padding: 6px 12px; letter-spacing: 1px; }

/* ========== M10 跨行快选 ========== */
.rs-m10 { background: $bg-card; border: 1px solid $border-light; border-left: 3px solid $primary; padding: $space-6; margin-bottom: $space-6; }
.rs-m10-loading { text-align: center; color: $text-weak; padding: $space-5; font-size: $font-sm; letter-spacing: 1px; }
.rs-m10-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: $space-4; }
.rs-m10-cur, .rs-m10-cand {
  background: $bg-soft; border: 1px solid $border-light; border-top: 3px solid $primary;
  padding: $space-4; position: relative;
}
.rs-m10-cand { border-top-color: $accent; cursor: pointer; transition: all .2s; }
.rs-m10-cand:hover { background: $primary-tint; transform: translateY(-2px); box-shadow: 0 6px 18px rgba(11,37,69,0.12); }
.rs-m10-tag {
  position: absolute; top: 8px; right: 8px; font-size: 10px; padding: 2px 8px;
  background: $primary; color: #fff; font-family: $ff-mono; letter-spacing: 1px;
}
.rs-m10-tag.alt { background: $accent; color: $primary; }
.rs-m10-name { font-family: $ff-serif; font-size: 18px; color: $primary; font-weight: 700; margin-bottom: $space-3; letter-spacing: 1px; }
.rs-m10-row { display: flex; justify-content: space-between; font-size: $font-sm; padding: 6px 0; border-bottom: 1px dashed $border-light; }
.rs-m10-row span { color: $text-weak; }
.rs-m10-row b { color: $primary; font-family: $ff-serif; font-weight: 600; }
.rs-m10-idx { margin-top: 8px; font-size: 12px; color: $text-weak; b { color: $accent-dark; font-size: 14px; font-family: $ff-serif; } }
.rs-m10-go { margin-top: 12px; text-align: center; font-size: 13px; color: $accent-dark; font-weight: 600; padding: 8px; background: rgba(197,165,114,0.1); letter-spacing: 1px; }
@media (max-width: 900px) { .rs-m10-grid { grid-template-columns: 1fr; } }

/* ========== M9 付费解锁 ========== */
.rs-m9 {
  background: linear-gradient(135deg, $bg-card 0%, $primary-tint 100%);
  border: 1px solid $border-light;
  border-top: 3px solid $accent;
  padding: $space-8 $space-6;
  margin-bottom: $space-6;
  text-align: center;
}
.rs-m9-eyebrow { color: $accent-dark; }
.rs-m9-title { font-family: $ff-serif; font-size: 24px; color: $primary; font-weight: 600; margin-top: 8px; letter-spacing: 1px; }
.rs-m9-grid { display: grid; grid-template-columns: 1fr 1fr; gap: $space-4; max-width: 720px; margin: 0 auto; }
.rs-m9-free, .rs-m9-pro {
  background: $bg-card;
  border: 1px solid $border-light;
  padding: $space-5;
  text-align: left;
  position: relative;
}
.rs-m9-pro { border: 2px solid $accent; box-shadow: 0 6px 20px rgba(197,165,114,0.15); }
.rs-m9-badge {
  position: absolute; top: -10px; right: 16px;
  background: $accent; color: $primary; padding: 4px 10px;
  font-size: 11px; font-family: $ff-mono; letter-spacing: 1px; font-weight: 700;
}
.rs-m9-col-title {
  font-family: $ff-serif; font-size: 18px; color: $primary; font-weight: 700;
  margin-bottom: $space-3; padding-bottom: $space-2; border-bottom: 1px solid $border-light;
  display: flex; justify-content: space-between; align-items: baseline;
  span { font-size: 13px; color: $text-secondary; font-weight: 400; font-family: $ff-mono; }
}
.rs-m9-pro .rs-m9-col-title span { color: $accent-dark; font-weight: 600; }
.rs-m9-grid ul { list-style: none; padding: 0; margin: 0 0 $space-4 0; }
.rs-m9-grid li {
  font-size: $font-sm; color: $text-secondary; padding: 6px 0 6px 20px;
  position: relative; line-height: 1.6;
  &::before { content: '✓'; position: absolute; left: 0; color: $success; font-weight: 700; }
  &.off { color: $text-weak; &::before { content: '×'; color: $text-weak; } }
}
.rs-m9-btn { width: 100%; margin-top: $space-3; font-size: 15px; letter-spacing: 1px; }
.rs-m9-err { color: $danger; font-size: 12px; margin-top: 8px; }
.rs-m9-tip { font-size: 11px; color: $text-weak; margin-top: 8px; letter-spacing: 0.5px; }
.rs-m9-done {
  background: $primary-tint; border: 1px solid $success;
  border-top: 3px solid $success; padding: $space-5; margin-bottom: $space-6;
  text-align: center;
}
.rs-m9-done-eyebrow { color: $success; }
.rs-m9-done-title { font-family: $ff-serif; font-size: 20px; color: $primary; margin-top: 6px; }
.rs-m9-md { text-align: left; margin-top: 16px; font-size: 14px; line-height: 1.8; color: $text-secondary; }
@media (max-width: 700px) { .rs-m9-grid { grid-template-columns: 1fr; } }

/* ========== M8 AI 咨询 ========== */
.rs-ai-fab {
  position: fixed; right: 32px; bottom: 32px; z-index: 99;
  background: linear-gradient(135deg, $primary 0%, $primary-dark 100%);
  color: #fff; padding: 12px 20px; border: 1px solid $accent;
  display: flex; align-items: center; gap: 10px; cursor: pointer;
  box-shadow: 0 6px 24px rgba(11,37,69,0.35); transition: transform .2s;
}
.rs-ai-fab:hover { transform: translateY(-2px); }
.rs-ai-fab-icon {
  background: $accent; color: $primary; width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  font-family: $ff-serif; font-weight: 700; font-size: 14px; letter-spacing: 1px;
}
.rs-ai-fab-txt { font-size: 14px; letter-spacing: 1px; }
.rs-ai-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 100; }
.rs-ai-panel {
  position: fixed; right: 32px; bottom: 100px; width: 420px; max-width: calc(100vw - 64px);
  height: 560px; max-height: 70vh; background: #fff; z-index: 101;
  border: 1px solid $border-light; border-top: 3px solid $primary;
  display: flex; flex-direction: column; box-shadow: 0 12px 40px rgba(0,0,0,0.2);
}
.rs-ai-head { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid $border-light; }
.rs-ai-eyebrow { font-size: 11px; color: $accent-dark; letter-spacing: 1.5px; font-family: $ff-mono; }
.rs-ai-title { font-family: $ff-serif; font-size: 18px; color: $primary; font-weight: 700; margin-top: 2px; }
.rs-ai-close { font-size: 24px; color: $text-weak; cursor: pointer; line-height: 1; }
.rs-ai-close:hover { color: $danger; }
.rs-chat-body { flex: 1; overflow-y: auto; padding: 16px 20px; background: $bg-soft; }
.rs-chat-empty-t { font-size: 12px; color: $text-weak; letter-spacing: 1px; margin-bottom: 8px; }
.rs-chat-quick { display: flex; flex-wrap: wrap; gap: 6px; }
.rs-chat-q { font-size: 12px; padding: 6px 10px; background: #fff; border: 1px solid $primary-tint; color: $primary; cursor: pointer; }
.rs-chat-q:hover { background: $primary-tint; }
.rs-chat-msg { margin-bottom: 12px; display: flex; }
.rs-chat-ai { justify-content: flex-start; }
.rs-chat-user { justify-content: flex-end; }
.rs-chat-bubble { max-width: 80%; padding: 10px 14px; font-size: 14px; line-height: 1.6; }
.rs-chat-ai .rs-chat-bubble { background: #fff; color: $text-secondary; border: 1px solid $border-light; }
.rs-chat-user .rs-chat-bubble { background: $primary; color: #fff; }
.rs-chat-dot span { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: $text-weak; margin: 0 2px; animation: rs-dot 1.2s infinite; }
.rs-chat-dot span:nth-child(2) { animation-delay: .2s; }
.rs-chat-dot span:nth-child(3) { animation-delay: .4s; }
@keyframes rs-dot { 0%, 60%, 100% { transform: translateY(0); opacity: .4; } 30% { transform: translateY(-4px); opacity: 1; } }
.rs-ai-foot { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid $border-light; background: #fff; }
.rs-ai-input { flex: 1; padding: 10px 12px; border: 1px solid $border-light; font-size: 14px; outline: none; }
.rs-ai-input:focus { border-color: $primary; }
.rs-ai-send { background: $primary; color: #fff; border: none; padding: 0 18px; cursor: pointer; font-size: 14px; letter-spacing: 1px; }
.rs-ai-send:hover { background: $primary-dark; }

/* ========== 底部操作 ========== */
.rs-foot {
  text-align: center;
  margin-top: $space-8;
  display: flex;
  justify-content: center;
  gap: $space-3;
}

@media (max-width: 900px) {
  .rs-card { grid-template-columns: 1fr; }
  .rs-card-left { border-right: none; border-bottom: 1px solid $border-light; }
  .rs-tags-grid, .rs-products { grid-template-columns: 1fr; }
  .rs-m1-verdict { font-size: 20px; }
  .rs-title { font-size: 26px; }
  .rs-level-letter { font-size: 72px; }
  .rs-ai-panel { right: 16px; left: 16px; width: auto; bottom: 90px; }
  .rs-ai-fab { right: 16px; bottom: 16px; }
}

@media (max-width: 700px) {
  .rs-timeline { grid-template-columns: 1fr; }
  .rs-pred { grid-template-columns: 1fr; }
  .rs-m10-grid { grid-template-columns: 1fr; }
  .rs-m9-grid { grid-template-columns: 1fr; }
  .rs-pass, .rs-stat { flex-direction: column; align-items: flex-start; gap: 4px; }
  .rs-product-meta { grid-template-columns: 1fr 1fr; }
  .rs-share { width: 100vw; height: auto; min-height: 100vh; }
}

/* B 项 · 动效与空态 */
@keyframes rs-fade-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes rs-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(197, 165, 114, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(197, 165, 114, 0); }
}
.rs-m1, .rs-m2, .rs-m4, .rs-m5, .rs-m9, .rs-m10 {
  animation: rs-fade-in 0.5s ease both;
}
.rs-m2 { animation-delay: 0.05s; }
.rs-m4 { animation-delay: 0.1s; }
.rs-m5 { animation-delay: 0.15s; }
.rs-m9 { animation-delay: 0.2s; }
.rs-m10 { animation-delay: 0.25s; }
.rs-ai-fab { animation: rs-pulse 2.5s infinite; }
.rs-score-bar-fill { transition: width 1s cubic-bezier(0.16, 1, 0.3, 1); }
.rs-empty {
  text-align: center; padding: $space-10 $space-6; color: $text-weak;
  background: $bg-soft; border: 1px dashed $border-regular;
}
.rs-empty-title { font-family: $ff-serif; font-size: 18px; color: $text-secondary; margin-bottom: 8px; }
.rs-empty-sub { font-size: $font-sm; }
</style>
