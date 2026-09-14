<template>
  <view class="compliance-bar">
    <text class="cb-line">|</text>
    <text class="cb-text">模拟测评 · 非银行官方 · 不查征信</text>
    <text class="cb-line">|</text>
  </view>
</template>

<script setup lang="ts">
// 顶部合规条组件 - 所有页面顶部必挂
// 提示用户：这是模拟工具，不查征信，不构成贷款承诺
</script>

<style lang="scss" scoped>
.compliance-bar {
  background: $primary;
  padding: 8rpx 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}
.cb-line {
  color: $accent;
  font-size: 18rpx;
  font-weight: 300;
  letter-spacing: 0;
}
.cb-text {
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 4rpx;
  font-family: $ff-base;
}
</style>
