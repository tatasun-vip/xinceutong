<!--
  free.vue · 测评结果 · 免费版
  v3.2 重构：1 屏精准，吊胃口但不过分
    - 顶部：一句话结论（按 level 给颜色/动作）
    - 评分环 + 综合分
    - 1 个最高严重度问题（量化影响）
    - 6 大产品摘要（带 ⭐）
    - 强动机付费引导卡
-->
<template>
  <view class="free-page">
    <ComplianceBar />

    <view v-if="loading" class="loading-state">
      <view class="loading-spinner" />
      <view class="loading-text">加载中</view>
    </view>

    <template v-else-if="result">
      <!-- v9 增量 · B1：360rpx 金色付费引导 banner（强动机付费）
           设计：金色渐变背景 + 左文"完整报告解锁 ¥9.9" + 右按钮"立即解锁"
           位置：fp-hero 之上，所有结果内容之前 → 用户第一眼看到 -->
      <view v-if="!result.is_paid" class="fp-paywall-banner" @tap="goPay">
        <view class="fp-paywall-banner-bg" />
        <view class="fp-paywall-banner-content">
          <view class="fp-paywall-banner-left">
            <view class="fp-paywall-banner-eyebrow">UNLOCK · 完整报告</view>
            <view class="fp-paywall-banner-title">
              6 大产品深度证据链
              <text class="fp-paywall-banner-amount">¥{{ siteStore.payPrice }}</text>
            </view>
            <view class="fp-paywall-banner-sub">命中规则 · 不推荐原因 · 提分建议 · 实际可贷金额</view>
          </view>
          <view class="fp-paywall-banner-btn">
            <text class="fp-paywall-banner-btn-text">立即解锁</text>
            <text class="fp-paywall-banner-btn-arrow">→</text>
          </view>
        </view>
        <view class="fp-paywall-banner-tip">7 天内不满意全额退款 · 支付即视为同意《付费服务协议》</view>
      </view>

      <!-- 报告头（深蓝渐变） -->
      <view class="fp-hero">
        <!-- v7 增量：顶部返回 + 标题（颗粒度优化：紧贴顶部 24rpx，玻璃质感） -->
        <view class="fp-nav-bar">
          <view class="fp-nav-back" @tap="goBack">
            <text class="fp-nav-back-arrow">‹</text>
          </view>
          <view class="fp-nav-title">免费预览</view>
          <!-- 顶部 nav 不再放客服按钮（避免和右下 fp-ai-fab 重复），留 56rpx 占位平衡布局 -->
          <view class="fp-nav-spacer" />
        </view>
        <view class="fp-hero-eyebrow">CREDIT REPORT</view>
        <view class="fp-hero-line" />
        <view class="fp-hero-no">报告编号 · {{ result.report_no }}</view>
        <view class="fp-hero-time">生成时间 · {{ formatTime(result.created_at) }}</view>
      </view>

      <!-- 1. 一句话结论（按 overall 级别给颜色） -->
      <view v-if="result.one_sentence" class="fp-verdict" :class="'fp-verdict-' + levelClass">
        <view class="fp-verdict-icon">
          <UiIcon :name="verdictIcon" :size="40" :color="verdictColor" />
        </view>
        <view class="fp-verdict-body">
          <view class="fp-verdict-eyebrow">模拟评审结论</view>
          <view class="fp-verdict-text" :style="{ color: verdictColor }">
            {{ result.one_sentence }}
          </view>
        </view>
      </view>

      <!-- 2. 评分环（圆形，居中） -->
      <view class="fp-score-card">
        <view class="fp-score-eyebrow">OVERALL SCORE</view>
        <view class="fp-score-wrap">
          <svg class="fp-score-svg" viewBox="0 0 100 100">
            <circle class="fp-score-bg" cx="50" cy="50" r="42" />
            <circle
              class="fp-score-fill"
              cx="50" cy="50" r="42"
              :stroke="levelCfg.color"
              :stroke-dasharray="`${(result.overall.score / 100) * 264} 264`"
            />
          </svg>
          <view class="fp-score-center">
            <view class="fp-score-num" :style="{ color: levelCfg.color }">
              {{ result.overall.score }}
            </view>
            <view class="fp-score-unit">SCORE</view>
          </view>
        </view>
        <view class="fp-score-meta">
          <view class="fp-score-level" :style="{ color: levelCfg.color, borderColor: levelCfg.color }">
            {{ result.overall.level }} · {{ levelCfg.desc }}
          </view>
          <view class="fp-score-pass">
            <text class="fp-score-pass-label">综合通过率</text>
            <text
              class="fp-score-pass-val"
              :style="{ color: PASS_PROB_COLOR[result.overall.pass_probability] || '#666' }"
            >{{ result.overall.pass_probability }}</text>
          </view>
        </view>
        <view class="fp-score-amount">
          <text class="fp-amount-label">模拟额度</text>
          <text class="fp-amount-val">{{ formatLimit(result.overall.limit_min, result.overall.limit_max) }}</text>
        </view>
      </view>

      <!-- v7 增量：银行评估侧重点（每家银行评分机制不同） -->
      <view v-if="result.bank_focus" class="fp-bank-focus">
        <view class="fp-bank-focus-head">
          <text class="fp-bank-focus-eyebrow">EVALUATION FOCUS</text>
          <text class="fp-bank-focus-title">{{ result.bank_name }} 评估侧重点</text>
          <text class="fp-bank-focus-slogan">{{ result.bank_focus }}</text>
        </view>
        <view v-if="result.bank_key_tags && result.bank_key_tags.length" class="fp-bank-focus-tags">
          <text v-for="(t, i) in result.bank_key_tags" :key="i" class="fp-bank-focus-tag">{{ t }}</text>
        </view>
        <view class="fp-bank-focus-foot">
          <text class="fp-bank-focus-foot-eyebrow">本报告已按该银行模型调权</text>
        </view>
      </view>

      <!-- 3. 1 个核心问题（最高严重度） -->
      <view v-if="result.top_issue_free" class="fp-issue-card" :style="{ borderLeftColor: result.top_issue_free.severity_color }">
        <!-- v9 增量：1/N 严重问题进度条（心锚：让用户感知"还有 N-1 个被锁"） -->
        <view class="fp-issue-progress">
          <text class="fp-issue-progress-eyebrow">CORE ISSUE</text>
          <text class="fp-issue-progress-text">第 <text class="fp-issue-progress-num">1</text> / {{ result.top_issues_total || 1 }} 个严重问题</text>
        </view>
        <view class="fp-issue-progress-bar">
          <view
            class="fp-issue-progress-fill"
            :style="{
              width: (100 / (result.top_issues_total || 1)) + '%',
              background: result.top_issue_free.severity_color
            }"
          />
        </view>
        <view class="fp-issue-head">
          <view class="fp-issue-tag" :style="{ background: result.top_issue_free.severity_color }">
            {{ severityLabel(result.top_issue_free.severity) }} · 核心问题
          </view>
          <view class="fp-issue-cat">{{ result.top_issue_free.category }}</view>
        </view>
        <view class="fp-issue-title">{{ result.top_issue_free.title }}</view>
        <view class="fp-issue-impact">
          <view class="fp-issue-impact-row">
            <text class="fp-impact-icon">↓</text>
            <text class="fp-impact-text">{{ result.top_issue_free.impact_prob }}</text>
          </view>
          <view v-if="result.top_issue_free.impact_amount && result.top_issue_free.impact_amount !== '—'" class="fp-issue-impact-row">
            <text class="fp-impact-icon">↓</text>
            <text class="fp-impact-text">{{ result.top_issue_free.impact_amount }}</text>
          </view>
        </view>
        <!-- v4 增量 M2：5 要素展开（free 版只露 what/why/impact/how 简化版） -->
        <view v-if="result.top_issue_free.what" class="fp-issue-5w">
          <view class="fp-issue-5w-row">
            <text class="fp-issue-5w-tag">WHAT</text>
            <text class="fp-issue-5w-text">{{ result.top_issue_free.what }}</text>
          </view>
          <view v-if="result.top_issue_free.why" class="fp-issue-5w-row">
            <text class="fp-issue-5w-tag">WHY</text>
            <text class="fp-issue-5w-text">{{ result.top_issue_free.why }}</text>
          </view>
          <view class="fp-issue-5w-row">
            <text class="fp-issue-5w-tag">HOW</text>
            <text class="fp-issue-5w-text">{{ result.top_issue_free.how || '请查看完整报告了解详细改善路径' }}</text>
          </view>
        </view>
        <!-- v9 增量：末 1/3 渐隐遮罩 + 锁标浮层（最强心锚：内容只露 2/3，剩下被锁） -->
        <view v-if="(result.top_issues_total || 1) > 1" class="fp-issue-locked">
          <view class="fp-issue-locked-fade" />
          <view class="fp-issue-locked-overlay" @tap="goPay">
            <view class="fp-issue-locked-icon-row">
              <text class="fp-issue-locked-icon">🔒</text>
              <text class="fp-issue-locked-title">解锁完整报告</text>
            </view>
            <text class="fp-issue-locked-sub">查看其余 {{ (result.top_issues_total || 1) - 1 }} 个核心问题深度分析 + 改善路径</text>
          </view>
        </view>
      </view>

      <!-- 3.5 改善后推演（v9 增量：整张虚化 + 锁标浮层） -->
      <view v-if="result.improvement_projection" class="fp-projection-card fp-projection-locked">
        <view class="fp-projection-content">
          <view class="fp-proj-eyebrow">AFTER 90 DAYS · 改善后预计</view>
          <view class="fp-proj-arrow">
            <view class="fp-proj-col">
              <text class="fp-proj-label">当前</text>
              <text class="fp-proj-val" :style="{ color: levelCfg.color }">
                {{ result.overall.level }} · {{ result.overall.score }}分
              </text>
              <text class="fp-proj-meta">通过率 {{ result.overall.pass_probability }}</text>
            </view>
            <view class="fp-proj-arrow-icon">→</view>
            <view class="fp-proj-col fp-proj-col-after">
              <text class="fp-proj-label">改善后</text>
              <text class="fp-proj-val" :style="{ color: PASS_PROB_COLOR[result.improvement_projection.pass_probability] || '#666' }">
                {{ result.improvement_projection.level }} · {{ result.improvement_projection.score }}分
              </text>
              <text class="fp-proj-meta">通过率 {{ result.improvement_projection.pass_probability }}</text>
            </view>
          </view>
          <view class="fp-proj-foot">
            💡 修复 {{ result.improvement_projection.fixed_count }} 个核心问题后预计可达
          </view>
        </view>
        <!-- v9 增量：整张虚化 + 中心锁标浮层（最强心锚：能看见但看不清，必须解锁） -->
        <view class="fp-projection-overlay" @tap="goPay">
          <view class="fp-projection-lock-card">
            <text class="fp-projection-lock-icon">🔒</text>
            <text class="fp-projection-lock-title">解锁 30/60/90 天路径</text>
            <text class="fp-projection-lock-sub">查看完整改善推演 + 分阶段动作</text>
          </view>
        </view>
      </view>

      <!-- 4. 6 大产品独立模拟结果（v9 重做：每产品独立色+icon+等级+基础分+blur 证据链）
           设计原则（C1 决策）：每张卡一眼看出产品名/等级/分数，证据链字段（命中规则/扣分/提分/实际可贷）blur 8rpx 模糊
           锁浮动在卡底部，不在第 6 个专属——所有 6 张都模糊，让"解锁=清晰"成为统一钩子 -->
      <view class="fp-products-card">
        <view class="fp-products-head">
          <text class="fp-products-eyebrow">PRODUCTS COMPARE</text>
          <text class="fp-products-title">各产品独立模拟结果</text>
        </view>
        <view
          v-for="p in result.product_results"
          :key="p.product_code"
          :class="['fp-product-wrap', p.product_code]"
        >
          <!-- 顶部条：icon + 产品名 + 等级 chip -->
          <view class="fp-product-head">
            <view class="fp-product-icon">{{ getProductColor(p.product_code).icon }}</view>
            <view class="fp-product-head-body">
              <view class="fp-product-name">{{ p.product_name }}</view>
              <view v-if="p.product_subtitle" class="fp-product-sub">{{ p.product_subtitle }}</view>
            </view>
            <view
              v-if="p.level"
              class="fp-product-level-chip"
              :style="{
                color: getLevelColor(p.level).color,
                background: getLevelColor(p.level).bg,
                borderColor: getLevelColor(p.level).color,
              }"
            >
              {{ p.level }} · {{ getLevelColor(p.level).label }}
            </view>
          </view>

          <!-- 基础分大数字（不模糊，全卡唯一清晰指标） -->
          <view class="fp-product-score">
            <view class="fp-product-score-num" :style="{ color: getProductColor(p.product_code).color }">
              {{ p.score }}
            </view>
            <view class="fp-product-score-unit">基础分</view>
            <view v-if="p.pass_probability" class="fp-product-score-pass">通过率 {{ p.pass_probability }}</view>
          </view>

          <!-- 模拟额度（核心数据，但免费版锁——解锁后显示） -->
          <view class="fp-product-limit">
            <view class="fp-product-limit-label">模拟额度</view>
            <view class="fp-product-limit-val" :style="{ color: getProductColor(p.product_code).color }">
              {{ formatLimit(p.realistic_limit_min || p.limit_min, p.realistic_limit_max || p.limit_max) }}
            </view>
          </view>

          <!-- 证据链 blur 区（解锁后清晰可见，免费版模糊遮罩） -->
          <view class="fp-product-evidence fp-product-evidence-locked">
            <!-- 命中规则（高分） -->
            <view v-if="p.hit_rules && p.hit_rules.length" class="fp-ev-block">
              <view class="fp-ev-label">✓ 命中加分</view>
              <view v-for="(r, k) in p.hit_rules" :key="k" class="fp-ev-row">
                <text class="fp-ev-rule">{{ r.rule }}</text>
                <text class="fp-ev-score" :style="{ color: getProductColor(p.product_code).color }">+{{ r.score }}</text>
              </view>
            </view>
            <!-- 扣分规则（低分） -->
            <view v-if="p.low_rules && p.low_rules.length" class="fp-ev-block">
              <view class="fp-ev-label">✗ 扣分项</view>
              <view v-for="(r, k) in p.low_rules" :key="k" class="fp-ev-row">
                <text class="fp-ev-rule">{{ r.rule }}</text>
                <text class="fp-ev-score fp-ev-score-neg">{{ r.score }}</text>
              </view>
            </view>
            <!-- 不推荐原因 -->
            <view v-if="p.not_recommend_reason" class="fp-ev-block">
              <view class="fp-ev-label">⚠ 不推荐原因</view>
              <view class="fp-ev-reason">{{ p.not_recommend_reason }}</view>
            </view>
            <!-- 提分变量 -->
            <view v-if="p.improve_vars && p.improve_vars.length" class="fp-ev-block">
              <view class="fp-ev-label">↑ 提分建议</view>
              <view v-for="(v, k) in p.improve_vars" :key="k" class="fp-ev-row">
                <text class="fp-ev-rule">{{ v.current }} → {{ v.best }}</text>
                <text class="fp-ev-score" :style="{ color: getProductColor(p.product_code).color }">+{{ v.delta }}</text>
              </view>
            </view>
            <!-- 实际可贷金额 -->
            <view class="fp-ev-block">
              <view class="fp-ev-label">¥ 实际可贷</view>
              <view class="fp-ev-reason">
                测算金额 × 等级折扣 + 渠道 cap 后预估
              </view>
            </view>
          </view>

          <!-- 锁标浮层（统一在每张卡底部，引导解锁） -->
          <view v-if="!result.is_paid" class="fp-product-locked-overlay" @tap.stop="goPay">
            <text class="fp-product-locked-icon">🔒</text>
            <text class="fp-product-locked-text">解锁查看 {{ p.product_name }} 完整证据链</text>
            <text class="fp-product-locked-sub">¥{{ siteStore.payPrice }} · 一次解锁全部 6 大产品</text>
          </view>
        </view>
      </view>

      <!-- 5. 极简金线 CTA（v9 增量：D3 决策 — 半透明白底 + 金线 + 9.9 + 箭头） -->
      <view v-if="!result.is_paid" class="fp-cta" @tap="goPay">
        <view class="fp-cta-line">
          <view class="fp-cta-left">
            <text class="fp-cta-eyebrow">UNLOCK FULL REPORT</text>
            <view class="fp-cta-price-row">
              <text class="fp-cta-price-num">¥{{ siteStore.payPrice }}</text>
              <text class="fp-cta-price-go">查看完整报告</text>
            </view>
          </view>
          <text class="fp-cta-arrow">→</text>
        </view>
        <text class="fp-cta-tip">7 天内不满意全额退款</text>
      </view>

      <!-- 免责声明 -->
      <view class="fp-disclaimer">
        <text class="fp-disc-title">关于本报告</text>
        <text class="fp-disc-line">{{ siteStore.disclaimerFullReport || defaultDisclaimer }}</text>
      </view>

      <!-- v6 修复：底部导航区（之前 free 报告出来只看到"支付"按钮，不付钱就没出口，
           用户只能按物理返回键，UX 极差。加"返回首页"+"查看我的报告"两个按钮） -->
      <view class="fp-footer-nav">
        <button class="fp-foot-btn fp-foot-btn-secondary" @tap="goHome">返回首页</button>
        <button class="fp-foot-btn fp-foot-btn-primary" @tap="goHistory">查看我的报告</button>
      </view>

      <!-- ========== v4 增量 · M7 分享卡（屏幕外 canvas 渲染） ========== -->
      <view class="fp-share-stage">
        <canvas
          canvas-id="shareCanvasId"
          id="shareCanvasId"
          class="fp-share-canvas"
          :style="{ width: shareCanvasW + 'px', height: shareCanvasH + 'px' }"
        ></canvas>
      </view>

      <!-- ========== v4 增量 · M10 跨行快选 ========== -->
      <view v-if="compareBanks.length || compareLoading" class="fp-m10-card">
        <view class="fp-m10-head">
          <text class="fp-m10-eyebrow">07 / COMPARE</text>
          <text class="fp-m10-title">换家银行试试 · 1v1 快速对比</text>
        </view>
        <view v-if="compareLoading" class="fp-m10-loading">加载其他银行中…</view>
        <scroll-view v-else class="fp-m10-scroll" scroll-x>
          <view class="fp-m10-list">
            <view
              v-for="b in compareBanks"
              :key="b.code"
              class="fp-m10-cand"
              @tap="pickBank(b.code)"
            >
              <view class="fp-m10-cand-tag">候选</view>
              <view class="fp-m10-cand-name">{{ b.name }}</view>
              <view v-if="topProductMatch(b.products)" class="fp-m10-cand-top">
                <view class="fp-m10-cand-row"><text>推荐产品</text><b>{{ topProductMatch(b.products)!.name }}</b></view>
                <view class="fp-m10-cand-row"><text>额度</text><b>{{ topProductMatch(b.products)!.limit_min }}-{{ topProductMatch(b.products)!.limit_max }} 万</b></view>
                <view class="fp-m10-cand-row"><text>利率</text><b>{{ topProductMatch(b.products)!.rate_min }}-{{ topProductMatch(b.products)!.rate_max }}%</b></view>
                <view class="fp-m10-cand-row"><text>准入分</text><b>≥{{ topProductMatch(b.products)!.pass_score_min }}</b></view>
                <view class="fp-m10-cand-idx">预估匹配度 <text class="fp-m10-cand-idx-num">{{ Math.round(topProductMatch(b.products)!._idx) }}</text>/100</view>
              </view>
              <view class="fp-m10-cand-go">→ 用这家重测</view>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- ========== v9 增量 · 客服浮窗低调化（去 ONLINE + 半透明白底 + 下移 + 金描边） ========== -->
      <view class="fp-ai-fab" @tap="chatOpen = !chatOpen">
        <view class="fp-ai-fab-dot" />
        <text class="fp-ai-fab-txt">客服</text>
      </view>
      <view v-if="chatOpen" class="fp-ai-mask" @tap="chatOpen = false"></view>
      <view v-if="chatOpen" class="fp-ai-panel">
        <view class="fp-ai-head">
          <view>
            <view class="fp-ai-eyebrow">客服 · ONLINE</view>
            <view class="fp-ai-title">{{ result.bank_name || '银行专家' }} 评估顾问</view>
          </view>
          <text class="fp-ai-close" @tap="chatOpen = false">×</text>
        </view>
        <scroll-view class="fp-chat-body" scroll-y scroll-into-view="chat-bottom">
          <view v-if="!chatMsgs.length" class="fp-chat-empty">
            <view class="fp-chat-empty-t">试试问我</view>
            <view class="fp-chat-quick">
              <text v-for="(q, i) in QUICK_QS" :key="i" class="fp-chat-q" @tap="sendChat(q)">{{ q }}</text>
            </view>
          </view>
          <view v-for="(m, i) in chatMsgs" :key="i" :class="['fp-chat-msg', 'fp-chat-' + m.role]">
            <view class="fp-chat-bubble">{{ m.text }}</view>
          </view>
          <view v-if="chatThinking" class="fp-chat-msg fp-chat-ai">
            <view class="fp-chat-bubble fp-chat-dot"><text></text><text></text><text></text></view>
          </view>
          <view id="chat-bottom"></view>
        </scroll-view>
        <view class="fp-ai-foot">
          <input v-model="chatInput" class="fp-ai-input" placeholder="输入你的问题…" confirm-type="send" @confirm="sendChat()" />
          <button class="fp-ai-send" @tap="sendChat()">发送</button>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import ProductCard from '@/components/product-card/ProductCard.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { getFreeResult, getCompareSnapshot, type FreeResultRes } from '@/api/assessment'
