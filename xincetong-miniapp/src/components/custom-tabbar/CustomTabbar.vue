<!--
  CustomTabbar - 自定义底部导航
  v1 (2026-09-14): 重排版设计
    1. 仅 2 tab（首页 / 我的），去"测评"中间冗余
    2. 居中等距布局（不是平均分布），更聚焦
    3. 编辑感大字号 + serif 字体（保持品牌）
    4. active 态：深蓝主色 + 上方 4rpx 金线 + 编号小角标
    5. inactive 态：浅灰
    6. 点击有微动画（active 微缩 + 金线滑动）
-->
<template>
  <view class="ctb-wrap">
    <view class="ctb">
      <view
        v-for="(it, i) in items"
        :key="it.path"
        class="ctb-item"
        :class="{ 'is-active': currentIdx === i }"
        @tap="onTap(it, i)"
      >
        <view class="ctb-rule" />
        <text class="ctb-idx">{{ String(i + 1).padStart(2, '0') }}</text>
        <text class="ctb-text">{{ it.text }}</text>
        <text class="ctb-sub">{{ it.sub }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const items = [
  { path: '/pages/index/index', text: '首页', sub: 'HOME' },
  { path: '/pages/mine/index',  text: '我的', sub: 'MINE' },
]

const currentIdx = ref(0)

onMounted(() => {
  // 同步当前路由 → active tab
  const pages = (typeof getCurrentPages === 'function' ? getCurrentPages() : []) as any[]
  const cur = pages[pages.length - 1]?.route || 'pages/index/index'
  const i = items.findIndex(it => cur.includes(it.path.replace('/pages/', '')))
  if (i >= 0) currentIdx.value = i
})

function onTap(it: { path: string }, i: number) {
  if (i === currentIdx.value) return // 已激活不重跳
  // 切换 tab：switchTab 才能正确显示自定义 tabBar
  uni.switchTab({ url: it.path })
}
</script>

<style lang="scss" scoped>
/* =========================================================================
   设计 token
   - 2 tab 居中等距布局：容器 750rpx，2 tab 各占 50% 内容宽度
   - 上方 1rpx 细线分隔（编辑感）
   - active 上方 4rpx 金色粗线（视觉锚点）
   ========================================================================= */
.ctb-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  background: $card;
  border-top: 1rpx solid $border-light;
  // iOS 安全区适配
  padding-bottom: env(safe-area-inset-bottom);
}

.ctb {
  display: flex;
  align-items: stretch;
  height: 120rpx;
  // 居中内边距（让两个 tab 视觉居中）
  padding: 0 24rpx;
}

.ctb-item {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  padding: 16rpx 0 12rpx;
  // 默认中间分隔线（最后一个不要）
  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: 32rpx;
    bottom: 32rpx;
    width: 1rpx;
    background: $border-light;
  }
  &:last-child::after { display: none; }

  // active 态：上方金线
  &.is-active {
    .ctb-rule { transform: scaleX(1); }
    .ctb-idx  { color: $accent; }
    .ctb-text {
      color: $primary;
      transform: scale(1.06);
    }
  }
  // 点击反馈
  &:active {
    opacity: 0.7;
  }
}

// 顶部金线（默认隐藏，active 滑出）
.ctb-rule {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  transform-origin: center;
  width: 64rpx;
  height: 4rpx;
  background: $accent;
  transition: transform 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

// 编号角标
.ctb-idx {
  font-family: $ff-mono;
  font-size: 18rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  line-height: 1;
  transition: color 250ms ease-out;
}

// 主文字
.ctb-text {
  font-family: $ff-serif;
  font-size: 30rpx;
  font-weight: 600;
  color: $text-weak;
  letter-spacing: 2rpx;
  line-height: 1.1;
  transition: color 250ms ease-out, transform 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

// 英文小标
.ctb-sub {
  font-family: $ff-mono;
  font-size: 16rpx;
  color: $text-weak;
  letter-spacing: 3rpx;
  line-height: 1;
  text-transform: uppercase;
  opacity: 0.6;
}
</style>
