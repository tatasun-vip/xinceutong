"""
初始化 6 大产品类型配置

利率按 2026 年银行实际水平校准（2026-09）：
  - 基准：LPR 1Y=3.00% / 5Y+=3.50%（连续多月不变）
  - 国家消费贷贴息 1 个点延到 2026 年底，国有大行优质客户 2.88% 起步
  - 工行融e借 2026.4 政策 2.8% 起；建行快贷 3.0% 起
  - 经营贷开门红国有大行 2.35% 起，但 2026 中小行"缩量抬价"普遍破 4%
  - 数据来源：央行 LPR、银行官网产品页、第三方调研（融 360/卡牛等）

每个产品定义：
  - code / name / subtitle / user_type
  - limit_formula（评分引擎中按 key 匹配具体函数）
  - rate_min / rate_max（年化 %）
  - focus_vars（重点考察变量）
  - key_points（关键考察点文案，报告详情页用）
  - description（产品页大段介绍）

用法：
  docker compose exec api python scripts/init_product_types.py
  或本地：PYTHONPATH=. python -m scripts.init_product_types
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models.product_type import ProductType
from app.utils.logger import logger


PRODUCT_TYPES_SEED: list[dict] = [
    # ============ 1. 优质单位贷 ============
    # 利率：工行融e借 2026.4 2.8% 起；建行快贷针对公务员 2.88% 起步
    # 上限：消费贷贴息 1 个点后多在 4.5% 上下；非贴息产品上限约 4.5-5%
    {
        "code": "quality_unit",
        "name": "优质单位贷",
        "subtitle": "公务员 / 事业单位 / 国企 / 央企专属",
        "user_type": "personal",
        "limit_formula": "quality_unit_income",
        "rate_min": 2.88,
        "rate_max": 4.50,
        "default_pass": "高",
        "focus_vars": ["company_type", "work_years", "monthly_income"],
        "key_points": [
            "单位性质（公务员/事业单位/国企/央企/上市公司）",
            "工龄与现单位连续工作年限",
            "收入稳定性（月收入 + 代发 + 社保）",
            "近 2 年无逾期记录",
            "信用卡使用率（建议 < 50%）",
        ],
        "description": (
            "适合：公务员、事业单位、国企、央企员工\n"
            "考察重点：单位性质、工龄、收入稳定性\n"
            "额度逻辑：月收入 × 30-36 倍\n"
            "参考偏好：审批稳定，利率较低"
        ),
        "recommend": 1,
        "sort_order": 1,
    },
    # ============ 2. 公积金贷 ============
    # 利率：公积金优质客户 2.88% 起（贴息），普通连续缴存 3.0-4.5%
    # 上限：单家银行最高一般不超过 4.8%（部分股份制银行稍高）
    {
        "code": "housing_fund",
        "name": "公积金贷",
        "subtitle": "公积金连续缴纳用户的稳定之选",
        "user_type": "personal",
        "limit_formula": "housing_fund_mult",
        "rate_min": 2.88,
        "rate_max": 4.80,
        "default_pass": "高",
        "focus_vars": ["housing_fund", "company_type", "credit_card_usage", "work_years"],
        "key_points": [
            "公积金连续缴纳时长（≥ 1 年更优）",
            "公积金月缴额（基数越高额度越高）",
            "单位性质（优质单位更易通过）",
            "信用卡使用率（< 50%）",
            "近 3 个月贷款申请次数（少更优）",
        ],
        "description": (
            "适合：连续缴纳公积金的工薪族\n"
            "考察重点：公积金缴纳时长、月缴额\n"
            "额度逻辑：月缴额 × 150-300 倍\n"
            "参考偏好：看重稳定性，容忍查询次数"
        ),
        "recommend": 1,
        "sort_order": 2,
    },
    # ============ 3. 工薪贷 ============
    # 利率：普通工薪族 3.0% 起步（贴息）；普通民营/外企员工上限可达 7.5%
    # 区间较宽因工薪族质量参差：稳定代发 < 6 月 / 工作年限 < 1 年会大幅上浮
    {
        "code": "salary",
        "name": "工薪贷",
        "subtitle": "有社保 / 代发工资的上班族首选",
        "user_type": "personal",
        "limit_formula": "salary_income",
        "rate_min": 3.00,
        "rate_max": 7.50,
        "default_pass": "中高",
        "focus_vars": ["social_security", "payroll", "company_type", "work_years", "monthly_income"],
        "key_points": [
            "社保连续缴纳时长",
            "代发工资记录（≥ 6 个月）",
            "单位类型（民营/外企亦可）",
            "工作年限（≥ 1 年）",
            "月收入水平",
        ],
        "description": (
            "适合：有社保、有代发工资的上班族\n"
            "考察重点：社保时长、单位类型、收入\n"
            "额度逻辑：月收入 × 18-24 倍\n"
            "参考偏好：审批灵活，覆盖人群广"
        ),
        "recommend": 0,
        "sort_order": 3,
    },
    # ============ 4. 有房客户贷 ============
    # 利率：房产作隐性增信，国有大行信用贷 2.88% 起步
    # 上限：纯信用（无抵押）有房客户多在 4.5-4.8%；含抵押可至 3.5% 以下
    {
        "code": "house_owner",
        "name": "有房客户贷",
        "subtitle": "名下有房产，额度高 / 利率有优势",
        "user_type": "personal",
        "limit_formula": "house_asset",
        "rate_min": 2.88,
        "rate_max": 4.80,
        "default_pass": "中高",
        "focus_vars": ["house", "deposit", "car", "monthly_income", "loan_count"],
        "key_points": [
            "房产评估价值",
            "按揭余额（无按揭更优）",
            "资产状况（存款 / 车辆 / 保险）",
            "月收入（决定 DSR 偿债比）",
            "现有贷款笔数（建议 < 3 笔）",
        ],
        "description": (
            "适合：名下有房产的客户\n"
            "考察重点：房产价值、按揭余额、资产\n"
            "额度逻辑：房产评估价 × 成数 - 负债\n"
            "参考偏好：额度高，利率有优势"
        ),
        "recommend": 0,
        "sort_order": 4,
    },
    # ============ 5. 纳税贷 ============
    # 利率：经营贷开门红国有大行 2.35% 起；A/B 级纳税户 2.85% 起步
    # 上限：2026 中小行缩量抬价后部分超 4%，但主流仍 ≤ 4.5%
    {
        "code": "tax",
        "name": "纳税贷",
        "subtitle": "正常纳税小微企业经营贷",
        "user_type": "business",
        "limit_formula": "tax_mult",
        "rate_min": 2.85,
        "rate_max": 4.50,
        "default_pass": "中",
        "focus_vars": ["tax_grade", "annual_tax", "tax_continuity", "business_years"],
        "key_points": [
            "企业纳税等级（A/B/M 级更优）",
            "年纳税额（连续 2 年）",
            "纳税连续性（无断缴）",
            "企业经营年限（≥ 2 年）",
            "法人征信（无重大逾期）",
        ],
        "description": (
            "适合：正常纳税的小微企业\n"
            "考察重点：纳税等级、年纳税额、连续性\n"
            "额度逻辑：年纳税额 × 5-15 倍\n"
            "参考偏好：看重经营稳定性"
        ),
        "recommend": 0,
        "sort_order": 5,
    },
    # ============ 6. 开票贷 ============
    # 利率：国有大行开票贷 3.5% 起步；行业/开票连续性差会大幅上浮
    # 上限：限制类行业或连续性差可达 9%（部分小行更高）
    {
        "code": "invoice",
        "name": "开票贷",
        "subtitle": "稳定开票记录企业的现金流之选",
        "user_type": "business",
        "limit_formula": "invoice_pct",
        "rate_min": 3.50,
        "rate_max": 9.00,
        "default_pass": "中",
        "focus_vars": ["annual_invoice", "industry", "business_years", "invoice_continuity"],
        "key_points": [
            "年开票额（近 12 个月）",
            "行业属性（非限制类行业）",
            "企业经营年限（≥ 1 年）",
            "开票连续性（无长期断票）",
            "企业征信（无重大异常）",
        ],
        "description": (
            "适合：有稳定开票记录的企业\n"
            "考察重点：年开票额、行业属性、流水\n"
            "额度逻辑：年开票额 × 5%-15%\n"
            "参考偏好：看重经营流水与行业"
        ),
        "recommend": 0,
        "sort_order": 6,
    },
]


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        # 清理后写入最新版本
        from sqlalchemy import delete
        existing = (await session.execute(select(ProductType))).scalars().first()
        if existing:
            logger.info("product_types 已存在，先清空再写入")
            await session.execute(delete(ProductType))
            await session.commit()

        for cfg in PRODUCT_TYPES_SEED:
            session.add(ProductType(**cfg))
        await session.commit()
        logger.info(f"写入 6 大产品类型 {len(PRODUCT_TYPES_SEED)} 条")

        logger.info("===== 6 大产品类型初始化完成 =====")
        for cfg in PRODUCT_TYPES_SEED:
            logger.info(f"  {cfg['sort_order']}. {cfg['name']}  利率 {cfg['rate_min']}-{cfg['rate_max']}%  公式 {cfg['limit_formula']}")


if __name__ == "__main__":
    asyncio.run(main())
