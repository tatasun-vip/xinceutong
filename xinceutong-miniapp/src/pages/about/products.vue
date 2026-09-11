<template>
  <view class="products">
    <ComplianceBar />

    <!-- 顶部标题 -->
    <view class="pp-hero">
      <text class="pp-eyebrow">6 PRODUCT TYPES</text>
      <text class="pp-title">不是一套模型套所有产品</text>
      <text class="pp-sub">每一类信用贷产品，我们单独建了一套模拟审批逻辑</text>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="pp-loading">
      <text>加载中…</text>
    </view>

    <!-- 6 大产品模块 -->
    <view v-else class="pp-list">
      <view v-for="(p, i) in products" :key="p.code" class="pp-card">
        <view class="pp-card-head">
          <view class="pp-card-num">
            <text class="pp-card-num-txt">{{ String(i + 1).padStart(2, '0') }}</text>
          </view>
          <view class="pp-card-title-block">
            <text class="pp-card-title">{{ p.name }}</text>
            <text class="pp-card-subtitle">{{ p.subtitle }}</text>
          </view>
        </view>

        <view class="pp-card-body">
          <view class="pp-row">
            <text class="pp-label">适合：</text>
            <text class="pp-value">{{ p.suitable }}</text>
          </view>
          <view class="pp-row">
            <text class="pp-label">考察重点：</text>
            <view class="pp-vars">
              <text v-for="v in p.focus_vars" :key="v" class="pp-var">{{ v }}</text>
            </view>
          </view>
          <view class="pp-row">
            <text class="pp-label">额度逻辑：</text>
            <text class="pp-value pp-value-emph">{{ p.limit_logic }}</text>
          </view>
          <view class="pp-row">
            <text class="pp-label">参考偏好：</text>
            <text class="pp-value">{{ p.preference }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部 -->
    <view class="pp-footer">
      <text class="pp-footer-emph">每类产品的审批逻辑不一样，</text>
      <text class="pp-footer-emph">同一份资料，在不同产品下的结果，本来就应该不同。</text>
      <text class="pp-footer-tip">信测通帮你一次看清。</text>
    </view>

    <BottomCompliance />
  </view>
</template>

<script setup lang="ts">
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import BottomCompliance from '@/components/bottom-compliance/BottomCompliance.vue'
import { ref, onMounted } from 'vue'
import { getProductTypes, type ProductType } from '@/api/product'

const loading = ref(true)
const products = ref<Array<ProductType & {
  suitable: string
  limit_logic: string
  preference: string
}>>([])

onMounted(async () => {
  try {
    const list = await getProductTypes()
    products.value = list.map(p => ({
      ...p,
      suitable: extractSuitable(p.description || ''),
      limit_logic: extractLimitLogic(p.description || ''),
      preference: extractPreference(p.description || ''),
    }))
  } catch (e) {
    console.error('加载产品列表失败', e)
  } finally {
    loading.value = false
  }
})

function extractSuitable(desc: string): string {
  const m = desc.match(/适合：([^\n]+)/)
  return m ? m[1].trim() : ''
}
function extractLimitLogic(desc: string): string {
  const m = desc.match(/额度逻辑：([^\n]+)/)
  return m ? m[1].trim() : ''
}
function extractPreference(desc: string): string {
  const m = desc.match(/参考偏好：([^\n]+)/)
  return m ? m[1].trim() : ''
}
</script>

<style lang="scss" scoped>
.products {
  min-height: 100vh;
  background: $bg;
  padding-bottom: 64rpx;
}
.pp-hero {
  background: $primary;
  padding: 48rpx 32rpx 56rpx;
  text-align: center;
  color: $text-white;
}
.pp-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
  margin-bottom: 16rpx;
}
.pp-title {
  font-family: $ff-serif;
  font-size: 44rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  display: block;
  line-height: 1.3;
}
.pp-sub {
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 1rpx;
  display: block;
  margin-top: 16rpx;
  line-height: 1.6;
}
.pp-loading {
  text-align: center;
  padding: 80rpx 0;
  color: $text-weak;
}
.pp-list {
  padding: 0 32rpx;
  margin-top: -16rpx;
}
.pp-card {
  background: $card;
  border: 1rpx solid $border-light;
  border-left: 6rpx solid $primary;
  margin-top: 32rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 35, 64, 0.04);
}
.pp-card-head {
  display: flex;
  gap: 24rpx;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid $border-light;
  margin-bottom: 24rpx;
}
.pp-card-num {
  width: 64rpx;
  height: 64rpx;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.pp-card-num-txt {
  font-family: $ff-serif;
  font-size: 32rpx;
  color: $accent;
  font-weight: 700;
  letter-spacing: 1rpx;
}
.pp-card-title-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4rpx;
}
.pp-card-title {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1rpx;
}
.pp-card-subtitle {
  font-size: $font-sm;
  color: $text-sub;
  letter-spacing: 0.3rpx;
}
.pp-card-body {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.pp-row {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
}
.pp-label {
  font-size: $font-sm;
  color: $text-sub;
  flex-shrink: 0;
  min-width: 120rpx;
  font-weight: 500;
}
.pp-value {
  flex: 1;
  font-size: $font-sm;
  color: $text-main;
  line-height: 1.7;
  &.pp-value-emph {
    color: $accent;
    font-weight: 600;
  }
}
.pp-vars {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}
.pp-var {
  font-size: $font-xs;
  color: $primary;
  background: rgba(15, 35, 64, 0.05);
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
}
.pp-footer {
  margin: 64rpx 32rpx 0;
  padding: 32rpx;
  background: $card;
  border: 1rpx solid $border-light;
  text-align: center;
}
.pp-footer-emph {
  display: block;
  font-family: $ff-serif;
  font-size: $font-md;
  color: $primary;
  font-weight: 500;
  line-height: 1.8;
  letter-spacing: 0.5rpx;
}
.pp-footer-tip {
  display: block;
  margin-top: 16rpx;
  font-size: $font-sm;
  color: $accent;
  font-weight: 600;
  letter-spacing: 1rpx;
}
</style>
