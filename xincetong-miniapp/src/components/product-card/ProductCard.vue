<!--
  ProductCard - 6 大产品卡
  用法：
    <ProductCard :product="..." :locked="false" :show-detail="true" @click="..." />
  用途：结果页/产品页通用
  v3.1 升级：所有图标改为 SVG 线性图标
-->
<template>
  <view class="product-card" :class="{ 'is-locked': locked, 'is-recommend': isUserBest }" @tap="onTap">
    <!-- 标题行 -->
    <view class="pc-head">
      <view class="pc-title">
        <text class="pc-name">{{ product.product_name }}</text>
        <!-- 报告页 ⭐：用「用户维度动态推荐」标志，绝不会和"通过率极低"同框 -->
        <view v-if="isUserBest" class="pc-star">
          <UiIcon name="star" :size="22" color="#c9a96e" />
          <text>推荐</text>
        </view>
      </view>
      <text v-if="product.pass_probability" class="pc-pass" :class="'pass-' + passClass">
        通过率 {{ product.pass_probability }}
      </text>
    </view>

    <!-- 副标题 -->
    <text v-if="product.product_subtitle" class="pc-sub">{{ product.product_subtitle }}</text>

    <!-- P3-2 cap 提示（按用户关注点：线上高/线下最高 + 用户填的数值好不能算出不切实际额度） -->
    <view v-if="showCapHint" class="pc-cap-hint">
      <UiIcon name="info" :size="20" color="#c9a96e" />
      <text class="pc-cap-hint-text">{{ product.limit_reason }}</text>
    </view>

    <!-- 额度/利率参考（核心数据；利率为参考项，不在推演范围） -->
    <view class="pc-data">
      <view class="pc-data-item">
        <text class="pc-label">模拟额度</text>
        <text class="pc-value pc-value-main" :class="{ 'pc-value-locked': locked }">
          {{ limitText }}
        </text>
      </view>
      <view class="pc-data-item">
        <text class="pc-label pc-label-ref">利率参考</text>
        <text class="pc-value pc-value-ref" :class="{ 'pc-value-locked': locked }">
          {{ rateText }}
        </text>
      </view>
    </view>

    <!-- P3-1 渠道双额度（线上/线下）— 让用户直接看到银行实际能给的最高额度 -->
    <view v-if="showChannelCaps" class="pc-channel">
      <view class="pc-channel-item">
        <text class="pc-channel-label">线上最高</text>
        <text class="pc-channel-val online">{{ channelOnlineText }}</text>
      </view>
      <view class="pc-channel-divider"></view>
      <view class="pc-channel-item">
        <text class="pc-channel-label">线下最高</text>
        <text class="pc-channel-val offline">{{ channelOfflineText }}</text>
      </view>
    </view>

    <text class="pc-ref-note">利率不在本平台推演范围 · 以银行实际报价为准</text>

    <!-- 详情：仅 show-detail 时显示 -->
    <view v-if="showDetail && !locked" class="pc-detail">
      <text class="pc-detail-label">本产品重点考察：</text>
      <view v-if="detail.focus_vars && detail.focus_vars.length" class="pc-vars">
        <text v-for="v in detail.focus_vars" :key="v" class="pc-var">{{ v }}</text>
      </view>
      <text v-if="detail.description" class="pc-desc">{{ detail.description }}</text>
    </view>

    <!-- 模糊遮罩 -->
    <view v-if="locked" class="pc-locked-mask">
      <view class="pc-locked-icon-wrap">
        <UiIcon name="lock" :size="56" color="#0f2340" />
      </view>
      <text class="pc-locked-text">解锁完整报告后可查看详情</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import type { ProductResult, ProductResultDetail } from '@/api/assessment'

interface Props {
  product: ProductResult | ProductResultDetail
  locked?: boolean
  showDetail?: boolean
  showLockIcon?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  locked: false,
  showDetail: false,
  showLockIcon: true,
})
const emit = defineEmits<{
  (e: 'click', product: ProductResult | ProductResultDetail): void
}>()

// 详情（focus_vars / description）只对 ProductResultDetail 有
const detail = computed(() => props.product as ProductResultDetail)

const limitText = computed(() => {
  if (props.locked) return '???'
  if (props.product.limit_min === 0 && props.product.limit_max === 0) return '—'
  const fmt = (n: number) => Math.round(n).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  if (props.product.limit_min === props.product.limit_max) return `${fmt(props.product.limit_min)} 元`
  return `${fmt(props.product.limit_min)}~${fmt(props.product.limit_max)} 元`
})

/**
 * P3-1 渠道上限（元 → 千分位 + 元，去"万"单位）
 * 当后端没传或为 0 时不展示该字段（老数据兼容）
 */
const channelOnlineText = computed(() => {
  const v = props.product.channel_online_max
  if (!v) return '—'
  return Math.round(v).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' 元'
})
const channelOfflineText = computed(() => {
  const v = props.product.channel_offline_max
  if (!v) return '—'
  return Math.round(v).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' 元'
})
const showChannelCaps = computed(() => {
  // 仅当有线上/线下上限数据时展示（unlock 后才有）
  return !props.locked && (props.product.channel_online_max || props.product.channel_offline_max)
})

/**
 * P3-2 cap 提示：被 cap 时显示 limit_reason
 */
const showCapHint = computed(() => {
  return !props.locked && props.product.limit_capped && props.product.limit_reason
})

const rateText = computed(() => {
  if (props.locked) return '???'
  if (props.product.rate_min === 0 && props.product.rate_max === 0) return '—'
  return `${props.product.rate_min}%-${props.product.rate_max}%`
})

