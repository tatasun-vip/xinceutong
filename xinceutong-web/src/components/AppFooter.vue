<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const year = new Date().getFullYear()
</script>

<template>
  <footer class="ft">
    <div class="ft-inner container">
      <!-- Top: brand + 4 columns -->
      <div class="ft-top">
        <div class="ft-brand-col">
          <div class="ft-brand">
            <div class="ft-mark">信</div>
            <div class="ft-brand-name">信测通</div>
          </div>
          <p class="ft-desc">
            独立第三方信用贷模拟测评工具。针对 10 家银行公开披露的审批偏好，
            分别构建独立的模拟评分卡。一分钟看清您在每家银行的真实画像。
          </p>
          <div class="ft-trust">
            <div class="ft-trust-item">
              <span class="ft-trust-num">10</span>
              <span class="ft-trust-label">合作银行</span>
            </div>
            <div class="ft-trust-item">
              <span class="ft-trust-num">6</span>
              <span class="ft-trust-label">产品类型</span>
            </div>
            <div class="ft-trust-item">
              <span class="ft-trust-num">100<span class="ft-trust-unit">%</span></span>
              <span class="ft-trust-label">不查征信</span>
            </div>
          </div>
        </div>

        <div class="ft-col">
          <div class="ft-col-title">产品</div>
          <a class="ft-link" @click="router.push('/banks')">10 大银行测评</a>
          <a class="ft-link" @click="router.push('/banks')">个人信用画像</a>
          <a class="ft-link" @click="router.push('/banks')">企业经营贷测评</a>
          <a class="ft-link" @click="router.push('/disclaimer')">测评原理说明</a>
        </div>

        <div class="ft-col">
          <div class="ft-col-title">合规</div>
          <a class="ft-link" @click="router.push('/disclaimer')">免责声明</a>
          <a class="ft-link">隐私保护政策</a>
          <a class="ft-link">用户使用协议</a>
          <a class="ft-link">数据来源说明</a>
        </div>

        <div class="ft-col">
          <div class="ft-col-title">服务</div>
          <div class="ft-line">测评服务时间 · 工作日 9:00-21:00</div>
          <div class="ft-line">反馈邮箱 · feedback@xinceutong.cn</div>
          <div class="ft-line">合作洽谈 · business@xinceutong.cn</div>
        </div>
      </div>

      <!-- Middle: compliance bar -->
      <div class="ft-compliance">
        <div class="ft-compliance-item">
          <span class="ft-compliance-icon">⚖</span>
          <span>不查征信</span>
        </div>
        <div class="ft-compliance-item">
          <span class="ft-compliance-icon">⊘</span>
          <span>不读取银行数据</span>
        </div>
        <div class="ft-compliance-item">
          <span class="ft-compliance-icon">⏱</span>
          <span>不存留敏感信息</span>
        </div>
        <div class="ft-compliance-item">
          <span class="ft-compliance-icon">⊕</span>
          <span>符合《征信业管理条例》</span>
        </div>
      </div>

      <!-- Bottom: copyright + risk warning -->
      <div class="ft-bottom">
        <div class="ft-copyright">
          © {{ year }} 信测通 XINCEUTONG. All rights reserved.
        </div>
        <div class="ft-risk">
          ⚠ 风险提示：本平台为第三方模拟测评工具，所有结果基于公开资料建模推演，
          不构成任何贷款承诺。实际审批以银行官方为准。
        </div>
        <div class="ft-icp">
          ICP 备案号 · 京ICP备 2026xxxxxx 号-1
        </div>
      </div>
    </div>
  </footer>
</template>

<style lang="scss" scoped>
.ft {
  background: $primary-deeper;
  color: rgba(255, 255, 255, 0.85);
  padding: $space-20 0 $space-6;
  position: relative;

  /* 顶部金色细线 */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, $accent 50%, transparent 100%);
  }
}

.ft-inner {
  position: relative;
}

.ft-top {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  gap: $space-12;
  padding-bottom: $space-12;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

/* Brand column */
.ft-brand-col {
  display: flex;
  flex-direction: column;
  gap: $space-4;
}

.ft-brand {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.ft-mark {
  width: 40px;
  height: 40px;
  background: $gradient-primary;
  border: 1px solid $accent;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: $ff-serif;
  font-size: 20px;
  color: $accent;
  font-weight: 700;
}

.ft-brand-name {
  font-family: $ff-serif;
  font-size: 20px;
  font-weight: 700;
  color: $accent;
  letter-spacing: 1px;
}

.ft-desc {
  font-size: $font-sm;
  line-height: $lh-relaxed;
  color: rgba(255, 255, 255, 0.7);
  max-width: 360px;
}

.ft-trust {
  display: flex;
  gap: $space-8;
  padding-top: $space-4;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.ft-trust-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ft-trust-num {
  font-family: $ff-serif;
  font-size: $font-3xl;
  font-weight: 700;
  color: $accent;
  line-height: 1;
}

.ft-trust-unit {
  font-size: $font-lg;
}

.ft-trust-label {
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 1px;
}

/* Columns */
.ft-col {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.ft-col-title {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 600;
  color: $accent;
  margin-bottom: $space-2;
  letter-spacing: 1px;
}

.ft-link {
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.75);
  cursor: pointer;
  transition: color $dur-fast $ease-out;

  &:hover {
    color: $accent;
  }
}

.ft-line {
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.65);
  line-height: 1.6;
}

/* Compliance bar */
.ft-compliance {
  display: flex;
  justify-content: center;
  gap: $space-12;
  padding: $space-8 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-wrap: wrap;
}

.ft-compliance-item {
  display: flex;
  align-items: center;
  gap: $space-2;
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 0.5px;
}

.ft-compliance-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(184, 149, 74, 0.15);
  border: 1px solid $border-gold;
  color: $accent;
  font-size: 12px;
  border-radius: 50%;
}

/* Bottom */
.ft-bottom {
  padding-top: $space-6;
  display: flex;
  flex-direction: column;
  gap: $space-3;
  align-items: center;
  text-align: center;
}

.ft-copyright,
.ft-icp {
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 0.5px;
}

.ft-risk {
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.55);
  line-height: $lh-relaxed;
  max-width: 720px;
  padding: $space-3 $space-4;
  background: rgba(184, 149, 74, 0.05);
  border-left: 2px solid $accent;
}

/* Mobile */
@media (max-width: $bp-md) {
  .ft {
    padding: $space-12 0 $space-4;
  }
  .ft-top {
    grid-template-columns: 1fr 1fr;
    gap: $space-8;
  }
  .ft-brand-col {
    grid-column: 1 / -1;
  }
  .ft-compliance {
    gap: $space-4;
  }
  .ft-compliance-item {
    font-size: $font-xs;
  }
}

@media (max-width: $bp-sm) {
  .ft-top {
    grid-template-columns: 1fr;
  }
}
</style>
