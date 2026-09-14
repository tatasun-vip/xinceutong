"""
Seed 脚本：10 家银行 + 每家 5 步 schema + 每家产品

执行：
  cd xincetong-server
  .venv/bin/python scripts/seed_banks.py
"""
import asyncio
import os
import sys

# 让脚本能 import app.*
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, Base, engine
from app.models import Bank, BankFormSchema, BankProduct  # noqa: F401  注册到 Base.metadata


# ============================================================================
# 10 家银行（覆盖国有大行 / 股份行 / 互联网银行）
# ============================================================================

BANKS = [
    # ---------- 国有大行 ----------
    {
        "code": "ICBC",
        "name": "工商银行",
        "short_name": "工行",
        "en_name": "ICBC",
        "type": "state_owned",
        "logo_url": "/static/banks/icbc.svg",
        "short_desc": "宇宙第一大行，准入严，利率最低",
        "description": "中国工商银行是中国最大的商业银行，对工薪阶层和代发工资客户准入友好。利率在国有大行中最低，但审批严格，对代发工资客户、公积金客户有专项产品。",
        "features": ["代发工资优待", "公积金专项", "利率最低", "审批严格"],
        "slogan": "宇宙行 · 利率最低",
        "brand_color": "#C7000B",
        "sort_order": 1,
    },
    {
        "code": "CCB",
        "name": "建设银行",
        "short_name": "建行",
        "en_name": "CCB",
        "type": "state_owned",
        "logo_url": "/static/banks/ccb.svg",
        "short_desc": "房产抵押贷款首选",
        "description": "建设银行以房贷业务见长，房产抵押贷款利率极具竞争力。快贷系列产品对优质客户非常友好，审批速度在国有大行中最快。",
        "features": ["房产抵押利率低", "快贷速度快", "客户经理响应快"],
        "slogan": "要买房 · 到建行",
        "brand_color": "#004B8D",
        "sort_order": 2,
    },
    {
        "code": "BOC",
        "name": "中国银行",
        "short_name": "中行",
        "en_name": "BOC",
        "type": "state_owned",
        "logo_url": "/static/banks/boc.svg",
        "short_desc": "外汇业务强、外贸企业友好",
        "description": "中国银行在外汇业务和国际贸易领域有传统优势，对外贸企业、高净值客户准入宽松。",
        "features": ["外汇业务强", "外贸企业友好", "海外背景优待"],
        "slogan": "全球银行 · 外汇专家",
        "brand_color": "#B71C1C",
        "sort_order": 3,
    },
    {
        "code": "ABC",
        "name": "农业银行",
        "short_name": "农行",
        "en_name": "ABC",
        "type": "state_owned",
        "logo_url": "/static/banks/abc.svg",
        "short_desc": "下沉市场覆盖最广",
        "description": "农业银行在三线及以下城市覆盖最广，对农户、县域客户、公务员、事业单位职工有专项准入通道。",
        "features": ["下沉市场广", "县域客户优待", "公务员专项"],
        "slogan": "耕耘美丽中国",
        "brand_color": "#00753A",
        "sort_order": 4,
    },
    {
        "code": "BCM",
        "name": "交通银行",
        "short_name": "交行",
        "en_name": "BCM",
        "type": "state_owned",
        "logo_url": "/static/banks/bcm.svg",
        "short_desc": "惠民贷信用贷口碑好",
        "description": "交通银行的惠民贷是市场上口碑最好的纯信用贷款产品之一，对优质单位客户准入宽松，审批快。",
        "features": ["惠民贷口碑好", "审批快", "优质单位友好"],
        "slogan": "惠民贷 · 信用贷首选",
        "brand_color": "#003C8F",
        "sort_order": 5,
    },
    # ---------- 股份制商业银行 ----------
    {
        "code": "CMB",
        "name": "招商银行",
        "short_name": "招行",
        "en_name": "CMB",
        "type": "joint_stock",
        "logo_url": "/static/banks/cmb.svg",
        "short_desc": "零售之王，闪电贷最快",
        "description": "招商银行是中国零售业务最出色的银行，闪电贷对优质客户能实现 3 分钟放款。已有招行卡客户额度通常更优。",
        "features": ["零售之王", "闪电贷 3 分钟", "已有客户额度优"],
        "slogan": "因您而变 · 闪电贷",
        "brand_color": "#A11B1B",
        "sort_order": 6,
    },
    {
        "code": "PAB",
        "name": "平安银行",
        "short_name": "平安",
        "en_name": "PAB",
        "type": "joint_stock",
        "logo_url": "/static/banks/pab.svg",
        "short_desc": "新一贷额度大、利息高",
        "description": "平安银行新一贷在市场上额度上限最高（最高 50 万），但利率也相对较高，对负债率容忍度较高。",
        "features": ["额度上限高", "负债容忍度高", "保险客户优待"],
        "slogan": "新一贷 · 额度高",
        "brand_color": "#E60012",
        "sort_order": 7,
    },
    {
        "code": "XCB",
        "name": "新网银行",
        "short_name": "新网",
        "en_name": "XCB",
        "type": "internet",
        "logo_url": "/static/banks/xcb.svg",
        "short_desc": "互联网银行，门槛低",
        "description": "新网银行是腾讯系互联网银行，准入门槛低、纯线上审批，对没有传统银行流水的客户较友好。",
        "features": ["互联网纯线上", "准入门槛低", "审批快"],
        "slogan": "互联网银行 · 纯线上",
        "brand_color": "#FF6A00",
        "sort_order": 8,
    },
    # ---------- 互联网银行 ----------
    {
        "code": "WEBANK",
        "name": "微众银行",
        "short_name": "微众",
        "en_name": "WeBank",
        "type": "internet",
        "logo_url": "/static/banks/webank.svg",
        "short_desc": "腾讯系微粒贷，扫码即贷",
        "description": "微众银行是腾讯发起的互联网银行，微粒贷是市场上规模最大的纯信用贷款产品，扫码即可申请，按日计息。",
        "features": ["腾讯系", "扫码即贷", "按日计息", "无抵押"],
        "slogan": "微粒贷 · 扫码即贷",
        "brand_color": "#00C250",
        "sort_order": 9,
    },
    {
        "code": "MYBANK",
        "name": "网商银行",
        "short_name": "网商",
        "en_name": "MyBank",
        "type": "internet",
        "logo_url": "/static/banks/mybank.svg",
        "short_desc": "阿里系，小微/电商专属",
        "description": "网商银行是阿里发起的互联网银行，专注小微企业和电商卖家贷款，对淘宝/天猫卖家有专项产品。",
        "features": ["阿里系", "小微专属", "电商卖家专项", "流水贷"],
        "slogan": "网商贷 · 小微专属",
        "brand_color": "#FF6A00",
        "sort_order": 10,
    },
]


