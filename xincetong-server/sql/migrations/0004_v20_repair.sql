-- =============================================================================
-- Migration 0004: v20 修复（2026-09-14）
-- 背景：
--   v17 评分卡上线时（0003），cvm_deploy.sh 用 `psql "$DB_URL"` 没传用户/密码，
--   静默失败但被 `| tail -8` 吞掉。结果生产库一直缺 3 列：
--     - scorecard_rules.is_deduction
--     - scorecard_rules.dimension
--     - scorecard_rules.policy_cap
--     - validation_rules.is_deduction
--   ORM 实际查询时 UndefinedColumnError，污染 asyncpg 事务状态为 aborted，
--   后续 INSERT 全部 500。
--   2026-09-14 22:56 现场手动补列 + 重跑 init_v17_scorecard 恢复 142+16 条规则。
--   这次 0004 把 ALTER 显式化，幂等（IF NOT EXISTS），不依赖 0003 是否真的跑过。
-- 用法：
--   psql "$DATABASE_URL" -f sql/migrations/0004_v20_repair.sql
-- =============================================================================

-- 显式补 3 列（即使 0003 跑过也是 IF NOT EXISTS 跳过）
ALTER TABLE scorecard_rules
  ADD COLUMN IF NOT EXISTS is_deduction SMALLINT NOT NULL DEFAULT 0;
ALTER TABLE scorecard_rules
  ADD COLUMN IF NOT EXISTS dimension VARCHAR(16) NOT NULL DEFAULT 'misc';
ALTER TABLE scorecard_rules
  ADD COLUMN IF NOT EXISTS policy_cap VARCHAR(8);

-- 显式补 validation_rules.is_deduction
ALTER TABLE validation_rules
  ADD COLUMN IF NOT EXISTS is_deduction SMALLINT NOT NULL DEFAULT 0;

-- 索引
CREATE INDEX IF NOT EXISTS idx_score_dimension ON scorecard_rules (dimension);
CREATE INDEX IF NOT EXISTS idx_score_type ON scorecard_rules (type);

SELECT '===== Migration 0004 完成（v20 修复：列 + 索引兜底）=====' AS msg;
