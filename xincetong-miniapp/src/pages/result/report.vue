<!--
  report.vue · 完整报告（付费后）
  v3.2 重构：8 大模块（按用户方案）
    1. 报告头 + 综合分回顾
    2. 一句话结论
    3. 核心问题诊断（3 个卡片）
    4. 每个问题深度分析（5 维度，可折叠）
    5. 改善路径（30/60/90 天时间轴）
    6. 改善后模拟推演（前后对比）
    7. 6 大产品模拟结果
    8. 申请顺序策略
    9. 免责声明
-->
<template>
  <view class="report-page">
    <ComplianceBar />

    <view v-if="loading" class="loading-state">
      <view class="loading-spinner" />
      <view class="loading-text">加载中</view>
    </view>

    <template v-else-if="report">
      <!-- 报告头 -->
      <view class="rp-hero">
        <view class="rp-hero-eyebrow">FULL REPORT · 完整模拟评审报告</view>
        <view class="rp-hero-no">报告编号 · {{ report.report_no }}</view>
        <view v-if="report.paid_at" class="rp-hero-time">解锁时间 · {{ formatTime(report.paid_at) }}</view>
      </view>

      <!-- 1. 一句话结论（首屏焦点） -->
      <view v-if="report.one_sentence" class="rp-verdict" :class="'rp-verdict-' + levelClass">
        <view class="rp-verdict-icon">
          <UiIcon :name="verdictIcon" :size="40" :color="verdictColor" />
        </view>
        <view class="rp-verdict-body">
          <view class="rp-verdict-eyebrow">模拟评审结论</view>
          <view class="rp-verdict-text" :style="{ color: verdictColor }">
            {{ report.one_sentence }}
          </view>
        </view>
      </view>

      <!-- 2. 综合分回顾 -->
      <view class="rp-overall-card">
        <view class="rp-overall-head">
          <text class="rp-overall-eyebrow">OVERALL SCORE</text>
          <text class="rp-overall-title">综合评分</text>
        </view>
        <view class="rp-overall-body">
          <view class="rp-overall-col">
            <text class="rp-overall-label">分数</text>
            <text class="rp-overall-val" :style="{ color: levelColor }">
              {{ report.overall.score }}
            </text>
          </view>
          <view class="rp-overall-col">
            <text class="rp-overall-label">等级</text>
            <text class="rp-overall-val">{{ report.overall.level }}</text>
          </view>
          <view class="rp-overall-col">
            <text class="rp-overall-label">综合额度</text>
            <text class="rp-overall-val">{{ formatLimit(report.overall.limit_min, report.overall.limit_max) }}</text>
          </view>
          <view class="rp-overall-col">
            <text class="rp-overall-label">通过率</text>
            <text class="rp-overall-val" :style="{ color: PASS_PROB_COLOR[report.overall.pass_probability] }">
              {{ report.overall.pass_probability }}
            </text>
          </view>
        </view>
      </view>

      <!-- 3. 核心问题诊断（3 个卡片，按严重度） -->
      <view v-if="report.top_issues && report.top_issues.length" class="rp-issues-card">
        <view class="rp-section-head">
          <text class="rp-section-eyebrow">CORE ISSUES</text>
          <text class="rp-section-title">核心问题诊断</text>
          <text class="rp-section-sub">按严重程度排序 · 共 {{ report.top_issues.length }} 个</text>
        </view>
        <view
          v-for="issue in report.top_issues"
          :key="issue.id"
          class="rp-issue-item"
          :style="{ borderLeftColor: issue.severity_color }"
        >
          <view class="rp-issue-head">
            <view class="rp-issue-num">#{{ issue.id }}</view>
            <view class="rp-issue-tag" :style="{ background: issue.severity_color }">
              {{ severityLabel(issue.severity) }}
            </view>
            <view class="rp-issue-cat">{{ issue.category }}</view>
          </view>
          <view class="rp-issue-title">{{ issue.title }}</view>
          <view class="rp-issue-impact-row">
            <view v-for="(val, idx) in impactList(issue)" :key="idx" class="rp-issue-impact-pill">
              <text class="rp-issue-impact-pill-icon">{{ idx === 0 ? '↓' : (idx === 2 ? '↑' : '↓') }}</text>
              <text class="rp-issue-impact-pill-text">{{ val }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 4. 每个问题深度分析（5 维度，可折叠） -->
      <view v-if="report.top_issues && report.top_issues.length" class="rp-deep-card">
        <view class="rp-section-head">
          <text class="rp-section-eyebrow">DEEP DIVE</text>
          <text class="rp-section-title">每个问题深度分析</text>
          <text class="rp-section-sub">5 维度展开：是什么 / 为什么 / 影响 / 怎么改 / 预期</text>
        </view>
        <view
          v-for="issue in report.top_issues"
          :key="'deep-' + issue.id"
          class="rp-deep-item"
          :class="{ 'rp-deep-item-open': openIssues[issue.id] }"
        >
          <view class="rp-deep-head" @tap="toggleIssue(issue.id)">
            <view class="rp-deep-head-left">
              <view class="rp-deep-num" :style="{ background: issue.severity_color }">{{ issue.id }}</view>
              <view class="rp-deep-head-text">
                <text class="rp-deep-title">{{ issue.title }}</text>
                <text class="rp-deep-meta">{{ issue.category }} · 严重度 {{ severityLabel(issue.severity) }}</text>
              </view>
            </view>
            <view class="rp-deep-toggle" :class="{ 'rp-deep-toggle-open': openIssues[issue.id] }">
              <UiIcon :name="openIssues[issue.id] ? 'arrow-up' : 'arrow-down'" :size="28" color="#0F1B2D" />
            </view>
          </view>
          <view v-if="openIssues[issue.id]" class="rp-deep-body">
            <view class="rp-deep-block">
              <view class="rp-deep-block-tag">01</view>
              <view class="rp-deep-block-body">
                <text class="rp-deep-block-label">问题是什么</text>
                <text class="rp-deep-block-text">{{ issue.what }}</text>
              </view>
            </view>
            <view class="rp-deep-block rp-deep-block-why">
              <view class="rp-deep-block-tag">02</view>
              <view class="rp-deep-block-body">
                <text class="rp-deep-block-label">为什么是问题</text>
                <text class="rp-deep-block-text">{{ issue.why }}</text>
              </view>
            </view>
            <view class="rp-deep-block rp-deep-block-impact">
              <view class="rp-deep-block-tag">03</view>
              <view class="rp-deep-block-body">
                <text class="rp-deep-block-label">影响有多大</text>
                <view class="rp-deep-impact-list">
                  <view class="rp-deep-impact-row">
                    <text class="rp-deep-impact-key">通过概率</text>
                    <text class="rp-deep-impact-val" :style="{ color: issue.severity_color }">{{ issue.impact_prob }}</text>
                  </view>
                  <view v-if="issue.impact_amount !== '—'" class="rp-deep-impact-row">
                    <text class="rp-deep-impact-key">额度影响</text>
                    <text class="rp-deep-impact-val" :style="{ color: issue.severity_color }">{{ issue.impact_amount }}</text>
                  </view>
                  <view v-if="issue.impact_rate !== '—'" class="rp-deep-impact-row">
                    <text class="rp-deep-impact-key">利率影响</text>
                    <text class="rp-deep-impact-val" :style="{ color: issue.severity_color }">{{ issue.impact_rate }}</text>
                  </view>
                </view>
              </view>
            </view>
            <view class="rp-deep-block rp-deep-block-how">
              <view class="rp-deep-block-tag">04</view>
              <view class="rp-deep-block-body">
                <text class="rp-deep-block-label">怎么改善</text>
                <text class="rp-deep-block-text">{{ issue.how }}</text>
                <view class="rp-deep-when">
                  <text class="rp-deep-when-icon">⏱</text>
                  <text class="rp-deep-when-text">预计耗时 · {{ issue.when }}</text>
                </view>
              </view>
            </view>
            <view class="rp-deep-block rp-deep-block-result">
              <view class="rp-deep-block-tag">05</view>
              <view class="rp-deep-block-body">
                <text class="rp-deep-block-label">改善后预期</text>
                <text class="rp-deep-block-text">{{ issue.result }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 5. 改善路径（30/60/90 天时间轴） -->
      <view v-if="pathTimeline.length" class="rp-path-card">
        <view class="rp-section-head">
          <text class="rp-section-eyebrow">IMPROVEMENT PATH</text>
          <text class="rp-section-title">改善路径</text>
          <text class="rp-section-sub">30 / 60 / 90 天分阶段动作 + 预期效果</text>
        </view>
        <view class="rp-path-timeline">
          <view
            v-for="(step, i) in pathTimeline"
            :key="i"
            class="rp-path-item"
            :class="'rp-path-item-' + step.color"
          >
            <view class="rp-path-axis">
              <view class="rp-path-dot" />
              <view v-if="i !== pathTimeline.length - 1" class="rp-path-line" />
            </view>
            <view class="rp-path-body">
              <view class="rp-path-period" :class="'rp-path-period-' + step.color">{{ step.period }}</view>
              <view v-for="(act, j) in step.actions" :key="j" class="rp-path-action">
                <text class="rp-path-action-bullet">·</text>
                <text class="rp-path-action-text">{{ act }}</text>
              </view>
              <view v-if="step.effect" class="rp-path-effect">
                <text class="rp-path-effect-tag">预期效果</text>
                <text class="rp-path-effect-text">{{ step.effect }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 6. 改善后模拟推演（前后对比） -->
      <view v-if="report.improvement_projection" class="rp-projection-card">
        <view class="rp-section-head">
          <text class="rp-section-eyebrow">PROJECTION</text>
          <text class="rp-section-title">改善后模拟推演</text>
          <text class="rp-section-sub">按建议执行 90 天后的预测评分 / 额度 / 通过率</text>
        </view>
        <view class="rp-proj-compare">
          <view class="rp-proj-col">
            <view class="rp-proj-col-head">
              <text class="rp-proj-col-eyebrow">BEFORE</text>
              <text class="rp-proj-col-title">当前状态</text>
            </view>
            <view class="rp-proj-row">
              <text class="rp-proj-key">综合评分</text>
              <text class="rp-proj-val">{{ report.overall.score }} 分 · {{ report.overall.level }}</text>
            </view>
            <view class="rp-proj-row">
              <text class="rp-proj-key">模拟额度</text>
              <text class="rp-proj-val">{{ formatLimit(report.overall.limit_min, report.overall.limit_max) }}</text>
            </view>
            <view class="rp-proj-row">
              <text class="rp-proj-key">通过概率</text>
              <text class="rp-proj-val" :style="{ color: PASS_PROB_COLOR[report.overall.pass_probability] }">
                {{ report.overall.pass_probability }}
              </text>
            </view>
          </view>
          <view class="rp-proj-arrow">
            <view class="rp-proj-arrow-icon">→</view>
            <text class="rp-proj-arrow-text">90 天</text>
          </view>
          <view class="rp-proj-col rp-proj-col-after">
            <view class="rp-proj-col-head">
              <text class="rp-proj-col-eyebrow rp-proj-col-eyebrow-after">AFTER</text>
              <text class="rp-proj-col-title">改善后</text>
            </view>
            <view class="rp-proj-row">
              <text class="rp-proj-key">综合评分</text>
              <text class="rp-proj-val">{{ report.improvement_projection.score }} 分 · {{ report.improvement_projection.level }}</text>
            </view>
            <view class="rp-proj-row">
              <text class="rp-proj-key">模拟额度</text>
              <text class="rp-proj-val">{{ formatLimit(report.improvement_projection.limit_min, report.improvement_projection.limit_max) }}</text>
            </view>
            <view class="rp-proj-row">
              <text class="rp-proj-key">通过概率</text>
              <text class="rp-proj-val" :style="{ color: PASS_PROB_COLOR[report.improvement_projection.pass_probability] }">
                {{ report.improvement_projection.pass_probability }}
              </text>
            </view>
          </view>
        </view>
        <view v-if="projectionGain" class="rp-proj-gain">
          <text class="rp-proj-gain-title">提升幅度</text>
          <view class="rp-proj-gain-row">
            <text class="rp-proj-gain-key">评分</text>
            <text class="rp-proj-gain-val" :style="{ color: '#C9A96E' }">+{{ projectionGain.score }} 分</text>
          </view>
          <view v-if="projectionGain.limit" class="rp-proj-gain-row">
            <text class="rp-proj-gain-key">额度</text>
            <text class="rp-proj-gain-val" :style="{ color: '#C9A96E' }">+{{ projectionGain.limit }}</text>
          </view>
          <view v-if="projectionGain.passRank" class="rp-proj-gain-row">
            <text class="rp-proj-gain-key">通过率</text>
            <text class="rp-proj-gain-val" :style="{ color: '#C9A96E' }">{{ projectionGain.passRank }}</text>
          </view>
        </view>
      </view>

      <!-- v4 增量 · M5 30/60/90 额度·利率预测表（与 web 端同源 projection_table） -->
      <view v-if="projectionTable.length" class="rp-m5-card">
        <view class="rp-section-head">
          <text class="rp-section-eyebrow">05 / PROJECTION</text>
          <text class="rp-section-title">30 / 60 / 90 天额度·利率预测</text>
          <text class="rp-section-sub">估算规则：按等级提升幅度线性外推 + 利率随等级下调</text>
        </view>
        <scroll-view class="rp-m5-scroll" scroll-x>
          <view class="rp-m5-list">
            <view
              v-for="(p, i) in projectionTable"
              :key="i"
              :class="['rp-m5-col', p.is_current ? 'rp-m5-cur' : '']"
            >
              <view class="rp-m5-day">{{ p.day }}</view>
              <view class="rp-m5-lv" :style="{ color: LEVEL_COLOR[p.level] }">{{ p.level }}</view>
              <view class="rp-m5-score">{{ p.score }} <text class="rp-m5-unit">分</text></view>
              <view class="rp-m5-bar">
                <view class="rp-m5-bar-fill" :style="{ width: p.score + '%' }" />
              </view>
              <view class="rp-m5-row"><text>额度</text><b>{{ formatLimit(p.limit_min, p.limit_max) }}</b></view>
              <view class="rp-m5-row"><text>利率</text><b>{{ p.rate_min }}~{{ p.rate_max }}%</b></view>
              <view v-if="!p.is_current" class="rp-m5-tag">+{{ p.growth_pct }}%</view>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 7. 6 大产品模拟结果（v9 重做：独立色+icon+等级+基础分+完整证据链） -->
      <view class="rp-products-card">
        <view class="rp-section-head">
          <text class="rp-section-eyebrow">PRODUCTS DETAIL</text>
          <text class="rp-section-title">各产品独立模拟结果</text>
          <text class="rp-section-sub">基于当前状态 · ⭐ 标识最适合您的产品</text>
        </view>
        <view
          v-for="p in report.product_results"
          :key="p.product_code"
          :class="['rp-product-wrap', p.product_code]"
        >
          <!-- 顶部条：icon + 产品名 + 等级 chip + ⭐推荐 -->
          <view class="rp-product-head">
            <view class="rp-product-icon">{{ getProductColor(p.product_code).icon }}</view>
            <view class="rp-product-head-body">
              <view class="rp-product-name-row">
                <text class="rp-product-name">{{ p.product_name }}</text>
                <text v-if="p.best_for_user" class="rp-product-star">⭐ 推荐</text>
              </view>
              <view v-if="p.product_subtitle" class="rp-product-sub">{{ p.product_subtitle }}</view>
            </view>
            <view
              v-if="p.level"
              class="rp-product-level-chip"
              :style="{
                color: getLevelColor(p.level).color,
                background: getLevelColor(p.level).bg,
                borderColor: getLevelColor(p.level).color,
              }"
            >
              {{ p.level }} · {{ getLevelColor(p.level).label }}
            </view>
          </view>

          <!-- 基础分大数字 -->
          <view class="rp-product-score">
            <view class="rp-product-score-num" :style="{ color: getProductColor(p.product_code).color }">
              {{ p.score }}
            </view>
            <view class="rp-product-score-unit">基础分</view>
            <view v-if="p.pass_probability" class="rp-product-score-pass">通过率 {{ p.pass_probability }}</view>
          </view>

          <!-- 模拟额度（清晰可见，付费用户专属） -->
          <view class="rp-product-limit">
            <view class="rp-product-limit-label">模拟额度</view>
            <view class="rp-product-limit-val" :style="{ color: getProductColor(p.product_code).color }">
              {{ formatLimit(p.realistic_limit_min || p.limit_min, p.realistic_limit_max || p.limit_max) }}
            </view>
            <view class="rp-product-limit-actual">实际可贷</view>
          </view>

          <!-- 完整证据链（不模糊，付费用户专属） -->
          <view class="rp-product-evidence">
            <!-- 命中加分 -->
            <view v-if="p.hit_rules && p.hit_rules.length" class="rp-ev-block">
              <view class="rp-ev-label">✓ 命中加分</view>
              <view v-for="(r, k) in p.hit_rules" :key="k" class="rp-ev-row">
                <text class="rp-ev-rule">{{ r.rule }}</text>
                <text class="rp-ev-score" :style="{ color: getProductColor(p.product_code).color }">+{{ r.score }}</text>
              </view>
            </view>
            <!-- 扣分项 -->
            <view v-if="p.low_rules && p.low_rules.length" class="rp-ev-block">
              <view class="rp-ev-label">✗ 扣分项</view>
              <view v-for="(r, k) in p.low_rules" :key="k" class="rp-ev-row">
                <text class="rp-ev-rule">{{ r.rule }}</text>
                <text class="rp-ev-score rp-ev-score-neg">{{ r.score }}</text>
              </view>
            </view>
            <!-- 不推荐原因 -->
            <view v-if="p.not_recommend_reason" class="rp-ev-block">
              <view class="rp-ev-label">⚠ 不推荐原因</view>
              <view class="rp-ev-reason">{{ p.not_recommend_reason }}</view>
            </view>
            <!-- 提分建议 -->
            <view v-if="p.improve_vars && p.improve_vars.length" class="rp-ev-block">
              <view class="rp-ev-label">↑ 提分建议</view>
              <view v-for="(v, k) in p.improve_vars" :key="k" class="rp-ev-row">
                <text class="rp-ev-rule">{{ v.current }} → {{ v.best }}</text>
                <text class="rp-ev-score" :style="{ color: getProductColor(p.product_code).color }">+{{ v.delta }}</text>
              </view>
            </view>
            <!-- 风险标签 / 优势（保留 report.vue 旧字段） -->
            <view v-if="p.risk_tags && p.risk_tags.length" class="rp-ev-block">
              <view class="rp-ev-label">⚠ 风险标签</view>
              <view v-for="(r, k) in p.risk_tags" :key="k" class="rp-ev-tag">{{ r }}</view>
            </view>
            <view v-if="p.advantages && p.advantages.length" class="rp-ev-block">
              <view class="rp-ev-label">✓ 优势</view>
              <view v-for="(a, k) in p.advantages" :key="k" class="rp-ev-tag">{{ a }}</view>
            </view>
          </view>
        </view>
      </view>

      <!-- 8. 申请顺序策略 -->
      <view class="rp-strategy-card">
        <view class="rp-section-head">
          <text class="rp-section-eyebrow">APPLY STRATEGY</text>
          <text class="rp-section-title">申请顺序策略</text>
          <text class="rp-section-sub">基于您当前资质 + 6 大产品通过率</text>
        </view>
        <view v-if="strategySteps.length" class="rp-strat-list">
          <view
            v-for="(step, i) in strategySteps"
            :key="i"
            class="rp-strat-item"
            :class="'rp-strat-item-' + step.priority"
          >
            <view class="rp-strat-priority">{{ step.priorityLabel }}</view>
            <view class="rp-strat-body">
              <view class="rp-strat-head">
                <text class="rp-strat-name">{{ step.name }}</text>
                <text class="rp-strat-pass" :style="{ color: PASS_PROB_COLOR[step.pass] }">
                  {{ step.pass }}
                </text>
              </view>
              <text class="rp-strat-reason">{{ step.reason }}</text>
            </view>
          </view>
        </view>
        <view v-else class="rp-strat-raw">
          <text class="rp-strat-raw-text">{{ report.apply_strategy }}</text>
        </view>
        <view class="rp-strat-warning">
          <text class="rp-strat-warning-icon">⚠</text>
          <text class="rp-strat-warning-text">不建议同时申请多个产品，会产生多次硬查询反而降低通过率</text>
        </view>
      </view>

      <!-- 9. 免责声明 -->
      <view class="rp-disclaimer">
        <text class="rp-disc-title">关于本报告</text>
        <text class="rp-disc-line">{{ report.disclaimer || defaultDisclaimer }}</text>
      </view>
    </template>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import ProductCard from '@/components/product-card/ProductCard.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { getFullReport, type FullReportRes } from '@/api/assessment'
import { getProductColor, getLevelColor } from '@/utils/productConfig'

// v9 增量：6 卡独立色绑定（给 :style 绑定 product_code 派生的色/边）
function productCardStyle(code: string) {
  const c = getProductColor(code)
  return {
    borderLeftColor: c.color,
    '--pc-color': c.color,
    '--pc-bg': c.bg,
    '--pc-text': c.text,
  } as any
}

// v11 增量：额度格式化改为元数 + 千分位（v9 旧版为"X.X 万"）
function formatLimit(min?: number, max?: number): string {
  if (!min && !max) return '—'
  const fmt = (n: number) => Math.round(n).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  if (min && max) {
    if (min === max) return `${fmt(min)} 元`
    return `${fmt(min)}~${fmt(max)} 元`
  }
  if (max) return `${fmt(max)} 元`
  return `${fmt(min || 0)} 元`
}

const loading = ref(true)
const report = ref<FullReportRes | null>(null)
const assessmentId = ref(0)

const LEVEL_COLOR: Record<string, string> = {
  S: '#1B5E20', A: '#2E7D32', B: '#558B2F', C: '#C9A96E', D: '#EF6C00', E: '#C62828',
}
const PASS_PROB_COLOR: Record<string, string> = {
  '高': '#2E7D32', '中高': '#558B2F', '中': '#C9A96E', '低': '#EF6C00', '极低': '#C62828',
}
const PASS_RANK: Record<string, number> = {
  '高': 5, '中高': 4, '中': 3, '低': 2, '极低': 1,
}

const levelColor = computed(() => LEVEL_COLOR[report.value?.overall?.level || 'E'] || '#666')

const levelClass = computed(() => {
  const lv = report.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return 'good'
  if (lv === 'B' || lv === 'C') return 'mid'
  return 'bad'
})
const verdictIcon = computed(() => {
  const lv = report.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return 'check'
  if (lv === 'B' || lv === 'C') return 'info'
  return 'warning'
})
const verdictColor = computed(() => {
  const lv = report.value?.overall?.level || 'E'
  if (lv === 'S' || lv === 'A') return '#2E7D32'
  if (lv === 'B' || lv === 'C') return '#C9A96E'
  return '#C62828'
})

const openIssues = reactive<Record<number, boolean>>({})
function toggleIssue(id: number) {
  openIssues[id] = !openIssues[id]
}

function severityLabel(sev: string): string {
  if (sev === 'high') return '高'
  if (sev === 'mid') return '中'
  return '低'
}

function impactList(issue: any): string[] {
  const arr: string[] = []
  if (issue.impact_prob) arr.push(issue.impact_prob)
  if (issue.impact_amount && issue.impact_amount !== '—') arr.push(issue.impact_amount)
  if (issue.impact_rate && issue.impact_rate !== '—') arr.push(issue.impact_rate)
  return arr
}

// 改善路径时间线（30/60/90 天）
const pathTimeline = computed(() => {
  if (!report.value?.suggestions) return []
  const groups: Record<string, any[]> = {}
  for (const s of report.value.suggestions) {
    const period = s.period || '持续'
    if (!groups[period]) groups[period] = []
    groups[period].push(s)
  }
  // 按时间顺序排
  const order = ['立即', '1-3 个月', '3-6 个月', '6 个月+', '持续']
  const colorMap: Record<string, string> = {
    '立即': 'urgent',
    '1-3 个月': 'soon',
    '3-6 个月': 'mid',
    '6 个月+': 'long',
    '持续': 'ongoing',
  }
  const result: any[] = []
  for (const p of order) {
    if (groups[p]) {
      result.push({
        period: p,
        color: colorMap[p],
        actions: groups[p].map((s) => s.action),
        effect: extractEffect(groups[p]),
      })
    }
  }
  return result
})

function extractEffect(sugs: any[]): string {
  // 从建议里抓含数字的效果描述
  for (const s of sugs) {
    if (s.reason && /\d+\s*[-~到]\s*\d*\s*%|\d+\s*分|\+\d+/.test(s.reason)) {
      return s.reason
    }
  }
  return ''
}

// 推演提升幅度
const projectionGain = computed(() => {
  if (!report.value?.improvement_projection) return null
  const cur = report.value.overall
  const pro = report.value.improvement_projection
  const scoreGain = pro.score - cur.score
  const limitGain = (pro.limit_min + pro.limit_max) / 2 - (cur.limit_min + cur.limit_max) / 2
  const curRank = PASS_RANK[cur.pass_probability] || 0
  const proRank = PASS_RANK[pro.pass_probability] || 0
  const passRankGain = proRank - curRank
  return {
    score: scoreGain,
    limit: limitGain > 0 ? `+${Math.round(limitGain).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')} 元` : '',
    passRank: passRankGain > 0 ? `从 ${cur.pass_probability} 提升到 ${pro.pass_probability}` : '持平',
  }
})

// v4 增量 · M5 30/60/90 预测表（与 web 端同源 projection_table 字段，兜底空表）
const projectionTable = computed(() => {
  const r: any = report.value
  if (!r) return []
  if (Array.isArray(r.projection_table) && r.projection_table.length) return r.projection_table
  return []
})

// 申请顺序策略（基于产品 + 通过率 + best_for_user）
const strategySteps = computed(() => {
  if (!report.value?.product_results) return []
  const products = [...report.value.product_results]
  // 排序：1) best_for_user 优先  2) pass_rank 高  3) 通过率非极低
  products.sort((a, b) => {
    const aBFU = a.best_for_user ? 1 : 0
    const bBFU = b.best_for_user ? 1 : 0
    if (aBFU !== bBFU) return bBFU - aBFU
    const aRank = PASS_RANK[a.pass_probability] || 0
    const bRank = PASS_RANK[b.pass_probability] || 0
    return bRank - aRank
  })
  return products.slice(0, 4).map((p, i) => {
    const priority = i + 1
    let reason = ''
    if (p.best_for_user) {
      reason = '这是最适合您的产品，建议第一个申请'
    } else if (p.pass_probability === '高' || p.pass_probability === '中高') {
      reason = '通过率高，资质匹配，可放心申请'
    } else if (p.pass_probability === '中') {
      reason = '通过率中等，可作为备选方案'
    } else {
      reason = '通过率较低，建议先改善再申请'
    }
    return {
      priority,
      priorityLabel: priority === 1 ? '① 首选' : (priority === 2 ? '② 次选' : (priority === 3 ? '③ 备选' : '④ 备选')),
      name: p.product_name,
      pass: p.pass_probability,
      reason,
      priorityCls: priority === 1 ? 'first' : (priority === 2 ? 'second' : 'last'),
    }
  })
})

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
    report.value = await getFullReport(assessmentId.value)
    // 默认展开第 1 个核心问题
    if (report.value.top_issues && report.value.top_issues.length > 0) {
      openIssues[report.value.top_issues[0].id] = true
    }
  } catch (e) {
    console.error('加载完整报告失败', e)
  } finally {
    loading.value = false
  }
})

