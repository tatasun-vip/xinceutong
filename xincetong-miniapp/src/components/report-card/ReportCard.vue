<template>
  <view :class="['rc-card', product.recommend ? 'rc-recommend' : '']" @tap="onTap">
    <view class="rc-head">
      <view class="rc-name">{{ product.name }}</view>
      <view v-if="product.recommend" class="rc-badge">推荐</view>
    </view>
    <view class="rc-row">
      <text class="rc-label">额度</text>
      <text class="rc-val">{{ product.limit }}</text>
    </view>
    <view class="rc-row">
      <text class="rc-label">利率参考</text>
      <text class="rc-val rc-val-ref">{{ product.rate }}</text>
    </view>
    <view class="rc-row">
      <text class="rc-label">通过率</text>
      <text :class="['rc-val', `rc-pass-${product.pass}`]">{{ product.pass }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
export interface Product {
  name: string
  limit: string
  rate: string
  pass: string  // 高 | 中高 | 中 | 低
  recommend?: boolean
}
interface Props { product: Product }
defineProps<Props>()
const emit = defineEmits<{ (e: 'select'): void }>()
function onTap() { emit('select') }
</script>

<style lang="scss" scoped>
.rc-card {
  background: $card;
  border: 2rpx solid $border;
  border-radius: $radius-card;
  padding: 24rpx;
  margin-bottom: 16rpx;
  &.rc-recommend {
    border-color: $accent;
    background: linear-gradient(180deg, $accent-light 0%, #FFFFFF 60%);
  }
}
.rc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}
.rc-name { font-size: $font-md; font-weight: 600; color: $primary; }
.rc-badge {
  font-size: 20rpx;
  background: $accent;
  color: #FFFFFF;
  padding: 2rpx 14rpx;
  border-radius: 16rpx;
}
.rc-row {
  display: flex;
  justify-content: space-between;
  font-size: 26rpx;
  margin-top: 8rpx;
}
.rc-label { color: $text-sub; }
.rc-val   { color: $text-main; font-weight: 500; }
.rc-val-ref { color: $text-weak; font-weight: 400; font-size: 24rpx; }
.rc-pass-高   { color: $success; }
.rc-pass-中高 { color: #5A9C7C; }
.rc-pass-中   { color: $warning; }
.rc-pass-低   { color: $danger; }
</style>
