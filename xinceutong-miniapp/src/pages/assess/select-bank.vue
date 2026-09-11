<!--
  select-bank.vue - 选择目标银行（测评入口）
  v2 (2026-09-10): 重新设计 — 提升信任感与设计水准
  - 去除标题重复（nav 1/5 + 步骤区大标）
  - logo 升级（短名 + 品牌色 + 白边）
  - 加 eyebrow + 数据徽章（已收录 / 更新于）
  - tabs 改 segment + 数量
  - 卡片加品牌渐变指示 + EN 副标 + 金线分割
  数据：GET /api/banks
-->
<template>
  <view class="page">
    <ComplianceBar />

    <!-- 顶部导航：步骤进度 + 操作 -->
    <view class="nav">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-char">‹</text>
      </view>
      <view class="nav-step">
        <text class="nav-step-num">01</text>
        <text class="nav-step-divider">/</text>
        <text class="nav-step-total">05</text>
      </view>
      <view class="nav-info" @tap="showInfo">
        <UiIcon name="info" :size="32" color="#0B2545" />
      </view>
    </view>

    <!-- 标题区：报告感卡片（与 free.vue 报告说明一致） -->
    <view class="hero">
      <view class="hero-eyebrow-row">
        <text class="hero-eyebrow">SELECT BANK</text>
        <text class="hero-eyebrow-line"></text>
        <text class="hero-eyebrow-count">{{ stats.total }} 家银行</text>
      </view>

      <view class="hero-intro">
        <view class="hero-intro-title">
          <text v-if="store.type === 'business'">本测评不是给 10 家银行都打同一个经营贷分数</text>
          <text v-else>本测评不是给 10 家银行都打同一个分</text>
        </view>
        <view class="hero-intro-line">
          <text v-if="store.type === 'business'">我们针对每家银行对公业务的审批偏好、纳税贷/开票贷额度区间、企业风险偏好，分别构建了独立的模拟评分卡。每个模块单独跑一遍，结果反映该行对公业务的真实审批倾向。</text>
          <text v-else>我们针对每家银行公开披露的审批偏好、额度区间、风险偏好，分别构建了独立的模拟评分卡。每个模块单独跑一遍，结果反映该行真实的审批倾向。</text>
        </view>
        <view class="hero-intro-line hero-intro-emph">
          <text v-if="store.type === 'business'">这意味着：同一企业在不同银行看到的对公额度和通过概率，可能天差地别——这正是本测评的价值，不是给一个数，而是让您看清 10 家银行对企业经营贷的真实差异。</text>
          <text v-else>这意味着：同一个人在不同银行看到的额度和通过概率，可能天差地别——这正是本测评的价值，不是给一个数，而是让您看清 10 家银行的真实差异。</text>
        </view>
        <view class="hero-intro-tiny">
          本平台为第三方模拟工具，不查征信、不上报任何数据。结果仅供您了解各行审批倾向，不构成贷款承诺。
        </view>
        <view class="hero-intro-meta">
          <text class="hero-intro-meta-row">最近一次更新 · {{ updatedAt }}</text>
          <text class="hero-intro-meta-row">数据来源 · 各行 2025 年度报告 / 公开授信政策</text>
        </view>
      </view>
    </view>

    <!-- 分类标签：segment + 数量 -->
    <view class="tabs">
      <view
        v-for="t in tabs"
        :key="t.value"
        :class="['tab', activeTab === t.value ? 'tab-active' : '']"
        @tap="activeTab = t.value"
      >
        <text class="tab-label">{{ t.label }}</text>
        <text class="tab-num">{{ stats.byType[t.value] || 0 }}</text>
      </view>
    </view>

    <!-- 银行列表 -->
    <view v-if="!loading" class="bank-list">
      <view
        v-for="(b, idx) in filteredBanks"
        :key="b.code"
        class="bank-card"
        @tap="onSelect(b)"
      >
        <!-- 推荐标识：仅顶部细线 -->
        <view v-if="b.features?.includes('推荐')" class="bank-card-indicator"></view>

        <view class="bank-card-head">
          <!-- logo：优先 url，否则短名 + 品牌色实心 -->
          <view
            v-if="!b.logo_url"
            class="bank-card-logo"
            :style="{ background: b.brand_color || '#0B2545' }"
          >
            <text class="bank-card-logo-text">{{ b.short_name.slice(0, 2) }}</text>
            <view class="bank-card-logo-ring"></view>
          </view>
          <image
            v-else
            class="bank-card-logo-img"
            :src="b.logo_url"
            mode="aspectFit"
            @error="onLogoError(b)"
          />
          <view class="bank-card-title">
            <view class="bank-card-name">{{ b.name }}</view>
            <view class="bank-card-en">
              <text class="bank-card-en-name">{{ b.en_name || b.code }}</text>
              <text class="bank-card-en-dot">·</text>
              <text class="bank-card-slogan">{{ b.slogan }}</text>
            </view>
          </view>
          <view class="bank-card-arrow">
            <UiIcon name="arrow-right" :size="28" color="#0B2545" />
          </view>
        </view>

        <view class="bank-card-divider"></view>

        <view v-if="b.short_desc" class="bank-card-desc">{{ b.short_desc }}</view>

        <view v-if="b.features && b.features.length" class="bank-card-tags">
          <text v-for="f in b.features.slice(0, 3)" :key="f" class="bank-card-tag">{{ f }}</text>
        </view>

        <view class="bank-card-meta">
          <text class="bank-card-type">{{ TYPE_LABELS[b.type] }}</text>
          <text class="bank-card-no">NO.{{ String(idx + 1).padStart(2, '0') }}</text>
        </view>
      </view>
    </view>

    <!-- 加载态 -->
    <view v-else class="loading">
      <view class="loading-bar"></view>
      <view class="loading-bar loading-bar-2"></view>
      <view class="loading-bar loading-bar-3"></view>
    </view>

    <!-- 空态 -->
    <view v-if="!loading && filteredBanks.length === 0" class="empty">
      <view class="empty-eyebrow">NO RESULT</view>
      <view class="empty-text">该分类下暂无收录的银行</view>
    </view>

    <!-- 底部信息卡（拉信任） -->
    <view class="info-card">
      <view class="info-card-head">
        <UiIcon name="shield" :size="32" color="#0B2545" />
        <text class="info-card-title">关于本测评</text>
      </view>
      <view class="info-card-text">
        本平台根据公开资料 + 50+ 位信贷从业者经验建模，模拟推演各银行审批倾向。结果仅供您了解，<text class="info-card-emph">不代表真实授信</text>，实际以银行审核为准。
      </view>
      <view class="info-card-meta">
        <text>最近更新 · {{ updatedAt }}</text>
        <text class="info-card-dot">·</text>
        <text>覆盖 {{ stats.total }} 家银行</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { listBanks, type Bank, type BankType } from '@/api/bank'
