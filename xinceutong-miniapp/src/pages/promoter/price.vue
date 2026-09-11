<template>
  <view class="page page-bg">
    <ComplianceBar />

    <view class="header">
      <view class="back" @tap="goBack">← 返回</view>
      <view class="step-info">第 1/5 步</view>
    </view>

    <view class="content">
      <view class="title">价格设置</view>
      <view class="subtitle">6.99 ~ 19.99 元</view>

      <view class="placeholder">本页面在阶段 6 实现</view>
      <view class="placeholder-sub">后端 admin 接口 + 数据看板</view>
    </view>

    <view class="footer">
      <button class="btn-primary" @tap="goNext">下一步</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import { useShareCode } from '@/composables/useShareCode'
import { pageView } from '@/utils/track'

const title = ref('价格设置')
const stage = ref('6')
const hint  = ref('6.99 ~ 19.99 元')

const { shareCode, promoterCode } = useShareCode()

onLoad(() => {
  pageView('promoter/price')
})

function goBack() {
  uni.navigateBack()
}

function goNext() {
  uni.navigateTo({ url: '/pages/promoter/dashboard' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg;
  display: flex;
  flex-direction: column;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx;
  background: $card;
  .back { font-size: $font-md; color: $primary; }
  .step-info { font-size: $font-sm; color: $text-sub; }
}
.content {
  flex: 1;
  padding: 32rpx;
}
.title {
  font-size: $font-xl;
  font-weight: 600;
  color: $text-main;
}
.subtitle {
  font-size: $font-sm;
  color: $text-sub;
  margin-top: 8rpx;
  margin-bottom: 32rpx;
}
.placeholder {
  font-size: $font-md;
  color: $text-sub;
  text-align: center;
  padding: 80rpx 0 $space-2;
}
.placeholder-sub {
  font-size: $font-xs;
  color: $text-weak;
  text-align: center;
}
.footer {
  padding: 24rpx 32rpx;
  background: $card;
  padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
}
</style>
