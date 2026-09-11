<script setup lang="ts">
import { onMounted, ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { assessmentApi } from '@/api/assessment'
import { useAssessmentStore } from '@/store/assessment'

const router = useRouter()
const store = useAssessmentStore()

const steps = ['汇总数据', '校验风险', '计算评分', '匹配产品', '出具结果']
const current = ref(0)
const progress = ref(20)
const statusText = ref(steps[0])
let timer: ReturnType<typeof setInterval> | null = null

function startAnimation() {
  timer = setInterval(() => {
    current.value++
    if (current.value >= steps.length) {
      if (timer) clearInterval(timer)
      progress.value = 100
      return
    }
    progress.value = (current.value + 1) * 20
    statusText.value = steps[current.value]
  }, 600)
}

async function submit() {
  try {
    const res = await assessmentApi.submit({
      type: 'personal',
      input_data: { ...store.allInput },
      bank_code: store.bankCode,
    })
    setTimeout(() => {
      router.replace(`/result/${res.assessment_id}`)
    }, 400)
  } catch (e: any) {
    ElMessage.error('评估失败：' + e.message)
    setTimeout(() => router.replace('/banks'), 1500)
  }
}

onMounted(() => {
  startAnimation()
  submit()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="ld">
    <div class="ld-inner">
      <div class="ld-brand">
        <div class="text-eyebrow">CREDIT ASSESSMENT</div>
        <h1 class="ld-title">信测通</h1>
        <div class="divider-line"></div>
      </div>

      <div class="ld-ring">
        <svg class="ld-ring-svg" viewBox="0 0 100 100">
          <circle class="ld-ring-bg" cx="50" cy="50" r="42" />
          <circle
            class="ld-ring-fill"
            cx="50" cy="50" r="42"
            :stroke-dasharray="`${progress * 2.64} 264`"
          />
        </svg>
        <div class="ld-ring-center">
          <div class="ld-ring-num text-num">{{ String(current + 1).padStart(2, '0') }}</div>
          <div class="ld-ring-total text-mono">/ {{ String(steps.length).padStart(2, '0') }}</div>
        </div>
      </div>

      <div class="ld-status">{{ statusText }}</div>

      <div class="ld-steps">
        <div
          v-for="(s, idx) in steps"
          :key="s"
          :class="['ld-step', idx <= current ? 'done' : '']"
        >
          <span class="ld-step-idx text-mono">{{ String(idx + 1).padStart(2, '0') }}</span>
          <span class="ld-step-name">{{ s }}</span>
          <span v-if="idx < current" class="ld-step-mark">·</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ld {
  min-height: calc(100vh - #{$header-height} - 28px);
  background: $bg;
  padding: $space-20 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ld-inner {
  max-width: 600px;
  width: 100%;
  text-align: center;
  padding: 0 $content-padding;
}

.ld-brand {
  margin-bottom: $space-8;
  .divider-line { margin: $space-3 auto; }
}

.ld-title {
  font-family: $ff-serif;
  font-size: 56px;
  color: $primary;
  font-weight: 700;
  letter-spacing: 6px;
  margin: $space-3 0;
}

/* ===== 旋转环 ===== */
.ld-ring {
  position: relative;
  width: 240px;
  height: 240px;
  margin: 0 auto $space-6;
}

.ld-ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ld-ring-bg {
  fill: none;
  stroke: $border-light;
  stroke-width: 2;
}

.ld-ring-fill {
  fill: none;
  stroke: $primary;
  stroke-width: 2;
  stroke-linecap: butt;
  transition: stroke-dasharray 0.5s ease;
}

.ld-ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.ld-ring-num {
  font-family: $ff-serif;
  font-size: 72px;
  color: $primary;
  font-weight: 700;
  line-height: 1;
}

.ld-ring-total {
  font-size: $font-sm;
  color: $text-weak;
  margin-top: 4px;
  letter-spacing: 1px;
}

.ld-status {
  font-family: $ff-serif;
  font-size: $font-xl;
  color: $primary;
  letter-spacing: 2px;
  margin-bottom: $space-8;
}

.ld-steps {
  background: $bg-card;
  border: 1px solid $border-light;
  border-left: 3px solid $primary;
  padding: $space-4 $space-6;
  text-align: left;
}

.ld-step {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: $font-sm;
  color: $text-weak;
  letter-spacing: 0.5px;
}

.ld-step-idx {
  width: 50px;
  font-weight: 500;
  color: $text-weak;
}

.ld-step-name { flex: 1; }

.ld-step-mark {
  color: $accent;
  font-weight: 700;
  margin-left: 8px;
}

.ld-step.done {
  color: $text-main;
  .ld-step-idx { color: $accent; font-weight: 700; }
}
</style>
