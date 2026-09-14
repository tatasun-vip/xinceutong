<!--
  pay.vue · 付费页
  v3.2 重构：信息差驱动付费
  v22 新增：mode=pre-asses 模式（测评前付费墙，付完跳 select-bank 而非 report）
    - 顶部：核心问题高亮 + 严重度 + 影响量化（仅 post-asses 显示）
    - 中部：改善预期（前后对比）（仅 post-asses 显示）
    - 下部：3 套定价套餐（单次 / 3次卡 / 月卡）
    - 信任 + 退款 + CTA
-->
<template>
  <view class="pay-page">
    <ComplianceBar />

    <!-- Hero：紧迫感（mode 切换文案） -->
    <view class="pay-hero">
      <view class="pay-hero-badge">{{ isPreAsses ? 'START ASSESSMENT' : 'UNLOCK FULL REPORT' }}</view>
      <text class="pay-hero-eyebrow">{{ isPreAsses ? '完整测评通行证' : '完整诊断报告' }}</text>
      <text class="pay-hero-title">
        {{ isPreAsses ? '解锁完整测评 + 完整报告' : `解锁您的${issueCountText}` }}
      </text>
      <view class="pay-hero-line" />
      <text class="pay-hero-sub">
        {{ isPreAsses
          ? '一次性付费 · 24h 内可多次答题 · 含完整诊断报告 + 改善路径'
          : '看完整诊断 + 改善路径 + 改善后额度推演' }}
      </text>
    </view>

    <!-- 1. 核心问题高亮（1个已露的 + "还有 N 个隐藏"）（仅 post-asses） -->
    <view v-if="!isPreAsses && topIssue" class="pay-issue-card" :style="{ borderLeftColor: topIssue.severity_color }">
      <view class="pay-issue-head">
        <view class="pay-issue-tag" :style="{ background: topIssue.severity_color }">
          {{ severityLabel(topIssue.severity) }} · 已识别
        </view>
        <view class="pay-issue-cat">{{ topIssue.category }}</view>
      </view>
      <view class="pay-issue-title">{{ topIssue.title }}</view>
      <view class="pay-issue-impact">
        <view class="pay-issue-impact-row">
          <text class="pay-impact-icon">↓</text>
          <text class="pay-impact-text">{{ topIssue.impact_prob }}</text>
        </view>
        <view v-if="topIssue.impact_amount !== '—'" class="pay-issue-impact-row">
          <text class="pay-impact-icon">↓</text>
          <text class="pay-impact-text">{{ topIssue.impact_amount }}</text>
        </view>
        <view v-if="topIssue.impact_rate !== '—'" class="pay-issue-impact-row">
          <text class="pay-impact-icon">↑</text>
          <text class="pay-impact-text">{{ topIssue.impact_rate }}</text>
        </view>
      </view>
      <view v-if="hiddenCount > 0" class="pay-issue-hidden">
        <view class="pay-hidden-icon">
          <UiIcon name="lock" :size="24" color="#8B8B8B" />
        </view>
        <text class="pay-hidden-text">还有 {{ hiddenCount }} 个核心问题未显示</text>
      </view>
    </view>

    <!-- 2. 改善预期（前后对比）（仅 post-asses） -->
    <view v-if="!isPreAsses && projection" class="pay-projection-card">
      <view class="pay-proj-eyebrow">AFTER 90 DAYS · 改善后预计</view>
      <view class="pay-proj-arrow">
        <view class="pay-proj-col">
          <text class="pay-proj-label">当前</text>
          <text class="pay-proj-val" :style="{ color: levelCfg.color }">
            {{ currentLevel }} · {{ currentScore }}分
          </text>
          <text class="pay-proj-meta">通过率 {{ currentPassProb }}</text>
        </view>
        <view class="pay-proj-arrow-icon">→</view>
        <view class="pay-proj-col pay-proj-col-after">
          <text class="pay-proj-label">改善后</text>
          <text class="pay-proj-val" :style="{ color: PASS_PROB_COLOR[projection.pass_probability] || '#666' }">
            {{ projection.level }} · {{ projection.score }}分
          </text>
          <text class="pay-proj-meta">通过率 {{ projection.pass_probability }}</text>
        </view>
      </view>
      <view class="pay-proj-foot">
        <UiIcon name="lightbulb" :size="24" color="#C9A96E" />
        <text class="pay-proj-foot-text">按建议执行 90 天，额度预计提升 {{ formatLimitGap }}</text>
      </view>
    </view>

    <!-- 3. 完整报告内容（解锁后您将获得） -->
    <view class="pay-unlock-card">
      <view class="pay-unlock-head">
        <text class="pay-unlock-eyebrow">UNLOCKED CONTENT</text>
        <text class="pay-unlock-title">解锁后您将获得</text>
      </view>
      <view class="pay-unlock-list">
        <!-- pre-asses 模式：突出"开始测评"价值 -->
        <template v-if="isPreAsses">
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">1</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">5 步完整测评（30+ 个问题）</text>
              <text class="pay-unlock-item-desc">覆盖信用 / 资产 / 收入 / 保障 / 公共信息 5 维度</text>
            </view>
          </view>
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">2</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">6 大产品并行测算</text>
              <text class="pay-unlock-item-desc">公积金贷 / 工资贷 / 房抵贷 / 装修贷 / 税贷 / 消费贷</text>
            </view>
          </view>
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">3</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">完整诊断报告 + 改善路径</text>
              <text class="pay-unlock-item-desc">每问题含"是什么 / 为什么 / 影响 / 怎么改 / 预期"5 维展开</text>
            </view>
          </view>
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">4</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">24h 内可重复测评</text>
              <text class="pay-unlock-item-desc">改完资料再测一次，看分提升了多少</text>
            </view>
          </view>
        </template>
        <!-- post-asses 模式：突出"完整报告"价值 -->
        <template v-else>
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">1</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">{{ issueCountText }} · 5 维度深度分析</text>
              <text class="pay-unlock-item-desc">每个问题含「是什么 / 为什么 / 影响 / 怎么改 / 预期」5 维展开</text>
            </view>
          </view>
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">2</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">30 / 60 / 90 天改善路径</text>
              <text class="pay-unlock-item-desc">分阶段动作 + 预期效果，知道「坚持多久能看到结果」</text>
            </view>
          </view>
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">3</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">6 大产品完整对比</text>
              <text class="pay-unlock-item-desc">含测算逻辑 + 重点变量 + 申请策略</text>
            </view>
          </view>
          <view class="pay-unlock-item">
            <view class="pay-unlock-num">4</view>
            <view class="pay-unlock-body">
              <text class="pay-unlock-item-title">申请顺序策略</text>
              <text class="pay-unlock-item-desc">避免 1 次硬查询被浪费，先申请哪个有讲究</text>
            </view>
          </view>
        </template>
      </view>
    </view>

    <!-- 4. 定价套餐 -->
    <view class="pay-pricing-card">
      <view class="pay-pricing-head">
        <text class="pay-pricing-eyebrow">CHOOSE YOUR PLAN</text>
        <text class="pay-pricing-title">选择套餐</text>
      </view>
      <view
        v-for="(pkg, i) in packages"
        :key="pkg.code"
        class="pay-pkg"
        :class="{ 'pay-pkg-active': selectedPkg === pkg.code, 'pay-pkg-recommend': pkg.recommend }"
        @tap="selectedPkg = pkg.code"
      >
        <view v-if="pkg.recommend" class="pay-pkg-flag">推荐</view>
        <view class="pay-pkg-name">{{ pkg.name }}</view>
        <view class="pay-pkg-desc">{{ pkg.desc }}</view>
        <view class="pay-pkg-foot">
          <text class="pay-pkg-each">≈ ¥{{ pkg.perUse }} / 次</text>
          <text class="pay-pkg-price">¥<text class="pay-pkg-price-num">{{ pkg.price }}</text></text>
        </view>
      </view>
    </view>

    <!-- 5. 信任符号 -->
    <view class="pay-trust">
      <view class="pay-trust-cell">
        <text class="pay-trust-num">{{ siteStore.expertCount }}</text>
        <text class="pay-trust-label">金融专家校准</text>
      </view>
      <view class="pay-trust-cell">
        <text class="pay-trust-num">{{ siteStore.caseCount }}</text>
        <text class="pay-trust-label">真实案例回测</text>
      </view>
      <view class="pay-trust-cell">
        <text class="pay-trust-num">{{ siteStore.satisfaction }}%</text>
        <text class="pay-trust-label">用户好评</text>
      </view>
    </view>

    <!-- 6. 退款保障 -->
    <view class="pay-refund">
      <view class="pay-refund-icon">
        <UiIcon name="check" :size="32" color="#FFFFFF" />
      </view>
      <view class="pay-refund-body">
        <text class="pay-refund-title">7 天不满意全额退款</text>
        <text class="pay-refund-desc">我们对自己的报告有信心。觉得没价值联系客服即可退款，无理由。</text>
      </view>
    </view>

    <!-- 7. CTA -->
    <view class="pay-cta-area">
      <view class="pay-cta-price">
        <text class="pay-cta-price-original">原价 ¥19.9</text>
        <text class="pay-cta-price-now">¥<text class="pay-cta-price-num">{{ activePackage.price }}</text></text>
        <text class="pay-cta-price-tag">限时 5 折</text>
      </view>
      <button class="pay-cta-btn" :disabled="paying" @tap="handlePay">
        {{ paying ? '支付中…' : (isPreAsses ? `支付 ¥${activePackage.price} 开始测评` : `支付 ¥${activePackage.price} 立即解锁`) }}
      </button>
      <text class="pay-cta-tip">7 天内可申请退款 · 已服务 12.8 万用户</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import { createOrder, mockPay } from '@/api/order'
