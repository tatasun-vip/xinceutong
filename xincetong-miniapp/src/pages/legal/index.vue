<!--
  pages/legal/index.vue
  法务咨询入口 - 展示场景 + 免费次数 + 开始咨询
-->
<template>
  <view class="page">
    <ComplianceBar />

    <!-- 顶部 nav -->
    <view class="nav">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-char">‹</text>
      </view>
      <view class="nav-title">法务助理</view>
      <view class="nav-spacer"></view>
    </view>

    <!-- 顶部 hero：定位 + 免费次数 -->
    <view class="hero">
      <view class="hero-eyebrow">LEGAL ASSISTANT</view>
      <view class="hero-title">法律咨询在线客服</view>
      <view class="hero-sub">
        贷款逾期 · 信用卡 · 征信修复 · 催收应对
      </view>

      <view class="hero-quota" v-if="usage">
        <view class="hero-quota-line">
          <text class="hero-quota-num">{{ freeRemaining }}</text>
          <text class="hero-quota-text">/ {{ usage.free_limit }} 次免费</text>
        </view>
        <view class="hero-quota-tip">
          {{ freeRemaining > 0
            ? '首次咨询免费，超出后将上线付费服务（9.9 元/次）'
            : '免费次数已用完，后续服务即将上线' }}
        </view>
      </view>
    </view>

    <!-- 场景快速入口 -->
    <view class="scenarios">
      <view class="scenarios-title">
        <text class="scenarios-title-char">常见问题</text>
        <text class="scenarios-title-en">COMMON SCENARIOS</text>
      </view>
      <view class="scenarios-grid">
        <view
          v-for="s in scenarios"
          :key="s.key"
          class="scenario-card"
          @tap="onScenarioTap(s)"
        >
          <view class="scenario-num">{{ String(scenarios.indexOf(s) + 1).padStart(2, '0') }}</view>
          <view class="scenario-title">{{ s.title }}</view>
          <view class="scenario-arrow">›</view>
        </view>
      </view>
    </view>

    <!-- 开始咨询按钮 -->
    <view class="cta" @tap="goChat()">
      <text class="cta-text">{{ freeRemaining > 0 ? '开始免费咨询' : '继续咨询' }}</text>
      <text class="cta-icon">→</text>
    </view>

    <!-- 服务说明 + 免责 -->
    <view class="disclaimer">
      <view class="disclaimer-title">关于本服务</view>
      <view class="disclaimer-text">
        · 本服务由 AI 模型提供，基于公开法律法规和常见案例，回答仅供参考
      </view>
      <view class="disclaimer-text">
        · 不构成正式法律意见，具体诉讼 / 协商建议请咨询当地执业律师
      </view>
      <view class="disclaimer-text">
        · 紧急情况请拨打 12348 法律援助热线 或 110
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import {
  legalUsage,
  legalScenarios,
  getFreeUsed,
  type UsageInfo,
  type Scenario,
} from '@/api/legal'

const usage = ref<UsageInfo | null>(null)
const scenarios = ref<Scenario[]>([])
const freeUsed = ref(0)

const freeRemaining = ref(0)

onMounted(async () => {
  freeUsed.value = getFreeUsed()
  await Promise.all([loadUsage(), loadScenarios()])
})

async function loadUsage() {
  try {
    usage.value = await legalUsage()
    if (usage.value) {
      freeRemaining.value = Math.max(0, usage.value.free_limit - freeUsed.value)
    }
  } catch (e) {
    console.error('加载服务状态失败', e)
  }
}

async function loadScenarios() {
  try {
    scenarios.value = await legalScenarios()
  } catch (e) {
    console.error('加载场景失败', e)
    // fallback：前端内置兜底
    scenarios.value = [
      { key: 'credit_overdue', title: '信用卡逾期', prompt: '我信用卡逾期了怎么办？' },
      { key: 'online_loan', title: '网贷催收', prompt: '网贷还不上，催收说要上门是真的吗？' },
      { key: 'credit_repair', title: '征信修复', prompt: '征信报告上有逾期记录，怎么消除？' },
      { key: 'lawsuit', title: '被起诉应诉', prompt: '我被银行起诉了，应该怎么应诉？' },
    ]
  }
}

