# v15a 额度计算规范化（2026-09-14 21:17）

## 问题
v15 修了 money.py 5 个 value 函数的规范化（dict.get 加 _norm），但**额度计算还有 6 处**没规范化：
- product_engine.py 4 个**内联 dict**（不走 value 函数）
- product_engine.py + scorecard_engine.py 各 1 处**字符串 == 比较**

用户表现：house_owner 税贷 开票贷 等产品即使评分正常，额度仍按"有按揭折扣"算（错的）。

## 修复（3 文件）

### 1. `app/utils/money.py`
- `_norm` → 改名为 `norm`（公开导出），向后兼容 `_norm = norm`
- 5 个 value 函数改用 `norm` 命名

### 2. `app/services/product_engine.py`（4 处 dict + 1 处 ==）
- `from app.utils.money import (... norm)`
- line 496: `data.get("house") == "无按揭"` → `norm(data.get("house")) == "无按揭"`
- line 546: `annual_tax_map.get(annual_tax_str, 0)` → `.get(norm(annual_tax_str), 0)`
- line 552: `tax_rate_map.get(tax_label, 0)` → `.get(norm(tax_label), 0)`
- line 589: `invoice_map.get(annual_invoice_str, 0)` → `.get(norm(annual_invoice_str), 0)`
- line 595: `mult_map.get(invoice_label, 0)` → `.get(norm(invoice_label), 0)`

### 3. `app/services/scorecard_engine.py`（1 处 ==）
- `from app.utils.money import (... norm)`
- line 404: `data.get("house") == "无按揭"` → `norm(data.get("house")) == "无按揭"`
  （v9 综合额度兜底路径用，影响 synthesize_overall_score）

## 回归测试
17/17 PASS：
- money.py 5 个 value 函数：v15 已修
- product_engine 4 个内联 dict：annual_tax / invoice / tax_rate / mult 带空格查表正常
- 字符串比较：`无按揭`/`无 按揭`/`有 按揭` 全部正确
- 边界：None/空串/未知 → 0

## e2e 验证（CVM /api/assessment/submit）

| 输入 | house_owner 额度 | 走分支 |
|------|----------------|--------|
| `house=无按揭` | 56-75.5 万 | 走全额净值 ✓ |
| `house=无 按揭`（带空格）| 56-75.5 万 | **走全额净值**（修复后）✓ |
| `house=有 按揭`（带空格）| 37.5-50.5 万 | 走 net_ratio 折扣 ✓ |

差异约 19-25 万（= 150万 × (1-0.65) × 0.45 × 0.85-1.15 = 22.9-31万），与公式吻合。

修复前 3 种都走折扣（== 失败），修复后能正确区分"无按揭"和"有按揭"。

## 部署
- SSOT: `dist/xincetong-ssot-20260914-2117.zip`
- CVM API active，3 文件编译 OK
- 改动文件：xincetong-server/app/utils/money.py + product_engine.py + scorecard_engine.py
