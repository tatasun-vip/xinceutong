# 信测通评估报告模型重整报告 v3（含 P3 渠道+DSR 修正）

> 日期：2026-09-11 · 范围：P0+P1+P2（19 处修复 + 1 个真实 bug 附加）+ **P3（前端展示 + 历史数据修正 + DSR 约束）** · 状态：已落地

## 一、P3 4 项修复（用户要求后续 1-4 全部完成）

### 1. P3-1 前端展示"线上 X 万 / 线下 Y 万"双额度卡片
- 修改文件：`xinceutong-miniapp/src/components/product-card/ProductCard.vue`
- 新增区块 `.pc-channel`：每个产品卡显示线上最高（蓝）+ 线下最高（绿）
- 让用户**直接看到银行实际能给的最高额度**，而不是只看一个混淆的"综合额度"

### 2. P3-2 cap 触发时前端显示 limit_reason 提示
- 修改文件：`ProductCard.vue` 加 `.pc-cap-hint`（金色 info 图标 + 文字）
- 当 `product.limit_capped === true` 时，自动显示后端返回的 `limit_reason`
- 示例如："测算值 489 万超过「线下最高 100 万」监管上限，已按线下额度 cap"

### 3. P3-3 历史数据修正（86 条全部重算）
- 新建脚本：`xinceutong-server/scripts/migrate_v2_recalc.py`
- 用 P0+P1+P2+P3 新模型重算所有已存的 86 条 assessment 记录
- 备份表：`backup_assessments_20260911_220719`（自动生成）
- 关键变化示例：
  - #62 旧：S 级 1209-2246 万 → **新：83.8-113.4 万**（3/6 产品被 cap）
  - #75 旧：A 级 705-1310 万 → **新：88.7-120 万**（1/6 被 cap）
  - #65 旧：D 级 176-327 万 → **新：88.7-120 万**（1/6 被 cap）
- 干跑：`python scripts/migrate_v2_recalc.py --dry-run`
- 真跑：`python scripts/migrate_v2_recalc.py`（会先备份再重写）

### 4. P3-4 DSR 加"本次新贷款月供"约束
- 修改文件：`xinceutong-server/app/services/scorecard_engine.py`
- 问题：chosen × 1.15 倍放大后，实际 DSR = 0.5 × 1.15 = 0.575，超过 0.5 上限
- 修复：当 `limit_max > limit_dsr`（DSR 反算的精确本金），把 `limit_max` cap 到 `limit_dsr`
- 验证：
  ```
  level=S, 触发 DSR cap：
  [dsr_cap] chosen=19.4万 raw_max=22.3万 dsr_exact=19.4万 → cap limit_max to 19.4万
  (DSR 上限 0.5，1.15 倍放大后月供 = 0.575 月收入，超标)
  ```

## 二、修改清单（共 27 处）

| # | 文件 | 改动 |
|---|---|---|
| 1-15 | （同 v2）| P0+P1 模型参数 + disclaimer + 前后端 label |
| 16-19 | （同 v2）| P2 渠道 cap + ProductResult 扩字段 |
| **20** | `xinceutong-miniapp/src/api/assessment.ts` | 扩 4 字段：channel_online_max / channel_offline_max / limit_capped / limit_reason |
| **21** | `xinceutong-miniapp/src/components/product-card/ProductCard.vue` | 新增 .pc-channel 双额度区块 + .pc-cap-hint cap 提示 |
| **22** | `xinceutong-server/app/services/scorecard_engine.py` | P3-4 DSR cap：limit_max > DSR 上限 → 截到 DSR 上限 |
| **23** | `xinceutong-server/scripts/migrate_v2_recalc.py` | **新建**历史数据重算脚本（备份+重算+对比） |

## 三、运行 P3 脚本

```bash
cd xinceutong-server && source .venv/bin/activate
# 干跑
python scripts/migrate_v2_recalc.py --dry-run
# 真跑（先备份后写库）
python scripts/migrate_v2_recalc.py
```

## 四、回滚方案

```sql
-- 用备份表回滚：
UPDATE assessments a, backup_assessments_20260911_220719 b
SET 
  a.score = b.score,
  a.level = b.level,
  a.limit_min = b.limit_min,
  a.limit_max = b.limit_max,
  a.product_results = b.product_results,
  ...
WHERE a.id = b.id;
```

## 五、剩余待办（v4+ 候选）

- 6 大产品专属规则补全（5/6 缺）
- `_build_suggestions` placeholder 修
- 报告"未通过项"按维度细分
- pd_calibration 接入历史数据做实际校准
- 前端 Web 端样式同步（目前只改 miniapp）
