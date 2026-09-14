-- =============================================================================
-- Migration 0001: 6 大产品独立建模改造
-- 时间: 2026-09-10
-- 用途: 已部署环境升级（init.sql 已含此内容，新部署忽略本文件）
-- =============================================================================

-- 1. 加 product_types 表
CREATE TABLE IF NOT EXISTS `product_types` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `code` VARCHAR(32) UNIQUE NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `subtitle` VARCHAR(128) DEFAULT NULL,
  `user_type` ENUM('personal','business') NOT NULL,
  `limit_formula` VARCHAR(64) NOT NULL,
  `rate_min` DECIMAL(5,2) NOT NULL,
  `rate_max` DECIMAL(5,2) NOT NULL,
  `default_pass` VARCHAR(8) DEFAULT '中',
  `focus_vars` JSON DEFAULT NULL,
  `key_points` JSON DEFAULT NULL,
  `description` TEXT,
  `recommend` INT DEFAULT 0,
  `sort_order` INT DEFAULT 0,
  `enabled` TINYINT DEFAULT 1,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_code` (`code`),
  INDEX `idx_user_type` (`user_type`),
  INDEX `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='6 大产品类型配置';

-- 2. 加 site_config 表
CREATE TABLE IF NOT EXISTS `site_config` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `config_key` VARCHAR(64) UNIQUE NOT NULL,
  `config_value` TEXT NOT NULL,
  `config_label` VARCHAR(128) DEFAULT NULL,
  `group_name` VARCHAR(32) DEFAULT 'text',
  `remark` VARCHAR(255) DEFAULT NULL,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站点配置';

-- 3. 改造 scorecard_rules（加 bank_id + product_type_id）
SET @add_scorecard_bank := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'scorecard_rules' AND column_name = 'bank_id');
SET @sql := IF(@add_scorecard_bank = 0,
  'ALTER TABLE `scorecard_rules` ADD COLUMN `bank_id` INT DEFAULT NULL COMMENT ''关联银行（NULL=通用）'' AFTER `id`, ADD COLUMN `product_type_id` INT DEFAULT NULL COMMENT ''关联产品类型（NULL=通用）'' AFTER `bank_id`, ADD INDEX `idx_bank` (`bank_id`), ADD INDEX `idx_product` (`product_type_id`)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4. 改造 assessments（加 product_results + paid_at + full_report）
SET @add_assess_product := (SELECT COUNT(*) FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 'assessments' AND column_name = 'product_results');
SET @sql := IF(@add_assess_product = 0,
  'ALTER TABLE `assessments` ADD COLUMN `product_results` JSON DEFAULT NULL COMMENT ''6 大产品独立测算结果'' AFTER `products`, ADD COLUMN `paid_at` DATETIME DEFAULT NULL COMMENT ''付费时间'' AFTER `is_paid`, ADD COLUMN `full_report` MEDIUMTEXT DEFAULT NULL COMMENT ''完整报告 Markdown（付费后生成）'' AFTER `paid_at`',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5. 加 3 张银行表（如未建）
CREATE TABLE IF NOT EXISTS `banks` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `code` VARCHAR(16) UNIQUE NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `short_name` VARCHAR(32) NOT NULL,
  `en_name` VARCHAR(64) DEFAULT NULL,
  `type` ENUM('state_owned','joint_stock','internet','policy','city_commercial') NOT NULL,
  `logo_url` VARCHAR(255) DEFAULT NULL,
  `short_desc` VARCHAR(255) DEFAULT NULL,
  `description` TEXT,
  `features` JSON DEFAULT NULL,
  `slogan` VARCHAR(128) DEFAULT NULL,
  `brand_color` VARCHAR(16) DEFAULT NULL,
  `enabled` TINYINT DEFAULT 1,
  `sort_order` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_type` (`type`),
  INDEX `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='银行主表';

CREATE TABLE IF NOT EXISTS `bank_form_schemas` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `bank_id` INT NOT NULL,
  `step_no` INT NOT NULL,
  `step_title` VARCHAR(64) NOT NULL,
  `step_subtitle` VARCHAR(128) DEFAULT NULL,
  `step_label` VARCHAR(32) DEFAULT NULL,
  `fields_json` JSON NOT NULL,
  `enabled` TINYINT DEFAULT 1,
  `sort_order` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_bank` (`bank_id`),
  INDEX `idx_step` (`bank_id`, `step_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='银行动态表单';

CREATE TABLE IF NOT EXISTS `bank_products` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `bank_id` INT NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `subtitle` VARCHAR(128) DEFAULT NULL,
  `limit_min` INT DEFAULT 0,
  `limit_max` INT DEFAULT 0,
  `rate_min` DECIMAL(5,2) DEFAULT 0,
  `rate_max` DECIMAL(5,2) DEFAULT 0,
  `pass_score_min` INT DEFAULT 0,
  `pass_score_max` INT DEFAULT 100,
  `features` JSON DEFAULT NULL,
  `requirement` VARCHAR(255) DEFAULT NULL,
  `recommend` TINYINT DEFAULT 0,
  `enabled` TINYINT DEFAULT 1,
  `sort_order` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_bank` (`bank_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='银行产品';

SELECT '===== Migration 0001 完成 =====' AS msg;
