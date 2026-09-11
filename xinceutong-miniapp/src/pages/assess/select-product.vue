<!--
  select-product.vue - 选择目标产品
  v1 (2026-09-10): 入口第二步 — 选产品
  数据：GET /api/banks/{code}/products
-->
<template>
  <view class="page">
    <ComplianceBar />

    <!-- 顶部导航 -->
    <view class="nav">
      <view class="nav-back" @tap="goBack">‹</view>
      <view class="nav-title">选择目标产品</view>
      <view class="nav-placeholder" />
    </view>

    <!-- 已选银行（步骤条） -->
    <view v-if="store.bankCode" class="bank-bar">
      <view class="bank-bar-label">已选银行</view>
      <view class="bank-bar-name">{{ store.bankName }}</view>
      <view class="bank-bar-change" @tap="goBack">重选</view>
    </view>

    <!-- 进度标识 -->
    <view class="step-bar">
      <view class="step-bar-num">00</view>
      <view class="step-bar-info">
        <view class="step-bar-title">选择目标产品</view>
        <view class="step-bar-sub">
          <text v-if="store.type === 'business'">请选择企业经营贷 / 纳税贷 / 开票贷 等企业专属产品</text>
          <text v-else>请选择个人信用贷 / 公积金贷 / 工薪贷 等个人专属产品</text>
        </view>
      </view>
    </view>

    <!-- 类型提示 banner（v5 新增）：个人/企业分流提示，防误选 -->
    <view :class="['type-banner', store.type === 'business' ? 'type-banner-biz' : 'type-banner-pers']">
      <text class="type-banner-icon">{{ store.type === 'business' ? 'B' : 'P' }}</text>
      <text class="type-banner-text">
        <text v-if="store.type === 'business'">当前测评：企业经营贷 · 仅显示对公产品</text>
        <text v-else>当前测评：个人信用贷 · 仅显示个人产品</text>
      </text>
    </view>

    <!-- 加载中 -->
    <view v-if="loading" class="loading">
      <view class="loading-spinner" />
      <text>加载中</text>
    </view>

    <!-- 产品列表 -->
    <view v-else-if="products.length" class="product-list">
      <view
        v-for="p in products"
        :key="p.id"
        :class="['product-card', p.recommend ? 'is-recommend' : '']"
        @tap="onSelect(p)"
      >
        <view class="product-card-head">
          <view class="product-card-name">{{ p.name }}</view>
          <view v-if="p.recommend" class="product-card-badge">推荐</view>
        </view>
        <view v-if="p.subtitle" class="product-card-sub">{{ p.subtitle }}</view>

        <view class="product-card-data">
          <view class="data-item">
            <text class="data-label">额度</text>
            <text class="data-value">{{ p.limit_min }}-{{ p.limit_max }} 万</text>
          </view>
          <view class="data-item">
            <text class="data-label">利率参考</text>
            <text class="data-value data-value-ref">{{ p.rate_min }}%-{{ p.rate_max }}%</text>
          </view>
        </view>

        <view v-if="p.features && p.features.length" class="product-card-tags">
          <text v-for="f in p.features" :key="f" class="product-card-tag">{{ f }}</text>
        </view>

        <view v-if="p.requirement" class="product-card-req">
          <text class="req-label">申请条件 ·</text>
          <text class="req-text">{{ p.requirement }}</text>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else class="empty">
      <view class="empty-icon">∅</view>
      <text class="empty-text">该银行暂无推荐产品</text>
    </view>

    <view class="disclaimer">实际审批以银行正式审核为准 · 本平台不参与贷款发放</view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import { getBankProducts, type BankProduct } from '@/api/bank'
import { useAssessmentStore } from '@/store/assessment'
import { pageView } from '@/utils/track'

const store = useAssessmentStore()
const products = ref<BankProduct[]>([])
const loading = ref(true)

onLoad(() => {
  pageView('assess/select-product')
  // 没选银行就跳回去
  if (!store.bankCode) {
    uni.redirectTo({ url: '/pages/assess/select-bank' })
  }
})

onMounted(async () => {
  if (!store.bankCode) return
  loading.value = true
  try {
    // 关键修复：按 store.type 过滤产品 —— 个人贷用户只看个人产品，企业贷用户只看企业产品
    // 配合 select-product 顶部的"个人/企业" banner 提示，避免企业用户误选个人专属产品
    const r = await getBankProducts(store.bankCode, store.type)
    products.value = r.items
  } catch (e) {
    console.error('加载产品列表失败', e)
  } finally {
    loading.value = false
  }
})

function onSelect(p: BankProduct) {
  store.setProduct(p.id, p.name)
  // 进 5 步问卷
  uni.redirectTo({ url: '/pages/assess/step1-basic' })
}

function goBack() {
  uni.redirectTo({ url: '/pages/assess/select-bank' })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg;
  padding-bottom: calc(40rpx + env(safe-area-inset-bottom));
}

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: $card;
  border-bottom: 1rpx solid $border-light;
  &-back {
    font-family: $ff-serif;
    font-size: 56rpx;
    color: $primary;
    width: 80rpx;
    line-height: 1;
  }
  &-placeholder { width: 80rpx; }
  &-title {
    font-family: $ff-serif;
    font-size: $font-lg;
    font-weight: 600;
    color: $primary;
    letter-spacing: 2rpx;
  }
}

