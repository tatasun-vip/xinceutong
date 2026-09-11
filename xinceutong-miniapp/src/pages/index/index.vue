<!--
  Home / Index - 信测通首页
  设计原则（v3.2）：
    1. Hero 极简：只用 LOGO + 一句话。让 LOGO 自己说话，不堆叠重复品牌名
    2. 8rpx 网格：所有 padding/margin 走 8/16/24/32/48/64 标尺
    3. 硬边 + 直线：去掉胶囊、伪元素 hack、模糊阴影
    4. Editorial 编辑风：左侧对齐 / 大标题 / 细分割线 / 大留白
-->
<template>
  <view class="home page-bg">
    <ComplianceBar />

    <!-- ========== 1. Hero：只保留 LOGO + 副标题 ========== -->
    <view class="hero">
      <view class="hero-logo">
        <BrandLogo variant="shield" layout="icon" :size="200" mode="light" />
      </view>
      <view class="hero-brand">{{ siteStore.brandName }}</view>
      <view class="hero-rule" />
      <view class="hero-sub">{{ siteStore.brandSubtitle }}</view>
      <view class="hero-cta" @tap="scrollToCta">
        <text class="hero-cta-text">开始测评</text>
        <text class="hero-cta-arrow">↓</text>
      </view>
      <view class="hero-disclaimer">模拟测评 · 非银行官方 · 不查征信</view>
    </view>

    <!-- ========== 2. 数据背书条 ========== -->
    <DataStrip />

    <!-- ========== 3. 6 大产品类型 ========== -->
    <ProductStrip />

    <!-- ========== 4. 专业背书条（左 border 严格对齐）========== -->
    <view class="pro-bar">
      <text class="pro-title">模型逻辑参考银行信用贷审批框架</text>
      <text
        v-if="siteStore.expertCount > 0"
        class="pro-desc"
      >由 {{ siteStore.expertCount }} 位资深金融分析师与一线信贷从业者参与校准</text>
      <text class="pro-desc">覆盖个人信用贷与企业信用贷两大场景</text>
    </view>

    <!-- ========== 5. 核心卖点（4 条，无重复编号）========== -->
    <view class="features">
      <view class="features-head">
        <text class="features-eyebrow">CORE FEATURES</text>
        <text class="features-title">为什么选信测通</text>
      </view>
      <view
        v-for="f in features"
        :key="f.idx"
        class="feature-item"
      >
        <view class="feature-tick">
          <UiIcon name="check" :size="32" color="#ffffff" />
        </view>
        <view class="feature-text">
          <text class="feature-label">{{ f.label }}</text>
          <text class="feature-desc">{{ f.desc }}</text>
        </view>
      </view>
    </view>

    <!-- ========== 6. CTA 按钮区 ========== -->
    <view class="cta-area" id="cta-area">
      <button class="cta-btn cta-btn-primary" @tap="goAssess('personal')">
        {{ siteStore.ctaPersonal }}
      </button>
      <button class="cta-btn cta-btn-secondary" @tap="goAssess('business')">
        {{ siteStore.ctaBusiness }}
      </button>
      <text class="cta-tip">不查征信 · 2 分钟出结果</text>
    </view>

    <!-- ========== 7. 信任区 ========== -->
    <TrustZone />

    <!-- ========== 8. 入口 ========== -->
    <view class="entries">
      <view v-for="(e, i) in entries" :key="e.idx" class="entry" :class="{ 'is-last': i === entries.length - 1 }" @tap="goEntry(e)">
        <text class="entry-idx">{{ e.idx }}</text>
        <text class="entry-text">{{ e.text }}</text>
        <text class="entry-arrow">›</text>
      </view>
    </view>

    <!-- ========== 9. 底部合规 ========== -->
    <BottomCompliance />
  </view>
</template>

<script setup lang="ts">
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import BrandLogo from '@/components/brand-logo/brand-logo.vue'
import DataStrip from '@/components/data-strip/DataStrip.vue'
import ProductStrip from '@/components/product-strip/ProductStrip.vue'
import TrustZone from '@/components/trust-zone/TrustZone.vue'
import BottomCompliance from '@/components/bottom-compliance/BottomCompliance.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { useShare } from '@/composables/useShare'
import { useSiteStore } from '@/store/site'
import { useAssessmentStore } from '@/store/assessment'
import { pageView } from '@/utils/track'

