<!--
  free.vue · 测评结果 · 免费版
  v3.2 重构：1 屏精准，吊胃口但不过分
    - 顶部：一句话结论（按 level 给颜色/动作）
    - 评分环 + 综合分
    - 1 个最高严重度问题（量化影响）
    - 6 大产品摘要（带 ⭐）
    - 强动机付费引导卡
-->
<template>
  <view class="free-page">
    <ComplianceBar />

    <view v-if="loading" class="loading-state">
      <view class="loading-spinner" />
      <view class="loading-text">加载中</view>
    </view>

    <template v-else-if="result">
      <!-- 报告头（深蓝渐变） -->
      <view class="fp-hero">
        <view class="fp-hero-eyebrow">CREDIT REPORT · 免费预览</view>
        <view class="fp-hero-line" />
        <view class="fp-hero-no">报告编号 · {{ result.report_no }}</view>
        <view class="fp-hero-time">生成时间 · {{ formatTime(result.created_at) }}</view>
      </view>

      <!-- 1. 一句话结论（按 overall 级别给颜色） -->
      <view v-if="result.one_sentence" class="fp-verdict" :class="'fp-verdict-' + levelClass">
        <view class="fp-verdict-icon">
          <UiIcon :name="verdictIcon" :size="40" :color="verdictColor" />
        </view>
        <view class="fp-verdict-body">
          <view class="fp-verdict-eyebrow">模拟评审结论</view>
          <view class="fp-verdict-text" :style="{ color: verdictColor }">
            {{ result.one_sentence }}
          </view>
        </view>
      </view>

      <!-- 2. 评分环（圆形，居中） -->
      <view class="fp-score-card">
        <view class="fp-score-eyebrow">OVERALL SCORE</view>
        <view class="fp-score-wrap">
          <svg class="fp-score-svg" viewBox="0 0 100 100">
            <circle class="fp-score-bg" cx="50" cy="50" r="42" />
            <circle
              class="fp-score-fill"
              cx="50" cy="50" r="42"
              :stroke="levelCfg.color"
              :stroke-dasharray="`${(result.overall.score / 100) * 264} 264`"
            />
          </svg>
          <view class="fp-score-center">
            <view class="fp-score-num" :style="{ color: levelCfg.color }">
              {{ result.overall.score }}
            </view>
            <view class="fp-score-unit">SCORE</view>
          </view>
        </view>
        <view class="fp-score-meta">
          <view class="fp-score-level" :style="{ color: levelCfg.color, borderColor: levelCfg.color }">
            {{ result.overall.level }} · {{ levelCfg.desc }}
          </view>
          <view class="fp-score-pass">
            <text class="fp-score-pass-label">综合通过率</text>
            <text
              class="fp-score-pass-val"
              :style="{ color: PASS_PROB_COLOR[result.overall.pass_probability] || '#666' }"
            >{{ result.overall.pass_probability }}</text>
          </view>
        </view>
        <view class="fp-score-amount">
          <text class="fp-amount-label">模拟额度</text>
          <text class="fp-amount-val">{{ formatLimit(result.overall.limit_min, result.overall.limit_max) }}</text>
        </view>
      </view>

      <!-- 3. 1 个核心问题（最高严重度） -->
      <view v-if="result.top_issue_free" class="fp-issue-card" :style="{ borderLeftColor: result.top_issue_free.severity_color }">
        <view class="fp-issue-head">
          <view class="fp-issue-tag" :style="{ background: result.top_issue_free.severity_color }">
            {{ severityLabel(result.top_issue_free.severity) }} · 核心问题
          </view>
          <view class="fp-issue-cat">{{ result.top_issue_free.category }}</view>
        </view>
        <view class="fp-issue-title">{{ result.top_issue_free.title }}</view>
        <view class="fp-issue-impact">
          <view class="fp-issue-impact-row">
            <text class="fp-impact-icon">↓</text>
            <text class="fp-impact-text">{{ result.top_issue_free.impact_prob }}</text>
          </view>
          <view v-if="result.top_issue_free.impact_amount && result.top_issue_free.impact_amount !== '—'" class="fp-issue-impact-row">
            <text class="fp-impact-icon">↓</text>
            <text class="fp-impact-text">{{ result.top_issue_free.impact_amount }}</text>
          </view>
        </view>
        <view class="fp-issue-tip">完整报告含 5 维度深度分析 + 改善路径 + 改善后推演</view>
      </view>

      <!-- 3.5 改善后推演（如果存在） -->
      <view v-if="result.improvement_projection" class="fp-projection-card">
        <view class="fp-proj-eyebrow">AFTER 90 DAYS · 改善后预计</view>
        <view class="fp-proj-arrow">
          <view class="fp-proj-col">
            <text class="fp-proj-label">当前</text>
            <text class="fp-proj-val" :style="{ color: levelCfg.color }">
              {{ result.overall.level }} · {{ result.overall.score }}分
            </text>
            <text class="fp-proj-meta">通过率 {{ result.overall.pass_probability }}</text>
          </view>
          <view class="fp-proj-arrow-icon">→</view>
          <view class="fp-proj-col fp-proj-col-after">
            <text class="fp-proj-label">改善后</text>
            <text class="fp-proj-val" :style="{ color: PASS_PROB_COLOR[result.improvement_projection.pass_probability] || '#666' }">
              {{ result.improvement_projection.level }} · {{ result.improvement_projection.score }}分
            </text>
            <text class="fp-proj-meta">通过率 {{ result.improvement_projection.pass_probability }}</text>
          </view>
        </view>
        <view class="fp-proj-foot">
          💡 修复 {{ result.improvement_projection.fixed_count }} 个核心问题后预计可达
        </view>
      </view>

      <!-- 4. 6 大产品摘要（带 ⭐） -->
      <view class="fp-products-card">
        <view class="fp-products-head">
          <text class="fp-products-eyebrow">PRODUCTS COMPARE</text>
          <text class="fp-products-title">各产品独立模拟结果</text>
        </view>
        <ProductCard
          v-for="(p, i) in result.product_results"
          :key="p.product_code"
          :product="p"
          :locked="i >= 5"
          :show-detail="false"
        />
      </view>

      <!-- 5. 强动机付费引导卡 -->
      <view v-if="!result.is_paid" class="fp-cta">
        <view class="fp-cta-eyebrow">UNLOCK FULL REPORT</view>
        <view class="fp-cta-title">查看完整诊断报告</view>
        <view class="fp-cta-bullets">
          <view class="fp-cta-bullet">
            <view class="fp-cta-bullet-tick">✓</view>
            <text class="fp-cta-bullet-text">{{ result.top_issues_total || 1 }} 个核心问题深度分析（影响量化 + 改善路径）</text>
          </view>
          <view class="fp-cta-bullet">
            <view class="fp-cta-bullet-tick">✓</view>
            <text class="fp-cta-bullet-text">6 大产品完整对比（含测算逻辑 + 重点变量）</text>
          </view>
          <view v-if="result.improvement_projection" class="fp-cta-bullet">
            <view class="fp-cta-bullet-tick">✓</view>
            <text class="fp-cta-bullet-text">30/60/90 天改善路径 + 改善后推演</text>
          </view>
          <view class="fp-cta-bullet">
            <view class="fp-cta-bullet-tick">✓</view>
            <text class="fp-cta-bullet-text">申请顺序策略（避免硬查询浪费）</text>
          </view>
        </view>
        <button class="fp-cta-btn" @tap="goPay">
          支付 {{ siteStore.payPrice }}，解锁完整报告
        </button>
        <text class="fp-cta-tip">7 天内不满意全额退款 · 已服务 12.8 万用户</text>
      </view>

      <!-- 免责声明 -->
      <view class="fp-disclaimer">
        <text class="fp-disc-title">关于本报告</text>
        <text class="fp-disc-line">{{ siteStore.disclaimerFullReport || defaultDisclaimer }}</text>
      </view>

      <!-- v6 修复：底部导航区（之前 free 报告出来只看到"支付"按钮，不付钱就没出口，
           用户只能按物理返回键，UX 极差。加"返回首页"+"查看我的报告"两个按钮） -->
      <view class="fp-footer-nav">
        <button class="fp-foot-btn fp-foot-btn-secondary" @tap="goHome">返回首页</button>
        <button class="fp-foot-btn fp-foot-btn-primary" @tap="goHistory">查看我的报告</button>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import ProductCard from '@/components/product-card/ProductCard.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { getFreeResult, type FreeResultRes } from '@/api/assessment'
