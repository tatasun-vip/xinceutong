<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { bankApi, type Bank, type FormStep, type FormField } from '@/api/bank'
import { useAssessmentStore } from '@/store/assessment'

const route = useRoute()
const router = useRouter()
const store = useAssessmentStore()

const bankCode = route.params.bankCode as string
const bank = ref<Bank | null>(null)
const schema = ref<{ steps: FormStep[] } | null>(null)
const loading = ref(true)

const currentStep = ref(0)

onMounted(async () => {
  store.reset()
  store.setBank(bankCode)
  try {
    const [bRes, sRes] = await Promise.all([
      bankApi.detail(bankCode),
      bankApi.schema(bankCode),
    ])
    bank.value = bRes
    schema.value = sRes
  } catch (e: any) {
    ElMessage.error('加载测评表单失败：' + e.message)
  } finally {
    loading.value = false
  }
})

const step = computed<FormStep | null>(() => schema.value?.steps[currentStep.value] || null)
const totalSteps = computed(() => schema.value?.steps.length || 0)

// 当前步骤的字段值（双向绑定到 store.allInput）
const getValue = (key: string) => store.allInput[key]
const setValue = (key: string, value: unknown) => store.setField(key, value)

// 校验当前步骤
const canNext = computed(() => {
  if (!step.value) return false
  for (const f of step.value.fields) {
    if (!f.required) continue
    const v = store.allInput[f.key]
    if (v === undefined || v === null || v === '') return false
    if (f.type === 'checkbox' && v !== true) return false
  }
  return true
})

function next() {
  if (!canNext.value) {
    ElMessage.warning('请完整填写必填项')
    return
  }
  if (currentStep.value < totalSteps.value - 1) {
    currentStep.value++
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    // 最后一步：跳到 loading
    router.push('/loading')
  }
}

function prev() {
  if (currentStep.value > 0) {
    currentStep.value--
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } else {
    router.push('/banks')
  }
}

const progressPct = computed(() => {
  return Math.round(((currentStep.value + 1) / totalSteps.value) * 100)
})

// 格式化 slider 值显示
const formatSlider = (val: number, field: FormField) => {
  if (field.unit) return `${val.toLocaleString()} ${field.unit}`
  return String(val)
}
</script>

<template>
  <div class="assess" v-loading="loading">
    <div class="assess-inner container" v-if="bank && schema">
      <!-- 顶部：银行信息 + 进度 -->
      <header class="assess-head">
        <div class="assess-bank">
          <div class="assess-bank-name">{{ bank.name }}</div>
          <div class="assess-bank-sub">{{ bank.short_desc }}</div>
        </div>
        <div class="assess-progress">
          <div class="assess-progress-text">
            <span class="text-mono">STEP {{ String(currentStep + 1).padStart(2, '0') }} / {{ String(totalSteps).padStart(2, '0') }}</span>
            <span class="text-mono">{{ progressPct }}%</span>
          </div>
          <div class="assess-progress-bar">
            <div class="assess-progress-fill" :style="{ width: progressPct + '%' }"></div>
          </div>
        </div>
      </header>

      <!-- 步骤内容 -->
      <div class="assess-step" v-if="step">
        <div class="assess-step-head">
          <div class="text-eyebrow">{{ step.step_label }}</div>
          <h2 class="assess-step-title">{{ step.step_title }}</h2>
          <div class="divider-line"></div>
          <p class="assess-step-sub">{{ step.step_subtitle }}</p>
        </div>

        <div class="assess-fields">
          <div v-for="f in step.fields" :key="f.key" class="assess-field">
            <div class="assess-field-label">
              <span class="assess-field-label-text">{{ f.label }}</span>
              <span v-if="f.required" class="assess-required">*</span>
              <span v-if="f.unit && f.type === 'number'" class="assess-unit">{{ f.unit }}</span>
            </div>

            <!-- number -->
            <el-input-number
              v-if="f.type === 'number'"
              :model-value="getValue(f.key) as number"
              @update:model-value="setValue(f.key, $event)"
              :min="f.min"
              :max="f.max"
              :step="f.step || 1"
              :placeholder="`请输入${f.label}`"
              size="large"
              style="width: 240px"
            />

            <!-- text -->
            <el-input
              v-else-if="f.type === 'text'"
              :model-value="(getValue(f.key) as string) || ''"
              @update:model-value="setValue(f.key, $event)"
              :placeholder="f.placeholder || `请输入${f.label}`"
              size="large"
            />

            <!-- select -->
            <el-select
              v-else-if="f.type === 'select'"
              :model-value="getValue(f.key) as string"
              @update:model-value="setValue(f.key, $event)"
              :placeholder="`请选择${f.label}`"
              size="large"
              style="width: 100%"
            >
              <el-option v-for="o in f.options" :key="o.value" :value="o.value" :label="o.label" />
            </el-select>

            <!-- radio -->
            <el-radio-group
              v-else-if="f.type === 'radio'"
              :model-value="getValue(f.key) as string"
              @update:model-value="setValue(f.key, $event)"
              size="large"
            >
              <el-radio v-for="o in f.options" :key="o.value" :value="o.value" :label="o.label" border />
            </el-radio-group>

            <!-- slider -->
            <div v-else-if="f.type === 'slider'" class="assess-slider">
              <el-slider
                :model-value="(getValue(f.key) as number) ?? f.min ?? 0"
                @update:model-value="setValue(f.key, $event)"
                :min="f.min || 0"
                :max="f.max || 100"
                :step="f.step || 1"
                :format-tooltip="(v) => formatSlider(v as number, f)"
                show-input
                :show-input-controls="false"
                style="margin-right: 16px"
              />
            </div>

            <!-- checkbox -->
            <el-checkbox
              v-else-if="f.type === 'checkbox'"
              :model-value="(getValue(f.key) as boolean) || false"
              @update:model-value="setValue(f.key, $event)"
              size="large"
            >
              {{ f.placeholder || f.label }}
            </el-checkbox>

            <!-- fallback -->
            <el-input
              v-else
              :model-value="(getValue(f.key) as string) || ''"
              @update:model-value="setValue(f.key, $event)"
              size="large"
            />
          </div>
        </div>
      </div>

      <!-- 底部操作 -->
      <footer class="assess-foot">
        <el-button size="large" @click="prev">
          {{ currentStep === 0 ? '重新选银行' : '上一步' }}
        </el-button>
        <div class="assess-foot-tip">
          <span class="text-mono">本过程为模拟运算 · 不查征信</span>
        </div>
        <el-button type="primary" size="large" :disabled="!canNext" @click="next">
          {{ currentStep === totalSteps - 1 ? '提交测评' : '下一步' }}
          <span style="margin-left: 4px">→</span>
        </el-button>
      </footer>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.assess {
  background: $bg;
  min-height: calc(100vh - #{$header-height} - 28px);
  padding: $space-8 0 $space-12;
}

.assess-inner {
  max-width: 880px;
}

/* ====== 头部 ====== */
.assess-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: $space-8;
  padding-bottom: $space-4;
  border-bottom: 1px solid $border-light;
}

