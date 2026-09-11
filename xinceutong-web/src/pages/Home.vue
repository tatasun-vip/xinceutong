<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { bankApi, type Bank, type BankType } from '@/api/bank'

const router = useRouter()
const banks = ref<Bank[]>([])

onMounted(async () => {
  try {
    const res = await bankApi.list()
    banks.value = res.items
  } catch (e) {
    console.error('加载银行失败', e)
  }
})

const stats = computed(() => ({
  totalBanks: banks.value.length,
  stateOwned: banks.value.filter(b => b.type === 'state_owned').length,
  internet: banks.value.filter(b => b.type === 'internet').length,
}))

const TYPE_LABELS: Record<BankType, string> = {
  state_owned: '国有大行',
  joint_stock: '股份制',
  internet: '互联网银行',
  policy: '政策性',
  city_commercial: '城商行',
}

const featuredBanks = computed(() => banks.value.slice(0, 4))

// 倒计时
const COUNTDOWN_KEY = 'xct_promo_end'
function initCountdown() {
  let end = parseInt(localStorage.getItem(COUNTDOWN_KEY) || '0')
  if (!end || end < Date.now()) {
    end = Date.now() + 23 * 3600 * 1000 + 47 * 60 * 1000 + 12 * 1000
    localStorage.setItem(COUNTDOWN_KEY, String(end))
  }
  return end
}

const endAt = ref(initCountdown())
const now = ref(Date.now())
let timer: number | null = null

onMounted(() => {
  timer = window.setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })

const countdown = computed(() => {
  const diff = Math.max(0, endAt.value - now.value)
  const h = Math.floor(diff / 3600000)
  const m = Math.floor((diff % 3600000) / 60000)
  const s = Math.floor((diff % 60000) / 1000)
  return { h: String(h).padStart(2, '0'), m: String(m).padStart(2, '0'), s: String(s).padStart(2, '0') }
})

const totalUsers = ref(287_341)
onMounted(() => {
  setInterval(() => { totalUsers.value += Math.floor(Math.random() * 3) }, 5000)
})
</script>