import { getFullReport } from '@/api/assessment'
import { useSiteStore } from '@/store/site'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { setPaidToken } from '@/utils/paywall'

const siteStore = useSiteStore()
const paying = ref(false)
const assessmentId = ref(0)
const topIssue = ref<any>(null)
const hiddenCount = ref(0)
const projection = ref<any>(null)
const currentLevel = ref('E')
const currentScore = ref(0)
const currentPassProb = ref('极低')
const selectedPkg = ref('once')

// v22 决策：mode=pre-asses 为测评前付费墙（付完跳 select-bank），否则为原 post-asses 流程
const isPreAsses = ref(false)
const fromSource = ref('index')  // 埋点：来源 index / history / type
const assessType = ref<'personal' | 'business'>('personal')

const LEVEL_COLOR: Record<string, string> = {
  S: '#1B5E20', A: '#2E7D32', B: '#558B2F', C: '#C9A96E', D: '#EF6C00', E: '#C62828',
}
const PASS_PROB_COLOR: Record<string, string> = {
  '高': '#2E7D32', '中高': '#558B2F', '中': '#C9A96E', '低': '#EF6C00', '极低': '#C62828',
}
const levelCfg = computed(() => ({ color: LEVEL_COLOR[currentLevel.value] || '#C62828' }))

