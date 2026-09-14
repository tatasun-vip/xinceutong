<template>
  <view class="assess-page">
    <ComplianceBar />
    <ProgressBar :current="4" :total="5" :titles="stepTitles" />

    <view class="assess-content">
      <view class="credit-tip">
        <text class="credit-tip-line">—</text>
        <text class="credit-tip-text">本步骤数据<text class="text-bold">不查征信</text>，仅用于模拟评分</text>
        <text class="credit-tip-progress" :class="{ 'is-done': filledCount === 9 }">{{ filledCount }} / 9</text>
      </view>

      <!-- 01 信用卡张数 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">01</text>
          <text class="section-title">信用卡张数</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">5 张以上属于多头授信，会扣分</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in CREDIT_CARD_COUNT_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.credit_card_count === opt.label"
            @select="selectOne('credit_card_count', opt.label)"
          />
        </view>
      </view>

      <!-- 02 信用卡使用率 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">02</text>
          <text class="section-title">信用卡使用率</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">使用率 = 已用额度 ÷ 总授信额度</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in CREDIT_CARD_USAGE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.credit_card_usage === opt.label"
            @select="selectOne('credit_card_usage', opt.label)"
          />
        </view>
      </view>

      <!-- 03 在贷笔数 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">03</text>
          <text class="section-title">在贷笔数</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">含房贷 / 车贷 / 信用贷 / 网贷等</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in LOAN_COUNT_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.loan_count === opt.label"
            @select="selectOne('loan_count', opt.label)"
          />
        </view>
      </view>

      <!-- 04 近 3 月查询 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">04</text>
          <text class="section-title">近 3 个月查询</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">包括贷款审批 / 信用卡审批 / 担保审查</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in RECENT_3M_QUERIES_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.recent_3month_queries === opt.label"
            @select="selectOne('recent_3month_queries', opt.label)"
          />
        </view>
      </view>

      <!-- 05 近 2 年逾期 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">05</text>
          <text class="section-title">近 2 年逾期次数</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">包括信用卡 / 贷款的所有逾期</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in OVERDUE_2Y_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.overdue_2year === opt.label"
            @select="selectOne('overdue_2year', opt.label)"
          />
        </view>
      </view>

      <!-- 06 当前逾期 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">06</text>
          <text class="section-title">当前是否有逾期</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">有当前逾期 = 一票否决，几乎无法通过</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in CURRENT_OVERDUE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.current_overdue === opt.label"
            @select="selectOne('current_overdue', opt.label)"
          />
        </view>
      </view>

      <!-- 07 连续 60 天+ -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">07</text>
          <text class="section-title">是否连续 60 天+ 逾期</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">连续 60 天以上逾期会被直接拒绝</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in SERIAL_OVERDUE_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.serial_overdue === opt.label"
            @select="selectOne('serial_overdue', opt.label)"
          />
        </view>
      </view>

      <!-- 08 白户 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">08</text>
          <text class="section-title">是否为白户</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">白户 = 无任何信贷记录（无信用卡无贷款）</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in WHITE_ACCOUNT_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.white_account === opt.label"
            @select="selectOne('white_account', opt.label)"
          />
        </view>
      </view>

      <!-- 09 账户状态 -->
      <view class="section">
        <view class="section-head">
          <text class="section-index">09</text>
          <text class="section-title">账户状态异常</text>
          <text class="section-required">*</text>
        </view>
        <view class="section-hint">包括次级 / 可疑 / 损失账户</view>
        <view class="section-options">
          <OptionCard
            v-for="opt in BAD_STATUS_OPTIONS"
            :key="opt.label"
            :label="opt.label"
            :desc="opt.desc"
            :selected="form.bad_status === opt.label"
            @select="selectOne('bad_status', opt.label)"
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

      <!-- ============================================================ -->
      <!-- v4 P0: 线下辅助资料（选填，不参与评分）                       -->
      <!-- 完整说明：可上传 5 类辅助资料图片，仅用于人工对接参考        -->
      <!-- 全部选填，跳过不影响评分和提交                              -->
      <!-- ============================================================ -->
      <view class="offline-docs-section">
        <view class="offline-docs-head" @tap="toggleOfflineDocs">
          <view class="offline-docs-head-l">
            <text class="offline-docs-icon">📎</text>
            <text class="offline-docs-title">线下辅助资料</text>
            <text class="offline-docs-tag">选填</text>
          </view>
          <text class="offline-docs-arrow">{{ showOfflineDocs ? '▲' : '▼' }}</text>
        </view>
        <text class="offline-docs-hint">
          可上传房本/行驶证/营业执照/纳税凭证/对公流水。人工对接时提高通过率，<text class="text-bold">不影响本次评估结果</text>
        </text>

        <view v-if="showOfflineDocs" class="offline-docs-body">
          <!-- 5 类资料 checkbox -->
          <view class="offline-docs-grid">
            <view
              v-for="opt in OFFLINE_DOC_OPTIONS"
              :key="opt.key"
              :class="['doc-chip', docsForm.docs.includes(opt.key) ? 'doc-chip-on' : '']"
              @tap="toggleDoc(opt.key)"
            >
              <text class="doc-chip-label">{{ opt.label }}</text>
              <text class="doc-chip-desc">{{ opt.desc }}</text>
            </view>
          </view>

          <!-- 已勾选资料 → 上传图片 -->
          <view v-if="docsForm.docs.length" class="offline-docs-uploads">
            <view
              v-for="key in docsForm.docs"
              :key="key"
              class="upload-item"
            >
              <view class="upload-item-head">
                <text class="upload-item-label">{{ docLabel(key) }}</text>
                <text class="upload-item-status">{{ docsForm.images[key] ? '已上传' : '未上传' }}</text>
              </view>
              <view v-if="docsForm.images[key]" class="upload-item-preview">
                <image :src="docsForm.images[key]" class="upload-item-img" mode="aspectFill" />
                <view class="upload-item-del" @tap="removeImage(key)">×</view>
              </view>
              <view v-else class="upload-item-btn" @tap="chooseImage(key)">
                <text class="upload-item-btn-text">+ 选择图片</text>
              </view>
            </view>
          </view>

          <!-- 备注 -->
          <view class="offline-docs-note">
            <text class="offline-docs-note-label">补充说明（可选）</text>
            <textarea
              v-model="docsForm.note"
              class="offline-docs-note-input"
              placeholder="如有特殊情况（资产冻结、诉讼中、刚换工作等）请简要说明，对接专员会优先处理"
              maxlength="200"
              auto-height
            />
            <text class="offline-docs-note-count">{{ docsForm.note.length }} / 200</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="!canNext && missingFields.length" class="assess-missing-hint">
      还差 {{ missingFields.length }} 项必填：{{ missingFields.join(' / ') }}
    </view>

    <view class="assess-footer">
      <view class="btn-row btn-row-3">
        <button class="btn-block-tertiary" @tap="exitToHome" @click="exitToHome">返回首页</button>
        <button class="btn-block-secondary" @tap="goBack" @click="goBack">上一步</button>
        <button
          :class="['btn-block-primary', canNext ? '' : 'is-pending']"
          :disabled="!canNext"
          @click="onBtnTap"
          @tap="onBtnTap"
        >{{ canNext ? '下一步' : '请补全必填项' }}</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, computed, watch, ref } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import ProgressBar from '@/components/progress-bar/ProgressBar.vue'
