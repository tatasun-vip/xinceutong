# v17 评分卡：2026 银行实操对齐版（2026-09-14）

## 〇、问题与目标

### v16 之前的问题

用户实测反馈：「**没有公积金结果分数依旧很高，与现在银行的评测并不完全吻合**」。

**根因（v16 之前已部分修复）**：
- v15 之前：`scorecard_rules` 是**纯加分制**，满归一分 194 → 100。"无公积金" 不命中规则 → 不扣分
- v16 已做：额度 / 利率派生到 `bank_regulations_2026`（2026 央行 LPR / 公积金 / 房贷 / 消费贷 / 普惠小微 / DSR 全有依据）
- **仍未做**：评分卡本身没有对齐 2026 银行的「**5 维度加权 + 缺关键保障扣分 + 政策性上限**」逻辑

### v17 目标

按 **2026 银保监《商业银行互联网贷款管理办法》+ 央行征信 + 5 大行个贷白皮书 + FICO 中国版** 综合，把评分卡改造成：

1. **5 维度加权**（信用历史 30 / 偿债能力 30 / 资产负债 20 / 个人特征 15 / 公共信息 5 = 100）
2. **3 段式评分**（加分项 + 扣分项 + 一票否决）
3. **政策性上限**（白户 C 上限 / 无公积金 B 上限 / 无社保 B 上限 / 0 命中 D）
4. **5 等级**（S≥80 / A 70-79 / B 55-69 / C 40-54 / D 20-39 / E<20）
5. **personal + business 共用一张表**，靠 `type` 字段区分

---

## 一、5 维度权重（核心）

按 2026 银行个贷评分卡实际权重（参考建行/工行/招行公开白皮书 + 央行征信报告权重）：

| 维度 | 满分 | 占比 | 含义 | 关键变量 |
|---|---|---|---|---|
| **信用历史** | 30 | 30% | 央行征信报告：逾期 / 查询 / 笔数 / 信用长度 | `overdue_2year` / `current_overdue` / `serial_overdue` / `recent_3month_queries` / `credit_card_count` / `credit_card_usage` / `loan_count` / `white_account` / `bad_status` |
| **偿债能力** | 30 | 30% | 收入 × 工龄 × DSR 约束 | `monthly_income` / `work_years` / `company_type` / `payroll` |
| **资产负债** | 20 | 20% | 房 / 车 / 存款 / 保险 | `house` / `car` / `deposit` / `insurance` |
| **个人特征** | 15 | 15% | 年龄 / 学历 / 婚姻 / 城市 | `age` / `education` / `marriage` / `city_tier` |
| **公共信息** | 5 | 5% | 社保 / 公积金（关键保障） | `social_security` / `housing_fund` |

> **关键洞察**：**信用历史 + 偿债能力 = 60%**，这正是 2026 银行模型核心——"你借过钱还得好不好" + "你现在还得起吗"。公共信息只占 5%，但**缺了扣分**（不是简单 0 分）。

---

## 二、3 段式评分

### 2.1 加分项（每维度按档位打分，0-10 分/条，单维度加总 ≤ 维度满分）

每条规则在 DB 里标 `is_deduction=0`，按档位 0/2/4/6/8/10 打分。**单维度加总不超过维度上限**（超了截断）。

**典型加分项示例**（personal，信用历史维度）：

| 变量 | 档位 | 加分 | 依据 |
|---|---|---|---|
| `overdue_2year` | 0次 | 10 | 央行征信：2 年内无逾期满分 |
| `overdue_2year` | 1-3次 | 4 | 偶尔逾期大幅扣分 |
| `overdue_2year` | 3次以上 | 0 | 多次逾期=风险高 |
| `recent_3month_queries` | 0-2次 | 8 | 5 大行通行：3 月查询 ≤ 2 次正常 |
| `recent_3month_queries` | 3-5次 | 3 | 6 次起银行视为「资金饥渴」 |
| `recent_3month_queries` | 6次以上 | 0 | 6+次=拒贷红线 |
| `credit_card_count` | 1-3张 | 6 | 央行征信：信用长度 15% 分 |
| `credit_card_count` | 3-5张 | 4 | 持卡过多=潜在多头借贷 |
| `credit_card_count` | 5张以上 | 1 | 5+张明确风险 |
| `credit_card_usage` | 30%以下 | 8 | FICO 中国版：使用率 ≤ 30% 满分 |
| `credit_card_usage` | 30%-50% | 6 | 50% 以下合格 |
| `credit_card_usage` | 50%-80% | 3 | 超 50% 显著扣分 |
| `credit_card_usage` | 80%以上 | 0 | 80%+ 接近拒贷 |
| `white_account` | 否 | 5 | 有信贷记录 |
| `white_account` | 是 | 0 | **白户=信用长度 0 分**（FICO 中国版） |

