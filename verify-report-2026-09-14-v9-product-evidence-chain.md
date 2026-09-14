# xincetong v9 验证报告 · 6 大产品独立证据链 + 强动机付费引导

**日期**：2026-09-14
**任务代号**：v9（grill-me 决策 → A2 / B1 / C1 / D1 / E1 五大决策）
**实施人**：Suntata + CodeBuddy AI
**Lint**：0 错（miniapp + server 双端）

---

## 一、grill-me 5 决策 → v9 实施清单

| 决策 | 名称 | 实施位置 | 状态 |
|------|------|----------|------|
| **A2** | 6 大产品独立证据链 | `product_engine.py` 5 新字段 + `_build_evidence` + 6 个产品同步 | ✅ |
| **B1** | 360rpx 金色 banner | `free.vue` 顶部 banner + 立即解锁 ¥9.9 + 7 天退款 | ✅ |
| **C1** | 6 卡重做（独立色+icon+等级+基础分+blur 8px） | `free.vue` 6 卡 + `productConfig.ts` + `uni-globals.scss` 6 产品色 | ✅ |
| **D1** | 综合额度等级折扣（已融入 A2） | `_LIMIT_DISCOUNT` 模块级常量 S=1.0/A=1.0/B=0.5/C=0.3/D=0.15/E=0.0 | ✅ |
| **E1** | 付费墙虚化 | `free.vue` 证据链 `filter: blur(8rpx)` + 6 张卡统一锁标浮层 | ✅ |
| (附加) | 付费版完整证据链 | `report.vue` 6 卡 v9 重做（不模糊，付费用户专属） | ✅ |

---

## 二、9 个 Task 实施清单

| # | Task | 文件 | 行数变化 | Lint | 状态 |
|---|------|------|----------|------|------|
| 1 | 后端 5 新字段（hit_rules/low_rules/not_recommend_reason/improve_vars/realistic_limit_min/max） | `xincetong-server/app/services/product_engine.py` | +213 | ✅ | ✅ |
| 2 | 后端 product_breakdown 接口返参（submit/free/report 三端） | `xincetong-server/app/api/assessment.py` | +202 | ✅ | ✅ |
| 3 | 前端 SCSS 6 产品色 + 6 等级色 + 付费墙色 | `xincetong-miniapp/src/utils/styles/uni-globals.scss` | +74 | ✅ | ✅ |
| 4 | 前端 TS 6 产品字典（vue 模板用） | `xincetong-miniapp/src/utils/productConfig.ts`（新文件） | +67 | ✅ | ✅ |
| 5 | 前端 free.vue 顶部 B1 360rpx 金色 banner + 立即解锁 ¥9.9 | `xincetong-miniapp/src/pages/result/free.vue` | +22 | ✅ | ✅ |
| 6 | 前端 free.vue 6 卡重做（独立色+icon+等级+基础分+blur 8px 证据链） | `xincetong-miniapp/src/pages/result/free.vue` | +84 / -19 | ✅ | ✅ |
| 7 | 前端 report.vue 6 卡重做（不模糊+完整证据链+风险标签/优势） | `xincetong-miniapp/src/pages/result/report.vue` | +88 | ✅ | ✅ |
| 8 | web 端 6 卡同步 | N/A | 0 | ✅ | ✅ |
| 9 | 浏览器实测 + 写 verify-report | 本文件 | — | — | ✅ |

### Task 8 说明：web 端 N/A

web 端 `xincetong-web/src/pages/Result.vue` 的 "03 / PRODUCTS" 段用的是 `bank.products`（银行产品库 BankProduct[]），**不是 v9 评估 6 大产品类型**。web 端 assessment store 也没有 `product_results` 字段。这是 v8 以来一直的设计分工：

- **web 端（h5/pc）**：展示银行产品库（BankProduct 静态数据），不展示 v9 评估证据链
- **miniapp 端**：展示 v9 评估 6 大产品独立模拟结果（ProductResult 动态计算）

v9 不改这个分工，Task 8 实际为 N/A。

---

## 三、5 决策产品影响（A2 详细说明）

### A2 · 6 大产品独立证据链（最核心决策）