import OptionCard from '@/components/option-card/OptionCard.vue'
import { useAssessmentStore } from '@/store/assessment'
import { useValidation } from '@/composables/useValidation'
import { useStepGuard } from '@/composables/useStepGuard'
import { useExitConfirm } from '@/composables/useExitConfirm'
import { pageView } from '@/utils/track'
import {
  CREDIT_CARD_COUNT_OPTIONS, CREDIT_CARD_USAGE_OPTIONS, LOAN_COUNT_OPTIONS,
  RECENT_3M_QUERIES_OPTIONS, OVERDUE_2Y_OPTIONS, CURRENT_OVERDUE_OPTIONS,
  SERIAL_OVERDUE_OPTIONS, WHITE_ACCOUNT_OPTIONS, BAD_STATUS_OPTIONS,
  OFFLINE_DOC_OPTIONS,
} from '@/constants/assess-options'

const store = useAssessmentStore()
const { items, runValidation, hasError, clear } = useValidation()

useStepGuard(4)
const stepTitles = ['基础', '职业', '资产', '征信', '确认']
const { exit: exitToHome } = useExitConfirm()

// v6 修复：H5 微信浏览器上 @click / @tap / @touchstart 会在一次手指点击中各触发一次，
// 多次触发 onBtnTap 会导致 goNext() 内 uni.reLaunch 被反复调用、step5 页面被反复重启。
// 用 isSubmitting 锁让同一次点击只走一次提交。
let isSubmitting = false