<template>
  <div class="home">
    <!-- HERO -->
    <section class="hero">
      <div class="hero-bg">
        <div class="hero-bg-grid"></div>
        <div class="hero-bg-glow"></div>
      </div>

      <div class="container hero-inner">
        <div class="hero-left">
          <div class="hero-eyebrow">
            <span class="hero-eyebrow-dot"></span>
            CREDIT ASSESSMENT · 信用贷模拟评审
          </div>

          <h1 class="hero-title">
            <span class="hero-title-line">10 家银行</span>
            <span class="hero-title-line">
              <span class="hero-title-accent">专属</span>测评体系
            </span>
          </h1>

          <p class="hero-desc">
            每家银行的准入门槛、利率模型、推荐产品各不相同。
            <br />
            选择银行 · 定制问卷 · 模拟运算 · 一分钟看到该行真实画像。
          </p>

          <div class="hero-cta">
            <button class="btn-cta btn-cta--xl" @click="router.push('/banks')">
              <span>立即免费测评</span>
              <span class="btn-cta__arrow">→</span>
            </button>
            <button class="btn-cta btn-cta--ghost btn-cta--lg" @click="router.push('/disclaimer')">
              <span>了解测评原理</span>
            </button>
          </div>

          <div class="hero-trust">
            <div class="hero-trust-item">
              <span class="hero-trust-num">{{ totalUsers.toLocaleString() }}+</span>
              <span class="hero-trust-label">用户已测评</span>
            </div>
            <div class="hero-trust-sep"></div>
            <div class="hero-trust-item">
              <span class="hero-trust-num">100%</span>
              <span class="hero-trust-label">不查征信</span>
            </div>
            <div class="hero-trust-sep"></div>
            <div class="hero-trust-item">
              <span class="hero-trust-num">60s</span>
              <span class="hero-trust-label">出结果</span>
            </div>
          </div>
        </div>

        <div class="hero-right">
          <div class="hero-card">
            <div class="hero-card-head">
              <div class="hero-card-bank">
                <div class="hero-card-bank-mark">建</div>
                <div>
                  <div class="hero-card-bank-name">建设银行</div>
                  <div class="hero-card-bank-tag">快贷 · 个人信用</div>
                </div>
              </div>
              <div class="hero-card-stamp">SAMPLE</div>
            </div>

            <div class="hero-card-body">
              <div class="hero-card-level">
                <div class="hero-card-level-letter" :style="{ color: '#1B7D3D' }">A</div>
                <div class="hero-card-level-meta">
                  <div class="hero-card-level-text">优秀 · 良好准入</div>
                  <div class="hero-card-score">
                    <span class="hero-card-score-num">87</span>
                    <span class="hero-card-score-max">/100</span>
                  </div>
                </div>
              </div>

              <div class="hero-card-bar">
                <div class="hero-card-bar-fill" :style="{ width: '87%' }"></div>
                <div class="hero-card-bar-tick" style="left: 60%"></div>
                <div class="hero-card-bar-tick" style="left: 75%"></div>
                <div class="hero-card-bar-tick" style="left: 90%"></div>
              </div>

              <div class="hero-card-grid">
                <div class="hero-card-cell">
                  <div class="hero-card-cell-label">参考额度</div>
                  <div class="hero-card-cell-val">¥ 87.0 ~ 162.0 万</div>
                </div>
                <div class="hero-card-cell">
                  <div class="hero-card-cell-label">参考利率</div>
                  <div class="hero-card-cell-val">3.45 ~ 4.20 %</div>
                </div>
                <div class="hero-card-cell">
                  <div class="hero-card-cell-label">通过概率</div>
                  <div class="hero-card-cell-val hero-card-cell-good">高</div>
                </div>
                <div class="hero-card-cell">
                  <div class="hero-card-cell-label">推荐产品</div>
                  <div class="hero-card-cell-val">3 款</div>
                </div>
              </div>
            </div>

            <div class="hero-card-foot">
              <span class="hero-card-foot-line"></span>
              <span class="hero-card-foot-text">此为示例 · 您的结果可能不同</span>
            </div>
          </div>

          <div class="hero-card-tag-strip">
            <div class="hero-card-tag-item">⏱ 平均 60 秒</div>
            <div class="hero-card-tag-item">⊘ 模拟运算</div>
            <div class="hero-card-tag-item">✓ 永久保存</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 信任凭证：合作银行带 -->
    <section class="trustbar">
      <div class="container">
        <div class="trustbar-head">
          <span class="trustbar-title">10 家合作银行</span>
          <span class="trustbar-sub">· 2025 年度报告数据 · 每月更新</span>
        </div>
        <div class="trustbar-banks">
          <div class="trustbar-bank" v-for="b in banks" :key="b.code">
            {{ b.name.replace(/银行|股份|有限责任|有限|集团/g, '').slice(0, 4) }}
          </div>
        </div>
      </div>
    </section>

    <!-- 4 大价值 -->
    <section class="value section">
      <div class="container">
        <div class="sec-head">
          <div class="sec-eyebrow">CORE VALUE · 核心价值</div>
          <h2 class="sec-title">为什么信测通更准确</h2>
          <div class="sec-divider"></div>
          <p class="sec-sub">不是给 10 家银行打同一个分，而是为每家银行单独建模</p>
        </div>

        <div class="value-grid">
          <div class="value-item" v-for="(item, idx) in [
            { n: '01', t: '银行专属问卷', d: '每家银行问卷不同。建行问房产估值、工行问代发工资、招行问已有卡额度，匹配该行真实审批模型。', kpi: '10', suf: '套问卷' },
            { n: '02', t: '差异化评分卡', d: '不同银行准入门槛、利率模型、产品池各自独立。同一个客户在工行和微众可能得到完全不同的画像。', kpi: '94', suf: '张评分卡' },
            { n: '03', t: '合规底线', d: '本测评全程模拟运算，不查征信、不读取任何银行数据、不留存敏感信息，符合《征信业管理条例》。', kpi: '100', suf: '% 合规' },
            { n: '04', t: '结果可解释', d: '不只给一个分数，告诉你为什么是这个等级、命中了哪些风险项、推荐哪些产品、应该先优化什么。', kpi: '6', suf: '个维度' },
          ]" :key="idx">
            <div class="value-num">{{ item.n }}</div>
            <div class="value-kpi">
              <span class="value-kpi-num">{{ item.kpi }}</span>
              <span class="value-kpi-suffix">{{ item.suf }}</span>
            </div>
            <div class="value-title">{{ item.t }}</div>
            <div class="value-divider"></div>
            <p class="value-desc">{{ item.d }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 10 大银行精选 -->
    <section class="featured section">
      <div class="container">
        <div class="sec-head">
          <div class="sec-eyebrow">PARTNER BANKS · 合作银行</div>
          <h2 class="sec-title">10 大银行 · 完整覆盖</h2>
          <div class="sec-divider"></div>
          <p class="sec-sub">国有大行 / 股份制 / 互联网银行 / 城商行 · 全部独立建模</p>
        </div>

        <div class="bank-grid">
          <div v-for="b in featuredBanks" :key="b.code" class="bank-card" @click="router.push(`/assess/${b.code}`)">
            <div class="bank-card-top">
              <div class="bank-card-type">{{ TYPE_LABELS[b.type] }}</div>
              <div class="bank-card-arrow">→</div>
            </div>
            <div class="bank-card-name">{{ b.name }}</div>
            <div class="bank-card-slogan">{{ b.slogan }}</div>
            <div class="bank-card-desc">{{ b.short_desc }}</div>
            <div class="bank-card-foot">
              <span class="bank-card-link">开始测评</span>
            </div>
          </div>
        </div>

        <div class="featured-more">
          <button class="btn-secondary" @click="router.push('/banks')">
            <span>查看全部 {{ banks.length }} 家银行</span>
            <span>→</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 3 步流程 -->
    <section class="flow section">
      <div class="container">
        <div class="sec-head">
          <div class="sec-eyebrow">PROCESS · 测评流程</div>
          <h2 class="sec-title">3 步完成测评</h2>
          <div class="sec-divider"></div>
          <p class="sec-sub">无需注册 · 无需下载 · 60 秒出结果</p>
        </div>

        <div class="flow-grid">
          <div class="flow-item">
            <div class="flow-num">01</div>
            <div class="flow-title">选择银行</div>
            <p class="flow-desc">10 家银行 · 每家问卷和评分卡独立</p>
            <div class="flow-illu flow-illu-1">
              <div class="flow-illu-card"></div>
              <div class="flow-illu-card"></div>
              <div class="flow-illu-card flow-illu-card-active"></div>
              <div class="flow-illu-card"></div>
            </div>
          </div>

          <div class="flow-arrow">→</div>

          <div class="flow-item">
            <div class="flow-num">02</div>
            <div class="flow-title">填写 5 步表单</div>
            <p class="flow-desc">基础 / 职业 / 资产 / 征信 / 确认</p>
            <div class="flow-illu flow-illu-2">
              <div class="flow-illu-row"></div>
              <div class="flow-illu-row"></div>
              <div class="flow-illu-row flow-illu-row-short"></div>
              <div class="flow-illu-row"></div>
            </div>
          </div>

          <div class="flow-arrow">→</div>

          <div class="flow-item">
            <div class="flow-num">03</div>
            <div class="flow-title">查看画像</div>
            <p class="flow-desc">等级 + 额度 + 利率 + 推荐产品</p>
            <div class="flow-illu flow-illu-3">
              <div class="flow-illu-pie"></div>
              <div class="hero-card-level-letter" :style="{ color: '#1B7D3D', fontSize: '40px', lineHeight: '1' }">A</div>
            </div>
          </div>
        </div>

        <div class="flow-cta">
          <button class="btn-cta btn-cta--lg" @click="router.push('/banks')">
            <span>开始 60 秒测评</span>
            <span class="btn-cta__arrow">→</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 样本测评展示 -->
    <section class="samples section">
      <div class="container">
        <div class="sec-head">
          <div class="sec-eyebrow">SAMPLE REPORTS · 样本报告</div>
          <h2 class="sec-title">真实测评效果展示</h2>
          <div class="sec-divider"></div>
          <p class="sec-sub">3 份不同等级的样本报告（脱敏数据，仅供预览）</p>
        </div>

        <div class="samples-grid">
          <div class="sample-card sample-card--a">
            <div class="sample-head">
              <div class="sample-eyebrow">A · 优秀</div>
              <div class="sample-bank">建设银行 · 快贷</div>
            </div>
            <div class="sample-score">
              <div class="sample-score-num">87</div>
              <div class="sample-score-max">/100</div>
            </div>
            <div class="sample-bar">
              <div class="sample-bar-fill" :style="{ width: '87%', background: '#1B7D3D' }"></div>
            </div>
            <div class="sample-meta">
              <div class="sample-meta-row"><span>参考额度</span><span class="sample-meta-val">¥ 87.0 ~ 162.0 万</span></div>
              <div class="sample-meta-row"><span>参考利率</span><span class="sample-meta-val">3.45 ~ 4.20 %</span></div>
              <div class="sample-meta-row"><span>通过概率</span><span class="sample-meta-val sample-meta-good">高</span></div>
            </div>
            <div class="sample-tip">命中：公积金高基数 / 一线城市 / 上市公司</div>
          </div>

          <div class="sample-card sample-card--c">
            <div class="sample-head">
              <div class="sample-eyebrow">C · 一般</div>
              <div class="sample-bank">招商银行 · 闪电贷</div>
            </div>
            <div class="sample-score">
              <div class="sample-score-num">52</div>
              <div class="sample-score-max">/100</div>
            </div>
            <div class="sample-bar">
              <div class="sample-bar-fill" :style="{ width: '52%', background: '#C77A0A' }"></div>
            </div>
            <div class="sample-meta">
              <div class="sample-meta-row"><span>参考额度</span><span class="sample-meta-val">¥ 12.0 ~ 25.0 万</span></div>
              <div class="sample-meta-row"><span>参考利率</span><span class="sample-meta-val">7.20 ~ 9.50 %</span></div>
              <div class="sample-meta-row"><span>通过概率</span><span class="sample-meta-val">中</span></div>
            </div>
            <div class="sample-tip">建议：先优化信用卡使用率 / 减少近期查询</div>
          </div>

          <div class="sample-card sample-card--e">
            <div class="sample-head">
              <div class="sample-eyebrow">E · 暂缓</div>
              <div class="sample-bank">微众银行 · 微粒贷</div>
            </div>
            <div class="sample-score">
              <div class="sample-score-num">18</div>
              <div class="sample-score-max">/100</div>
            </div>
            <div class="sample-bar">
              <div class="sample-bar-fill" :style="{ width: '18%', background: '#5C6B7C' }"></div>
            </div>
            <div class="sample-meta">
              <div class="sample-meta-row"><span>参考额度</span><span class="sample-meta-val">¥ 0.0 ~ 0.0 万</span></div>
              <div class="sample-meta-row"><span>参考利率</span><span class="sample-meta-val">暂不适用</span></div>
              <div class="sample-meta-row"><span>通过概率</span><span class="sample-meta-val sample-meta-bad">极低</span></div>
            </div>
            <div class="sample-tip">建议：先稳定工作 / 修复征信 / 6 个月后重测</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 限时优惠 + 倒计时 -->
    <section class="promo section">
      <div class="container">
        <div class="promo-card">
          <div class="promo-left">
            <div class="promo-eyebrow">
              <span class="promo-eyebrow-tag">限时活动</span>
              LIMITED OFFER
            </div>
            <h2 class="promo-title">完整报告 · 限时 7 折</h2>
            <p class="promo-desc">
              包含完整 6 维度画像、产品对比、改善建议、推演未来通过率。
              本次活动每日限量 50 份，先到先得。
            </p>
            <div class="promo-cta">
              <button class="btn-cta btn-cta--lg" @click="router.push('/banks')">
                <span>立即领取</span>
                <span class="btn-cta__arrow">→</span>
              </button>
              <div class="promo-price">
                <span class="promo-price-old">¥ 19.9</span>
                <span class="promo-price-now">¥ 13.9</span>
              </div>
            </div>
          </div>

          <div class="promo-right">
            <div class="promo-countdown">
              <div class="promo-countdown-eyebrow">活动剩余时间</div>
              <div class="promo-countdown-grid">
                <div class="promo-countdown-cell">
                  <div class="promo-countdown-num">{{ countdown.h }}</div>
                  <div class="promo-countdown-label">小时</div>
                </div>
                <div class="promo-countdown-sep">:</div>
                <div class="promo-countdown-cell">
                  <div class="promo-countdown-num">{{ countdown.m }}</div>
                  <div class="promo-countdown-label">分钟</div>
                </div>
                <div class="promo-countdown-sep">:</div>
                <div class="promo-countdown-cell">
                  <div class="promo-countdown-num">{{ countdown.s }}</div>
                  <div class="promo-countdown-label">秒</div>
                </div>
              </div>
            </div>

            <div class="promo-stock">
              <div class="promo-stock-label">今日剩余名额</div>
              <div class="promo-stock-bar">
                <div class="promo-stock-bar-fill" :style="{ width: '23%' }"></div>
              </div>
              <div class="promo-stock-num">仅剩 <strong>12</strong> / 50 份</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ -->
    <section class="faq section">
      <div class="container">
        <div class="sec-head">
          <div class="sec-eyebrow">FAQ · 常见问题</div>
          <h2 class="sec-title">关于本测评，您可能想了解</h2>
          <div class="sec-divider"></div>
        </div>

        <div class="faq-grid">
          <details class="faq-item" v-for="(item, i) in [
            { q: '测评结果准确吗？', a: '本测评基于 10 家银行 2025 年度报告与公开授信政策建模，不查征信、不上报数据。结果反映该行真实审批倾向，准确度高于通用评分工具。' },
            { q: '会查我的征信吗？', a: '不会。本平台为纯模拟运算工具，不连接征信系统、不读取任何银行数据、不存留敏感信息。符合《征信业管理条例》。' },
            { q: '为什么不同银行结果差别大？', a: '这正是本测评的价值。工行看重代发工资，建行看公积金，招行看已有卡额度。同一个客户在 10 家银行的画像可能天差地别。' },
            { q: '测评需要多长时间？', a: '平均 60 秒完成问卷填写，系统自动运算并出结果。' },
            { q: '完整报告包含什么？', a: '免费版：1 份核心画像 + 1 个核心问题。完整报告：6 维度画像 + 产品对比 + 改善建议 + 未来通过率推演。' },
            { q: '可以重新测评吗？', a: '可以。改善条件后重新测评，结果即时更新。建议先优化系统提示的 1-2 个核心问题，再做第二次测评。' },
          ]" :key="i" :open="i === 0">
            <summary class="faq-q">
              <span>{{ item.q }}</span>
              <span class="faq-icon">+</span>
            </summary>
            <div class="faq-a">{{ item.a }}</div>
          </details>
        </div>
      </div>
    </section>

    <!-- 移动端底部固定 CTA -->
    <div class="mbar">
      <div class="mbar-price">
        <span class="mbar-price-old">¥ 19.9</span>
        <span class="mbar-price-now">¥ 13.9</span>
        <span class="mbar-price-tag">限时</span>
      </div>
      <button class="btn-cta btn-cta--block" @click="router.push('/banks')">
        <span>立即免费测评</span>
        <span class="btn-cta__arrow">→</span>
      </button>
    </div>
  </div>
