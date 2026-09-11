<!--
  Mine / History - 测评历史
  v3.4 (2026-09-11): 重写
    1. 修复 bug：原"返回"在 navigateBack 失败（mine 是 tabBar 父级）时静默无效
       新版：navigateBack 失败 → switchTab 兜底跳回 mine
    2. 完整列表：日期 / 报告号 / 类型 / 银行 / 评分 / 等级 / 状态
    3. 空状态：未测评时引导去评估
-->
<template>
  <view class="history page-bg">
    <ComplianceBar />

    <!-- ========== 1. 顶部 ========== -->
    <view class="hd">
      <view class="hd-back" @tap="goBack">
        <text class="hd-back-arrow">‹</text>
        <text class="hd-back-text">返回</text>
      </view>
      <view class="hd-title">测评历史</view>
      <view class="hd-count" v-if="!loading">{{ history.length }} 条</view>
      <view v-else class="hd-count-placeholder" />
    </view>

    <!-- ========== 2. 加载中 ========== -->
    <view v-if="loading" class="loading">
      <text class="loading-text">加载中...</text>
    </view>

    <!-- ========== 3. 空状态 ========== -->
    <view v-else-if="history.length === 0" class="empty">
      <view class="empty-icon">
        <UiIcon name="history" :size="80" color="#94A0B0" />
      </view>
      <text class="empty-title">还没有测评记录</text>
      <text class="empty-sub">完成 5 步问卷后，报告将自动保存到这里</text>
      <view class="empty-cta" @tap="goAssess">
        <text class="empty-cta-text">立即测评</text>
      </view>
    </view>

    <!-- ========== 4. 历史列表 ========== -->
    <view v-else class="list">
      <view
        v-for="(it, i) in history"
        :key="it.id"
        class="item"
        :class="{ 'is-first': i === 0 }"
        @tap="openResult(it)"
      >
        <!-- 左侧：报告号 + 类型 + 银行 + 日期 -->
        <view class="item-left">
          <view class="item-head">
            <text class="item-no">#{{ it.report_no }}</text>
            <text class="item-type">{{ typeLabel(it.type) }}</text>
          </view>
          <view class="item-meta">
            <text v-if="it.bank_name" class="item-bank">{{ it.bank_name }}</text>
            <text v-if="it.bank_name && it.product_name" class="item-dot">·</text>
            <text v-if="it.product_name" class="item-product">{{ it.product_name }}</text>
            <text v-if="!it.bank_name && !it.product_name" class="item-bank">综合测评</text>
          </view>
          <text class="item-date">{{ formatDate(it.created_at, false) }}</text>
        </view>

        <!-- 右侧：评分 + 等级 + 状态 -->
        <view class="item-right">
          <view class="item-score-row">
            <text class="item-score">{{ it.score }}</text>
            <text class="item-score-unit">分</text>
          </view>
          <text class="item-level" :class="`lv-${levelKey(it.level)}`">
            {{ levelText(it.level) }}
          </text>
          <text v-if="it.is_paid" class="item-status is-paid">已解锁</text>
          <text v-else class="item-status is-free">免费版</text>
        </view>

        <!-- 箭头 -->
        <view class="item-arrow">›</view>
      </view>
    </view>

    <!-- ========== 5. 底部说明 ========== -->
    <view v-if="!loading && history.length > 0" class="footer-note">
      <text class="footer-line">本地最多保留 50 条历史记录</text>
      <text class="footer-sub">更换设备或清除缓存将丢失本地数据</text>
    </view>

    <view class="tabbar-safe" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { useAssessmentStore, HistoryItem } from '@/store/assessment'
import { useUserStore } from '@/store/user'
import { formatDate } from '@/utils/format'
import { pageView, track } from '@/utils/track'

const assessStore = useAssessmentStore()
const userStore   = useUserStore()

const loading = ref(false)
const history = computed<HistoryItem[]>(() => assessStore.history)

onShow(() => {
  pageView('mine/history')
  loadHistory()
})

function loadHistory() {
  loading.value = true
  // 同步本地存储（其他页面可能更新了）
  assessStore.restoreFromStorage()
  // 模拟一点点 loading（无网络时也不至于闪烁）
  setTimeout(() => {
    loading.value = false
  }, 100)
}

// ============ 等级配置 ============
function levelKey(level: string): 's' | 'a' | 'b' | 'c' | 'd' | 'e' {
  const k = level.toUpperCase()
  if (k === 'S' || k === 'A') return 's'
  if (k === 'B') return 'b'
  if (k === 'C') return 'c'
  if (k === 'D') return 'd'
  return 'e'
}
function levelText(level: string): string {
  const k = level.toUpperCase()
  if (k === 'S') return 'S 级 · 极优'
  if (k === 'A') return 'A 级 · 优秀'
  if (k === 'B') return 'B 级 · 良好'
  if (k === 'C') return 'C 级 · 一般'
  if (k === 'D') return 'D 级 · 较弱'
  return 'E 级 · 不建议'
}
function typeLabel(type: string): string {
  return type === 'business' ? '企业贷' : '个人贷'
}

