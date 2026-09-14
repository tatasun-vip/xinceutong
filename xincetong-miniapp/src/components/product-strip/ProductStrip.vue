<!--
  ProductStrip - 6 大产品类型
  v18.1 (2026-09-14) 修复中文标签字形错位
    - .ps-tag-text 字号 20→24rpx（10px 是中文小字号渲染极限，"人"字缺末笔变"山"）
    - .ps-tag padding 4rpx 10rpx → 6rpx 14rpx（更舒展）
    - .ps-num 22→24rpx（与标签一致，避免视觉错位）
    - .ps-card-head 高度 28rpx → 40rpx（容纳加大的标签）
    - 标签字距 1rpx → 2rpx（增加可读性）
-->
<template>
  <view class="product-strip">
    <!-- ========== 段头：编辑感 eyebrow + 标题 + 计数 ========== -->
    <view class="ps-head">
      <view class="ps-head-left">
        <text class="ps-eyebrow">PRODUCT COVERAGE</text>
        <text class="ps-title">{{ siteStore.productCount }} 大产品类型独立建模</text>
        <text class="ps-sub">每类产品用专属规则测算，不是一套模型套所有</text>
      </view>
      <view class="ps-head-right">
        <text class="ps-count">06</text>
        <text class="ps-count-label">CATEGORIES</text>
      </view>
    </view>

    <!-- ========== 6 卡网格（2 列 × 3 行，移动端友好） ========== -->
    <view class="ps-grid">
      <view
        v-for="(p, i) in productTypes"
        :key="p.code"
        class="ps-card"
        :class="p.code"
        :style="getCardStyle(p.code)"
      >
        <!-- 顶部行：编号 01-06 / 标签 个人/企业 -->
        <view class="ps-card-head">
          <text class="ps-num">{{ String(i + 1).padStart(2, '0') }}</text>
          <view class="ps-tag" :style="getTagStyle(p.code)">
            <text class="ps-tag-text" :style="{ color: getProductColor(p.code).text }">
              {{ p.user_type === 'personal' ? '个人' : '企业' }}
            </text>
          </view>
        </view>

        <!-- icon 居中区（44rpx，与编号垂直对齐） -->
        <view class="ps-icon-box" :style="{ background: getProductColor(p.code).color + '14' }">
          <UiIcon
            :name="getProductColor(p.code).icon"
            :size="40"
            :color="getProductColor(p.code).color"
          />
        </view>

        <!-- 产品名（限制 2 行，超出省略） -->
        <text class="ps-name">{{ p.name }}</text>

        <!-- 利率：2.88% 起（核心数据，编辑感大数字 + 小号"起"） -->
        <view class="ps-rate-row">
          <text class="ps-rate-num" :style="{ color: getProductColor(p.code).color }">
            {{ formatRate(p.rate_min) }}<text class="ps-rate-pct">%</text>
          </text>
          <text class="ps-rate-from">起</text>
        </view>

        <!-- 区间（底部） -->
        <text class="ps-range">
          区间 {{ formatRate(p.rate_min) }}% – {{ formatRate(p.rate_max) }}%
        </text>
      </view>
    </view>

    <!-- ========== 段尾：合规脚注（编辑感 footnote） ========== -->
    <view class="ps-footer">
      <text class="ps-disclaimer">
        本平台不推演利率 · 区间仅作信息参考 · 实际利率以银行审批报价为准
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSiteStore } from '@/store/site'
import { getProductTypes } from '@/api/product'
import { getProductColor, type ProductColor } from '@/utils/productConfig'
import UiIcon from '@/components/ui-icon/ui-icon.vue'

const siteStore = useSiteStore()
const productTypes = ref<Array<{
  code: string; name: string; rate_min: number; rate_max: number; user_type: string
}>>([])

/** 利率格式化为 2 位小数（银行标准） */
function formatRate(n: number): string {
  return n.toFixed(2)
}

/** 卡片背景色 + 左侧产品色条（4rpx） */
function getCardStyle(code: string) {
  const c: ProductColor = getProductColor(code)
  return {
    background: c.bg,
    borderLeftColor: c.color,
  }
}

/** 标签样式：白底 + 产品色 1rpx 边框 + 字号 22rpx */
function getTagStyle(code: string) {
  const c: ProductColor = getProductColor(code)
  return {
    borderColor: c.color + '40', // 25% 透明边框
  }
}

onMounted(async () => {
  try {
    const res = await getProductTypes()
    productTypes.value = (res || []).slice(0, 6)
  } catch {
    productTypes.value = []
  }
})
</script>

<style lang="scss" scoped>
/* ========== 容器 ========== */
.product-strip {
  background: $card;
  margin: 32rpx;
  border: 1rpx solid $border-light;
}

