<template>
  <view class="assess-page">
    <ComplianceBar />
    <ProgressBar :current="3" :total="5" :titles="stepTitles" />

    <view class="assess-content">
      <view class="biz-banner">
        <text class="biz-banner-title">企业信息</text>
        <text class="biz-banner-sub">7 项核心指标 · 直接影响「纳税贷/开票贷」额度 · 不影响个人评分</text>
      </view>

      <!-- 01 纳税等级 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">01</text>
          <text class="section-title">纳税信用等级</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">A/B 级为优质纳税户</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in TAX_GRADE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.tax_grade === opt.label"
            @select="selectOne('tax_grade', opt.label)"
          />
        </view>
      </view>

      <!-- 02 年纳税额 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">02</text>
          <text class="section-title">年纳税额</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">增值税 + 所得税合计</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in ANNUAL_TAX_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.annual_tax === opt.label"
            @select="selectOne('annual_tax', opt.label)"
          />
        </view>
      </view>

      <!-- 03 纳税连续性 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">03</text>
          <text class="section-title">纳税连续性</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-options">
          <OptionCard
            v-for="opt in TAX_CONTINUITY_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.tax_continuity === opt.label"
            @select="selectOne('tax_continuity', opt.label)"
          />
        </view>
      </view>

      <!-- 04 经营年限 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">04</text>
          <text class="section-title">企业经营年限</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-options">
          <OptionCard
            v-for="opt in BUSINESS_YEARS_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.business_years === opt.label"
            @select="selectOne('business_years', opt.label)"
          />
        </view>
      </view>

      <!-- 05 年开票额 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">05</text>
          <text class="section-title">年开票额</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">近 12 个月累计开票金额</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in ANNUAL_INVOICE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.annual_invoice === opt.label"
            @select="selectOne('annual_invoice', opt.label)"
          />
        </view>
      </view>

      <!-- 06 开票连续性 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">06</text>
          <text class="section-title">开票连续性</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-options">
          <OptionCard
            v-for="opt in INVOICE_CONTINUITY_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.invoice_continuity === opt.label"
            @select="selectOne('invoice_continuity', opt.label)"
          />
        </view>
      </view>

      <!-- 07 行业 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">07</text>
          <text class="section-title">所属行业</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">科技/互联网 + 制造业加分；限制类行业降分</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in INDUSTRY_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.industry === opt.label"
            @select="selectOne('industry', opt.label)"
          />
        </view>
      </view>

      <!-- ============ v5 P0 新增：8 个企业专属变量 ============ -->

      <view class="biz-divider">
        <text class="biz-divider-text">— 法人画像（影响 30% 评分）—</text>
      </view>

      <!-- 08 组织形式 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">08</text>
          <text class="section-title">企业组织形式</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">有限公司最优；个体户/个人独资=无限责任评分较低</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in LEGAL_FORM_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.legal_form === opt.label"
            @select="selectOne('legal_form', opt.label)"
          />
        </view>
      </view>

      <!-- 09 法人持股比例 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">09</text>
          <text class="section-title">法人持股比例</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">持股比例越高，还款意愿越强</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in LEGAL_HOLDING_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.legal_holding === opt.label"
            @select="selectOne('legal_holding', opt.label)"
          />
        </view>
      </view>

      <view class="biz-divider">
        <text class="biz-divider-text">— 企业画像（影响 40% 评分）—</text>
      </view>

      <!-- 10 参保人数 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">10</text>
          <text class="section-title">企业参保人数</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">0 参保=空壳企业高风险</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in EMPLOYEE_COUNT_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.employee_count === opt.label"
            @select="selectOne('employee_count', opt.label)"
          />
        </view>
      </view>

      <!-- 11 对公账户日均余额 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">11</text>
          <text class="section-title">对公账户日均余额</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">还款能力核心指标</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in BIZ_BALANCE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.biz_balance === opt.label"
            @select="selectOne('biz_balance', opt.label)"
          />
        </view>
      </view>

      <!-- 12 企业现有贷款笔数 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">12</text>
          <text class="section-title">对公贷款笔数</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">对公多头借贷=资金紧张信号</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in BIZ_LOAN_COUNT_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.biz_loan_count === opt.label"
            @select="selectOne('biz_loan_count', opt.label)"
          />
        </view>
      </view>

      <!-- 13 近 2 年对公逾期（命中 3+ 即一票否决） -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">13</text>
          <text class="section-title">近 2 年对公逾期</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint section-hint-warn">⚠ 3 次以上=严重逾期，将被一票否决</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in BIZ_OVERDUE_2Y_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.biz_overdue_2y === opt.label"
            @select="selectOne('biz_overdue_2y', opt.label)"
          />
        </view>
      </view>

      <!-- 14 近 3 月对公查询 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">14</text>
          <text class="section-title">近 3 月对公征信查询</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">查询过多=频繁申贷被拒</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in BIZ_QUERY_3M_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.biz_query_3m === opt.label"
            @select="selectOne('biz_query_3m', opt.label)"
          />
        </view>
      </view>

      <view class="biz-divider">
        <text class="biz-divider-text">— 合规风险（影响 20% 评分；命中即一票否决）—</text>
      </view>

      <!-- 15 合规风险自查（任一异常即拒贷） -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">15</text>
          <text class="section-title">合规风险自查</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint section-hint-warn">⚠ 如实选择。命中任一异常项将直接判定为 D/E 级，建议先解决再申请</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in COMPLIANCE_RISK_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.compliance_risk === opt.label"
            @select="selectOne('compliance_risk', opt.label)"
          />
        </view>
      </view>

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
      <view class="btn-row">
        <button class="btn-block-secondary" @tap="goBack">上一步</button>
        <button
          :class="['btn-block-primary', canNext ? '' : 'disabled']"
          :disabled="!canNext"
          @tap="goNext"
        >下一步</button>
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
import { pageView } from '@/utils/track'
import {
  TAX_GRADE_OPTIONS, ANNUAL_TAX_OPTIONS, TAX_CONTINUITY_OPTIONS,
  BUSINESS_YEARS_OPTIONS, ANNUAL_INVOICE_OPTIONS, INVOICE_CONTINUITY_OPTIONS,
  INDUSTRY_OPTIONS,
  // v5 P0 新增 8 个企业专属变量选项
  LEGAL_FORM_OPTIONS, LEGAL_HOLDING_OPTIONS,
  EMPLOYEE_COUNT_OPTIONS, BIZ_BALANCE_OPTIONS,
  BIZ_LOAN_COUNT_OPTIONS, BIZ_OVERDUE_2Y_OPTIONS, BIZ_QUERY_3M_OPTIONS,
  COMPLIANCE_RISK_OPTIONS,
} from '@/constants/assess-options'

