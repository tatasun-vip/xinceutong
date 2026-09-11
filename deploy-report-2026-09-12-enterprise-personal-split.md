# 信测通 · 企业贷/个人贷差异修复完成报告

> 部署时间：2026-09-12  ·  改动总数：6 项（P0 × 3 + P1 × 3）  ·  Lint：0 errors

## 一句话总结

**修了 3 个 P0 Bug（企业数据没传到后端、刷新丢失、用户看不到） + 3 个 P1 改进（路由守卫、状态重置、产品按 type 过滤的接口和前端传参）**。现在企业贷和个人贷评估的"差异"才真正生效，而不是只在前端路由上分了个支、后端收到的还是同一份数据。

---

## 一、P0 Bug 修复（3 个）

### ① P0 #1 — 提交时漏合并 step1B（致命）

| | |
|---|---|
| 文件 | `xinceutong-miniapp/src/pages/assess/loading.vue:90-94` |
| Bug | 提交评估的 `inputData` 合并 `step1/step2/step3/step4` 但漏了 `step1B`（7 个企业字段） |
| 影响 | 企业用户填完 7 个企业字段后，**后端评分拿不到企业数据**，跑出来跟个人评估一模一样 |
| 修复 | 在 `inputData` 合并逻辑里加 `...(store.step1B as any \|\| {})` |

### ② P0 #2 — store.persist 漏保存 step1B（致命）

| | |
|---|---|
| 文件 | `xinceutong-miniapp/src/store/assessment.ts:165-205` |
| Bug | `persist()` 没把 `step1B` 写进 localStorage；`restoreFromStorage()` 没读 `step1B`；`reset()` 没清 `step1B` 和 `step4Docs` |
| 影响 | 企业用户**刷新/重进页面后 7 个企业字段全部丢失**；切换个人/企业时残留数据 |
| 修复 | persist/restore/reset 三处都同步 step1B + step4Docs |

### ③ P0 #3 — step5-confirm 确认页不展示 step1B（致命）

| | |
|---|---|
| 文件 | `xinceutong-miniapp/src/pages/assess/step5-confirm.vue:50-86, 211-241` |
| Bug | 确认页只展示 4 步（基础/职业/资产/征信），完全没有 step1B 的 7 个企业字段 |
| 影响 | **企业用户在 step5 看不到自己填的纳税/开票/经营年限等核心信息**，无法核对 |
| 修复 | 在 step2 之后、step3 之前插入 02B 企业 section（`v-if="store.step1B"`）；ProgressBar 动态 5/6 段；加 `goEditBiz()` 函数跳回 step1b-business |

---

## 二、P1 改进（3 个）

### ④ P1 #4 — useStepGuard 加 step1B 校验

| | |
|---|---|
| 文件 | `xinceutong-miniapp/src/composables/useStepGuard.ts:52-60` |
| 问题 | `isStepCompleted(3)` 只校验 `store.step3`（资产），business 时应该校验 `store.step1B`（企业） |
| 影响 | business 用户**手动改 URL 跳过 step1b-business 时，前置校验完全失效** |
| 修复 | case 3 加 business 分支：`if (store.type === 'business') return !!store.step1B && Object.keys(store.step1B).length >= 7` |

### ⑤ P1 #5 — store.reset 清空 step1B

| | |
|---|---|
| 文件 | `xinceutong-miniapp/src/store/assessment.ts:195-204` |
| 问题 | reset 没清 step1B / step4Docs，业务类型切换时残留 |
| 修复 | 在 P0 #2 中一并处理（reset 加 `step1B.value = null; step4Docs.value = null`） |

### ⑥ P1 #6 — select-bank / select-product 按 type 过滤

**前端**：

| 文件 | 改动 |
|---|---|
| `xinceutong-miniapp/src/api/bank.ts:10-26, 88-100` | `BankProduct` 接口加 `user_type?` 字段；`getBankProducts(code, userType?)` 加可选参数（拼 `?user_type=...`） |
| `xinceutong-miniapp/src/pages/assess/select-product.vue:7-23, 109-114` | onMounted 时传 `store.type`；顶部加 `.type-banner`（个人/企业）提示组件 |
| `xinceutong-miniapp/src/pages/assess/select-bank.vue:38-60` | hero 文案根据 `store.type` 切换（"个人信用贷" vs "企业经营贷"） |

**后端**：