const form = reactive({
  credit_card_count: store.step4?.credit_card_count || '',
  credit_card_usage: store.step4?.credit_card_usage || '',
  loan_count: store.step4?.loan_count || '',
  recent_3month_queries: store.step4?.recent_3month_queries || '',
  overdue_2year: store.step4?.overdue_2year || '',
  current_overdue: store.step4?.current_overdue || '',
  serial_overdue: store.step4?.serial_overdue || '',
  white_account: store.step4?.white_account || '',
  bad_status: store.step4?.bad_status || '',
})

const canNext = computed(() =>
  !!form.credit_card_count && !!form.credit_card_usage && !!form.loan_count
  && !!form.recent_3month_queries && !!form.overdue_2year
  && !!form.current_overdue && !!form.serial_overdue
  && !!form.white_account && !!form.bad_status
)

const fieldLabels: Record<keyof typeof form, string> = {
  credit_card_count: '01 信用卡张数',
  credit_card_usage: '02 信用卡使用率',
  loan_count: '03 在贷笔数',
  recent_3month_queries: '04 近3月查询',
  overdue_2year: '05 近2年逾期',
  current_overdue: '06 当前是否有逾期',
  serial_overdue: '07 连续60天+逾期',
  white_account: '08 是否为白户',
  bad_status: '09 账户状态异常',
}

const missingFields = computed<string[]>(() => {
  const out: string[] = []
  ;(Object.keys(fieldLabels) as Array<keyof typeof form>).forEach((k) => {
    if (!form[k]) out.push(fieldLabels[k])
  })
  return out
})

const filledCount = computed(() => 9 - missingFields.value.length)

pageView('assess/step4-credit')

watch(form, (v) => {
  store.setStep4(v as any)
  runValidation({
    step: 4,
    data: v as any,
    type: store.type,
    prevData: {
      ...(store.step1 as any || {}),
      ...(store.step2 as any || {}),
      ...(store.step3 as any || {}),
    },
  })
}, { deep: true })

function selectOne(key: keyof typeof form, label: string) {
  form[key] = label as any
}
function goBack() {
  clear()
  uni.redirectTo({ url: '/pages/assess/step3-asset' })
}
function onBtnTap() {
  // v6 修复：H5 微信浏览器 click 经常被吞，touchstart + setTimeout 兜底。
  // 但 touchstart 早于 click/tap，会导致 goNext 被调 3 次以上，uni.reLaunch 反复重置 step5 页面。
  // 解决：去掉 touchstart/longpress 多事件，只留 @tap + @click；并加 isSubmitting 锁防重入
  if (isSubmitting) return
  isSubmitting = true
  goNext()
}

