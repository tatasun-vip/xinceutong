<template>
  <view class="assess-page">
    <ComplianceBar />
    <ProgressBar :current="1" :total="5" :titles="stepTitles" />

    <view class="assess-content">
      <!-- 01 年龄段 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">01</text>
          <text class="section-title">年龄段</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">22-30 岁与 31-40 岁为黄金客群，评分最高</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in AGE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.age === opt.label"
            @select="selectOne('age', opt.label)"
          />
        </view>
      </view>

      <!-- 02 学历 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">02</text>
          <text class="section-title">学历</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">学历越高，评分越高</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in EDUCATION_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.education === opt.label"
            @select="selectOne('education', opt.label)"
          />
        </view>
      </view>

      <!-- 03 婚姻 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">03</text>
          <text class="section-title">婚姻状况</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">已婚有子女家庭稳定性最好</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in MARRIAGE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.marriage === opt.label"
            @select="selectOne('marriage', opt.label)"
          />
        </view>
      </view>

      <!-- 04 城市 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">04</text>
          <text class="section-title">城市等级</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">按常住地选择（影响当地分行的产品匹配）</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in CITY_TIER_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.city_tier === opt.label"
            @select="selectOne('city_tier', opt.label)"
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
import { onLoad } from '@dcloudio/uni-app'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import ProgressBar from '@/components/progress-bar/ProgressBar.vue'
import OptionCard from '@/components/option-card/OptionCard.vue'
import { useAssessmentStore } from '@/store/assessment'
import { useValidation } from '@/composables/useValidation'
import { useExitConfirm } from '@/composables/useExitConfirm'
import { pageView } from '@/utils/track'
import {
  AGE_OPTIONS, EDUCATION_OPTIONS, MARRIAGE_OPTIONS, CITY_TIER_OPTIONS,
} from '@/constants/assess-options'

const store = useAssessmentStore()

const { exit: exitToHome } = useExitConfirm()
const { items, runValidation } = useValidation()

const stepTitles = ['基础', '职业', '资产', '征信', '确认']

const form = reactive({
  age: store.step1?.age || '',
  education: store.step1?.education || '',
  marriage: store.step1?.marriage || '',
  city_tier: store.step1?.city_tier || '',
})

const canNext = computed(
  () => !!form.age && !!form.education && !!form.marriage && !!form.city_tier
)

onLoad(() => {
  pageView('assess/step1-basic')
})

watch(form, (v) => {
  store.setStep1(v as any)
  runValidation({
    step: 1,
    data: v as any,
    type: store.type,
  })
}, { deep: true })

function selectOne(key: keyof typeof form, label: string) {
  form[key] = label as any
}

function goBack() {
  uni.navigateBack()
}

function onBtnTap() {
  if (!canNext.value) {
    uni.showToast({ title: '请完成所有选项', icon: 'none' })
    return
  }
  store.setStep1(form as any)              // 同步写一次（不等 watch nextTick）
  store.setStepNum(2)
  uni.redirectTo({ url: '/pages/assess/step2-career' })
}
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';
</style>
