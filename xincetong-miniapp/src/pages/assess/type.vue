<template>
  <view class="page">
    <ComplianceBar />

    <view class="header">
      <view class="back" @tap="goBack">返回</view>
      <view class="header-title">选择测评类型</view>
      <view class="back-placeholder" />
    </view>

    <view class="content">
      <view class="hero">
        <view class="hero-eyebrow">CREDIT ASSESSMENT</view>
        <view class="hero-title">信测通</view>
        <view class="hero-subtitle">免费 · 隐私 · 30 秒出结果</view>
        <view class="hero-line" />
        <view class="hero-desc">
          基于模拟评分卡，<text class="text-bold">不查征信</text>、<text class="text-bold">不上报数据</text>、<text class="text-bold">不构成贷款承诺</text>。所有结果仅供个人参考。
        </view>
      </view>

      <view class="section-head">
        <text class="section-index">01</text>
        <text class="section-title">选择业务类型</text>
      </view>

      <view class="type-list">
        <view
          v-for="(t, i) in types"
          :key="t.value"
          :class="['type-card', selected === t.value ? 'type-active' : '']"
          @tap="onSelect(t.value)"
        >
          <view class="type-card-num">{{ String(i + 1).padStart(2, '0') }}</view>
          <view class="type-card-body">
            <view class="type-name">{{ t.name }}</view>
            <view class="type-desc">{{ t.desc }}</view>
            <view class="type-points">
              <view v-for="p in t.points" :key="p" class="type-point">
                <text class="type-point-line">—</text>
                <text>{{ p }}</text>
              </view>
            </view>
          </view>
          <view class="type-card-arrow">›</view>
        </view>
      </view>

      <view class="disclaimer">
        实际审批以金融机构为准。<text class="text-bold">本平台与任何银行无合作关系</text>。
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import { useAssessmentStore } from '@/store/assessment'
import { useShareCode } from '@/composables/useShareCode'
import { pageView } from '@/utils/track'
import { hasPaidToken, getPaywallUrl } from '@/utils/paywall'

const store = useAssessmentStore()
const selected = ref<'personal' | 'business' | ''>('')

useShareCode()

const types = [
  {
    value: 'personal' as const,
    name: '个人信用贷',
    desc: '面向工薪 / 个体 / 自由职业',
    points: ['公积金 · 社保 · 工资代发', '房产 · 车辆 · 存款', '信用卡 · 贷款 · 逾期记录'],
  },
  {
    value: 'business' as const,
    name: '企业经营贷',
    desc: '面向法人 / 个体工商户',
    points: ['营业执照 · 经营年限', '对公流水 · 开票 · 纳税', '企业征信 · 法人征信'],
  },
] as const

onLoad(() => {
  pageView('assess/type')
  selected.value = store.type
})

function onSelect(v: 'personal' | 'business') {
  selected.value = v
  store.setType(v)
  // v22 决策：进入测评前先弹 9.9 付费墙（防 history redirectTo 绕过）
  if (!hasPaidToken()) {
    uni.redirectTo({ url: getPaywallUrl('type', v) })
    return
  }
  setTimeout(() => {
    uni.redirectTo({ url: '/pages/assess/step1-basic' })
  }, 200)
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';

.page {
  min-height: 100vh;
  background: $bg;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx;
  background: $card;
  border-bottom: 1rpx solid $border-light;
  .back { font-size: $font-md; color: $primary; width: 120rpx; }
  .back-placeholder { width: 120rpx; }
  .header-title {
    font-family: $ff-serif;
    font-size: $font-lg;
    font-weight: 600;
    color: $primary;
    letter-spacing: 2rpx;
  }
}

.content {
  padding: $space-5 $space-4 0;
  padding-bottom: calc($space-5 + env(safe-area-inset-bottom));
}

/* ===== Hero 区 ===== */
.hero {
  background: $primary;
  padding: $space-5 $space-4;
  color: $text-white;
  position: relative;
  margin: 0 (-$space-4);
  &-eyebrow {
    font-family: $ff-mono;
    font-size: $font-xs;
    color: $accent;
    letter-spacing: 4rpx;
    font-weight: 500;
  }
  &-title {
    font-family: $ff-serif;
    font-size: 64rpx;
    font-weight: 700;
    letter-spacing: 8rpx;
    margin-top: 12rpx;
    line-height: 1.1;
  }
  &-subtitle {
    font-size: $font-sm;
    color: rgba(255, 255, 255, 0.65);
    margin-top: 12rpx;
    letter-spacing: 6rpx;
  }
  &-line {
    width: 48rpx;
    height: 2rpx;
    background: $accent;
    margin: $space-3 0;
  }
  &-desc {
    font-size: $font-sm;
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.75);
    letter-spacing: 0.5rpx;
    .text-bold { color: $accent; }
  }
}

/* ===== 章节头 ===== */
.section-head {
  display: flex;
  align-items: baseline;
  gap: $space-2;
  margin: $space-5 0 $space-3;
  padding-bottom: $space-2;
  border-bottom: 1rpx solid $border;
}
.section-index {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 600;
  color: $accent;
}
.section-title {
  font-family: $ff-serif;
  font-size: $font-xl;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
}

/* ===== 卡片 ===== */
.type-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}
.type-card {
  position: relative;
  display: flex;
  background: $card;
  border: 1rpx solid $border-light;
  border-left: 4rpx solid $primary;
  padding: $space-4 $space-3;
  transition: all 0.2s;
  &.type-active {
    border-color: $primary;
    background: $primary-tint;
  }
  &-num {
    font-family: $ff-serif;
    font-size: $font-3xl;
    font-weight: 700;
    color: $primary;
    width: 96rpx;
    line-height: 1;
    flex-shrink: 0;
    letter-spacing: 0;
  }
  &-body { flex: 1; min-width: 0; }
  &-arrow {
    font-family: $ff-serif;
    font-size: 48rpx;
    color: $text-weak;
    line-height: 1;
    align-self: center;
    margin-left: $space-2;
  }
}
.type-name {
  font-family: $ff-serif;
  font-size: $font-xl;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
}
.type-desc {
  font-size: $font-sm;
  color: $text-sub;
  margin-top: 6rpx;
  letter-spacing: 0.5rpx;
}
.type-points {
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx dashed $border-light;
}
.type-point {
  display: flex;
  gap: 8rpx;
  font-size: $font-sm;
  color: $text-main;
  line-height: 1.8;
  letter-spacing: 0.5rpx;
  &-line { color: $accent; }
}

/* ===== 免责 ===== */
.disclaimer {
  margin-top: $space-5;
  font-size: $font-xs;
  color: $text-weak;
  text-align: center;
  line-height: 1.8;
  letter-spacing: 0.5rpx;
  padding: 0 $space-2;
  .text-bold { color: $text-sub; }
}
</style>