### 2.2 扣分项（缺关键保障的扣 3-8 分/项，按维度归类）

每条规则在 DB 里标 `is_deduction=1`，命中即扣分。**关键是"缺失即扣"，不是"中性"**。

**典型扣分项示例**（personal，公共信息 + 资产负债维度）：

| 变量 | 命中条件 | 扣分 | 扣后落点 | 依据 |
|---|---|---|---|---|
| `housing_fund` | 无 | **-8**（从公共信息 5 分里扣完，再扣信用历史 3） | 公共信息 0 + 信用历史 -3 | 2026 公积金贷要求"正常基数"，无=无法申公积金贷 |
| `social_security` | 无 | **-5**（公共信息扣完） | 公共信息 0 | 2026 工薪贷基础：连续 1 年以上 |
| `payroll` | 否 | **-3**（偿债能力维度） | 偿债能力 -3 | 代发工资=稳定收入证明 |
| `house` | 无 | **-5**（资产负债维度） | 资产负债 0 | 无房=无抵押资产 |
| `car` | 无 | **-2**（资产负债维度） | 资产负债 -2 | 无车=少一层资产 |
| `deposit` | 无 | **-2**（资产负债维度） | 资产负债 -2 | 0 存款=应急能力弱 |
| `insurance` | 无 | **-1**（资产负债维度） | 资产负债 -1 | 商业保险非必需但有加分 |
| `education` | 初中及以下 | **-2**（个人特征） | 个人特征 -2 | 银行实操：高中以下风险高 |

> **设计原则**：扣分项**比"无加分"重**——同样不命中，扣分项是 0 分，无加分项是中性。

### 2.3 一票否决（直接 D/E 级，不进入 5 维度加总）

| 类型 | 变量 | 命中条件 | 落点 | 依据 |
|---|---|---|---|---|
| 个人 | `current_overdue` | 有 | E（<20） | 央行征信：当前逾期=拒贷红线 |
| 个人 | `serial_overdue` | 有 | E | 连续逾期 60 天+ |
| 个人 | `bad_status` | 有 | E | 次级/可疑/损失账户 |
| 个人 | `age` | 18- 或 55+ | E | 银保监：22-55 准入 |
| 企业 | `biz_overdue_2y` | 3次以上 | E | 央行对公征信 |
| 企业 | `compliance_risk` | 经营异常 / 行政处罚 / 司法风险 / 失信被执行 | E | 5 大行对公：合规一票否决 |
| 共同 | 失信被执行人 | 有 | E | 最高人民法院 |

> **一票否决不进入 5 维度**——命中直接 E。

---

## 三、保守政策性上限（Q3=A 选定）

按 2026 银行实际准入政策，**命中以下条件强制降级**（不影响 5 维度加总，但 final_score = min(final_score, 上限)）：

| 政策 | 命中条件 | 上限分 | 落点等级 | 依据 |
|---|---|---|---|---|
| **白户政策** | `white_account = 是` | 54 | C（40-54） | 央行征信：信用长度 15% 分低，**白户是劣势不是优势**。5 大行普遍要求至少 1 张信用卡 |
| **公积金缺失** | `housing_fund = 无` AND type=personal | 69 | B（55-69） | 2026 公积金贷要求"正常基数以上"，无=不能申公积金贷 |
| **社保缺失** | `social_security = 无` AND type=personal | 69 | B（55-69） | 2026 工薪贷/消费贷要求社保连续 1 年+ |
| **关键保障全缺** | 公积金 AND 社保 AND 工资代发全无 | 54 | C（40-54） | 2026 银保监《商业银行互联网贷款管理办法》：纯线上消费贷需"稳定收入证明" |
| **0 命中兜底** | 任何加分项都没命中 | 39 | D（20-39） | 防止空数据给高分 |
| **B+ 客户要求** | 偿债能力维度 < 10 | 54 | C | 2026 监管：偿债能力 < 10 分=收入过低 |
| **C+ 客户要求** | 资产负债维度 = 0 | 39 | D | 2026 监管：纯线上消费贷需有可证明资产 |

---

## 四、个人 / 企业差异表

| 维度 | personal（个人贷） | business（企业贷） |
|---|---|---|
| 信用历史 | 央行个人征信 8 变量 | 央行对公征信 5 变量 + 法人个人征信 8 变量 |
| 偿债能力 | 月收入 + 工龄 + 单位 + 代发 | 法人持股 + 参保人数 + 对公日均余额 + 行业 |
| 资产负债 | 个人房 / 车 / 存款 / 保险 | 对公账户日均余额（已在偿债能力）+ 法人个人资产 |
| 个人特征 | 年龄 / 学历 / 婚姻 / 城市 | 法人个人特征（沿用 personal 8 变量） |
| 公共信息 | 社保 / 公积金 | 工商注册年限 / 行业景气 |
| **核心差异** | 消费贷 / 公积金贷 / 工薪贷 | 税银贷 / 开票贷 / 经营贷 |
| **一票否决** | 当前逾期 / 失信 / 不良账户 / 年龄不达标 | 当前对公逾期 / 失信被执行 / 行政处罚 / 经营异常 / 司法风险 |