# ============================================================================
# 5 步问卷 schema（每家银行可不同，但基础字段一致；差异化字段见各银行配置）
# ============================================================================

def _common_steps(bank_code: str) -> list[dict]:
    """
    5 步基础 schema（所有银行通用骨架）
    银行可在 admin 后台动态修改 fields_json 加特色字段
    """
    return [
        {
            "step_no": 1,
            "step_title": "基础信息",
            "step_subtitle": "请如实填写您的个人基本信息",
            "step_label": "01 / BASIC",
            "sort_order": 1,
            "fields_json": [
                {"key": "age", "label": "年龄", "type": "number", "required": True, "min": 18, "max": 65, "unit": "岁"},
                {"key": "gender", "label": "性别", "type": "radio", "required": True,
                 "options": [{"value": "male", "label": "男"}, {"value": "female", "label": "女"}]},
                {"key": "city_tier", "label": "城市层级", "type": "select", "required": True,
                 "options": [{"value": "t1", "label": "一线城市"}, {"value": "t2", "label": "新一线"}, {"value": "t3", "label": "二线"}, {"value": "t4", "label": "三线及以下"}]},
                {"key": "education", "label": "学历", "type": "select", "required": True,
                 "options": [{"value": "phd", "label": "博士"}, {"value": "master", "label": "硕士"}, {"value": "bachelor", "label": "本科"}, {"value": "college", "label": "大专"}, {"value": "highschool", "label": "高中及以下"}]},
                {"key": "marital", "label": "婚姻状况", "type": "radio", "required": False,
                 "options": [{"value": "single", "label": "未婚"}, {"value": "married", "label": "已婚"}, {"value": "divorced", "label": "离异"}]},
            ],
        },
        {
            "step_no": 2,
            "step_title": "职业情况",
            "step_subtitle": "请填写您的职业与收入信息",
            "step_label": "02 / CAREER",
            "sort_order": 2,
            "fields_json": [
                {"key": "employment", "label": "就业类型", "type": "select", "required": True,
                 "options": [{"value": "civil_servant", "label": "公务员/事业编"}, {"value": "state_enterprise", "label": "国企"}, {"value": "private_employee", "label": "私营企业员工"}, {"value": "foreign_enterprise", "label": "外企"}, {"value": "self_employed", "label": "自雇/个体"}, {"value": "freelancer", "label": "自由职业"}]},
                {"key": "industry", "label": "所在行业", "type": "select", "required": True,
                 "options": [{"value": "finance", "label": "金融"}, {"value": "it", "label": "IT/互联网"}, {"value": "manufacturing", "label": "制造业"}, {"value": "education", "label": "教育"}, {"value": "healthcare", "label": "医疗"}, {"value": "government", "label": "政府机关"}, {"value": "other", "label": "其他"}]},
                {"key": "position", "label": "职位", "type": "select", "required": True,
                 "options": [{"value": "executive", "label": "高管"}, {"value": "manager", "label": "中层管理"}, {"value": "staff", "label": "普通员工"}, {"value": "entry", "label": "应届/初级"}]},
                {"key": "work_years", "label": "工作年限", "type": "number", "required": True, "min": 0, "max": 50, "unit": "年"},
                {"key": "income", "label": "税后月收入", "type": "slider", "required": True, "min": 0, "max": 100000, "step": 1000, "unit": "元"},
                {"key": "social_security", "label": "社保连续缴存月数", "type": "number", "required": True, "min": 0, "max": 600, "unit": "月"},
                {"key": "housing_fund", "label": "是否缴存公积金", "type": "radio", "required": True,
                 "options": [{"value": "yes", "label": "有"}, {"value": "no", "label": "无"}]},
            ],
        },
        {
            "step_no": 3,
            "step_title": "资产情况",
            "step_subtitle": "请填写您的资产与负债信息",
            "step_label": "03 / ASSET",
            "sort_order": 3,
            "fields_json": [
                {"key": "housing", "label": "住房情况", "type": "radio", "required": True,
                 "options": [{"value": "owned", "label": "自有无贷"}, {"value": "owned_mortgage", "label": "自有有按揭"}, {"value": "rent", "label": "租赁"}]},
                {"key": "car", "label": "车辆情况", "type": "radio", "required": True,
                 "options": [{"value": "yes", "label": "有车"}, {"value": "no", "label": "无车"}]},
                {"key": "deposit", "label": "金融资产（存款/理财/基金）", "type": "slider", "required": True, "min": 0, "max": 5000000, "step": 10000, "unit": "元"},
                {"key": "debt", "label": "现有贷款月还款", "type": "slider", "required": True, "min": 0, "max": 100000, "step": 500, "unit": "元"},
            ],
        },
        {
            "step_no": 4,
            "step_title": "征信情况",
            "step_subtitle": "请如实填写您的征信记录",
            "step_label": "04 / CREDIT",
            "sort_order": 4,
            "fields_json": [
                {"key": "overdue", "label": "近 2 年是否逾期", "type": "radio", "required": True,
                 "options": [{"value": "no", "label": "无逾期"}, {"value": "minor", "label": "轻微逾期（已还清）"}, {"value": "serious", "label": "严重逾期"}]},
                {"key": "current_overdue", "label": "当前是否有逾期", "type": "radio", "required": True,
                 "options": [{"value": "no", "label": "无"}, {"value": "yes", "label": "有"}]},
                {"key": "credit_limit", "label": "信用卡总额度", "type": "slider", "required": False, "min": 0, "max": 500000, "step": 5000, "unit": "元"},
                {"key": "utilization", "label": "信用卡使用率", "type": "slider", "required": False, "min": 0, "max": 100, "step": 5, "unit": "%"},
                {"key": "loan_count", "label": "在贷笔数", "type": "number", "required": False, "min": 0, "max": 50, "unit": "笔"},
                {"key": "query_count_3m", "label": "近 3 个月贷款审批查询次数", "type": "number", "required": False, "min": 0, "max": 50, "unit": "次"},
            ],
        },
        {
            "step_no": 5,
            "step_title": "确认提交",
            "step_subtitle": "请确认信息无误后提交测评",
            "step_label": "05 / CONFIRM",
            "sort_order": 5,
            "fields_json": [
                {"key": "agree_disclaimer", "label": "我已阅读并同意《测评免责声明》，本测评结果仅为模拟运算，不查征信、不读取任何银行数据。", "type": "checkbox", "required": True},
            ],
        },
    ]


