"""
初始化评分卡规则 + 纠错规则到数据库

评分卡模型：满分 ≈ 200 分（按类别粗估），归一化到 0~100
v3 升级（2026-09-10）：每条规则加 product_type_id 字段
  - product_type_id = NULL：通用规则（所有产品都适用，6 套独立模型共用）
  - product_type_id = X：该产品专属规则（仅对 X 产品生效，覆盖通用规则）

8 个核心原则：
  1. 评分规则全走 scorecard_rules 表（不硬编码）
  2. 一票否决单独判断，不进入评分
  3. 4 种额度测算方法取最小值（v3 改成按 product_type 选公式）
  4. 通过概率基于 PD 违约概率映射
  5. 接口返回统一 {code, message, data} 格式
  6. AES 加密身份证号（见 security.py，阶段 6 完善）
  7. 金额用 INT（分）或 DECIMAL（元）
  8. 推广员价格区间 6.99 ~ 19.99，分佣事务保证

用法：
  docker compose exec api python scripts/init_scorecard.py
  或本地：python -m scripts.init_scorecard
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal, engine, init_db
from app.models.scorecard import ScorecardRule, ValidationRule
from app.utils.logger import logger


# ============================================================================
# 评分卡规则
# 字段：(category, variable, option_label, score, type, is_veto, sort_order, product_type_id)
# ============================================================================
# 总分（满分粗估）：
#   基础 ~22 + 职业 ~52 + 收入 ~30 + 资产 ~40 + 征信 ~50 = ~194
# 归一化到 0~100：对半映射（score / 2）
# 通用规则（product_type_id=None）对所有 6 大产品都适用
# 注：额度公式 + 利率区间在 product_types 表中按 product_type_id 配置


SCORECARD_SEED: list[tuple[str, str, str, float, str, int, int, int | None]] = [
    # ============ 基础（22 分，通用规则）============
    # 注：product_type_id = None = 通用规则，对所有 6 大产品都适用
    # 注：额度公式 + 利率区间在 product_types 表中按 product_type_id 配置
    ("基础", "age", "22-30岁", 8, "personal", 0, 1, None),
    ("基础", "age", "31-40岁", 10, "personal", 0, 2, None),
    ("基础", "age", "41-50岁", 6, "personal", 0, 3, None),
    ("基础", "age", "51-55岁", 3, "personal", 0, 4, None),
    # 一票否决
    ("基础", "age", "18岁以下", 0, "personal", 1, 5, None),
    ("基础", "age", "55岁以上", 0, "personal", 1, 6, None),

    ("基础", "education", "本科及以上", 4, "personal", 0, 10, None),
    ("基础", "education", "大专", 3, "personal", 0, 11, None),
    ("基础", "education", "高中/中专", 1, "personal", 0, 12, None),
    ("基础", "education", "初中及以下", 0, "personal", 0, 13, None),

    ("基础", "marriage", "已婚有子女", 3, "personal", 0, 20, None),
    ("基础", "marriage", "已婚无子女", 2, "personal", 0, 21, None),
    ("基础", "marriage", "未婚", 1, "personal", 0, 22, None),
    ("基础", "marriage", "离异", 0, "personal", 0, 23, None),

    ("基础", "city_tier", "一线城市", 3, "personal", 0, 30, None),
    ("基础", "city_tier", "新一线/省会", 2, "personal", 0, 31, None),
    ("基础", "city_tier", "其他城市", 1, "personal", 0, 32, None),

    # ============ 职业（52 分，通用规则）============
    ("职业", "company_type", "公务员/事业单位", 15, "personal", 0, 40, None),
    ("职业", "company_type", "国企/央企", 13, "personal", 0, 41, None),
    ("职业", "company_type", "上市公司", 10, "personal", 0, 42, None),
    ("职业", "company_type", "民营/外企", 6, "personal", 0, 43, None),
    ("职业", "company_type", "个体户/小微企业", 3, "personal", 0, 44, None),
    ("职业", "company_type", "自由职业", 1, "personal", 0, 45, None),

    ("职业", "work_years", "5年以上", 10, "personal", 0, 50, None),
    ("职业", "work_years", "3-5年", 7, "personal", 0, 51, None),
    ("职业", "work_years", "1-3年", 4, "personal", 0, 52, None),
    ("职业", "work_years", "1年以下", 1, "personal", 0, 53, None),

    ("职业", "social_security", "连续3年以上", 8, "personal", 0, 60, None),
    ("职业", "social_security", "连续1-3年", 5, "personal", 0, 61, None),
    ("职业", "social_security", "1年以下", 2, "personal", 0, 62, None),
    ("职业", "social_security", "无", 0, "personal", 0, 63, None),

    ("职业", "housing_fund", "高基数", 8, "personal", 0, 70, None),
    ("职业", "housing_fund", "正常基数", 5, "personal", 0, 71, None),
    ("职业", "housing_fund", "最低基数", 2, "personal", 0, 72, None),
    ("职业", "housing_fund", "无", 0, "personal", 0, 73, None),

    ("职业", "payroll", "是", 6, "personal", 0, 80, None),
    ("职业", "payroll", "否", 0, "personal", 0, 81, None),

    # ============ 收入（30 分，通用规则）============
    ("收入", "monthly_income", "5万以上", 30, "personal", 0, 90, None),
    ("收入", "monthly_income", "3万-5万", 22, "personal", 0, 91, None),
    ("收入", "monthly_income", "1.5万-3万", 15, "personal", 0, 92, None),
    ("收入", "monthly_income", "8000-1.5万", 8, "personal", 0, 93, None),
    ("收入", "monthly_income", "5000-8000", 3, "personal", 0, 94, None),
    ("收入", "monthly_income", "5000以下", 0, "personal", 0, 95, None),

    # ============ 资产（40 分，通用规则）============
    ("资产", "house", "无按揭", 18, "personal", 0, 100, None),
    ("资产", "house", "有按揭", 8, "personal", 0, 101, None),
    ("资产", "house", "无房", 0, "personal", 0, 102, None),

    ("资产", "car", "30万以上", 10, "personal", 0, 110, None),
    ("资产", "car", "10-30万", 6, "personal", 0, 111, None),
    ("资产", "car", "10万以下", 2, "personal", 0, 112, None),
    ("资产", "car", "无车", 0, "personal", 0, 113, None),

    ("资产", "deposit", "50万以上", 8, "personal", 0, 120, None),
    ("资产", "deposit", "10-50万", 5, "personal", 0, 121, None),
    ("资产", "deposit", "10万以下", 2, "personal", 0, 122, None),
    ("资产", "deposit", "无", 0, "personal", 0, 123, None),

    ("资产", "insurance", "有", 4, "personal", 0, 130, None),
    ("资产", "insurance", "无", 0, "personal", 0, 131, None),

    # ============ 征信（50 分，通用规则）============
    ("征信", "credit_card_count", "无", 4, "personal", 0, 140, None),
    ("征信", "credit_card_count", "1-3张", 6, "personal", 0, 141, None),
    ("征信", "credit_card_count", "3-5张", 4, "personal", 0, 142, None),
    ("征信", "credit_card_count", "5张以上", 1, "personal", 0, 143, None),

    ("征信", "credit_card_usage", "30%以下", 8, "personal", 0, 150, None),
    ("征信", "credit_card_usage", "30%-50%", 6, "personal", 0, 151, None),
    ("征信", "credit_card_usage", "50%-80%", 3, "personal", 0, 152, None),
    ("征信", "credit_card_usage", "80%以上", 0, "personal", 0, 153, None),

    ("征信", "loan_count", "无", 6, "personal", 0, 160, None),
    ("征信", "loan_count", "1-2笔", 4, "personal", 0, 161, None),
    ("征信", "loan_count", "3-5笔", 1, "personal", 0, 162, None),
    ("征信", "loan_count", "5笔以上", 0, "personal", 0, 163, None),

    ("征信", "recent_3month_queries", "0-2次", 5, "personal", 0, 170, None),
    ("征信", "recent_3month_queries", "3-5次", 2, "personal", 0, 171, None),
    ("征信", "recent_3month_queries", "6次以上", 0, "personal", 0, 172, None),

    ("征信", "overdue_2year", "0次", 10, "personal", 0, 180, None),
    ("征信", "overdue_2year", "1-3次", 4, "personal", 0, 181, None),
    ("征信", "overdue_2year", "3次以上", 0, "personal", 0, 182, None),

    # 一票否决（对所有产品生效）
    ("征信", "current_overdue", "有", 0, "personal", 1, 190, None),
    ("征信", "current_overdue", "无", 0, "personal", 0, 191, None),
    ("征信", "serial_overdue", "有", 0, "personal", 1, 200, None),
    ("征信", "serial_overdue", "无", 0, "personal", 0, 201, None),
    ("征信", "white_account", "是", 0, "personal", 0, 210, None),
    ("征信", "white_account", "否", 0, "personal", 0, 211, None),
    ("征信", "bad_status", "有", 0, "personal", 1, 220, None),
    ("征信", "bad_status", "无", 0, "personal", 0, 221, None),

    # ============ 产品专属规则（product_type_id = 1~6）============
    # 优质单位贷（id=1）：单位性质权重 ×1.5（专属规则覆盖通用规则）
    ("职业", "company_type", "公务员/事业单位", 25, "personal", 0, 40, 1),
    ("职业", "company_type", "国企/央企", 22, "personal", 0, 41, 1),
    ("职业", "company_type", "上市公司", 18, "personal", 0, 42, 1),

    # 公积金贷（id=2）：公积金规则权重 ×1.5
    ("职业", "housing_fund", "高基数", 12, "personal", 0, 70, 2),
    ("职业", "housing_fund", "正常基数", 8, "personal", 0, 71, 2),

    # 工薪贷（id=3）：社保+代发权重 ×1.5
    ("职业", "social_security", "连续3年以上", 12, "personal", 0, 60, 3),
    ("职业", "social_security", "连续1-3年", 8, "personal", 0, 61, 3),
    ("职业", "payroll", "是", 10, "personal", 0, 80, 3),

    # 有房客户贷（id=4）：房产+存款权重 ×1.5
    ("资产", "house", "无按揭", 28, "personal", 0, 100, 4),
    ("资产", "house", "有按揭", 14, "personal", 0, 101, 4),
    ("资产", "deposit", "50万以上", 12, "personal", 0, 120, 4),
    ("资产", "deposit", "10-50万", 8, "personal", 0, 121, 4),
]


# ============================================================================
# 纠错规则（实时校验）
# 字段：rule_name, condition_json, message, level
# condition_json DSL 详见 app/utils/condition_dsl.py
# ============================================================================


VALIDATION_SEED: list[dict] = [
    {
        "rule_name": "近3个月查询过多",
        "condition_json": {"op": "in", "variable": "recent_3month_queries", "value": ["6次以上"]},
        "message": "近3个月查询超过6次，建议暂缓3-6个月再申请",
        "level": "warning",
    },
    {
        "rule_name": "当前逾期警告",
        "condition_json": {"op": "eq", "variable": "current_overdue", "value": "有"},
        "message": "当前存在逾期记录，几乎无法通过任何审批",
        "level": "error",
    },
    {
        "rule_name": "连续逾期警告",
        "condition_json": {"op": "eq", "variable": "serial_overdue", "value": "有"},
        "message": "存在连续逾期，会被多数银行直接拒绝",
        "level": "error",
    },
    {
        "rule_name": "账户状态异常",
        "condition_json": {"op": "eq", "variable": "bad_status", "value": "有"},
        "message": "存在次级/可疑/损失账户，几乎无法获得贷款",
        "level": "error",
    },
    {
        "rule_name": "信用卡使用率过高",
        "condition_json": {"op": "in", "variable": "credit_card_usage", "value": ["80%以上"]},
        "message": "信用卡使用率超过80%，建议先还款降低使用率",
        "level": "warning",
    },
    {
        "rule_name": "近2年多次逾期",
        "condition_json": {"op": "in", "variable": "overdue_2year", "value": ["3次以上"]},
        "message": "近2年逾期超过3次，会显著降低通过率",
        "level": "warning",
    },
    {
        "rule_name": "年龄不达标",
        "condition_json": {"op": "in", "variable": "age", "value": ["18岁以下", "55岁以上"]},
        "message": "年龄不符合多数银行准入条件（22-55岁）",
        "level": "error",
    },
    {
        "rule_name": "白户风险",
        "condition_json": {"op": "eq", "variable": "white_account", "value": "是"},
        "message": "无任何信贷记录（白户），建议先申请 1 张信用卡建立信用",
        "level": "info",
    },
    {
        "rule_name": "收入过低",
        "condition_json": {"op": "in", "variable": "monthly_income", "value": ["5000以下"]},
        "message": "月收入低于5000元，多数银行无法通过",
        "level": "warning",
    },
    {
        "rule_name": "工作年限过短",
        "condition_json": {"op": "in", "variable": "work_years", "value": ["1年以下"]},
        "message": "工作年限不足1年，建议稳定工作后再申请",
        "level": "info",
    },
    {
        "rule_name": "在贷笔数过多",
        "condition_json": {"op": "in", "variable": "loan_count", "value": ["5笔以上"]},
        "message": "在贷笔数超过5笔，负债率可能过高",
        "level": "warning",
    },
    {
        "rule_name": "优质客户确认",
        "condition_json": {
            "op": "and",
            "children": [
                {"op": "in", "variable": "company_type", "value": ["公务员/事业单位", "国企/央企"]},
                {"op": "in", "variable": "monthly_income", "value": ["1.5万-3万", "3万-5万", "5万以上"]},
                {"op": "eq", "variable": "current_overdue", "value": "无"},
            ],
        },
        "message": "您属于优质客户群体，建议优先申请公积金 / 工资代发银行的低息产品",
        "level": "info",
    },
]


# ============================================================================
# 主入口
# ============================================================================


async def _sqlite_migrate() -> None:
    """SQLite 模式：旧表缺新加的列时，自动 ALTER TABLE 补齐"""
    from sqlalchemy import text
    from app.config import settings
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    async with engine.begin() as conn:
        # 检查 scorecard_rules 表是否已有 product_type_id
        try:
            r = await conn.execute(text("PRAGMA table_info(scorecard_rules)"))
            cols = {row[1] for row in r.fetchall()}
        except Exception:
            cols = set()
        if "product_type_id" not in cols:
            await conn.execute(text("ALTER TABLE scorecard_rules ADD COLUMN product_type_id INT DEFAULT NULL"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_score_product ON scorecard_rules(product_type_id)"))
            logger.info("SQLite 迁移：scorecard_rules.product_type_id 已加")
        # assessments 表新增 product_results / paid_at / full_report
        try:
            r = await conn.execute(text("PRAGMA table_info(assessments)"))
            acols = {row[1] for row in r.fetchall()}
        except Exception:
            acols = set()
        if "product_results" not in acols:
            await conn.execute(text("ALTER TABLE assessments ADD COLUMN product_results TEXT DEFAULT NULL"))
            logger.info("SQLite 迁移：assessments.product_results 已加")
        if "paid_at" not in acols:
            await conn.execute(text("ALTER TABLE assessments ADD COLUMN paid_at DATETIME DEFAULT NULL"))
            logger.info("SQLite 迁移：assessments.paid_at 已加")
        if "full_report" not in acols:
            await conn.execute(text("ALTER TABLE assessments ADD COLUMN full_report TEXT DEFAULT NULL"))
            logger.info("SQLite 迁移：assessments.full_report 已加")


async def main() -> None:
    await _sqlite_migrate()
    await init_db()
    async with AsyncSessionLocal() as session:
        # 1. 评分卡
        existing = (await session.execute(select(ScorecardRule))).scalars().first()
        if existing:
            logger.info("评分卡规则已存在，先清空再写入最新版本")
            from sqlalchemy import delete
            await session.execute(delete(ScorecardRule))
            await session.commit()

        for cat, var, opt, score, typ, veto, sort_order, product_type_id in SCORECARD_SEED:
            session.add(ScorecardRule(
                category=cat,
                variable=var,
                option_label=opt,
                score=score,
                type=typ,
                is_veto=veto,
                sort_order=sort_order,
                product_type_id=product_type_id,
                enabled=1,
            ))
        await session.commit()
        logger.info(f"写入评分卡规则 {len(SCORECARD_SEED)} 条")

        # 2. 纠错规则
        existing = (await session.execute(select(ValidationRule))).scalars().first()
        if existing:
            logger.info("纠错规则已存在，先清空再写入最新版本")
            from sqlalchemy import delete
            await session.execute(delete(ValidationRule))
            await session.commit()

        for r in VALIDATION_SEED:
            session.add(ValidationRule(**r, enabled=1))
        await session.commit()
        logger.info(f"写入纠错规则 {len(VALIDATION_SEED)} 条")

        logger.info("===== 阶段 2 评分卡初始化完成 =====")
        logger.info(f"  评分卡规则: {len(SCORECARD_SEED)} 条")
        logger.info(f"  纠错规则  : {len(VALIDATION_SEED)} 条")
        logger.info(f"  一票否决项: {sum(1 for r in SCORECARD_SEED if r[5] == 1)} 条")


if __name__ == "__main__":
    asyncio.run(main())