import { useSiteStore } from '@/store/site'
import { useUserStore } from '@/store/user'
import { useAssessmentStore } from '@/store/assessment'
import { listBanks, getBankProducts, type Bank, type BankProduct } from '@/api/bank'
import { getProductColor, getLevelColor } from '@/utils/productConfig'

// v9 增量：6 卡独立色绑定（用 computed 风格的 helper，给 :style 绑定 product_code 派生的色/边）
function productCardStyle(code: string) {
  const c = getProductColor(code)
  return {
    borderLeftColor: c.color,
    '--pc-color': c.color,
    '--pc-bg': c.bg,
    '--pc-text': c.text,
  } as any
}

const siteStore = useSiteStore()
const loading = ref(true)
const result = ref<FreeResultRes | null>(null)
const assessmentId = ref<number>(0)

// v8 重构：极致简约配色 - 全屏只保留 4 色（深蓝/金/灰/白）
// 之前：A=绿/B=蓝/C=橙/D=红/E=灰 5 色饱和度太高，和深蓝金奢华风冲突
// 现在：S=金棕（最亮）→ A=金 → B=暗金 → C=深灰 → D=暗棕 → E=中灰（单色阶）
const LEVEL_CONFIG_FALLBACK: Record<string, { color: string; desc: string }> = {
  S: { color: '#8E6F2C', desc: '极佳' },
  A: { color: '#C9A96E', desc: '优秀' },
  B: { color: '#8B7E5E', desc: '良好' },
  C: { color: '#6B7280', desc: '一般' },
  D: { color: '#4A4A4A', desc: '较弱' },
  E: { color: '#5C6B7C', desc: '极弱' },
}
const LEVEL_CONFIG = computed<Record<string, { color: string; desc: string }>>(() => {
  const cfg = result.value?.ui_config?.level_config
  return (cfg as any) || LEVEL_CONFIG_FALLBACK
})
// v8 极简：通过率从 5 色改成 3 色（金/中灰/暗棕）
const PASS_PROB_COLOR: Record<string, string> = {
  '高': '#C9A96E',
  '中高': '#B89554',
  '中': '#8B7E5E',
  '低': '#6B7280',
  '极低': '#4A4A4A',
}

