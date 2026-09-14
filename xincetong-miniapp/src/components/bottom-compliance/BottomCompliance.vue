<!--
  BottomCompliance - 底部合规块
  用法：<BottomCompliance />
  用途：所有页面底部显示「模拟测评 · 不查征信」声明，固定在底部
-->
<template>
  <view class="bottom-compliance">
    <view class="bc-divider" />
    <view class="bc-content">
      <text class="bc-line">{{ siteStore.disclaimerShort }}</text>
      <text class="bc-line">{{ siteStore.disclaimerLong }}</text>
      <text class="bc-tip">本平台不参与任何贷款发放 · 不收取贷款中介费 · 不承诺审批通过 · 利率不在推演范围</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useSiteStore } from '@/store/site'
const siteStore = useSiteStore()
</script>

<style lang="scss" scoped>
.bottom-compliance {
  margin-top: 64rpx;
  padding: 0 32rpx 32rpx;
}
.bc-divider {
  height: 1rpx;
  background: $border-light;
  margin-bottom: 24rpx;
}
.bc-content {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.bc-line {
  font-size: $font-xs;
  color: $text-weak;
  line-height: 1.6;
  text-align: center;
  letter-spacing: 0.5rpx;
}
.bc-tip {
  font-size: $font-xs;
  color: $text-weak;
  text-align: center;
  margin-top: 8rpx;
  letter-spacing: 0.5rpx;
}
</style>