</template>

<style lang="scss" scoped>
// ============================================================================
// 通用
// ============================================================================
.section {
  padding: clamp(56px, 8vw, 96px) 0;
}
.sec-head {
  text-align: center;
  margin-bottom: $space-12;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.sec-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  letter-spacing: 4px;
  color: $accent;
  text-transform: uppercase;
  font-weight: 500;
  margin-bottom: $space-3;
}
.sec-title {
  font-family: $ff-serif;
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  color: $primary;
  line-height: 1.2;
  letter-spacing: 1px;
  margin: 0;
}
.sec-divider {
  width: 56px;
  height: 2px;
  background: $accent;
  margin: $space-4 0;
}
.sec-sub {
  font-size: $font-md;
  color: $text-secondary;
  letter-spacing: 0.5px;
}

// ============================================================================
// HERO
// ============================================================================
.hero {
  position: relative;
  background: $gradient-dark-hero;
  color: $text-on-primary;
  padding: clamp(64px, 10vw, 120px) 0 clamp(80px, 12vw, 140px);
  overflow: hidden;
}
.hero-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.hero-bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}
.hero-bg-glow {
  position: absolute;
  top: -200px;
  right: -100px;
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, rgba(212, 181, 116, 0.12) 0%, transparent 60%);
}
.hero-inner {
  position: relative;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: $space-16;
  align-items: center;
}
.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: $space-2;
  font-family: $ff-mono;
  font-size: $font-xs;
  letter-spacing: 3px;
  color: $accent;
  font-weight: 500;
  padding: 6px 12px;
  border: 1px solid $border-gold;
  background: rgba(184, 149, 74, 0.08);
  margin-bottom: $space-6;
}
.hero-eyebrow-dot {
  width: 6px;
  height: 6px;
  background: $accent;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
.hero-title {
  font-family: $ff-serif;
  font-size: clamp(40px, 6vw, 72px);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: 2px;
  margin: 0 0 $space-6;
  color: $text-on-primary;
  span { display: block; }
}
.hero-title-accent {
  background: $gradient-text-gold;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}
.hero-desc {
  font-size: $font-lg;
  line-height: $lh-relaxed;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 $space-8;
  max-width: 520px;
  letter-spacing: 0.5px;
}
.hero-cta {
  display: flex;
  gap: $space-3;
  margin-bottom: $space-12;
  flex-wrap: wrap;
}
.hero-trust {
  display: flex;
  align-items: center;
  gap: $space-6;
  padding-top: $space-6;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}
.hero-trust-item { display: flex; flex-direction: column; gap: 2px; }
.hero-trust-num {
  font-family: $ff-serif;
  font-size: $font-2xl;
  font-weight: 700;
  color: $accent;
  line-height: 1;
}
.hero-trust-label {
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.65);
  letter-spacing: 1px;
}
.hero-trust-sep {
  width: 1px;
  height: 32px;
  background: rgba(255, 255, 255, 0.15);
}