const levelCfg = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  return LEVEL_CONFIG.value[lv] || LEVEL_CONFIG.value['E']
})

// 一句话结论的视觉风格
const levelClass = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return 'good'
  if (lv === 'B' || lv === 'C') return 'mid'
  return 'bad'  // D/E
})

const verdictIcon = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return 'check'
  if (lv === 'B' || lv === 'C') return 'info'
  return 'warning'
})

const verdictColor = computed(() => {
  const lv = result.value?.overall?.level || 'E'
  // v8 极简：去绿色 + 去红色，统一金色阶
  if (lv === 'S' || lv === 'A') return '#8E6F2C'   // S/A 用古铜金（最显眼）
  if (lv === 'B' || lv === 'C') return '#C9A96E'   // B/C 用香槟金
  return '#6B7280'                                  // D/E 用暖灰（不再刺眼红）
})

function severityLabel(sev: string): string {
  if (sev === 'high') return '高严重度'
  if (sev === 'mid') return '中严重度'
  return '低严重度'
}

const defaultDisclaimer = `本报告由信测通模拟评审模型生成。模型逻辑参考银行信用贷审批框架，由 50+ 位资深金融分析师与一线信贷从业者参与校准。累计 20,000+ 真实案例回测验证。\n本报告基于您主动填写的信息进行模拟分析，所有评分、额度、利率、通过概率均为虚拟计算结果，不代表任何银行或金融机构的真实授信，不构成贷款承诺、投资建议或法律意见。\n实际审批结果受银行政策、市场环境、个人资质等多因素影响，可能与模拟结果存在差异。\n请勿将本报告作为贷款申请的唯一依据。`

onMounted(async () => {
  const pages = getCurrentPages()
  const page = pages[pages.length - 1] as any
  const id = (page.options?.id || page.$route?.query?.id) as string
  assessmentId.value = parseInt(id, 10) || 0

  if (!assessmentId.value) {
    loading.value = false
    return
  }

  try {
    result.value = await getFreeResult(assessmentId.value)
    // v6 一致性：与 web 端校验 data_hash，发现不一致提示刷新
    if (result.value?.data_hash) {
      try {
        const snap = await getCompareSnapshot(assessmentId.value)
        if (snap?.data_hash && snap.data_hash !== result.value!.data_hash) {
          uni.showToast({ title: '数据已更新，建议刷新', icon: 'none' })
        }
      } catch {}
    }
  } catch (e) {
    console.error('加载免费结果失败', e)
  } finally {
    loading.value = false
  }

  siteStore.load()
  // v4 增量 M10：异步加载对比银行
  loadCompare()
})