.bank-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 24rpx 32rpx 0;
  padding: 16rpx 20rpx;
  background: $primary-tint;
  border-left: 4rpx solid $primary;
  &-label {
    font-size: $font-xs;
    color: $text-sub;
    letter-spacing: 0.5rpx;
  }
  &-name {
    flex: 1;
    font-family: $ff-serif;
    font-size: $font-md;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }
  &-change {
    font-size: $font-xs;
    color: $accent-dark;
    border-bottom: 1rpx solid $accent-dark;
    padding-bottom: 2rpx;
    letter-spacing: 1rpx;
  }
}

.step-bar {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 32rpx;
  background: $card;
  margin: 24rpx 32rpx;
  border: 1rpx solid $border-light;
  border-left: 4rpx solid $accent;
  &-num {
    font-family: $ff-serif;
    font-size: 56rpx;
    font-weight: 700;
    color: $accent;
    line-height: 1;
  }
  &-title {
    font-family: $ff-serif;
    font-size: $font-lg;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
    line-height: 1.4;
  }
  &-sub {
    font-size: $font-xs;
    color: $text-sub;
    margin-top: 4rpx;
    letter-spacing: 0.5rpx;
    line-height: 1.5;
  }
}

.loading {
  padding: 96rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
  color: $text-sub;
  font-size: $font-sm;
}
.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid $border-light;
  border-top-color: $primary;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.product-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  padding: 0 32rpx;
}

// ============ 类型 banner（个人/企业分流提示）============
.type-banner {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin: 0 32rpx 16rpx;
  padding: 12rpx 20rpx;
  border-left: 4rpx solid;
  font-size: $font-xs;
  letter-spacing: 0.5rpx;

  &-icon {
    width: 32rpx;
    height: 32rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: $ff-serif;
    font-weight: 700;
    font-size: 22rpx;
    color: #fff;
    flex-shrink: 0;
  }

  &-text {
    flex: 1;
    line-height: 1.5;
  }

  &-pers {
    background: rgba(15, 35, 64, 0.04);
    border-left-color: $primary;
    color: $primary;
    .type-banner-icon { background: $primary; }
  }

  &-biz {
    background: rgba(201, 169, 110, 0.08);
    border-left-color: $accent;
    color: $accent-dark;
    .type-banner-icon { background: $accent; }
  }
}
.product-card {
  background: $card;
  border: 1rpx solid $border-light;
  border-left: 4rpx solid $primary;
  padding: 24rpx;
  transition: all 0.2s;
  &.is-recommend {
    border-left-color: $accent;
    background: linear-gradient(to right, rgba(201, 169, 110, 0.05), $card 40%);
  }
  &-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8rpx;
  }
  &-name {
    font-family: $ff-serif;
    font-size: $font-lg;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }
  &-badge {
    font-size: 20rpx;
    background: $accent;
    color: #fff;
    padding: 2rpx 12rpx;
    border-radius: 16rpx;
    letter-spacing: 1rpx;
  }
  &-sub {
    font-size: $font-sm;
    color: $text-sub;
    margin-bottom: 16rpx;
    letter-spacing: 0.5rpx;
  }
  &-data {
    display: flex;
    gap: 32rpx;
    padding: 16rpx 0;
    border-top: 1rpx solid $border-light;
    border-bottom: 1rpx solid $border-light;
  }
  &-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8rpx;
    margin-top: 12rpx;
  }
  &-tag {
    font-size: 20rpx;
    color: $primary;
    background: rgba(15, 35, 64, 0.05);
    padding: 4rpx 12rpx;
    border-radius: 4rpx;
    letter-spacing: 0.5rpx;
  }
  &-req {
    margin-top: 12rpx;
    font-size: $font-xs;
    line-height: 1.6;
    letter-spacing: 0.5rpx;
  }
}
.data-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}
.data-label {
  font-size: $font-xs;
  color: $text-sub;
  letter-spacing: 0.5rpx;
}
.data-value {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 700;
  color: $primary;
  letter-spacing: 0.5rpx;
}
.data-value-ref {
  font-family: $ff-mono;
  font-size: $font-sm;
  font-weight: 500;
  color: $text-sub;
}
.req-label {
  color: $text-sub;
  font-weight: 600;
}
.req-text {
  color: $text-main;
}

.empty {
  padding: 96rpx 32rpx;
  text-align: center;
  &-icon {
    font-family: $ff-serif;
    font-size: 96rpx;
    color: $text-weak;
    line-height: 1;
  }
  &-text {
    display: block;
    margin-top: 16rpx;
    font-size: $font-sm;
    color: $text-sub;
    letter-spacing: 0.5rpx;
  }
}

.disclaimer {
  margin-top: 32rpx;
  padding: 0 32rpx;
  font-size: $font-xs;
  color: $text-weak;
  text-align: center;
  line-height: 1.8;
  letter-spacing: 0.5rpx;
}
</style>