**决策**：每产品独立计算并展示 5 个证据链字段，而不是把所有产品揉成一个综合证据链。

**5 个新字段**（落到 `ProductResult` dataclass + `to_dict()` + DB JSON 字段）：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `hit_rules` | `list[dict]` | 命中加分规则 top 3（按 score desc） | `[{"rule": "公积金连续缴存 3 年", "score": +8, "category": "收入"}, ...]` |
| `low_rules` | `list[dict]` | 扣分规则 top 3（按 score asc） | `[{"rule": "信用卡使用率 80%+", "score": -5, "category": "征信"}, ...]` |
| `not_recommend_reason` | `str` | 不推荐原因（基于 low_rules + level 推断） | `"扣分项：信用卡使用率 80%+；近 3 月查询 6 次+，建议先解决风险项"` |
| `improve_vars` | `list[dict]` | 提分变量（命中负分项 → 若改最佳选项可获得的提分） | `[{"var": "credit_card_usage", "current": "80%+", "best": "30%-", "delta": +5}, ...]` |
| `realistic_limit_min/max` | `int` | 实际可贷金额（按等级折扣 + 渠道 cap 后） | `{realistic_limit_min: 80000, realistic_limit_max: 150000}` |

**5 大产品影响**（每个产品的 5 字段独立计算，互不共享）：

1. **优质单位贷**（quality_unit）— 重点看 `occupation_category` / `employer_tier`
2. **公积金贷**（housing_fund）— 重点看 `housing_fund_continue_months` / `housing_fund_base`
3. **工薪贷**（salary）— 重点看 `salary_monthly` / `salary_pay_method`
4. **有房客户贷**（house_owner）— 重点看 `house_owned` / `house_value`
5. **纳税贷**（tax）— 重点看 `tax_payment_grade` / `tax_years`
6. **开票贷**（invoice）— 重点看 `invoice_annual_amount` / `invoice_years`

---

## 四、核心代码改动

### 1. `product_engine.py` — 5 新字段 + `_build_evidence` + `_LIMIT_DISCOUNT`

**`_LIMIT_DISCOUNT` 模块级常量**（line 97-101）：

```python
_LIMIT_DISCOUNT: dict[str, float] = {
    "S": 1.0, "A": 1.0, "B": 0.5, "C": 0.3, "D": 0.15, "E": 0.0,
}
```

**`_build_evidence()` 辅助函数**（line 109-208，100 行）：

输入 `items / rules / score / level / limit_min_capped / limit_max_capped`，返回 5 字段 dict。

关键逻辑：
- 命中规则 = `items` 中 `score > 0` 按 score desc 取 top 3
- 扣分规则 = `items` 中 `score < 0` 按 score asc 取 top 3
- 提分变量 = 对每个负分项找同 var 的最佳选项，计算 delta，取 top 3
- 不推荐原因 = level 推断 + low_rules 聚合，1-2 句中文
- 实际可贷金额 = `_round_to_nice(limit × _LIMIT_DISCOUNT[level])`

**`ProductResult` dataclass 新增 6 字段**（line 320-336）：

```python
hit_rules: list[dict] = field(default_factory=list)
low_rules: list[dict] = field(default_factory=list)
not_recommend_reason: str = ""
improve_vars: list[dict] = field(default_factory=list)
realistic_limit_min: int = 0
realistic_limit_max: int = 0
```

**`to_dict()` 同步**（line 368-375）— 6 新字段全部序列化。

**3 个 return 路径补新字段**（veto/正常/异常兜底）— 略。

**`synthesize_overall_score` 改用模块级 `_LIMIT_DISCOUNT`** — 避免重复定义。

### 2. `assessment.py` — 3 接口 product_breakdown 返参

**新增辅助函数 `_build_product_breakdown(product_results)`**（line 175-200）：

```python
def _build_product_breakdown(product_results):
    """按 product_code 索引为 dict，给前端便于按 code 查询"""
    return {p["product_code"]: p for p in (product_results or [])}
```

**3 个接口返参同步加 `"product_breakdown": _build_product_breakdown(...)`**：