function formatTime(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatLimit(min?: number, max?: number) {
  if (!min && !max) return '—'
  if (!min) return `${(max || 0) / 10000} 万`
  if (!max) return `${min / 10000} 万`
  return `${min / 10000}-${max / 10000} 万`
}

// ========== v4 增量 · M6 产品匹配度（与 web 端同源：r.product_matches 优先，本地兜底） ==========
const productMatch = (p: any) => {
  const r: any = result.value
  if (!r) return { idx: 0, gap: 0, tips: ['数据未就绪'] as string[] }
  const matches: any[] = r.product_matches || []
  const m = matches.find((x: any) => x.product_code === (p.code || p.product_code))
  if (m) return { idx: m.match_idx, gap: m.gap, tips: m.tips || [] }
  const score = r.overall?.score || 0
  const minReq = p.pass_score_min || 0
  const gap = Math.max(0, minReq - score)
  const idx = Math.max(0, Math.min(100, 100 - gap * 1.2))
  return { idx: Math.round(idx), gap, tips: gap > 0 ? [`分数差 ${gap} 分`] : ['当前资质可直接申请'] }
}
function matchColor(idx: number): string {
  // v8 极简：匹配度颜色全金色系
  if (idx >= 80) return 'linear-gradient(90deg, #8E6F2C 0%, #C9A96E 100%)'
  if (idx >= 60) return 'linear-gradient(90deg, #C9A96E 0%, #B89554 100%)'
  if (idx >= 40) return 'linear-gradient(90deg, #8B7E5E 0%, #6B7280 100%)'
  return 'linear-gradient(90deg, #4A4A4A 0%, #2F2F2F 100%)'
}

// ========== v4 增量 · M7 分享卡（uniapp Canvas 2D 绘制） ==========
const shareCanvasW = ref(750)  // 设计稿宽度（按 px 计算，rpx 转 px 由调用方处理）
const shareCanvasH = ref(1000) // 设计稿高度
const generating = ref(false)
async function genShare() {
  if (!result.value) {
    uni.showToast({ title: '数据未就绪', icon: 'none' })
    return
  }
  generating.value = true
  try {
    // #ifdef H5
    // H5 端：直接跳到长图预览（用 dataURL canvas 截图）
    // H5 Canvas 2D API 可直接调用 toDataURL
    await renderShareCanvas()
    uni.showToast({ title: 'H5 端请长按图片保存', icon: 'none', duration: 3000 })
    // #endif
    // #ifndef H5
    await renderShareCanvas()
    // 小程序端：调用 uni.canvasToTempFilePath 保存到相册
    uni.canvasToTempFilePath({
      canvasId: 'shareCanvasId',
      success: (res) => {
        uni.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => uni.showToast({ title: '图片已保存到相册', icon: 'success' }),
          fail: () => uni.showToast({ title: '保存失败，请截图分享', icon: 'none' }),
        })
      },
      fail: () => uni.showToast({ title: '生成失败', icon: 'none' }),
    })
    // #endif
  } catch (e: any) {
    uni.showToast({ title: '生成失败：' + (e?.message || '未知错误'), icon: 'none' })
  } finally {
    generating.value = false
  }
}

function renderShareCanvas(): Promise<void> {
  return new Promise((resolve, reject) => {
    // 平台分支：H5 用标准 Canvas2D context；小程序用 uni.createCanvasContext
    // 用 let 单一变量 + 各自条件块赋值，下方绘图代码共用 ctx（避免 ctxH5/ctxMini 重复声明）
    let ctx: any
    // #ifdef H5
    const canvas: any = document.getElementById('shareCanvasId')
    if (!canvas) return reject(new Error('canvas not found'))
    ctx = canvas.getContext('2d') as CanvasRenderingContext2D
    // #endif
    // #ifndef H5
    ctx = uni.createCanvasContext('shareCanvasId')
    if (!ctx) return reject(new Error('ctx not found'))
    // #endif
    const r: any = result.value
    const lv = r.overall?.level || 'E'
    const levelColor = LEVEL_CONFIG.value[lv]?.color || '#0F1B2D'
    const W = shareCanvasW.value
    const H = shareCanvasH.value

    // 背景：深蓝渐变
    const grd = ctx.createLinearGradient(0, 0, W, H)
    grd.addColorStop(0, '#0B2545')
    grd.addColorStop(1, '#061A33')
    ctx.fillStyle = grd
    ctx.fillRect(0, 0, W, H)

    // 金色装饰线
    ctx.fillStyle = '#C9A96E'
    ctx.fillRect(W / 2 - 30, 60, 60, 2)
    ctx.fillRect(W / 2 - 50, 70, 100, 1)

    // 头部 eyebrow
    ctx.fillStyle = '#C9A96E'
    ctx.font = '500 18px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('CREDIT ASSESSMENT · 信测通银行画像', W / 2, 110)

    // 银行名（截取前 2 字）
    const bankName = (r.bank_name || '').slice(0, 4) || '专属画像'
    ctx.fillStyle = '#FFFFFF'
    ctx.font = '600 32px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText(`${bankName} · 您的专属画像`, W / 2, 160)

    // 报告编号
    ctx.fillStyle = 'rgba(255,255,255,0.5)'
    ctx.font = '400 16px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText(`报告编号 · ${r.report_no || ''}`, W / 2, 195)

    // 金线
    ctx.fillStyle = '#C9A96E'
    ctx.fillRect(60, 240, W - 120, 1)

    // 一句话结论
    ctx.fillStyle = '#FFFFFF'
    ctx.font = '600 36px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    const verdict = r.one_sentence || r.free_summary || '请完成测评查看结论'
    // 简易换行
    const lines = wrapText(ctx, verdict, W - 120, 36)
    let y = 320
    for (const line of lines.slice(0, 3)) {
      ctx.fillText(line, W / 2, y)
      y += 50
    }

    // 3 格指标（等级 / 分数 / 通过率）
    const cells = [
      { lbl: '等级', val: lv, color: levelColor },
      { lbl: '分数', val: String(r.overall?.score ?? 0), color: '#FFFFFF' },
      { lbl: '通过率', val: r.overall?.pass_probability || '—', color: '#C9A96E' },
    ]
    const cellW = (W - 120 - 40) / 3
    cells.forEach((c, i) => {
      const x = 60 + i * (cellW + 20)
      ctx.strokeStyle = 'rgba(201,169,110,0.4)'
      ctx.lineWidth = 1
      ctx.strokeRect(x, 540, cellW, 120)
      ctx.fillStyle = 'rgba(255,255,255,0.6)'
      ctx.font = '400 16px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(c.lbl, x + cellW / 2, 575)
      ctx.fillStyle = c.color
      ctx.font = '700 48px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
      ctx.fillText(c.val, x + cellW / 2, 630)
    })

    // 额度
    ctx.fillStyle = 'rgba(255,255,255,0.7)'
    ctx.font = '400 18px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    const limMin = r.overall?.limit_min || 0
    const limMax = r.overall?.limit_max || 0
    const limText = limMin || limMax
      ? `参考额度 ¥ ${(limMin / 10000).toFixed(1)} ~ ${(limMax / 10000).toFixed(1)} 万 · 利率 ${r.overall?.rate_min || 0}~${r.overall?.rate_max || 0}%`
      : ''
    if (limText) ctx.fillText(limText, W / 2, 720)

    // 金线
    ctx.fillStyle = '#C9A96E'
    ctx.fillRect(60, 800, W - 120, 1)

    // 底部 CTA
    ctx.fillStyle = '#FFFFFF'
    ctx.font = '500 22px "PingFang SC", sans-serif'
    ctx.fillText('扫码测一测你的专属画像', W / 2, 870)
    ctx.fillStyle = '#C9A96E'
    ctx.font = '500 18px -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText('信测通 · 银行画像测评', W / 2, 910)

    // #ifdef H5
    // H5 立即 resolve（用户可右键保存）
    setTimeout(resolve, 100)
    // #endif
    // #ifndef H5
    ctx.draw(false, () => setTimeout(resolve, 200))
    // #endif
  })
}

function wrapText(ctx: any, text: string, maxWidth: number, fontSize: number): string[] {
  // 简易按字符截断（中文 2 字符宽）
  const lines: string[] = []
  let line = ''
  for (const ch of text) {
    const test = line + ch
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line)
      line = ch
    } else {
      line = test
    }
  }
  if (line) lines.push(line)
  return lines
}

// ========== v4 增量 · M8 AI 浮动咨询（本地关键词路由，零 API 成本） ==========
const chatOpen = ref(false)
const chatMsgs = ref<{ role: 'user' | 'ai'; text: string }[]>([])
const chatInput = ref('')
const chatThinking = ref(false)
// v7 增量：客服话术（更亲民，去 AI 感）
const QUICK_QS = [
  '我这种情况能过吗？',
  '你们客服评估多久出结果？',
  '怎么提高通过率？',
  '现在申请哪个产品最稳？',
  'D+90 后能改善多少？',
  '这家银行和别家有啥不一样？',
]

// v7 增量：顶部返回按钮
function goBack() {
  const pages = getCurrentPages() as any[]
  if (pages.length > 1) {
    uni.navigateBack({ delta: 1 })
  } else {
    // 当前栈只有 free 一个，回到首页
    uni.reLaunch({ url: '/pages/index/index' })
  }
}

