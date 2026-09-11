# 信测通评估报告模型重整报告

> 日期：2026-09-11 · 范围：P0+P1+P2（19 处修复 + 1 个真实 bug 附加）· 状态：已落地

## 一、问题诊断（3 轮修复）

### P0/P1 第一轮：模型参数过于夸张
- 评分归一化分母、6 大产品倍数、PD 斜率、额度上下限、综合分折扣、房产净值、自审上限、文案背书 → 全部严重偏离银行实操

### P2 第二轮：监管合规硬上限缺失
- 用户关键反馈："信用贷款是有上限的，线上高，线下最高，你不能因为用户填的数值好，给出报告是不切实际的额度"
- 6 大产品 × 线上/线下 缺硬上限 → 高净值用户被算出 489-662 万（**严重超标**，建行快贷线下最高 100 万）

## 二、修复对比（高净值用户场景，最关键 P2）

> 用户：22-30 岁 / 公务员 / 5万+ 月收 / 高基数公积金 / 500 万无按揭房 / 50 万车 / 全好征信

| 产品 | 修复前 | P0+P1 后 | P2 后（最终） | 银行实际 |
|---|---|---|---|---|
| 优质单位贷 | 1814-3370 万 | 489-662 万 | **73.9-100 万** | 线下 ≤ 100 万 ✓ |
| 公积金贷 | 882-1638 万 | 714-966 万 | **88.7-120 万** | 线下 ≤ 120 万 ✓ |
| 工薪贷 | 1209-2246 万 | 306-414 万 | **73.9-100 万** | 线下 ≤ 100 万 ✓ |
| 纳税贷 | 425-575 万 | 425-575 万 | **73.9-100 万** | 线下 ≤ 100 万 ✓ |
| 开票贷 | 85-115 万 | 85-115 万 | **85-115 万**（不 cap）| 线下 ≤ 500 万 ✓ |
| 综合额度 | 22-41 万 | 73.9-100 万 | **73.9-100 万** | 线下 ≤ 100 万 ✓ |

## 三、关键修复细节

### P2 渠道合规硬上限
**银保监 2020/7《关于加强商业银行互联网贷款业务管理》**：
- 互联网消费贷（线上）：单户 ≤ 30 万
- 商业银行自营消费贷（线下）：≤ 100 万
- 公积金贷（线下）：单职工 60 万 / 双职工 120 万
- 经营贷（线下）：≤ 500-1000 万（含担保）
- 房抵贷（二抵）：≤ 1000 万

**CHANNEL_CAPS 字典**（product_engine.py 顶部）：
```python
CHANNEL_CAPS = {
    "quality_unit":  {"online": 30_0000, "offline": 100_0000},  # 优质单位贷
    "housing_fund":  {"online": 30_0000, "offline": 120_0000},  # 公积金贷
    "salary":        {"online": 30_0000, "offline": 100_0000},  # 工薪贷
    "house_owner":   {"online": 50_0000, "offline": 1000_0000}, # 房抵贷
    "tax":           {"online": 30_0000, "offline": 100_0000},  # 纳税贷
    "invoice":       {"online": 100_0000, "offline": 500_0000}, # 开票贷
}
```

**apply_channel_cap**（product_engine.py）：
- 当 `limit_max > offline_cap` → 整区间 cap 到上限
- 返回 `was_capped` 标志 + `limit_reason` 文案（"测算值 X 万超过「线下最高 Y 万」监管上限"）
- ProductResult 扩 4 字段：`channel_online_max` / `channel_offline_max` / `limit_capped` / `limit_reason`

### P0/P1 关键修复（快速回顾）
- 评分归一化：/2.0 → ×100/174
- PD 斜率：k=0.08 → 0.12
- 收入倍数：24/18/12/8/2 → 6/5/4/2/1
- 优质单位贷：36x → 8x
- 公积金贷：300x → 200x
- 工薪贷：24x → 5x
- 纳税贷：15x → 10x
- 开票贷：15% → 10%
- 上下限：±30% → ±15%
- 综合分折扣：B 0.7→0.5, C 0.5→0.3, D 0.3→0.15
- 房产净值：等级化净值率 0.85/0.75/0.65/0.55/0.4
- 自审 LEVEL_LIMIT_FACTOR：16.8-31.2 → 6-12

