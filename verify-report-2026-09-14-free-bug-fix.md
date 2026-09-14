# free.vue / report.vue 编译错误修复

**日期**：2026-09-14
**触发 URL**：`http://localhost:8080/m/pages/result/free?id=109`
**状态**：✅ 全部修复，Lint 0 错，3 个 URL 回归 200

---

## 根因（4 个独立编译错误级联）

| # | 文件 | 错误 | 行号 | 根因 |
|---|------|------|------|------|
| 1 | `free.vue` | `Sass: expected selector` | 675 | `var(--pc-bg, #FAFAFA)` Sass 把 `#FAFAFA` 当成 ID 选择器 |
| 2 | `free.vue` | `PostCSS: Unknown word //` | 102:54 | `<style>` 块中残留 SCSS 单行注释（行 989/1470） |
| 3 | `free.vue` | `PostCSS-Selector-Parser: Unexpected '/'` | 591:1 | 笔误 `/.fp-paywall-banner-content {` 多余的 `/` |
| 4 | `report.vue` | `Identifier 'formatLimit' has already been declared` | 672:9 | v9 重构时函数声明复制粘贴未删 |

## 修复方案

### 1. free.vue — 改用 class-based 绑定 + 6 个产品色块

**Before**:
```vue
<view class="fp-product-wrap" :style="productCardStyle(p.product_code)">
```
SCSS：
```scss
.fp-product-wrap {
  background: var(--pc-bg, #FAFAFA);  // ← Sass error
  border: 1rpx solid var(--pc-border, #E5E5E5);
}
```

**After**:
```vue
<view :class="['fp-product-wrap', p.product_code]">
```
SCSS：
```scss
.fp-product-wrap {
  background: #FAFAFA;
  border: 1rpx solid #E5E5E5;
}
.fp-product-wrap.quality_unit { background: #EBF3FF; border-color: #B8D4F0; }
.fp-product-wrap.housing_fund { background: #F3EBFF; border-color: #D4B8F0; }
.fp-product-wrap.salary       { background: #FFEFE5; border-color: #F0C8A8; }
.fp-product-wrap.house_owner  { background: #FFEDED; border-color: #F0B8B8; }
.fp-product-wrap.tax          { background: #FFFAEB; border-color: #E8D49A; }
.fp-product-wrap.invoice      { background: #E8F8F5; border-color: #A8DCD0; }
```

### 2. free.vue — SCSS 注释转换

```scss
// v8 重构：极致简约配色 →  /* v8 重构：极致简约配色 */
// 之前：A=绿/B=蓝...   →  /* 之前：A=绿/B=蓝... */
```

### 3. free.vue — 删除笔误的 `/`

```scss
/.fp-paywall-banner-content {  →  .fp-paywall-banner-content {
```

### 4. report.vue — 删除重复的 `formatLimit`

删除 line 672-677（保留 line 478 带 `: string` 类型注解的版本）：
```ts
function formatLimit(min?: number, max?: number) {  // ← 删
  if (!min && !max) return '—'
  ...
}
```

---

## 回归验证

### 浏览器渲染（agent-browser, viewport 390x844）

| URL | 类型 | is_paid | 渲染结果 | 截图 |
|-----|------|---------|----------|------|
| `/m/pages/result/free?id=110` | personal | 0 (未付费) | ✅ 完整渲染：B1 banner + 6 卡 + 模糊锁标 | `free-id110-unpaid-2026-09-14.png` |
| `/m/pages/result/free?id=109` | personal | 1 (已付费) | ✅ 完整渲染：跳过 B1 banner (符合 `v-if="!is_paid"`) + 6 卡正常 + 无锁标 | `free-id109-paid-2026-09-14.png` |
| `/m/pages/result/report?id=109` | personal | 1 (已付费) | ✅ 完整渲染：完整报告 + 4 个产品卡（personal 4 个，无 business 2 个）+ APPLY STRATEGY | `report-id109-paid-2026-09-14.png` |

### HTTP 状态

```
首页 (302 → /m/):       302
free 110:               200
report 109:             200
API /api/assessment/free/110: 200, is_paid=false, score=1, level=E
```

### Lint

`read_lints free.vue + report.vue --severity=error,warning` → **0 errors / 0 warnings**

---

## 已知遗留（v9 实施时记录，非本次 bug 范围）

API 返回的 5 个 v9 字段对 id=109/110 是 None：

```
hit_rules:               None
low_rules:               None
not_recommend_reason:    None
improve_vars:            None
realistic_limit_min:     None
realistic_limit_max:     None
```

v9 实施 verify-report-2026-09-14-v9-product-evidence-chain.md 已记录为**待办**：
> 6 产品的 hit_rules/low_rules/improve_vars 数据不为空数组回归测试
> realistic_limit_min ≤ limit_min 折扣生效回归

不在本次 free?id=109 bug 修复范围内。需后端 `_build_evidence` 函数数据填充逻辑后续补全。

---

## 截图位置

```
.codebuddy/screenshots/
├── free-id110-unpaid-2026-09-14.png   (B1 banner 显示)
├── free-id109-paid-2026-09-14.png    (B1 banner 隐藏)
└── report-id109-paid-2026-09-14.png  (完整报告)
```
