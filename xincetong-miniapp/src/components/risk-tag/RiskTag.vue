<template>
  <view :class="['risk-tag', `risk-${level}`]">{{ text }}</view>
</template>

<script setup lang="ts">
type Level = 'info' | 'success' | 'warning' | 'danger'
interface Props {
  text: string
  level?: Level
}
withDefaults(defineProps<Props>(), { level: 'info' })
</script>

<style lang="scss" scoped>
.risk-tag {
  display: inline-block;
  padding: 4rpx 16rpx;
  border-radius: 24rpx;
  font-size: $font-xs;
  line-height: 1.6;
  margin-right: 12rpx;
  margin-bottom: 8rpx;
}
.risk-info    { background: $primary-light; color: $primary; }
.risk-success { background: #E0F2E9; color: $success; }
.risk-warning { background: $accent-light; color: $warning; }
.risk-danger  { background: #FBE6E2; color: $danger; }
</style>
