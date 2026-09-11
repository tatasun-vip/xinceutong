# 信测通评估报告模型重整报告

> 日期：2026-09-11 · 范围：P0+P1（15 处修复 + 1 个真实 bug 附加）· 状态：已落地

## 一、问题诊断

原模型在 7 处"参数 × 银行实际"严重偏离，导致报告"过于夸张、不像银行"：

| 问题 | 旧值 | 实际值 | 偏离 |
|---|---|---|---|
| 评分归一化分母 | 200（注释瞎写） | 174 | 偏高 15% |
| 优质单位贷倍数 | S=36x | 4-8x | **4-5x** |
| 公积金贷倍数 | S=300x | 100-200x | 2-3x |
| 工薪贷倍数 | S=24x | 2-5x | **5-8x** |
| 纳税贷倍数 | S=15x | 5-10x | 1.5-2x |
| 开票贷比例 | S=15% | 5-10% | 1.5x |
| PD 斜率 | k=0.08 | 银行实操 ~0.12 | 太缓 |
| 额度上下限 | ±30% | ±10-15% | 太宽 |
| 房产净值 | 有按揭=0 | 评估价×净值率 | 漏算净值 |
| 综合分折扣 | B=0.7 | B=0.5 | 太宽松 |
| 自审上限 | 16.8-31.2x年收 | 6-12x | 拦不住虚高 |
| 文案背书 | "50+ 金融分析师 + 20,000 案例" | 无 | 虚假宣传 |
| 前后端 label | 前端"3 万-5 万" ≠ 后端"3万-5万" | — | 解析失败 |

## 二、修复对比（关键数据）

### 理想用户（30 岁公务员/4 万月收/高公积金/有按揭房 150 万/10-30 万车/无负债/无逾期）

| 维度 | 修复前 | 修复后 | 银行实际 |
|---|---|---|---|
| 评分 | 76 (A 中高) | **88 (S 高)** | S 客 80+ |
| 综合额度 | 9.8-18.2 万 | **57-78 万** | DSR 反算 60-80 万 |
| 优质单位贷 | 1108-2059 万 | **326-441 万** | 建行快贷 8x年收 = 384 万 |
| 公积金贷 | 705-1310 万 | **714-966 万** | 招行月缴 200x = 840 万上限 |
| 工薪贷 | 739-1372 万 | **204-276 万** | 平安新一贷 5x = 240 万 |

### 较差用户（55 岁/初中/无房无车/5 笔贷款/3 次逾期/5000 负债）

| 维度 | 修复前 | 修复后 | 银行实际 |
|---|---|---|---|
| 评分 | 2 (E) | **2 (E)** | E 拒批 ✓ |
| 所有产品 | 0（拒批） | 0（拒批） | ✓ |
| 通过率 | 极低 | 极低 | ✓ |

## 三、修改清单

| # | 文件 | 改动 |
|---|---|---|
| 1 | `app/services/scorecard_engine.py` | `INCOME_MULTIPLIER` 24→6、`HOUSING_FUND_MULTIPLIER` 400→200 |
| 2 | `app/services/scorecard_engine.py` | `_normalize` `/2.0` → `/1.74` |
| 3 | `app/services/scorecard_engine.py` | `_calc_pd_and_pass` k=0.08 → 0.12 |
| 4 | `app/services/scorecard_engine.py` | `_calc_limits` 上下限 ±30% → ±15% |
| 5 | `app/services/scorecard_engine.py` | 资产法加入净值率 0.85/0.75/0.65/0.55/0.4 |
| 6 | `app/services/product_engine.py` | 5 个产品公式倍数全部下调 |
| 7 | `app/services/product_engine.py` | `_calc_pd_and_pass` k 同步 0.08 → 0.12 |
| 8 | `app/services/product_engine.py` | 综合分折扣 B 0.7→0.5, C 0.5→0.3, D 0.3→0.15 |
| 9 | `app/services/report_auditor.py` | `LEVEL_LIMIT_FACTOR` 16.8-31.2 → 6-12 |
| 10 | `scripts/init_site_config.py` | `case_count` "20000" → "0"，`expert_count` "50" → "0" |
| 11 | `scripts/init_site_config.py` | `brand_one_liner` / `disclaimer_full_report` 删虚假背书 |
| 12 | `app/api/assessment.py` | API 报告 disclaimer 同步改文案 |
| 13 | `xinceutong-miniapp/src/pages/assess/loading.vue` | 提交前 normalize label 中文/英文空格 |
| 14 | `xinceutong-miniapp/src/pages/index/index.vue` | 专家数 0 时整行隐藏 |
| 15 | `xinceutong-miniapp/src/components/data-strip/DataStrip.vue` | 数字 0 时整项隐藏 |
| 16 | `xinceutong-miniapp/src/store/site.ts` | `caseCount`/`expertCount` 默认值改 0 |

