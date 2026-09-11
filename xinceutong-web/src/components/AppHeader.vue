<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const router = useRouter()

const navItems = [
  { name: '首页', path: '/' },
  { name: '选择银行', path: '/banks' },
  { name: '测评说明', path: '/disclaimer' },
]

const isActive = (path: string) => computed(() => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
})

function goCTA() {
  router.push('/banks')
}
</script>

<template>
  <header class="hdr">
    <div class="hdr-inner container">
      <!-- Brand -->
      <div class="hdr-brand" @click="router.push('/')">
        <div class="hdr-mark">
          <span class="hdr-mark-zh">信</span>
        </div>
        <div class="hdr-brand-meta">
          <div class="hdr-brand-name">信测通 <span class="hdr-brand-en">XINCEUTONG</span></div>
          <div class="hdr-brand-tag">10 大银行专属测评体系</div>
        </div>
      </div>

      <!-- Nav -->
      <nav class="hdr-nav">
        <template v-for="item in navItems" :key="item.path">
          <div
            class="hdr-nav-item"
            :class="{ active: isActive(item.path).value }"
            @click="router.push(item.path)"
          >
            <span class="hdr-nav-label">{{ item.name }}</span>
            <span class="hdr-nav-line"></span>
          </div>
        </template>
      </nav>

      <!-- CTA — 金质主按钮，永远醒目 -->
      <div class="hdr-cta">
        <button class="btn-cta" @click="goCTA" aria-label="开始测评">
          <span>免费测评</span>
          <span class="btn-cta__arrow">→</span>
        </button>
      </div>
    </div>
  </header>
</template>

<style lang="scss" scoped>
.hdr {
  position: sticky;
  top: 0;
  z-index: $z-header;
  background: $bg-glass;
  backdrop-filter: saturate(180%) blur(16px);
  -webkit-backdrop-filter: saturate(180%) blur(16px);
  border-bottom: 1px solid $border-light;
  height: $header-height;
}

.hdr-inner {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $space-6;
}

/* Brand */
.hdr-brand {
  display: flex;
  align-items: center;
  gap: $space-3;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}

.hdr-mark {
  width: 44px;
  height: 44px;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid $accent;
  position: relative;
  overflow: hidden;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 12px;
    height: 12px;
    background: $accent;
    transform: rotate(45deg) translate(6px, -6px);
  }
}

.hdr-mark-zh {
  font-family: $ff-serif;
  font-size: 22px;
  color: $accent;
  font-weight: 700;
  letter-spacing: 1px;
  z-index: 1;
}

.hdr-brand-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.1;
}

.hdr-brand-name {
  font-family: $ff-serif;
  font-size: 18px;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.hdr-brand-en {
  font-family: $ff-mono;
  font-size: 10px;
  color: $accent;
  letter-spacing: 2px;
  font-weight: 500;
}

.hdr-brand-tag {
  font-size: 11px;
  color: $text-weak;
  letter-spacing: 0.5px;
}

/* Nav */
.hdr-nav {
  display: flex;
  gap: $space-8;
  flex: 1;
  justify-content: center;
}

.hdr-nav-item {
  position: relative;
  padding: 8px 0;
  cursor: pointer;
  color: $text-regular;
  font-size: $font-md;
  font-weight: 500;
  transition: color $dur-fast $ease-out;
  user-select: none;

  &:hover {
    color: $primary;
  }

  &.active {
    color: $primary;
    font-weight: 600;
  }
}

.hdr-nav-line {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: $accent;
  transform: scaleX(0);
  transform-origin: center;
  transition: transform $dur-base $ease-out;
}

.hdr-nav-item:hover .hdr-nav-line,
.hdr-nav-item.active .hdr-nav-line {
  transform: scaleX(1);
}

/* CTA */
.hdr-cta {
  flex-shrink: 0;
}

/* 移动端 */
@media (max-width: $bp-md) {
  .hdr {
    height: $mobile-header;
  }
  .hdr-brand-tag,
  .hdr-brand-en {
    display: none;
  }
  .hdr-mark {
    width: 36px;
    height: 36px;
  }
  .hdr-mark-zh {
    font-size: 18px;
  }
  .hdr-nav {
    display: none;
  }
  .hdr-cta {
    :deep(.btn-cta) {
      padding: 8px 14px;
      font-size: 13px;
      letter-spacing: 0.5px;
    }
  }
}
</style>