import { useAssessmentStore } from '@/store/assessment'
import { pageView } from '@/utils/track'

const store = useAssessmentStore()
const banks = ref<Bank[]>([])
const loading = ref(true)
const activeTab = ref<'all' | BankType>('all')

const TYPE_LABELS: Record<BankType, string> = {
  state_owned: '国有大行',
  joint_stock: '股份制',
  internet: '互联网',
  policy: '政策性',
  city_commercial: '城商行',
}

const tabs = [
  { value: 'all' as const, label: '全部' },
  { value: 'state_owned' as const, label: '国有大行' },
  { value: 'joint_stock' as const, label: '股份制' },
  { value: 'internet' as const, label: '互联网' },
]

// 更新日期（系统级常量；实际产品可以放后端返回）
const updatedAt = '2026-09-10'

// 按类型统计
const stats = computed(() => {
  const byType: Record<string, number> = { all: banks.value.length }
  banks.value.forEach(b => {
    byType[b.type] = (byType[b.type] || 0) + 1
  })
  return { total: banks.value.length, byType }
})

const filteredBanks = computed(() => {
  if (activeTab.value === 'all') return banks.value
  return banks.value.filter(b => b.type === activeTab.value)
})

onMounted(async () => {
  pageView('assess/select-bank')
  try {
    const r = await listBanks()
    banks.value = r.items
  } catch (e) {
    console.error('加载银行列表失败', e)
  } finally {
    loading.value = false
  }
})

function onSelect(b: Bank) {
  store.setBank(b.code, b.name)
  uni.redirectTo({ url: '/pages/assess/select-product' })
}

function goBack() {
  uni.navigateBack()
}

/** logo 加载失败时降级到色块短名 */
function onLogoError(b: Bank) {
  b.logo_url = undefined
  // 触发 ref 重渲染（修改对象属性不会自动触发）
  banks.value = [...banks.value]
}

