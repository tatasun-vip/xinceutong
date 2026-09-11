<template>
  <view class="materials">
    <ComplianceBar />

    <!-- 顶部 -->
    <view class="mt-hero">
      <text class="mt-eyebrow">PROMOTE MATERIALS</text>
      <text class="mt-title">推广员素材库</text>
      <text class="mt-sub">朋友圈 / 微信群 / 短视频口播 — 一键复制</text>
    </view>

    <!-- 1. 朋友圈文案 -->
    <view class="mt-section">
      <view class="mt-section-head">
        <text class="mt-section-num">01</text>
        <text class="mt-section-name">朋友圈文案</text>
        <text class="mt-section-tip">点击文案区域可一键复制</text>
      </view>

      <view v-for="(m, i) in moments" :key="i" class="mt-material">
        <view class="mt-material-head">
          <text class="mt-material-label">朋友圈文案 {{ i + 1 }}</text>
          <view class="mt-copy-btn" @tap="copy(m.content)">
            <text class="mt-copy-text">{{ copied === m.content ? '已复制' : '一键复制' }}</text>
          </view>
        </view>
        <view class="mt-material-body" @tap="copy(m.content)">
          <text class="mt-content" :selectable="true">{{ m.content }}</text>
        </view>
      </view>
    </view>

    <!-- 2. 微信群发话术 -->
    <view class="mt-section">
      <view class="mt-section-head">
        <text class="mt-section-num">02</text>
        <text class="mt-section-name">微信群发话术</text>
      </view>
      <view class="mt-material">
        <view class="mt-material-head">
          <text class="mt-material-label">一对一推荐话术</text>
          <view class="mt-copy-btn" @tap="copy(groupScript.content)">
            <text class="mt-copy-text">{{ copied === groupScript.content ? '已复制' : '一键复制' }}</text>
          </view>
        </view>
        <view class="mt-material-body" @tap="copy(groupScript.content)">
          <text class="mt-content" :selectable="true">{{ groupScript.content }}</text>
        </view>
      </view>
    </view>

    <!-- 3. 短视频口播脚本 -->
    <view class="mt-section">
      <view class="mt-section-head">
        <text class="mt-section-num">03</text>
        <text class="mt-section-name">短视频口播脚本（60 秒）</text>
      </view>
      <view class="mt-material">
        <view class="mt-material-head">
          <text class="mt-material-label">60 秒口播</text>
          <view class="mt-copy-btn" @tap="copy(videoScript.content)">
            <text class="mt-copy-text">{{ copied === videoScript.content ? '已复制' : '一键复制' }}</text>
          </view>
        </view>
        <view class="mt-material-body" @tap="copy(videoScript.content)">
          <text class="mt-content" :selectable="true">{{ videoScript.content }}</text>
        </view>
      </view>
    </view>

    <!-- 4. 使用提示 -->
    <view class="mt-tip">
      <text class="mt-tip-title">使用建议</text>
      <text class="mt-tip-line">· 朋友圈每天发 1-2 条，配合真实客户案例效果更好</text>
      <text class="mt-tip-line">· 微信群发时先一对一私聊，再发群，避免被踢</text>
      <text class="mt-tip-line">· 短视频前 3 秒必须吸引人，参考"同一份资料，额度差一倍"开头</text>
      <text class="mt-tip-line">· 推广员后台可查看点击 / 注册 / 付费转化数据</text>
    </view>

    <BottomCompliance />
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import BottomCompliance from '@/components/bottom-compliance/BottomCompliance.vue'

const copied = ref<string>('')

function copy(text: string) {
  copied.value = text
  uni.setClipboardData({
    data: text,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    },
  })
}

const moments = [
  {
    content: `做了这么多年助贷，我最怕客户说：
"我随便试了几家，都被拒了。"

征信花了，后面再好的资质也难做。

现在我让客户先做一次信测通模拟测评。
不查征信，一次看到 6 大产品下的额度、通过概率（利率仅作参考）。
模型由 50+ 位业内人士参与校准，逻辑经得起推敲。

先测再申请，少走弯路。
扫码免费测一次 ↓`,
  },
  {
    content: `你知道吗？
同一份资料，申请不同产品，额度可能差一倍。

为什么？
因为每家银行的审批逻辑不一样。
公积金贷看公积金，有房客户贷看资产，纳税贷看企业纳税。

信测通不是一套模型套所有产品，
而是按产品类型独立建模。
一次测评，看到不同产品下的真实差异。

不查征信，9.9元看完整报告。`,
  },
  {
    content: `很多人被拒，不是因为资质差，
是因为顺序错了。

先申请哪家、后申请哪家，
结果可能完全不一样。

信测通帮你模拟一遍，
少走弯路，少留查询。

模型参考银行风控框架，
50+ 位业内人士参与校准。
不查征信，先测再申请。`,
  },
]