// 定价套餐
const packages = [
  {
    code: 'once',
    name: '单次完整报告',
    desc: '一次解锁，永久查看',
    price: '9.9',
    perUse: '9.9',
    recommend: true,
  },
  {
    code: 'three',
    name: '3 次卡',
    desc: '反复优化资质用',
    price: '19.9',
    perUse: '6.6',
    recommend: false,
  },
  {
    code: 'month',
    name: '月卡（30 天 10 次）',
    desc: '高频测试 / 反复推演',
    price: '29.9',
    perUse: '3.0',
    recommend: false,
  },
]
const activePackage = computed(() => packages.find((p) => p.code === selectedPkg.value) || packages[0])

const issueCountText = computed(() => {
  const n = (hiddenCount.value || 0) + (topIssue.value ? 1 : 0)
  if (n === 0) return '完整报告'
  if (n === 1) return '1 个核心问题完整分析'
  return `${n} 个核心问题完整分析`
})

const formatLimitGap = computed(() => {
  if (!projection.value) return ''
  // projection 是"改善后"，需要与"当前"对比
  // 当前额度从 overall 取（但 free.vue 没存到本地，这里简化展示）
  return '若干万'
})

function severityLabel(sev: string): string {
  if (sev === 'high') return '高严重度'
  if (sev === 'mid') return '中严重度'
  return '低严重度'
}

