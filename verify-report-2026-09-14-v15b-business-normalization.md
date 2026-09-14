# v15b 企业流程评估规范化（2026-09-14 21:22）

## 问题
v15a 只修了 **personal 流程** 的规范化（house_owner / annual_tax / annual_invoice / salary 等 dict.get + 字符串 ==），但 **business 流程** 还有大量遗漏：

### A. assessment.py 字符串 == 比较未规范化（17 处）
- `_build_suggestions()` 13+ 处 `input_data.get(x) == "y"` 或 `in (a,b)`
- `_aggregate_top_issues()` input_match 的 `in` 比较

### B. assessment.py income_map 内联 dict bug
- key 有空格（"3-5万"/"5000 以下"）但前端 norm 后变 "3万-5万"/"5000以下" → 不匹配 → 0
- v15a 我加了 norm 但 dict key 设计本身有问题

### C. scorecard_engine.py _build_tags 闭包
- `has(var, val)` / `in_(var, vals)` 直接 == / in，没规范化
- 影响：风险标签（risks）、优势（advs）、弱点（weaks）判定失效
- 还有自己定义的 `_norm` 函数（与 money.norm 一致但独立存在，会漂移）

## 修复（4 文件）

### 1. `app/utils/money.py`
- 之前 v15a 改 `_norm` → `norm` 公开，本次无需再改

### 2. `app/api/assessment.py`（17 处）
- 顶部加 `from app.utils.money import income_value, norm`
- 加 helper 函数：
  ```python
  def _has_norm(data, var, val) -> bool:  # 单值 ==
  def _in_norm(data, var, vals) -> bool:   # 多值 in
  ```
- `_build_suggestions` 17 处 == / in 全部改 `_has_norm` / `_in_norm`
- `_aggregate_top_issues` input_match 的 in 改 `_in_norm`
- **删除 income_map**（key 不一致 bug），改用 `income_value` × 12

### 3. `app/services/scorecard_engine.py`（3 处）
- 顶部 `from app.utils.money import norm`（v15a 已加）
- `_build_tags` 闭包 `has/in_` 用 `norm` 比较
- **删除本文件 `_norm` 定义**（与 money.norm 逻辑一致，避免 3 处漂移）
- line 249 / 331 `_norm(...)` 改 `norm(...)` 复用

### 4. `app/services/product_engine.py`
- v15a 已修复，无需改动

## 验证（CVM e2e）

### personal 流程（11 字段带空格 vs 不带空格）
| 指标 | 带空格 | 不带空格 | 一致 |
|------|--------|---------|------|
| 综合 score | 66 | 66 | ✓ |
| 综合 limit | 84-120万 | 84-120万 | ✓ |
| quality_unit | 74-100万 | 74-100万 | ✓ |
| housing_fund | 88.5-120万 | 88.5-120万 | ✓ |
| salary | 74-100万 | 74-100万 | ✓ |
| house_owner | 56-75.5万 | 56-75.5万 | ✓ |

### business 流程（21 字段带空格 vs 不带空格）
| 指标 | 带空格 | 不带空格 | 一致 |
|------|--------|---------|------|
| 综合 score | 55 | 55 | ✓ |
| 综合 limit | 37-50万 | 37-50万 | ✓ |
| housing_fund | 88.5-120万 | 88.5-120万 | ✓ |
| house_owner | 57.5-77.5万 | 57.5-77.5万 | ✓ |
| tax | 74-100万 (A) | 74-100万 (A) | ✓ |
| invoice | 12-16万 | 12-16万 | ✓ |

## 部署
- 4 文件：money.py + assessment.py + product_engine.py + scorecard_engine.py
- SSOT: `dist/xincetong-ssot-20260914-2122.zip`
- CVM API active，4 文件编译 OK

## 重要发现
- **assessment.py:269 income_map 是错误实现**：dict key 与前端 norm 后字符串不完全一致（"3-5万" vs "3万-5万" 差一个空格位置）
- 改用 `income_value` 复用 money.INCOME_MIDPOINT（key 已是去空格版本 "3万-5万"）
- 单一规范化函数（money.norm）+ 单一数据源（INCOME_MIDPOINT），不再漂移
