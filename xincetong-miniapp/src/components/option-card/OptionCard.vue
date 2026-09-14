<template>
  <view :class="['opt-card', selected ? 'opt-selected' : '']" @tap="onTap">
    <view class="opt-body">
      <view class="opt-label">{{ label }}</view>
      <view v-if="desc" class="opt-desc">{{ desc }}</view>
    </view>
    <view class="opt-mark">
      <view v-if="selected" class="opt-mark-line opt-mark-v" />
      <view v-if="selected" class="opt-mark-line opt-mark-h" />
    </view>
  </view>
</template>

<script setup lang="ts">
interface Props {
  label: string
  desc?: string
  selected?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  desc: '',
  selected: false,
})
const emit = defineEmits<{ (e: 'select', payload: { label: string }): void }>()

function onTap() {
  emit('select', { label: props.label })
}
</script>

<style lang="scss" scoped>
.opt-card {
  position: relative;
  display: flex;
  align-items: center;
  background: $card;
  border: 1rpx solid $border-light;
  border-left: 4rpx solid transparent;
  border-radius: 0;
  padding: 28rpx 24rpx;
  margin-bottom: 0;
  transition: all 0.2s;
  &.opt-selected {
    border-color: $primary;
    border-left-color: $accent;
    background: $primary-tint;
    .opt-label { color: $primary; font-weight: 600; }
  }
}
.opt-body { flex: 1; min-width: 0; }
.opt-label {
  font-size: $font-md;
  color: $text-main;
  font-weight: 500;
  letter-spacing: 0.5rpx;
}
.opt-desc {
  font-size: $font-xs;
  color: $text-sub;
  margin-top: 6rpx;
  line-height: 1.5;
}
.opt-mark {
  width: 32rpx;
  height: 32rpx;
  border: 1rpx solid $border;
  border-radius: 0;
  flex-shrink: 0;
  margin-left: 16rpx;
  position: relative;
  background: $card;
}
.opt-selected .opt-mark {
  background: $primary;
  border-color: $primary;
}
.opt-mark-line {
  position: absolute;
  background: $text-white;
}
.opt-mark-v {
  left: 14rpx; top: 6rpx; width: 2rpx; height: 14rpx;
  transform: rotate(-45deg);
}
.opt-mark-h {
  left: 8rpx; top: 14rpx; width: 14rpx; height: 2rpx;
  transform: rotate(-45deg);
}
</style>