const groupScript = {
  content: `您好，我是XX，做贷款咨询服务。

很多客户问我"能贷多少"，
我一般推荐先做一次模拟测评。

信测通不查征信，不产生查询记录，
2分钟出结果，
能看到 6 大产品下的额度区间、通过概率和风险点。

模型逻辑参考银行审批框架，
由 50+ 位资深金融分析师与一线信贷从业者参与校准，
累计 20,000+ 真实案例回测验证。

需要的话我发您链接，免费测一次。
先测再申请，少走弯路。`,
}

const videoScript = {
  content: `你知道吗？
同一份资料，申请不同银行，额度可能差一倍。

为什么？
因为每家银行的审批逻辑不一样。
公积金贷看公积金，
有房客户贷看资产，
纳税贷看企业纳税。

市面上大多数额度测算工具，
都是一套模型套所有产品，
算出来的结果粗糙、偏差大。

信测通选择了一条更难的路：
按主流信用贷产品类型，分别独立建模。
6 大产品，6 套逻辑，独立测算。

模型由 50+ 位资深金融分析师
与一线信贷从业者参与校准，
累计 20,000+ 真实案例回测验证。

不查征信，不产生硬查询。
一次测评，看到不同产品下的真实差异。

先测再申请，少走弯路。
点击下方链接，免费测一次。`,
}
</script>

<style lang="scss" scoped>
.materials {
  min-height: 100vh;
  background: $bg;
  padding-bottom: 64rpx;
}
.mt-hero {
  background: $primary;
  padding: 48rpx 32rpx 56rpx;
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
  font-size: 44rpx;
  font-weight: 700;
  letter-spacing: 4rpx;
  display: block;
}
.mt-sub {
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 1rpx;
  display: block;
  margin-top: 16rpx;
}
.mt-section {
  background: $card;
  margin: 32rpx;
  border: 1rpx solid $border-light;
  padding: 32rpx;
}
.mt-section-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid $border-light;
  margin-bottom: 24rpx;
}
.mt-section-num {
  font-family: $ff-mono;
  font-size: $font-sm;
  color: $accent;
  font-weight: 700;
  background: rgba(201, 169, 110, 0.1);
  padding: 4rpx 12rpx;
  letter-spacing: 1rpx;
}
.mt-section-name {
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
  flex: 1;
}
.mt-section-tip {
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 0.3rpx;
}
.mt-material {
  margin-bottom: 24rpx;
  border: 1rpx dashed $border-light;
  &:last-child { margin-bottom: 0; }
}
.mt-material-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 24rpx;
  background: rgba(15, 35, 64, 0.03);
  border-bottom: 1rpx solid $border-light;
}
.mt-material-label {
  font-size: $font-sm;
  color: $text-sub;
  font-weight: 600;
  letter-spacing: 0.5rpx;
}
.mt-copy-btn {
  background: $accent;
  padding: 6rpx 20rpx;
  border-radius: 4rpx;
}
.mt-copy-text {
  font-size: $font-xs;
  color: $text-white;
  font-weight: 600;
  letter-spacing: 1rpx;
}
.mt-material-body {
  padding: 24rpx;
}
.mt-content {
  font-size: $font-md;
  color: $text-main;
  line-height: 2;
  white-space: pre-wrap;
  letter-spacing: 0.3rpx;
  display: block;
}
.mt-tip {
  background: $card;
  margin: 32rpx;
  border: 1rpx solid $border-light;
  border-left: 4rpx solid $accent;
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.mt-tip-title {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
  display: block;
  margin-bottom: 8rpx;
}
.mt-tip-line {
  font-size: $font-sm;
  color: $text-sub;
  line-height: 1.7;
  display: block;
}
</style>
