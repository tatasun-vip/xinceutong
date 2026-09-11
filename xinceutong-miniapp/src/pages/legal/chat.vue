<!--
  pages/legal/chat.vue
  法务 AI 聊天界面
-->
<template>
  <view class="page">
    <!-- 顶部 nav -->
    <view class="nav">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-char">‹</text>
      </view>
      <view class="nav-center">
        <view class="nav-title">法务助理</view>
        <view class="nav-sub">{{ usage?.enabled ? 'AI 在线 · DeepSeek' : '暂未配置' }}</view>
      </view>
      <view class="nav-action" @tap="clearChat">
        <text class="nav-action-text">清空</text>
      </view>
    </view>

    <!-- 消息列表 -->
    <scroll-view
      class="messages"
      :scroll-y="true"
      :scroll-into-view="scrollIntoView"
      :upper-threshold="50"
    >
      <!-- 欢迎语 -->
      <view v-if="messages.length === 0" class="welcome">
        <view class="welcome-eyebrow">AI LEGAL ASSISTANT</view>
        <view class="welcome-title">您好，我是您的法务助理</view>
        <view class="welcome-text">
          贷款逾期、信用卡、催收应对、征信修复等问题，<br />
          请直接描述您的情况，我会尽力帮您分析。
        </view>
        <view class="welcome-tips">
          <view class="welcome-tip">· 描述越具体，建议越精准</view>
          <view class="welcome-tip">· 单次回答约 1-3 秒</view>
          <view class="welcome-tip">· 信息仅用于生成回答，不会保存</view>
        </view>
      </view>

      <!-- 消息气泡 -->
      <view
        v-for="(m, i) in messages"
        :key="i"
        :id="`msg-${i}`"
        :class="['msg-row', m.role]"
      >
        <view v-if="m.role === 'assistant'" class="msg-avatar">
          <text class="msg-avatar-text">AI</text>
        </view>
        <view class="msg-bubble">
          <text class="msg-content" :selectable="true" space="emsp">{{ m.content }}</text>
        </view>
        <view v-if="m.role === 'user'" class="msg-avatar msg-avatar-user">
          <text class="msg-avatar-text">我</text>
        </view>
      </view>

      <!-- AI 思考中 -->
      <view v-if="loading" class="msg-row assistant" id="msg-loading">
        <view class="msg-avatar">
          <text class="msg-avatar-text">AI</text>
        </view>
        <view class="msg-bubble msg-bubble-loading">
          <view class="loading-dots">
            <view class="loading-dot"></view>
            <view class="loading-dot"></view>
            <view class="loading-dot"></view>
          </view>
          <text class="msg-loading-text">正在分析...</text>
        </view>
      </view>

      <view class="messages-bottom" :style="{ height: '32rpx' }"></view>
    </scroll-view>

    <!-- 输入栏 -->
    <view class="input-bar">
      <view class="input-quota" v-if="freeRemaining === 0 && !paid">
        <text class="input-quota-text">免费次数已用完</text>
      </view>
      <view class="input-row">
        <textarea
          v-model="input"
          class="input-textarea"
          placeholder="输入您的问题..."
          placeholder-class="input-placeholder"
          :auto-height="true"
          :maxlength="2000"
          :show-confirm-bar="false"
          :adjust-position="true"
          :cursor-spacing="20"
          :disabled="freeRemaining === 0 && !paid"
          @input="onInput"
        />
        <button
          class="send-btn"
          :class="{ 'send-btn-active': canSend }"
          :disabled="!canSend"
          @tap="send"
        >
          <text class="send-btn-text">发送</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import {
  legalChat,
  legalUsage,
  getFreeUsed,
  incFreeUsed,
  getOrCreateUserId,
  type UsageInfo,
  type ChatMessage,
} from '@/api/legal'

const messages = ref<ChatMessage[]>([])
const input = ref('')
const loading = ref(false)
const freeUsed = ref(0)
const freeLimit = ref(1)
const usage = ref<UsageInfo | null>(null)
const paid = ref(false) // MVP 阶段：付费锁 stub
const userId = getOrCreateUserId()