function aiAnswer(q: string): string {
  const r: any = result.value
  if (!r) return '亲，请先完成测评哦~'
  const lv = r.overall?.level || 'E'
  const issue = r.top_issue_free
  // v7 增量：客服亲民口吻（前缀用"亲"或"小信"）
  if (/多久|时间|评估|等/.test(q)) {
    return '亲~ 本报告是实时计算秒级出结果的哦。完整版报告下单后立即解锁，AI 专家团 24h 内人工复核。'
  }
  if (/通过率|提高|怎么|如何|能过吗/.test(q)) {
    if (issue) return `亲，${lv} 级主要问题：${issue.title}。${issue.how || ''} 按 30/60/90 节奏落地，3 个月可升至下一档~`
    return `亲~ ${lv} 级建议先修复主要风险项，再发起申请，成功率会高很多哦。`
  }
  if (/申请|产品|哪个|合适|最稳/.test(q)) {
    const list: any[] = r.product_results || []
    const top = list.find(p => p.best_for_user) || list[0]
    if (!top) return '亲~ 当前没有匹配产品，先优化资质再申请更稳。'
    const m = productMatch(top)
    return `亲，推荐「${top.product_name}」匹配度 ${m.idx}/100。${(m.tips || []).join('；') || '建议优先申请'}.`
  }
  if (/90|改善|提升|预测/.test(q)) {
    const p = r.improvement_projection
    if (!p) return '亲~ 改善数据未生成，请查看完整报告。'
    return `亲，按当前修复节奏，90 天后等级预计从 ${lv} 升至 ${p.level}，参考额度可达 ${(p.limit_min/10000).toFixed(1)}~${(p.limit_max/10000).toFixed(1)} 万，通过率 ${p.pass_probability}。`
  }
  if (/现在|该不该|立刻|不同|不一样|别家/.test(q)) {
    if (['S', 'A', 'B'].includes(lv)) return `亲~ ${lv} 级属于准入优秀，可立即提交申请，本银行 ${r.bank_focus || '审批流程完善'}。`
    return `亲，${lv} 级建议先修复 top issue 再申请哦，强行申请会留硬查询记录，得不偿失~`
  }
  return '亲，关于这份报告还有其他问题吗？客服小信 9:00-22:00 在线~'
}

function sendChat(q?: string) {
  const text = (q || chatInput.value).trim()
  if (!text) return
  chatMsgs.value.push({ role: 'user', text })
  chatInput.value = ''
  chatThinking.value = true
  setTimeout(() => {
    chatMsgs.value.push({ role: 'ai', text: aiAnswer(text) })
    chatThinking.value = false
  }, 600)
}

// ========== v4 增量 · M10 跨行快选 ==========
const compareBanks = ref<{ code: string; name: string; products: BankProduct[] }[]>([])
const compareLoading = ref(false)

async function loadCompare() {
  if (compareBanks.value.length) return
  compareLoading.value = true
  try {
    const userStore = useUserStore()
    const assessmentStore = useAssessmentStore()
    const list: any = await listBanks()
    // 过滤当前银行（用 assessmentId 反查 bank_code 不便，先随机取 2 个）
    const others: Bank[] = (list.items || []).slice(0, 3)
    const arr: { code: string; name: string; products: BankProduct[] }[] = []
    for (const b of others) {
      try {
        const ps: any = await getBankProducts(b.code, assessmentStore.type)
        arr.push({ code: b.code, name: b.name, products: ps.items || [] })
      } catch {}
    }
    compareBanks.value = arr
  } catch (e) {
    // 静默失败
  } finally {
    compareLoading.value = false
  }
}

function topProductMatch(ps: BankProduct[]): (BankProduct & { _idx: number }) | null {
  if (!ps.length) return null
  const r: any = result.value
  const score = r?.overall?.score || 0
  return ps.map((p: any) => {
    const gap = Math.max(0, (p.pass_score_min || 0) - score)
    return { ...p, _idx: Math.max(0, Math.min(100, 100 - gap * 1.2)) }
  }).sort((a, b) => b._idx - a._idx)[0] as any
}

function pickBank(code: string) {
  uni.showToast({ title: '已切换到 ' + code + '，请重新测评', icon: 'none' })
  setTimeout(() => {
    uni.redirectTo({ url: `/pages/assess/select-bank?bank=${code}` })
  }, 800)
}

function goPay() {
  uni.navigateTo({ url: `/pages/result/pay?id=${assessmentId.value}` })
}

// v6 修复：报告页底部导航（返回首页 / 查看我的报告）
function goHome() {
  // switchTab 是跳到 tabBar 页（首页在 tabBar）的标准方式，会清空非 tabBar 页面栈
  uni.switchTab({
    url: '/pages/index/index',
    fail: () => {
      // 兜底：如果首页不是 tabBar，就 reLaunch
      uni.reLaunch({ url: '/pages/index/index' })
    },
  })
}
function goHistory() {
  // 查看我的报告（mine 历史）
  uni.switchTab({
    url: '/pages/mine/index',
    fail: () => {
      uni.navigateTo({ url: '/pages/mine/history' })
    },
  })
}
</script>

<style lang="scss" scoped>
/* ============================================
   免费版结果页 · v3.2
   设计风格：奢华金融
   - 深空蓝主色（#0F1B2D）
   - 金色描边（#C9A96E）
   - 大量留白 + 卡片化
   - serif 字体用于数字
   ============================================ */
.free-page {
  min-height: 100vh;
  background: #F5F3EF;
  padding-bottom: 80rpx;
}

/* === 加载态 === */
.loading-state {
  padding: 200rpx 0;
  text-align: center;
}
.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border: 4rpx solid rgba(15, 27, 45, 0.1);
  border-top-color: #0F1B2D;
  border-radius: 50%;
  margin: 0 auto 16rpx;
  animation: spin 1s linear infinite;
}
.loading-text { font-size: 28rpx; color: #8B8B8B; letter-spacing: 1rpx; }
@keyframes spin { to { transform: rotate(360deg); } }

/* === 报告头（深蓝渐变） === */
.fp-hero {
  background: linear-gradient(180deg, #0F1B2D 0%, #1B2A4A 100%);
  /* v7 修复：padding-top 从 48rpx 改 88rpx 让出 nav-bar 高度，避免 eyebrow 和 nav-title 字体重叠 */
  padding: 88rpx 32rpx 56rpx;
  text-align: center;
  color: #FFFFFF;
  position: relative;
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 80rpx;
    height: 2rpx;
    background: #C9A96E;
  }
}
.fp-hero-eyebrow {
  font-family: $ff-base;
  /* v8 调 L：字号 20→18rpx（更精致）+ letter-spacing 4→8rpx（更"展"）+ 字号缩小让英文小标签更"轻" */
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 8rpx;
  font-weight: 500;
  margin-top: 32rpx;
}
.fp-hero-line {
  width: 48rpx;
  height: 1rpx;
  background: rgba(201, 169, 110, 0.4);
  margin: 24rpx auto;
}
/* v8 调 L：合并规则改成单独规则，fp-hero-no 白色 20rpx，fp-hero-time 浅白 20rpx 0.55透明，letter-spacing 1→2rpx */
.fp-hero-no {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.95);
  letter-spacing: 2rpx;
  display: block;
  margin-top: 12rpx;
  font-family: $ff-base;
}
.fp-hero-time {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 2rpx;
  display: block;
  margin-top: 6rpx;
  font-family: $ff-base;
}

/* === 1. 一句话结论（首屏焦点） === */
.fp-verdict {
  background: #FFFFFF;
  margin: -32rpx 32rpx 0;
  padding: 32rpx;
  display: flex;
  gap: 24rpx;
  align-items: center;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-top: 4rpx solid #C9A96E;
  box-shadow: 0 8rpx 24rpx rgba(15, 27, 45, 0.06);
  position: relative;
  z-index: 1;

  /* v8 极简：verdict 顶部条从 3 色改 3 金色阶（去绿去红） */
  &.fp-verdict-good { border-top-color: #8E6F2C; }   /* 极佳 */
  &.fp-verdict-mid  { border-top-color: #C9A96E; }   /* 中等 */
  &.fp-verdict-bad  { border-top-color: #6B7280; }   /* 较差（暖灰，不再刺眼红） */
}
.fp-verdict-icon {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(201, 169, 110, 0.08);
  border-radius: 50%;
  flex-shrink: 0;
}
.fp-verdict-body { flex: 1; min-width: 0; }
/* v8 调 L：verdict-eyebrow 中文标签字号 20→18rpx，letter-spacing 3→2rpx（中文不需要太大间距） */
.fp-verdict-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #8B8B8B;
  letter-spacing: 2rpx;
  margin-bottom: 8rpx;
  display: block;
}
.fp-verdict-text {
  font-family: $ff-base;
  font-size: 34rpx;
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: 1rpx;
}

/* === 2. 评分卡 === */
.fp-score-card {
  background: #FFFFFF;
  margin: 24rpx 32rpx;
  padding: 48rpx 32rpx 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  text-align: center;
}
/* v8 调 L：score-eyebrow 字号 20→18rpx + letter-spacing 4→6rpx（更"展"） */
.fp-score-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 500;
  display: block;
  margin-bottom: 24rpx;
}
.fp-score-wrap {
  position: relative;
  width: 240rpx;
  height: 240rpx;
  margin: 0 auto 24rpx;
}
.fp-score-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.fp-score-bg {
  fill: none;
  stroke: rgba(15, 27, 45, 0.08);
  stroke-width: 2;
}
.fp-score-fill {
  fill: none;
  stroke-width: 2;
  stroke-linecap: butt;
  transition: stroke-dasharray 0.8s ease;
}
.fp-score-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.fp-score-num {
  font-family: $ff-base;
  font-size: 72rpx;
  font-weight: 700;
  letter-spacing: 2rpx;
  line-height: 1;
}
.fp-score-unit {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 4rpx;
  margin-top: 8rpx;
}
.fp-score-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  margin-bottom: 24rpx;
  flex-wrap: wrap;
}
.fp-score-level {
  font-family: $ff-base;
  font-size: 26rpx;
  font-weight: 600;
  padding: 6rpx 20rpx;
  border: 1rpx solid;
  letter-spacing: 2rpx;
}
/* v8 极简：pass 简化为「中点 + 通过率文字」，去掉圆角胶囊背景 */
.fp-score-pass {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  padding: 0;
  background: none;
}
.fp-score-pass-label {
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  font-weight: 400;
}
.fp-score-pass-val {
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 600;
  letter-spacing: 0.5rpx;
}
/* v8 极简：amount 边框淡化（0.06→0.04），font 字号 36→32rpx（更精致） */
.fp-score-amount {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 12rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid rgba(15, 27, 45, 0.04);
}
.fp-amount-label {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  font-weight: 400;
}
.fp-amount-val {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
}