// 右侧 Hero 卡片
.hero-right { position: relative; }
.hero-card {
  background: $white;
  color: $text-main;
  box-shadow: $shadow-xl;
  position: relative;
  overflow: hidden;
  &::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: $gradient-gold;
  }
}
.hero-card-head {
  padding: $space-5 $space-6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px dashed $border-light;
}
.hero-card-bank { display: flex; align-items: center; gap: $space-3; }
.hero-card-bank-mark {
  width: 40px;
  height: 40px;
  background: $primary;
  color: $accent;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: $ff-serif;
  font-size: $font-lg;
  font-weight: 700;
  border: 1px solid $border-gold;
}
.hero-card-bank-name {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 600;
  color: $primary;
  line-height: 1.2;
}
.hero-card-bank-tag {
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 0.5px;
}
.hero-card-stamp {
  font-family: $ff-mono;
  font-size: 10px;
  letter-spacing: 2px;
  color: $text-disabled;
  padding: 3px 8px;
  border: 1px solid $border-light;
  transform: rotate(-2deg);
}
.hero-card-body { padding: $space-6; }
.hero-card-level {
  display: flex;
  align-items: baseline;
  gap: $space-4;
  margin-bottom: $space-4;
}
.hero-card-level-letter {
  font-family: $ff-serif;
  font-size: 72px;
  font-weight: 700;
  line-height: 0.9;
  letter-spacing: -2px;
}
.hero-card-level-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.hero-card-level-text {
  font-size: $font-md;
  color: $text-regular;
  font-weight: 500;
}
.hero-card-score { font-family: $ff-serif; }
.hero-card-score-num {
  font-size: $font-3xl;
  font-weight: 700;
  color: $primary;
  line-height: 1;
}
.hero-card-score-max { font-size: $font-md; color: $text-weak; }
.hero-card-bar {
  height: 6px;
  background: $border-light;
  position: relative;
  margin-bottom: $space-5;
}
.hero-card-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, $primary 0%, $accent 100%);
  transition: width $dur-slow $ease-out;
}
.hero-card-bar-tick {
  position: absolute;
  top: -2px;
  width: 1px;
  height: 10px;
  background: $border-regular;
}
.hero-card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $space-3;
}
.hero-card-cell {
  padding: $space-3;
  background: $bg-soft;
  border-left: 2px solid $accent;
}
.hero-card-cell-label {
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 1px;
  margin-bottom: 2px;
}
.hero-card-cell-val {
  font-family: $ff-mono;
  font-size: $font-sm;
  color: $text-strong;
  font-weight: 600;
}
.hero-card-cell-good { color: $success; }
.hero-card-foot {
  background: $accent-bg;
  padding: $space-3 $space-6;
  text-align: center;
  font-size: $font-xs;
  color: $accent-dark;
  letter-spacing: 1px;
}
.hero-card-tag-strip {
  display: flex;
  gap: $space-2;
  margin-top: $space-3;
  flex-wrap: wrap;
}
.hero-card-tag-item {
  flex: 1;
  text-align: center;
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 0.5px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

// ============================================================================
// 信任凭证带
// ============================================================================
.trustbar {
  background: $white;
  padding: $space-10 0;
  border-bottom: 1px solid $border-light;
}
.trustbar-head {
  text-align: center;
  margin-bottom: $space-6;
}
.trustbar-title {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 600;
  color: $primary;
  letter-spacing: 2px;
}
.trustbar-sub {
  font-size: $font-sm;
  color: $text-weak;
  margin-left: $space-2;
}
.trustbar-banks {
  display: flex;
  flex-wrap: wrap;
  gap: $space-2;
  justify-content: center;
}
.trustbar-bank {
  font-family: $ff-serif;
  font-size: $font-md;
  font-weight: 500;
  color: $text-secondary;
  padding: 8px 16px;
  background: $bg-soft;
  border: 1px solid $border-light;
  letter-spacing: 1px;
  transition: all $dur-fast $ease-out;
  &:hover {
    color: $accent-dark;
    border-color: $border-gold;
    background: $accent-bg;
  }
}

// ============================================================================
// 4 大价值
// ============================================================================
.value { background: $bg-soft; }
.value-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $space-5;
}
.value-item {
  background: $white;
  padding: $space-8 $space-6;
  border: 1px solid $border-light;
  border-top: 3px solid $accent;
  position: relative;
  transition: transform $dur-base $ease-out, box-shadow $dur-base $ease-out;
  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-lg;
  }
}
.value-num {
  font-family: $ff-mono;
  font-size: $font-sm;
  color: $accent;
  letter-spacing: 2px;
  margin-bottom: $space-4;
}
.value-kpi {
  display: flex;
  align-items: baseline;
  gap: $space-2;
  margin-bottom: $space-3;
}
.value-kpi-num {
  font-family: $ff-serif;
  font-size: 56px;
  font-weight: 700;
  color: $primary;
  line-height: 1;
  letter-spacing: -1px;
}
.value-kpi-suffix {
  font-size: $font-sm;
  color: $text-weak;
  letter-spacing: 0.5px;
}
.value-title {
  font-family: $ff-serif;
  font-size: $font-xl;
  font-weight: 600;
  color: $primary;
  margin-bottom: $space-3;
  letter-spacing: 1px;
}
.value-divider {
  width: 32px;
  height: 1px;
  background: $accent;
  margin-bottom: $space-4;
}
.value-desc {
  font-size: $font-sm;
  line-height: $lh-relaxed;
  color: $text-secondary;
  margin: 0;
}