const siteStore = useSiteStore()
const assessStore = useAssessmentStore()

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
  // v3.4 (2026-09-10): 先选银行 → 选产品，再进入 5 步问卷
  assessStore.setType(type)
  assessStore.reset()  // 清掉之前选择的银行/产品，重新选择
  uni.navigateTo({ url: '/pages/assess/select-bank' })
}
function scrollToCta() {
  uni.pageScrollTo({ selector: '#cta-area', duration: 300 })
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
   设计 token（局部 v3.2，scoped）
   - 8rpx 网格：4/8/16/24/32/48/64
   - 唯一品牌色：$primary（深蓝）+ $accent（金）
   ========================================================================= */
.home {
  min-height: 100vh;
  background: $bg;
  padding-bottom: 64rpx;
}

/* ========== Hero：极简到只剩 LOGO + 副标题 ========== */
.hero {
  background: $primary;
  padding: 96rpx 48rpx 80rpx;
  color: $text-white;
  text-align: center;
  position: relative;
  // 微妙的金色顶部装饰线（替代胶囊）
  &::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 96rpx;
    height: 2rpx;
    background: $accent;
  }
}
.hero-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32rpx;
}
.hero-brand {
  font-family: $ff-serif;
  font-size: 56rpx;
  font-weight: 700;
  letter-spacing: 16rpx;
  line-height: 1;
  // 用 padding-left 抵消最后一个字 letter-spacing 造成的视觉偏移
  padding-left: 16rpx;
}
.hero-rule {
  width: 48rpx;
  height: 2rpx;
  background: $accent;
  margin: 32rpx auto;
}
.hero-sub {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.78);
  letter-spacing: 2rpx;
  line-height: 1.7;
  max-width: 540rpx;
  margin: 0 auto;
  // 两端对齐（编辑感）
  text-align: justify;
  text-align-last: center;
}
.hero-cta {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 48rpx;
  padding: 16rpx 32rpx;
  // 透明底 + 金色下划线，替代"按钮"硬质感
  border-bottom: 1rpx solid $accent;
  animation: hero-bounce 2s ease-in-out infinite;
}
.hero-cta-text {
  font-family: $ff-serif;
  font-size: 30rpx;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.hero-cta-arrow {
  font-size: 24rpx;
  color: $accent;
  line-height: 1;
}
@keyframes hero-bounce {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(4rpx); }
}
.hero-disclaimer {
  margin-top: 32rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 2rpx;
}

/* ========== 专业背书条（去掉伪元素 hack，border-left 严格对齐）========== */
.pro-bar {
  background: $card;
  margin: 32rpx;
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

/* ========== 核心卖点（去掉重复编号，feature-tick 已是圆形）========== */
.features {
  background: $card;
  margin: 32rpx;
  padding: 32rpx;
}
.features-head {
  margin-bottom: 32rpx;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid $border-light;
}
.features-eyebrow {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
  margin-bottom: 8rpx;
}
.features-title {
  font-family: $ff-serif;
  font-size: 32rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1rpx;
  display: block;
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
  width: 48rpx;
  height: 48rpx;
  background: $primary;
  border-radius: 50%;
  flex-shrink: 0;
}
.feature-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0; // 防止 flex 子项溢出
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
  margin: 64rpx 32rpx 0;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  align-items: stretch;
}
.cta-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  font-family: $ff-serif;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 4rpx;
  border-radius: 0; // 硬边
  border: none;
  transition: all 200ms ease-out;
}
.cta-btn-primary {
  background: $primary;
  color: $text-white;
  box-shadow: 0 8rpx 24rpx rgba(11, 37, 69, 0.18);
}
.cta-btn-primary:active {
  transform: translateY(2rpx);
  box-shadow: 0 4rpx 12rpx rgba(11, 37, 69, 0.14);
}
.cta-btn-secondary {
  background: transparent;
  color: $primary;
  border: 1rpx solid $primary;
}
.cta-btn-secondary:active {
  background: rgba(15, 35, 64, 0.04);
}
.cta-tip {
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 2rpx;
  text-align: center;
  margin-top: 8rpx;
}

/* ========== 入口（去除视觉噪音，左对齐）========== */
.entries {
  background: $card;
  margin: 48rpx 32rpx 32rpx;
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
