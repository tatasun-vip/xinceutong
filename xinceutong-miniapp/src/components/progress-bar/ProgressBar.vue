<template>
  <view class="progress-bar">
    <view class="bar-top">
      <text class="bar-label">第 {{ pad(current) }} 步 / 共 {{ pad(total) }} 步</text>
      <text class="bar-step">{{ pad(current) }} / {{ pad(total) }}</text>
    </view>
    <view class="bar-track">
      <view
        v-for="i in total"
        :key="i"
        :class="[
          'bar-seg',
          i < current ? 'done' : '',
          i === current ? 'active' : '',
        ]"
      />
    </view>
    <view v-if="titles.length" class="bar-titles">
      <view
        v-for="(t, idx) in titles"
        :key="t"
        :class="[
          'bar-title',
          idx + 1 < current ? 'done' : '',
          idx + 1 === current ? 'active' : '',
        ]"
      >
        <text class="bar-title-idx">{{ pad(idx + 1) }}</text>
        <text class="bar-title-name">{{ t }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  current: number
  total: number
  titles?: string[]
}
withDefaults(defineProps<Props>(), {
  current: 1,
  total: 5,
  titles: () => [],
})

function pad(n: number) {
  return n < 10 ? `0${n}` : String(n)
}
</script>

<style lang="scss" scoped>
.progress-bar {
  padding: 24rpx 32rpx 20rpx;
  background: $card;
  border-bottom: 1rpx solid $border-light;
}
.bar-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16rpx;
}
.bar-label {
  font-family: $ff-serif;
  font-size: $font-sm;
  color: $text-sub;
  letter-spacing: 1rpx;
}
.bar-step {
  font-family: $ff-mono;
  font-size: $font-sm;
  color: $primary;
  font-weight: 500;
  letter-spacing: 0.5rpx;
}
.bar-track {
  display: flex;
  gap: 8rpx;
}
.bar-seg {
  flex: 1;
  height: 4rpx;
  background: $border-light;
  transition: background 0.3s;
  &.done   { background: $primary-2; }
  &.active { background: $primary; }
}
.bar-titles {
  display: flex;
  margin-top: 20rpx;
  gap: 4rpx;
}
.bar-title {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: $font-xs;
  color: $text-weak;
  font-family: $ff-base;
  &-idx {
    font-family: $ff-mono;
    font-size: $font-xs;
    font-weight: 500;
    margin-bottom: 6rpx;
  }
  &-name {
    letter-spacing: 1rpx;
  }
  &.active {
    color: $primary;
    .bar-title-idx { color: $accent; font-weight: 700; }
    .bar-title-name { font-weight: 600; }
  }
  &.done {
    color: $text-sub;
    .bar-title-idx { color: $primary-2; }
  }
}
</style>