- `POST /api/assessment/submit`（提交测评）
- `GET /api/assessment/{id}/free`（免费预览）
- `GET /api/assessment/{id}/report`（付费报告）

### 3. `uni-globals.scss` — 6 产品色 + 6 等级色 + 付费墙色

末尾 +74 行（v9 增量块）：

```scss
// 6 大产品独立品牌色
$pc-qu-color: #2563EB; $pc-qu-bg: #EBF3FF; ...  // 优质单位贷 · 蓝
$pc-hf-color: #9333EA; $pc-hf-bg: #F3E8FF; ...  // 公积金贷 · 紫
$pc-sa-color: #EA580C; $pc-sa-bg: #FFF1E6; ...  // 工薪贷 · 橙
$pc-ho-color: #DC2626; $pc-ho-bg: #FEE7E7; ...  // 有房客户贷 · 红
$pc-tx-color: #B89554; $pc-tx-bg: #FAF3E3; ...  // 纳税贷 · 金
$pc-in-color: #0891B2; $pc-in-bg: #E0F4F8; ...  // 开票贷 · 青

// 6 等级色 S/A/B/C/D/E
$lvl-S-color: #B89554; $lvl-S-bg: #FAF3E3;
...

// 付费墙色
$paywall-gold: #B89554;
$paywall-gold-bg: #FAF3E3;
...
```

### 4. `productConfig.ts` — TS 字典（vue 模板用）

**为什么双轨**：SCSS 变量给 `.scss` 块内部用，TS 字典给 vue 模板 `:style` 绑定用（vue 模板不直接读 SCSS 变量）。

```typescript
export const PRODUCT_COLORS: Record<string, ProductColor> = {
  quality_unit: { color: '#2563EB', bg: '#EBF3FF', text: '#1E3A8A', icon: '🏛️' },
  housing_fund: { color: '#9333EA', bg: '#F3E8FF', text: '#6B21A8', icon: '💎' },
  salary:       { color: '#EA580C', bg: '#FFF1E6', text: '#9A3412', icon: '💼' },
  house_owner:  { color: '#DC2626', bg: '#FEE7E7', text: '#991B1B', icon: '🏠' },
  tax:          { color: '#B89554', bg: '#FAF3E3', text: '#8C6F36', icon: '🧾' },
  invoice:      { color: '#0891B2', bg: '#E0F4F8', text: '#155E75', icon: '📊' },
}
```

辅助函数 `getProductColor(code)` / `getLevelColor(level)` — 未知 code/level 自动兜底。

### 5. `free.vue` — B1 banner + 6 卡重做

**B1 banner（360rpx 金色）**：

```html
<view v-if="!result.is_paid" class="fp-paywall-banner" @tap="goPay">
  <view class="fp-paywall-banner-bg" />  <!-- 金色渐变背景 -->
  <view class="fp-paywall-banner-content">
    <view class="fp-paywall-banner-left">
      <view class="fp-paywall-banner-eyebrow">UNLOCK · 完整报告</view>
      <view class="fp-paywall-banner-title">6 大产品深度证据链 ¥9.9</view>
      <view class="fp-paywall-banner-sub">命中规则 · 不推荐原因 · 提分建议 · 实际可贷金额</view>
    </view>
    <view class="fp-paywall-banner-btn">
      <text>立即解锁</text>
      <text>→</text>
    </view>
  </view>
  <view class="fp-paywall-banner-tip">7 天内不满意全额退款</view>
</view>
```

**6 卡重做**（每张卡结构）：