/* === 3. 核心问题卡（强烈刺激付费） === */
.fp-issue-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-left: 6rpx solid #C62828;
  position: relative;
}
.fp-issue-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.fp-issue-tag {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #FFFFFF;
  padding: 4rpx 12rpx;
  letter-spacing: 1rpx;
  font-weight: 600;
}
.fp-issue-cat {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  padding: 2rpx 12rpx;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 4rpx;
}
.fp-issue-title {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 600;
  color: #0F1B2D;
  line-height: 1.4;
  margin-bottom: 20rpx;
  letter-spacing: 1rpx;
}
/* v8 极简：impact 背景从红色 rgba(198,40,40,0.04) 改暖灰 + border 改金色，去除刺眼红色 */
.fp-issue-impact {
  background: rgba(15, 27, 45, 0.03);
  padding: 16rpx 20rpx;
  border-left: 2rpx solid #C9A96E;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-bottom: 16rpx;
}
.fp-issue-impact-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
/* v8 极简：impact icon 从 "↓" 红色 改 "—" 米色，去除符号刺眼感 */
.fp-impact-icon {
  color: #8E6F2C;
  font-weight: 600;
  font-size: 26rpx;
  letter-spacing: 0;
}
.fp-impact-text {
  font-size: 26rpx;
  color: #0F1B2D;
  font-weight: 500;
  letter-spacing: 0.5rpx;
}
/* v8 极简：tip 字号 22→20rpx，去 italic，颜色更淡（暖灰 8B8B8B→A0A0A0） */
.fp-issue-tip {
  font-size: 20rpx;
  color: #A0A0A0;
  letter-spacing: 0.5rpx;
  line-height: 1.6;
  margin-top: 4rpx;
}

/* === v4 M2 5 要素展开 === */
.fp-issue-5w {
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx dashed rgba(15, 27, 45, 0.12);
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.fp-issue-5w-row {
  display: flex;
  gap: 12rpx;
  align-items: flex-start;
}
/* v8 极简：5w 标签 letter-spacing 1→3rpx，字号 20→18rpx（更精致） */
.fp-issue-5w-tag {
  font-family: $ff-base;
  font-size: 18rpx;
  font-weight: 600;
  color: #8E6F2C;
  letter-spacing: 3rpx;
  flex-shrink: 0;
  width: 56rpx;
  padding-top: 4rpx;
}
.fp-issue-5w-text {
  flex: 1;
  font-size: 24rpx;
  color: #0F1B2D;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
}

/* === v9 增量 · 1/N 严重问题进度条（心锚：让用户感知"还有 N-1 个被锁"） === */
.fp-issue-progress {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8rpx;
}
.fp-issue-progress-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #8B8B8B;
  letter-spacing: 4rpx;
  font-weight: 600;
}
.fp-issue-progress-text {
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
}
.fp-issue-progress-num {
  font-family: $ff-base;
  font-size: 26rpx;
  font-weight: 700;
  color: #0F1B2D;
  margin: 0 2rpx;
}
.fp-issue-progress-bar {
  height: 4rpx;
  background: rgba(15, 27, 45, 0.06);
  border-radius: 2rpx;
  overflow: hidden;
  margin-bottom: 20rpx;
}
.fp-issue-progress-fill {
  height: 100%;
  border-radius: 2rpx;
  transition: width 0.6s ease;
}

/* === v9 增量 · 末尾 1/3 渐隐遮罩 + 锁标浮层 === */
.fp-issue-locked {
  position: relative;
  margin: 20rpx -32rpx -32rpx;
  height: 200rpx;
  pointer-events: none;
}
.fp-issue-locked-fade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, #FFFFFF 60%, #FFFFFF 100%);
  pointer-events: none;
}
.fp-issue-locked-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 24rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  pointer-events: auto;
}
.fp-issue-locked-icon-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 4rpx;
}
.fp-issue-locked-icon {
  font-size: 28rpx;
  filter: grayscale(0.3);
}
.fp-issue-locked-title {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
}
.fp-issue-locked-sub {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
  text-align: center;
  line-height: 1.5;
}

/* === 3.5 改善后推演（前后对比） === */
.fp-projection-card {
  background: linear-gradient(135deg, rgba(201, 169, 110, 0.08), rgba(201, 169, 110, 0.04));
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  position: relative;
  overflow: hidden;
}
/* v9 增量：投影卡片虚化容器（最关键样式，让用户"看到"但"看不清"） */
.fp-projection-content {
  filter: blur(6rpx);
  pointer-events: none;
  user-select: none;
  /* 防止虚化导致选择文字 */
  -webkit-user-select: none;
}
.fp-projection-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 243, 239, 0.4);
  z-index: 2;
}
.fp-projection-lock-card {
  background: #FFFFFF;
  border: 1rpx solid #C9A96E;
  padding: 32rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  box-shadow: 0 8rpx 24rpx rgba(15, 27, 45, 0.1);
  min-width: 380rpx;
}
.fp-projection-lock-icon {
  font-size: 36rpx;
  filter: grayscale(0.2);
}
.fp-projection-lock-title {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
}
.fp-projection-lock-sub {
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
  text-align: center;
}
/* v8 调 L：proj-eyebrow 字号 20→18rpx + letter-spacing 4→6rpx */
.fp-proj-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 20rpx;
}
.fp-proj-arrow {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}
.fp-proj-col {
  flex: 1;
  background: #FFFFFF;
  padding: 20rpx 16rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
/* v8 极简：proj-col-after 改纯白底（去掉金色渐变），用左竖线 + 金色顶部条做差异（distill 思路） */
.fp-proj-col-after {
  background: #FFFFFF;
  border-color: rgba(201, 169, 110, 0.4);
  border-top-width: 2rpx;
}
.fp-proj-label {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 2rpx;
}
.fp-proj-val {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}
.fp-proj-meta {
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
}
/* v8 极简：proj-arrow-icon 字号 32→28rpx + 颜色淡化（700→400） */
.fp-proj-arrow-icon {
  font-size: 28rpx;
  color: #C9A96E;
  font-weight: 400;
  letter-spacing: 0;
}
.fp-proj-foot {
  text-align: center;
  font-size: 22rpx;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
}

/* === 4. 6 大产品摘要 === */
.fp-products-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}

/* v9 增量 · B1：360rpx 金色付费引导 banner */
.fp-paywall-banner {
  position: relative;
  margin: 0 0 -16rpx;     /* 紧贴 fp-hero 之下，与 verdict 拉开 */
  padding: 28rpx 32rpx 24rpx;
  overflow: hidden;
  cursor: pointer;
}
.fp-paywall-banner-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #B89554 0%, #C9A96E 50%, #8C6F36 100%);
  z-index: 0;
}
.fp-paywall-banner-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 24rpx;
  min-height: 100rpx;
}
.fp-paywall-banner-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}
.fp-paywall-banner-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 4rpx;
  font-weight: 600;
  display: block;
}
.fp-paywall-banner-title {
  font-family: $ff-base;
  font-size: 30rpx;
  color: #FFFFFF;
  font-weight: 700;
  letter-spacing: 1rpx;
  line-height: 1.3;
  display: block;
}
.fp-paywall-banner-amount {
  font-size: 36rpx;
  color: #FFFFFF;
  font-weight: 800;
  margin-left: 8rpx;
  font-family: $ff-base;
}
.fp-paywall-banner-sub {
  font-family: $ff-base;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.78);
  letter-spacing: 0.5rpx;
  display: block;
  line-height: 1.4;
}
.fp-paywall-banner-btn {
  flex-shrink: 0;
  padding: 16rpx 28rpx;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  gap: 8rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.12);
}
.fp-paywall-banner-btn-text {
  font-family: $ff-base;
  font-size: 26rpx;
  color: #8C6F36;
  font-weight: 700;
  letter-spacing: 1rpx;
}
.fp-paywall-banner-btn-arrow {
  font-size: 30rpx;
  color: #8C6F36;
  font-weight: 700;
  line-height: 1;
}
.fp-paywall-banner-tip {
  position: relative;
  z-index: 1;
  font-family: $ff-base;
  font-size: 18rpx;
  color: rgba(255, 255, 255, 0.65);
  text-align: center;
  margin-top: 14rpx;
  letter-spacing: 0.5rpx;
  display: block;
}

/* v9 增量 · C1：6 卡重做样式（独立色+icon+等级+基础分+blur 证据链）
   关键修复：v9 初版用 var(--pc-bg) / var(--pc-color) CSS 变量 + .fp-product-wrap 共享样式
   但 Sass 把 var() 第二个参数 / 复合选择器解析为选择器上下文 → "expected selector" 编译错
   修复：6 产品各写 6 套 SCSS 类（绕开 var() + 用具体类名让 Sass 解析明确） */
