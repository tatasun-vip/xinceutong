<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Search, InfoFilled, CircleCheck, Clock, Lock } from '@element-plus/icons-vue'
import { bankApi, type Bank, type BankType } from '@/api/bank'

const router = useRouter()
const banks = ref<Bank[]>([])
const loading = ref(true)

const filterType = ref<BankType | 'all'>('all')
const search = ref('')

const TYPE_OPTIONS: Array<{ value: BankType | 'all'; label: string; }> = [
  { value: 'all', label: '全部' },
  { value: 'state_owned', label: '国有大行' },
  { value: 'joint_stock', label: '股份制' },
  { value: 'internet', label: '互联网银行' },
]

const TYPE_LABELS: Record<BankType, string> = {
  state_owned: '国有大行',
  joint_stock: '股份制',
  internet: '互联网银行',
  policy: '政策性',
  city_commercial: '城商行',
}

const updatedAt = '2026-09-10'

onMounted(async () => {
  try {
    const res = await bankApi.list()
    banks.value = res.items
  } finally {
    loading.value = false
  }
})

const stats = computed(() => {
  const byType: Record<string, number> = { all: banks.value.length }
  banks.value.forEach(b => {
    byType[b.type] = (byType[b.type] || 0) + 1
  })
  return { total: banks.value.length, byType }
})

const filtered = computed(() => {
  return banks.value.filter(b => {
    if (filterType.value !== 'all' && b.type !== filterType.value) return false
    if (search.value && !b.name.includes(search.value) && !b.short_desc?.includes(search.value)) return false
    return true
  })
})

function showInfo() {
  // 简化版：console 提示；实际产品用 el-message-box
  console.info('本平台为模拟测评工具，所有数据基于公开资料建模。')
}

/** logo 加载失败时降级到色块短名 */
function onLogoError(b: Bank) {
  b.logo_url = null
  banks.value = [...banks.value]  // 触发 ref 重渲染
}
</script>

