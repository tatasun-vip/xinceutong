<template>
  <svg
    class="ui-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke="color"
    :style="{ width: sizePx, height: sizePx }"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <!-- 基础通用 -->
    <g v-if="name === 'check'">
      <path d="M5 13l4 4L19 7" />
    </g>
    <g v-else-if="name === 'check-circle'">
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.5l3 3 5-6" />
    </g>
    <g v-else-if="name === 'x'">
      <path d="M6 6l12 12M18 6L6 18" />
    </g>
    <g v-else-if="name === 'arrow-right'">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </g>
    <g v-else-if="name === 'arrow-up'">
      <path d="M12 19V5M6 11l6-6 6 6" />
    </g>
    <g v-else-if="name === 'arrow-down'">
      <path d="M12 5v14M6 13l6 6 6-6" />
    </g>
    <!-- 业务 -->
    <g v-else-if="name === 'lock'">
      <rect x="4" y="11" width="16" height="10" rx="1.5" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </g>
    <g v-else-if="name === 'unlock'">
      <rect x="4" y="11" width="16" height="10" rx="1.5" />
      <path d="M8 11V7a4 4 0 0 1 7-2.6" />
    </g>
    <g v-else-if="name === 'lightbulb'">
      <path d="M9 18h6M10 22h4" />
      <path d="M12 2a7 7 0 0 0-4 12.7c.5.5 1 1.3 1 2.3v1h6v-1c0-1 .5-1.8 1-2.3A7 7 0 0 0 12 2z" />
    </g>
    <g v-else-if="name === 'chart'">
      <path d="M3 3v18h18" />
      <path d="M7 14l3-3 4 4 5-6" />
    </g>
    <g v-else-if="name === 'warning'">
      <path d="M12 3l10 18H2L12 3z" />
      <path d="M12 10v5M12 18h.01" />
    </g>
    <!-- 6 大产品专用（替代 emoji）-->
    <g v-else-if="name === 'landmark'">
      <path d="M3 21h18" />
      <path d="M3 10h18" />
      <path d="M5 10v8M9 10v8M15 10v8M19 10v8" />
      <path d="M3 7l9-5 9 5" />
      <path d="M12 2v5" />
    </g>
    <g v-else-if="name === 'gem'">
      <path d="M6 3h12l3 6-9 12L3 9z" />
      <path d="M3 9h18" />
      <path d="M9 3l3 6 3-6" />
      <path d="M12 9L3 21M12 9l9 12" />
    </g>
    <g v-else-if="name === 'briefcase'">
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <path d="M3 13h18" />
    </g>
    <g v-else-if="name === 'house'">
      <path d="M3 11l9-7 9 7" />
      <path d="M5 10v10h14V10" />
      <path d="M10 20v-6h4v6" />
    </g>
    <g v-else-if="name === 'receipt'">
      <path d="M5 3h14v18l-3-2-3 2-3-2-3 2-2-2z" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </g>
    <g v-else-if="name === 'x-circle'">
      <circle cx="12" cy="12" r="9" />
      <path d="M9 9l6 6M15 9l-6 6" />
    </g>
    <g v-else-if="name === 'info-circle'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5" />
      <path d="M12 8h.01" />
    </g>
    <g v-else-if="name === 'star-fill'">
      <path
        d="M12 3l3 6 6 .9-4.5 4.4 1 6.7L12 17.8 6.5 21l1-6.7L3 9.9 9 9l3-6z"
        fill="currentColor"
        stroke="none"
      />
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    name:
      | 'check' | 'check-circle' | 'x'
      | 'arrow-right' | 'arrow-up' | 'arrow-down'
      | 'lock' | 'unlock' | 'lightbulb' | 'chart' | 'warning'
      | 'landmark' | 'gem' | 'briefcase' | 'house' | 'receipt'
      | 'x-circle' | 'info-circle' | 'star-fill'
    size?: number
    color?: string
  }>(),
  { size: 16, color: 'currentColor' },
)

// web 用 px 不用 rpx
const sizePx = computed(() => `${props.size}px`)
</script>

<style scoped>
.ui-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}
</style>