// ============ 行为 ============
function goBack() {
  // v3.4 修复：原本 navigateBack 在 tabBar 父页面下静默失败
  // 新版：先 navigateBack，失败则 switchTab 兜底跳回 mine（tabBar 入口）
  uni.navigateBack({
    fail: () => {
      uni.switchTab({ url: '/pages/mine/index' })
    },
  })
}

function openResult(it: HistoryItem) {
  track({ event: 'button_click', page: 'mine/history', data: { id: it.id, is_paid: it.is_paid } })
  // 已支付 → 完整报告页；免费 → 免费结果页
  const url = it.is_paid
    ? `/pages/result/report?id=${it.id}`
    : `/pages/result/free?id=${it.id}`
  uni.navigateTo({ url })
}

function goAssess() {
  uni.switchTab({ url: '/pages/assess/type' })
}
</script>

<style lang="scss" scoped>
.history {
  min-height: 100vh;
  background: $bg;
  display: flex;
  flex-direction: column;
}

/* ========== 顶部 ========== */
.hd {
  background: $card;
  display: flex;
  align-items: center;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid $border-light;
}
.hd-back {
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 8rpx 0;
  flex-shrink: 0;
  min-width: 96rpx;
}
.hd-back-arrow {
  font-size: 40rpx;
  color: $primary;
  line-height: 1;
  font-weight: 300;
}
.hd-back-text {
  font-size: 28rpx;
  color: $primary;
  letter-spacing: 0.5rpx;
}
.hd-title {
  flex: 1;
  text-align: center;
  font-family: $ff-serif;
  font-size: 32rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 2rpx;
}
.hd-count {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  min-width: 96rpx;
  text-align: right;
  flex-shrink: 0;
}
.hd-count-placeholder {
  min-width: 96rpx;
}

/* ========== 加载中 ========== */
.loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 96rpx 0;
}
.loading-text {
  font-size: 26rpx;
  color: $text-weak;
  letter-spacing: 2rpx;
}

/* ========== 空状态 ========== */
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 96rpx 64rpx;
  gap: 16rpx;
}
.empty-icon {
  width: 160rpx;
  height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
  background: $bg-2;
  border-radius: 0;
  border: 1rpx solid $border-light;
}
.empty-title {
  font-family: $ff-serif;
  font-size: 32rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
  margin-top: 16rpx;
}
.empty-sub {
  font-size: 24rpx;
  color: $text-sub;
  letter-spacing: 0.5rpx;
  text-align: center;
  line-height: 1.6;
  margin-bottom: 32rpx;
}
.empty-cta {
  background: $primary;
  padding: 20rpx 64rpx;
  border-left: 4rpx solid $accent;
}
.empty-cta-text {
  font-family: $ff-serif;
  font-size: 28rpx;
  color: $text-white;
  letter-spacing: 4rpx;
  font-weight: 500;
}

/* ========== 列表 ========== */
.list {
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}
.item {
  background: $card;
  padding: 32rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
  border-left: 4rpx solid $border;
  &.is-first { border-left-color: $accent; }
}
.item-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}
.item-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}
.item-no {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
}
.item-type {
  font-size: 20rpx;
  color: $primary;
  letter-spacing: 2rpx;
  padding: 2rpx 8rpx;
  border: 1rpx solid $primary;
  font-family: $ff-mono;
  font-weight: 500;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 28rpx;
  color: $primary;
  letter-spacing: 0.5rpx;
  font-weight: 500;
  min-width: 0;
}
.item-bank {
  max-width: 280rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-product {
  color: $text-sub;
  font-weight: 400;
  max-width: 240rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-dot {
  color: $text-weak;
}
.item-date {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  font-variant-numeric: tabular-nums;
}

.item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4rpx;
  flex-shrink: 0;
}
.item-score-row {
  display: flex;
  align-items: baseline;
  gap: 2rpx;
  line-height: 1;
}
.item-score {
  font-family: $ff-serif;
  font-size: 48rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 0;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.item-score-unit {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $text-sub;
  letter-spacing: 0.5rpx;
}
.item-level {
  font-family: $ff-mono;
  font-size: 22rpx;
  letter-spacing: 1rpx;
  font-weight: 500;
  &.lv-s { color: $success; }
  &.lv-a { color: $success; }
  &.lv-b { color: $primary; }
  &.lv-c { color: $warning; }
  &.lv-d { color: $danger; }
  &.lv-e { color: $danger; }
}
.item-status {
  font-family: $ff-mono;
  font-size: 18rpx;
  letter-spacing: 1rpx;
  padding: 2rpx 8rpx;
  border: 1rpx solid currentColor;
  margin-top: 4rpx;
  &.is-paid { color: $accent-dark; border-color: $accent; }
  &.is-free { color: $text-weak; }
}

.item-arrow {
  color: $text-weak;
  font-size: 36rpx;
  line-height: 1;
  font-weight: 300;
  flex-shrink: 0;
  margin-left: 4rpx;
}

/* ========== 底部说明 ========== */
.footer-note {
  margin: 16rpx 32rpx 0;
  padding: 24rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  border-top: 1rpx solid $border-light;
}
.footer-line {
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
}
.footer-sub {
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 0.5rpx;
  font-family: $ff-mono;
}

.tabbar-safe {
  height: 32rpx;
}
</style>
