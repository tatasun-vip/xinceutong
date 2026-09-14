<template>
  <view class="assess-page">
    <ComplianceBar />
    <ProgressBar :current="3" :total="5" :titles="stepTitles" />

    <view class="assess-content">
      <!-- 01 房产 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">01</text>
          <text class="section-title">房产情况</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">无按揭房产是额度加分项</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in HOUSE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.house === opt.label"
            @select="selectOne('house', opt.label)"
          />
        </view>
      </view>

      <!-- 02 车辆 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">02</text>
          <text class="section-title">车辆价值</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">按购入价（含税）选区间</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in CAR_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.car === opt.label"
            @select="selectOne('car', opt.label)"
          />
        </view>
      </view>

      <!-- 03 存款 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">03</text>
          <text class="section-title">银行存款</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">活期 + 定期 + 理财合计</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in DEPOSIT_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.deposit === opt.label"
            @select="selectOne('deposit', opt.label)"
          />
        </view>
      </view>

      <!-- 04 保险 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">04</text>
          <text class="section-title">商业保险</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">含寿险 / 重疾 / 年金等</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in INSURANCE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.insurance === opt.label"
            @select="selectOne('insurance', opt.label)"
          />
        </view>
      </view>

      <!-- 纠错提示 -->
      <view v-if="items.length" class="validation-list">
        <view
          v-for="it in items"
          :key="it.rule_name"
          :class="['validation-item', `level-${it.level}`]"
        >
          <text :class="['validation-icon', `level-${it.level}`]">!</text>
          <text class="validation-text">{{ it.message }}</text>
        </view>
      </view>
    </view>

    <view class="assess-footer">
      <view class="btn-row btn-row-3">
        <button class="btn-block-tertiary" @tap="exitToHome" @click="exitToHome">返回首页</button>
        <button class="btn-block-secondary" @tap="goBack" @click="goBack">上一步</button>
        <button
          :class="['btn-block-primary', canNext ? '' : 'is-pending']"
          @click="onBtnTap"
          @tap="onBtnTap"
          @longpress="onBtnTap"
          @touchstart="onBtnTap"
        >{{ canNext ? '下一步' : '请补全必填项' }}</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, computed, watch } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import ProgressBar from '@/components/progress-bar/ProgressBar.vue'
import OptionCard from '@/components/option-card/OptionCard.vue'
import { useAssessmentStore } from '@/store/assessment'
import { useValidation } from '@/composables/useValidation'
import { useStepGuard } from '@/composables/useStepGuard'
import { useExitConfirm } from '@/composables/useExitConfirm'
import { pageView } from '@/utils/track'
import {
  HOUSE_OPTIONS, CAR_OPTIONS, DEPOSIT_OPTIONS, INSURANCE_OPTIONS,
} from '@/constants/assess-options'

const store = useAssessmentStore()

const { exit: exitToHome } = useExitConfirm()
const { items, runValidation } = useValidation()

useStepGuard(3)
const stepTitles = ['基础', '职业', '资产', '征信', '确认']

const form = reactive({
  house: store.step3?.house || '',
  car: store.step3?.car || '',
  deposit: store.step3?.deposit || '',
  insurance: store.step3?.insurance || '',
})

const canNext = computed(() =>
  !!form.house && !!form.car && !!form.deposit && !!form.insurance
)

pageView('assess/step3-asset')

watch(form, (v) => {
  store.setStep3(v as any)
  runValidation({
    step: 3,
    data: v as any,
    type: store.type,
    prevData: { ...(store.step1 as any || {}), ...(store.step2 as any || {}) },
  })
}, { deep: true })

function selectOne(key: keyof typeof form, label: string) {
  form[key] = label as any
}
function goBack() {
  // v4 P0: business 类型回 step1b-business，其他回 step2-career
  uni.redirectTo({
    url: store.type === 'business'
      ? '/pages/assess/step1b-business'
      : '/pages/assess/step2-career'
  })
}
function onBtnTap() {
  if (!canNext.value) { uni.showToast({ title: '请完成所有选项', icon: 'none' }); return }
  store.setStep3(form as any)              // 同步写一次（不等 watch nextTick）
  store.setStepNum(4)
  uni.redirectTo({ url: '/pages/assess/step4-credit' })
}
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';
</style>
