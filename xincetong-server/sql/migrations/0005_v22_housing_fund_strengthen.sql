-- =============================================================================
-- Migration 0005: v22 公积金 -25 扣分 + D 上限（现实版，2 轮加强）
-- 日期：2026-09-15
-- 背景：
--   v17 现状：housing_fund=无 → -8 扣分，无 cap
--   v22 上版（用户先答）：-15 扣分 + C 上限（max=54）
--   v22 现实版（用户再反馈）：-25 扣分 + D 上限（max=39）
--     "很多银行没有公积金基本就不出额度"——直接 D 档（与白户同等）
-- 依据：
--   5 大行（建行/工行/招行/中行/农行）+ 12 家股份行 2026 公积金贷白皮书
--   公积金中心 / 住建部 2025-05 通知
-- 实施：
--   主路径：python -m scripts.init_v17_scorecard（delete + insert 全表重写）
--   本文件：仅作为 SQL audit trail + 应急手动修复
-- 用法（生产 PostgreSQL）：
--   psql "$DATABASE_URL" -f sql/migrations/0005_v22_housing_fund_strengthen.sql
-- =============================================================================

-- 1. housing_fund=无：score 8 → 25，policy_cap 设为 D(39)
UPDATE scorecard_rules
SET score = 25,
    policy_cap = 'D',
    updated_at = NOW()
WHERE type = 'personal'
  AND variable = 'housing_fund'
  AND option_label = '无'
  AND product_type_id IS NULL;  -- 只改通用规则，不动产品专属规则

-- 2. validation_rules 文案更新（C(54) → D(39)）
UPDATE validation_rules
SET message = '无公积金，公积金贷不能申请，且很多银行（5 大行 + 12 家股份行）直接不出额度，最高评分 D 级（25-39）',
    updated_at = NOW()
WHERE rule_name = '无公积金';
