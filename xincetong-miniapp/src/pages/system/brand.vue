<!--
  Brand Identity Showroom - 信测通品牌标识展示
  用法：访问 /pages/system/brand
  用途：对比 3 套 Logo 方案（盾+刻度 / XT 通道 / 印章），并预览不同场景
-->
<template>
  <view class="brand-page page-bg">
    <ComplianceBar />

    <!-- 顶部 -->
    <view class="bp-head">
      <text class="bp-eyebrow">BRAND IDENTITY</text>
      <text class="bp-title">信测通 · 品牌标识系统</text>
      <text class="bp-sub">3 套候选方案 · 应用于不同场景</text>
    </view>

    <!-- ========== 方案 A：盾+刻度（主推）========== -->
    <view class="bp-section">
      <view class="bp-section-head">
        <text class="bp-section-num">A</text>
        <view class="bp-section-meta">
          <text class="bp-section-name">盾 · 刻度</text>
          <text class="bp-section-desc">信=保护 / 测=量化 / 通=通道</text>
        </view>
      </view>

      <view class="bp-card bp-card-dark">
        <text class="bp-card-label">DARK MODE</text>
        <view class="bp-logo-row">
          <BrandLogo variant="shield" layout="horizontal" :size="120" mode="light" />
        </view>
        <view class="bp-divider" />
        <view class="bp-icon-row">
          <view class="bp-icon-cell">
            <BrandLogo variant="shield" layout="icon" :size="64" mode="light" />
            <text class="bp-icon-label">小图标</text>
          </view>
          <view class="bp-icon-cell">
            <BrandLogo variant="shield" layout="icon" :size="96" mode="light" />
            <text class="bp-icon-label">标准</text>
          </view>
          <view class="bp-icon-cell">
            <BrandLogo variant="shield" layout="vertical" :size="120" mode="light" />
            <text class="bp-icon-label">竖排</text>
          </view>
        </view>
      </view>

      <view class="bp-card">
        <text class="bp-card-label">LIGHT MODE</text>
        <view class="bp-logo-row">
          <BrandLogo variant="shield" layout="horizontal" :size="120" mode="dark" />
        </view>
      </view>
    </view>

    <!-- ========== 方案 B：XT 通道 ========== -->
    <view class="bp-section">
      <view class="bp-section-head">
        <text class="bp-section-num">B</text>
        <view class="bp-section-meta">
          <text class="bp-section-name">XT · 通道</text>
          <text class="bp-section-desc">信通首字母 · 通道 = 信用流通</text>
        </view>
      </view>

      <view class="bp-card bp-card-dark">
        <text class="bp-card-label">DARK MODE</text>
        <view class="bp-logo-row">
          <BrandLogo variant="xt" layout="horizontal" :size="120" mode="light" />
        </view>
        <view class="bp-divider" />
        <view class="bp-icon-row">
          <view class="bp-icon-cell">
            <BrandLogo variant="xt" layout="icon" :size="64" mode="light" />
            <text class="bp-icon-label">小图标</text>
          </view>
          <view class="bp-icon-cell">
            <BrandLogo variant="xt" layout="icon" :size="96" mode="light" />
            <text class="bp-icon-label">标准</text>
          </view>
          <view class="bp-icon-cell">
            <BrandLogo variant="xt" layout="vertical" :size="120" mode="light" />
            <text class="bp-icon-label">竖排</text>
          </view>
        </view>
      </view>

      <view class="bp-card">
        <text class="bp-card-label">LIGHT MODE</text>
        <view class="bp-logo-row">
          <BrandLogo variant="xt" layout="horizontal" :size="120" mode="dark" />
        </view>
      </view>
    </view>

    <!-- ========== 方案 C：印章 ========== -->
    <view class="bp-section">
      <view class="bp-section-head">
        <text class="bp-section-num">C</text>
        <view class="bp-section-meta">
          <text class="bp-section-name">印章 · 测</text>
          <text class="bp-section-desc">金融传统 + 现代几何 · 权威感</text>
        </view>
      </view>

      <view class="bp-card bp-card-dark">
        <text class="bp-card-label">DARK MODE</text>
        <view class="bp-logo-row">
          <BrandLogo variant="seal" layout="horizontal" :size="120" mode="light" />
        </view>
        <view class="bp-divider" />
        <view class="bp-icon-row">
          <view class="bp-icon-cell">
            <BrandLogo variant="seal" layout="icon" :size="64" mode="light" />
            <text class="bp-icon-label">小图标</text>
          </view>
          <view class="bp-icon-cell">
            <BrandLogo variant="seal" layout="icon" :size="96" mode="light" />
            <text class="bp-icon-label">标准</text>
          </view>
          <view class="bp-icon-cell">
            <BrandLogo variant="seal" layout="vertical" :size="120" mode="light" />
            <text class="bp-icon-label">竖排</text>
          </view>
        </view>
      </view>

      <view class="bp-card">
        <text class="bp-card-label">LIGHT MODE</text>
        <view class="bp-logo-row">
          <BrandLogo variant="seal" layout="horizontal" :size="120" mode="dark" />
        </view>
      </view>
    </view>

    <!-- ========== 品牌色卡 ========== -->
    <view class="bp-section">
      <view class="bp-section-head">
        <text class="bp-section-num">D</text>
        <view class="bp-section-meta">
          <text class="bp-section-name">品牌色板</text>
          <text class="bp-section-desc">深蓝主色 · 金色强调</text>
        </view>
      </view>
      <view class="bp-color-grid">
        <view class="bp-color-card">
          <view class="bp-color-swatch" style="background: #0F2340" />
          <text class="bp-color-name">深蓝主色</text>
          <text class="bp-color-hex">#0F2340</text>
        </view>
        <view class="bp-color-card">
          <view class="bp-color-swatch" style="background: #C9A96E" />
          <text class="bp-color-name">金色强调</text>
          <text class="bp-color-hex">#C9A96E</text>
        </view>
        <view class="bp-color-card">
          <view class="bp-color-swatch" style="background: #E5C77E" />
          <text class="bp-color-name">浅金辅助</text>
          <text class="bp-color-hex">#E5C77E</text>
        </view>
        <view class="bp-color-card">
          <view class="bp-color-swatch" style="background: #F5F1E8; border: 1rpx solid #e0d8c5" />
          <text class="bp-color-name">米白背景</text>
          <text class="bp-color-hex">#F5F1E8</text>
        </view>
      </view>
    </view>

    <!-- 底部合规 -->
    <BottomCompliance />
  </view>