function goNext() {
  // 二次防御：用户点完按钮到代码执行期间，form 可能被 watch 改写
  if (!canNext.value) {
    isSubmitting = false
    const tip = missingFields.value.length === 1
      ? `请填写：${missingFields.value[0]}`
      : `还差 ${missingFields.value.length} 项，请看底部提示`
    uni.showToast({ title: tip, icon: "none", duration: 2500 })
    return
  }
  // 防御性：捕捉 store 写入异常
  try {
    store.setStep4(form as any)
    store.setStep4Docs(docsForm as any)
    store.setStepNum(5)
  } catch (err) {
    console.error("[step4] store 写入失败", err)
    isSubmitting = false
    uni.showToast({ title: "数据保存失败，请重试", icon: "none", duration: 2500 })
    return
  }
  // 路由：用 reLaunch 而非 redirectTo —— reLaunch 不经过 stepGuard 守卫
  // （redirectTo 在某些版本下被 step5 守卫打回，且失败时静默）
  const target = "/pages/assess/step5-confirm"
  try {
    uni.reLaunch({
      url: target,
      success: () => { console.log("[step4] reLaunch step5 OK") },
      fail: (err) => {
        console.error("[step4] reLaunch 失败，尝试 redirectTo", err)
        uni.redirectTo({ url: target })
      },
    })
  } catch (err) {
    console.error("[step4] 路由抛出异常，强制 location 跳", err)
    if (typeof window !== "undefined") {
      window.location.href = "#" + target
    }
  }
}

// ============================================================================
// v4 P0: 线下辅助资料（选填，不参与评分）
// ============================================================================
const showOfflineDocs = ref(false)
const docsForm = reactive({
  docs:  [...(store.step4Docs?.docs  || [])] as string[],
  images: { ...(store.step4Docs?.images || {}) } as Record<string, string>,
  note:   store.step4Docs?.note || '',
})

function toggleOfflineDocs() { showOfflineDocs.value = !showOfflineDocs.value }
function toggleDoc(key: string) {
  const i = docsForm.docs.indexOf(key)
  if (i >= 0) {
    docsForm.docs.splice(i, 1)
    // 同时清掉该 key 的图片
    if (docsForm.images[key]) {
      delete docsForm.images[key]
    }
  } else {
    docsForm.docs.push(key)
  }
}
function docLabel(key: string): string {
  const it = OFFLINE_DOC_OPTIONS.find(o => o.key === key)
  return it?.label || key
}
function removeImage(key: string) {
  delete docsForm.images[key]
}
function chooseImage(key: string) {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      const path = res.tempFilePaths[0]
      if (path) {
        docsForm.images[key] = path
      }
    },
    fail: () => {
      uni.showToast({ title: '图片选择已取消', icon: 'none' })
    }
  })
}
</script>

<style lang="scss" scoped>
@import '@/utils/styles/assess.scss';

.credit-tip {
  display: flex;
  align-items: center;
  background: $primary-tint;
  margin: $space-3 $space-4 0;
  padding: 16rpx 20rpx;
  font-size: $font-sm;
  color: $primary;
  border-left: 4rpx solid $primary;
  &-line { color: $accent; margin-right: 12rpx; }
  &-text { flex: 1; line-height: 1.6; letter-spacing: 0.5rpx; }
  .text-bold { color: $primary; }
  &-progress {
    flex: none;
    margin-left: 12rpx;
    padding: 2rpx 12rpx;
    border-radius: 999px;
    background: rgba(15, 35, 64, 0.08);
    color: $primary;
    font-size: 22rpx;
    font-weight: 600;
    letter-spacing: 0.5rpx;
    &.is-done {
      background: $primary;
      color: #fff;
    }
  }
}

.assess-missing-hint {
  margin: $space-3 $space-4 0;
  padding: 12rpx 20rpx;
  border-radius: 8rpx;
  background: rgba(155, 34, 38, 0.08);
  border-left: 4rpx solid $danger;
  color: $danger;
  font-size: $font-sm;
  line-height: 1.5;
  letter-spacing: 0.3rpx;
}

