<template>
  <view class="methodology">
    <ComplianceBar />

    <!-- 顶部标题 -->
    <view class="mt-hero">
      <text class="mt-eyebrow">METHODOLOGY</text>
      <text class="mt-title">我们的模型是怎么来的</text>
    </view>

    <!-- 第一段：评分逻辑不是凭空设计 -->
    <view class="mt-section">
      <text class="mt-section-title">评分逻辑，不是凭空设计的</text>
      <text class="mt-paragraph">
        我们参考了商业银行个人信用贷与企业信用贷的主流审批框架，
        包括准入规则、反欺诈规则、A卡评分、额度测算、定价模型五个环节，
        并结合 {{ siteStore.expertCount }} 位资深金融分析师与一线信贷从业者的实战经验，
        对规则权重、额度公式、利率区间进行了多轮校准。
      </text>
    </view>

    <!-- 第二段：不满足通用模型 -->
    <view class="mt-section">
      <text class="mt-section-title">我们不满足于做一套通用模型</text>
      <text class="mt-paragraph">
        市面上大多数额度测算工具，都是一套模型套所有产品，
        算出来的结果粗糙、偏差大，用户看了也不敢信。
      </text>
      <text class="mt-paragraph mt-paragraph-emph">
        信测通选择了一条更难的路：按主流信用贷产品类型，分别构建独立的模拟审批模块。
      </text>
    </view>

    <!-- 第三段：6 大产品分别建模 -->
    <view class="mt-section">
      <text class="mt-section-title">每一类产品，单独建模、单独测算</text>
      <view class="mt-list">
        <view v-for="(p, i) in products" :key="p.code" class="mt-list-item">
          <text class="mt-list-idx">{{ i + 1 }}</text>
          <view class="mt-list-content">
            <text class="mt-list-name">{{ p.name }}</text>
            <text class="mt-list-desc">{{ p.subtitle }}</text>
            <view class="mt-list-vars">
              <text v-for="v in p.focus_vars_short" :key="v" class="mt-list-var">{{ v }}</text>
            </view>
          </view>
        </view>
      </view>
      <text class="mt-paragraph">
        每一类产品的审批偏好、额度公式、风险规则都不一样。
        同一份用户信息，在不同产品下的结果，本来就应该不同。
      </text>
    </view>

    <!-- 第四段：经得起三个追问 -->
    <view class="mt-section">
      <text class="mt-section-title">我们的模型，经得起三个追问</text>
      <view class="mt-qa">
        <text class="mt-qa-q">第一，逻辑从哪里来？</text>
        <text class="mt-qa-a">——来自银行信用贷审批的主流框架，由多位业内人士参与拆解。</text>
      </view>
      <view class="mt-qa">
        <text class="mt-qa-q">第二，权重怎么定？</text>
        <text class="mt-qa-a">——来自真实审批经验与案例回测，不是拍脑袋定的。</text>
      </view>
      <view class="mt-qa">
        <text class="mt-qa-q">第三，结果怎么验证？</text>
        <text class="mt-qa-a">——累计 {{ siteStore.caseCount }} 真实案例回测，评分与实际审批结果一致率持续优化。</text>
      </view>
    </view>

    <!-- 第五段：意义 -->
    <view class="mt-section mt-section-emph">
      <text class="mt-section-title">少一次硬查询，多一分未来获批的可能</text>
      <text class="mt-paragraph">
        我们不查征信，不接触真实放贷，所有结果均为模拟测算。
        但我们希望，这份模拟报告能让你在真正申请贷款之前，心里有数。
      </text>
      <text class="mt-paragraph mt-paragraph-emph">
        少一次盲目申请，就少一次硬查询。
      </text>
      <text class="mt-paragraph mt-paragraph-emph">
        少一次硬查询，就多一分未来获批的可能。
      </text>
      <text class="mt-paragraph">
        这就是信测通存在的意义。
      </text>
    </view>

    <!-- 谁参与了模型校准 -->
    <view class="mt-section">
      <text class="mt-section-title">谁参与了模型校准</text>
      <text class="mt-paragraph">
        我们的模型规则，由以下角色共同参与校准：
      </text>
      <view class="mt-roles">
        <view class="mt-role">
          <text class="mt-role-name">· 资深金融分析师</text>
          <text class="mt-role-desc">负责评分维度设计与权重分配</text>
        </view>
        <view class="mt-role">
          <text class="mt-role-name">· 一线信贷从业者</text>
          <text class="mt-role-desc">提供真实审批经验与产品差异反馈</text>
        </view>
        <view class="mt-role">
          <text class="mt-role-name">· 数据与风控从业者</text>
          <text class="mt-role-desc">负责规则落地、案例回测与模型迭代</text>
        </view>
        <view class="mt-role">
          <text class="mt-role-name">· 企业信贷顾问</text>
          <text class="mt-role-desc">负责企业贷模块的经营、纳税、法人维度校准</text>
        </view>
      </view>
      <text class="mt-paragraph mt-paragraph-tiny">
        他们的经验来自个人消费贷、公积金贷、企业经营贷、纳税贷、开票贷等多个业务场景，
        覆盖不同类型的审批偏好。
      </text>
      <text class="mt-paragraph mt-paragraph-tiny mt-paragraph-emph">
        所有参与者均以个人专业身份提供经验参考，不代表任何具体机构。
      </text>
      <text class="mt-paragraph mt-paragraph-tiny mt-paragraph-emph">
        信测通与任何银行或金融机构无官方合作关系。
      </text>
    </view>

    <!-- 信任区 -->
    <TrustZone />

    <BottomCompliance />
  </view>