// ============================================================================
// 10 大银行精选
// ============================================================================
.featured { background: $white; }
.bank-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $space-5;
}
.bank-card {
  background: $white;
  border: 1px solid $border-light;
  padding: $space-6;
  cursor: pointer;
  transition: all $dur-base $ease-out;
  position: relative;
  overflow: hidden;
  &:hover {
    border-color: $accent;
    box-shadow: $shadow-gold;
    transform: translateY(-2px);
  }
  &:hover .bank-card-arrow { color: $accent; transform: translate(4px, -4px); }
  &:hover .bank-card-link { color: $accent-dark; }
}
.bank-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $space-4;
}
.bank-card-type {
  font-family: $ff-mono;
  font-size: 10px;
  letter-spacing: 2px;
  color: $text-weak;
  padding: 3px 8px;
  background: $bg-soft;
  border: 1px solid $border-light;
}
.bank-card-arrow {
  font-size: 20px;
  color: $text-weak;
  transition: all $dur-fast $ease-out;
}
.bank-card-name {
  font-family: $ff-serif;
  font-size: $font-2xl;
  font-weight: 700;
  color: $primary;
  margin-bottom: $space-2;
  letter-spacing: 1px;
}
.bank-card-slogan {
  font-size: $font-sm;
  color: $accent;
  margin-bottom: $space-3;
  letter-spacing: 0.5px;
}
.bank-card-desc {
  font-size: $font-sm;
  line-height: $lh-relaxed;
  color: $text-secondary;
  margin-bottom: $space-5;
  min-height: 60px;
}
.bank-card-foot {
  padding-top: $space-3;
  border-top: 1px solid $border-light;
}
.bank-card-link {
  font-size: $font-sm;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1px;
  transition: color $dur-fast $ease-out;
}
.featured-more {
  text-align: center;
  margin-top: $space-12;
}

