<!--
  Home / Index - 信测通首页
  设计原则（v18 重设计 / v18.5 简化 tab / v19 完全去顶 nav 2026-09-14）：
    1. 编辑感节奏：每段加 01/02/03 section number + 8rpx hairline 分隔
    2. 颗粒对称：所有 padding/margin 走 8/16/24/32/48/64 标尺
    3. v19 去顶 nav：移动端品牌交给 ComplianceBar 顶部一条 + 落地页直接进 Hero
    4. Hero 单 CTA：v18.5 删除主测评按钮（防落地页转化分散），保留次查看方法论
    5. 9.9 banner 后置：先让产品说话再引导付费，节奏更自然
-->
<template>
  <view class="home page-bg">
    <ComplianceBar />

    <!-- ========== 1. Hero ========== -->
    <view class="section section-hero">
      <view class="hero">
        <view class="hero-eyebrow">{{ siteStore.brandTagline }}</view>
        <view class="hero-rule" />
        <view class="hero-brand">{{ siteStore.brandName }}</view>
        <view class="hero-sub">{{ siteStore.brandSubtitle }}</view>
        <view class="hero-cta-row">
          <view class="hero-cta hero-cta-secondary" @tap="goEntry(entries[0])">
            <text class="hero-cta-text-2">了解方法论</text>
          </view>
        </view>
        <view class="hero-disclaimer">模拟测评 · 非银行官方 · 不查征信</view>
      </view>
    </view>

    <!-- ========== 2. 数据背书条 ========== -->
    <view class="section">
      <DataStrip />
    </view>

    <!-- ========== 3. 6 大产品类型 ========== -->
    <view class="section">
      <ProductStrip />
    </view>

    <!-- ========== 4. 专业背书条（3 字段，节奏：1-2-3）========== -->
    <view class="section">
      <view class="pro-bar">
        <text class="pro-title">模型逻辑参考银行信用贷审批框架</text>
        <text
          v-if="parseCount(siteStore.expertCount) > 0"
          class="pro-desc"
        >由 {{ siteStore.expertCount }} 位资深金融分析师与一线信贷从业者参与校准</text>
        <text class="pro-desc">覆盖个人信用贷与企业信用贷两大场景</text>
      </view>
    </view>

    <!-- ========== 5. 核心卖点（4 条）========== -->
    <view class="section">
      <view class="features">
        <view class="features-head">
          <view class="features-head-left">
            <text class="features-eyebrow">CORE FEATURES</text>
            <text class="features-title">为什么选信测通</text>
          </view>
          <text class="features-head-num">04</text>
        </view>
        <view
          v-for="f in features"
          :key="f.idx"
          class="feature-item"
        >
          <view class="feature-tick">
            <UiIcon name="check" :size="24" color="#0B2545" />
          </view>
          <view class="feature-text">
            <text class="feature-label">{{ f.label }}</text>
            <text class="feature-desc">{{ f.desc }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- ========== 6. CTA 按钮区 ========== -->
    <view class="section">
      <view class="cta-area" id="cta-area">
        <button class="cta-btn cta-btn-primary" @tap="goAssess('personal')">
          {{ siteStore.ctaPersonal }}
        </button>
        <button class="cta-btn cta-btn-secondary" @tap="goAssess('business')">
          {{ siteStore.ctaBusiness }}
        </button>
        <text class="cta-tip">不查征信 · 2 分钟出结果</text>
      </view>
    </view>

    <!-- ========== 7. 信任区 ========== -->
    <view class="section">
      <TrustZone />
    </view>

    <!-- ========== 8. 入口 ========== -->
    <view class="section">
      <view class="entries">
        <view v-for="(e, i) in entries" :key="e.idx" class="entry" :class="{ 'is-last': i === entries.length - 1 }" @tap="goEntry(e)">
          <text class="entry-idx">{{ e.idx }}</text>
          <text class="entry-text">{{ e.text }}</text>
          <text class="entry-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- ========== 9. 底部合规 ========== -->
    <view class="section">
      <BottomCompliance />
    </view>

    <!-- ========== 10. 自定义 tabBar（v1 删测评 tab，2 tab 居中）========== -->
    <CustomTabbar />
  </view>
</template>

<script setup lang="ts">
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import DataStrip from '@/components/data-strip/DataStrip.vue'
import CustomTabbar from '@/components/custom-tabbar/CustomTabbar.vue'
import ProductStrip from '@/components/product-strip/ProductStrip.vue'
import TrustZone from '@/components/trust-zone/TrustZone.vue'
import BottomCompliance from '@/components/bottom-compliance/BottomCompliance.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { useShare } from '@/composables/useShare'
import { useSiteStore } from '@/store/site'
import { useAssessmentStore } from '@/store/assessment'
import { pageView } from '@/utils/track'
import { hasPaidToken, getPaywallUrl } from '@/utils/paywall'

const siteStore = useSiteStore()
const assessStore = useAssessmentStore()

/**
 * 把 siteStore 返回的格式化字符串（如 "128,000+"）解析回 number
 * 用于模板上的 v-if 渲染判断（避免 string > number TS 报错）
 */
function parseCount(s: string | number | undefined | null): number {
  const n = Number(String(s ?? '').replace(/[^0-9.]/g, ''))
  return Number.isFinite(n) ? n : 0
}

// ============ 卖点列表（去掉重复的 01-04 编号，feature-tick 自己表达）===========
const features = [
  { idx: 1, label: '不查征信',         desc: '不产生任何硬查询，模拟测评不留痕' },
  { idx: 2, label: '按产品独立建模',   desc: `不是一套模型套所有产品，${siteStore.productCount} 大产品类型分别测算` },
  { idx: 3, label: '一次测评看清差异', desc: '看到不同产品下的额度、通过概率（利率仅供参考）' },
  { idx: 4, label: '模型经得起推敲',   desc: '逻辑透明，结果可解释' },
]

// ============ 入口列表（配置化，左对齐）===========
const entries = [
  { idx: '01', text: '我们的方法论',     action: () => uni.navigateTo({ url: '/pages/about/methodology' }) },
  { idx: '02', text: `${siteStore.productCount} 大产品类型`, action: () => uni.navigateTo({ url: '/pages/about/products' }) },
  { idx: '03', text: '推广员素材库',     action: () => uni.navigateTo({ url: '/pages/promote/materials' }) },
  { idx: '04', text: '历史测评',         action: () => uni.navigateTo({ url: '/pages/mine/history' }) },
  { idx: '05', text: '法务咨询',         action: () => uni.navigateTo({ url: '/pages/legal/index' }) },
  { idx: '06', text: '推广员入驻',       action: () => uni.navigateTo({ url: '/pages/promoter/login' }) },
]

function goAssess(type: 'personal' | 'business') {
  assessStore.setType(type)
  assessStore.reset()
  // v22 决策：进入测评前先弹 9.9 付费墙（付完才进入答题）
  if (!hasPaidToken()) {
    uni.navigateTo({ url: getPaywallUrl('index', type) })
    return
  }
  uni.navigateTo({ url: '/pages/assess/select-bank' })
}
function goEntry(e: typeof entries[number]) {
  e.action()
}

pageView('index')

useShare({
  title: '信测通 - 别再用征信试错，模拟 6 大产品审批逻辑',
  path: '/pages/index/index',
})
</script>

<style lang="scss" scoped>
/* =========================================================================
   设计 token
   - 8rpx 网格：4/8/16/24/32/48/64
   - 品牌色：$primary（深蓝）+ $accent（金）
   - v18 节奏：每段用 .section 包裹，section 间 24rpx gap 留白呼吸
   ========================================================================= */
.home {
  min-height: 100vh;
  background-color: $bg;
  background-image: radial-gradient(rgba(11, 37, 69, 0.04) 1rpx, transparent 1rpx);
  background-size: 16rpx 16rpx;
  background-position: 0 0;
  padding-bottom: 64rpx;
}

/* ========== 段容器（v18 新增，节奏呼吸）========== */
.section {
  margin-top: 24rpx;
  &:first-child {
    margin-top: 0; // 顶部 nav 紧贴合规条
  }
}

/* ========== Hero（v18.1 收敛 / v19 紧贴 ComplianceBar）========== */
.section-hero {
  margin-top: 0; // 紧贴 ComplianceBar
}
.hero {
  background: $primary;
  padding: 64rpx 48rpx 56rpx;
  color: $text-white;
  text-align: center;
  position: relative;

  // 顶部 1rpx 金色 hairline（编辑感，颗粒）
  &::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 64rpx;
    height: 1rpx;
    background: $accent;
  }
}
.hero-eyebrow {
  font-family: $ff-mono;
  font-size: 24rpx;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.65);
  letter-spacing: 4rpx;
  text-transform: uppercase;
  line-height: 1;
  margin-bottom: 16rpx;
}
.hero-brand {
  font-family: $ff-serif;
  font-size: 60rpx;
  font-weight: 700;
  letter-spacing: 12rpx;
  line-height: 1;
  color: #FFFFFF;
  padding-left: 12rpx;
  margin-bottom: 20rpx;
}
.hero-rule {
  width: 48rpx;
  height: 2rpx;
  background: $accent;
  margin: 24rpx auto;
}
.hero-sub {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.78);
  letter-spacing: 2rpx;
  line-height: 1.7;
  max-width: 520rpx;
  margin: 0 auto 40rpx;
  text-align: justify;
  text-align-last: center;
}
.hero-cta-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  margin-top: 4rpx;
}
.hero-cta {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
  padding: 20rpx 32rpx;
  transition: background 200ms ease-out, transform 150ms ease-out;
  &:active { transform: scale(0.98); }
}
.hero-cta-primary {
  background: $accent;
  border: 1rpx solid $accent;
  box-shadow: 0 6rpx 20rpx rgba(184, 149, 84, 0.3);
  &:active { background: #A8843F; }
}
.hero-cta-secondary {
  background: transparent;
  border: 1rpx solid rgba(255, 255, 255, 0.4);
  &:active { background: rgba(255, 255, 255, 0.08); }
}
.hero-cta-text {
  font-family: $ff-serif;
  font-size: 26rpx;
  color: #FFFFFF;
  letter-spacing: 4rpx;
  font-weight: 600;
}
.hero-cta-text-2 {
  font-family: $ff-serif;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 2rpx;
  font-weight: 500;
}
.hero-cta-arrow {
  font-size: 24rpx;
  color: #FFFFFF;
  line-height: 1;
}
.hero-disclaimer {
  margin-top: 28rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 2rpx;
}

/* ========== 专业背书条 ========== */
.pro-bar {
  background: $card;
  margin: 0 32rpx;
  padding: 32rpx 32rpx 32rpx 40rpx;
  border-left: 4rpx solid $accent;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.pro-title {
  font-family: $ff-serif;
  font-size: 30rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
  line-height: 1.5;
}
.pro-desc {
  font-size: 26rpx;
  color: $text-sub;
  line-height: 1.7;
  letter-spacing: 0.3rpx;
}

/* ========== 核心卖点（v18 加段头 04 编号）========== */
.features {
  background: $card;
  margin: 0 32rpx;
  padding: 32rpx;
}
.features-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 32rpx;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid $border-light;
  gap: 16rpx;
}
.features-head-left {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
  flex: 1;
}
.features-eyebrow {
  font-family: $ff-mono;
  font-size: 24rpx;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
}
.features-title {
  font-family: $ff-serif;
  font-size: 32rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1rpx;
  display: block;
}
.features-head-num {
  font-family: $ff-serif;
  font-size: 56rpx;
  font-weight: 700;
  color: $primary;
  line-height: 1;
  font-feature-settings: 'tnum' 1;
  font-variant-numeric: tabular-nums;
  letter-spacing: 1rpx;
  opacity: 0.18; // 编辑感大号水印
  flex-shrink: 0;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 24rpx 0;
  border-bottom: 1rpx solid $border-light;
  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
}
.feature-tick {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36rpx;
  height: 36rpx;
  background: transparent;
  border: 1rpx solid $primary;
  border-radius: 50%;
  flex-shrink: 0;
}
.feature-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0;
}
.feature-label {
  font-family: $ff-serif;
  font-size: 30rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 0.5rpx;
}
.feature-desc {
  font-size: 26rpx;
  color: $text-sub;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
}