.assess-bank-name {
  font-family: $ff-serif;
  font-size: 24px;
  color: $primary;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.assess-bank-sub {
  font-size: $font-sm;
  color: $text-secondary;
  letter-spacing: 0.5px;
}

.assess-progress {
  width: 280px;
  text-align: right;
}

.assess-progress-text {
  display: flex;
  justify-content: space-between;
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.assess-progress-bar {
  height: 4px;
  background: $border-light;
  position: relative;
}

.assess-progress-fill {
  position: absolute;
  top: 0; left: 0; bottom: 0;
  background: linear-gradient(90deg, $primary 0%, $accent 100%);
  transition: width 0.3s ease;
}

/* ====== 步骤 ====== */
.assess-step {
  background: $bg-card;
  border: 1px solid $border-light;
  border-top: 3px solid $primary;
  padding: $space-8;
}

.assess-step-head {
  margin-bottom: $space-8;
  padding-bottom: $space-6;
  border-bottom: 1px solid $border-light;
  .divider-line { margin: $space-3 0; }
}

.assess-step-title {
  font-family: $ff-serif;
  font-size: 28px;
  color: $primary;
  font-weight: 600;
  letter-spacing: 1px;
  margin: $space-2 0;
}

.assess-step-sub {
  font-size: $font-sm;
  color: $text-secondary;
  letter-spacing: 0.5px;
}

/* ====== 字段 ====== */
.assess-fields {
  display: flex;
  flex-direction: column;
  gap: $space-6;
}

.assess-field {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.assess-field-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: $font-md;
  color: $text-main;
  font-weight: 500;
}

.assess-required { color: $danger; }

.assess-unit {
  font-size: $font-xs;
  color: $text-weak;
  margin-left: 4px;
}

.assess-slider {
  padding: 0 8px;
}

:deep(.el-slider__input) {
  width: 140px;
}

:deep(.el-radio.is-bordered) {
  margin-right: 12px;
  margin-bottom: 8px;
  padding: 8px 16px;
}

/* ====== 底部 ====== */
.assess-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: $space-6;
  padding: $space-4;
  background: $bg-card;
  border: 1px solid $border-light;
  border-left: 3px solid $accent;
}

.assess-foot-tip {
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 1px;
}

@media (max-width: 700px) {
  .assess-head { flex-direction: column; align-items: stretch; gap: $space-3; }
  .assess-progress { width: 100%; }
  .assess-foot { flex-wrap: wrap; }
}
</style>