// ============================================================================
// 3 步流程
// ============================================================================
.flow {
  background: $bg-soft;
  position: relative;
}
.flow-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  gap: $space-6;
  align-items: center;
  margin-bottom: $space-12;
}
.flow-item {
  text-align: center;
  padding: $space-8;
  background: $white;
  border: 1px solid $border-light;
  position: relative;
  transition: all $dur-base $ease-out;
  &:hover {
    border-color: $accent;
    box-shadow: $shadow-gold;
  }
}
.flow-num {
  font-family: $ff-serif;
  font-size: 48px;
  font-weight: 700;
  color: $accent;
  line-height: 1;
  margin-bottom: $space-3;
}
.flow-title {
  font-family: $ff-serif;
  font-size: $font-xl;
  font-weight: 600;
  color: $primary;
  margin-bottom: $space-2;
  letter-spacing: 1px;
}
.flow-desc {
  font-size: $font-sm;
  color: $text-secondary;
  margin: 0 0 $space-5;
  letter-spacing: 0.5px;
}
.flow-illu {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: $space-3;
  background: $bg-soft;
  border: 1px dashed $border-regular;
}
.flow-illu-card {
  width: 36px;
  height: 48px;
  background: $white;
  border: 1px solid $border-light;
  position: relative;
  &::before {
    content: '';
    position: absolute;
    top: 6px;
    left: 6px;
    right: 6px;
    height: 2px;
    background: $border-light;
  }
  &::after {
    content: '';
    position: absolute;
    top: 12px;
    left: 6px;
    right: 14px;
    height: 2px;
    background: $border-light;
  }
}
.flow-illu-card-active {
  border-color: $accent;
  box-shadow: 0 0 0 2px $accent-bg;
  background: $accent-bg;
  &::before, &::after { background: $accent; }
}
.flow-illu-row {
  width: 80%;
  height: 8px;
  background: $border-light;
}
.flow-illu-row-short { width: 60%; background: $accent; }
.flow-illu-3 {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.flow-illu-pie {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: conic-gradient($accent 0% 87%, $border-light 87% 100%);
  position: absolute;
}
.flow-arrow {
  font-size: 32px;
  color: $accent;
  font-weight: 300;
}
.flow-cta {
  text-align: center;
}

// ============================================================================
// 样本测评
// ============================================================================
.samples { background: $white; }
.samples-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-6;
}
.sample-card {
  background: $white;
  border: 1px solid $border-light;
  padding: $space-6;
  position: relative;
  transition: all $dur-base $ease-out;
  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-lg;
  }
}
.sample-card--a { border-top: 3px solid $level-a; }
.sample-card--c { border-top: 3px solid $level-c; }
.sample-card--e { border-top: 3px solid $level-e; }
.sample-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $space-5;
}
.sample-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  letter-spacing: 2px;
  color: $text-weak;
  padding: 2px 8px;
  background: $bg-soft;
}
.sample-card--a .sample-eyebrow { color: $level-a; }
.sample-card--c .sample-eyebrow { color: $level-c; }
.sample-card--e .sample-eyebrow { color: $level-e; }
.sample-bank {
  font-size: $font-sm;
  color: $text-regular;
  font-weight: 500;
}
.sample-score {
  display: flex;
  align-items: baseline;
  gap: $space-2;
  margin-bottom: $space-3;
}
.sample-score-num {
  font-family: $ff-serif;
  font-size: 64px;
  font-weight: 700;
  color: $primary;
  line-height: 1;
}
.sample-score-max {
  font-family: $ff-serif;
  font-size: $font-md;
  color: $text-weak;
}
.sample-bar {
  height: 6px;
  background: $border-light;
  margin-bottom: $space-5;
  overflow: hidden;
}
.sample-bar-fill {
  height: 100%;
  transition: width $dur-slow $ease-out;
}
.sample-meta {
  display: flex;
  flex-direction: column;
  gap: $space-2;
  padding-top: $space-4;
  border-top: 1px dashed $border-light;
  margin-bottom: $space-4;
}
.sample-meta-row {
  display: flex;
  justify-content: space-between;
  font-size: $font-sm;
  color: $text-secondary;
}
.sample-meta-val {
  font-family: $ff-mono;
  font-weight: 600;
  color: $text-strong;
}
.sample-meta-good { color: $success; }
.sample-meta-bad { color: $danger; }
.sample-tip {
  font-size: $font-xs;
  color: $text-weak;
  line-height: 1.6;
  padding: $space-2 $space-3;
  background: $bg-soft;
  border-left: 2px solid $accent;
}

