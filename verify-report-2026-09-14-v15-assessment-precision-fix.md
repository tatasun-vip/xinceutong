# v15 评估精度修复 (2026-09-14 21:08)

## 根因
后端 `app/utils/money.py` 的 5 个 value 函数（`income_value` / `housing_fund_value` / `house_value` / `car_value` / `monthly_debt_value`）**没做字符串规范化**。

前端选项值带空格（如 `"1.5 万-3 万"`），dict key 无空格（如 `"1.5万-3万"`）：
- 评分匹配（`scorecard_engine._norm` line 313）有去空格 → **score 正常**
- 额度计算（`money.py` dict 查表）无去空格 → 查不到 → 返 0 → **limit_min=0, limit_max=0**

表现：用户看到的报告"分数有，额度是 0"——感觉"测试不准"。

## 修复
`xincetong-server/app/utils/money.py`：加 `_norm()` 函数（去空格、全角转半角、转小写），5 个 value 函数全部 `_norm(label)` 后再查表。

## 回归测试
12/12 PASS：
- `"1.5 万-3 万"` / `"1.5万-3万"` / `"5 万以上"` / `"5000以下"` → 收入正确
- `"高 基 数"` / `"无按揭"` / `"10-30万"` → 公积金/房产/车产正确
- `"30%以下"` / `"3000-5000"` → 信用率/月还款正确
- `None` / `""` / `"xxx不存在"` → 0 防御 OK

## e2e 验证 (CVM /api/assessment/submit)
| 字段 | #28 (修复前) | #33 (修复后) |
|------|-------------|-------------|
| 综合 score / level | 56 / B | 60 / B |
| 综合 limit_min/max | 0 / 0 | 370,000 / 500,000 |
| quality_unit limit | 0 / 0 | 740,000 / 1,000,000 (A) |
| housing_fund limit | 0 / 0 | 885,000 / 1,200,000 (B) |
| salary limit | 0 / 0 | (同 housing_fund 量级) |
| house_owner limit | 0 / 0 | (按房产计算) |
| tax / invoice | (业务类型过滤) | (按需计算) |

## 部署
- SSOT 新包：`dist/xincetong-ssot-20260914-2108.zip`
- CVM API 状态：active，23 paths alive
- 改动文件：`xincetong-server/app/utils/money.py`（仅 1 文件）