const scrollIntoView = ref('')
const canSend = computed(() => input.value.trim().length > 0 && !loading.value && (freeRemaining.value > 0 || paid.value))
const freeRemaining = computed(() => Math.max(0, freeLimit.value - freeUsed.value))

onLoad(() => {
  // 从入口页预填问题
  const prefill = uni.getStorageSync('legal_prefill')
  if (prefill) {
    input.value = prefill
    uni.removeStorageSync('legal_prefill')
  }
})

onShow(() => {
  loadUsage()
  freeUsed.value = getFreeUsed()
})

async function loadUsage() {
  try {
    usage.value = await legalUsage()
    if (usage.value) {
      freeLimit.value = usage.value.free_limit
    }
  } catch (e) {
    console.error('加载服务状态失败', e)
  }
}

function onInput(e: any) {
  input.value = e.detail.value
}

async function send() {
  const text = input.value.trim()
  if (!text || loading.value) return

  // 免费次数检查
  if (freeRemaining.value <= 0 && !paid.value) {
    showPayLock()
    return
  }

  // 添加用户消息
  const userMsg: ChatMessage = { role: 'user', content: text }
  messages.value.push(userMsg)
  input.value = ''

  // 滚动到底
  await nextTick()
  scrollToBottom()

  loading.value = true
  try {
    // 调用 AI（只传最近 10 轮，控制 token）
    const recent = messages.value.slice(-10)
    const result = await legalChat(recent, userId, `s_${Date.now()}`)

    // 扣免费次数（仅在未付费时）
    if (!paid.value) {
      freeUsed.value = incFreeUsed()
    }

    // 添加 AI 回复
    messages.value.push({
      role: 'assistant',
      content: result.reply,
    })
  } catch (e: any) {
    console.error('AI 调用失败', e)
    let errMsg = '抱歉，服务暂时不可用，请稍后重试。'
    // 优先根据 statusCode 精确判断
    if (e?.statusCode === 503) {
      errMsg = '法务 AI 暂未配置 DEEPSEEK_API_KEY。\n请管理员在 Vercel 环境变量中配置后即可使用。'
    } else if (e?.statusCode === 502) {
      errMsg = 'AI 服务上游异常，请稍后重试。'
    } else if (e?.statusCode === 500) {
      errMsg = '服务器内部错误，请稍后重试。'
    } else if (e?.statusCode === 404) {
      errMsg = 'API 路由不存在，请检查部署。'
    } else if (e?.networkError) {
      errMsg = '网络异常，请检查网络后重试。\n（如跨域或 VPN 可能影响访问）'
    } else if (e?.message?.includes('503')) {
      errMsg = '法务 AI 暂未配置 DEEPSEEK_API_KEY。'
    } else if (e?.message?.includes('502')) {
      errMsg = 'AI 服务异常，请稍后重试。'
    } else if (e?.message?.includes('网络')) {
      errMsg = '网络异常，请检查网络后重试。'
    }
    messages.value.push({
      role: 'assistant',
      content: `⚠️ ${errMsg}\n\n如需帮助，请拨打：\n· 12348 法律援助热线\n· 12378 银保监投诉\n· 12309 检察服务`,
    })
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  if (messages.value.length > 0) {
    scrollIntoView.value = `msg-${messages.value.length - 1}`
  } else if (loading.value) {
    scrollIntoView.value = 'msg-loading'
  }
}

function showPayLock() {
  uni.showModal({
    title: '免费次数已用完',
    content: '解锁深度服务 ¥9.9/次（即将上线）\n\n当前可继续体验：清空后重置免费次数（仅本次会话）。',
    confirmText: '了解付费',
    cancelText: '清空记录',
    success: (r) => {
      if (r.cancel) {
        clearChat()
      }
    },
  })
}

function clearChat() {
  uni.showModal({
    title: '确认清空',
    content: '清空后会话记录将删除，并重置免费次数。',
    success: (r) => {
      if (r.confirm) {
        messages.value = []
        uni.removeStorageSync('xinceutong_legal_free_used')
        freeUsed.value = 0
      }
    },
  })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style lang="scss" scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg;
}

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  background: $card;
  border-bottom: 1rpx solid $border-light;

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

  &-center {
    flex: 1;
    text-align: center;
  }

  &-title {
    font-family: $ff-serif;
    font-size: 30rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }

  &-sub {
    font-family: $ff-mono;
    font-size: 18rpx;
    color: $text-weak;
    letter-spacing: 1rpx;
    margin-top: 4rpx;
  }

  &-action {
    width: 80rpx;
    text-align: right;
  }

  &-action-text {
    font-size: 24rpx;
    color: $text-sub;
  }
}