.fp-product-wrap {
  position: relative;
  margin-top: 24rpx;
  padding: 24rpx 28rpx 28rpx;
  background: rgb(250, 250, 250);
  border-left: 6rpx solid rgb(90, 100, 115);
  border-radius: 8rpx;
  overflow: hidden;
}
.fp-product-wrap.quality_unit {
  background: #EBF3FF;
  border-left-color: #2563EB;
}
.fp-product-wrap.housing_fund {
  background: #F3E8FF;
  border-left-color: #9333EA;
}
.fp-product-wrap.salary {
  background: #FFF1E6;
  border-left-color: #EA580C;
}
.fp-product-wrap.house_owner {
  background: #FEE7E7;
  border-left-color: #DC2626;
}
.fp-product-wrap.tax {
  background: #FAF3E3;
  border-left-color: #B89554;
}
.fp-product-wrap.invoice {
  background: #E0F4F8;
  border-left-color: #0891B2;
}
.fp-product-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 20rpx;
}
.fp-product-icon {
  font-size: 44rpx;
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8rpx;
  flex-shrink: 0;
  line-height: 1;
}
.fp-product-head-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}
.fp-product-name {
  font-family: $ff-base;
  font-size: 30rpx;
  color: #0F1B2D;
  font-weight: 700;
  letter-spacing: 0.5rpx;
  line-height: 1.2;
  display: block;
}
.fp-product-sub {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
  line-height: 1.3;
  display: block;
}
.fp-product-level-chip {
  flex-shrink: 0;
  padding: 6rpx 14rpx;
  font-family: $ff-base;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 0.5rpx;
  border: 1rpx solid;
  line-height: 1.2;
  border-radius: 4rpx;
}
.fp-product-score {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  margin-bottom: 12rpx;
  flex-wrap: wrap;
}
.fp-product-score-num {
  font-family: $ff-base;
  font-size: 64rpx;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1rpx;
}
.fp-product-score-unit {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
}
.fp-product-score-pass {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
  margin-left: auto;
  padding: 4rpx 12rpx;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 4rpx;
}
.fp-product-limit {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  padding: 12rpx 16rpx;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 4rpx;
  margin-bottom: 16rpx;
}
.fp-product-limit-label {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
  flex-shrink: 0;
}
.fp-product-limit-val {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 700;
  letter-spacing: 0.5rpx;
  line-height: 1.2;
}
/* 证据链 blur 区：默认模糊，付费后去掉 .fp-product-evidence-locked 即可清晰 */
.fp-product-evidence {
  position: relative;
  padding: 16rpx 18rpx;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6rpx;
  min-height: 80rpx;
}
.fp-product-evidence-locked {
  filter: blur(8rpx);
  -webkit-filter: blur(8rpx);
  user-select: none;
  pointer-events: none;
}
.fp-ev-block {
  margin-bottom: 12rpx;
}
.fp-ev-block:last-child {
  margin-bottom: 0;
}
.fp-ev-label {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
  font-weight: 600;
  margin-bottom: 6rpx;
  display: block;
}
.fp-ev-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 2rpx 0;
  font-family: $ff-base;
  font-size: 22rpx;
  line-height: 1.5;
}
.fp-ev-rule {
  flex: 1;
  min-width: 0;
  color: #1A1A1A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.fp-ev-score {
  font-size: 22rpx;
  font-weight: 700;
  flex-shrink: 0;
  font-family: $ff-base;
}
.fp-ev-score-neg {
  color: #9B2226;
}
.fp-ev-reason {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #1A1A1A;
  line-height: 1.5;
  letter-spacing: 0.3rpx;
}

/* v9 增量：每张卡底部锁标浮层（C1 决策：所有 6 张都模糊，统一"解锁=清晰"钩子） */
.fp-product-locked-overlay {
  position: relative;
  margin-top: 16rpx;
  padding: 18rpx 20rpx;
  background: linear-gradient(135deg, rgba(184, 149, 84, 0.95) 0%, rgba(201, 169, 110, 0.95) 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  text-align: center;
  border-radius: 6rpx;
  cursor: pointer;
}
.fp-product-locked-icon {
  font-size: 32rpx;
  line-height: 1;
  margin-bottom: 2rpx;
}
.fp-product-locked-text {
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 0.5rpx;
  line-height: 1.3;
  display: block;
}
.fp-product-locked-sub {
  font-family: $ff-base;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 0.5rpx;
  line-height: 1.3;
  display: block;
}
/* v8 极简：products-head 边框更淡 + 间距缩小 */
.fp-products-head {
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.04);
}
/* v8 调 L：products-eyebrow 字号 20→18rpx + letter-spacing 4→6rpx */
.fp-products-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 500;
  display: block;
}
/* v8 极简：products-title 字号 32→28rpx（更精致），letter-spacing 2→1rpx */
.fp-products-title {
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 600;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  display: block;
  margin-top: 8rpx;
}

/* === 5. 极简金线 CTA（v9 增量：D3 决策 — 半透明白底 + 金线 + 9.9 + 箭头） === */
.fp-cta {
  background: rgba(255, 255, 255, 0.88);
  margin: 32rpx;
  padding: 24rpx 32rpx;
  border: 1rpx solid #C9A96E;
  box-shadow: 0 4rpx 16rpx rgba(15, 27, 45, 0.06);
  backdrop-filter: blur(8rpx);
  -webkit-backdrop-filter: blur(8rpx);
}
.fp-cta-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 12rpx 0;
}
.fp-cta-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}
.fp-cta-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 600;
  display: block;
}
.fp-cta-price-row {
  display: flex;
  align-items: baseline;
  gap: 14rpx;
}
.fp-cta-price-num {
  font-family: $ff-base;
  font-size: 44rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  line-height: 1;
}
.fp-cta-price-go {
  font-size: 26rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
  font-weight: 500;
}
.fp-cta-arrow {
  font-family: $ff-base;
  font-size: 48rpx;
  color: #C9A96E;
  font-weight: 400;
  line-height: 1;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}
.fp-cta:active .fp-cta-arrow {
  transform: translateX(6rpx);
}
.fp-cta-tip {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #A0A0A0;
  letter-spacing: 2rpx;
  display: block;
  text-align: center;
  margin-top: 12rpx;
  padding-top: 12rpx;
  border-top: 1rpx dashed rgba(201, 169, 110, 0.3);
}

/* === 免责声明 === */
.fp-disclaimer {
  margin: 48rpx 32rpx 0;
  padding: 24rpx;
  background: rgba(0, 0, 0, 0.02);
  border: 1rpx solid rgba(0, 0, 0, 0.06);
}
.fp-disc-title {
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 600;
  color: #0F1B2D;
  display: block;
  margin-bottom: 12rpx;
  letter-spacing: 1rpx;
}
.fp-disc-line {
  font-size: 22rpx;
  color: #8B8B8B;
  line-height: 1.8;
  display: block;
  white-space: pre-wrap;
  letter-spacing: 0.3rpx;
}

/* v6 修复：底部导航区 */
.fp-footer-nav {
  display: flex;
  gap: 24rpx;
  margin: 48rpx 32rpx 0;
  padding-top: 32rpx;
  border-top: 1rpx solid rgba(15, 27, 45, 0.08);
}
.fp-foot-btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  font-size: 28rpx;
  font-weight: 500;
  letter-spacing: 1rpx;
  border-radius: 8rpx;
  border: none;
  font-family: inherit;
  text-align: center;
}
.fp-foot-btn-secondary {
  background: #FFFFFF;
  color: #0F1B2D;
  border: 1rpx solid #0F1B2D;
}
.fp-foot-btn-primary {
  background: #0F1B2D;
  color: #FFFFFF;
}
.fp-foot-btn::after { border: none; }

/* ============================================
   v4 增量样式
   M6 产品匹配度 / M7 分享卡 / M8 AI 浮动咨询 / M10 跨行快选
   ============================================ */

/* === M6 产品匹配度（v9 删除：块被 C1 决策的 6 卡重做取代） === */
/* v9 重做：fp-product-wrap 基础样式已迁到前面 .fp-product-wrap（C1 决策 6 卡重做） */



/* === M7 分享卡（屏幕外 canvas） === */
.fp-share-stage {
  position: fixed;
  left: -9999rpx;
  top: 0;
  pointer-events: none;
}
.fp-share-canvas {
  display: block;
}