# 每家银行的特色字段（在基础之上追加）
BANK_FEATURED_FIELDS = {
    "ICBC": [
        # 代发工资专项
        {"step_no": 2, "key": "is_payroll", "label": "是否工行代发工资", "type": "radio", "required": True,
         "options": [{"value": "yes", "label": "是"}, {"value": "no", "label": "否"}]},
    ],
    "CCB": [
        # 房产估值
        {"step_no": 3, "key": "house_value", "label": "房产估值（自有住房）", "type": "slider", "required": False, "min": 0, "max": 30000000, "step": 100000, "unit": "元"},
        {"step_no": 3, "key": "mortgage_balance", "label": "房贷余额", "type": "slider", "required": False, "min": 0, "max": 20000000, "step": 100000, "unit": "元"},
    ],
    "CMB": [
        # 已有招行卡
        {"step_no": 1, "key": "has_cmb_card", "label": "是否已有招行卡", "type": "radio", "required": False,
         "options": [{"value": "yes", "label": "是"}, {"value": "no", "label": "否"}]},
        {"step_no": 4, "key": "cmb_credit_used", "label": "招行信用卡已用额度", "type": "slider", "required": False, "min": 0, "max": 300000, "step": 5000, "unit": "元"},
    ],
    "PAB": [
        # 保险客户
        {"step_no": 2, "key": "is_pingan_insurance", "label": "是否平安保险客户", "type": "radio", "required": False,
         "options": [{"value": "yes", "label": "是"}, {"value": "no", "label": "否"}]},
    ],
    "WEBANK": [
        # 微信支付分
        {"step_no": 4, "key": "wechat_pay_score", "label": "微信支付分", "type": "number", "required": False, "min": 350, "max": 850, "unit": "分"},
    ],
    "MYBANK": [
        # 淘宝店铺
        {"step_no": 2, "key": "is_taobao_seller", "label": "是否淘宝/天猫卖家", "type": "radio", "required": False,
         "options": [{"value": "yes", "label": "是"}, {"value": "no", "label": "否"}]},
        {"step_no": 3, "key": "monthly_sales", "label": "近 12 个月店铺流水", "type": "slider", "required": False, "min": 0, "max": 10000000, "step": 50000, "unit": "元"},
    ],
    "BOC": [
        # 外汇/外贸
        {"step_no": 2, "key": "has_foreign_income", "label": "是否有境外收入", "type": "radio", "required": False,
         "options": [{"value": "yes", "label": "是"}, {"value": "no", "label": "否"}]},
    ],
    "XCB": [
        # 微信/QQ 等级
        {"step_no": 4, "key": "qq_level", "label": "QQ 等级", "type": "number", "required": False, "min": 0, "max": 200, "unit": "级"},
    ],
}