<template>
  <div class="bs">
    <!-- 顶部：步骤进度 -->
    <div class="bs-nav">
      <div class="bs-nav-back" @click="router.back()">←</div>
      <div class="bs-nav-step">
        <span class="bs-nav-step-num">01</span>
        <span class="bs-nav-step-divider">/</span>
        <span class="bs-nav-step-total">05</span>
      </div>
      <div class="bs-nav-info" @click="showInfo">
        <el-icon :size="18"><InfoFilled /></el-icon>
      </div>
    </div>

    <div class="bs container">
      <!-- 标题区：报告感卡片（与 free.vue 报告说明一致） -->
      <div class="bs-head">
        <div class="bs-eyebrow">
          <span class="bs-eyebrow-text">SELECT BANK</span>
          <span class="bs-eyebrow-line"></span>
          <span class="bs-eyebrow-count">{{ stats.total }} 家银行</span>
        </div>

        <div class="bs-intro">
          <div class="bs-intro-title">本测评不是给 10 家银行都打同一个分</div>
          <p class="bs-intro-line">
            我们针对每家银行公开披露的审批偏好、额度区间、风险偏好，分别构建了独立的模拟评分卡。每个模块单独跑一遍，结果反映该行真实的审批倾向。
          </p>
          <p class="bs-intro-line bs-intro-emph">
            这意味着：同一个人在不同银行看到的额度和通过概率，可能天差地别——这正是本测评的价值，不是给一个数，而是让您看清 10 家银行的真实差异。
          </p>
          <p class="bs-intro-tiny">
            本平台为第三方模拟工具，不查征信、不上报任何数据。结果仅供您了解各行审批倾向，不构成贷款承诺。
          </p>
          <div class="bs-intro-meta">
            <span class="bs-intro-meta-row">最近一次更新 · {{ updatedAt }}</span>
            <span class="bs-intro-meta-row">数据来源 · 各行 2025 年度报告 / 公开授信政策</span>
          </div>
        </div>
      </div>

      <!-- 工具栏：segment tabs + 搜索 -->
      <div class="bs-toolbar">
        <div class="bs-tabs">
          <div
            v-for="o in TYPE_OPTIONS"
            :key="o.value"
            :class="['bs-tab', filterType === o.value ? 'bs-tab-active' : '']"
            @click="filterType = o.value"
          >
            <span class="bs-tab-label">{{ o.label }}</span>
            <span class="bs-tab-num">{{ stats.byType[o.value] || 0 }}</span>
          </div>
        </div>
        <div class="bs-search">
          <el-icon :size="16" class="bs-search-icon"><Search /></el-icon>
          <input
            v-model="search"
            class="bs-search-input"
            type="text"
            placeholder="搜索银行名称或描述"
          />
        </div>
      </div>

      <!-- 银行列表 -->
      <div v-loading="loading" class="bs-grid">
        <article
          v-for="(b, idx) in filtered"
          :key="b.code"
          class="bs-card"
          @click="router.push(`/assess/${b.code}`)"
        >
          <!-- 推荐卡：顶部细线 -->
          <div v-if="b.features?.includes('推荐')" class="bs-card-indicator"></div>

          <div class="bs-card-head">
            <!-- logo：优先 url，否则短名 + 品牌色实心 -->
            <img
              v-if="b.logo_url"
              :src="b.logo_url"
              :alt="b.name"
              class="bs-card-logo bs-card-logo-img"
              @error="onLogoError(b)"
            />
            <div
              v-else
              class="bs-card-logo"
              :style="{ background: b.brand_color || '#0B2545' }"
            >
              <span class="bs-card-logo-text">{{ b.short_name.slice(0, 2) }}</span>
              <div class="bs-card-logo-ring"></div>
            </div>

            <div class="bs-card-title">
              <div class="bs-card-name">{{ b.name }}</div>
              <div class="bs-card-en">
                <span class="bs-card-en-name">{{ b.en_name || b.code }}</span>
                <span class="bs-card-en-dot">·</span>
                <span class="bs-card-slogan">{{ b.slogan }}</span>
              </div>
            </div>

            <div class="bs-card-arrow">
              <el-icon :size="16"><ArrowRight /></el-icon>
            </div>
          </div>

          <div class="bs-card-divider"></div>

          <div v-if="b.short_desc" class="bs-card-desc">{{ b.short_desc }}</div>

          <div v-if="b.features && b.features.length" class="bs-card-tags">
            <span v-for="f in b.features.slice(0, 3)" :key="f" class="bs-card-tag">{{ f }}</span>
          </div>

          <div class="bs-card-meta">
            <span class="bs-card-type">{{ TYPE_LABELS[b.type] }}</span>
            <span class="bs-card-no">NO.{{ String(idx + 1).padStart(2, '0') }}</span>
          </div>
        </article>
      </div>

      <!-- 空态 -->
      <div v-if="!loading && filtered.length === 0" class="bs-empty">
        <div class="bs-empty-eyebrow">NO RESULT</div>
        <div class="bs-empty-text">该分类下暂无收录的银行</div>
      </div>

      <!-- 底部信息卡（拉信任） -->
      <div class="bs-info-card">
        <div class="bs-info-card-head">
          <el-icon :size="18" class="bs-info-card-icon"><Lock /></el-icon>
          <span class="bs-info-card-title">关于本测评</span>
        </div>
        <p class="bs-info-card-text">
          本平台根据公开资料 + 50+ 位信贷从业者经验建模，模拟推演各银行审批倾向。结果仅供您了解，<span class="bs-info-card-emph">不代表真实授信</span>，实际以银行审核为准。
        </p>
        <div class="bs-info-card-meta">
          <span>最近更新 · {{ updatedAt }}</span>
          <span class="bs-info-card-dot">·</span>
          <span>覆盖 {{ stats.total }} 家银行</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.bs {
  background: $bg;
  min-height: 100vh;
  padding-bottom: $space-20;
}

