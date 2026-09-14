# 信测通 v23 话术规范化（narrative SSOT）验证报告

**部署时间**：2026-09-15 01:12
**SSOT 包**：`xincetong-ssot-20260915-0112.zip`
**根因**：v9 之后 evidence chain 落地了，但话术/分析文字描述散落在 5+ 个 hardcoded 字符串拼接点（`_build_one_sentence` / `_build_free_summary_from_db` / `_build_suggestions` / `_build_tags` / `_build_evidence`），无法保证不出现"评级 E 但说高通过率 / 信用卡使用率高又说使用率低"之类的自相矛盾。

---

## 一、SSOT 设计

新文件 `xincetong-server/app/services/narrative.py`（714 行）定义 5 大自洽保证：

| 维度 | 关键常量 | 作用 |
|---|---|---|
| 1. 等级 SSOT | `LEVEL_NARRATIVE`（6 等级 × 5 字段） | S/A/B/C/D/E 各有 title/description/verdict/recommendation/cta，措辞统一 |
| 2. 通过概率 SSOT | `LEVEL_PASS_PROB` | S 通过率 80-95%、E "央行一票否决"，避免数字与 level 矛盾 |
| 3. 风险-优势互斥 | `RISK_ADVANTAGE_MUTEX`（16 条规则） | "高负债率" + "负债率合理" 不能共存；命中"信用卡使用率高"必须撤掉"使用率低" |
| 4. 模板库 | `ISSUE_TEMPLATES`（14 套）/ `SUGGESTION_TEMPLATES`（16 套） | 5 维度（what/why/impact/when/result）标准化模板，避免硬编码 |
| 5. 一致性自检 | `consistency_check` | 上线前自动扫 5 大矛盾（level口径/veto互斥/数字逻辑/产品推荐/改善建议） |

银行话术口径（SSOT verdict 示例）：
- S："您的资质已属卓越，可直接申请"
- E："建议暂缓申请，先解决风险项"
- D："目前较弱，建议先优化再申请"
- C："您的资质一般，建议先优化再申请"

---

## 二、集成点（5 处后端 + 2 处前端）

| # | 文件 | 改动 |
|---|---|---|
| 1 | `app/services/narrative.py` | 新建（714 行 SSOT） |
| 2 | `app/api/assessment.py` | `_build_one_sentence` 改用 `LEVEL_NARRATIVE["verdict"]`；`_build_free_summary_from_db` 注入"根据我行 A 卡模型综合评估"+ SSOT `recommendation`；`_build_suggestions` 加 Phase 0 调 `SUGGESTION_TEMPLATES` |
| 3 | `app/services/scorecard_engine.py` | `_build_tags` 输出走 `apply_mutex()`，自动剔除与风险矛盾的"优势/弱点" |
| 4 | `app/services/product_engine.py` | `_build_evidence` 改 `_compose_product_not_recommend` 派生；新增 `_compose_product_improve_hint` 派生 `improve_hint` 字段；`ProductResult` 加 `improve_hint` 字段 + to_dict 同步；修原 line 247 引用未传入 `product_code` / `input_data` 的 NameError 隐患 |
| 5 | `xincetong-miniapp/src/api/assessment.ts` + `free.vue` + `report.vue` | `ProductResult` TS 加 `improve_hint`；新增绿色"如何改善"块（与"不推荐原因"互补） |
| 6 | `xincetong-web/src/api/assessment.ts` + `Result.vue` | 同上 |

---

## 三、端到端测试（6 场景）

测试脚本 `/tmp/test_evidence_ssot.py`，项目 venv `.venv/bin/python` 跑：

| 场景 | score | not_recommend_reason | improve_hint | 一致性 |
|---|---|---|---|---|
| **S**（月入 5 万+、信用卡 30% 以下） | 95 | ✅ 空（不写"不推荐"） | ✅ 空 | 0 问题 |
| **A**（月入 2-5 万） | 82 | ✅ 空 | ✅ 空 | 0 问题 |
| **B**（月入 1-2 万） | 70 | ✅ 空 | ✅ 空 | 0 问题 |
| **C**（月入 5千-1万 + 信用卡 80%） | 55 | ✅ "综合分 55 分（C 级），可优化项：…"。含 SSOT recommendation | ✅ "如将「信用卡使用率 80%以上」调整为「信用卡使用率 30%以下」，预计可提升 11.0 分" | 0 问题 |
| **D**（信用卡 80% + 逾期 3-6 次） | 38 | ✅ "综合分 38 分（D 级），主要扣分项：…"。含 SSOT | ✅ "如将「近 2 年逾期 3-6 次」调整为「无逾期」，预计可提升 14.0 分" | 0 问题 |
| **E**（央行黑名单 + 逾期 6 次+） | 12 | ✅ "命中央行黑名单；近 2 年逾期 6 次以上。建议先到央行打印详版征信报告…" | ✅ "如将「近 2 年逾期 6 次以上」调整为「无逾期」，预计可提升 21.0 分" | 0 问题 |

**关键校验**：
- E 级文案绝不出现"可申请 / 建议申请 / 可优先选择 / 建议优先在"等乐观词 ✅
- D/C/E 必含 LEVEL_NARRATIVE 的"暂缓/优化/建立"等 SSOT 关键词 ✅
- S/A/B not_recommend_reason 必空（已推荐就别说"不推荐"） ✅
- improve_hint 必为口语化"如将 X 调整为 Y，预计可提 N 分"格式 ✅