</template>

<script setup lang="ts">
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import BottomCompliance from '@/components/bottom-compliance/BottomCompliance.vue'
import BrandLogo from '@/components/brand-logo/brand-logo.vue'
</script>

<style lang="scss" scoped>
.brand-page {
  min-height: 100vh;
  padding-bottom: 64rpx;
}

.bp-head {
  text-align: center;
  padding: 48rpx 32rpx 32rpx;
}
.bp-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.bp-title {
  display: block;
  font-family: $ff-serif;
  font-size: 44rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 4rpx;
  margin-top: 16rpx;
  line-height: 1.3;
}
.bp-sub {
  display: block;
  font-size: $font-sm;
  color: $text-sub;
  margin-top: 12rpx;
  letter-spacing: 1rpx;
}

.bp-section {
  margin: 32rpx 32rpx 0;
}
.bp-section-head {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid $border-light;
}
.bp-section-num {
  font-family: $ff-serif;
  font-size: 40rpx;
  font-weight: 700;
  color: $accent;
  width: 56rpx;
  text-align: center;
  letter-spacing: 0;
}
.bp-section-meta {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  flex: 1;
}
.bp-section-name {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 600;
  color: $primary;
  letter-spacing: 2rpx;
}
.bp-section-desc {
  font-size: $font-xs;
  color: $text-sub;
  letter-spacing: 0.5rpx;
}

.bp-card {
  background: $card;
  border: 1rpx solid $border-light;
  padding: 32rpx;
  margin-bottom: 16rpx;
  position: relative;
}
.bp-card-dark {
  background: $primary;
  border-color: $primary;
}
.bp-card-label {
  position: absolute;
  top: 16rpx;
  right: 24rpx;
  font-family: $ff-mono;
  font-size: 18rpx;
  color: $text-weak;
  letter-spacing: 2rpx;
}
.bp-card-dark .bp-card-label {
  color: rgba(255, 255, 255, 0.4);
}

.bp-logo-row {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}
.bp-divider {
  height: 1rpx;
  background: rgba(255, 255, 255, 0.1);
  margin: 16rpx 0;
}
.bp-card:not(.bp-card-dark) .bp-divider {
  background: $border-light;
}
.bp-icon-row {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 16rpx 0 8rpx;
}
.bp-icon-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}
.bp-icon-label {
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  font-family: $ff-mono;
}
.bp-card-dark .bp-icon-label {
  color: rgba(255, 255, 255, 0.5);
}

/* 色卡 */
.bp-color-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}
.bp-color-card {
  background: $card;
  border: 1rpx solid $border-light;
  padding: 16rpx;
}
.bp-color-swatch {
  width: 100%;
  height: 96rpx;
  margin-bottom: 12rpx;
}
.bp-color-name {
  display: block;
  font-family: $ff-serif;
  font-size: $font-sm;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
}
.bp-color-hex {
  display: block;
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $text-sub;
  letter-spacing: 1rpx;
  margin-top: 2rpx;
}
</style>