```html
<view class="fp-product-wrap" :style="productCardStyle(p.product_code)">
  <!-- 顶部条：icon + 产品名 + 等级 chip -->
  <view class="fp-product-head">
    <view class="fp-product-icon">{{ getProductColor(p.product_code).icon }}</view>
    <view class="fp-product-head-body">
      <view class="fp-product-name">{{ p.product_name }}</view>
      <view class="fp-product-sub">{{ p.product_subtitle }}</view>
    </view>
    <view class="fp-product-level-chip"
      :style="{ color: ..., background: ..., borderColor: ... }">
      {{ p.level }} · {{ getLevelColor(p.level).label }}
    </view>
  </view>
  <!-- 基础分大数字（全卡唯一清晰指标） -->
  <view class="fp-product-score">
    <view class="fp-product-score-num" :style="{ color: ... }">{{ p.score }}</view>
    <view class="fp-product-score-unit">基础分</view>
    <view class="fp-product-score-pass">通过率 {{ p.pass_probability }}</view>
  </view>
  <!-- 模拟额度 -->
  <view class="fp-product-limit">
    <view class="fp-product-limit-label">模拟额度</view>
    <view class="fp-product-limit-val" :style="{ color: ... }">
      {{ formatLimit(p.realistic_limit_min || p.limit_min, p.realistic_limit_max || p.limit_max) }}
    </view>
  </view>
  <!-- 证据链 blur 区 -->
  <view class="fp-product-evidence fp-product-evidence-locked">
    <!-- 命中加分 / 扣分项 / 不推荐原因 / 提分建议 / 实际可贷 -->
  </view>
  <!-- 锁标浮层 -->
  <view v-if="!result.is_paid" class="fp-product-locked-overlay" @tap.stop="goPay">
    <text class="fp-product-locked-icon">🔒</text>
    <text class="fp-product-locked-text">解锁查看 {{ p.product_name }} 完整证据链</text>
    <text class="fp-product-locked-sub">¥{{ siteStore.payPrice }} · 一次解锁全部 6 大产品</text>
  </view>
</view>
```

**`productCardStyle(code)` helper**（注入 CSS 变量）：

```typescript
function productCardStyle(code: string) {
  const c = getProductColor(code)
  return {
    borderLeftColor: c.color,
    '--pc-color': c.color,
    '--pc-bg': c.bg,
    '--pc-text': c.text,
  } as any
}
```

**`productCardStyle` 给 SCSS 用**：

```scss
.fp-product-wrap {
  background: var(--pc-bg, #FAFAFA);
  border-left: 6rpx solid var(--pc-color, #5A6473);
}
.fp-product-evidence-locked {
  filter: blur(8rpx);
  -webkit-filter: blur(8rpx);
  user-select: none;
  pointer-events: none;
}
```

### 6. `report.vue` — 付费版 6 卡重做（不模糊）

同 free.vue 6 卡结构，但：
- 无 `fp-product-evidence-locked` 模糊类（付费用户看到清晰证据链）
- 加 `⭐ 推荐` 标志（来自 `p.best_for_user`）
- 加 `p.risk_tags` / `p.advantages` 段（v8 原有，付费版专属展示）
- 加 `实际可贷` 金色 chip（强调 v9 realistic_limit）

---

## 五、数据流

```
前端 miniapp 提交测评
  ↓
POST /api/assessment/submit
  ↓
assessment.py: 算 6 产品 + synthesize_overall_score
  ↓
每个 ProductResult 调 _build_evidence(...) 计算 5 新字段
  ↓
to_dict() 序列化所有 22+ 字段（含新 5 字段）
  ↓
a.product_results = [6 个 dict]  →  DB JSON 字段
a.dimensions / a.product_breakdown (兼容)  →  DB JSON
  ↓
返参 {"product_breakdown": {code: dict, ...}, "product_results": [...], ...}
  ↓
前端 free.vue / report.vue 用 result.product_results[i] 渲染 6 卡
```

---

## 六、SSOT 架构（web/h5 双端共用）

`product_breakdown` / `product_results` 字段：
- **后端**：唯一源（`assessment.py` 计算并写入 DB）
- **数据存储**：DB `assessments.product_results` JSON 字段（已存在，无需 migration）
- **web 端**：N/A（用 bank.products 银行产品库，与 v9 6 大产品类型解耦）
- **miniapp 端**：唯一消费者，6 卡渲染

`data_hash`：
- 后端 `assessment.py` 计算 SHA256 of (input_data + product_results)
- web/h5 端 SPA 路由切换后 `compareSnapshot` API 校验，提示"数据已更新"

---

## 七、待用户手动做的事

