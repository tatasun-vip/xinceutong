-- =============================================================================
-- 信测通 · 数据库初始化 SQL
-- 数据库：MySQL 8.0+，字符集 utf8mb4
-- 注意事项：
--   1. 金额一律用 INT（分）或 DECIMAL（元），不要用 FLOAT
--   2. 评分卡/纠错规则全部走表配置，禁止硬编码
--   3. 所有 ENUM 字段新增值时需用 ALTER TABLE 修改
--   4. 首次部署执行：mysql -uroot -p xincetong < sql/init.sql
--   5. docker-compose 已挂载到 /docker-entrypoint-initdb.d/ 容器自动初始化
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. 用户表
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `openid` VARCHAR(64) UNIQUE NOT NULL COMMENT '微信 openid',
  `unionid` VARCHAR(64) DEFAULT NULL COMMENT '微信 unionid',
  `nickname` VARCHAR(64) DEFAULT NULL,
  `avatar` VARCHAR(255) DEFAULT NULL,
  `role` ENUM('user','promoter','admin') DEFAULT 'user' COMMENT '用户角色',
  `inviter_id` BIGINT DEFAULT NULL COMMENT '邀请人用户ID',
  `promoter_id` BIGINT DEFAULT NULL COMMENT '归属推广员ID',
  `status` TINYINT DEFAULT 1 COMMENT '1=正常 0=封禁',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_openid` (`openid`),
  INDEX `idx_promoter` (`promoter_id`),
  INDEX `idx_inviter` (`inviter_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- -----------------------------------------------------------------------------
-- 2. 测评记录表
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `assessments`;
CREATE TABLE `assessments` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `report_no` VARCHAR(32) UNIQUE NOT NULL COMMENT '报告编号 R+YYYYMMDD+XXXX',
  `user_id` BIGINT NOT NULL,
  `type` ENUM('personal','business') NOT NULL COMMENT '个人贷/企业贷',
  `input_data` JSON NOT NULL COMMENT '用户填写数据（敏感字段加密）',
  `score` INT DEFAULT NULL COMMENT '模拟评分 0-100',
  `level` VARCHAR(4) DEFAULT NULL COMMENT 'A/B/C/D/E',
  `limit_min` INT DEFAULT NULL COMMENT '模拟额度下限（元）',
  `limit_max` INT DEFAULT NULL COMMENT '模拟额度上限（元）',
  `rate_min` DECIMAL(5,2) DEFAULT NULL COMMENT '模拟利率下限（%）',
  `rate_max` DECIMAL(5,2) DEFAULT NULL COMMENT '模拟利率上限（%）',
  `pass_probability` VARCHAR(8) DEFAULT NULL COMMENT '通过概率等级',
  `risk_tags` JSON DEFAULT NULL COMMENT '风险标签',
  `advantages` JSON DEFAULT NULL COMMENT '优势',
  `weak_points` JSON DEFAULT NULL COMMENT '弱点',
  `suggestions` JSON DEFAULT NULL COMMENT '改善建议',
  `products` JSON DEFAULT NULL COMMENT '推荐产品对比',
  `is_paid` TINYINT DEFAULT 0 COMMENT '是否已付费解锁完整报告',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_report_no` (`report_no`),
  INDEX `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='测评记录';

-- -----------------------------------------------------------------------------
-- 3. 推广员表
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `promoters`;
CREATE TABLE `promoters` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT UNIQUE NOT NULL,
  `real_name` VARCHAR(64) DEFAULT NULL,
  `id_card_encrypted` VARCHAR(255) DEFAULT NULL COMMENT '身份证号 AES 加密',
  `org_name` VARCHAR(128) DEFAULT NULL COMMENT '机构/公司名',
  `city` VARCHAR(64) DEFAULT NULL,
  `years` INT DEFAULT 0 COMMENT '从业年限',
  `status` ENUM('pending','approved','rejected','banned') DEFAULT 'pending',
  `commission_rate` DECIMAL(4,2) DEFAULT 0.30 COMMENT '分佣比例 0-1',
  `custom_price` DECIMAL(8,2) DEFAULT 9.99 COMMENT '推广员自定义价格（元）',
  `total_earnings` DECIMAL(12,2) DEFAULT 0 COMMENT '累计收益（元）',
  `balance` DECIMAL(12,2) DEFAULT 0 COMMENT '可提现余额（元）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `approved_at` DATETIME DEFAULT NULL,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推广员';

