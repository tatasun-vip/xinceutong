-- =============================================================================
-- Migration 0006: v22 信用查询一票否决（近 3 月 > 6 / 近 6 月 > 10）
-- 日期：2026-09-15
-- 背景：
--   v17 现状：近 3 月 > 6 = 0 分（仅扣分，不否决）
--   v22 决策（用户 2026-09-15）：央行征信硬指标，一票否决
--     - 近 3 月查询 > 6 = 拒贷（E 级直接）
--     - 近 6 月查询 > 10 = 拒贷（E 级直接）
-- 依据：
--   - 央行征信中心 2024 报告：硬查询 > 6 次/3 月 = 资金紧张信号
--   - 5 大行（建行/工行/招行/中行/农行）2026 个贷白皮书一致
-- 实施：
--   主路径：python -m scripts.init_v17_scorecard（delete + insert 全表重写）
--   本文件：作为 SQL audit trail + 应急手动修复
-- 用法（生产 PostgreSQL）：
--   psql "$DATABASE_URL" -f sql/migrations/0006_v22_credit_inquiry_veto.sql
-- =============================================================================

-- 1. 近 3 月 > 6：从"扣分"升级为"一票否决"
UPDATE scorecard_rules
SET is_veto = 1,
    score = 0,
    updated_at = NOW()
WHERE type = 'personal'
  AND variable = 'recent_3month_queries'
  AND option_label = '6次以上'
  AND product_type_id IS NULL;

-- 2. 新增近 6 月查询变量（4 档：0-3 / 4-6 / 7-10 / 10次以上）
-- 10次以上 = 一票否决
INSERT INTO scorecard_rules
  (category, variable, option_label, score, type, is_veto, is_deduction, dimension, policy_cap, sort_order, product_type_id, enabled, created_at, updated_at)
VALUES
  ('征信', 'recent_6month_queries', '0-3次', 8, 'personal', 0, 0, 'credit', NULL, 109, NULL, 1, NOW(), NOW()),
  ('征信', 'recent_6month_queries', '4-6次', 5, 'personal', 0, 0, 'credit', NULL, 110, NULL, 1, NOW(), NOW()),
  ('征信', 'recent_6month_queries', '7-10次', 2, 'personal', 0, 0, 'credit', NULL, 111, NULL, 1, NOW(), NOW()),
  ('征信', 'recent_6month_queries', '10次以上', 0, 'personal', 1, 0, 'credit', NULL, 112, NULL, 1, NOW(), NOW())
ON CONFLICT (variable, option_label, type, product_type_id) DO UPDATE SET
  score = EXCLUDED.score,
  is_veto = EXCLUDED.is_veto,
  is_deduction = EXCLUDED.is_deduction,
  dimension = EXCLUDED.dimension,
  sort_order = EXCLUDED.sort_order,
  enabled = 1,
  updated_at = NOW();

-- 3. 升级 validation_rules 文案与级别
UPDATE validation_rules
SET level = 'error',
    message = '近3个月查询超过6次，央行征信硬指标一票否决，几乎所有银行都会拒贷',
    updated_at = NOW()
WHERE rule_name = '近3个月查询过多';

-- 4. 新增近 6 月查询 validation rule
INSERT INTO validation_rules
  (rule_name, condition_json, message, level, is_deduction, enabled, created_at, updated_at)
VALUES
  ('近6月查询过多',
   '{"op": "in", "variable": "recent_6month_queries", "value": ["10次以上"]}'::jsonb,
   '近6个月查询超过10次，央行征信硬指标一票否决，几乎所有银行都会拒贷',
   'error', 0, 1, NOW(), NOW())
ON CONFLICT (rule_name) DO UPDATE SET
  condition_json = EXCLUDED.condition_json,
  message = EXCLUDED.message,
  level = EXCLUDED.level,
  enabled = 1,
  updated_at = NOW();
