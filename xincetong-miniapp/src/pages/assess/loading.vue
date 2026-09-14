<template>
  <view class="loading-page">
    <ComplianceBar />

    <view class="loading-content">
      <view class="loading-brand">
        <view class="loading-eyebrow">CREDIT ASSESSMENT</view>
        <view class="loading-title">信测通</view>
        <view class="loading-line" />
      </view>

      <view class="loading-ring">
        <svg class="loading-ring-svg" viewBox="0 0 100 100">
          <circle class="loading-ring-bg" cx="50" cy="50" r="42" />
          <circle
            class="loading-ring-fill"
            cx="50" cy="50" r="42"
            :stroke-dasharray="`${progress * 2.64} 264`"
          />
        </svg>
        <view class="loading-ring-center">
          <text class="loading-ring-num">{{ String(currentIdx + 1).padStart(2, '0') }}</text>
          <text class="loading-ring-total">/ {{ String(stepTexts.length).padStart(2, '0') }}</text>
        </view>
      </view>

      <view class="loading-status">
        <text class="loading-status-text">{{ stepText }}</text>
      </view>

      <view class="loading-steps">
        <view
          v-for="(s, idx) in stepTexts"
          :key="s"
          :class="['loading-step', idx <= currentIdx ? 'done' : '']"
        >
          <text class="loading-step-idx">{{ String(idx + 1).padStart(2, '0') }}</text>
          <text class="loading-step-name">{{ s }}</text>
          <text v-if="idx < currentIdx" class="loading-step-mark">·</text>
        </view>
      </view>
    </view>

    <view class="loading-footer">
      <text class="text-disclaimer">
        本过程为模拟运算，<text class="text-bold">不查征信</text>、<text class="text-bold">不读取任何银行数据</text>
      </text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import { useAssessmentStore } from '@/store/assessment'
import { useStepGuard } from '@/composables/useStepGuard'
import { assessmentApi } from '@/api'
import { pageView, track } from '@/utils/track'
import { getStorage } from '@/utils/storage'

useStepGuard(5)

const store = useAssessmentStore()

const stepTexts = ['汇总数据', '校验风险', '计算评分', '匹配产品', '出具结果']
const currentIdx = ref(0)
const progress = ref(0)
const stepText = ref('正在汇总您填写的数据...')

let timer: ReturnType<typeof setInterval> | null = null

pageView('assess/loading')

function startAnimation() {
  let i = 0
  timer = setInterval(() => {
    i++
    if (i >= stepTexts.length) {
      if (timer) clearInterval(timer)
      progress.value = 100
      return
    }
    currentIdx.value = i
    progress.value = Math.min(100, (i + 1) * 22)
    stepText.value = ['正在汇总您填写的数据...', '正在校验硬性风险...', '正在计算评分...', '正在匹配推荐产品...', '正在出具结果...'][i] || '正在出具结果...'
  }, 500)
}