const passClass = computed(() => {
  const p = props.product.pass_probability
  if (p === '高') return 'high'
  if (p === '中高') return 'mid-high'
  if (p === '中') return 'mid'
  if (p === '低') return 'low'
  return 'very-low'
})

/**
 * 报告页 ⭐ 显示依据：用户维度的动态推荐
 *   - 优先使用后端 best_for_user 标志
 *   - 兜底兼容：如果老数据没有该字段，再看 pass_probability
 *     避免"⭐ + 通过率极低"这种自相矛盾
 */
const isUserBest = computed(() => {
  const p = props.product as any
  if (typeof p.best_for_user === 'boolean') return p.best_for_user
  // 兜底：仅当有真实通过率时（不是"极低"或空）才显示 ⭐
  const pass = p.pass_probability
  return pass === '高' || pass === '中高' || pass === '中' || pass === '低'
})

function onTap() {
  if (!props.locked) emit('click', props.product)
}
</script>

<style lang="scss" scoped>
.product-card {
  position: relative;
  background: $card;
  border: 1rpx solid $border-light;
  border-left: 4rpx solid $primary;
  padding: 32rpx;
  margin-bottom: 24rpx;
  transition: all 0.2s;

  &.is-recommend {
    border-left-color: $accent;
    background: linear-gradient(to right, rgba(201, 169, 110, 0.04), $card 30%);
  }
  &.is-locked {
    overflow: hidden;
  }
}
.pc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8rpx;
}
.pc-title {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.pc-name {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
}
.pc-star {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  font-size: $font-xs;
  color: $accent;
  font-weight: 600;
  background: rgba(201, 169, 110, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
  letter-spacing: 1rpx;
}
.pc-pass {
  font-size: $font-xs;
  font-weight: 600;
  padding: 4rpx 16rpx;
  border-radius: 4rpx;
  letter-spacing: 1rpx;
  &.pass-high     { color: #2e7d32; background: rgba(46, 125, 50, 0.1); }
  &.pass-mid-high { color: #558b2f; background: rgba(85, 139, 47, 0.1); }
  &.pass-mid      { color: $accent; background: rgba(201, 169, 110, 0.1); }
  &.pass-low      { color: #ef6c00; background: rgba(239, 108, 0, 0.1); }
  &.pass-very-low { color: #c62828; background: rgba(198, 40, 40, 0.1); }
}
.pc-sub {
  display: block;
  font-size: $font-sm;
  color: $text-sub;
  margin-bottom: 24rpx;
  letter-spacing: 0.5rpx;
}
.pc-data {
  display: flex;
  gap: 32rpx;
  padding: 24rpx 0;
  border-top: 1rpx solid $border-light;
  border-bottom: 1rpx solid $border-light;
}
.pc-data-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.pc-label {
  font-size: $font-xs;
  color: $text-sub;
  letter-spacing: 0.5rpx;
}
.pc-label-ref {
  color: $text-weak;
  font-size: 22rpx;
}
.pc-value {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1rpx;
  &.pc-value-locked {
    color: $text-weak;
    letter-spacing: 4rpx;
  }
}
// 主推演值（额度）— 保持视觉强调
.pc-value-main {
  color: $primary;
  font-weight: 700;
}
// 参考值（利率）— 视觉降级
.pc-value-ref {
  font-family: $ff-mono;
  font-size: 28rpx;
  font-weight: 500;
  color: $text-sub;
  letter-spacing: 0.5rpx;
}
.pc-ref-note {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 0.5rpx;
  line-height: 1.6;
}

// === P3-1 渠道双额度（线上/线下）===
.pc-channel {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 20rpx;
  padding: 16rpx 20rpx;
  background: rgba(15, 35, 64, 0.04);
  border-radius: 4rpx;
}
.pc-channel-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.pc-channel-label {
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 0.5rpx;
}
.pc-channel-val {
  font-family: $ff-mono;
  font-size: 26rpx;
  font-weight: 600;
  letter-spacing: 0.5rpx;
  &.online { color: #1976d2; }   // 蓝：线上
  &.offline { color: #2e7d32; }  // 绿：线下（更稳）
}
.pc-channel-divider {
  width: 1rpx;
  height: 32rpx;
  background: rgba(15, 35, 64, 0.12);
}

// === P3-2 cap 提示（金色 info 图标 + 文字）===
.pc-cap-hint {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  margin: 16rpx 0 -4rpx;
  padding: 12rpx 16rpx;
  background: rgba(201, 169, 110, 0.08);
  border-left: 2rpx solid $accent;
  border-radius: 2rpx;
}
.pc-cap-hint-text {
  flex: 1;
  font-size: 22rpx;
  color: $text-sub;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
}
.pc-detail {
  margin-top: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.pc-detail-label {
  font-size: $font-xs;
  color: $text-sub;
  font-weight: 600;
  letter-spacing: 0.5rpx;
}
.pc-vars {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}
.pc-var {
  font-size: $font-xs;
  color: $primary;
  background: rgba(15, 35, 64, 0.05);
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
}
.pc-desc {
  font-size: $font-sm;
  color: $text-sub;
  line-height: 1.7;
  white-space: pre-wrap;
}
.pc-locked-mask {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  pointer-events: none;
}
.pc-locked-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 96rpx;
  height: 96rpx;
  background: rgba(15, 35, 64, 0.06);
  border: 1rpx solid rgba(15, 35, 64, 0.12);
  border-radius: 50%;
}
.pc-locked-text {
  font-size: $font-sm;
  color: $text-sub;
  letter-spacing: 1rpx;
}
</style>