// ============ 顶部 nav（步骤进度）============
.bs-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $space-3 $content-padding;
  background: $bg-card;
  border-bottom: 1px solid $border-light;
  position: sticky;
  top: 0;
  z-index: 10;

  &-back {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: $ff-serif;
    font-size: 24px;
    color: $primary;
    cursor: pointer;
    transition: opacity 0.2s;
    &:hover { opacity: 0.7; }
  }
  &-info {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: $primary;
    cursor: pointer;
    border-radius: 50%;
    transition: background 0.2s;
    &:hover { background: $primary-tint; }
  }
  &-step {
    display: flex;
    align-items: baseline;
    gap: 4px;
    font-family: $ff-mono;
    &-num {
      font-size: 20px;
      font-weight: 600;
      color: $primary;
      letter-spacing: 1px;
    }
    &-divider {
      font-size: 14px;
      color: $text-weak;
    }
    &-total {
      font-size: 12px;
      color: $text-weak;
      letter-spacing: 0.5px;
    }
  }
}

// ============ 标题区 ============
.bs-head {
  text-align: left;
  padding: $space-12 0 $space-8;
  max-width: 720px;
}
.bs-eyebrow {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-4;

  &-text {
    font-family: $ff-mono;
    font-size: $font-sm;
    font-weight: 600;
    color: $accent;
    letter-spacing: 4px;
  }
  &-line {
    flex: 0 0 48px;
    height: 1px;
    background: $accent;
  }
  &-count {
    font-family: $ff-mono;
    font-size: $font-xs;
    color: $text-weak;
    letter-spacing: 1px;
  }
}
// 报告感卡片（与 Result 报告说明完全一致）
.bs-intro {
  background: #fff;
  border: 1px solid $border-light;
  border-left: 4px solid $accent;
  padding: 28px 32px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 760px;
}
.bs-intro-title {
  font-family: $ff-serif;
  font-size: 28px;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1px;
  line-height: 1.4;
}
.bs-intro-line {
  font-size: 15px;
  color: $text-main;
  line-height: 1.85;
  letter-spacing: 0.3px;
  margin: 0;
}
.bs-intro-emph {
  color: $primary;
  font-weight: 500;
}
.bs-intro-tiny {
  font-size: 13px;
  color: $text-weak;
  line-height: 1.7;
  letter-spacing: 0.2px;
  margin: 0;
  padding-top: 10px;
  border-top: 1px dashed $border-light;
}
.bs-intro-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 8px;
}
.bs-intro-meta-row {
  font-family: $ff-mono;
  font-size: 12px;
  color: $text-weak;
  letter-spacing: 1px;
}

// ============ 工具栏：tabs + search ============
.bs-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $space-4;
  margin-bottom: $space-6;
  padding-bottom: $space-3;
  border-bottom: 1px solid $border-light;
}
.bs-tabs {
  display: flex;
  gap: 8px;
}
.bs-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: $font-sm;
  color: $text-secondary;
  background: transparent;
  border: 1px solid $border-light;
  border-radius: 100px;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;

  &-label { font-weight: 500; }
  &-num {
    font-family: $ff-mono;
    font-size: 12px;
    color: $text-weak;
    font-weight: 500;
  }
  &:hover {
    border-color: $primary;
    color: $primary;
  }
  &-active {
    background: $primary;
    border-color: $primary;
    .bs-tab-label { color: #fff; font-weight: 600; }
    .bs-tab-num { color: $accent-light; }
  }
}
.bs-search {
  position: relative;
  width: 280px;

  &-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: $text-weak;
  }
  &-input {
    width: 100%;
    height: 40px;
    padding: 0 14px 0 40px;
    border: 1px solid $border-light;
    border-radius: $radius;
    font-size: $font-sm;
    color: $text-main;
    background: $bg-card;
    outline: none;
    transition: border-color 0.2s;
    font-family: $ff-base;
    &::placeholder { color: $text-weak; }
    &:focus { border-color: $primary; }
  }
}

