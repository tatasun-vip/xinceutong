<template>
  <view class="assess-page">
    <ComplianceBar />
    <ProgressBar :current="2" :total="5" :titles="stepTitles" />

    <view class="assess-content">
      <!-- 01 单位类型 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">01</text>
          <text class="section-title">单位类型</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">优质单位 = 高额度低利率</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in COMPANY_TYPE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.company_type === opt.label"
            @select="selectOne('company_type', opt.label)"
          />
        </view>
      </view>

      <!-- 02 工作年限 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">02</text>
          <text class="section-title">工作年限</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">5 年以上评分最高</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in WORK_YEARS_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.work_years === opt.label"
            @select="selectOne('work_years', opt.label)"
          />
        </view>
      </view>

      <!-- 03 社保缴存 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">03</text>
          <text class="section-title">社保缴存</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">连续缴存时间越长，评分越高</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in SOCIAL_SECURITY_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.social_security === opt.label"
            @select="selectOne('social_security', opt.label)"
          />
        </view>
      </view>

      <!-- 04 公积金 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">04</text>
          <text class="section-title">公积金基数</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">高基数是优质客群的重要标志</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in HOUSING_FUND_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.housing_fund === opt.label"
            @select="selectOne('housing_fund', opt.label)"
          />
        </view>
      </view>

      <!-- 05 工资代发 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">05</text>
          <text class="section-title">工资代发</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">银行代发工资可显著提升评分</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in PAYROLL_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.payroll === opt.label"
            @select="selectOne('payroll', opt.label)"
          />
        </view>
      </view>

      <!-- 06 月收入 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">06</text>
          <text class="section-title">月收入区间</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">含税前工资 + 奖金 + 副业等综合收入</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in MONTHLY_INCOME_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.monthly_income === opt.label"
            @select="selectOne('monthly_income', opt.label)"
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
  COMPANY_TYPE_OPTIONS, WORK_YEARS_OPTIONS, SOCIAL_SECURITY_OPTIONS,
  HOUSING_FUND_OPTIONS, PAYROLL_OPTIONS, MONTHLY_INCOME_OPTIONS,
} from '@/constants/assess-options'

const store = useAssessmentStore()

const { exit: exitToHome } = useExitConfirm()
const { items, runValidation } = useValidation()

useStepGuard(2)
const stepTitles = ['基础', '职业', '资产', '征信', '确认']

const form = reactive({
  company_type: store.step2?.company_type || '',
  work_years: store.step2?.work_years || '',
  social_security: store.step2?.social_security || '',
  housing_fund: store.step2?.housing_fund || '',
  payroll: store.step2?.payroll || '',
  monthly_income: store.step2?.monthly_income || '',
})

const canNext = computed(() =>
  !!form.company_type && !!form.work_years && !!form.social_security
  && !!form.housing_fund && !!form.payroll && !!form.monthly_income
)

pageView('assess/step2-career')

watch(form, (v) => {
  store.setStep2(v as any)
  runValidation({
    step: 2,
    data: v as any,
    type: store.type,
    prevData: store.step1 as any,
  })
}, { deep: true })

function selectOne(key: keyof typeof form, label: string) {
  form[key] = label as any
}
function goBack() {
  uni.redirectTo({ url: '/pages/assess/step1-basic' })
}
function onBtnTap() {
  if (!canNext.value) { uni.showToast({ title: '请完成所有选项', icon: 'none' }); return }
  store.setStep2(form as any)              // 同步写一次（不等 watch nextTick）
  store.setStepNum(store.type === 'business' ? 3 : 3)  // step1B 总在 step2 之后
  // v4 P0: business 类型插入 step1b-business（7 个企业变量）
  uni.redirectTo({
    url: store.type === 'business'
      ? '/pages/assess/step1b-business'
      : '/pages/assess/step3-asset'
  })
}
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';
</style>