/* === M10 跨行快选 === */
.fp-m10-card {
  background: #FFFFFF;
  margin: 32rpx 32rpx 24rpx;
  padding: 32rpx 0 24rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-top: 4rpx solid #C9A96E;
}
.fp-m10-head {
  padding: 0 32rpx 20rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
  margin-bottom: 24rpx;
}
/* v8 调 L：m10-eyebrow 字号 20→18rpx + letter-spacing 4→6rpx */
.fp-m10-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 8rpx;
}
.fp-m10-title {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  display: block;
}
.fp-m10-loading {
  padding: 60rpx 32rpx;
  text-align: center;
  color: #8B8B8B;
  font-size: 24rpx;
  letter-spacing: 1rpx;
}
.fp-m10-scroll { width: 100%; }
.fp-m10-list {
  display: inline-flex;
  flex-direction: row;
  gap: 20rpx;
  padding: 0 32rpx;
}
.fp-m10-cand {
  width: 420rpx;
  background: linear-gradient(180deg, #FFFFFF, rgba(201, 169, 110, 0.05));
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  padding: 24rpx;
  position: relative;
  flex-shrink: 0;
}
.fp-m10-cand-tag {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  background: #C9A96E;
  color: #FFFFFF;
  font-family: $ff-base;
  font-size: 18rpx;
  padding: 2rpx 12rpx;
  letter-spacing: 1rpx;
  font-weight: 600;
}
.fp-m10-cand-name {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  margin-bottom: 16rpx;
  padding-right: 80rpx;
}
.fp-m10-cand-top {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  margin-bottom: 16rpx;
}
.fp-m10-cand-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
  text {
    flex: 1;
  }
  b {
    font-family: $ff-base;
    font-weight: 700;
    color: #0F1B2D;
    text-align: right;
  }
}
.fp-m10-cand-idx {
  margin-top: 8rpx;
  padding-top: 12rpx;
  border-top: 1rpx dashed rgba(15, 27, 45, 0.1);
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
}
.fp-m10-cand-idx-num {
  font-family: $ff-base;
  font-weight: 700;
  color: #C9A96E;
  font-size: 28rpx;
  margin: 0 4rpx;
}
.fp-m10-cand-go {
  text-align: center;
  background: #0F1B2D;
  color: #FFFFFF;
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 500;
  letter-spacing: 1rpx;
  padding: 16rpx;
  border-radius: 4rpx;
}

/* === v9 客服浮窗低调化（半透明白底 + 文字深蓝 + 金描边不抢戏） === */
.fp-ai-fab {
  position: fixed;
  right: 32rpx;
  /* v9 增量：bottom 200→280rpx，往下挪 80rpx 让出底部空间，不挤 CTA */
  bottom: 280rpx;
  background: rgba(255, 255, 255, 0.88);
  color: #0F1B2D;
  padding: 16rpx 24rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  box-shadow: 0 4rpx 16rpx rgba(15, 27, 45, 0.08);
  z-index: 99;
  border: 1rpx solid #C9A96E;
  backdrop-filter: blur(8rpx);
  -webkit-backdrop-filter: blur(8rpx);
}
.fp-ai-fab-dot {
  width: 12rpx;
  height: 12rpx;
  background: #C9A96E;
  border-radius: 50%;
  box-shadow: 0 0 8rpx rgba(201, 169, 110, 0.5);
  animation: fabDot 1.8s infinite ease-in-out;
}
@keyframes fabDot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.15); }
}
.fp-ai-fab-txt {
  font-size: 24rpx;
  font-weight: 500;
  letter-spacing: 2rpx;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #0F1B2D;
}

/* === v7 顶部 nav-bar（返回 + 客服 ONLINE 入口） === */
.fp-nav-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24rpx;
  z-index: 10;
}
.fp-nav-back {
  width: 56rpx;
  height: 56rpx;
  background: rgba(255, 255, 255, 0.1);
  border: 1rpx solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10rpx);
  -webkit-backdrop-filter: blur(10rpx);
}
.fp-nav-back-arrow {
  color: #FFFFFF;
  font-size: 36rpx;
  line-height: 1;
  font-weight: 300;
  margin-top: -2rpx;
}
.fp-nav-title {
  color: #FFFFFF;
  font-size: 28rpx;
  font-weight: 500;
  letter-spacing: 2rpx;
  opacity: 0.9;
}
.fp-nav-spacer {
  width: 56rpx;
  height: 56rpx;
  /* 占位用：和左侧返回按钮同尺寸，保持标题居中 */
}

/* === v7 银行评估侧重点 === */
.fp-bank-focus {
  margin: 24rpx 32rpx 0;
  padding: 28rpx 32rpx;
  background: linear-gradient(135deg, #FFFFFF 0%, #FDFCF6 100%);
  border: 1rpx solid rgba(201, 169, 110, 0.4);
  border-top: 4rpx solid #C9A96E;
  position: relative;
  overflow: hidden;
}
.fp-bank-focus::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 200rpx;
  height: 200rpx;
  background: radial-gradient(circle at top right, rgba(201, 169, 110, 0.12) 0%, transparent 70%);
  pointer-events: none;
}
.fp-bank-focus-head {
  position: relative;
  z-index: 1;
  margin-bottom: 20rpx;
}
/* v8 调 L：bank-focus-eyebrow 字号 20→18rpx + letter-spacing 4→6rpx */
.fp-bank-focus-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 8rpx;
}
.fp-bank-focus-title {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  display: block;
  margin-bottom: 8rpx;
}
.fp-bank-focus-slogan {
  font-size: 26rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
  display: block;
  line-height: 1.5;
  font-weight: 500;
}
.fp-bank-focus-tags {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
/* v8 极简：bank-focus-tag 圆角胶囊 改 横线 + 文字（distill 思路：极致简约） */
.fp-bank-focus-tag {
  display: inline-block;
  padding: 4rpx 0;
  margin-right: 4rpx;
  background: transparent;
  color: #8C6F36;
  font-size: 22rpx;
  letter-spacing: 0.5rpx;
  border: none;
  border-bottom: 1rpx solid rgba(201, 169, 110, 0.4);
  border-radius: 0;
}
.fp-bank-focus-foot {
  position: relative;
  z-index: 1;
  padding-top: 12rpx;
  border-top: 1rpx dashed rgba(201, 169, 110, 0.3);
}
.fp-bank-focus-foot-eyebrow {
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
  font-style: italic;
}
.fp-ai-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 100;
}
.fp-ai-panel {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  height: 80vh;
  background: #FFFFFF;
  border-top-left-radius: 24rpx;
  border-top-right-radius: 24rpx;
  z-index: 101;
  display: flex;
  flex-direction: column;
  box-shadow: 0 -8rpx 32rpx rgba(0, 0, 0, 0.15);
}
.fp-ai-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
  background: linear-gradient(180deg, rgba(201, 169, 110, 0.05), #FFFFFF);
}
/* v8 调 L：ai-eyebrow 字号 18rpx 不变 + letter-spacing 3→6rpx（和 hero-eyebrow 风格统一） */
.fp-ai-eyebrow {
  font-family: $ff-base;
  font-size: 18rpx;
  color: #C9A96E;
  letter-spacing: 6rpx;
  font-weight: 600;
  display: block;
  margin-bottom: 4rpx;
}
.fp-ai-title {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  display: block;
}
.fp-ai-close {
  font-size: 48rpx;
  color: #8B8B8B;
  line-height: 1;
  padding: 0 12rpx;
}
.fp-chat-body {
  flex: 1;
  padding: 24rpx 32rpx;
}
.fp-chat-empty {
  padding: 40rpx 0;
  text-align: center;
}
.fp-chat-empty-t {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 2rpx;
  margin-bottom: 24rpx;
}
.fp-chat-quick {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  justify-content: center;
}
.fp-chat-q {
  display: inline-block;
  padding: 12rpx 20rpx;
  background: rgba(201, 169, 110, 0.1);
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  color: #8C6F36;
  font-size: 24rpx;
  letter-spacing: 0.5rpx;
  border-radius: 999rpx;
}
.fp-chat-msg {
  display: flex;
  margin-bottom: 20rpx;
  &.fp-chat-user { justify-content: flex-end; }
  &.fp-chat-ai   { justify-content: flex-start; }
}
.fp-chat-bubble {
  max-width: 80%;
  padding: 20rpx 24rpx;
  font-size: 26rpx;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
  word-break: break-word;
}
.fp-chat-user .fp-chat-bubble {
  background: #0F1B2D;
  color: #FFFFFF;
  border-radius: 16rpx 16rpx 4rpx 16rpx;
}
.fp-chat-ai .fp-chat-bubble {
  background: rgba(201, 169, 110, 0.1);
  color: #0F1B2D;
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  border-radius: 16rpx 16rpx 16rpx 4rpx;
}
.fp-chat-dot {
  display: flex;
  gap: 6rpx;
  text {
    display: inline-block;
    width: 8rpx;
    height: 8rpx;
    background: #C9A96E;
    border-radius: 50%;
    animation: chatDot 1.2s infinite ease-in-out;
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}
@keyframes chatDot {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4rpx); opacity: 1; }
}
.fp-ai-foot {
  display: flex;
  gap: 16rpx;
  padding: 20rpx 32rpx;
  border-top: 1rpx solid rgba(15, 27, 45, 0.08);
  background: #FAFAF7;
}
.fp-ai-input {
  flex: 1;
  height: 72rpx;
  background: #FFFFFF;
  border: 1rpx solid rgba(15, 27, 45, 0.15);
  border-radius: 36rpx;
  padding: 0 24rpx;
  font-size: 26rpx;
  letter-spacing: 0.3rpx;
}
.fp-ai-send {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 32rpx;
  background: #0F1B2D;
  color: #FFFFFF;
  font-size: 26rpx;
  letter-spacing: 2rpx;
  border-radius: 36rpx;
  border: none;
  font-family: inherit;
}
</style>