async function submit() {
  const inputData: Record<string, unknown> = {
    ...(store.step1 as any || {}),
    ...(store.step2 as any || {}),
    // 关键修复：把企业专属的 step1B（7 个企业字段：纳税/开票/经营年限/行业等）也合并进去
    // 之前漏了导致后端评分拿不到企业数据，business 和 personal 跑出一样的结果
    ...(store.step1B as any || {}),
    ...(store.step3 as any || {}),
    ...(store.step4 as any || {}),
  }
  // 关键：把前端 label 里的中文空格（"3 万-5 万"）去成后端 SCORECARD_SEED / money.py 字典用的 key（"3万-5万"）
  // 解决前后端 label 不一致导致 income_value/INCOME_MIDPOINT 匹配不到返回 0 的 bug
  for (const k of Object.keys(inputData)) {
    const v = inputData[k]
    if (typeof v === 'string') {
      // 中文空格 U+3000 + 英文空格 U+0020
      inputData[k] = v.replace(/[\u3000\s]/g, '')
    }
  }
  const shareCode = getStorage<string>('share_code', '')
  const promoterCode = getStorage<string>('promoter_code', '')

  track({ event: 'assessment_start', page: 'assess/loading' })

  try {
    const res = await assessmentApi.submitAssessment({
      type: store.type,
      input_data: inputData,
      // v7 增量：传银行 code 触发 bank_scorecard.py 的 apply_bank_bias（10 家银行差异化评分）
      // 不传则用通用模型（1.0 权重），传了则按 BANK_FOCUS 表差异化
      bank_code: store.bankCode || undefined,
      share_code: shareCode || undefined,
      promoter_code: promoterCode || undefined,
    })

    track({ event: 'assessment_complete', page: 'assess/loading', data: { id: res.assessment_id, score: res.overall.score, level: res.overall.level } })

    // 写入历史索引（mine/history 页面读取展示）
    store.addHistory({
      id: res.assessment_id,
      report_no: res.report_no,
      type: store.type,
      bank_name: store.bankName,
      product_name: store.productName,
      score: res.overall.score,
      level: res.overall.level,
      pass_probability: res.overall.pass_probability,
      limit_min: res.overall.limit_min,
      limit_max: res.overall.limit_max,
      is_paid: !!res.is_paid,
      created_at: new Date().toISOString(),
    })

    // 等动画跑完一圈（约 600ms），再跳 9.9 付费层
    // v21 决策：取消 free/pay 二段式，submit 完成后直接弹 9.9 支付层
    setTimeout(() => {
      const targetUrl = `/pages/result/pay?id=${res.assessment_id}`
      uni.redirectTo({
        url: targetUrl,
        fail: (err) => {
          // pay 不是 tabBar 页，redirectTo 失败一般是页面栈问题或参数错误
          console.error('跳支付页失败', err)
          uni.showModal({ title: '支付页打开失败', content: '请到「我的」- 测评历史中重新进入', showCancel: false })
        },
      })
    }, 600)
  } catch (e: any) {
    // v6 修复：把"评估失败"弹窗加 retry 按钮（之前 showCancel:false 直接跳回 step5，
    // 用户不清楚失败原因，反复点"开始评估"同样失败，体验极差）
    const errMsg = (e && (e.errMsg || e.message)) || '请稍后重试'
    const isNetwork = /network|timeout|request:fail|statusCode/i.test(errMsg)
    uni.showModal({
      title: isNetwork ? '网络异常' : '评估失败',
      content: isNetwork
        ? '网络异常或服务暂不可用。\n请检查网络后点击"重试"，或稍后再试。'
        : `${errMsg}\n请截图联系客服，或点击"重试"再试一次。`,
      confirmText: '重试',
      cancelText: '返回上一步',
      success: (r) => {
        if (r.confirm) {
          // 重试：再次跑 submit（不重置动画，避免 0-100% 闪烁）
          submit()
        } else {
          uni.redirectTo({ url: '/pages/assess/step5-confirm' })
        }
      },
    })
  }
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

startAnimation()
submit()
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';

.loading-page {
  min-height: 100vh;
  background: $bg;
  display: flex;
  flex-direction: column;
}

.loading-content {
  flex: 1;
  padding: $space-5 $space-4;
  display: flex;
  flex-direction: column;
}

.loading-brand {
  text-align: center;
  margin-bottom: $space-5;
}
.loading-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.loading-title {
  font-family: $ff-serif;
  font-size: 64rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 8rpx;
  margin-top: 12rpx;
  line-height: 1.1;
}
.loading-line {
  width: 48rpx;
  height: 2rpx;
  background: $accent;
  margin: $space-3 auto 0;
}

/* 旋转环 */
.loading-ring {
  position: relative;
  width: 240rpx;
  height: 240rpx;
  margin: 0 auto $space-4;
}
.loading-ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.loading-ring-bg {
  fill: none;
  stroke: $border-light;
  stroke-width: 2;
}
.loading-ring-fill {
  fill: none;
  stroke: $primary;
  stroke-width: 2;
  stroke-linecap: butt;
  transition: stroke-dasharray 0.5s ease;
}
.loading-ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.loading-ring-num {
  font-family: $ff-serif;
  font-size: 72rpx;
  font-weight: 700;
  color: $primary;
  line-height: 1;
  font-feature-settings: "tnum";
}
.loading-ring-total {
  font-family: $ff-mono;
  font-size: $font-sm;
  color: $text-weak;
  margin-top: 4rpx;
  letter-spacing: 1rpx;
}

.loading-status {
  text-align: center;
  margin-bottom: $space-4;
}
.loading-status-text {
  font-family: $ff-serif;
  font-size: $font-lg;
  color: $primary;
  letter-spacing: 2rpx;
}

/* 步骤列表 */
.loading-steps {
  background: $card;
  border: 1rpx solid $border-light;
  padding: $space-3 $space-4;
  margin: 0 $space-3;
  border-left: 4rpx solid $primary;
}
.loading-step {
  display: flex;
  align-items: center;
  padding: 12rpx 0;
  font-size: $font-sm;
  color: $text-weak;
  font-family: $ff-base;
  letter-spacing: 0.5rpx;
  &-idx {
    font-family: $ff-mono;
    font-size: $font-sm;
    font-weight: 500;
    color: $text-weak;
    width: 64rpx;
  }
  &-name {
    flex: 1;
  }
  &-mark {
    color: $accent;
    font-weight: 700;
    margin-left: 8rpx;
  }
  &.done {
    color: $text-main;
    .loading-step-idx { color: $accent; font-weight: 700; }
  }
}

.loading-footer {
  padding: $space-3 $space-4;
  padding-bottom: calc($space-3 + env(safe-area-inset-bottom));
}
</style>
