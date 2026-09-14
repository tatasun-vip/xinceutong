<template>
  <view class="assess-page">
    <ComplianceBar />
    <ProgressBar :current="progressTotal" :total="progressTotal" :titles="stepTitles" />

    <view class="assess-content">
      <view class="confirm-tip">
        <text class="confirm-tip-line">—</text>
        <view class="confirm-tip-text">
          请确认以下信息无误，确认后系统将基于模拟评分卡为您出具结果
        </view>
      </view>

      <!-- 测评目标（银行 + 产品） -->
      <view v-if="store.bankName || store.productName" class="confirm-target">
        <text class="confirm-target-label">本次测评目标</text>
        <text class="confirm-target-value">
          <text v-if="store.bankName">{{ store.bankName }}</text>
          <text v-if="store.bankName && store.productName"> · </text>
          <text v-if="store.productName">{{ store.productName }}</text>
        </text>
        <text class="confirm-target-edit" @tap="goReselect">重选</text>
      </view>

      <!-- 01 基础信息 -->
      <view class="confirm-section">
        <view class="confirm-head">
          <text class="confirm-index">01</text>
          <text class="confirm-name">基础信息</text>
          <text class="confirm-edit" @tap="goEdit(1)">修改</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">年龄</text>
          <text class="confirm-val">{{ store.step1?.age || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">学历</text>
          <text class="confirm-val">{{ store.step1?.education || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">婚姻</text>
          <text class="confirm-val">{{ store.step1?.marriage || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">城市</text>
          <text class="confirm-val">{{ store.step1?.city_tier || '-' }}</text>
        </view>
      </view>

      <!-- 02 职业 / 收入 -->
      <view class="confirm-section">
        <view class="confirm-head">
          <text class="confirm-index">02</text>
          <text class="confirm-name">职业 / 收入</text>
          <text class="confirm-edit" @tap="goEdit(2)">修改</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">单位类型</text>
          <text class="confirm-val">{{ store.step2?.company_type || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">工作年限</text>
          <text class="confirm-val">{{ store.step2?.work_years || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">社保缴存</text>
          <text class="confirm-val">{{ store.step2?.social_security || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">公积金基数</text>
          <text class="confirm-val">{{ store.step2?.housing_fund || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">工资代发</text>
          <text class="confirm-val">{{ store.step2?.payroll || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">月收入</text>
          <text class="confirm-val">{{ store.step2?.monthly_income || '-' }}</text>
        </view>
      </view>

      <!-- 02B 企业信息（仅 business 时显示，位于 step2 之后、step3 资产之前） -->
      <view v-if="store.step1B" class="confirm-section confirm-section-biz">
        <view class="confirm-head">
          <text class="confirm-index">02B</text>
          <text class="confirm-name">企业信息</text>
          <text class="confirm-edit" @tap="goEditBiz">修改</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">纳税信用等级</text>
          <text class="confirm-val">{{ store.step1B?.tax_grade || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">年纳税额</text>
          <text class="confirm-val">{{ store.step1B?.annual_tax || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">纳税连续性</text>
          <text class="confirm-val">{{ store.step1B?.tax_continuity || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">经营年限</text>
          <text class="confirm-val">{{ store.step1B?.business_years || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">年开票额</text>
          <text class="confirm-val">{{ store.step1B?.annual_invoice || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">开票连续性</text>
          <text class="confirm-val">{{ store.step1B?.invoice_continuity || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">所属行业</text>
          <text class="confirm-val">{{ store.step1B?.industry || '-' }}</text>
        </view>
        <!-- ============ v5 P0 新增：8 个企业专属变量确认行 ============ -->
        <view class="confirm-row">
          <text class="confirm-label">组织形式</text>
          <text class="confirm-val">{{ store.step1B?.legal_form || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">法人持股</text>
          <text class="confirm-val">{{ store.step1B?.legal_holding || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">参保人数</text>
          <text class="confirm-val">{{ store.step1B?.employee_count || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">对公日均余额</text>
          <text class="confirm-val">{{ store.step1B?.biz_balance || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">对公贷款笔数</text>
          <text class="confirm-val">{{ store.step1B?.biz_loan_count || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">对公近 2 年逾期</text>
          <text class="confirm-val">{{ store.step1B?.biz_overdue_2y || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">对公近 3 月查询</text>
          <text class="confirm-val">{{ store.step1B?.biz_query_3m || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">合规风险</text>
          <text class="confirm-val">{{ store.step1B?.compliance_risk || '-' }}</text>
        </view>
      </view>

      <!-- 03 资产 -->
      <view class="confirm-section">
        <view class="confirm-head">
          <text class="confirm-index">{{ store.step1B ? '03' : '03' }}</text>
          <text class="confirm-name">资产</text>
          <text class="confirm-edit" @tap="goEdit(3)">修改</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">房产</text>
          <text class="confirm-val">{{ store.step3?.house || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">车辆</text>
          <text class="confirm-val">{{ store.step3?.car || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">存款</text>
          <text class="confirm-val">{{ store.step3?.deposit || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">商业保险</text>
          <text class="confirm-val">{{ store.step3?.insurance || '-' }}</text>
        </view>
      </view>

      <!-- 04 征信 -->
      <view class="confirm-section">
        <view class="confirm-head">
          <text class="confirm-index">04</text>
          <text class="confirm-name">征信</text>
          <text class="confirm-edit" @tap="goEdit(4)">修改</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">信用卡数</text>
          <text class="confirm-val">{{ store.step4?.credit_card_count || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">使用率</text>
          <text class="confirm-val">{{ store.step4?.credit_card_usage || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">在贷笔数</text>
          <text class="confirm-val">{{ store.step4?.loan_count || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">近 3 月查询</text>
          <text class="confirm-val">{{ store.step4?.recent_3month_queries || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">近 2 年逾期</text>
          <text class="confirm-val">{{ store.step4?.overdue_2year || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">当前逾期</text>
          <text class="confirm-val">{{ store.step4?.current_overdue || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">连续 60 天+</text>
          <text class="confirm-val">{{ store.step4?.serial_overdue || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">白户</text>
          <text class="confirm-val">{{ store.step4?.white_account || '-' }}</text>
        </view>
        <view class="confirm-row">
          <text class="confirm-label">账户状态</text>
          <text class="confirm-val">{{ store.step4?.bad_status || '-' }}</text>
        </view>
      </view>

      <view class="disclaimer-final">
        <text class="text-disclaimer">
          点击"开始评估"即表示您同意以上信息用于本次模拟评分。<text class="text-bold">不查征信、不上报金融机构、不构成贷款承诺</text>。
        </text>
      </view>
    </view>

    <view class="assess-footer">
      <view class="btn-row btn-row-3">
        <button class="btn-block-tertiary" @tap="exitToHome" @click="exitToHome">返回首页</button>
        <button class="btn-block-secondary" @tap="goBack" @click="goBack">上一步</button>
        <button
          class="btn-block-primary btn-accent"
          :disabled="isSubmitting"
          @click="onSubmitTap"
          @tap="onSubmitTap"
        >{{ isSubmitting ? '提交中...' : '开始评估' }}</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import ProgressBar from '@/components/progress-bar/ProgressBar.vue'
import { useAssessmentStore } from '@/store/assessment'
import { useStepGuard } from '@/composables/useStepGuard'
import { useExitConfirm } from '@/composables/useExitConfirm'
import { pageView } from '@/utils/track'

const store = useAssessmentStore()

const { exit: exitToHome } = useExitConfirm()

useStepGuard(5)

// 关键修复：business 时 5 步 + 确认页（6 段），personal 时 4 步 + 确认页（5 段）
// stepTitles 列表中"确认"始终是最后一段（current 高亮位置）
const isBusiness = computed(() => store.type === 'business')
const progressTotal = computed(() => isBusiness.value ? 6 : 5)
const stepTitles = computed(() => isBusiness.value
  ? ['基础', '职业', '企业', '资产', '征信', '确认']
  : ['基础', '职业', '资产', '征信', '确认']
)

pageView('assess/step5-confirm')

// v6 修复：H5 微信浏览器上"开始评估"按钮同时绑了 4 个事件（@click + @tap + @longpress + @touchstart），
// 一次手指点击会触发 3-4 次 onSubmitTap，uni.redirectTo 被反复调用，loading 页面栈被反复重置。
// 用 isSubmitting 锁让同一次点击只提交一次。
let isSubmitting = false

function goBack() {
  uni.redirectTo({ url: '/pages/assess/step4-credit' })
}
function goReselect() {
  uni.redirectTo({ url: '/pages/assess/select-bank' })
}

function goEdit(step: number) {
  const map: Record<number, string> = {
    1: '/pages/assess/step1-basic',
    2: '/pages/assess/step2-career',
    3: '/pages/assess/step3-asset',
    4: '/pages/assess/step4-credit',
  }
  uni.redirectTo({ url: map[step] })
}

function goEditBiz() {
  // 关键修复：让 business 用户在确认页能跳回企业信息页修改
  uni.redirectTo({ url: '/pages/assess/step1b-business' })
}

function onSubmitTap() {
  if (isSubmitting) return
  isSubmitting = true
  uni.redirectTo({ url: '/pages/assess/loading' })
}
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';

.confirm-tip {
  display: flex;
  align-items: center;
  background: $accent-light;
  margin: $space-3 0;
  padding: 16rpx 20rpx;
  font-size: $font-sm;
  color: $accent-dark;
  border-left: 4rpx solid $accent;
  &-line { color: $accent-dark; margin-right: 12rpx; flex-shrink: 0; font-size: $font-md; }
  &-text { flex: 1; line-height: 1.6; letter-spacing: 0.5rpx; }
}

.confirm-section {
  background: $card;
  border: 1rpx solid $border-light;
  margin: 0 0 $space-3;
  padding: $space-3 $space-3;
  border-left: 4rpx solid $primary;
}
.confirm-head {
  display: flex;
  align-items: center;
  margin-bottom: $space-2;
  padding-bottom: $space-2;
  border-bottom: 1rpx solid $border-light;
}
.confirm-index {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 600;
  color: $accent;
  margin-right: $space-2;
  letter-spacing: 1rpx;
}
.confirm-name {
  flex: 1;
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
}
.confirm-edit {
  font-size: $font-sm;
  color: $text-sub;
  letter-spacing: 1rpx;
  border-bottom: 1rpx solid $text-sub;
  padding-bottom: 2rpx;
}
.confirm-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 10rpx 0;
  font-size: $font-sm;
  border-bottom: 1rpx dashed $border-light;
  &:last-child { border-bottom: none; }
}
.confirm-label { color: $text-sub; letter-spacing: 0.5rpx; }
.confirm-val {
  color: $text-main;
  font-weight: 500;
  font-family: $ff-base;
  text-align: right;
}

.disclaimer-final {
  margin: $space-3 0;
  padding: $space-3;
  background: $primary-tint;
  border-left: 4rpx solid $primary;
  .text-bold { color: $primary; }
}

// 测评目标
.confirm-target {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin: 0 0 $space-3;
  padding: $space-3;
  background: $accent-light;
  border-left: 4rpx solid $accent;
  &-label {
    font-size: $font-xs;
    color: $text-sub;
    letter-spacing: 0.5rpx;
  }
  &-value {
    flex: 1;
    font-family: $ff-serif;
    font-size: $font-md;
    font-weight: 600;
    color: $primary;
    letter-spacing: 1rpx;
  }
  &-edit {
    font-size: $font-xs;
    color: $accent-dark;
    border-bottom: 1rpx solid $accent-dark;
    padding-bottom: 2rpx;
    letter-spacing: 1rpx;
  }
}
</style>
