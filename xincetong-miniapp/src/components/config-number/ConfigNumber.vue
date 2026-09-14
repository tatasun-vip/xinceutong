<!--
  ConfigNumber - 数字变量化组件
  用法：<ConfigNumber config-key="site.user_count" suffix="+" />
  用途：所有数字都从 site store 拉，运营改 DB 即生效
-->
<template>
  <text class="config-number">{{ display }}</text>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSiteStore } from '@/store/site'

interface Props {
  configKey: string
  suffix?: string
  fallback?: string
}
const props = withDefaults(defineProps<Props>(), {
  suffix: '',
  fallback: '0',
})

const siteStore = useSiteStore()

const display = computed(() => {
  const raw = siteStore.get(props.configKey, props.fallback)
  const n = parseInt(raw, 10)
  if (isNaN(n)) return raw + props.suffix
  return n.toLocaleString('en-US') + props.suffix
})
</script>

<style lang="scss" scoped>
.config-number {
  font-family: $ff-serif;
  font-weight: 700;
  color: inherit;
}
</style>
