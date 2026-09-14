<!--
  DataStrip - 数据背书条
  v18 (2026-09-14): 横板三列
    - 移动端 3 列等宽（用户要求"横板 颗粒对齐"，同时防溢出）
    - 字号缩：移动端数字 38rpx / label 22rpx / sublabel 14rpx
    - 桌面数字 64rpx / label 26rpx / sublabel 15rpx
    - 桌面 4 列（auto-fit），移动端 3 列强制等分
    - 防溢出：所有文字 white-space: nowrap + 数字 tabular-nums
    - 序号基于 visibleItems 重新编号
-->
<template>
  <view class="data-strip" :class="{ 'is-in': inView }">
    <view
      v-for="(item, i) in visibleItems"
      :key="item.key"
      class="ds-item"
      :style="{ transitionDelay: i * 100 + 'ms' }"
    >
      <!-- 序号角标（编辑感杂志感，置顶右） -->
      <text class="ds-idx">{{ padIdx(i + 1) }}</text>

      <!-- 大数字 + 单位 -->
      <view class="ds-num-row">
        <text class="ds-num">{{ display[i] }}</text>
        <text class="ds-num-suffix">{{ item.suffix }}</text>
      </view>

      <!-- 金色 hairline（视觉锚点） -->
      <view class="ds-rule" />

      <!-- 中文标签 -->
      <text class="ds-label">{{ item.label }}</text>
      <!-- 英文小标 -->
      <text class="ds-sublabel">{{ item.sub }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useSiteStore } from '@/store/site'

const siteStore = useSiteStore()

interface DataItem {
  key: string
  value: number
  suffix: string
  label: string
  sub: string
}

/** 把 siteStore 返回的"128,000+" 字符串解析回数字用于 > 0 渲染判断 */
function parseCount(s: string): number {
  const n = Number(String(s || '').replace(/[^0-9.]/g, ''))
  return Number.isFinite(n) ? n : 0
}

const items: DataItem[] = [
  { key: 'user', value: parseCount(siteStore.userCount),    suffix: '+', label: '已服务用户',   sub: 'CUMULATIVE USERS' },
  { key: 'test', value: parseCount(siteStore.testCount),    suffix: '+', label: '累计模拟测评', sub: 'ASSESSMENTS DONE' },
  { key: 'case', value: parseCount(siteStore.caseCount),    suffix: '+', label: '真实案例回测', sub: 'CASES VERIFIED' },
  { key: 'pass', value: parseCount(siteStore.satisfaction), suffix: '%', label: '报告满意度',   sub: 'USER SATISFACTION' },
]

/** 过滤 value>0 的项，序号基于可见项重新编号 */
const visibleItems = computed(() => items.filter(i => i.value > 0))

/** 千分位（整数） */
function fmt(n: number): string {
  return Math.round(n).toLocaleString('en-US')
}

/** 01 / 02 / 03 / 04 编辑感角标 */
function padIdx(n: number): string {
  return n < 10 ? '0' + n : String(n)
}

// 初始全部 0，进入视口后 rAF 滚动到目标值
const display = reactive<string[]>(visibleItems.value.map(() => '0'))
const inView = ref(false)

onMounted(() => {
  // 给首屏渲染一个 tick，再触发滚动（避免数字闪一下又重置）
  setTimeout(trigger, 60)
})

function trigger() {
  inView.value = true
  const start = Date.now()
  const dur = 1200
  const targets = visibleItems.value.map(i => i.value)

  function step() {
    const t = Math.min(1, (Date.now() - start) / dur)
    // ease-out cubic
    const e = 1 - Math.pow(1 - t, 3)
    for (let i = 0; i < targets.length; i++) {
      display[i] = fmt(targets[i] * e)
    }
    if (t < 1) {
      // 跨端：rAF 在 H5 可用，小程序/APP 走 setTimeout 兜底
      if (typeof requestAnimationFrame === 'function') {
        requestAnimationFrame(step)
      } else {
        setTimeout(step, 16)
      }
    } else {
      // 收尾精确到目标值
      for (let i = 0; i < targets.length; i++) display[i] = fmt(targets[i])
    }
  }
  if (typeof requestAnimationFrame === 'function') {
    requestAnimationFrame(step)
  } else {
    setTimeout(step, 16)
  }
}
</script>