// ============================================================================
// 限时优惠
// ============================================================================
.promo { background: $bg-soft; }
.promo-card {
  background: $gradient-dark-hero;
  color: $text-on-primary;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $space-12;
  padding: $space-12 $space-10;
  position: relative;
  overflow: hidden;
  &::before {
    content: '';
    position: absolute;
    top: -100px;
    right: -100px;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(212, 181, 116, 0.15) 0%, transparent 60%);
    pointer-events: none;
  }
}
.promo-left {
  position: relative;
  z-index: 1;
}
.promo-eyebrow {
  font-family: $ff-mono;
  font-size: $font-xs;
  letter-spacing: 3px;
  color: $accent;
  margin-bottom: $space-3;
  display: flex;
  align-items: center;
  gap: $space-2;
}
.promo-eyebrow-tag {
  padding: 3px 10px;
  background: $accent;
  color: $primary;
  font-weight: 700;
  letter-spacing: 1px;
}
.promo-title {
  font-family: $ff-serif;
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
  margin: 0 0 $space-4;
  color: $text-on-primary;
  letter-spacing: 1px;
}
.promo-desc {
  font-size: $font-md;
  line-height: $lh-relaxed;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 $space-8;
}
.promo-cta {
  display: flex;
  align-items: center;
  gap: $space-6;
  flex-wrap: wrap;
}
.promo-price {
  display: flex;
  align-items: baseline;
  gap: $space-2;
}
.promo-price-old {
  font-family: $ff-serif;
  font-size: $font-xl;
  color: rgba(255, 255, 255, 0.5);
  text-decoration: line-through;
}
.promo-price-now {
  font-family: $ff-serif;
  font-size: $font-4xl;
  font-weight: 700;
  color: $accent;
  line-height: 1;
}
.promo-right {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: $space-8;
}
.promo-countdown-eyebrow {
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 2px;
  text-align: center;
  margin-bottom: $space-3;
}
.promo-countdown-grid {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr;
  gap: $space-3;
  align-items: center;
}
.promo-countdown-cell {
  text-align: center;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid $border-gold;
  padding: $space-4 $space-3;
}
.promo-countdown-num {
  font-family: $ff-mono;
  font-size: 48px;
  font-weight: 700;
  color: $accent;
  line-height: 1;
  letter-spacing: 2px;
}
.promo-countdown-label {
  font-size: $font-xs;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 2px;
  margin-top: $space-2;
}
.promo-countdown-sep {
  font-family: $ff-mono;
  font-size: 32px;
  color: $accent;
  font-weight: 300;
  text-align: center;
}
.promo-stock-label {
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 1px;
  text-align: center;
  margin-bottom: $space-2;
}
.promo-stock-bar {
  height: 6px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  margin-bottom: $space-2;
}
.promo-stock-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, $warning 0%, $danger 100%);
  transition: width $dur-slow $ease-out;
}
.promo-stock-num {
  font-size: $font-sm;
  color: rgba(255, 255, 255, 0.85);
  text-align: center;
  strong {
    font-family: $ff-mono;
    color: $warning;
    font-size: $font-lg;
  }
}

