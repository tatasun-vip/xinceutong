-- =============================================================================
-- Migration 0002: business 4 维度分（v5 P0 补全）
-- 日期：2026-09-12（重写为 PostgreSQL 优先，因为生产是 Render PostgreSQL）
-- 背景：
--   v4 报告只有综合分（6 套产品加权），无法告诉企业主"扣分在哪儿、怎么提升"。
--   v5 给 Assessment 表加 dimensions JSON 字段，存「法人画像/企业画像/合规风险/行业景气」4 维度。
--   字段可空，老数据不受影响。
-- 用法：
--   # 生产（Render PostgreSQL，asyncpg + psycopg2）
--   psql "$DATABASE_URL" -f sql/migrations/0002_business_dimensions.sql
--
--   # 本地开发（SQLite）
--   sqlite3 server/db/salion.db < sql/migrations/0002_business_dimensions.sql
--
--   # 老 MySQL 环境（按需启用）
--   # mysql -uroot -p xinceutong < sql/migrations/0002_business_dimensions.sql
-- =============================================================================

-- ============ PostgreSQL（生产 Render）==========
-- IF NOT EXISTS 兼容幂等（重复跑不会报错；PostgreSQL 9.6+ 支持）
ALTER TABLE assessments ADD COLUMN IF NOT EXISTS dimensions JSONB;

-- 老数据回填（如果有需要的话）：business 类型的 assessment 把 dimensions 设为占位空对象
-- 实际是 optional，不强制回填
UPDATE assessments
SET dimensions = '{}'::jsonb
WHERE type = 'business' AND dimensions IS NULL;

-- 索引：业务用户查询时按 type 过滤 + dimensions JSONB 路径查询
CREATE INDEX IF NOT EXISTS idx_assessment_type ON assessments (type);
-- GIN 索引便于 dimensions 内的字段查询（可选，加速改善后推演）
-- CREATE INDEX IF NOT EXISTS idx_assessment_dimensions ON assessments USING GIN (dimensions);


-- ============ SQLite（本地开发）==========
/*
ALTER TABLE assessments ADD COLUMN dimensions JSON;
CREATE INDEX IF NOT EXISTS idx_assessment_type ON assessments (type);
*/


-- ============ MySQL（老环境，按需启用）==========
/*
SET @add_dim := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'assessments' AND column_name = 'dimensions');
SET @sql := IF(@add_dim = 0,
  'ALTER TABLE `assessments` ADD COLUMN `dimensions` JSON DEFAULT NULL COMMENT ''v5 P0 4 维度分（business 专用）'' AFTER `product_results`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @add_idx := (SELECT COUNT(*) FROM information_schema.statistics
  WHERE table_schema = DATABASE() AND table_name = 'assessments' AND index_name = 'idx_assessment_type');
SET @sql := IF(@add_idx = 0,
  'CREATE INDEX `idx_assessment_type` ON `assessments` (`type`)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
*/

SELECT '===== Migration 0002 完成（PostgreSQL 优先）=====' AS msg;