// step4 专属：禁用态视觉灰显但保留点击能力（点击触发 toast 提示具体缺哪项）
.btn-block-primary.is-pending {
  background: $text-weak;
  opacity: 0.85;
}

// === v4 P0: 线下辅助资料（折叠面板）===
.offline-docs-section {
  margin: $space-4 $space-4 0;
  background: $bg-card;
  border: 1rpx solid $border-light;
  border-radius: 8rpx;
  overflow: hidden;
}
.offline-docs-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  background: rgba(15, 35, 64, 0.02);
}
.offline-docs-head-l {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.offline-docs-icon { font-size: 28rpx; }
.offline-docs-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-main;
  letter-spacing: 0.5rpx;
}
.offline-docs-tag {
  display: inline-block;
  padding: 2rpx 12rpx;
  font-size: 20rpx;
  color: $accent;
  background: rgba(201, 169, 110, 0.12);
  border-radius: 2rpx;
  letter-spacing: 0.3rpx;
}
.offline-docs-arrow {
  font-size: 22rpx;
  color: $text-weak;
}
.offline-docs-hint {
  display: block;
  padding: 0 24rpx 16rpx;
  font-size: 22rpx;
  color: $text-sub;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
  .text-bold { color: $accent; font-weight: 600; }
}
.offline-docs-body {
  padding: 0 24rpx 24rpx;
  border-top: 1rpx dashed $border-light;
}
.offline-docs-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 20rpx;
}
.doc-chip {
  flex: 0 0 calc(50% - 8rpx);
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  padding: 16rpx 20rpx;
  background: $bg-card;
  border: 1rpx solid $border-light;
  border-radius: 6rpx;
  transition: all 0.15s ease;

  &-on {
    background: rgba(201, 169, 110, 0.10);
    border-color: $accent;
    .doc-chip-label { color: $accent; }
  }
}
.doc-chip-label {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-main;
  letter-spacing: 0.5rpx;
}
.doc-chip-desc {
  font-size: 20rpx;
  color: $text-weak;
  line-height: 1.4;
  letter-spacing: 0.2rpx;
}
.offline-docs-uploads {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 24rpx;
}
.upload-item {
  background: $bg-page;
  border-radius: 6rpx;
  padding: 16rpx;
}
.upload-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.upload-item-label {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-main;
}
.upload-item-status {
  font-size: 20rpx;
  color: $text-weak;
}
.upload-item-preview {
  position: relative;
  width: 200rpx;
  height: 200rpx;
}
.upload-item-img {
  width: 200rpx;
  height: 200rpx;
  border-radius: 4rpx;
  object-fit: cover;
}
.upload-item-del {
  position: absolute;
  top: -16rpx;
  right: -16rpx;
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #d9534f;
  color: #fff;
  border-radius: 50%;
  font-size: 28rpx;
  line-height: 1;
  font-weight: 600;
}
.upload-item-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 200rpx;
  height: 80rpx;
  background: $bg-card;
  border: 1rpx dashed $border-base;
  border-radius: 4rpx;
}
.upload-item-btn-text {
  font-size: 22rpx;
  color: $text-sub;
  letter-spacing: 0.5rpx;
}
.offline-docs-note {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-top: 24rpx;
  padding: 16rpx;
  background: $bg-page;
  border-radius: 6rpx;
}
.offline-docs-note-label {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-main;
}
.offline-docs-note-input {
  width: 100%;
  min-height: 100rpx;
  padding: 12rpx;
  font-size: 24rpx;
  color: $text-main;
  background: $bg-card;
  border-radius: 4rpx;
  line-height: 1.6;
  box-sizing: border-box;
}
.offline-docs-note-count {
  align-self: flex-end;
  font-size: 20rpx;
  color: $text-weak;
}
</style>