const store = useAssessmentStore()
const { items, runValidation } = useValidation()

// step1b 实际位于"第 3 步"位置（step1 基础、step2 职业、step1B 企业、step3 资产、step4 征信）
useStepGuard(3)
const stepTitles = ['基础', '职业', '企业', '资产', '征信']

const form = reactive({
  tax_grade:        store.step1B?.tax_grade        || '',
  annual_tax:       store.step1B?.annual_tax       || '',
  tax_continuity:   store.step1B?.tax_continuity   || '',
  business_years:   store.step1B?.business_years   || '',
  annual_invoice:   store.step1B?.annual_invoice   || '',
  invoice_continuity: store.step1B?.invoice_continuity || '',
  industry:         store.step1B?.industry         || '',
  // v5 P0 新增 8 字段
  legal_form:       store.step1B?.legal_form       || '',
  legal_holding:    store.step1B?.legal_holding    || '',
  employee_count:   store.step1B?.employee_count   || '',
  biz_balance:      store.step1B?.biz_balance      || '',
  biz_loan_count:   store.step1B?.biz_loan_count   || '',
  biz_overdue_2y:   store.step1B?.biz_overdue_2y   || '',
  biz_query_3m:     store.step1B?.biz_query_3m     || '',
  compliance_risk:  store.step1B?.compliance_risk  || '',
})

const canNext = computed(() =>
  // v4 7 字段
  !!form.tax_grade && !!form.annual_tax && !!form.tax_continuity
  && !!form.business_years && !!form.annual_invoice && !!form.invoice_continuity
  && !!form.industry
  // v5 8 字段
  && !!form.legal_form && !!form.legal_holding
  && !!form.employee_count && !!form.biz_balance
  && !!form.biz_loan_count && !!form.biz_overdue_2y
  && !!form.biz_query_3m && !!form.compliance_risk
)

pageView('assess/step1b-business')

watch(form, (v) => {
  store.setStep1B(v as any)
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
  uni.redirectTo({ url: '/pages/assess/step2-career' })
}
function goNext() {
  if (!canNext.value) { uni.showToast({ title: '请完成所有选项', icon: 'none' }); return }
  store.setStep1B(form as any)
  store.setStepNum(4)
  uni.redirectTo({ url: '/pages/assess/step3-asset' })
}
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';
.biz-banner {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  margin: 0 0 32rpx;
  padding: 20rpx 24rpx;
  background: linear-gradient(135deg, rgba(201, 169, 110, 0.10) 0%, rgba(201, 169, 110, 0.04) 100%);
  border-left: 4rpx solid $accent;
  border-radius: 4rpx;
}
.biz-banner-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-main;
  letter-spacing: 0.5rpx;
}
.biz-banner-sub {
  font-size: 22rpx;
  color: $text-sub;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
}

/* v5 P0: 4 维度分组分隔线 */
.biz-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 36rpx 0 12rpx;
  padding: 12rpx 0;
  position: relative;
}
.biz-divider::before,
.biz-divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 80rpx;
  height: 1rpx;
  background: linear-gradient(to right, transparent, $accent, transparent);
}
.biz-divider::before { left: 25%; }
.biz-divider::after  { right: 25%; }
.biz-divider-text {
  font-size: 22rpx;
  color: $accent;
  letter-spacing: 1rpx;
  padding: 0 16rpx;
  font-weight: 600;
}

/* v5 P0: 警告类 hint（逾期/合规风险） */
.section-hint-warn {
  color: #C0392B !important;
  font-weight: 500;
}
</style>
