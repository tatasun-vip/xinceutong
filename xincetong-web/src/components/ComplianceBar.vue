<script setup lang="ts">
// 顶部备案条
</script>

<template>
  <div class="cb">
    <div class="cb-line"></div>
    <span class="cb-text">
      信用贷模拟评审 · 不查征信 · 不读取任何银行数据 · 备案号 沪ICP备 2026 0000000 号
    </span>
  </div>
</template>

<style lang="scss" scoped>
.cb {
  background: $primary-dark;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.cb-line {
  width: 16px;
  height: 1px;
  background: $accent;
}

.cb-text {
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.5px;
  font-weight: 300;
}
</style>
