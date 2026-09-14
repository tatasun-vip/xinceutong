"""
初始化站点配置（数字/文案变量化）

所有页面/组件中需要运营调整的数字和文案（如 128,000+、50+、9.99）
都从这里读，运营改 DB 即可全站生效。

按 group_name 分类：
  - number: 数字（如 site.user_count）
  - text: 文案（如 site.brand_slogan）
  - compliance: 合规（如 site.disclaimer_short）

用法：
  docker compose exec api python scripts/init_site_config.py
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_db
from app.models.site_config import SiteConfig
from app.utils.logger import logger


SITE_CONFIG_SEED: list[dict] = [
    # ============ 数字（占位数字，上线后替换真实数据）============
    {
        "config_key": "site.user_count",
        "config_value": "128000",
        "config_label": "已服务用户数",
        "group_name": "number",
        "remark": "首页/方法论/信任区展示，已服务用户数（占位数字）",
    },
    {
        "config_key": "site.test_count",
        "config_value": "356000",
        "config_label": "累计模拟测评次数",
        "group_name": "number",
        "remark": "首页数据背书条",
    },
    {
        "config_key": "site.case_count",
        "config_value": "0",
        "config_label": "真实案例回测数（设为 0 时前端隐藏该项，避免与「模拟评审」表述冲突）",
        "group_name": "number",
        "remark": "首页/方法论/报告底部专业说明",
    },
    {
        "config_key": "site.expert_count",
        "config_value": "0",
        "config_label": "业内专家数（设为 0 时前端隐藏「由 N 位资深金融分析师」表述，避免无依据背书）",
        "group_name": "number",
        "remark": "首页/方法论/推广文案",
    },
    {
        "config_key": "site.satisfaction",
        "config_value": "96.3",
        "config_label": "报告满意度 (%)",
        "group_name": "number",
        "remark": "首页/信任区",
    },
    {
        "config_key": "site.product_count",
        "config_value": "6",
        "config_label": "覆盖产品类型数",
        "group_name": "number",
        "remark": "信任区/方法论",
    },
    {
        "config_key": "pay.price",
        "config_value": "9.99",
        "config_label": "报告解锁价格 (元)",
        "group_name": "number",
        "remark": "付费页/启动页/分享海报",
    },
    {
        "config_key": "site.bank_mentioned",
        "config_value": "10",
        "config_label": "提及银行数（方法论页背景）",
        "group_name": "number",
        "remark": "方法论页『参考银行审批框架』的具体数字",
    },
    # ============ 文案 ============
    {
        "config_key": "site.brand_name",
        "config_value": "信测通",
        "config_label": "品牌名",
        "group_name": "text",
    },
    {
        "config_key": "site.brand_slogan",
        "config_value": "别再用征信试错",
        "config_label": "主标题（首页 hero）",
        "group_name": "text",
    },
    {
        "config_key": "site.brand_subtitle",
        "config_value": "一次模拟测评，看清你在不同产品下的可贷资质",
        "config_label": "副标题（首页 hero）",
        "group_name": "text",
    },
    {
        "config_key": "site.brand_tagline",
        "config_value": "信用贷模拟评审系统",
        "config_label": "品牌 tagline",
        "group_name": "text",
    },
    {
        "config_key": "site.brand_one_liner",
        "config_value": "信测通 · 不查征信的信用贷模拟评审系统 · 一次输入，6 大产品独立测算 · 先看清资质，再决定申请",
        "config_label": "一句话总结（启动页/分享海报）",
        "group_name": "text",
    },
    {
        "config_key": "site.cta_personal",
        "config_value": "开始模拟测评（个人）",
        "config_label": "首页 CTA 按钮 1",
        "group_name": "text",
    },
    {
        "config_key": "site.cta_business",
        "config_value": "开始模拟测评（企业）",
        "config_label": "首页 CTA 按钮 2",
        "group_name": "text",
    },
    # ============ 合规 ============
    {
        "config_key": "site.disclaimer_short",
        "config_value": "本工具为模拟测评，不查询您的征信，不构成贷款承诺。",
        "config_label": "顶部合规（短）",
        "group_name": "compliance",
    },
    {
        "config_key": "site.disclaimer_long",
        "config_value": (
            "本报告为模拟测评结果，不构成贷款承诺。"
            "实际审批结果以金融机构正式审批为准。"
            "本平台不参与任何贷款发放、不收取贷款中介费、不承诺审批通过。"
        ),
        "config_label": "底部合规（长）",
        "group_name": "compliance",
    },
    {
        "config_key": "site.disclaimer_full_report",
        "config_value": (
            "本报告由信测通模拟评审模型生成。"
            "模型逻辑参考银行信用贷审批框架（A 卡 / B 卡 / 反欺诈层），"
            "额度、利率、综合通过率按真实业务区间测算，"
            "但本平台不查征信、不接入任何银行系统、不收集您的真实数据。\n"
            "本报告基于您主动填写的信息进行模拟分析，"
            "所有评分、额度、利率、通过概率均为模拟计算结果，"
            "不代表任何银行或金融机构的真实授信，"
            "不构成贷款承诺、投资建议或法律意见。\n"
            "本报告中的额度已按银保监 2020/7《关于加强商业银行互联网贷款业务管理》"
            "及商业银行自营消费贷行业惯例限高：互联网消费贷单户 ≤ 30 万，"
            "线下消费贷单户 ≤ 100 万，公积金贷单户 ≤ 120 万，"
            "小微企业税贷/开票贷 ≤ 500 万，房抵贷 ≤ 1000 万。\n"
            "实际审批结果受银行政策、市场环境、个人资质等多因素影响，"
            "可能与模拟结果存在差异。\n"
            "请勿将本报告作为贷款申请的唯一依据。"
        ),
        "config_label": "报告页底部专业说明（最全）",
        "group_name": "compliance",
    },
    {
        "config_key": "site.disclaimer_pay",
        "config_value": "虚拟服务，一经解锁，原则上不退款。",
        "config_label": "付费页底部",
        "group_name": "compliance",
    },
]


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        existing = (await session.execute(select(SiteConfig))).scalars().first()
        if existing:
            logger.info("site_config 已存在，先清空再写入")
            await session.execute(delete(SiteConfig))
            await session.commit()

        for cfg in SITE_CONFIG_SEED:
            session.add(SiteConfig(**cfg))
        await session.commit()
        logger.info(f"写入站点配置 {len(SITE_CONFIG_SEED)} 条")

        # 按 group 分组打印
        groups: dict[str, int] = {}
        for cfg in SITE_CONFIG_SEED:
            g = cfg["group_name"]
            groups[g] = groups.get(g, 0) + 1
        logger.info("===== 站点配置初始化完成 =====")
        for g, n in groups.items():
            logger.info(f"  {g}: {n} 条")


if __name__ == "__main__":
    asyncio.run(main())