/* ========== CTA ========== */
.cta-area {
  margin: 0 32rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  align-items: stretch;
}
.cta-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  font-family: $ff-serif;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 4rpx;
  border-radius: 0;
  border: none;
  transition: all 200ms ease-out;
}
.cta-btn-primary {
  background: $primary;
  color: $text-white;
  box-shadow: 0 8rpx 24rpx rgba(11, 37, 69, 0.18);
  &:active {
    transform: translateY(2rpx);
    box-shadow: 0 4rpx 12rpx rgba(11, 37, 69, 0.14);
  }
}
.cta-btn-secondary {
  background: transparent;
  color: $primary;
  border: 1rpx solid $primary;
  &:active { background: rgba(15, 35, 64, 0.04); }
}
.cta-tip {
  font-size: 24rpx;
  color: $text-weak;
  letter-spacing: 2rpx;
  text-align: center;
  margin-top: 8rpx;
}

/* ========== 入口 ========== */
.entries {
  background: $card;
  margin: 0 32rpx;
}
.entry {
  display: flex;
  align-items: center;
  padding: 32rpx 24rpx;
  border-bottom: 1rpx solid $border-light;
  transition: background 150ms ease-out;
  &:active { background: rgba(15, 35, 64, 0.03); }
  &.is-last { border-bottom: none; }
}
.entry-idx {
  font-family: $ff-mono;
  font-size: 24rpx;
  color: $accent;
  font-weight: 600;
  width: 64rpx;
  letter-spacing: 1rpx;
  flex-shrink: 0;
}
.entry-text {
  flex: 1;
  font-size: 30rpx;
  color: $text-main;
  letter-spacing: 0.5rpx;
}
.entry-arrow {
  font-family: $ff-serif;
  color: $text-weak;
  font-size: 36rpx;
  line-height: 1;
  font-weight: 300;
}
</style>