onMounted(async () => {
  siteStore.load()
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  const opts = page.options || page.$route?.query || {}
  const id = (opts.id as string) || ''
  assessmentId.value = parseInt(id, 10) || 0

  // v22 解析付费墙模式
  const mode = (opts.mode as string) || 'post-asses'
  isPreAsses.value = mode === 'pre-asses'
  fromSource.value = (opts.from as string) || 'index'
  assessType.value = ((opts.type as string) === 'business' ? 'business' : 'personal')

  if (assessmentId.value) {
    try {
      const r = await getFullReport(assessmentId.value)
      topIssue.value = (r.top_issues || [])[0] || null
      hiddenCount.value = Math.max(0, (r.top_issues || []).length - 1)
      projection.value = r.improvement_projection || null
      currentLevel.value = r.overall.level || 'E'
      currentScore.value = r.overall.score || 0
      currentPassProb.value = r.overall.pass_probability || '极低'
    } catch (e) {
      console.error('加载报告预览失败', e)
    }
  }
})

async function handlePay() {
  if (paying.value) return
  // post-asses 模式必须有 assessmentId；pre-asses 模式不需要（只是开通 token）
  if (!isPreAsses.value && !assessmentId.value) {
    uni.showToast({ title: '测评 ID 缺失', icon: 'none' })
    return
  }
  paying.value = true
  try {
    if (isPreAsses.value) {
      // v22 pre-asses 模式：直接开通 paid_token（无需后端下单，因为还没测评）
      // 用 setTimeout 模拟支付动画
      await new Promise<void>((resolve) => setTimeout(resolve, 800))
      setPaidToken()
      uni.showToast({ title: '解锁成功', icon: 'success' })
      setTimeout(() => {
        // 跳到 select-bank，开始答题
        uni.redirectTo({ url: '/pages/assess/select-bank' })
      }, 1000)
    } else {
      const order = await createOrder({ assessment_id: assessmentId.value })
      await mockPay(order.order_no)
      uni.showToast({ title: '解锁成功', icon: 'success' })
      setTimeout(() => {
        uni.redirectTo({ url: `/pages/result/report?id=${assessmentId.value}` })
      }, 1000)
    }
  } catch (e: any) {
    uni.showModal({ title: '支付失败', content: e?.message || '请稍后重试', showCancel: false })
  } finally {
    paying.value = false
  }
}
</script>

<style lang="scss" scoped>
.pay-page {
  min-height: 100vh;
  background: #F5F3EF;
  padding-bottom: 80rpx;
}