<style lang="scss" scoped>
.data-strip {
  display: grid;
  // v18：移动端 3 列等宽（横板 + 颗粒对齐），用 minmax(0, 1fr) 防止文字溢出撑开列宽
  grid-template-columns: repeat(3, minmax(0, 1fr));
  background: $card;
  margin: 0 24rpx;
  border-top: 1rpx solid $border-light;
  border-bottom: 1rpx solid $border-light;
  overflow: hidden;
}

.ds-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  // v18：紧凑 padding（横板需要更窄的内边距才能放得下数字）
  padding: 40rpx 16rpx 44rpx;
  // 移动端用竖线分隔（横板）
  border-right: 1rpx solid $border-light;
  &:last-child { border-right: none; }
  // 进入前：向下偏移 + 透明
  opacity: 0;
  transform: translateY(20rpx);
  transition: opacity 500ms ease-out, transform 500ms ease-out;
  // 悬停态：仅桌面 / 鼠标设备生效
  &:hover {
    background: $primary-tint;
  }
}
// 进入视口后：所有 .ds-item 复位
.is-in .ds-item {
  opacity: 1;
  transform: translateY(0);
}

// 序号角标 01/02/03（编辑感杂志感，置顶右）
.ds-idx {
  position: absolute;
  top: 24rpx;
  right: 16rpx;
  font-family: $ff-mono;
  font-size: 18rpx;
  color: $text-weak;
  letter-spacing: 2rpx;
  line-height: 1;
  white-space: nowrap;
}

// 大数字行
.ds-num-row {
  display: flex;
  align-items: baseline;
  gap: 2rpx;
  margin-bottom: 16rpx;
  // v18：防数字换行
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
}
.ds-num {
  font-family: $ff-serif;
  font-size: 38rpx;       // v18 移动端 38rpx（横板 3 列下保证 128,000+ 不溢出）
  font-weight: 500;
  color: $primary;
  letter-spacing: -0.5rpx;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: clip;
}
.ds-num-suffix {
  font-family: $ff-mono;
  font-size: 20rpx;       // v18 移动端 20rpx
  color: $accent;
  font-weight: 500;
  line-height: 1;
  margin-left: 2rpx;
  white-space: nowrap;
}

// 金色 hairline（视觉锚点）
.ds-rule {
  width: 40rpx;           // v18 移动端 40rpx
  height: 1rpx;
  background: $accent;
  margin-bottom: 16rpx;
}

// 中文标签
.ds-label {
  font-family: $ff-serif;
  font-size: 22rpx;       // v18 移动端 22rpx
  font-weight: 600;
  color: $primary;
  letter-spacing: 0.5rpx;
  line-height: 1.3;
  margin-bottom: 4rpx;
  // 防换行（横板下中文不溢出）
  word-break: keep-all;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

// 英文小标
.ds-sublabel {
  font-family: $ff-mono;
  font-size: 13rpx;       // v18 移动端 13rpx
  color: $text-weak;
  letter-spacing: 2rpx;
  line-height: 1.3;
  text-transform: uppercase;
  // 防换行
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

// ===== 桌面端（≥1024rpx ≈ 512px CSS px）：auto-fit 多列 + 大字号 =====
@media (min-width: 1024rpx) {
  .data-strip {
    grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
    margin: 0 32rpx;
  }
  .ds-item {
    padding: 56rpx 32rpx 64rpx;
  }
  .ds-num { font-size: 64rpx; letter-spacing: -1rpx; }
  .ds-num-suffix { font-size: 28rpx; }
  .ds-rule { width: 56rpx; margin-bottom: 24rpx; }
  .ds-idx { top: 32rpx; right: 32rpx; font-size: 20rpx; }
  .ds-num-row { margin-bottom: 24rpx; gap: 4rpx; }
  .ds-label { font-size: 26rpx; letter-spacing: 1rpx; }
  .ds-sublabel { font-size: 15rpx; letter-spacing: 3rpx; }
}
</style>