// ============ 银行卡片 ============
.bs-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-4;
}
.bs-card {
  position: relative;
  background: $bg-card;
  border: 1px solid $border-light;
  padding: $space-5;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-md;
    border-color: $primary;
    .bs-card-arrow { background: $primary; color: $accent; transform: translateX(2px); }
  }

  &-indicator {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, $accent 0%, $accent-light 60%, transparent 100%);
  }

  &-head {
    display: flex;
    align-items: center;
    gap: $space-3;
    margin-bottom: $space-4;
  }
  &-logo {
    position: relative;
    width: 56px;
    height: 56px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;

    &-img {
      background: #fff;
      border: 1px solid $border-light;
      object-fit: contain;
      padding: 4px;
    }
  }
  &-logo-text {
    font-family: $ff-serif;
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.5px;
    line-height: 1;
  }
  &-logo-ring {
    position: absolute;
    inset: 0;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
  }

  &-title { flex: 1; min-width: 0; }
  &-name {
    font-family: $ff-serif;
    font-size: 22px;
    color: $primary;
    font-weight: 600;
    margin-bottom: 4px;
    letter-spacing: 1px;
    line-height: 1.2;
  }
  &-en {
    display: flex;
    align-items: center;
    gap: 4px;
    font-family: $ff-mono;
    font-size: 11px;
    color: $text-weak;
    letter-spacing: 0.5px;
  }
  &-en-name {
    text-transform: uppercase;
    font-weight: 500;
  }
  &-en-dot { color: $border-regular; }
  &-slogan {
    color: $text-secondary;
    font-family: $ff-base;
    font-size: 12px;
  }

  &-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: $bg-soft;
    border-radius: 50%;
    color: $primary;
    transition: all 0.2s;
  }

  &-divider {
    height: 1px;
    background: $border-light;
    margin-bottom: $space-3;
  }

  &-desc {
    font-size: $font-sm;
    color: $text-secondary;
    line-height: 1.7;
    margin-bottom: $space-3;
    min-height: 44px;
  }

  &-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: $space-4;
  }
  &-tag {
    font-size: 11px;
    color: $primary;
    background: $primary-tint;
    padding: 3px 10px;
    border-radius: $radius;
    letter-spacing: 0.5px;
    font-weight: 500;
  }

  &-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: $space-3;
    border-top: 1px dashed $border-light;
  }
  &-type {
    font-size: 12px;
    color: $text-weak;
    letter-spacing: 1px;
  }
  &-no {
    font-family: $ff-mono;
    font-size: 11px;
    color: $text-weak;
    letter-spacing: 1px;
  }
}

// ============ 空态 ============
.bs-empty {
  text-align: center;
  padding: $space-16 0;
  color: $text-weak;
  &-eyebrow {
    font-family: $ff-mono;
    font-size: 12px;
    letter-spacing: 4px;
    margin-bottom: $space-2;
  }
  &-text { font-size: $font-sm; color: $text-secondary; }
}

// ============ 底部信息卡（拉信任）============
.bs-info-card {
  margin-top: $space-8;
  padding: $space-5;
  background: $bg-card;
  border: 1px solid $border-light;
  border-left: 3px solid $primary;

  &-head {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: $space-2;
  }
  &-icon { color: $primary; }
  &-title {
    font-family: $ff-serif;
    font-size: 16px;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1px;
  }
  &-text {
    font-size: $font-sm;
    color: $text-secondary;
    line-height: 1.7;
    margin: 0 0 $space-3;
    letter-spacing: 0.3px;
  }
  &-emph { color: $primary; font-weight: 600; }
  &-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: $font-xs;
    color: $text-weak;
    letter-spacing: 0.5px;
  }
  &-dot { color: $border-regular; }
}

@media (max-width: 1100px) {
  .bs-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 720px) {
  .bs-grid { grid-template-columns: 1fr; }
  .bs-toolbar { flex-direction: column; gap: $space-3; align-items: stretch; }
  .bs-search { width: 100%; }
  .bs-intro-title { font-size: 22px; }
}
</style>