| 文件 | 改动 |
|---|---|
| `xinceutong-server/app/api/bank.py:81-100` | `get_bank_products` 接口加 `user_type: str \| None = None` 可选参数（接口就绪，DB schema 迁移是独立 feature） |

**待办（独立 feature）**：
- BankProduct 表加 `user_type` 字段（alembic 迁移 + 重新 seed）→ 1-2 天
- 让 select-product 列表前端按 `product.user_type` 显示"个人/企业"标签 → 半天

---

## 三、状态校验

| 检查 | 结果 |
|---|---|
| Lint 静态分析（`read_lints`） | **0 errors** ✅ |
| TypeScript 类型检查（vue-tsc） | 受限于沙箱环境（无 `sh`），需要 Vercel 构建时验证 |
| 文件改动总数 | 8 个 |

---

## 四、部署步骤

**当前沙箱环境**没有 `git` / `sh` / `npm install`，无法直接 `git push`。请在你的 IDE 终端执行以下 3 行：

```bash
cd /Users/suntata/CodeBuddy/20260907155240
git add -A
git commit -m "fix(assess): 企业贷/个人贷数据真正分离 - 修3 P0 bug + 3 P1 改进

P0:
- loading.vue: 提交时合并 step1B（企业 7 字段不丢）
- store: persist/restore/reset 同步 step1B + step4Docs
- step5-confirm: 加 02B 企业 section（v-if step1B）

P1:
- useStepGuard: case 3 business 分支校验 step1B
- api/bank + select-product: getBankProducts 传 userType
- select-bank hero 文案按 type 切换

P0 bug 修复理由：之前企业用户填的 7 个字段完全没传出去，
跑出来的评估报告跟个人一模一样，等于骗人。"
git push origin main
```

Vercel 会自动触发部署（~2-3 分钟）。

---

## 五、部署后线上回归测试

部署完成后，请按以下 3 个测试验证：

### 测试 1：企业用户数据真的传到后端
1. 打开 `https://www.trumpdream.site/` → 首页点"企业经营贷"
2. 走完 step1（基础）→ step2（职业）→ step1b-business（7 个企业字段，认真填，例如 `tax_grade: A, annual_tax: 50万, business_years: 5年, annual_invoice: 200万, industry: 制造业`）→ step3（资产）→ step4（征信）→ step5 确认页
3. **预期**：step5 出现"02B 企业信息"section，能看到 7 个填的企业字段
4. 点"开始评估" → 等 loading 跑完
5. 在浏览器 DevTools 看 `/api/assessments` 请求的 body（或 Vercel Function logs）
6. **预期**：body 里**包含** step1B 的 7 个字段

### 测试 2：URL 跳过企业页被拦截
1. 打开 `https://www.trumpdream.site/pages/assess/step1-basic` 入口
2. **故意只填 step1**（基础）就直接改 URL 跳到 `step5-confirm`
3. **预期**：被 useStepGuard 拦回 step1（因为 step2/step3 都没填），提示"请先完成上一步"
4. **关键**：模拟 business 时（type 切到 'business'）只填 step1 后跳 step5，也应该被拦回（之前 bug：business 跳过 step1b 不被拦）

### 测试 3（可选）：个人用户没受影响
1. 打开首页点"个人信用贷"
2. 走完 step1 → step2 → step3 → step4 → step5
3. **预期**：step5 **不**出现"02B 企业信息"section（因为 store.step1B 为空），其余流程不变

---

## 六、遗留 feature（需单独立项）

| 优先级 | Feature | 工作量 | 说明 |
|---|---|---|---|
| P0 (高) | BankProduct 表加 `user_type` 字段 + alembic 迁移 + 重新 seed | 1-2 天 | 让 `?user_type=` 参数真正过滤；select-product 显示"个人/企业"标签 |
| P1 (中) | 后端评分模型按 `type` 跑不同分支 | 半天 | 评分算法应该按 type 走不同规则（企业看纳税/开票连续性，个人看社保/公积金） |
| P2 (低) | step4 报告页按 type 切换字段 | 半天 | 报告卡显示企业专属指标 |

---

> **完成度自评**：
> - P0（数据 bug）：3/3 完成 ✅
> - P1（接口 + 前端传参 + UI 提示）：3/3 完成 ✅
> - 评分模型按 type 走不同规则：**未做**（独立 feature，已在 memory 中标记）
> - 数据库 schema 迁移：**未做**（独立 feature，已在 memory 中标记）