function showInfo() {
  uni.showModal({
    title: '关于测评',
    content: '本平台为模拟测评工具，所有数据基于公开资料建模。测评结果仅供您了解不同银行的审批倾向，不构成贷款承诺。',
    showCancel: false,
    confirmText: '我知道了',
  })
}
</script>

<style lang="scss" scoped>
// 变量由 vite.config.ts additionalData 自动从 uni-globals.scss 注入

.page {
  min-height: 100vh;
  background: $bg;
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
}

// ============ 顶部 nav（步骤进度）============
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: $card;

  &-back,
  &-info {
    width: 64rpx;
    height: 64rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  &-back-char {
    font-family: $ff-serif;
    font-size: 56rpx;
    color: $primary;
    line-height: 1;
    font-weight: 400;
  }

  &-step {
    display: flex;
    align-items: baseline;
    gap: 6rpx;
    font-family: $ff-mono;

    &-num {
      font-size: 36rpx;
      font-weight: 600;
      color: $primary;
      letter-spacing: 1rpx;
    }
    &-divider {
      font-size: 24rpx;
      color: $text-weak;
    }
    &-total {
      font-size: 22rpx;
      color: $text-weak;
      letter-spacing: 0.5rpx;
    }
  }
}

// ============ 标题区（编辑感）============
.hero {
  padding: 48rpx 32rpx 32rpx;
  background: $card;

  &-eyebrow-row {
    display: flex;
    align-items: center;
    gap: 16rpx;
    padding: 0 32rpx 24rpx;
  }
  &-eyebrow {
    font-family: $ff-mono;
    font-size: 22rpx;
    font-weight: 600;
    color: $accent;
    letter-spacing: 4rpx;
  }
  &-eyebrow-line {
    flex: 0 0 64rpx;
    height: 1rpx;
    background: $accent;
  }
  &-eyebrow-count {
    font-family: $ff-mono;
    font-size: 20rpx;
    color: $text-weak;
    letter-spacing: 1rpx;
  }

  // 报告感卡片（与 free.vue 报告说明完全一致）
  &-intro {
    background: $card;
    margin: 0 32rpx 32rpx;
    border: 1rpx solid $border-light;
    border-left: 4rpx solid $accent;
    padding: 28rpx 32rpx;
    display: flex;
    flex-direction: column;
    gap: 16rpx;
  }
  &-intro-title {
    font-family: $ff-serif;
    font-size: 36rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
    line-height: 1.4;
    display: block;
  }
  &-intro-line {
    font-size: 28rpx;
    color: $text-main;
    line-height: 1.85;
    letter-spacing: 0.5rpx;
    display: block;
  }
  &-intro-emph {
    color: $primary;
    font-weight: 500;
  }
  &-intro-tiny {
    font-size: 24rpx;
    color: $text-weak;
    line-height: 1.7;
    letter-spacing: 0.3rpx;
    display: block;
    padding-top: 8rpx;
    border-top: 1rpx dashed $border-light;
    margin-top: 4rpx;
  }
  &-intro-meta {
    display: flex;
    flex-direction: column;
    gap: 4rpx;
    padding-top: 8rpx;
  }
  &-intro-meta-row {
    font-family: $ff-mono;
    font-size: 20rpx;
    color: $text-weak;
    letter-spacing: 1rpx;
  }
}

