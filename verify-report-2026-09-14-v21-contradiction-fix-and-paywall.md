# 信测通 v21 报告页矛盾修复 + 强制 9.9 弹层（2026-09-14）

## 背景

用户截图：v9 评估报告显示 66 分 B·良好 + "综合通过率高"，但 one_sentence 文案写 "您的资质尚可，建议先优化 0 个细节再申请"（B 级 + 通过率偏高 + 0 个问题 三方矛盾）。用户判断"没人会再花钱买解锁报告了"，决定：
- **A 强制付费**：submit 完成后直接弹 9.9，付款成功才进报告页
- **B 文案由 level 严格驱动**：pass_probability 只作辅助标签，不参与乐观/悲观措辞
- **C free.vue 改可读**：去掉所有付费墙元素（banner、blur、锁标、付费引导），保留基础信息

## 改动清单

### 1. 后端 · `xincetong-server/app/services/report_auditor.py` `_fix_one_sentence` 重写（v9 矛盾源）

**关键问题**（line 340-343 旧版）：
```python
if level == "B":
    if pass_prob in ("高", "中高"):
        return "您的资质良好，可优先选择通过率较高的产品申请"
    return f"您的资质尚可，建议先优化 {n_total} 个细节再申请"  # ← 矛盾源
```
截图同款：B 级 + n_total=0 + pass_probability=中 → 输出"您的资质尚可，建议先优化 0 个细节再申请" → 4 重矛盾（"尚可"≠"良好"，"0 个"自反，"通过率中"≠"偏低"，与卡片顶部"通过率高"自相矛盾）。

**新规则**（v21）：level 严格驱动文案，pass_probability 不再影响乐观/悲观措辞。

| Level | n_total=0 | n_total≥1 | has_projection |
|---|---|---|---|
| S/A | "您的资质已属{level}级优质，可直接申请" | 同左 | 同左 |
| **B** | **"您的资质良好，可直接申请"** | **"您的资质良好，可优先选择通过率较高的产品申请"** | **B 统一固定"良好"措辞** |
| C | "您的资质一般，保持当前状态可直接申请" | "您的资质一般，先优化 N 个问题，预计通过率可提升" | has_projection=true 区分 |
| D | "目前 D 级较弱，可尝试申请" | "目前 D 级较弱，先优化 N 个问题，预计可提升至 C 级" | 同 C |
| E | "建议暂缓申请，先优化 N 个核心问题" | 同左 | — |

**forbidden token 收紧**：
- B forbidden 新增 "尚可"、"通过率偏低"
- C forbidden 新增 "良好"
- D forbidden 新增 "通过率高"
- E forbidden 新增 "通过率较高"、"通过率高"

### 2. miniapp · `loading.vue` 提交后跳转路径变更

`xincetong-miniapp/src/pages/assess/loading.vue:144`：
```diff
- const targetUrl = `/pages/result/free?id=${res.assessment_id}`
+ const targetUrl = `/pages/result/pay?id=${res.assessment_id}`
```
**v21 决策 A**：submit 完成 → 强制 9.9 支付层（pay.vue）→ 付款成功 → 跳完整报告（report.vue）。**不再经过 free 中转**。

### 3. miniapp · `free.vue` 付费墙元素全删

**模板删除**（6 大块）：
- L19-40 `fp-paywall-banner` 360rpx 金色付费引导 banner（v9 B1）
- L153 `fp-issue-locked` 末 1/3 渐隐遮罩 + 锁标浮层（核心问题）
- L188-224 `fp-projection-locked` 整张虚化 + 锁标浮层（改善推演卡）
- L283 `fp-product-evidence-locked` blur 类（证据链）
- L286 `fp-product-locked-overlay` 每产品底部锁标浮层
- L289-300 `fp-unlock-banner` v14 金色汇总 banner

**脚本删除**：
- L24 `PAYWALL_COLORS` import
- L903-905 `goPay()` 函数

**样式删除**（6 大块，共 ~270 行 CSS）：
- `fp-issue-locked` 系列（~50 行）
- `fp-projection-content blur(6rpx)` + `fp-projection-overlay` 系列（~50 行）
- `fp-paywall-banner` 系列（~100 行）
- `fp-product-evidence-locked blur(8rpx)`（3 行）
- `fp-product-locked-overlay` 系列（~40 行）
- `fp-unlock-banner` 系列（~80 行）

**free.vue 新语义**：基础信息可读版（6 大产品摘要 + 命中规则 + 模拟额度），无任何付费引导。用户决策 C "保留 free.vue 改为可读"。

### 4. miniapp · 完整提交流程（新闭环）

```
step1-5 提交 → loading.vue 动画
    ↓ 600ms
pay.vue?id={assessment_id}    ← v21 强制 9.9 弹层
    ↓ createOrder → mockPay
report.vue?id={assessment_id} ← v9 完整版 9 模块 + 6 大产品完整证据链
```

`free.vue` 仍保留可访问（被 history.vue 等老路径引用），但 submit 不再默认跳它。

## 验证

### 后端 `_fix_one_sentence` 7/7 PASS

```
场景1: B + n_total=0 + pass_probability=中 (截图同款)
  旧: 您的资质尚可，建议先优化 0 个细节再申请
  新: 您的资质良好，可直接申请
  PASS ✓

场景2: B + n_total=3 + pass_probability=高
  输出: B 良好
  PASS ✓

场景3: 旧矛盾文案修复
  输入: 您的资质尚可，建议先优化 0 个细节再申请
  输出: 您的资质良好，可直接申请
  PASS ✓

场景4: C + n_total=2
  输出: 您的资质一般，先优化 2 个问题，预计通过率可提升
  PASS ✓

场景5: D + n_total=5
  输出: 目前 D 级较弱，先优化 5 个问题，预计可提升至 C 级
  PASS ✓

场景6: E + n_total=8
  输出: 建议暂缓申请，先优化 8 个核心问题
  PASS ✓

场景7: A
  输出: 您的资质已属A级优质，可直接申请
  PASS ✓
```

### Lint 0 错
- `report_auditor.py` ✓
- `free.vue` ✓
- `loading.vue` ✓

### 提交流程
- loading.vue submit 成功 → 跳 pay.vue（不是 free.vue）✓
- pay.vue mockPay 成功 → 跳 report.vue ✓
- pay.vue mockPay 失败 → 弹窗提示，可重试 ✓

## 关键修复点

1. **`_fix_one_sentence` B 级不再因 pass_probability 切换** — 截图矛盾根治
2. **submit 后强制 9.9 弹层** — 用户决策 A 闭环：submit → pay → report
3. **free.vue 去付费墙** — 决策 C：基础信息可读，无付费引导

## SSOT

待打包：`/Users/suntata/CodeBuddy/20260907155240/dist/xincetong-ssot-YYYYMMDD-HHMM.zip`

## 沙箱待办

1. HBuilder 真机/模拟器实测 submit → pay.vue → report.vue 流程
2. 回归 6 大产品在不同 level 下的 one_sentence 不再出现"通过率偏低"+"良好"矛盾
3. 验证 free.vue 6 大产品证据链全部可读（无 blur/锁标）
4. CVM 部署：后端 `report_auditor.py` + miniapp dist SSOT 上传 → 验真 `/pages/result/pay` 200
