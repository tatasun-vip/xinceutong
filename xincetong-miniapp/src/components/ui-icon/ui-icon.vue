<!--
  UiIcon - 统一 SVG 图标库（替代所有 emoji）
  用法：<UiIcon name="bank" :size="40" color="#0f2340" />
  命名：line style (stroke-width: 1.5)，24x24 viewBox，currentColor
  设计原则：
    - 线性（描边）风格，与专业金融产品调性匹配
    - 1.5 stroke-width，圆角端点
    - 24x24 viewBox，size 可控
    - 颜色用 currentColor / color prop 传入
-->
<template>
  <view class="ui-icon" :style="iconStyle" :aria-label="name">
    <svg
      :width="size"
      :height="size"
      viewBox="0 0 24 24"
      fill="none"
      :stroke="color"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      aria-hidden="true"
    >
      <!-- ============ 勾选 ============ -->
      <g v-if="name === 'check'">
        <path d="M5 12.5l4.5 4.5L19 7" />
      </g>
      <!-- ============ 银行 / 模型专业 ============ -->
      <g v-else-if="name === 'bank'">
        <path d="M3 10h18M5 10v8M9 10v8M15 10v8M19 10v8M2 21h20" />
        <path d="M12 3L3 8h18L12 3z" />
      </g>
      <!-- ============ 数据 / 覆盖全面 ============ -->
      <g v-else-if="name === 'chart'">
        <path d="M4 20V8M10 20V4M16 20v-6M22 20H2" />
      </g>
      <!-- ============ 锁 / 隐私安全 ============ -->
      <g v-else-if="name === 'lock'">
        <rect x="4" y="11" width="16" height="10" rx="1" />
        <path d="M8 11V7a4 4 0 1 1 8 0v4" />
      </g>
      <!-- ============ 盾牌 / 结果可靠 ============ -->
      <g v-else-if="name === 'shield'">
        <path d="M12 3l8 3v5c0 5-3.5 9-8 10-4.5-1-8-5-8-10V6l8-3z" />
        <path d="M9 12l2 2 4-4" />
      </g>
      <!-- ============ 中立 / 合作 ============ -->
      <g v-else-if="name === 'handshake'">
        <path d="M11 17l-3-3-2 2 5 5 3-3M13 7l3 3 2-2-5-5-3 3" />
        <path d="M8 14l3 3M16 10l-3-3M12 8l-2-2M14 18l2 2" />
      </g>
      <!-- ============ 星 / 推荐 ============ -->
      <g v-else-if="name === 'star'">
        <path d="M12 3l3 6 6 .9-4.5 4.4 1 6.7L12 17.8 6.5 21l1-6.7L3 9.9 9 9l3-6z" />
      </g>
      <!-- ============ 右箭头 ============ -->
      <g v-else-if="name === 'arrow-right'">
        <path d="M5 12h14M13 6l6 6-6 6" />
      </g>
      <!-- ============ 下箭头 ============ -->
      <g v-else-if="name === 'arrow-down'">
        <path d="M12 5v14M6 13l6 6 6-6" />
      </g>
      <!-- ============ 文档 / 报告 ============ -->
      <g v-else-if="name === 'doc'">
        <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6z" />
        <path d="M14 3v6h6M8 13h8M8 17h5" />
      </g>
      <!-- ============ 钱包 / 金融 ============ -->
      <g v-else-if="name === 'wallet'">
        <rect x="3" y="6" width="18" height="13" rx="2" />
        <path d="M3 10h18M16 14.5h.01" />
      </g>
      <!-- ============ 时钟 / 速度 ============ -->
      <g v-else-if="name === 'clock'">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </g>
      <!-- ============ 通知 ============ -->
      <g v-else-if="name === 'bell'">
        <path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 9H3c0-2 3-2 3-9zM10 21a2 2 0 0 0 4 0" />
      </g>
      <!-- ============ 列表 ============ -->
      <g v-else-if="name === 'list'">
        <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
      </g>
      <!-- ============ 信息 ============ -->
      <g v-else-if="name === 'info'">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8h.01M12 11v5" />
      </g>
      <!-- ============ 用户 / 头像 ============ -->
      <g v-else-if="name === 'user'">
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
      </g>
      <!-- ============ 历史 / 时钟回溯 ============ -->
      <g v-else-if="name === 'history'">
        <path d="M3 12a9 9 0 1 0 3-6.7" />
        <path d="M3 3v5h5" />
        <path d="M12 7v5l3 2" />
      </g>
      <!-- ============ 设置 / 齿轮 ============ -->
      <g v-else-if="name === 'settings'">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1A2 2 0 1 1 4.4 17l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
      </g>
      <!-- ============ 电话 / 客服 ============ -->
      <g v-else-if="name === 'phone'">
        <path d="M5 4h4l2 5-3 2a12 12 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 6a2 2 0 0 1 2-2z" />
      </g>
      <!-- ============ 分享 / 转发 ============ -->
      <g v-else-if="name === 'share'">
        <circle cx="6" cy="12" r="2.5" />
        <circle cx="18" cy="6" r="2.5" />
        <circle cx="18" cy="18" r="2.5" />
        <path d="M8.2 10.8l7.6-3.6M8.2 13.2l7.6 3.6" />
      </g>
      <!-- ============ 退出登录 ============ -->
      <g v-else-if="name === 'exit'">
        <path d="M14 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2v-3" />
        <path d="M10 12h11M18 8l4 4-4 4" />
      </g>
      <!-- ============ 推广员 / 喇叭 ============ -->
      <g v-else-if="name === 'promoter'">
        <path d="M3 11v2a2 2 0 0 0 2 2h2l5 4V5L7 9H5a2 2 0 0 0-2 2z" />
        <path d="M16 8a5 5 0 0 1 0 8" />
        <path d="M19 5a9 9 0 0 1 0 14" />
      </g>
      <!-- ============ 法务 / 律师 ============ -->
      <g v-else-if="name === 'legal'">
        <path d="M12 3v18M5 7h14M5 17h14" />
        <path d="M3 7l3-4M21 7l-3-4M3 17l3 4M21 17l-3 4" />
      </g>
      <!-- ============ 客服 / 消息 ============ -->
      <g v-else-if="name === 'service'">
        <path d="M21 12a9 9 0 1 1-3.5-7.1L21 4l-1 4.5A9 9 0 0 1 21 12z" />
        <path d="M8 11h.01M12 11h.01M16 11h.01" />
      </g>
      <!-- ============ 关于 / 圆圈 i ============ -->
      <g v-else-if="name === 'about'">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 8h.01" />
        <path d="M11 12h1v5h1" />
      </g>
      <!-- ============ 链接 / 链条 ============ -->
      <g v-else-if="name === 'link'">
        <path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" />
        <path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" />
      </g>
      <!-- ============ 隐私 / 隐身 ============ -->
      <g v-else-if="name === 'eye'">
        <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" />
        <circle cx="12" cy="12" r="3" />
      </g>
      <!-- ============ 礼物 / 优惠 ============ -->
      <g v-else-if="name === 'gift'">
        <path d="M3 8h18v4H3z" />
        <path d="M5 12v9h14v-9" />
        <path d="M12 8v13" />
        <path d="M12 8c-1-2-3-3-4.5-2C6 7 6 8 7 8h5zM12 8c1-2 3-3 4.5-2 1.5 1 1.5 2 .5 2h-5z" />
      </g>
      <!-- ============ 上箭头 / 上滑 ============ -->
      <g v-else-if="name === 'arrow-up'">
        <path d="M12 19V5M6 11l6-6 6 6" />
      </g>
      <!-- ============ 左箭头 ============ -->
      <g v-else-if="name === 'arrow-left'">
        <path d="M19 12H5M11 18l-6-6 6-6" />
      </g>
      <!-- ============ 关闭 / 叉 ============ -->
      <g v-else-if="name === 'close'">
        <path d="M6 6l12 12M18 6L6 18" />
      </g>
      <!-- ============ 勾选圆圈 ============ -->
      <g v-else-if="name === 'check-circle'">
        <circle cx="12" cy="12" r="9" />
        <path d="M8 12l3 3 5-6" />
      </g>
      <!-- ============ 警告三角 ============ -->
      <g v-else-if="name === 'warning'">
        <path d="M12 3l10 18H2L12 3z" />
        <path d="M12 10v5M12 18h.01" />
      </g>
    </svg>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  name:
    | 'check'
    | 'bank'
    | 'chart'
    | 'lock'
    | 'shield'
    | 'handshake'
    | 'star'
    | 'arrow-right'
    | 'arrow-down'
    | 'arrow-up'
    | 'arrow-left'
    | 'doc'
    | 'wallet'
    | 'clock'
    | 'bell'
    | 'list'
    | 'info'
    | 'user'
    | 'history'
    | 'settings'
    | 'phone'
    | 'share'
    | 'exit'
    | 'promoter'
    | 'legal'
    | 'service'
    | 'about'
    | 'link'
    | 'eye'
    | 'gift'
    | 'close'
    | 'check-circle'
    | 'warning'
  size?: number
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 24,
  color: 'currentColor',
})

const iconStyle = computed(() => ({
  width: `${props.size}rpx`,
  height: `${props.size}rpx`,
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: props.color === 'currentColor' ? undefined : props.color,
}))
</script>

<style lang="scss" scoped>
.ui-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 0;

  :deep(svg) {
    display: block;
  }
}
</style>
