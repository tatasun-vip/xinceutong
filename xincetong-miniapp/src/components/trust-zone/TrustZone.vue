<!--
  TrustZone - 信任区组件
  用法：<TrustZone />
  用途：首页底部 + 报告页顶部，展示「为什么 128,000+ 用户选择信测通」
  所有数字从 site store 拉，运营可调
  v3.1 升级：所有图标改为 SVG 线性图标（替代 emoji）
-->
<template>
  <view class="trust-zone">
    <view class="tz-head">
      <view class="tz-eyebrow">WHY US</view>
      <view class="tz-title">为什么 <text class="tz-num">{{ siteStore.userCount }}</text> 用户选择信测通</view>
    </view>

    <view class="tz-grid">
      <view class="tz-item">
        <view class="tz-icon-wrap tz-icon-primary">
          <UiIcon name="bank" :size="44" color="#0f2340" />
        </view>
        <text class="tz-label">模型专业</text>
        <text class="tz-desc">参考银行信用贷审批框架 · {{ siteStore.expertCount }} 位业内人士参与校准</text>
      </view>

      <view class="tz-item">
        <view class="tz-icon-wrap tz-icon-primary">
          <UiIcon name="chart" :size="44" color="#0f2340" />
        </view>
        <text class="tz-label">覆盖全面</text>
        <text class="tz-desc">{{ siteStore.productCount }} 大产品类型独立建模 · 个人贷 + 企业贷双场景</text>
      </view>

      <view class="tz-item">
        <view class="tz-icon-wrap tz-icon-primary">
          <UiIcon name="lock" :size="44" color="#0f2340" />
        </view>
        <text class="tz-label">隐私安全</text>
        <text class="tz-desc">不查征信 · 不产生硬查询 · 不收集身份证号 / 银行卡号</text>
      </view>

      <view class="tz-item">
        <view class="tz-icon-wrap tz-icon-primary">
          <UiIcon name="shield" :size="44" color="#0f2340" />
        </view>
        <text class="tz-label">结果可靠</text>
        <text class="tz-desc">累计 {{ siteStore.caseCount }} 真实案例回测 · 报告满意度 {{ siteStore.satisfaction }}</text>
      </view>

      <view class="tz-item tz-item-wide">
        <view class="tz-icon-wrap tz-icon-primary">
          <UiIcon name="handshake" :size="44" color="#0f2340" />
        </view>
        <text class="tz-label">中立第三方</text>
        <text class="tz-desc">与任何银行无官方合作 · 不参与放贷 · 不收中介费</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { useSiteStore } from '@/store/site'
const siteStore = useSiteStore()
</script>

<style lang="scss" scoped>
.trust-zone {
  margin: 48rpx 32rpx;
  background: $card;
  border: 1rpx solid $border-light;
  padding: 48rpx 32rpx;
}
.tz-head {
  text-align: center;
  margin-bottom: 48rpx;
}
.tz-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.tz-title {
  font-family: $ff-serif;
  font-size: $font-xl;
  font-weight: 700;
  color: $primary;
  margin-top: 16rpx;
  letter-spacing: 1rpx;
  line-height: 1.4;
}
.tz-num {
  color: $accent;
  font-size: 36rpx;
}
.tz-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32rpx 24rpx;
}
.tz-item {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  padding: 32rpx 24rpx;
  background: rgba(15, 35, 64, 0.02);
  border-left: 4rpx solid $accent;
  position: relative;

  &.tz-item-wide {
    grid-column: 1 / -1;
  }
}
.tz-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  background: rgba(15, 35, 64, 0.06);
  border: 1rpx solid rgba(15, 35, 64, 0.12);
  margin-bottom: 4rpx;

  &.tz-icon-primary {
    color: $primary;
  }
}
.tz-label {
  font-family: $ff-serif;
  font-size: $font-md;
  color: $primary;
  font-weight: 600;
  letter-spacing: 1rpx;
}
.tz-desc {
  font-size: $font-xs;
  color: $text-sub;
  line-height: 1.7;
  letter-spacing: 0.3rpx;
}
</style>
