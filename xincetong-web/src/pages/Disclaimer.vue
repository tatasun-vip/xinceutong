<script setup lang="ts">
</script>

<template>
  <div class="dc container">
    <div class="dc-head">
      <div class="text-eyebrow">LEGAL · DISCLAIMER</div>
      <h1 class="dc-title">测评免责声明</h1>
      <div class="divider-line"></div>
    </div>

    <div class="dc-content">
      <section class="dc-section">
        <h2 class="dc-h2">01 · 服务性质</h2>
        <p>信测通（以下简称"本平台"）所提供的测评服务，是基于公开市场数据与算法模型，对用户填写的信息进行模拟运算的工具。本平台不是银行、不发放贷款、不提供任何形式的金融服务。</p>
        <p>所有测评结果仅为算法模拟值，用于帮助用户了解不同银行的准入门槛和画像差异，<strong>不构成任何银行授信承诺，不代表任何银行官方立场</strong>。</p>
      </section>

      <section class="dc-section">
        <h2 class="dc-h2">02 · 数据使用</h2>
        <p>本平台在测评过程中：</p>
        <ul>
          <li><strong>不查征信</strong>：不接入任何征信系统（包括但不限于央行征信、百行征信、朴道征信等）。</li>
          <li><strong>不读取任何银行数据</strong>：不接入任何银行核心系统、信用卡系统、贷款系统。</li>
          <li><strong>不要求实名</strong>：测评过程不需要用户提供真实姓名、身份证号、银行卡号等敏感信息。</li>
          <li><strong>不存储敏感数据</strong>：测评结果不与个人身份信息绑定，仅用于本次会话展示。</li>
        </ul>
      </section>

      <section class="dc-section">
        <h2 class="dc-h2">03 · 结果解读</h2>
        <p>本平台展示的以下信息，均为<strong>模拟运算</strong>结果：</p>
        <ul>
          <li>信用等级（S/A/B/C/D/E）— 基于模型打分映射，非银行真实评级</li>
          <li>参考额度区间 — 模拟测算，非银行预授信</li>
          <li>参考利率区间 — 基于公开市场信息估算，非银行报价</li>
          <li>通过概率 — 模型估算，非银行审批结论</li>
          <li>推荐产品 — 基于银行公开产品信息，非银行定向推荐</li>
        </ul>
      </section>

      <section class="dc-section">
        <h2 class="dc-h2">04 · 风险提示</h2>
        <p>实际贷款申请请以银行官方审批结果为准。本平台结果与银行真实审批结果<strong>可能存在差异</strong>，包括但不限于：</p>
        <ul>
          <li>银行政策调整</li>
          <li>用户实际征信状况</li>
          <li>用户实际收入与负债</li>
          <li>银行风控模型差异</li>
        </ul>
      </section>

      <section class="dc-section">
        <h2 class="dc-h2">05 · 适用法律</h2>
        <p>本声明的解释、效力及争议解决均适用中华人民共和国法律。如本声明任何条款被认定为无效或不可执行，不影响其他条款的效力。</p>
      </section>

      <div class="dc-stamp">
        <div class="dc-stamp-line"></div>
        <div class="dc-stamp-text text-eyebrow">SIMULATION ONLY · 模拟运算工具</div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.dc {
  padding: $space-12 $content-padding $space-20;
  max-width: 880px;
}

.dc-head {
  text-align: center;
  margin-bottom: $space-12;
  .divider-line { margin: $space-3 auto; }
}

.dc-title {
  font-family: $ff-serif;
  font-size: 36px;
  color: $primary;
  font-weight: 600;
  letter-spacing: 2px;
  margin: $space-3 0;
}

.dc-content {
  background: $bg-card;
  border: 1px solid $border-light;
  border-top: 3px solid $primary;
  padding: $space-10 $space-12;
}

.dc-section {
  margin-bottom: $space-8;
  &:last-child { margin-bottom: 0; }
}

.dc-h2 {
  font-family: $ff-serif;
  font-size: 20px;
  color: $primary;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: $space-3;
  padding-bottom: $space-2;
  border-bottom: 1px solid $border-light;
}

.dc-content p, .dc-content li {
  font-size: $font-md;
  color: $text-regular;
  line-height: 1.9;
  margin-bottom: $space-3;
}

.dc-content ul {
  padding-left: $space-5;
  li {
    list-style: square;
    &::marker { color: $accent; }
  }
}

.dc-content strong {
  color: $primary;
  font-weight: 600;
}

.dc-stamp {
  text-align: center;
  padding-top: $space-8;
  margin-top: $space-8;
  border-top: 1px solid $border-light;
}

.dc-stamp-line {
  width: 48px;
  height: 2px;
  background: $accent;
  margin: 0 auto $space-3;
}
</style>