function onScenarioTap(s: Scenario) {
  uni.setStorageSync('legal_prefill', s.prompt)
  goChat()
}

function goChat() {
  uni.navigateTo({ url: '/pages/legal/chat' })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg;
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
}

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: $card;

  &-back {
    width: 64rpx;
    height: 64rpx;
    display: flex;
    align-items: center;
    justify-content: center;

    &-char {
      font-family: $ff-serif;
      font-size: 56rpx;
      color: $primary;
      line-height: 1;
      font-weight: 400;
    }
  }

  &-title {
    font-family: $ff-serif;
    font-size: 32rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }

  &-spacer {
    width: 64rpx;
  }
}

.hero {
  background: $card;
  padding: 48rpx 32rpx 32rpx;
  border-bottom: 1rpx solid $border-light;

  &-eyebrow {
    font-family: $ff-mono;
    font-size: 22rpx;
    font-weight: 600;
    color: $accent;
    letter-spacing: 4rpx;
    margin-bottom: 16rpx;
  }

  &-title {
    font-family: $ff-serif;
    font-size: 48rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 2rpx;
    line-height: 1.3;
    margin-bottom: 16rpx;
  }

  &-sub {
    font-size: 28rpx;
    color: $text-sub;
    line-height: 1.6;
    letter-spacing: 0.5rpx;
    margin-bottom: 32rpx;
  }

  &-quota {
    padding: 24rpx 28rpx;
    background: $primary-light;
    border-left: 4rpx solid $accent;
  }

  &-quota-line {
    display: flex;
    align-items: baseline;
    gap: 8rpx;
    margin-bottom: 8rpx;
  }

  &-quota-num {
    font-family: $ff-serif;
    font-size: 56rpx;
    font-weight: 700;
    color: $primary;
    line-height: 1;
  }

  &-quota-text {
    font-family: $ff-mono;
    font-size: 22rpx;
    color: $text-sub;
  }

  &-quota-tip {
    font-size: 22rpx;
    color: $text-sub;
    line-height: 1.5;
    letter-spacing: 0.5rpx;
  }
}

.scenarios {
  padding: 32rpx;

  &-title {
    display: flex;
    align-items: baseline;
    gap: 12rpx;
    margin-bottom: 24rpx;
  }

  &-title-char {
    font-family: $ff-serif;
    font-size: 30rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }

  &-title-en {
    font-family: $ff-mono;
    font-size: 18rpx;
    color: $text-weak;
    letter-spacing: 2rpx;
  }

  &-grid {
    display: flex;
    flex-direction: column;
    gap: 16rpx;
  }
}

.scenario-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 28rpx 32rpx;
  background: $card;
  border: 1rpx solid $border-light;
  transition: all 0.2s;

  &:active {
    background: $bg-2;
    transform: scale(0.99);
  }

  &-num {
    font-family: $ff-mono;
    font-size: 22rpx;
    color: $accent;
    font-weight: 600;
    letter-spacing: 1rpx;
    min-width: 48rpx;
  }

  &-title {
    flex: 1;
    font-family: $ff-serif;
    font-size: 30rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }

  &-arrow {
    font-size: 40rpx;
    color: $text-weak;
    line-height: 1;
    font-weight: 300;
  }
}

.cta {
  margin: 32rpx;
  padding: 28rpx;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  border-radius: 4rpx;
  transition: all 0.2s;

  &:active {
    background: $primary-dark;
    transform: scale(0.99);
  }

  &-text {
    font-family: $ff-serif;
    font-size: 32rpx;
    font-weight: 600;
    color: #fff;
    letter-spacing: 4rpx;
  }

  &-icon {
    font-size: 32rpx;
    color: $accent;
    font-weight: 400;
  }
}

.disclaimer {
  margin: 32rpx;
  padding: 24rpx 28rpx;
  background: $bg-2;
  border-left: 3rpx solid $text-weak;

  &-title {
    font-family: $ff-serif;
    font-size: 24rpx;
    font-weight: 600;
    color: $text-sub;
    margin-bottom: 12rpx;
    letter-spacing: 1rpx;
  }

  &-text {
    font-size: 22rpx;
    color: $text-weak;
    line-height: 1.7;
    letter-spacing: 0.5rpx;
    margin-bottom: 6rpx;
  }
}
</style>