function formatTime(iso?: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
/* ============================================
   完整报告页 · v3.2
   设计：奢华金融 + 信息密度合理
   ============================================ */
.report-page {
  min-height: 100vh;
  background: #F5F3EF;
  padding-bottom: 80rpx;
}
.loading-state { padding: 200rpx 0; text-align: center; }
.loading-spinner {
  width: 48rpx; height: 48rpx;
  border: 4rpx solid rgba(15, 27, 45, 0.1);
  border-top-color: #0F1B2D;
  border-radius: 50%;
  margin: 0 auto 16rpx;
  animation: spin 1s linear infinite;
}
.loading-text { font-size: 28rpx; color: #8B8B8B; }
@keyframes spin { to { transform: rotate(360deg); } }

/* === 通用 Section Head === */
.rp-section-head {
  margin-bottom: 24rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-section-eyebrow {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
}
.rp-section-title {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
  display: block;
  margin-top: 8rpx;
}
.rp-section-sub {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
  margin-top: 8rpx;
  display: block;
  line-height: 1.5;
}

/* === 报告头 === */
.rp-hero {
  background: linear-gradient(180deg, #0F1B2D 0%, #1B2A4A 100%);
  padding: 48rpx 32rpx 32rpx;
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
.rp-hero-eyebrow {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.rp-hero-no, .rp-hero-time {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 1rpx;
  display: block;
  margin-top: 12rpx;
}

/* === 1. 一句话结论 === */
.rp-verdict {
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
  &.rp-verdict-good { border-top-color: #2E7D32; }
  &.rp-verdict-mid  { border-top-color: #C9A96E; }
  &.rp-verdict-bad  { border-top-color: #C62828; }
}
.rp-verdict-icon {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(201, 169, 110, 0.08);
  border-radius: 50%;
  flex-shrink: 0;
}
.rp-verdict-body { flex: 1; min-width: 0; }
.rp-verdict-eyebrow {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 3rpx;
  margin-bottom: 8rpx;
  display: block;
}
.rp-verdict-text {
  font-family: $ff-base;
  font-size: 34rpx;
  font-weight: 600;
  line-height: 1.4;
  letter-spacing: 1rpx;
}

/* === 2. 综合分回顾 === */
.rp-overall-card {
  background: #FFFFFF;
  margin: 24rpx 32rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-overall-head {
  margin-bottom: 20rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-overall-eyebrow {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 4rpx;
  font-weight: 500;
  display: block;
}
.rp-overall-title {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 2rpx;
  display: block;
  margin-top: 6rpx;
}
.rp-overall-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}
.rp-overall-col {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  padding: 16rpx;
  background: rgba(15, 27, 45, 0.02);
  border: 1rpx solid rgba(15, 27, 45, 0.04);
}
.rp-overall-label {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
}
.rp-overall-val {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
}

/* === 3. 核心问题诊断 === */
.rp-issues-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-issue-item {
  padding: 24rpx 24rpx 24rpx 28rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-left: 6rpx solid #C62828;
  margin-bottom: 16rpx;
  background: #FFFFFF;
  transition: all 0.2s;
  &:last-child { margin-bottom: 0; }
  &:active { background: rgba(15, 27, 45, 0.02); }
}
.rp-issue-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}
.rp-issue-num {
  font-family: $ff-base;
  font-size: 22rpx;
  font-weight: 700;
  color: #8B8B8B;
  letter-spacing: 1rpx;
}
.rp-issue-tag {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #FFFFFF;
  padding: 3rpx 10rpx;
  letter-spacing: 1rpx;
  font-weight: 600;
}
.rp-issue-cat {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  padding: 2rpx 10rpx;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 4rpx;
}
.rp-issue-title {
  font-family: $ff-base;
  font-size: 30rpx;
  font-weight: 600;
  color: #0F1B2D;
  line-height: 1.4;
  margin-bottom: 16rpx;
  letter-spacing: 1rpx;
}
.rp-issue-impact-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}
.rp-issue-impact-pill {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  padding: 6rpx 12rpx;
  background: rgba(198, 40, 40, 0.06);
  border: 1rpx solid rgba(198, 40, 40, 0.2);
}
.rp-issue-impact-pill-icon {
  color: #C62828;
  font-weight: 700;
  font-size: 20rpx;
}
.rp-issue-impact-pill-text {
  font-size: 22rpx;
  color: #0F1B2D;
  font-weight: 500;
  letter-spacing: 0.3rpx;
}

/* === 4. 每个问题深度分析 === */
.rp-deep-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-deep-item {
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  margin-bottom: 16rpx;
  overflow: hidden;
  transition: all 0.3s;
  &:last-child { margin-bottom: 0; }
  &.rp-deep-item-open { border-color: #C9A96E; box-shadow: 0 4rpx 12rpx rgba(201, 169, 110, 0.12); }
}
.rp-deep-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  background: #FFFFFF;
}
.rp-deep-head-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
  flex: 1;
  min-width: 0;
}
.rp-deep-num {
  width: 40rpx;
  height: 40rpx;
  line-height: 40rpx;
  text-align: center;
  background: #C62828;
  color: #FFFFFF;
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}
.rp-deep-head-text {
  flex: 1;
  min-width: 0;
}
.rp-deep-title {
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 600;
  color: #0F1B2D;
  display: block;
  letter-spacing: 0.5rpx;
  margin-bottom: 2rpx;
}
.rp-deep-meta {
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
  display: block;
}
.rp-deep-toggle {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 50%;
  flex-shrink: 0;
  transition: transform 0.3s;
}
.rp-deep-toggle-open { transform: rotate(0deg); }
.rp-deep-body {
  padding: 8rpx 24rpx 24rpx;
  background: #FAF8F4;
  border-top: 1rpx solid rgba(15, 27, 45, 0.06);
}
.rp-deep-block {
  display: flex;
  gap: 16rpx;
  padding: 16rpx 0;
  border-bottom: 1rpx dashed rgba(15, 27, 45, 0.08);
  &:last-child { border-bottom: none; padding-bottom: 4rpx; }
}
.rp-deep-block-tag {
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 700;
  color: #C9A96E;
  letter-spacing: 1rpx;
  flex-shrink: 0;
  width: 32rpx;
  padding-top: 2rpx;
}
.rp-deep-block-body { flex: 1; min-width: 0; }
.rp-deep-block-label {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  display: block;
  margin-bottom: 6rpx;
  text-transform: uppercase;
}
.rp-deep-block-text {
  font-size: 26rpx;
  color: #0F1B2D;
  line-height: 1.7;
  display: block;
  letter-spacing: 0.3rpx;
}
.rp-deep-block-impact .rp-deep-block-tag { color: #C62828; }
.rp-deep-impact-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  background: rgba(198, 40, 40, 0.04);
  padding: 12rpx 16rpx;
  border-left: 2rpx solid #C62828;
}
.rp-deep-impact-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12rpx;
}
.rp-deep-impact-key {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
}
.rp-deep-impact-val {
  font-family: $ff-base;
  font-size: 26rpx;
  font-weight: 700;
  letter-spacing: 0.3rpx;
}
.rp-deep-block-how .rp-deep-block-tag { color: #2E7D32; }
.rp-deep-when {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 12rpx;
  padding: 8rpx 12rpx;
  background: rgba(201, 169, 110, 0.1);
  border-left: 2rpx solid #C9A96E;
}
.rp-deep-when-icon {
  font-size: 20rpx;
  color: #C9A96E;
}
.rp-deep-when-text {
  font-size: 22rpx;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
  font-weight: 500;
}
.rp-deep-block-result {
  background: rgba(46, 125, 50, 0.04);
  margin: 0 -24rpx -24rpx;
  padding: 16rpx 24rpx;
  border-top: 1rpx solid rgba(46, 125, 50, 0.15);
  border-bottom: none !important;
}
.rp-deep-block-result .rp-deep-block-tag { color: #2E7D32; }

/* === 5. 改善路径（时间轴） === */
.rp-path-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-path-timeline {
  padding: 8rpx 0 0;
}
.rp-path-item {
  display: flex;
  gap: 16rpx;
  padding-bottom: 32rpx;
  &:last-child { padding-bottom: 0; }
}
.rp-path-axis {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24rpx;
  flex-shrink: 0;
  padding-top: 8rpx;
}
.rp-path-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #0F1B2D;
  box-shadow: 0 0 0 4rpx rgba(15, 27, 45, 0.08);
  flex-shrink: 0;
}
.rp-path-line {
  width: 1rpx;
  flex: 1;
  background: rgba(15, 27, 45, 0.15);
  margin-top: 8rpx;
}
.rp-path-item-urgent .rp-path-dot { background: #C62828; box-shadow: 0 0 0 4rpx rgba(198, 40, 40, 0.1); }
.rp-path-item-soon .rp-path-dot { background: #EF6C00; box-shadow: 0 0 0 4rpx rgba(239, 108, 0, 0.1); }
.rp-path-item-mid .rp-path-dot { background: #C9A96E; box-shadow: 0 0 0 4rpx rgba(201, 169, 110, 0.1); }
.rp-path-item-long .rp-path-dot { background: #558B2F; box-shadow: 0 0 0 4rpx rgba(85, 139, 47, 0.1); }
.rp-path-item-ongoing .rp-path-dot { background: #2E7D32; box-shadow: 0 0 0 4rpx rgba(46, 125, 50, 0.1); }

.rp-path-body {
  flex: 1;
  min-width: 0;
}
.rp-path-period {
  display: inline-block;
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  margin-bottom: 12rpx;
}
.rp-path-period-urgent { color: #C62828; }
.rp-path-period-soon { color: #EF6C00; }
.rp-path-period-mid { color: #C9A96E; }
.rp-path-period-long { color: #558B2F; }
.rp-path-period-ongoing { color: #2E7D32; }
.rp-path-action {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  margin-bottom: 8rpx;
}
.rp-path-action-bullet {
  color: #C9A96E;
  font-weight: 700;
  flex-shrink: 0;
}
.rp-path-action-text {
  font-size: 26rpx;
  color: #0F1B2D;
  line-height: 1.7;
  letter-spacing: 0.3rpx;
}
.rp-path-effect {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 12rpx;
  padding: 12rpx 16rpx;
  background: rgba(201, 169, 110, 0.08);
  border-left: 2rpx solid #C9A96E;
}
.rp-path-effect-tag {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 1rpx;
  font-weight: 700;
  flex-shrink: 0;
}
.rp-path-effect-text {
  font-size: 24rpx;
  color: #0F1B2D;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
  flex: 1;
}

/* === 6. 改善后模拟推演 === */
.rp-projection-card {
  background: linear-gradient(135deg, rgba(201, 169, 110, 0.05), #FFFFFF);
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(201, 169, 110, 0.3);
  border-top: 4rpx solid #C9A96E;
}
.rp-proj-compare {
  display: flex;
  align-items: stretch;
  gap: 12rpx;
  margin-bottom: 24rpx;
}
.rp-proj-col {
  flex: 1;
  background: #FFFFFF;
  padding: 20rpx 16rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-proj-col-after {
  background: linear-gradient(180deg, #FFFFFF, rgba(201, 169, 110, 0.05));
  border-color: rgba(201, 169, 110, 0.3);
}
.rp-proj-col-head {
  margin-bottom: 12rpx;
  padding-bottom: 12rpx;
  border-bottom: 1rpx solid rgba(15, 27, 45, 0.08);
}
.rp-proj-col-eyebrow {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 4rpx;
  font-weight: 600;
  display: block;
}
.rp-proj-col-eyebrow-after { color: #C9A96E; }
.rp-proj-col-title {
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 600;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  display: block;
  margin-top: 4rpx;
}
.rp-proj-row {
  display: flex;
  flex-direction: column;
  gap: 2rpx;
  padding: 8rpx 0;
  border-bottom: 1rpx dashed rgba(15, 27, 45, 0.06);
  &:last-child { border-bottom: none; }
}
.rp-proj-key {
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
}
.rp-proj-val {
  font-family: $ff-base;
  font-size: 26rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 0.3rpx;
}
.rp-proj-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  flex-shrink: 0;
  width: 80rpx;
}
.rp-proj-arrow-icon {
  font-size: 40rpx;
  color: #C9A96E;
  font-weight: 700;
}
.rp-proj-arrow-text {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #C9A96E;
  letter-spacing: 1rpx;
  font-weight: 600;
}
.rp-proj-gain {
  background: rgba(201, 169, 110, 0.08);
  padding: 20rpx 24rpx;
  border-left: 3rpx solid #C9A96E;
}
.rp-proj-gain-title {
  font-family: $ff-base;
  font-size: 26rpx;
  font-weight: 700;
  color: #0F1B2D;
  letter-spacing: 1rpx;
  display: block;
  margin-bottom: 12rpx;
}
.rp-proj-gain-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6rpx 0;
}
.rp-proj-gain-key {
  font-size: 24rpx;
  color: #8B8B8B;
  letter-spacing: 0.5rpx;
}
.rp-proj-gain-val {
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 700;
  letter-spacing: 0.3rpx;
}

/* === 7. 6 大产品模拟结果 === */
.rp-products-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
}

/* v9 增量：6 卡重做样式（付费版 · 无 blur · 完整证据链）
   关键修复（同 free.vue）：6 产品用具体 SCSS 类名绑定（绕开 var() Sass 解析 bug） */
.rp-product-wrap {
  position: relative;
  margin-top: 24rpx;
  padding: 24rpx 28rpx 28rpx;
  background: rgb(250, 250, 250);
  border-left: 6rpx solid rgb(90, 100, 115);
  border-radius: 8rpx;
  overflow: hidden;
}
.rp-product-wrap.quality_unit {
  background: #EBF3FF;
  border-left-color: #2563EB;
}
.rp-product-wrap.housing_fund {
  background: #F3E8FF;
  border-left-color: #9333EA;
}
.rp-product-wrap.salary {
  background: #FFF1E6;
  border-left-color: #EA580C;
}
.rp-product-wrap.house_owner {
  background: #FEE7E7;
  border-left-color: #DC2626;
}
.rp-product-wrap.tax {
  background: #FAF3E3;
  border-left-color: #B89554;
}
.rp-product-wrap.invoice {
  background: #E0F4F8;
  border-left-color: #0891B2;
}
.rp-product-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 20rpx;
}
.rp-product-icon {
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
.rp-product-head-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}
.rp-product-name-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}
.rp-product-name {
  font-family: $ff-base;
  font-size: 30rpx;
  color: #0F1B2D;
  font-weight: 700;
  letter-spacing: 0.5rpx;
  line-height: 1.2;
  display: block;
}
.rp-product-star {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #C9A96E;
  font-weight: 700;
  letter-spacing: 0.5rpx;
  padding: 2rpx 10rpx;
  background: #FAF3E3;
  border-radius: 4rpx;
  flex-shrink: 0;
}
.rp-product-sub {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
  line-height: 1.3;
  display: block;
}
.rp-product-level-chip {
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
.rp-product-score {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  margin-bottom: 12rpx;
  flex-wrap: wrap;
}
.rp-product-score-num {
  font-family: $ff-base;
  font-size: 64rpx;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -1rpx;
}
.rp-product-score-unit {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
}
.rp-product-score-pass {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 0.5rpx;
  margin-left: auto;
  padding: 4rpx 12rpx;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 4rpx;
}
.rp-product-limit {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  padding: 12rpx 16rpx;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 4rpx;
  margin-bottom: 16rpx;
}
.rp-product-limit-label {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
  flex-shrink: 0;
}
.rp-product-limit-val {
  font-family: $ff-base;
  font-size: 32rpx;
  font-weight: 700;
  letter-spacing: 0.5rpx;
  line-height: 1.2;
  flex: 1;
  min-width: 0;
}
.rp-product-limit-actual {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
  padding: 4rpx 10rpx;
  background: #FAF3E3;
  color: #8C6F36;
  border-radius: 4rpx;
  flex-shrink: 0;
}
/* 完整证据链区：付费版不模糊（无 .rp-product-evidence-locked 类） */
.rp-product-evidence {
  position: relative;
  padding: 16rpx 18rpx;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6rpx;
  min-height: 80rpx;
}
.rp-ev-block {
  margin-bottom: 12rpx;
}
.rp-ev-block:last-child {
  margin-bottom: 0;
}
.rp-ev-label {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #5A6473;
  letter-spacing: 1rpx;
  font-weight: 600;
  margin-bottom: 6rpx;
  display: block;
}
.rp-ev-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 2rpx 0;
  font-family: $ff-base;
  font-size: 22rpx;
  line-height: 1.5;
}
.rp-ev-rule {
  flex: 1;
  min-width: 0;
  color: #1A1A1A;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rp-ev-score {
  font-size: 22rpx;
  font-weight: 700;
  flex-shrink: 0;
  font-family: $ff-base;
}
.rp-ev-score-neg {
  color: #9B2226;
}
.rp-ev-reason {
  font-family: $ff-base;
  font-size: 22rpx;
  color: #1A1A1A;
  line-height: 1.5;
  letter-spacing: 0.3rpx;
}
.rp-ev-tag {
  display: inline-block;
  font-family: $ff-base;
  font-size: 20rpx;
  color: #5A6473;
  padding: 4rpx 12rpx;
  background: rgba(15, 27, 45, 0.04);
  border-radius: 4rpx;
  margin: 0 8rpx 6rpx 0;
  line-height: 1.3;
  letter-spacing: 0.3rpx;
}

/* === 8. 申请顺序策略 === */
.rp-strategy-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-top: 4rpx solid #C9A96E;
}
.rp-strat-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.rp-strat-item {
  display: flex;
  gap: 20rpx;
  padding: 20rpx;
  background: #FFFFFF;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  align-items: center;
  &.rp-strat-item-first {
    background: linear-gradient(135deg, rgba(201, 169, 110, 0.06), rgba(201, 169, 110, 0.02));
    border-color: rgba(201, 169, 110, 0.3);
  }
}
.rp-strat-priority {
  font-family: $ff-base;
  font-size: 22rpx;
  font-weight: 700;
  color: #8B8B8B;
  letter-spacing: 1rpx;
  flex-shrink: 0;
  width: 80rpx;
}
.rp-strat-item-first .rp-strat-priority { color: #C9A96E; }
.rp-strat-body {
  flex: 1;
  min-width: 0;
}
.rp-strat-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 4rpx;
}
.rp-strat-name {
  font-family: $ff-base;
  font-size: 28rpx;
  font-weight: 600;
  color: #0F1B2D;
  letter-spacing: 0.5rpx;
  flex: 1;
  min-width: 0;
}
.rp-strat-pass {
  font-family: $ff-base;
  font-size: 22rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  padding: 2rpx 10rpx;
  background: rgba(0, 0, 0, 0.04);
}
.rp-strat-reason {
  font-size: 22rpx;
  color: #8B8B8B;
  letter-spacing: 0.3rpx;
  line-height: 1.6;
  display: block;
}
.rp-strat-warning {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 24rpx;
  padding: 16rpx 20rpx;
  background: rgba(239, 108, 0, 0.06);
  border-left: 3rpx solid #EF6C00;
}
.rp-strat-warning-icon {
  color: #EF6C00;
  font-size: 24rpx;
  font-weight: 700;
  flex-shrink: 0;
}
.rp-strat-warning-text {
  font-size: 24rpx;
  color: #0F1B2D;
  line-height: 1.6;
  letter-spacing: 0.3rpx;
  flex: 1;
}
.rp-strat-raw {
  padding: 20rpx;
  background: rgba(15, 27, 45, 0.02);
  border: 1rpx solid rgba(15, 27, 45, 0.06);
}
.rp-strat-raw-text {
  font-size: 26rpx;
  color: #0F1B2D;
  line-height: 1.7;
  letter-spacing: 0.3rpx;
  display: block;
}

/* === 免责声明 === */
.rp-disclaimer {
  margin: 48rpx 32rpx 0;
  padding: 24rpx;
  background: rgba(0, 0, 0, 0.02);
  border: 1rpx solid rgba(0, 0, 0, 0.06);
}
.rp-disc-title {
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 600;
  color: #0F1B2D;
  display: block;
  margin-bottom: 12rpx;
  letter-spacing: 1rpx;
}
.rp-disc-line {
  font-size: 22rpx;
  color: #8B8B8B;
  line-height: 1.8;
  display: block;
  white-space: pre-wrap;
  letter-spacing: 0.3rpx;
}

/* ============================================
   v4 增量 · M5 30/60/90 预测表
   ============================================ */
.rp-m5-card {
  background: #FFFFFF;
  margin: 0 32rpx 24rpx;
  padding: 32rpx 0 24rpx;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  border-top: 4rpx solid #C9A96E;
}
.rp-m5-scroll { width: 100%; }
.rp-m5-list {
  display: inline-flex;
  flex-direction: row;
  gap: 16rpx;
  padding: 0 32rpx;
}
.rp-m5-col {
  width: 220rpx;
  background: #FAFAF7;
  border: 1rpx solid rgba(15, 27, 45, 0.08);
  padding: 20rpx 16rpx;
  position: relative;
  flex-shrink: 0;
  text-align: center;
}
.rp-m5-col.rp-m5-cur {
  background: linear-gradient(180deg, #FFFFFF, rgba(201, 169, 110, 0.08));
  border-color: rgba(201, 169, 110, 0.5);
}
.rp-m5-day {
  font-family: $ff-base;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 2rpx;
  margin-bottom: 8rpx;
}
.rp-m5-lv {
  font-family: $ff-base;
  font-size: 36rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  line-height: 1;
  margin-bottom: 4rpx;
}
.rp-m5-score {
  font-family: $ff-base;
  font-size: 24rpx;
  font-weight: 600;
  color: #0F1B2D;
  margin-bottom: 8rpx;
  letter-spacing: 0.5rpx;
}
.rp-m5-unit { font-size: 18rpx; color: #8B8B8B; font-weight: 400; }
.rp-m5-bar {
  height: 6rpx;
  background: rgba(15, 27, 45, 0.08);
  border-radius: 3rpx;
  overflow: hidden;
  margin-bottom: 12rpx;
}
.rp-m5-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #C9A96E 0%, #B89554 100%);
  border-radius: 3rpx;
}
.rp-m5-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 20rpx;
  color: #8B8B8B;
  letter-spacing: 0.3rpx;
  margin-bottom: 6rpx;
  text {
    flex: 1;
    text-align: left;
  }
  b {
    font-family: $ff-base;
    font-weight: 700;
    color: #0F1B2D;
    text-align: right;
  }
}
.rp-m5-tag {
  position: absolute;
  top: 8rpx;
  right: 8rpx;
  background: #C9A96E;
  color: #FFFFFF;
  font-family: $ff-base;
  font-size: 18rpx;
  padding: 2rpx 8rpx;
  letter-spacing: 1rpx;
  font-weight: 600;
}
</style>