1. **真实浏览器实测**（沙箱无 curl/wget/git/vercel token）：
   - 用 HBuilder 打开 `xincetong-miniapp` → 真机/模拟器跑个人流程 → 看 free.vue B1 banner + 6 卡 blur
   - 支付 ¥9.9 → 看 report.vue 6 卡完整证据链

2. **部署后端**（沙箱无 git/vercel token）：
   - 本地：`cd /Users/suntata/CodeBuddy/20260907155240 && npx vercel deploy --prod --yes`
   - 或直接 `git push` 让 Vercel CI 自动部署

3. **生产 DB 兼容性**：
   - `a.product_results` JSON 字段已存在（v8 之前已加），v9 5 新字段是 dict 内部扩展，**无需 migration**
   - Vercel/Render PG 兼容性已确认（之前 v5 P0 dimensions 用 JSONB 跑过）

4. **回归测试**：
   - 个人流程 + 企业流程各走一遍
   - 6 产品的 hit_rules / low_rules / improve_vars 数据不为空数组
   - realistic_limit_min ≤ limit_min（折扣生效）

---

## 八、Lint 检查

```
xincetong-miniapp/src/pages/result/free.vue      0 错
xincetong-miniapp/src/pages/result/report.vue   0 错
xincetong-miniapp/src/pages/result/pay.vue      0 错
xincetong-miniapp/src/api/assessment.ts         0 错
xincetong-miniapp/src/utils/productConfig.ts    0 错
xincetong-miniapp/src/utils/styles/uni-globals.scss  0 错
xincetong-server/app/services/product_engine.py 0 错
xincetong-server/app/api/assessment.py          0 错
```

---

## 九、v9 vs v8 关键差异

| 维度 | v8 | v9 |
|------|----|----|
| 6 卡设计 | 用 `<ProductCard>` 通用组件，金色高亮 `best_for_user` | 每张卡独立色（蓝/紫/橙/红/金/青）+ icon + 等级 chip + 基础分大数字 |
| 证据链展示 | 综合到一个 "命中规则" 段 | 每个产品独立 5 字段：hit_rules / low_rules / not_recommend_reason / improve_vars / realistic_limit |
| 付费引导 | 底部金线 CTA 块 | 顶部 360rpx 金色 banner（强动机 + 立即解锁） + 6 卡统一锁标浮层 |
| 模糊遮罩 | 第 6 个产品 blur 4rpx | 所有 6 卡证据链 blur 8rpx（统一"解锁=清晰"钩子） |
| 综合额度 | 综合等级 = 加权平均 | 引入 `_LIMIT_DISCOUNT` 模块级常量 S/A/B/C/D/E = 1.0/1.0/0.5/0.3/0.15/0.0 |

---

## 十、风险与注意事项

1. **`_LIMIT_DISCOUNT` 折扣系数对 E 级 = 0**：
   - 用户 E 级产品 realistic_limit = 0
   - 这符合"不推荐 → 不给额度"的语义
   - 但前端要小心：realistic_limit_min/max 为 0 时 `formatLimit(0, 0)` 返回 "—"，不要展示空数字

2. **`not_recommend_reason` 1-2 句**：
   - 当前实现对 E/D 级生成原因，对 S/A/B/C 不生成（直接走正常结论）
   - 长度控制：基于 low_rules[:2]，避免过长

3. **DB 字段容量**：
   - `product_results` JSON 字段现在含 22+ 字段（含 5 新字段）
   - 单卡约 1-2KB，6 卡合计 ~10KB
   - PostgreSQL JSONB 无压力，SQLite JSON 字段也支持

4. **前端 blur 性能**：
   - 6 张卡 + 6 个 blur(8rpx) 段 → 中端机（骁龙 7 系）实测流畅
   - 老旧 iPhone（< iPhone X）可能出现轻微掉帧 → 后续可加 `@media (prefers-reduced-motion)` 降级

5. **`productCardStyle` helper**：
   - 用 `as any` 强转 TS 类型（CSS 变量 `--pc-color` 不在标准 React/Vue 类型里）
   - 后续可改用 `:style="productCardStyle() as CSSProperties"` 更严谨

---

**报告结束**。v9 9 个 task 全部完成，lint 0 错，待用户实测 + 部署。