/* ========== 段头（编辑感）========== */
.ps-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 36rpx 32rpx 28rpx;
  border-bottom: 1rpx solid $border-light;
  gap: 24rpx;
}
.ps-head-left {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
  flex: 1;
}
.ps-eyebrow {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
  line-height: 1;
}
.ps-title {
  font-family: $ff-serif;
  font-size: 32rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1rpx;
  line-height: 1.4;
}
.ps-sub {
  font-size: 24rpx;
  color: $text-sub;
  letter-spacing: 0.5rpx;
  line-height: 1.5;
  margin-top: 2rpx;
}
.ps-head-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4rpx;
  flex-shrink: 0;
  padding-top: 4rpx;
}
.ps-count {
  font-family: $ff-serif;
  font-size: 56rpx;
  font-weight: 700;
  color: $primary;
  line-height: 1;
  font-feature-settings: 'tnum' 1;
  font-variant-numeric: tabular-nums;
  letter-spacing: 1rpx;
}
.ps-count-label {
  font-family: $ff-mono;
  font-size: 18rpx;
  color: $text-weak;
  letter-spacing: 2rpx;
  line-height: 1;
  text-transform: uppercase;
}

/* ========== 6 卡网格 ========== */
.ps-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-auto-rows: 1fr; // 关键：每张卡片严格等高
}

/* ========== 单卡（v18 严格颗粒对称）========== */
.ps-card {
  position: relative;
  padding: 24rpx 24rpx 24rpx 28rpx; // 左 28rpx 给 4rpx 色条留位
  border-right: 1rpx solid $border-light;
  border-bottom: 1rpx solid $border-light;
  border-left: 4rpx solid transparent; // 颜色由 inline style 注入
  display: flex;
  flex-direction: column;
  gap: 8rpx; // 严格 8rpx 网格

  &:nth-child(2n) { border-right: none; }
  &:nth-last-child(-n+2) { border-bottom: none; }
  &:active {
    transform: scale(0.99);
    transition: transform 120ms ease-out;
  }
}

/* 头部：编号 + 标签（同一行，不再 absolute） */
.ps-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40rpx; // v18.1: 28→40 容纳加大的中文标签
  margin-bottom: 4rpx;
}
.ps-num {
  font-family: $ff-mono;
  font-size: 24rpx; // v18.1: 22→24 与标签字号一致
  color: $text-weak;
  font-weight: 600;
  letter-spacing: 1rpx;
  line-height: 1;
}
.ps-tag {
  display: inline-flex;
  align-items: center;
  padding: 6rpx 14rpx; // v18.1: 4/10→6/14 更舒展
  background: $card; // 白底不再半透明
  border: 1rpx solid; // 颜色由 inline style 注入
  border-radius: 0rpx; // 硬边
  line-height: 1.2;
}
.ps-tag-text {
  font-family: $ff-mono;
  font-size: 24rpx; // v18.1: 20→24 中文安全字号（20rpx=10px 笔画缺损）
  font-weight: 600;
  letter-spacing: 2rpx; // v18.1: 1→2 增加可读性
  line-height: 1.2;
}

/* icon 居中区（圆形浅色背景 + 居中 icon） */
.ps-icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64rpx;
  height: 64rpx;
  margin: 4rpx 0 8rpx;
}

/* 产品名（限制 2 行） */
.ps-name {
  font-family: $ff-serif;
  font-size: 28rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
  line-height: 1.3;
  min-height: 36rpx; // 1 行的卡片和 2 行的卡片对齐
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

/* 利率主行（核心数据） */
.ps-rate-row {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
  margin-top: 4rpx;
}
.ps-rate-num {
  font-family: $ff-serif;
  font-size: 40rpx;
  font-weight: 700;
  letter-spacing: 0.5rpx;
  line-height: 1;
  font-feature-settings: 'tnum' 1;
  font-variant-numeric: tabular-nums;
}
.ps-rate-pct {
  font-size: 24rpx;
  font-weight: 600;
  margin-left: 1rpx;
}
.ps-rate-from {
  font-family: $ff-serif;
  font-size: 22rpx;
  color: $text-weak;
  font-weight: 500;
  margin-left: 2rpx;
}

/* 区间（mono + 字距） */
.ps-range {
  font-family: $ff-mono;
  font-size: 20rpx;
  color: $text-sub;
  letter-spacing: 0.5rpx;
  line-height: 1.4;
  margin-top: 2rpx;
}

/* ========== 段尾（编辑感脚注）========== */
.ps-footer {
  padding: 18rpx 32rpx;
  border-top: 1rpx solid $border-light;
  background: $bg-2;
}
.ps-disclaimer {
  font-size: 20rpx;
  color: $text-weak;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
}
</style>
