<!--
  Launch - 信测通启动页
  v3.2 极简化：去掉重复 eyebrow/tagline，LOGO 自己说话
  视觉序列：顶部短线 → 大 LOGO → 品牌名 → tagline → 底部合规
  时长 1.5s 后 reLaunch 到首页
-->
<template>
  <view class="launch">
    <view class="lc-content">
      <!-- 顶部金色短线（编辑感） -->
      <view class="lc-rule" />

      <!-- 核心：LOGO -->
      <view class="lc-logo">
        <BrandLogo variant="shield" layout="icon" :size="200" mode="light" />
      </view>

      <view class="lc-name">{{ siteStore.brandName }}</view>
      <view class="lc-tagline">{{ siteStore.brandTagline }}</view>

      <!-- 底部合规：双行小字 -->
      <view class="lc-footer">
        <text class="lc-disclaimer">模拟测评 · 非银行官方 · 不查征信</text>
        <text class="lc-disclaimer-2">实际审批结果以金融机构正式审批为准</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useSiteStore } from '@/store/site'
import BrandLogo from '@/components/brand-logo/brand-logo.vue'
import { onMounted } from 'vue'

const siteStore = useSiteStore()

onMounted(() => {
  // 启动页 1.5 秒后跳到首页
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/index/index' })
  }, 1500)
})
</script>

<style lang="scss" scoped>
.launch {
  min-height: 100vh;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 64rpx 48rpx;
  position: relative;
}

.lc-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  color: $text-white;
  width: 100%;
  max-width: 600rpx;
}

// 顶部金色短线（编辑风/杂志感）
.lc-rule {
  width: 48rpx;
  height: 2rpx;
  background: $accent;
  margin-bottom: 64rpx;
}

// 核心：LOGO（带金色光晕）
.lc-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 48rpx;
  filter: drop-shadow(0 6rpx 20rpx rgba(201, 169, 110, 0.25));
}

.lc-name {
  font-family: $ff-serif;
  font-size: 80rpx;
  font-weight: 700;
  color: $text-white;
  letter-spacing: 24rpx;
  line-height: 1;
  padding-left: 24rpx; // 抵消末字 letter-spacing
  margin-bottom: 32rpx;
}

.lc-tagline {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 4rpx;
  line-height: 1.6;
}

// 底部：双行小字
.lc-footer {
  position: absolute;
  bottom: 64rpx;
  left: 64rpx;
  right: 64rpx;
  text-align: center;
}
.lc-disclaimer {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 2rpx;
  margin-bottom: 4rpx;
}
.lc-disclaimer-2 {
  display: block;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 1rpx;
}
</style>