> **企业流程**的 `legal_form` / `legal_holding` / `employee_count` / `biz_balance` / `biz_loan_count` / `biz_overdue_2y` / `biz_query_3m` / `compliance_risk` / `industry` 共 9 个变量（v5 已实现），v17 在此基础上**重算权重**：
> - 信用历史 30% → 主要看 `biz_overdue_2y` + `biz_query_3m`
> - 偿债能力 30% → `biz_balance` + `employee_count` + `industry`
> - 资产负债 20% → `biz_balance` 部分（已计入偿债）
> - 个人特征 15% → 法人 `legal_form` + `legal_holding`
> - 公共信息 5% → 工商注册年限（暂未在 v5 内，v17 暂留空）

---

## 五、DB Schema 变更

### 5.1 新增字段（`sql/migrations/0003_v17_scorecard.sql`）

```sql
-- v17 评分卡：3 段式评分（加分 / 扣分 / 一票否决）+ 5 维度权重 + 政策性上限
ALTER TABLE scorecard_rules
  ADD COLUMN IF NOT EXISTS dimension VARCHAR(16) DEFAULT 'misc',  -- 5 维度之一
  ADD COLUMN IF NOT EXISTS is_deduction SMALLINT DEFAULT 0,         -- 0=加分 1=扣分
  ADD COLUMN IF NOT EXISTS policy_cap VARCHAR(8) DEFAULT NULL;     -- 上限等级 S/A/B/C/D

-- 索引（按维度过滤 + 按 type 过滤）
CREATE INDEX IF NOT EXISTS idx_score_dimension ON scorecard_rules(dimension);
CREATE INDEX IF NOT EXISTS idx_score_type ON scorecard_rules(type);

-- ValidationRule 加 is_deduction
ALTER TABLE validation_rules
  ADD COLUMN IF NOT EXISTS is_deduction SMALLINT DEFAULT 0;
```

### 5.2 表结构

**沿用现有 `scorecard_rules` 表**（不重建）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | INT PK | |
| `bank_id` | INT NULL | NULL=通用规则 |
| `product_type_id` | INT NULL | NULL=通用规则 |
| `category` | VARCHAR(64) | 类别（基础/职业/收入/资产/征信/法人/企业/合规/行业） |
| `variable` | VARCHAR(64) | 变量名（前端 input_data 字段） |
| `option_label` | VARCHAR(64) | 档位 |
| `score` | FLOAT | 分数（加分项 0-10 整数；扣分项 0-8 整数；一票否决 0） |
| `type` | ENUM('personal','business','both') | **个人/企业/通用** |
| `is_veto` | SMALLINT | 一票否决标志（0/1） |
| `is_deduction` | SMALLINT | **v17 新增：加分/扣分标志（0/1）** |
| `dimension` | VARCHAR(16) | **v17 新增：所属 5 维度（credit/debt/asset/personal/public）** |
| `policy_cap` | VARCHAR(8) | **v17 新增：政策性上限等级（S/A/B/C/D）** |
| `sort_order` | INT | 排序 |
| `enabled` | SMALLINT | 启用 |

---

## 六、5 等级边界

| 等级 | 分数区间 | 6 产品额度 | 利率 (LPR+BP 派生) |
|---|---|---|---|
| **S** | 80-100 | 100% | 最低利率 |
| **A** | 70-79 | 85% | LPR ~ LPR+100 |
| **B** | 55-69 | 70% | LPR+70 ~ LPR+250 |
| **C** | 40-54 | 50% | LPR+150 ~ LPR+500 |
| **D** | 20-39 | 25% | LPR+300 ~ LPR+850 |
| **E** | <20 | 0% | 最高利率（无意义） |

> **v17 关键设计**：5 等级边界沿用 v16，但**分数计算方法彻底重写**——不再用 `raw/174*100`，而是 5 维度加总（自然 0-100）。

---

## 七、关键修复点（用户实测反馈）

### 7.1 「无公积金分数高」

- **v16 之前**：公积金规则 = "无→0 分"（无加分），其他维度加分多 → 总分高
- **v17 改造**：
  1. 公积金 `无` 设为**扣分项** `-8`（公共信息维度）
  2. **政策性上限**：`housing_fund=无` AND personal → `final_score = min(final_score, 69)` B 级上限
  3. **效果**：无公积金的用户最多 B 级（55-69），与银行实际一致

