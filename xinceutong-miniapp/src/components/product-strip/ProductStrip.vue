<!--
  ProductStrip - 6 大产品名横排
  v3.3 (2026-09): 利率与 2026 银行实际对齐
    - 展示规范：起始年化 + 区间
    - 格式：2.88% 起 ｜ 区间 2.88% - 4.50%
    - 视觉：硬边 1rpx border + 序号 + 个人/企业标签
-->
<template>
  <view class="product-strip">
    <view class="ps-head">
      <view class="ps-head-left">
        <text class="ps-eyebrow">PRODUCT COVERAGE</text>
        <text class="ps-title">{{ siteStore.productCount }} 大产品类型独立建模</text>
      </view>
      <text class="ps-head-tip">2026.09</text>
    </view>
    <view class="ps-grid">
      <view
        v-for="(p, i) in productTypes"
        :key="p.code"
        class="ps-item"
        :class="{ 'is-personal': p.user_type === 'personal' }"
      >
        <view class="ps-item-head">
          <text class="ps-num">{{ String(i + 1).padStart(2, '0') }}</text>
          <text class="ps-user-tag">{{ p.user_type === 'personal' ? '个人' : '企业' }}</text>
        </view>
        <text class="ps-name">{{ p.name }}</text>
        <view class="ps-rate-row">
          <text class="ps-rate-from">{{ formatRate(p.rate_min) }}%</text>
          <text class="ps-rate-sep">起</text>
        </view>
        <text class="ps-rate-range">区间 {{ formatRate(p.rate_min) }}% – {{ formatRate(p.rate_max) }}%</text>
      </view>
    </view>
    <view class="ps-footer">
      <text class="ps-disclaimer">本平台不推演利率 · 区间仅作信息参考 · 实际利率以银行审批报价为准</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSiteStore } from '@/store/site'
import { getProductTypes } from '@/api/product'

const siteStore = useSiteStore()
const productTypes = ref<Array<{ code: string; name: string; rate_min: number; rate_max: number; user_type: string }>>([])

/** 利率格式化为 2 位小数（银行标准） */
function formatRate(n: number): string {
  return n.toFixed(2)
}

onMounted(async () => {
  try {
    const res = await getProductTypes()
    productTypes.value = (res || []).slice(0, 6)
  } catch {
    productTypes.value = []
  }
})
</script>

<style lang="scss" scoped>
.product-strip {
  background: $card;
  margin: 32rpx;
  border: 1rpx solid $border-light;
}

.ps-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 32rpx 32rpx 24rpx;
  border-bottom: 1rpx solid $border-light;
  gap: 16rpx;
}
.ps-head-left {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  min-width: 0;
  flex: 1;
}
.ps-eyebrow {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.ps-title {
  font-family: $ff-serif;
  font-size: 30rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1rpx;
}
.ps-head-tip {
  font-family: $ff-mono;
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  padding: 6rpx 12rpx;
  background: $bg-2;
  border: 1rpx solid $border-light;
  flex-shrink: 0;
}

.ps-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
}
.ps-item {
  padding: 24rpx;
  border-right: 1rpx solid $border-light;
  border-bottom: 1rpx solid $border-light;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  position: relative;
  transition: background 150ms ease-out;
  &:nth-child(2n) { border-right: none; }
  &:nth-last-child(-n+2) { border-bottom: none; }
  &:active { background: rgba(15, 35, 64, 0.02); }
}

.ps-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ps-num {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $accent;
  font-weight: 600;
  letter-spacing: 1rpx;
}
.ps-user-tag {
  font-family: $ff-mono;
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  padding: 2rpx 8rpx;
  border: 1rpx solid $border-light;
  line-height: 1.4;
}
.ps-name {
  font-family: $ff-serif;
  font-size: 28rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
  line-height: 1.3;
  margin-top: 4rpx;
}
.ps-rate-row {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
  margin-top: 4rpx;
}
.ps-rate-from {
  font-family: $ff-serif;
  font-size: 36rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 0.5rpx;
  line-height: 1;
}
.ps-rate-sep {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $accent;
  font-weight: 500;
}
.ps-rate-range {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $text-sub;
  letter-spacing: 0.5rpx;
  line-height: 1.4;
}

.ps-footer {
  padding: 16rpx 32rpx;
  border-top: 1rpx solid $border-light;
  background: $bg-2;
}
.ps-disclaimer {
  font-size: 20rpx;
  color: $text-weak;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
}
</style>