## 四、关键修复细节

### 1. 评分归一化（`/1.74` vs `/2.0`）
- 实际命中满分 ~174 分（基础 22 + 职业 52 + 收入 30 + 资产 40 + 征信 50）
- 旧 `/2.0` 让全优用户只到 87 分；新 `/1.74` 让全优用户到 98 分

### 2. PD 斜率（k=0.12 vs k=0.08）
- 旧：score=80 → PD=0.146（"中高"）— S 客户只能"中高"，与等级矛盾
- 新：score=80 → PD=0.027（"高"）— S 客户得"高"，与等级匹配
- 各档位：80→高、70→中高、60→中、50→低、40→极低

### 3. 房产净值算法
- 旧：有按揭 → 资产 = 0 + 车（漏算 100+ 万房产）
- 新：净值 = 评估价 × 净值率（S 85% / A 75% / B 65% / C 55% / D 40%）
- 弱客群按 D=40% 净值率（按揭比例往往更高）

### 4. 6 大产品公式全部按银行实际下调
- 优质单位贷：36x → 8x（建行快贷参考）
- 公积金贷：300x → 200x（招行公积金优享贷）
- 工薪贷：24x → 5x（平安新一贷）
- 纳税贷：15x → 10x（建行税易贷）
- 开票贷：15% → 10%（网商银行开票贷）

### 5. Disclaimer 文案规范
- 删："由 50+ 位资深金融分析师参与校准"
- 删："累计 20,000+ 真实案例回测验证"
- 改："模型逻辑参考银行信用贷审批框架（A 卡 / B 卡 / 反欺诈层），额度、利率、综合通过率按真实业务区间测算，但本平台不查征信、不接入任何银行系统、不收集您的真实数据"

## 五、附加发现的真实 Bug

**前后端 label 不一致**（导致 income 永远是 0）：
- 前端 `assess-options.ts` 用 "3 万-5 万"（带空格）
- 后端 `INCOME_MIDPOINT` / `SCORECARD_SEED` / `money.py` 用 "3万-5万"（无空格）
- 影响：所有收入相关计算（评分命中 + 收入法 + DSR 法）解析失败
- 修复：前端 `loading.vue` 提交前 normalize（去中文/英文空格）

## 六、未做（按 P2 留作后续）

1. 6 大产品专属规则补全（5/6）
2. DSR 计算加"本次新贷款月供"约束
3. 历史数据修正（数据库已存记录保持原值）
4. `_build_suggestions` placeholder 修
5. 前端"推荐产品"卡片按等级动态展示
6. `pd_calibration` 接入历史数据做实际校准
7. 报告"未通过项"按维度细分（如资产法原因 / 收入法原因）

## 七、测试脚本

`xinceutong-server/tests/test_before_after.py` 保留：跑两个测试用户（理想/较差），对比修复前后所有关键数据。
跑法：`cd xinceutong-server && source .venv/bin/activate && python tests/test_before_after.py`