/* === Hero（紧迫感） === */
.pay-hero {
  background: linear-gradient(180deg, #0F1B2D 0%, #1B2A4A 100%);
  padding: 56rpx 32rpx 80rpx;
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
.pay-hero-badge {
  display: inline-block;
  font-family: $ff-base;
  font-size: 24rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 600;
  padding: 6rpx 20rpx;
  border: 1rpx solid #C9A96E;
  margin-bottom: 24rpx;
}
.pay-hero-eyebrow {
  font-family: $ff-base;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 4rpx;
  display: block;
  margin-bottom: 12rpx;
}
.pay-hero-title {
  font-family: $ff-base;
  font-size: 44rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
  display: block;
  line-height: 1.3;
}
.pay-hero-line {
  width: 64rpx;
  height: 1rpx;
  background: rgba(201, 169, 110, 0.4);
  margin: 24rpx auto;
}
.pay-hero-sub {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 1rpx;
  display: block;
  line-height: 1.6;
}

/* === 1. 核心问题高亮 === */
.pay-issue-card {
  background: #FFFFFF;
  margin: -32rpx 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-left: 6rpx solid #C62828;
  position: relative;
  z-index: 1;
}
.pay-issue-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.pay-issue-tag {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #FFFFFF;
  padding: 4rpx 12rpx;
  letter-spacing: 1rpx;
  font-weight: 600;
}
.pay-issue-cat {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  padding: 2rpx 12rpx;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 4rpx;
}
.pay-issue-title {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 600;
  color: #0F1B2D;
  line-height: 1.4;
  margin-bottom: 20rpx;
  letter-spacing: 1rpx;
}
.pay-issue-impact {
  background: rgba(198, 40, 40, 0.04);
  padding: 16rpx 20rpx;
  border-left: 2rpx solid #C62828;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.pay-issue-impact-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.pay-impact-icon {
  color: #C62828;
  font-weight: 700;
  font-size: 24rpx;
  width: 24rpx;
}
.pay-impact-text {
  font-size: 26rpx;
  color: #0F1B2D;
  font-weight: 500;
  letter-spacing: 0.5rpx;
}
.pay-issue-hidden {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 16rpx;
  padding: 12rpx 16rpx;
  background: rgba(15, 27, 45, 0.04);
  border: 1rpx dashed rgba(15, 27, 45, 0.2);
}
.pay-hidden-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28rpx;
  height: 28rpx;
}
.pay-hidden-text {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
}

/* === 2. 改善预期 === */
.pay-projection-card {
  background: linear-gradient(135deg, rgba(201, 169, 110, 0.08), rgba(201, 169, 110, 0.04));
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(201, 169, 110, 0.3);
}
.pay-proj-eyebrow {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 20rpx;
}
.pay-proj-arrow {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.pay-proj-col {
  flex: 1;
  background: #FFFFFF;
  padding: 20rpx 16rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.pay-proj-col-after {
  background: linear-gradient(180deg, #FFFFFF, rgba(201, 169, 110, 0.08));
  border-color: rgba(201, 169, 110, 0.3);
}
.pay-proj-label {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 2rpx;
}
.pay-proj-val {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}
.pay-proj-meta {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
}
.pay-proj-arrow-icon {
  font-size: 32rpx;
  color: #C9A96E;
  font-weight: 700;
}
.pay-proj-foot {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  text-align: center;
  font-size: 24rpx;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
}
.pay-proj-foot-text {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
}

/* === 3. 解锁后内容 === */
.pay-unlock-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.pay-unlock-head {
  margin-bottom: 24rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
}
.pay-unlock-eyebrow {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
}
.pay-unlock-title {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
  display: block;
  margin-top: 8rpx;
}
.pay-unlock-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
.pay-unlock-item {
  display: flex;
  gap: 20rpx;
  align-items: flex-start;
}
.pay-unlock-num {
  width: 48rpx;
  height: 48rpx;
  line-height: 48rpx;
  text-align: center;
  background: rgba(201, 169, 110, 0.1);
  color: #C9A96E;
  font-family: $ff-base;
  font-size: 26rpx;
  font-weight: 700;
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  border-radius: 50%;
  flex-shrink: 0;
}
.pay-unlock-body {
  flex: 1;
  min-width: 0;
}
.pay-unlock-item-title {
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 600;
  color: #0F1B2D;
  display: block;
  margin-bottom: 4rpx;
  letter-spacing: 0.5rpx;
}
.pay-unlock-item-desc {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 0.3rpx;
  line-height: 1.6;
  display: block;
}

/* === 4. 定价套餐 === */
.pay-pricing-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.pay-pricing-head {
  margin-bottom: 24rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
}
.pay-pricing-eyebrow {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
}
.pay-pricing-title {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
  display: block;
  margin-top: 8rpx;
}
.pay-pkg {
  position: relative;
  padding: 24rpx;
  margin-bottom: 16rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  background: #FFFFFF;
  transition: all 0.2s;
  &:last-child { margin-bottom: 0; }

  &.pay-pkg-active {
    border-color: #C9A96E;
    background: linear-gradient(135deg, rgba(201, 169, 110, 0.05), rgba(201, 169, 110, 0.02));
    box-shadow: 0 4rpx 12rpx rgba(201, 169, 110, 0.15);
  }
  &.pay-pkg-recommend::before {
    content: '★';
    position: absolute;
    top: -2rpx;
    left: -2rpx;
    width: 32rpx;
    height: 32rpx;
    line-height: 32rpx;
    text-align: center;
    background: #C9A96E;
    color: #FFFFFF;
    font-size: 24rpx;
  }
}
.pay-pkg-flag {
  position: absolute;
  top: -10rpx;
  right: 24rpx;
  background: #C9A96E;
  color: #FFFFFF;
  font-family: $ff-base;
  font-size: 24rpx;
  padding: 4rpx 16rpx;
  letter-spacing: 1rpx;
  font-weight: 600;
}
.pay-pkg-name {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 600;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  margin-bottom: 8rpx;
}
.pay-pkg-desc {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
  margin-bottom: 16rpx;
}
.pay-pkg-foot {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding-top: 16rpx;
  border-top: 1rpx dashed rgba(15, 27, 45, 0.1);
}
.pay-pkg-each {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
}
.pay-pkg-price {
  font-family: $ff-base;
  font-size: 28rpx;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
  font-weight: 500;
}
.pay-pkg-price-num {
  font-size: 40rpx;
  font-weight: 700;
  margin-left: 4rpx;
}

/* === 5. 信任符号 === */
.pay-trust {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx 16rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  display: flex;
  justify-content: space-around;
}
.pay-trust-cell { text-align: center; flex: 1; }
.pay-trust-num {
  font-family: $ff-base;
  font-size: 40rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  display: block;
  line-height: 1;
}
.pay-trust-label {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  display: block;
  margin-top: 8rpx;
}

/* === 6. 退款保障 === */
.pay-refund {
  background: #FFFFFF;
  margin: 0 32rpx 32rpx;
  padding: 24rpx;
  border: 1rpx solid rgba(46, 125, 50, 0.3);
  display: flex;
  gap: 16rpx;
  align-items: flex-start;
}
.pay-refund-icon {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2E7D32;
  color: #FFFFFF;
  font-size: 28rpx;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}
.pay-refund-body { flex: 1; }
.pay-refund-title {
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 600;
  color: #2E7D32;
  display: block;
  margin-bottom: 6rpx;
  letter-spacing: 0.5rpx;
}
.pay-refund-desc {
  font-size: 24rpx;
  color: #8B8B8B;
  line-height: 1.6;
  display: block;
  letter-spacing: 0.3rpx;
}

/* === 7. CTA === */
.pay-cta-area {
  margin: 32rpx 32rpx 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.pay-cta-price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 12rpx;
  padding: 20rpx 0;
  background: rgba(201, 169, 110, 0.05);
  border: 1rpx dashed rgba(201, 169, 110, 0.3);
  margin-bottom: 8rpx;
}
.pay-cta-price-original {
  font-size: 24rpx;
  color: #8B8B8B;
  text-decoration: line-through;
  letter-spacing: 1rpx;
}
.pay-cta-price-now {
  font-family: $ff-base;
  font-size: 32rpx;
  color: #C9A96E;
  font-weight: 500;
  letter-spacing: 0.5rpx;
}
.pay-cta-price-num {
  font-size: 56rpx;
  font-weight: 700;
  margin-left: 4rpx;
}
.pay-cta-price-tag {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #C9A96E;
  padding: 2rpx 10rpx;
  background: rgba(201, 169, 110, 0.1);
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  letter-spacing: 1rpx;
  font-weight: 600;
}
.pay-cta-btn {
  width: 100%;
  height: 104rpx;
  line-height: 104rpx;
  background: #0F1B2D;
  color: #FFFFFF;
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 4rpx;
  border-radius: 0;
  border: none;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
  &:active { transform: scale(0.99); }
  &:disabled { opacity: 0.6; }
}
.pay-cta-tip {
  font-family: $ff-base;
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  display: block;
  text-align: center;
}
</style>