</template>

<script setup lang="ts">
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import TrustZone from '@/components/trust-zone/TrustZone.vue'
import BottomCompliance from '@/components/bottom-compliance/BottomCompliance.vue'
import { useSiteStore } from '@/store/site'

const siteStore = useSiteStore()

const products = [
  { code: 'quality_unit', name: '优质单位贷', subtitle: '重点考察单位性质、工龄、收入稳定性', focus_vars_short: ['单位性质', '工龄', '收入稳定性'] },
  { code: 'housing_fund', name: '公积金贷', subtitle: '重点考察公积金连续缴纳时长与月缴额', focus_vars_short: ['公积金时长', '月缴额'] },
  { code: 'salary', name: '工薪贷', subtitle: '重点考察社保、代发工资、单位类型', focus_vars_short: ['社保', '代发工资', '单位类型'] },
  { code: 'house_owner', name: '有房客户贷', subtitle: '重点考察房产价值、按揭余额、资产状况', focus_vars_short: ['房产价值', '按揭余额', '资产状况'] },
  { code: 'tax', name: '纳税贷', subtitle: '重点考察企业纳税等级、年纳税额、连续性', focus_vars_short: ['纳税等级', '年纳税额', '连续性'] },
  { code: 'invoice', name: '开票贷', subtitle: '重点考察年开票额、经营稳定性、行业属性', focus_vars_short: ['年开票额', '行业属性', '经营稳定性'] },
]
</script>

<style lang="scss" scoped>
.methodology {
  min-height: 100vh;
  background: $bg;
  padding-bottom: 64rpx;
}
.mt-hero {
  background: $primary;
  padding: 48rpx 32rpx 64rpx;
  text-align: center;
  color: $text-white;
}
.mt-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
  margin-bottom: 16rpx;
}
.mt-title {
  font-family: $ff-serif;
  font-size: 48rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  display: block;
}
.mt-section {
  background: $card;
  margin: 32rpx;
  border: 1rpx solid $border-light;
  padding: 32rpx;
  &.mt-section-emph {
    background: linear-gradient(135deg, rgba(15, 35, 64, 0.04), $card);
    border-left: 4rpx solid $accent;
  }
}
.mt-section-title {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 700;
  color: $primary;
  letter-spacing: 1rpx;
  display: block;
  margin-bottom: 24rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid $border-light;
}
.mt-paragraph {
  font-size: $font-md;
  color: $text-main;
  line-height: 1.9;
  letter-spacing: 0.5rpx;
  display: block;
  margin-bottom: 16rpx;
  &.mt-paragraph-emph {
    color: $primary;
    font-weight: 500;
  }
  &.mt-paragraph-tiny {
    font-size: $font-sm;
    color: $text-sub;
  }
}
.mt-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin: 24rpx 0;
}
.mt-list-item {
  display: flex;
  gap: 24rpx;
  padding: 24rpx;
  background: rgba(15, 35, 64, 0.02);
  border-left: 4rpx solid $accent;
}
.mt-list-idx {
  font-family: $ff-serif;
  font-size: 32rpx;
  color: $accent;
  font-weight: 700;
  line-height: 1.2;
  flex-shrink: 0;
}
.mt-list-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.mt-list-name {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
}
.mt-list-desc {
  font-size: $font-sm;
  color: $text-sub;
  line-height: 1.6;
}
.mt-list-vars {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 4rpx;
}
.mt-list-var {
  font-size: $font-xs;
  color: $primary;
  background: $card;
  padding: 4rpx 12rpx;
  border: 1rpx solid $border-light;
  border-radius: 4rpx;
}
.mt-qa {
  padding: 16rpx 0;
  border-bottom: 1rpx dashed $border-light;
  &:last-child { border-bottom: none; }
}
.mt-qa-q {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 600;
  color: $accent;
  display: block;
  margin-bottom: 8rpx;
  letter-spacing: 0.5rpx;
}
.mt-qa-a {
  font-size: $font-sm;
  color: $text-main;
  line-height: 1.7;
  display: block;
  padding-left: 16rpx;
}
.mt-roles {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin: 16rpx 0;
}
.mt-role {
  padding: 16rpx;
  background: rgba(201, 169, 110, 0.05);
  border-left: 2rpx solid $accent;
}
.mt-role-name {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 600;
  color: $primary;
  display: block;
  margin-bottom: 4rpx;
}
.mt-role-desc {
  font-size: $font-sm;
  color: $text-sub;
  display: block;
}
</style>
