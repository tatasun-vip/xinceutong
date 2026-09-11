<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { bankApi, type Bank, type BankProduct } from '@/api/bank'
import { useAssessmentStore } from '@/store/assessment'

const route = useRoute()
const router = useRouter()
const store = useAssessmentStore()

const bank = ref<Bank | null>(null)
const products = ref<BankProduct[]>([])
const result = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  // 临时：从 store 反推（不持久化 assessment 详情）
  // Phase 7 接入后端 GET /api/assessment/free/{id}
  try {
    if (store.bankCode) {
      const [bRes, pRes] = await Promise.all([
        bankApi.detail(store.bankCode),
        bankApi.products(store.bankCode),
      ])
      bank.value = bRes
      products.value = pRes.items
    }
  } catch (e: any) {
    ElMessage.error('加载结果失败：' + e.message)
  } finally {
    loading.value = false
  }
  // 占位：从 URL hash 读取（loading 时用 query 带过来）
  if (route.query.r) {
    try { result.value = JSON.parse(decodeURIComponent(route.query.r as string)) } catch {}
  }
})

function goBanks() { router.push('/banks') }
function goHome() { router.push('/') }

const LEVEL_COLORS: Record<string, string> = {
  S: '#8E6F2C',
  A: '#2E7D32',
  B: '#0288D1',
  C: '#ED6C02',
  D: '#C62828',
  E: '#5C6B7C',
}

const LEVEL_DESC: Record<string, string> = {
  S: '极佳 · 优质客户',
  A: '优秀 · 良好准入',
  B: '良好 · 标准准入',
  C: '一般 · 准入边界',
  D: '较弱 · 谨慎准入',
  E: '极弱 · 暂缓申请',
}
</script>