# ============================================================================
# 每家银行的推荐产品
# ============================================================================

BANK_PRODUCTS = {
    "ICBC": [
        {"name": "融 e 借", "subtitle": "工行信用贷旗舰产品", "limit_min": 1, "limit_max": 30, "rate_min": 3.7, "rate_max": 5.6, "pass_score_min": 70, "features": ["利率最低", "代发工资优待"], "requirement": "近 2 年无逾期，公积金连续缴存 6 个月以上", "recommend": 1},
        {"name": "公积金贷", "subtitle": "公积金客户专项", "limit_min": 1, "limit_max": 50, "rate_min": 3.45, "rate_max": 4.5, "pass_score_min": 65, "features": ["公积金专项", "额度高"], "requirement": "公积金连续缴存 12 个月以上", "recommend": 0},
    ],
    "CCB": [
        {"name": "建行快贷", "subtitle": "全线上 3 分钟放款", "limit_min": 1, "limit_max": 20, "rate_min": 3.85, "rate_max": 5.6, "pass_score_min": 65, "features": ["审批快", "线上申请"], "requirement": "建行代发工资客户/有房贷客户优先", "recommend": 1},
        {"name": "房产抵押贷", "subtitle": "房产抵押，利率最低", "limit_min": 10, "limit_max": 500, "rate_min": 3.15, "rate_max": 4.2, "pass_score_min": 55, "features": ["利率最低", "额度高"], "requirement": "有房产可抵押", "recommend": 0},
    ],
    "BOC": [
        {"name": "中银 e 贷", "subtitle": "中行线上信用贷", "limit_min": 1, "limit_max": 20, "rate_min": 3.9, "rate_max": 5.8, "pass_score_min": 65, "features": ["外汇客户优待"], "requirement": "中行代发工资或中行卡客户", "recommend": 1},
    ],
    "ABC": [
        {"name": "网捷贷", "subtitle": "农行线上信用贷", "limit_min": 1, "limit_max": 30, "rate_min": 3.65, "rate_max": 5.5, "pass_score_min": 60, "features": ["公务员专项", "县域友好"], "requirement": "优质单位/公务员/事业编", "recommend": 1},
    ],
    "BCM": [
        {"name": "惠民贷", "subtitle": "交行口碑最好的信用贷", "limit_min": 1, "limit_max": 50, "rate_min": 3.85, "rate_max": 5.4, "pass_score_min": 60, "features": ["口碑好", "审批快"], "requirement": "优质单位客户/代发工资客户", "recommend": 1},
    ],
    "CMB": [
        {"name": "闪电贷", "subtitle": "3 分钟放款，零售之王", "limit_min": 1, "limit_max": 50, "rate_min": 3.6, "rate_max": 5.8, "pass_score_min": 65, "features": ["3 分钟放款", "已有客户优待"], "requirement": "招行代发/招行卡客户优先", "recommend": 1},
        {"name": "招行 e 招贷", "subtitle": "大额分期", "limit_min": 5, "limit_max": 100, "rate_min": 4.5, "rate_max": 7.2, "pass_score_min": 60, "features": ["额度高", "分期还款"], "requirement": "招行白金卡及以上客户", "recommend": 0},
    ],
    "PAB": [
        {"name": "新一贷", "subtitle": "平安信用贷，最高 50 万", "limit_min": 1, "limit_max": 50, "rate_min": 5.4, "rate_max": 17.88, "pass_score_min": 50, "features": ["额度上限高", "负债容忍度高"], "requirement": "有稳定收入证明", "recommend": 1},
        {"name": "保单贷", "subtitle": "用保单贷款", "limit_min": 1, "limit_max": 50, "rate_min": 4.8, "rate_max": 8.4, "pass_score_min": 55, "features": ["保单客户优待"], "requirement": "持有平安保单满 2 年", "recommend": 0},
    ],
    "XCB": [
        {"name": "好人贷", "subtitle": "新网信用贷", "limit_min": 0.5, "limit_max": 20, "rate_min": 7.2, "rate_max": 18.0, "pass_score_min": 40, "features": ["门槛低", "线上申请"], "requirement": "无重大征信瑕疵", "recommend": 1},
    ],
    "WEBANK": [
        {"name": "微粒贷", "subtitle": "腾讯系，扫码即贷", "limit_min": 0.5, "limit_max": 20, "rate_min": 7.2, "rate_max": 18.0, "pass_score_min": 45, "features": ["扫码即贷", "按日计息"], "requirement": "微信白名单受邀用户", "recommend": 1},
    ],
    "MYBANK": [
        {"name": "网商贷", "subtitle": "阿里小微专属", "limit_min": 1, "limit_max": 100, "rate_min": 6.0, "rate_max": 14.4, "pass_score_min": 50, "features": ["电商卖家专项", "流水贷"], "requirement": "淘宝/天猫/1688 卖家", "recommend": 1},
    ],
}


