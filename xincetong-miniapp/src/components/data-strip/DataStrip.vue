<!--
  DataStrip - 数据背书条
  v3.4 (2026-09): 重新设计
    旧问题：4 色（金/蓝/灰/边框）+ box-shadow + 左色条 + 负 margin → 老气奢华
    新设计：编辑感 2 色（深蓝 + 灰） + 1rpx 细线 + 数字单位 + 标签左对齐
-->
<template>
  <view class="data-strip">
    <view
      v-for="(item, i) in items"
      v-show="item.value > 0"
      :key="item.key"
      class="ds-item"
      :class="{ 'is-first': i === 0 }"
    >
      <!-- 数字 + 单位 + 后缀 -->
      <view class="ds-num-row">
        <text class="ds-num">{{ formatNum(item.value) }}</text>
        <text class="ds-num-suffix">{{ item.suffix }}</text>
      </view>

      <!-- 1rpx 极细分隔线（编辑感，替代粗 divider） -->
      <view class="ds-rule" />

      <!-- 标签：全小写 mono + letter-spacing（编辑感） -->
      <text class="ds-label">{{ item.label }}</text>
      <text class="ds-sublabel">{{ item.sub }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useSiteStore } from '@/store/site'

const siteStore = useSiteStore()

interface DataItem {
  key: string
  value: number
  suffix: string
  label: string
  sub: string
}

/**
 * 把 siteStore 返回的"128,000+" 字符串解析回数字用于 > 0 渲染判断
 * store 端 userCount/testCount/caseCount 是 formatNumber 后的可读串（含分隔符 + 后缀），
 * 模板上不再做 number 运算，只需要判断"是否非零（有没有填 DB）" → 0 时整列隐藏
 */
function parseCount(s: string): number {
  const n = Number(String(s || '').replace(/[^0-9.]/g, ''))
  return Number.isFinite(n) ? n : 0
}

const items: DataItem[] = [
  {
    key: 'user',
    value: parseCount(siteStore.userCount),
    suffix: '+',
    label: '已服务用户',
    sub: 'CUMULATIVE USERS',
  },
  {
    key: 'test',
    value: parseCount(siteStore.testCount),
    suffix: '+',
    label: '累计模拟测评',
    sub: 'ASSESSMENTS DONE',
  },
  {
    key: 'case',
    value: parseCount(siteStore.caseCount),
    suffix: '+',
    label: '真实案例回测',
    sub: 'CASES VERIFIED',
  },
]

/** 千分位格式化（数字部分保留 0 位小数） */
function formatNum(n: number): string {
  return n.toLocaleString('en-US')
}
</script>

<style lang="scss" scoped>
.data-strip {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  background: $card;
  margin: 0 32rpx;
  padding: 32rpx 0;
  border-top: 1rpx solid $border-light;
  border-bottom: 1rpx solid $border-light;
}

.ds-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 0 24rpx;
  border-right: 1rpx solid $border-light;

  &:last-child { border-right: none; }
  &.is-first { padding-left: 8rpx; }
}

// 数字 + 单位行
.ds-num-row {
  display: flex;
  align-items: baseline;
  gap: 2rpx;
  margin-bottom: 16rpx;
}
.ds-num {
  font-family: $ff-serif;
  font-size: 44rpx;
  font-weight: 500;
  color: $primary;
  letter-spacing: 0.5rpx;
  line-height: 1;
  // 用 font-feature-settings 让数字等宽（编辑感 / 表格感）
  font-feature-settings: 'tnum' 1;
  font-variant-numeric: tabular-nums;
}
.ds-num-suffix {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $accent;
  font-weight: 500;
  line-height: 1;
}

// 1rpx 极细线（编辑感）
.ds-rule {
  width: 32rpx;
  height: 1rpx;
  background: $accent;
  margin-bottom: 16rpx;
}

// 中文标签
.ds-label {
  font-family: $ff-serif;
  font-size: 24rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
  line-height: 1.4;
  margin-bottom: 4rpx;
}

// 英文小标（mono + 字母间距 + 灰色）
.ds-sublabel {
  font-family: $ff-mono;
  font-size: 18rpx;
  color: $text-weak;
  letter-spacing: 2rpx;
  line-height: 1.4;
  text-transform: uppercase;
}
</style>