## 四、修改清单

| # | 文件 | 改动 |
|---|---|---|
| 1 | `app/services/scorecard_engine.py` | INCOME_MULTIPLIER 24→6, HOUSING_FUND_MULTIPLIER 400→200 |
| 2 | `app/services/scorecard_engine.py` | `_normalize` /2.0 → ×100/174 |
| 3 | `app/services/scorecard_engine.py` | `_calc_pd_and_pass` k 0.08→0.12 |
| 4 | `app/services/scorecard_engine.py` | `_calc_limits` ±30% → ±15% |
| 5 | `app/services/scorecard_engine.py` | 资产法加净值率 |
| 6 | `app/services/scorecard_engine.py` | `_calc_limits` 加线下 100 万 cap |
| 7 | `app/services/product_engine.py` | **新增 CHANNEL_CAPS 字典** |
| 8 | `app/services/product_engine.py` | **新增 apply_channel_cap 函数** |
| 9 | `app/services/product_engine.py` | ProductResult 扩 4 字段 |
| 10 | `app/services/product_engine.py` | to_dict 加 cap 字段 |
| 11 | `app/services/product_engine.py` | 计算返回前应用 cap + logger |
| 12 | `app/services/product_engine.py` | 5 个产品公式倍数全部下调 |
| 13 | `app/services/product_engine.py` | `_calc_pd_and_pass` k 同步 |
| 14 | `app/services/product_engine.py` | 综合分折扣 B 0.7→0.5 等 |
| 15 | `app/services/report_auditor.py` | LEVEL_LIMIT_FACTOR 16.8-31.2 → 6-12 |
| 16 | `scripts/init_site_config.py` | case_count "20000"→"0", expert_count "50"→"0" |
| 17 | `scripts/init_site_config.py` | brand_one_liner 删虚假背书 |
| 18 | `scripts/init_site_config.py` | **disclaimer 加渠道合规说明** |
| 19 | `app/api/assessment.py` | API disclaimer 同步 |
| 20 | `xinceutong-miniapp/src/pages/assess/loading.vue` | label 空格 normalize |
| 21 | `xinceutong-miniapp/src/pages/index/index.vue` | expertCount 0 时隐藏 |
| 22 | `xinceutong-miniapp/src/components/data-strip/DataStrip.vue` | 数字 0 时整项隐藏 |
| 23 | `xinceutong-miniapp/src/store/site.ts` | caseCount/expertCount 默认 0 |

## 五、附加发现的真实 Bug

**前后端 label 不一致**：
- 前端 `assess-options.ts` 用 "3 万-5 万"（带空格）
- 后端 `INCOME_MIDPOINT` / `SCORECARD_SEED` / `money.py` 用 "3万-5万"（无空格）
- 影响：所有收入相关计算（评分命中 + 收入法 + DSR 法）解析失败
- 修复：前端 `loading.vue` 提交前 normalize（去中文/英文空格）

## 六、未做（按 P3 留作后续）

1. 6 大产品专属规则补全（5/6）
2. DSR 计算加"本次新贷款月供"约束
3. 历史数据修正（数据库已存记录保持原值）
4. `_build_suggestions` placeholder 修
5. 前端"推荐产品"卡片按等级动态展示
6. `pd_calibration` 接入历史数据做实际校准
7. 报告"未通过项"按维度细分（如资产法原因 / 收入法原因）
8. 前端展示"线上 X 万 / 线下 Y 万"双额度卡片

## 七、测试脚本

`xinceutong-server/tests/test_before_after.py` 保留：3 个测试用户（理想/较差/高净值），对比 P0+P1+P2 修复后所有关键数据 + 渠道 cap 专项验证。
跑法：`cd xinceutong-server && source .venv/bin/activate && python tests/test_before_after.py`