<template>
  <div class="rs" v-loading="loading">
    <div class="rs-inner container" v-if="bank">
      <div class="rs-head">
        <div class="text-eyebrow">ASSESSMENT RESULT · 测评结果</div>
        <h1 class="rs-title">{{ bank.name }} · 您的专属画像</h1>
        <div class="divider-line"></div>
        <p class="rs-sub">基于您填写的信息和该行评分卡模型，本次为模拟运算结果，不查征信、不读取任何银行数据。</p>
      </div>

      <div class="rs-card">
        <div class="rs-card-left">
          <div class="rs-eyebrow text-eyebrow">CREDIT LEVEL</div>
          <div class="rs-level" :style="{ color: LEVEL_COLORS[result?.level || 'E'] }">
            <span class="rs-level-letter text-num">{{ result?.level || '—' }}</span>
            <span class="rs-level-desc">{{ LEVEL_DESC[result?.level || 'E'] }}</span>
          </div>
          <div class="rs-score">
            <div class="rs-score-label">SCORE</div>
            <div class="rs-score-num text-num">{{ result?.score ?? 0 }}</div>
            <div class="rs-score-bar">
              <div class="rs-score-bar-fill" :style="{ width: (result?.score ?? 0) + '%' }"></div>
            </div>
          </div>
          <div class="rs-pass">
            <span class="rs-pass-label">通过概率</span>
            <span class="rs-pass-val text-num">{{ result?.pass_probability || '—' }}</span>
          </div>
          <div class="rs-summary">{{ result?.free_summary || '请完成测评查看结果' }}</div>
        </div>

        <div class="rs-card-right">
          <div class="rs-stat">
            <div class="rs-stat-label">参考额度</div>
            <div class="rs-stat-val text-num">
              ¥ {{ ((result?.limit_min || 0) / 10000).toFixed(1) }} ~ {{ ((result?.limit_max || 0) / 10000).toFixed(1) }} 万
            </div>
          </div>
          <div class="rs-stat">
            <div class="rs-stat-label">参考利率</div>
            <div class="rs-stat-val text-num">{{ result?.rate_min || 0 }} ~ {{ result?.rate_max || 0 }} %</div>
          </div>
          <div class="rs-stat rs-stat-veto" v-if="result?.veto">
            <div class="rs-stat-label">触发一票否决</div>
            <div class="rs-stat-val" style="font-size: 14px; color: $danger">{{ result.veto.message }}</div>
          </div>
        </div>
      </div>

      <div class="rs-section" v-if="result?.risk_tags?.length || result?.advantages?.length || result?.weak_points?.length">
        <div class="rs-sec-title">
          <span class="text-mono">02 / DETAIL</span>
          <span>详细解读</span>
          <div class="divider-line"></div>
        </div>
        <div class="rs-tags-grid">
          <div class="rs-tag-col" v-if="result?.risk_tags?.length">
            <div class="rs-tag-col-title">风险标签</div>
            <div class="rs-tag-list">
              <span v-for="t in result.risk_tags" :key="t" class="rs-tag rs-tag-risk">{{ t }}</span>
            </div>
          </div>
          <div class="rs-tag-col" v-if="result?.advantages?.length">
            <div class="rs-tag-col-title">您的优势</div>
            <div class="rs-tag-list">
              <span v-for="t in result.advantages" :key="t" class="rs-tag rs-tag-adv">{{ t }}</span>
            </div>
          </div>
          <div class="rs-tag-col" v-if="result?.weak_points?.length">
            <div class="rs-tag-col-title">待优化</div>
            <div class="rs-tag-list">
              <span v-for="t in result.weak_points" :key="t" class="rs-tag rs-tag-weak">{{ t }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="rs-section">
        <div class="rs-sec-title">
          <span class="text-mono">03 / PRODUCTS</span>
          <span>{{ bank.name }} · 推荐产品</span>
          <div class="divider-line"></div>
        </div>
        <div class="rs-products">
          <div
            v-for="p in products"
            :key="p.id"
            :class="['rs-product', p.recommend ? 'rs-product-rec' : '']"
          >
            <div class="rs-product-head">
              <div>
                <div class="rs-product-name">{{ p.name }}</div>
                <div class="rs-product-sub">{{ p.subtitle }}</div>
              </div>
              <span v-if="p.recommend" class="rs-product-badge">推荐</span>
            </div>
            <div class="divider-line" style="margin: 12px 0"></div>
            <div class="rs-product-meta">
              <div class="rs-product-stat">
                <div class="rs-product-stat-label">额度</div>
                <div class="rs-product-stat-val text-num">{{ p.limit_min }}-{{ p.limit_max }} 万</div>
              </div>
              <div class="rs-product-stat">
                <div class="rs-product-stat-label">利率</div>
                <div class="rs-product-stat-val text-num">{{ p.rate_min }}-{{ p.rate_max }} %</div>
              </div>
              <div class="rs-product-stat">
                <div class="rs-product-stat-label">准入分数</div>
                <div class="rs-product-stat-val text-num">≥ {{ p.pass_score_min }}</div>
              </div>
            </div>
            <div class="rs-product-features" v-if="p.features?.length">
              <span v-for="f in p.features" :key="f" class="rs-product-tag">{{ f }}</span>
            </div>
            <div class="rs-product-req" v-if="p.requirement">准入：{{ p.requirement }}</div>
          </div>
        </div>
      </div>

      <div class="rs-foot">
        <el-button size="large" @click="goBanks">选择其他银行</el-button>
        <el-button type="primary" size="large" @click="goHome">返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.rs {
  background: $bg;
  padding: $space-12 0 $space-20;
  min-height: calc(100vh - #{$header-height} - 28px);
}

.rs-inner {
  max-width: 1080px;
}

.rs-head {
  text-align: center;
  margin-bottom: $space-10;
  .divider-line { margin: $space-3 auto; }
}

.rs-title {
  font-family: $ff-serif;
  font-size: 32px;
  color: $primary;
  font-weight: 600;
  margin: $space-3 0;
  letter-spacing: 1px;
}

.rs-sub {
  font-size: $font-sm;
  color: $text-secondary;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.7;
}

/* ========== 顶部大卡 ========== */
.rs-card {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  background: $bg-card;
  border: 1px solid $border-light;
  border-top: 3px solid $primary;
  margin-bottom: $space-8;
}

.rs-card-left {
  padding: $space-8 $space-6;
  border-right: 1px solid $border-light;
}

.rs-eyebrow {
  margin-bottom: $space-3;
}

.rs-level {
  display: flex;
  align-items: baseline;
  gap: $space-3;
  margin-bottom: $space-6;
}

.rs-level-letter {
  font-family: $ff-serif;
  font-size: 96px;
  font-weight: 700;
  line-height: 1;
}

.rs-level-desc {
  font-size: $font-lg;
  color: $text-secondary;
  letter-spacing: 1px;
}

.rs-score {
  margin-bottom: $space-5;
}

.rs-score-label {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.rs-score-num {
  font-family: $ff-serif;
  font-size: 48px;
  color: $primary;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 8px;
}

.rs-score-bar {
  height: 6px;
  background: $border-light;
  position: relative;
}

.rs-score-bar-fill {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, $primary 0%, $accent 100%);
  transition: width 0.6s ease;
}

.rs-pass {
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: $space-3 $space-4;
  background: $primary-tint;
  border-left: 3px solid $accent;
  margin-bottom: $space-5;
}

.rs-pass-label {
  font-size: $font-sm;
  color: $text-secondary;
  letter-spacing: 0.5px;
}

.rs-pass-val {
  font-size: $font-lg;
  color: $accent-dark;
  font-weight: 600;
}

.rs-summary {
  font-size: $font-sm;
  color: $text-secondary;
  line-height: 1.8;
  padding: $space-3 $space-4;
  background: $bg-soft;
  border-left: 2px solid $border-regular;
}

.rs-card-right {
  padding: $space-8 $space-6;
  display: flex;
  flex-direction: column;
  gap: $space-5;
}

.rs-stat-label {
  font-family: $ff-mono;
  font-size: $font-xs;
  color: $text-weak;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.rs-stat-val {
  font-family: $ff-serif;
  font-size: 24px;
  color: $primary;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.rs-stat-veto .rs-stat-val { color: $danger !important; }

/* ========== 标签 ========== */
.rs-section {
  background: $bg-card;
  border: 1px solid $border-light;
  padding: $space-6;
  margin-bottom: $space-6;
}

.rs-sec-title {
  display: flex;
  align-items: center;
  gap: $space-3;
  font-family: $ff-serif;
  font-size: $font-lg;
  color: $primary;
  font-weight: 600;
  margin-bottom: $space-4;
  .divider-line { margin: 0; }
}

.rs-tags-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-5;
}

.rs-tag-col-title {
  font-size: $font-sm;
  color: $text-secondary;
  margin-bottom: $space-2;
  letter-spacing: 0.5px;
}

.rs-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.rs-tag {
  font-size: $font-xs;
  padding: 4px 10px;
  border: 1px solid;
  letter-spacing: 0.5px;
}

.rs-tag-risk { color: $danger; border-color: $danger; background: rgba(198, 40, 40, 0.06); }
.rs-tag-adv   { color: $success; border-color: $success; background: rgba(46, 125, 50, 0.06); }
.rs-tag-weak  { color: $warning; border-color: $warning; background: rgba(237, 108, 2, 0.06); }

/* ========== 产品 ========== */
.rs-products {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $space-4;
}

.rs-product {
  background: $bg-soft;
  border: 1px solid $border-light;
  border-left: 3px solid $primary;
  padding: $space-5;
  position: relative;
}

.rs-product-rec {
  border-left-color: $accent;
  background: $accent-bg;
}

.rs-product-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.rs-product-name {
  font-family: $ff-serif;
  font-size: 20px;
  color: $primary;
  font-weight: 700;
  letter-spacing: 1px;
  margin-bottom: 4px;
}

.rs-product-sub {
  font-size: $font-sm;
  color: $text-secondary;
}

.rs-product-badge {
  font-size: $font-xs;
  color: $accent-dark;
  border: 1px solid $accent;
  background: $bg-card;
  padding: 2px 8px;
  letter-spacing: 0.5px;
}

.rs-product-meta {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $space-3;
  margin-bottom: $space-3;
}

.rs-product-stat-label {
  font-size: $font-xs;
  color: $text-weak;
  margin-bottom: 2px;
}

.rs-product-stat-val {
  font-family: $ff-serif;
  font-size: $font-md;
  color: $primary;
  font-weight: 600;
}

.rs-product-features {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
}

.rs-product-tag {
  font-size: $font-xs;
  color: $primary;
  background: $bg-card;
  border: 1px solid $primary-tint;
  padding: 2px 6px;
}

.rs-product-req {
  font-size: $font-xs;
  color: $text-weak;
  margin-top: 4px;
  letter-spacing: 0.5px;
}

/* ========== 底部操作 ========== */
.rs-foot {
  text-align: center;
  margin-top: $space-8;
  display: flex;
  justify-content: center;
  gap: $space-3;
}

@media (max-width: 900px) {
  .rs-card { grid-template-columns: 1fr; }
  .rs-card-left { border-right: none; border-bottom: 1px solid $border-light; }
  .rs-tags-grid, .rs-products { grid-template-columns: 1fr; }
}
</style>
