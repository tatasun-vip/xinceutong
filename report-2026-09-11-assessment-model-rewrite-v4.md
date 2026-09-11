# 信测通评估模型 v4 P0 修复报告（业务补全 + 标签修复 + 辅助资料）

> 日期：2026-09-11 · 范围：v3 之后的「补全 + 校对 + 辅助资料」共 6 项 + 自检全通过 · 状态：已落地

## 一、用户要求的 3 件事

### ① 补全
- **business 7 个变量通用规则**（51 条）— 之前业务类型用户走纳税贷/开票贷全部 score=0
- **6 大产品专属规则**（5/6 加权 ×1.5）— 之前 5/6 完全没规则
- **前端 business 问卷**（step1b-business 7 步）— 之前 type=business 走 personal 5 步全错
- **13 个变量中文名**（_var_zh）— 之前显示给用户的标签用 raw 变量名
- **DSR cap**（v3 已做，验证触发）

### ② 校对
- 7 项自检 PASS（personal A 评级、business tax/invoice 综合分、_var_zh、_build_tags、_build_suggestions）
- 前后端 label 一致性校对（修正 "5000 以下" / "5000以下" 双 label）
- 修复 3 个 placeholder / bug：
  - `_build_suggestions`: 永久 `False` 占位
  - `_build_tags`: social_security label 不匹配（"连续1年以上" 不存在）
  - `_var_zh`: 13 个变量无中文名

### ③ 线下辅助资料
- **5 类全选填**：房本 / 行驶证 / 营业执照 / 纳税凭证 / 对公流水
- **不影响评分**：仅用于人工对接参考
- **最多 200 字备注**：资产冻结/诉讼/换工作等特殊情况
- **可单张图上传**（uni.chooseImage，album/camera）
- **折叠面板**：默认收起，展开后才显示 5 类

## 二、修改清单（共 9 处）

| # | 文件 | 改动 |
|---|---|---|
| 1 | `server/scripts/init_business_rules.py` | **新建**51 条 business 通用+专属规则（7 变量 ×6 档 + 5/6 加权）|
| 2 | `server/app/services/scorecard_engine.py` | `_var_zh` 补全 13 个变量 |
| 3 | `server/app/services/scorecard_engine.py` | `_build_suggestions` 修 label + 去空格兼容 |
| 4 | `server/app/services/scorecard_engine.py` | `_build_tags` social_security label 兼容 |
| 5 | `miniapp/src/constants/assess-options.ts` | 加 7 个 business 选项 + 5 个 OFFLINE_DOC_OPTIONS |
| 6 | `miniapp/src/store/assessment.ts` | 加 Step1B + Step4Docs 类型 + actions |
| 7 | `miniapp/src/pages/assess/step1b-business.vue` | **新建**企业信息问卷（7 步，business 类型专属）|
| 8 | `miniapp/src/pages/assess/step4-credit.vue` | 折叠面板"线下辅助资料"（5 类全选填）|
| 9 | `miniapp/src/pages.json` | 新增 step1b-business 路由 |

## 三、自检结果（7/7 PASS）

```
[PASS] personal A → B 级（score 69.0，4 产品加权平均）
[PASS] business tax 综合分 69.0（之前=0）
[PASS] 纳税贷 score 71.0（之前=0）
[PASS] 开票贷 score 48.0（之前=0）
[PASS] _build_suggestions 修复：月收入 5000 以下 C 级触发 '提升收入' 建议
[PASS] _build_tags 修复：social_security 标签逻辑正确（advs=0, risks=2）
[PASS] _var_zh 补全 13 个变量（13/13）
✅ 自检全部通过
```

## 四、关键示例

### A. 业务类型用户（之前完全不可用）
```
business 法人（A 级纳税+科技互联网+深圳）：
  tax       score=71.0 level=A   max=100.0万 [CAPPED 渠道 100万上限]
  invoice   score=67.0 level=B   max=103.5万
  综合 score=69.0 level=B 额度=38.2-51.8万 利率=6.0-12.0% 通过率=中高
```

### B. 渠道 cap 触发
```
[channel_cap] product=tax level=A raw=[1020.0万 ~ 1380.0万] → capped=[73.9万 ~ 100.0万]
[channel_cap] product=tax level=C raw=[89.2万 ~ 120.8万] → capped=[73.9万 ~ 100.0万]
```

### C. 标签/建议逻辑
```
低月收入 C 级用户：
  → "3-6 个月：提升收入流水（兼职、副业等）" ✅ 修复生效

社保连续 B 级用户：
  → "社保连续缴存"（用 [连续1-3年, 连续3年以上, 连续 1-3 年, 连续 3 年以上] 4 个 label 兼容）✅
```

## 五、运行

```bash
cd xinceutong-server && source .venv/bin/activate

# 1. 初始化 business 规则（51 条）
python -m scripts.init_business_rules

# 2. 跑自检（7 项断言）
python -m scripts.selfcheck_v4

# 3. 历史数据用 v4 模型重算（备份表自动建）
python scripts/migrate_v2_recalc.py

# 干跑模式（不写库）
python -m scripts.selfcheck_v4 --dry-run  # 自检脚本目前直接读 db，不需 dry-run
python scripts/migrate_v2_recalc.py --dry-run
```

## 六、用户操作路径

**personal 用户**（保持原样）：
```
type.vue → step1-basic → step2-career → step3-asset → step4-credit → step5-confirm
```

**business 用户**（新增 step1b）：
```
type.vue → step1-basic → step2-career → step1b-business(7 企业变量) → step3-asset → step4-credit → step5-confirm
```

**线下辅助资料**（所有类型共用）：
```
step4-credit 末尾"📎 线下辅助资料"折叠面板 → 勾选 5 类 → 上传图片 → 备注
```

## 七、回滚

```sql
-- 用最新备份表回滚：
UPDATE assessments a, backup_assessments_20260911_221809 b
SET 
  a.score = b.score,
  a.level = b.level,
  a.limit_min = b.limit_min,
  a.limit_max = b.limit_max,
  a.product_results = b.product_results
WHERE a.id = b.id;
```

## 八、剩余待办（v5+ 候选）

- 6 大产品专属规则补全（已完成 5/6 全部 business 加权 ✅）
- `_build_suggestions` 更多智能化（如"近 3 个月查询"触发立即"停止申请"）
- 报告"未通过项"按维度细分（critical / warning / info）
- `pd_calibration` 接入历史数据做实际校准
- 前端 Web 端样式同步
- 线下辅助资料 后端 API（目前只本地存储，未上传服务器）