// ============ Tabs：segment + 数量 ============
.tabs {
  display: flex;
  gap: 8rpx;
  padding: 32rpx 32rpx 16rpx;
  background: $card;
  border-bottom: 1rpx solid $border-light;
}
.tab {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 24rpx;
  font-size: $font-sm;
  color: $text-sub;
  background: transparent;
  border: 1rpx solid $border-light;
  border-radius: 100rpx;
  letter-spacing: 0.5rpx;
  white-space: nowrap;
  transition: all 0.2s;

  &-label {
    font-weight: 500;
  }
  &-num {
    font-family: $ff-mono;
    font-size: 20rpx;
    color: $text-weak;
    font-weight: 500;
  }
  &-active {
    background: $primary;
    border-color: $primary;

    .tab-label { color: #fff; font-weight: 600; }
    .tab-num { color: $accent; }
  }
}

// ============ 银行列表 ============
.bank-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  padding: 32rpx;
}
.bank-card {
  position: relative;
  background: $card;
  border: 1rpx solid $border-light;
  padding: 32rpx;
  transition: all 0.2s;

  &:active {
    transform: scale(0.99);
    background: $bg-2;
  }

  &-indicator {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3rpx;
    background: linear-gradient(90deg, $accent 0%, $accent-light 60%, transparent 100%);
  }

  &-head {
    display: flex;
    align-items: center;
    gap: 20rpx;
    margin-bottom: 24rpx;
  }

  // logo：品牌色实心 + 白边
  &-logo {
    position: relative;
    width: 80rpx;
    height: 80rpx;
    border-radius: 12rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
  }
  &-logo-text {
    font-family: $ff-serif;
    font-size: 30rpx;
    font-weight: 700;
    color: #fff;
    letter-spacing: 1rpx;
    line-height: 1;
  }
  &-logo-ring {
    position: absolute;
    inset: 0;
    border: 1rpx solid rgba(255, 255, 255, 0.3);
    border-radius: 12rpx;
  }
  &-logo-img {
    width: 80rpx;
    height: 80rpx;
    border-radius: 12rpx;
    flex-shrink: 0;
  }

  &-title { flex: 1; min-width: 0; }
  &-name {
    font-family: $ff-serif;
    font-size: 36rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
    line-height: 1.2;
    margin-bottom: 6rpx;
  }
  &-en {
    display: flex;
    align-items: center;
    gap: 6rpx;
    font-family: $ff-mono;
    font-size: 20rpx;
    color: $text-weak;
    letter-spacing: 0.5rpx;
  }
  &-en-name {
    text-transform: uppercase;
    font-weight: 500;
  }
  &-en-dot { color: $border; }
  &-slogan {
    color: $text-sub;
    font-family: $ff-base;
    font-size: 22rpx;
  }

  &-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56rpx;
    height: 56rpx;
    background: $bg-2;
    border-radius: 50%;
  }

  &-divider {
    height: 1rpx;
    background: $border-light;
    margin-bottom: 20rpx;
  }

  &-desc {
    font-size: $font-sm;
    color: $text-sub;
    line-height: 1.7;
    letter-spacing: 0.5rpx;
    margin-bottom: 20rpx;
  }

  &-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8rpx;
    margin-bottom: 20rpx;
  }
  &-tag {
    font-size: 20rpx;
    color: $primary;
    background: $primary-light;
    padding: 4rpx 14rpx;
    border-radius: $radius-tag;
    letter-spacing: 0.5rpx;
    font-weight: 500;
  }

  &-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 20rpx;
    border-top: 1rpx dashed $border-light;
  }
  &-type {
    font-size: 22rpx;
    color: $text-weak;
    letter-spacing: 1rpx;
  }
  &-no {
    font-family: $ff-mono;
    font-size: 20rpx;
    color: $text-weak;
    letter-spacing: 1rpx;
  }
}

// ============ 加载态 ============
.loading {
  padding: 64rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;

  &-bar {
    height: 200rpx;
    background: $card;
    border: 1rpx solid $border-light;
    border-radius: 4rpx;
    animation: pulse 1.4s ease-in-out infinite;
  }
  &-bar-2 { animation-delay: 0.2s; }
  &-bar-3 { animation-delay: 0.4s; }
}
@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

// ============ 空态 ============
.empty {
  padding: 96rpx 32rpx;
  text-align: center;
  &-eyebrow {
    font-family: $ff-mono;
    font-size: 24rpx;
    color: $text-weak;
    letter-spacing: 4rpx;
    margin-bottom: 16rpx;
  }
  &-text {
    font-size: $font-sm;
    color: $text-sub;
  }
}

// ============ 底部信息卡（拉信任）============
.info-card {
  margin: 32rpx;
  padding: 32rpx;
  background: $card;
  border: 1rpx solid $border-light;
  border-left: 3rpx solid $primary;

  &-head {
    display: flex;
    align-items: center;
    gap: 12rpx;
    margin-bottom: 16rpx;
  }
  &-title {
    font-family: $ff-serif;
    font-size: 28rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }
  &-text {
    font-size: 24rpx;
    color: $text-sub;
    line-height: 1.7;
    letter-spacing: 0.5rpx;
    margin-bottom: 16rpx;
  }
  &-emph {
    color: $primary;
    font-weight: 600;
  }
  &-meta {
    display: flex;
    align-items: center;
    gap: 8rpx;
    font-size: 20rpx;
    color: $text-weak;
    letter-spacing: 0.5rpx;
  }
  &-dot { color: $border; }
}
</style>