-- -----------------------------------------------------------------------------
-- 4. 推广链接
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `promoter_links`;
CREATE TABLE `promoter_links` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `promoter_id` BIGINT NOT NULL,
  `code` VARCHAR(16) UNIQUE NOT NULL COMMENT '推广码',
  `clicks` INT DEFAULT 0,
  `assessments` INT DEFAULT 0,
  `payments` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_code` (`code`),
  INDEX `idx_promoter` (`promoter_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推广链接';

-- -----------------------------------------------------------------------------
-- 5. 订单表
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `order_no` VARCHAR(64) UNIQUE NOT NULL COMMENT '订单号 O+时间戳+随机',
  `user_id` BIGINT NOT NULL,
  `assessment_id` BIGINT NOT NULL,
  `promoter_id` BIGINT DEFAULT NULL,
  `amount` DECIMAL(8,2) NOT NULL COMMENT '实付金额',
  `base_price` DECIMAL(8,2) DEFAULT 9.99 COMMENT '基础价格',
  `markup` DECIMAL(8,2) DEFAULT 0 COMMENT '推广员加价',
  `status` ENUM('pending','paid','refunded','failed') DEFAULT 'pending',
  `pay_method` VARCHAR(16) DEFAULT NULL COMMENT 'wechat_jsapi / wechat_h5',
  `transaction_id` VARCHAR(64) DEFAULT NULL COMMENT '微信交易号',
  `paid_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_promoter` (`promoter_id`),
  INDEX `idx_status` (`status`),
  INDEX `idx_assessment` (`assessment_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单';

-- -----------------------------------------------------------------------------
-- 6. 分佣记录
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `commissions`;
CREATE TABLE `commissions` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `order_id` BIGINT NOT NULL,
  `promoter_id` BIGINT NOT NULL,
  `base_commission` DECIMAL(8,2) DEFAULT NULL COMMENT '基础分佣',
  `markup_commission` DECIMAL(8,2) DEFAULT NULL COMMENT '加价分佣',
  `total_commission` DECIMAL(8,2) DEFAULT NULL,
  `platform_income` DECIMAL(8,2) DEFAULT NULL COMMENT '平台收入',
  `status` ENUM('pending','settled','frozen') DEFAULT 'pending',
  `settled_at` DATETIME DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_promoter` (`promoter_id`),
  INDEX `idx_order` (`order_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分佣记录';

-- -----------------------------------------------------------------------------
-- 7. 评分卡配置
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `scorecard_rules`;
CREATE TABLE `scorecard_rules` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `category` VARCHAR(64) DEFAULT NULL COMMENT '基础/职业/收入/资产/征信...',
  `variable` VARCHAR(64) NOT NULL COMMENT '字段名（与 input_data 对应）',
  `option_label` VARCHAR(64) NOT NULL COMMENT '选项文案',
  `score` DECIMAL(6,2) DEFAULT 0 COMMENT '本项得分',
  `type` ENUM('personal','business','both') DEFAULT 'both',
  `is_veto` TINYINT DEFAULT 0 COMMENT '是否一票否决',
  `sort_order` INT DEFAULT 0,
  `enabled` TINYINT DEFAULT 1,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_variable` (`variable`),
  INDEX `idx_type_enabled` (`type`, `enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评分卡规则';

-- -----------------------------------------------------------------------------
-- 8. 纠错规则
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `validation_rules`;
CREATE TABLE `validation_rules` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `rule_name` VARCHAR(64) NOT NULL,
  `condition_json` JSON NOT NULL COMMENT '触发条件 DSL',
  `message` VARCHAR(255) NOT NULL,
  `level` ENUM('info','warning','error') DEFAULT 'warning',
  `enabled` TINYINT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='纠错规则';

-- -----------------------------------------------------------------------------
-- 9. 分享记录
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `shares`;
CREATE TABLE `shares` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `share_code` VARCHAR(16) UNIQUE NOT NULL,
  `clicks` INT DEFAULT 0,
  `new_users` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_code` (`share_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分享记录';

-- -----------------------------------------------------------------------------
-- 10. 免费体验记录
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `free_trials`;
CREATE TABLE `free_trials` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL,
  `sharer_id` BIGINT DEFAULT NULL COMMENT '邀请人用户ID',
  `assessment_id` BIGINT DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_sharer` (`sharer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='免费体验记录';

-- -----------------------------------------------------------------------------
-- 11. 提现申请
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `withdraws`;
CREATE TABLE `withdraws` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `promoter_id` BIGINT NOT NULL,
  `amount` DECIMAL(8,2) NOT NULL,
  `account_info_encrypted` VARCHAR(512) DEFAULT NULL COMMENT '收款账号加密',
  `status` ENUM('pending','approved','rejected','paid') DEFAULT 'pending',
  `reject_reason` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `processed_at` DATETIME DEFAULT NULL,
  INDEX `idx_promoter` (`promoter_id`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='提现申请';

-- -----------------------------------------------------------------------------
-- 12. 操作日志（合规审计）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
  `user_id` BIGINT DEFAULT NULL,
  `role` VARCHAR(16) DEFAULT NULL,
  `action` VARCHAR(64) NOT NULL COMMENT '操作类型',
  `target` VARCHAR(128) DEFAULT NULL COMMENT '操作对象',
  `ip` VARCHAR(45) DEFAULT NULL,
  `ua` VARCHAR(255) DEFAULT NULL,
  `detail` JSON DEFAULT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_user` (`user_id`),
  INDEX `idx_action` (`action`),
  INDEX `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审计日志';

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================================================
-- 初始管理员账号（密码 admin123，生产请立刻改掉）
-- =============================================================================
-- INSERT INTO users (openid, role, nickname) VALUES ('admin_openid_placeholder', 'admin', '平台管理员');

-- =============================================================================
-- 13. 银行主表（10 家起步，作为方法论/推广素材的支撑数据）
-- =============================================================================
DROP TABLE IF EXISTS `banks`;
CREATE TABLE `banks` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `code` VARCHAR(16) UNIQUE NOT NULL COMMENT '业务编码 ICBC/CCB/CMB/...',
  `name` VARCHAR(64) NOT NULL COMMENT '中文名',
  `short_name` VARCHAR(32) NOT NULL COMMENT '简称',
  `en_name` VARCHAR(64) DEFAULT NULL,
  `type` ENUM('state_owned','joint_stock','internet','policy','city_commercial') NOT NULL,
  `logo_url` VARCHAR(255) DEFAULT NULL,
  `short_desc` VARCHAR(255) DEFAULT NULL,
  `description` TEXT,
  `features` JSON DEFAULT NULL COMMENT '特点标签',
  `slogan` VARCHAR(128) DEFAULT NULL,
  `brand_color` VARCHAR(16) DEFAULT NULL,
  `enabled` TINYINT DEFAULT 1,
  `sort_order` INT DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_type` (`type`),
  INDEX `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='银行主表';

-- -----------------------------------------------------------------------------
-- 14. 银行动态表单 schema（每家银行每步 1 条）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `bank_form_schemas`;
CREATE TABLE `bank_form_schemas` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `bank_id` INT NOT NULL,
  `step_no` INT NOT NULL COMMENT '1~5',
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

-- -----------------------------------------------------------------------------
-- 15. 银行推荐产品
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `bank_products`;
CREATE TABLE `bank_products` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `bank_id` INT NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  `subtitle` VARCHAR(128) DEFAULT NULL,
  `limit_min` INT DEFAULT 0 COMMENT '万元',
  `limit_max` INT DEFAULT 0 COMMENT '万元',
  `rate_min` DECIMAL(5,2) DEFAULT 0 COMMENT '年化%',
  `rate_max` DECIMAL(5,2) DEFAULT 0 COMMENT '年化%',
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

-- =============================================================================
-- 16. 6 大产品类型配置（核心：按产品类型独立建模）
-- =============================================================================
DROP TABLE IF EXISTS `product_types`;
CREATE TABLE `product_types` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `code` VARCHAR(32) UNIQUE NOT NULL COMMENT '业务编码 quality_unit/housing_fund/salary/house_owner/tax/invoice',
  `name` VARCHAR(64) NOT NULL COMMENT '中文名',
  `subtitle` VARCHAR(128) DEFAULT NULL COMMENT '副标题',
  `user_type` ENUM('personal','business') NOT NULL,
  `limit_formula` VARCHAR(64) NOT NULL COMMENT '额度公式 key（评分引擎中匹配）',
  `rate_min` DECIMAL(5,2) NOT NULL COMMENT '利率下限 年化%',
  `rate_max` DECIMAL(5,2) NOT NULL COMMENT '利率上限 年化%',
  `default_pass` VARCHAR(8) DEFAULT '中' COMMENT '默认通过概率',
  `focus_vars` JSON DEFAULT NULL COMMENT '重点考察变量数组',
  `key_points` JSON DEFAULT NULL COMMENT '关键考察点（文案数组）',
  `description` TEXT COMMENT '产品详细介绍',
  `recommend` INT DEFAULT 0 COMMENT '是否推荐展示',
  `sort_order` INT DEFAULT 0,
  `enabled` TINYINT DEFAULT 1,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_code` (`code`),
  INDEX `idx_user_type` (`user_type`),
  INDEX `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='6 大产品类型配置';

-- =============================================================================
-- 17. 站点配置（数字/文案变量化）
-- =============================================================================
DROP TABLE IF EXISTS `site_config`;
CREATE TABLE `site_config` (
  `id` INT PRIMARY KEY AUTO_INCREMENT,
  `config_key` VARCHAR(64) UNIQUE NOT NULL,
  `config_value` TEXT NOT NULL,
  `config_label` VARCHAR(128) DEFAULT NULL,
  `group_name` VARCHAR(32) DEFAULT 'text' COMMENT 'number/text/compliance',
  `remark` VARCHAR(255) DEFAULT NULL,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站点配置';

-- =============================================================================
-- 18. 改造评分卡规则：加 bank_id + product_type_id 双维度
-- =============================================================================
ALTER TABLE `scorecard_rules`
  ADD COLUMN `bank_id` INT DEFAULT NULL COMMENT '关联银行（NULL=通用）' AFTER `id`,
  ADD COLUMN `product_type_id` INT DEFAULT NULL COMMENT '关联产品类型（NULL=通用）' AFTER `bank_id`,
  ADD INDEX `idx_bank` (`bank_id`),
  ADD INDEX `idx_product` (`product_type_id`);

-- =============================================================================
-- 19. 改造测评记录：加 product_results + paid_at + full_report
-- =============================================================================
ALTER TABLE `assessments`
  ADD COLUMN `product_results` JSON DEFAULT NULL COMMENT '6 大产品独立测算结果' AFTER `products`,
  ADD COLUMN `paid_at` DATETIME DEFAULT NULL COMMENT '付费时间' AFTER `is_paid`,
  ADD COLUMN `full_report` MEDIUMTEXT DEFAULT NULL COMMENT '完整报告 Markdown（付费后生成）' AFTER `paid_at`;

-- =============================================================================
-- 20. 测评记录加 bank_id（兼容旧版按银行测评）
-- =============================================================================
-- assessments 表已无 bank_id 字段（init.sql 没建），加一个保留字段
-- 注意：assessments.id 是 INT 而非 BIGINT，但保留字段保持 INT 即可
-- 此处不重复创建 bank_id，避免与旧字段冲突
