-- =============================================================================
-- Migration 0003: v17 评分卡（5 维度 + 加扣分 + 政策性上限）
-- 日期：2026-09-14
-- 背景：
--   v15 之前：纯加分制（raw/174*100），无公积金不扣分 → 无公积金用户也能拿高分，与 2026 银行实操不符
--   v17：按 2026 银保监《商业银行互联网贷款管理办法》+ 央行征信 + 5 大行个贷白皮书 + FICO 中国版
--   改 3 段式评分（加分 + 扣分 + 一票否决）+ 5 维度权重 + 政策性上限
--   例：白户 → C 级上限 54；无公积金 → B 级上限 69；关键保障全缺 → C 级；纯白户无任何加分 → D 级
-- 用法：
--   # 生产（PostgreSQL）
--   psql "$DATABASE_URL" -f sql/migrations/0003_v17_scorecard.sql
--
--   # 本地开发（SQLite）
--   sqlite3 server/db/salion.db < sql/migrations/0003_v17_scorecard.sql
-- =============================================================================

-- ============ PostgreSQL（生产）==========
-- 给 scorecard_rules 加 3 字段：dimension（5 维度）/ is_deduction（加扣分）/ policy_cap（政策性上限）
ALTER TABLE scorecard_rules
  ADD COLUMN IF NOT EXISTS dimension VARCHAR(16) DEFAULT 'misc',  -- 5 维度之一：credit/debt/asset/personal/public/misc
  ADD COLUMN IF NOT EXISTS is_deduction SMALLINT DEFAULT 0,         -- 0=加分 1=扣分
  ADD COLUMN IF NOT EXISTS policy_cap VARCHAR(8) DEFAULT NULL;     -- 上限等级 S/A/B/C/D（命中此规则后 final_score 不能超过此等级上界）

-- 给 validation_rules 加 is_deduction（纠错规则也分加扣分）
ALTER TABLE validation_rules
  ADD COLUMN IF NOT EXISTS is_deduction SMALLINT DEFAULT 0;

-- 索引：按维度过滤（5 维度分别统计用）+ 按 type 过滤（personal/business）
CREATE INDEX IF NOT EXISTS idx_score_dimension ON scorecard_rules (dimension);
CREATE INDEX IF NOT EXISTS idx_score_type ON scorecard_rules (type);

-- 老数据回填：已有 94 + 35 = 129 条规则，dimension 字段默认 'misc'，is_deduction 默认 0
-- 重写由 init_v17_scorecard.py 完成（推荐清空后重写，确保 5 维度分类正确）
-- 备份老数据 SQL：
--   CREATE TABLE scorecard_rules_v16_backup AS SELECT * FROM scorecard_rules;
--   备份完后可执行：TRUNCATE scorecard_rules; 再跑 init_v17_scorecard.py


-- ============ SQLite（本地开发）==========
/*
ALTER TABLE scorecard_rules ADD COLUMN dimension VARCHAR(16) DEFAULT 'misc';
ALTER TABLE scorecard_rules ADD COLUMN is_deduction SMALLINT DEFAULT 0;
ALTER TABLE scorecard_rules ADD COLUMN policy_cap VARCHAR(8) DEFAULT NULL;

ALTER TABLE validation_rules ADD COLUMN is_deduction SMALLINT DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_score_dimension ON scorecard_rules (dimension);
CREATE INDEX IF NOT EXISTS idx_score_type ON scorecard_rules (type);
*/


-- ============ MySQL（老环境，按需启用）==========
/*
SET @add_dim := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'scorecard_rules' AND column_name = 'dimension');
SET @sql := IF(@add_dim = 0,
  'ALTER TABLE `scorecard_rules` ADD COLUMN `dimension` VARCHAR(16) DEFAULT ''misc'' COMMENT ''5 维度之一：credit/debt/asset/personal/public'' AFTER `category`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @add_ded := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'scorecard_rules' AND column_name = 'is_deduction');
SET @sql := IF(@add_ded = 0,
  'ALTER TABLE `scorecard_rules` ADD COLUMN `is_deduction` SMALLINT DEFAULT 0 COMMENT ''0=加分 1=扣分'' AFTER `is_veto`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @add_cap := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'scorecard_rules' AND column_name = 'policy_cap');
SET @sql := IF(@add_cap = 0,
  'ALTER TABLE `scorecard_rules` ADD COLUMN `policy_cap` VARCHAR(8) DEFAULT NULL COMMENT ''政策性上限等级 S/A/B/C/D'' AFTER `is_deduction`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

CREATE INDEX `idx_score_dimension` ON `scorecard_rules` (`dimension`);
CREATE INDEX `idx_score_type` ON `scorecard_rules` (`type`);
*/


SELECT '===== Migration 0003 完成（v17 评分卡：5 维度 + 加扣分 + 政策性上限）=====' AS msg;