---

## 四、5 大自洽保证对照

| 矛盾类型 | 旧问题 | v23 SSOT 解决方案 |
|---|---|---|
| ① level 口径 | E 级说"可申请" | `_build_one_sentence` 强制用 `LEVEL_NARRATIVE[level]["verdict"]` |
| ② veto 互斥 | "信用卡使用率高" 优势里又写 "使用率低" | `_build_tags` 输出走 `apply_mutex()`（16 条 MUTEX 规则） |
| ③ 数字逻辑 | 综合分 12 还说"通过率高" | `LEVEL_PASS_PROB` 与 `LEVEL_NARRATIVE` 强绑定 |
| ④ 产品推荐 | 推荐列表里出现已否决产品 | 6 产品 `not_recommend_reason` / `recommendation` 派生自同一份 `LEVEL_NARRATIVE` |
| ⑤ 改善建议 | 必推荐"维持现状" | `SUGGESTION_TEMPLATES` 按"phase × source"双维度给模板，避免画饼 |

---

## 五、SSOT 一致性自检报告

`consistency_check` 自动扫 6 场景：

```
S 级: 报告问题 0 项, 描述口径 ✅
A 级: 报告问题 0 项, 描述口径 ✅
B 级: 报告问题 0 项, 描述口径 ✅
C 级: 报告问题 0 项, 描述口径 ✅
D 级: 报告问题 0 项, 描述口径 ✅
E 级: 报告问题 0 项, 描述口径 ✅
```

**6/6 场景无矛盾，0 自洽问题。**

---

## 六、SSOT 包内容

`xincetong-ssot-20260915-0112.zip` 包含：

| 文件 | 改动类型 |
|---|---|
| `xincetong-server/app/services/narrative.py` | 新增 714 行 |
| `xincetong-server/app/services/product_engine.py` | 改 _build_evidence（+80 行）+ ProductResult.improve_hint + 修 NameError 隐患 |
| `xincetong-server/app/services/scorecard_engine.py` | 改 _build_tags（加 apply_mutex） |
| `xincetong-server/app/api/assessment.py` | 改 _build_one_sentence / _build_free_summary_from_db / _build_suggestions（SSOT 派生） |
| `xincetong-miniapp/src/api/assessment.ts` | ProductResult TS +improve_hint |
| `xincetong-miniapp/src/pages/result/free.vue` | + "如何改善" 块 + 绿色 CSS |
| `xincetong-miniapp/src/pages/result/report.vue` | + "如何改善" 块 + 绿色 CSS |
| `xincetong-web/src/api/assessment.ts` | ProductResult TS +improve_hint |
| `xincetong-web/src/pages/Result.vue` | + "如何改善" 块 + CSS |

---

## 七、部署命令

```bash
# 1. 上传 SSOT 到 CVM
cd /Users/suntata/CodeBuddy/20260907155240
bash scripts/upload_to_cvm.sh dist/xincetong-ssot-20260915-0112.zip

# 2. 重启 API
ssh root@82.156.166.188 "systemctl restart xincetong-api"

# 3. 验证
curl -s https://www.trumpdream.site/api/health
curl -X POST https://www.trumpdream.site/api/assessment/submit \
  -H "Content-Type: application/json" \
  -d '{"type":"personal","input_data":{"monthly_income":"1-2万","housing_fund":"无","credit_overdue":0,"credit_card_usage":"30%-50%","car":"无","house":"无","deposit":"5万以下","monthly_debt":"无"}}' | jq
```

---

## 八、待用户手动验证

1. **HBuilder 真机/模拟器**：测 miniapp 6 大产品卡，新"如何改善"块在 D/C/E 显示
2. **Web 端浏览器**：test.trumpdream.site（如果还在）走完整流程
3. **真用户回归**：邀请 2-3 个真用户走 C/D/E 流程，确认话术"听着像客户经理"
4. **后续 0 回归测试**：
   - 输入 `monthly_income="5万以上"` + 全优数据 → 必须 S/A 级 verdict
   - 输入 `is_blacklist=1` + `credit_overdue=6` → 必须 E 级 + "建议暂缓" + "央行打印详版征信"
   - 输入 `credit_card_usage="80%以上"` + `credit_overdue=3` → D 级 + "如调整为 30% 以下，可提 11 分"

---

## 九、关键设计决策（v23 → v24+ TODO）

1. **数据库层**：是否将 `improve_hint` / `not_recommend_reason` 也存到 `assessments.product_results` JSON 内？目前只在前端展示，后端重算，不持久化（v9 设计）。如要做"3 个月内再次测评时复用历史话术"，需要 ALTER COLUMN。
2. **银行专属话术**：v23 SSOT 用通用 5 大行口径，未来可加 `BANK_NARRATIVE` 二级 SSOT（如招商银行"闪电贷"专属 verdict）。
3. **多语言**：当前所有 SSOT 是中文，未来 i18n 化需要把 `LEVEL_NARRATIVE` 做成 `{zh: {...}, en: {...}}` 字典树。

---

**Lint 0 错。SSOT 测试 6/6 PASS。0 自相矛盾。**