def _merge_featured_fields(steps: list[dict], featured: list[dict]) -> list[dict]:
    """把特色字段追加到对应 step 的 fields_json"""
    out = [dict(s, fields_json=list(s["fields_json"])) for s in steps]
    for f in featured:
        for s in out:
            if s["step_no"] == f["step_no"]:
                s["fields_json"].append(
                    {k: v for k, v in f.items() if k != "step_no"}
                )
                break
    return out


async def main() -> None:
    """执行 seed"""
    # 先建表（SQLite 本地模式）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ 表结构已确认")

    async with AsyncSessionLocal() as db:
        # 清空旧数据
        await db.execute(delete(BankProduct))
        await db.execute(delete(BankFormSchema))
        await db.execute(delete(Bank))
        await db.commit()
        print("✓ 已清空 banks / bank_form_schemas / bank_products")

        bank_id_map: dict[str, int] = {}

        # 1. 插银行
        for b in BANKS:
            obj = Bank(**b)
            db.add(obj)
        await db.commit()

        # 拉回 id
        res = await db.execute(select(Bank).order_by(Bank.id))
        for obj in res.scalars().all():
            bank_id_map[obj.code] = obj.id
        print(f"✓ 插入 {len(bank_id_map)} 家银行")

        # 2. 插 schema
        for code, featured in BANK_FEATURED_FIELDS.items():
            bank_id = bank_id_map[code]
            steps = _merge_featured_fields(_common_steps(code), featured)
            for s in steps:
                db.add(BankFormSchema(
                    bank_id=bank_id,
                    step_no=s["step_no"],
                    step_title=s["step_title"],
                    step_subtitle=s["step_subtitle"],
                    step_label=s["step_label"],
                    fields_json=s["fields_json"],
                    sort_order=s["sort_order"],
                    enabled=1,
                ))
        await db.commit()
        print(f"✓ 插入 {sum(len(_common_steps(c)) for c in bank_id_map)} 条 schema（含 {len(BANK_FEATURED_FIELDS)} 家特色字段）")

        # 3. 插产品
        product_count = 0
        for code, products in BANK_PRODUCTS.items():
            bank_id = bank_id_map[code]
            for i, p in enumerate(products):
                db.add(BankProduct(
                    bank_id=bank_id,
                    sort_order=i,
                    **p,
                ))
                product_count += 1
        await db.commit()
        print(f"✓ 插入 {product_count} 款产品")

    print("\n🎉 Seed 完成！")
    print(f"   - 银行: {len(BANKS)} 家")
    print(f"   - Schema: {len(BANKS)} × 5 步")
    print(f"   - 产品: {product_count} 款")


if __name__ == "__main__":
    asyncio.run(main())