// ============================================================================
// FAQ
// ============================================================================
.faq { background: $white; }
.faq-grid {
  max-width: 840px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}
.faq-item {
  background: $bg-soft;
  border: 1px solid $border-light;
  padding: 0;
  transition: all $dur-fast $ease-out;
  &[open] {
    background: $white;
    border-color: $border-gold;
    box-shadow: $shadow-sm;
  }
}
.faq-q {
  padding: $space-5 $space-6;
  font-size: $font-md;
  font-weight: 500;
  color: $primary;
  cursor: pointer;
  list-style: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  letter-spacing: 0.5px;
  &::-webkit-details-marker { display: none; }
}
.faq-icon {
  font-size: 24px;
  color: $accent;
  font-weight: 300;
  transition: transform $dur-base $ease-out;
  flex-shrink: 0;
  margin-left: $space-4;
}
.faq-item[open] .faq-icon {
  transform: rotate(45deg);
}
.faq-a {
  padding: 0 $space-6 $space-5;
  font-size: $font-sm;
  line-height: $lh-relaxed;
  color: $text-secondary;
}

// ============================================================================
// 移动端底部固定 CTA
// ============================================================================
.mbar {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: $z-sticky;
  background: $white;
  border-top: 1px solid $border-light;
  padding: $space-2 $space-3;
  gap: $space-3;
  align-items: center;
  box-shadow: 0 -4px 16px rgba(11, 37, 69, 0.08);
}
.mbar-price {
  display: flex;
  align-items: baseline;
  gap: 2px;
  flex-direction: column;
  flex-shrink: 0;
}
.mbar-price-old {
  font-size: 10px;
  color: $text-weak;
  text-decoration: line-through;
}
.mbar-price-now {
  font-family: $ff-serif;
  font-size: $font-xl;
  font-weight: 700;
  color: $accent-dark;
  line-height: 1;
}
.mbar-price-tag {
  font-size: 9px;
  color: $white;
  background: $danger;
  padding: 1px 4px;
  letter-spacing: 0.5px;
}

// ============================================================================
// 移动端响应式
// ============================================================================
@media (max-width: $bp-lg) {
  .hero-inner { grid-template-columns: 1fr; gap: $space-12; }
  .value-grid { grid-template-columns: repeat(2, 1fr); }
  .bank-grid { grid-template-columns: repeat(2, 1fr); }
  .samples-grid { grid-template-columns: 1fr; }
  .promo-card { grid-template-columns: 1fr; gap: $space-8; padding: $space-8 $space-6; }
  .flow-grid { grid-template-columns: 1fr; }
  .flow-arrow { transform: rotate(90deg); }
}
@media (max-width: $bp-md) {
  .mbar { display: flex; }
  .home { padding-bottom: $bottom-bar-h; }
  .hero-card-tag-strip { display: none; }
  .flow-item { padding: $space-5; }
  .promo-countdown-num { font-size: 32px; }
  .promo-countdown-cell { padding: $space-3 $space-2; }
  .faq-q { font-size: $font-sm; padding: $space-4 $space-5; }
}
@media (max-width: $bp-sm) {
  .value-grid { grid-template-columns: 1fr; }
  .bank-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 36px; }
  .promo-title { font-size: 24px; }
}
</style>