import { useSiteStore } from '@/store/site'

const siteStore = useSiteStore()
const loading = ref(true)
const result = ref<FreeResultRes | null>(null)
const assessmentId = ref<number>(0)

const LEVEL_CONFIG: Record<string, { color: string; desc: string }> = {
  S: { color: '#1B5E20', desc: '极优' },
  A: { color: '#2E7D32', desc: '优质' },
  B: { color: '#558B2F', desc: '中上' },
  C: { color: '#C9A96E', desc: '一般' },
  D: { color: '#EF6C00', desc: '较弱' },
  E: { color: '#C62828', desc: '暂缓' },
}
const PASS_PROB_COLOR: Record<string, string> = {
  '高': '#2E7D32',
  '中高': '#558B2F',
  '中': '#C9A96E',
  '低': '#EF6C00',
  '极低': '#C62828',
}

const levelCfg = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  return LEVEL_CONFIG[lv] || LEVEL_CONFIG['E']
})

// 一句话结论的视觉风格
const levelClass = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return 'good'
  if (lv === 'B' || lv === 'C') return 'mid'
  return 'bad'  // D/E
})

const verdictIcon = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return 'check'
  if (lv === 'B' || lv === 'C') return 'info'
  return 'alert'
})

const verdictColor = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return '#2E7D32'
  if (lv === 'B' || lv === 'C') return '#C9A96E'
  return '#C62828'
})