.messages {
  flex: 1;
  padding: 24rpx 24rpx 0;
  box-sizing: border-box;
}

.welcome {
  padding: 64rpx 32rpx;
  text-align: center;

  &-eyebrow {
    font-family: $ff-mono;
    font-size: 20rpx;
    color: $accent;
    letter-spacing: 4rpx;
    font-weight: 600;
    margin-bottom: 16rpx;
  }

  &-title {
    font-family: $ff-serif;
    font-size: 36rpx;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
    margin-bottom: 24rpx;
  }

  &-text {
    font-size: 26rpx;
    color: $text-sub;
    line-height: 1.8;
    letter-spacing: 0.5rpx;
    margin-bottom: 32rpx;
  }

  &-tips {
    text-align: left;
    padding: 24rpx 28rpx;
    background: $card;
    border: 1rpx solid $border-light;
  }

  &-tip {
    font-size: 22rpx;
    color: $text-weak;
    line-height: 1.7;
    letter-spacing: 0.5rpx;
  }
}

.msg-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;

  &.user {
    flex-direction: row-reverse;
  }
}

.msg-avatar {
  width: 64rpx;
  height: 64rpx;
  background: $primary;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &-text {
    font-family: $ff-serif;
    font-size: 22rpx;
    color: #fff;
    font-weight: 600;
    letter-spacing: 1rpx;
  }

  &-user {
    background: $accent;
  }
}

.msg-bubble {
  max-width: 72%;
  padding: 20rpx 24rpx;
  background: $card;
  border: 1rpx solid $border-light;
  border-radius: 4rpx;
}

.msg-row.user .msg-bubble {
  background: $primary;
  border-color: $primary;
}

.msg-content {
  font-size: 28rpx;
  color: $text-main;
  line-height: 1.7;
  letter-spacing: 0.5rpx;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.msg-row.user .msg-content {
  color: #fff;
}

.msg-bubble-loading {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.loading-dots {
  display: flex;
  gap: 8rpx;
}

.loading-dot {
  width: 12rpx;
  height: 12rpx;
  background: $accent;
  border-radius: 50%;
  animation: bounce 1.2s infinite;
}

.loading-dot:nth-child(2) { animation-delay: 0.15s; }
.loading-dot:nth-child(3) { animation-delay: 0.3s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-8rpx); opacity: 1; }
}

.msg-loading-text {
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 0.5rpx;
}

.input-bar {
  background: $card;
  border-top: 1rpx solid $border-light;
  padding: 16rpx 24rpx calc(16rpx + env(safe-area-inset-bottom));
}

.input-quota {
  padding: 12rpx 16rpx;
  background: $bg-2;
  border-left: 3rpx solid $accent;
  margin-bottom: 12rpx;

  &-text {
    font-size: 22rpx;
    color: $accent;
    font-weight: 500;
  }
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 12rpx;
}

.input-textarea {
  flex: 1;
  min-height: 72rpx;
  max-height: 240rpx;
  padding: 16rpx 20rpx;
  background: $bg-2;
  border: 1rpx solid $border-light;
  border-radius: 4rpx;
  font-size: 28rpx;
  color: $text-main;
  line-height: 1.5;
  box-sizing: border-box;
}

.input-placeholder {
  color: $text-weak;
  font-size: 28rpx;
}

.send-btn {
  padding: 16rpx 28rpx;
  background: $bg-2;
  border: 1rpx solid $border-light;
  border-radius: 4rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &-active {
    background: $primary;
    border-color: $primary;
  }

  &-text {
    font-family: $ff-serif;
    font-size: 26rpx;
    font-weight: 600;
    color: $text-weak;
    letter-spacing: 1rpx;
  }
}

.send-btn-active .send-btn-text {
  color: #fff;
}
</style>