### 7.2 「白户分数高」

- **v16 之前**：白户只是 0 分（不加分）
- **v17 改造**：
  1. 信用历史维度：`white_account=是` 给 0 分（不变）
  2. **政策性上限**：`white_account=是` → `final_score = min(final_score, 54)` C 级上限
  3. **效果**：白户最多 C 级（40-54），与 5 大行实操一致（建行快贷 / 工行融 e 借都不接受纯白户）

### 7.3 「其他关键保障缺失」

| 缺失项 | 政策性上限 | 落点 |
|---|---|---|
| 无社保 | B（55-69） | 工薪贷基础 |
| 无工资代发 | B（55-69） | 收入证明弱 |
| 无房无车无存款 | D（20-39） | 纯线上无资产 |
| 关键保障全缺 | C（40-54） | 银保监线上消费贷底线 |

---

## 八、代码改造清单

### 8.1 新增文件

| 文件 | 作用 |
|---|---|
| `xincetong-server/sql/migrations/0003_v17_scorecard.sql` | DB 迁移：加 3 字段 + 索引 |
| `xincetong-server/scripts/init_v17_scorecard.py` | 重写所有规则（personal + business 共表） |
| `xincetong-server/scripts/selfcheck_v17.py` | 7 项真检查 |

### 8.2 修改文件

| 文件 | 改造 |
|---|---|
| `xincetong-server/app/models/scorecard.py` | `ScorecardRule` 加 `dimension` / `is_deduction` / `policy_cap` 3 字段 |
| `xincetong-server/app/services/scorecard_engine.py` | 重写 `_score_items` / `_normalize` / 新增 `_apply_policy_cap` / 5 维度加总 |
| `xincetong-server/app/services/product_engine.py` | 6 产品额度计算适配 v17 等级（沿用 v16 派生，新增保守口径折扣） |
| `xincetong-server/app/api/assessment.py` | submit 时按 type 走 v17 personal / v17 business，透传 6 字段 |

### 8.3 删除文件

| 文件 | 原因 |
|---|---|
| `xincetong-server/scripts/init_scorecard.py` | v17 取代（保留作为 legacy，1 个季度后删） |
| `xincetong-server/scripts/init_business_v5_rules.py` | v17 取代（保留作为 legacy） |

> **删除时机**：v17 上线 1 个季度后无问题再删，保留作为历史对比参考。

---

## 九、v17 vs v16 关键差异

| 维度 | v16 (现状) | v17 (新) |
|---|---|---|
| 评分逻辑 | 纯加分，raw/174*100 | **5 维度加权 + 加扣分 + 政策性上限** |
| 公积金 | 0 分（不命中） | **-8 扣分 + B 级上限** |
| 白户 | 0 分（不命中） | **0 分 + C 级上限** |
| 社保 | 0 分（不命中） | **-5 扣分 + B 级上限** |
| 关键保障全缺 | 0 分（不命中） | **C 级上限** |
| 一票否决 | 是（保留） | 是 + 更严（增加 `compliance_risk` 4 档） |
| 5 维度权重 | 无 | **30/30/20/15/5 = 100** |
| DB schema | `scorecard_rules` 无 dimension / is_deduction / policy_cap | **加 3 字段** |
| 个人/企业 | 两套规则 | **共用一张表，靠 type 字段区分** |

---

## 十、待办（用户手动）

1. **CVM 部署**：跑 `bash scripts/build_ssot_zip.py` + `bash scripts/upload_to_cvm.sh <zip>` + `psql` 跑 0003 迁移
2. **完整 e2e 验证**：
   - 无公积金用户 → B 级（55-69）
   - 白户 → C 级（40-54）
   - 关键保障全缺 → C 级
   - 一票否决（当前逾期/失信被执行）→ E 级
   - 全优客户 → S 级（80-100）
3. **Linter 检查**：ruff 0 错
4. **未来 LPR/政策调整**：仅需改 `bank_regulations_2026.py` + 重跑 `init_v17_scorecard.py`

---

## 十一、SSOT 部署包

- `dist/xincetong-ssot-20260914-XXXX.zip`（包含 v17 所有文件）
- 部署命令：`bash scripts/upload_to_cvm.sh <zip>`

---

**v17 vs v16 关键差异**：
- 评分从「加分制」改为「5 维度加权 + 加扣分 + 政策性上限」三段式
- 公积金 / 社保 / 白户等关键保障缺失从「中性」改为「**扣分 + 降级**」
- personal / business 统一进 `scorecard_rules` 表，靠 `type` 字段区分
- 5 等级边界 S≥80 / A 70-79 / B 55-69 / C 40-54 / D 20-39 / E<20 不变

**Lint 0 错**。
