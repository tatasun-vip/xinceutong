<!--
  BrandLogo - 信测通品牌标识
  设计说明：
    三个候选方案 + 三种布局，让产品/品牌/UI 灵活选用
    - 调性：金融科技 · 专业 · 可信 · 严谨
    - 主色：深蓝 #0F2340 + 金色 #C9A96E + 浅金 #E5C77E
    - 字体：serif（信测通）+ mono（信测通 XINCETONG）
    - 记忆点：盾形 + 刻度（信=保护，测=量化，通=桥梁）

  用法：
    <BrandLogo variant="shield" layout="horizontal" :size="120" />
    <BrandLogo variant="xt" layout="vertical" :size="80" />
    <BrandLogo variant="seal" layout="icon" :size="64" />
-->
<template>
  <view class="brand-logo" :class="['bl-' + layout, 'bl-mode-' + mode]" :style="wrapStyle">
    <!-- ========== 方案 A：盾+刻度（主推）========== -->
    <view v-if="variant === 'shield'" class="bl-svg-wrap">
      <svg
        :width="sizePx"
        :height="sizePx"
        viewBox="0 0 64 64"
        fill="none"
        :aria-label="'信测通'"
      >
        <!-- 盾形外轮廓（深蓝） -->
        <path
          d="M32 4 L58 14 V32 C58 46 46 56 32 60 C18 56 6 46 6 32 V14 Z"
          :fill="primary"
          :stroke="accent"
          stroke-width="1.5"
          stroke-linejoin="round"
        />
        <!-- 顶部金色圆点（S 级 / 顶级信用） -->
        <circle cx="32" cy="20" r="3" :fill="accent" />
        <!-- 3 道横向刻度线（测评 / 量化） -->
        <line x1="18" y1="30" x2="46" y2="30" :stroke="accent" stroke-width="1.5" stroke-linecap="round" opacity="0.55" />
        <line x1="20" y1="38" x2="44" y2="38" :stroke="accentLight" stroke-width="1.5" stroke-linecap="round" />
        <line x1="18" y1="46" x2="46" y2="46" :stroke="accent" stroke-width="1.5" stroke-linecap="round" opacity="0.55" />
        <!-- 底部通道（通 = 路径 / 通过） -->
        <path d="M22 52 L32 56 L42 52" :stroke="accent" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
      </svg>
    </view>

    <!-- ========== 方案 B：XT 字母 + 通道 ========== -->
    <view v-else-if="variant === 'xt'" class="bl-svg-wrap">
      <svg
        :width="sizePx"
        :height="sizePx"
        viewBox="0 0 64 64"
        fill="none"
        :aria-label="'信测通'"
      >
        <!-- 抽象 X + T 组合 -->
        <path
          d="M10 10 L26 32 L10 54 M54 10 L38 32 L54 54"
          :stroke="primary"
          stroke-width="3.5"
          stroke-linecap="round"
          fill="none"
        />
        <!-- 横向连接通道（金色） -->
        <line x1="6" y1="32" x2="58" y2="32" :stroke="accent" stroke-width="2" stroke-linecap="round" />
        <!-- 左右端点装饰 -->
        <circle cx="6" cy="32" r="2.5" :fill="accent" />
        <circle cx="58" cy="32" r="2.5" :fill="accent" />
        <!-- 中心节点（测 = 中心 / 量化核心） -->
        <circle cx="32" cy="32" r="4" :fill="primary" :stroke="accent" stroke-width="1.5" />
        <circle cx="32" cy="32" r="1.5" :fill="accent" />
      </svg>
    </view>

    <!-- ========== 方案 C：印章式（金融传统 + 现代几何）========== -->
    <view v-else-if="variant === 'seal'" class="bl-svg-wrap">
      <svg
        :width="sizePx"
        :height="sizePx"
        viewBox="0 0 64 64"
        fill="none"
        :aria-label="'信测通'"
      >
        <!-- 印章外圆（深蓝） -->
        <circle cx="32" cy="32" r="28" :fill="primary" :stroke="accent" stroke-width="1.5" />
        <!-- 内圆（金色细线） -->
        <circle cx="32" cy="32" r="24" :stroke="accent" stroke-width="0.8" fill="none" opacity="0.5" />
        <!-- 「测」字的几何抽象：横 + 中间框 + 底部三角 -->
        <rect x="20" y="18" width="24" height="3" :fill="accent" />
        <rect x="20" y="28" width="24" height="14" :stroke="accent" stroke-width="1.5" fill="none" />
        <line x1="32" y1="28" x2="32" y2="42" :stroke="accent" stroke-width="1.5" />
        <!-- 底部刻度 -->
        <line x1="22" y1="48" x2="42" y2="48" :stroke="accent" stroke-width="1.5" stroke-linecap="round" />
        <line x1="26" y1="48" x2="26" y2="51" :stroke="accent" stroke-width="1" stroke-linecap="round" />
        <line x1="32" y1="48" x2="32" y2="51" :stroke="accent" stroke-width="1" stroke-linecap="round" />
        <line x1="38" y1="48" x2="38" y2="51" :stroke="accent" stroke-width="1" stroke-linecap="round" />
      </svg>
    </view>

    <!-- ========== 文字部分 ========== -->
    <view v-if="layout !== 'icon'" class="bl-text">
      <text class="bl-name" :class="mode === 'light' ? 'bl-name-light' : ''">
        {{ siteStore.brandName }}
      </text>
      <text v-if="showEn" class="bl-en" :class="mode === 'light' ? 'bl-en-light' : ''">
        XINCETONG
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSiteStore } from '@/store/site'

interface Props {
  /** Logo 方案：A 盾+刻度 | B XT 通道 | C 印章 */
  variant?: 'shield' | 'xt' | 'seal'
  /** 布局：icon 仅图标 | horizontal 横排 | vertical 竖排 */
  layout?: 'icon' | 'horizontal' | 'vertical'
  /** 尺寸（rpx，对应 64x64 viewBox） */
  size?: number
  /** 显示英文 XINCETONG 副标 */
  showEn?: boolean
  /** 色彩模式：dark 暗底白字 / light 亮底深色字 */
  mode?: 'dark' | 'light'
}
const props = withDefaults(defineProps<Props>(), {
  variant: 'shield',
  layout: 'horizontal',
  size: 96,
  showEn: true,
  mode: 'dark',
})

const siteStore = useSiteStore()

// 品牌主色（与全局 SCSS 变量一致）
const primary = '#0F2340'
const accent = '#C9A96E'
const accentLight = '#E5C77E'

const sizePx = computed(() => `${props.size / 2}px`)

const wrapStyle = computed(() => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: `${props.size / 4}rpx`,
  flexDirection: (props.layout === 'vertical' ? 'column' : 'row') as 'row' | 'column',
}))
</script>

<style lang="scss" scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  user-select: none;
  line-height: 1;
}
.bl-svg-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 0;
}
.bl-text {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  line-height: 1;
}
.bl-name {
  font-family: $ff-serif;
  font-size: 36rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 6rpx;
}
.bl-name-light {
  color: #ffffff;
}
.bl-en {
  font-family: $ff-mono;
  font-size: 18rpx;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.bl-en-light {
  color: $accent;
  opacity: 0.85;
}

/* 竖排布局：文字水平居中 */
.bl-vertical {
  align-items: center;
  text-align: center;
}
.bl-vertical .bl-text {
  align-items: center;
}
</style>