function severityLabel(sev: string): string {
  if (sev === 'high') return '高严重度'
  if (sev === 'mid') return '中严重度'
  return '低严重度'
}

const defaultDisclaimer = `本报告由信测通模拟评审模型生成。模型逻辑参考银行信用贷审批框架，由 50+ 位资深金融分析师与一线信贷从业者参与校准。累计 20,000+ 真实案例回测验证。\n本报告基于您主动填写的信息进行模拟分析，所有评分、额度、利率、通过概率均为虚拟计算结果，不代表任何银行或金融机构的真实授信，不构成贷款承诺、投资建议或法律意见。\n实际审批结果受银行政策、市场环境、个人资质等多因素影响，可能与模拟结果存在差异。\n请勿将本报告作为贷款申请的唯一依据。`

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  const id = (page.options?.id || page.$route?.query?.id) as string
  assessmentId.value = parseInt(id, 10) || 0

  if (!assessmentId.value) {
    loading.value = false
    return
  }

  try {
    result.value = await getFreeResult(assessmentId.value)
  } catch (e) {
    console.error('加载免费结果失败', e)
  } finally {
    loading.value = false
  }

  siteStore.load()
})

function formatTime(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatLimit(min?: number, max?: number) {
  if (!min && !max) return '—'
  if (!min) return `${(max || 0) / 10000} 万`
  if (!max) return `${min / 10000} 万`
  return `${min / 10000}-${max / 10000} 万`
}

function goPay() {
  uni.navigateTo({ url: `/pages/result/pay?id=${assessmentId.value}` })
}

// v6 修复：报告页底部导航（返回首页 / 查看我的报告）
function goHome() {
  // switchTab 是跳到 tabBar 页（首页在 tabBar）的标准方式，会清空非 tabBar 页面栈
  uni.switchTab({
    url: '/pages/index/index',
    fail: () => {
      // 兜底：如果首页不是 tabBar，就 reLaunch
      uni.reLaunch({ url: '/pages/index/index' })
    },
  })
}
function goHistory() {
  // 查看我的报告（mine 历史）
  uni.switchTab({
    url: '/pages/mine/index',
    fail: () => {
      uni.navigateTo({ url: '/pages/mine/history' })
    },
  })
}
</script>

<style lang="scss" scoped>
/* ============================================
   免费版结果页 · v3.2
   设计风格：奢华金融
   - 深空蓝主色（#0F1B2D）
   - 金色描边（#C9A96E）
   - 大量留白 + 卡片化
   - serif 字体用于数字
   ============================================ */
.free-page {
  min-height: 100vh;
  background: #F5F3EF;
  padding-bottom: 80rpx;
}

/* === 加载态 === */
.loading-state {
  padding: 200rpx 0;
  text-align: center;
}
.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid rgba(15, 27, 45, 0.1);
  border-top-color: #0F1B2D;
  border-radius: 50%;
  margin: 0 auto 16rpx;
  animation: spin 1s linear infinite;
}
.loading-text { font-size: 28rpx; color: #8B8B8B; letter-spacing: 1rpx; }
@keyframes spin { to { transform: rotate(360deg); } }

/* === 报告头（深蓝渐变） === */
.fp-hero {
  background: linear-gradient(180deg, #0F1B2D 0%, #1B2A4A 100%);
  padding: 48rpx 32rpx 56rpx;
  text-align: center;
  color: #FFFFFF;
  position: relative;
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 80rpx;
    height: 2rpx;
    background: #C9A96E;
  }
}
.fp-hero-eyebrow {
  font-family: 'Courier New', monospace;
  font-size: 22rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 500;
}
.fp-hero-line {
  width: 48rpx;
  height: 1rpx;
  background: rgba(201, 169, 110, 0.4);
  margin: 24rpx auto;
}
.fp-hero-no, .fp-hero-time {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 1rpx;
  display: block;
  margin-top: 6rpx;
}

/* === 1. 一句话结论（首屏焦点） === */
.fp-verdict {
  background: #FFFFFF;
  margin: -32rpx 32rpx 0;
  padding: 32rpx;
  display: flex;
  gap: 24rpx;
  align-items: center;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-top: 4rpx solid #C9A96E;
  box-shadow: 0 8rpx 24rpx rgba(15, 27, 45, 0.06);
  position: relative;
  z-index: 1;

  &.fp-verdict-good { border-top-color: #2E7D32; }
  &.fp-verdict-mid  { border-top-color: #C9A96E; }
  &.fp-verdict-bad  { border-top-color: #C62828; }
}
.fp-verdict-icon {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(201, 169, 110, 0.08);
  border-radius: 50%;
  flex-shrink: 0;
}
.fp-verdict-body { flex: 1; min-width: 0; }
.fp-verdict-eyebrow {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 3rpx;
  margin-bottom: 8rpx;
  display: block;
}
.fp-verdict-text {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 34rpx;
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: 1rpx;
}

/* === 2. 评分卡 === */
.fp-score-card {
  background: #FFFFFF;
  margin: 24rpx 32rpx;
  padding: 48rpx 32rpx 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  text-align: center;
}
.fp-score-eyebrow {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
  margin-bottom: 24rpx;
}
.fp-score-wrap {
  position: relative;
  width: 240rpx;
  height: 240rpx;
  margin: 0 auto 24rpx;
}
.fp-score-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.fp-score-bg {
  fill: none;
  stroke: rgba(15, 27, 45, 0.08);
  stroke-width: 2;
}
.fp-score-fill {
  fill: none;
  stroke-width: 2;
  stroke-linecap: butt;
  transition: stroke-dasharray 0.8s ease;
}
.fp-score-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.fp-score-num {
  font-family: Georgia, serif;
  font-size: 72rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
  line-height: 1;
}
.fp-score-unit {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 4rpx;
  margin-top: 8rpx;
}
.fp-score-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  margin-bottom: 24rpx;
  flex-wrap: wrap;
}
.fp-score-level {
  font-family: Georgia, serif;
  font-size: 26rpx;
  font-weight: 600;
  padding: 6rpx 20rpx;
  border: 1rpx solid;
  letter-spacing: 2rpx;
}
.fp-score-pass {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
  padding: 6rpx 20rpx;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 999rpx;
}
.fp-score-pass-label {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
}
.fp-score-pass-val {
  font-family: Georgia, serif;
  font-size: 26rpx;
  font-weight: 700;
}
.fp-score-amount {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 12rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(15, 27, 45, 0.06);
}
.fp-amount-label {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
}
.fp-amount-val {
  font-family: Georgia, serif;
  font-size: 36rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
}

/* === 3. 核心问题卡（强烈刺激付费） === */
.fp-issue-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-left: 6rpx solid #C62828;
  position: relative;
}
.fp-issue-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.fp-issue-tag {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #FFFFFF;
  padding: 4rpx 12rpx;
  letter-spacing: 1rpx;
  font-weight: 600;
}
.fp-issue-cat {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  padding: 2rpx 12rpx;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 4rpx;
}
.fp-issue-title {
  font-family: Georgia, serif;
  font-size: 32rpx;
  font-weight: 600;
  color: #0F1B2D;
  line-height: 1.4;
  margin-bottom: 20rpx;
  letter-spacing: 1rpx;
}
.fp-issue-impact {
  background: rgba(198, 40, 40, 0.04);
  padding: 16rpx 20rpx;
  border-left: 2rpx solid #C62828;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 16rpx;
}
.fp-issue-impact-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.fp-impact-icon {
  color: #C62828;
  font-weight: 700;
  font-size: 24rpx;
}
.fp-impact-text {
  font-size: 26rpx;
  color: #0F1B2D;
  font-weight: 500;
  letter-spacing: 0.5rpx;
}
.fp-issue-tip {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
  line-height: 1.6;
  font-style: italic;
}

/* === 3.5 改善后推演（前后对比） === */
.fp-projection-card {
  background: linear-gradient(135deg, rgba(201, 169, 110, 0.08), rgba(201, 169, 110, 0.04));
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(201, 169, 110, 0.3);
}
.fp-proj-eyebrow {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 20rpx;
}
.fp-proj-arrow {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.fp-proj-col {
  flex: 1;
  background: #FFFFFF;
  padding: 20rpx 16rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.fp-proj-col-after {
  background: linear-gradient(180deg, #FFFFFF, rgba(201, 169, 110, 0.08));
  border-color: rgba(201, 169, 110, 0.3);
}
.fp-proj-label {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 2rpx;
}
.fp-proj-val {
  font-family: Georgia, serif;
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}
.fp-proj-meta {
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
}
.fp-proj-arrow-icon {
  font-size: 32rpx;
  color: #C9A96E;
  font-weight: 700;
}
.fp-proj-foot {
  text-align: center;
  font-size: 22rpx;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
}

/* === 4. 6 大产品摘要 === */
.fp-products-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.fp-products-head {
  margin-bottom: 24rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
}
.fp-products-eyebrow {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
}
.fp-products-title {
  font-family: Georgia, serif;
  font-size: 32rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
  display: block;
  margin-top: 8rpx;
}

/* === 5. 付费 CTA === */
.fp-cta {
  background: #FFFFFF;
  margin: 32rpx;
  padding: 40rpx 32rpx;
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  border-top: 4rpx solid #C9A96E;
  box-shadow: 0 12rpx 32rpx rgba(15, 27, 45, 0.08);
}
.fp-cta-eyebrow {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 12rpx;
}
.fp-cta-title {
  font-family: Georgia, serif;
  font-size: 36rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
  margin-bottom: 24rpx;
  line-height: 1.3;
}
.fp-cta-bullets {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-bottom: 32rpx;
}
.fp-cta-bullet {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}
.fp-cta-bullet-tick {
  width: 32rpx;
  height: 32rpx;
  line-height: 32rpx;
  text-align: center;
  background: #C9A96E;
  color: #FFFFFF;
  font-weight: 700;
  border-radius: 50%;
  font-size: 22rpx;
  flex-shrink: 0;
}
.fp-cta-bullet-text {
  flex: 1;
  font-size: 26rpx;
  color: #0F1B2D;
  line-height: 1.6;
  letter-spacing: 0.5rpx;
}
.fp-cta-btn {
  width: 100%;
  height: 100rpx;
  line-height: 100rpx;
  background: #0F1B2D;
  color: #FFFFFF;
  font-family: Georgia, serif;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 4rpx;
  border-radius: 0;
  border: none;
  margin-bottom: 16rpx;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;

  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(201, 169, 110, 0.2);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.4s, height 0.4s;
  }
  &:active {
    transform: scale(0.98);
    &::after { width: 200%; height: 200%; }
  }
}
.fp-cta-tip {
  font-family: 'Courier New', monospace;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  display: block;
  text-align: center;
}

/* === 免责声明 === */
.fp-disclaimer {
  margin: 48rpx 32rpx 0;
  padding: 24rpx;
  background: rgba(0, 0, 0, 0.02);
  border: 1rpx solid rgba(0, 0, 0, 0.06);
}
.fp-disc-title {
  font-family: Georgia, serif;
  font-size: 24rpx;
  font-weight: 600;
  color: #0F1B2D;
  display: block;
  margin-bottom: 12rpx;
  letter-spacing: 1rpx;
}
.fp-disc-line {
  font-size: 22rpx;
  color: #8B8B8B;
  line-height: 1.8;
  display: block;
  white-space: pre-wrap;
  letter-spacing: 0.3rpx;
}

/* v6 修复：底部导航区 */
.fp-footer-nav {
  display: flex;
  gap: 24rpx;
  margin: 48rpx 32rpx 0;
  padding-top: 32rpx;
  border-top: 1rpx solid rgba(15, 27, 45, 0.08);
}
.fp-foot-btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  font-size: 28rpx;
  font-weight: 500;
  letter-spacing: 1rpx;
  border-radius: 8rpx;
  border: none;
  font-family: inherit;
  text-align: center;
}
.fp-foot-btn-secondary {
  background: #FFFFFF;
  color: #0F1B2D;
  border: 1rpx solid #0F1B2D;
}
.fp-foot-btn-primary {
  background: #0F1B2D;
  color: #FFFFFF;
}
.fp-foot-btn::after { border: none; }
</style>
