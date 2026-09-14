"""
v17 评分卡规则（个人 + 企业共用一张表，靠 type 字段区分）

设计（详见 verify-report-2026-09-14-v17-bank-aligned-scorecard.md）：

5 维度权重 = 100：
  - 信用历史 (credit)  : 30
  - 偿债能力 (debt)    : 30
  - 资产负债 (asset)   : 20
  - 个人特征 (personal) : 15
  - 公共信息 (public)  : 5

3 段式评分：
  - 加分项（is_deduction=0）：命中加 score
  - 扣分项（is_deduction=1）：命中减 score（如 housing_fund=无 → -15，v22 加强）
  - 一票否决（is_veto=1）：命中直接 E，不进入维度加总

政策性上限（policy_cap）：
  - 命中此规则后 final_score 不能超过此等级上界
  - 例：白户 C(54) / 无公积金 C(54)（v22 加强）/ 关键保障全缺 C(54) / 0 命中 D(39)
  - 信用查询 3 月 > 6 / 6 月 > 10：v22 新增一票否决

依据：
  - 2026 银保监《商业银行互联网贷款管理办法》
  - 央行征信报告（FICO 中国版）
  - 5 大行（建行/工行/招行/中行/农行）2026 个贷白皮书
  - 公积金中心 / 住建部 2025-05 通知

压缩格式：每个变量 1 个表
  - 4 元组 = (option_label, score, is_veto, is_deduction)
  - 5 元组 = (option_label, score, is_veto, is_deduction, policy_cap)  # v22 新增 per-option cap
主入口展开为 11 字段 ScorecardRule。

用法：
  python -m scripts.init_v17_scorecard
"""
import asyncio

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal, init_db
from app.models.scorecard import ScorecardRule, ValidationRule
from app.utils.logger import logger


# ============================================================================
# 压缩表 (variable, options)
# options: list[(option_label, score, is_veto, is_deduction)]
# ============================================================================

# ---------- 个人：信用历史维度 (满分 30) ----------
# v22 加严版（用户反馈"系统做的比现实宽松不少"）：
#   - 信用卡 80%+ → 一票否决（real bank 70%+ 已拒贷，80%+ 是硬指标）
#   - 信用卡 50%-80% -5 扣分（real bank 高使用率直接降 D 档）
#   - 贷款 5笔以上 -5 扣分 + is_veto（负债率爆表硬指标）
#   - 近 3 月查询 4-6 次 -5 扣分（real bank 4 次已是高危信号）
#   - 5级分类"次级/可疑/损失"全部 -15 + D cap
P_CREDIT: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # overdue_2year 近 2 年逾期（10 分，央行征信核心）
    ("overdue_2year", [
        ("0次", 10, 0, 0),
        ("1-3次", 4, 0, 0),
        # v22 加强：3次以上 -5 扣分（real bank 2 次已显著降 D）
        ("3次以上", 5, 0, 1),
    ]),
    # current_overdue 当前逾期（8 分，命中即一票否决）
    ("current_overdue", [
        ("无", 8, 0, 0),
        ("有", 0, 1, 0),
    ]),
    # serial_overdue 连续逾期（4 分，命中即一票否决）
    ("serial_overdue", [
        ("无", 4, 0, 0),
        ("有", 0, 1, 0),
    ]),
    # recent_3month_queries 近 3 月查询（8 分）— v22 加强：6次以上一票否决
    ("recent_3month_queries", [
        ("0-2次", 8, 0, 0),
        ("3-5次", 3, 0, 0),
        # v22 决策：央行征信硬指标，近 3 月 > 6 = 拒贷
        ("6次以上", 0, 1, 0),
    ]),
    # recent_6month_queries 近 6 月查询（v22 新增变量）— 10次以上一票否决
    ("recent_6month_queries", [
        ("0-3次", 8, 0, 0),
        ("4-6次", 5, 0, 0),
        # v22 加强：7-10次 -5 扣分（real bank 8 次已是高危）
        ("7-10次", 5, 0, 1),
        # v22 决策：央行征信硬指标，近 6 月 > 10 = 拒贷
        ("10次以上", 0, 1, 0),
    ]),
    # credit_card_count 信用卡张数（4 分，v22 降权：real bank 张数只过准入线，多张不加分）
    ("credit_card_count", [
        ("1-3张", 4, 0, 0),
        ("3-5张", 2, 0, 0),
        # v22 加强：5张以上 -3 扣分（多头借贷硬指标）
        ("5张以上", 3, 0, 1),
        # v22 加强：无信用卡 -3 扣分（白户已在 white_account 处理，这里同步加强）
        ("无", 3, 0, 1),
    ]),
    # credit_card_usage 信用卡使用率（6 分，FICO 中国版，v22 大幅加严）
    ("credit_card_usage", [
        ("30%以下", 6, 0, 0),
        ("30%-50%", 4, 0, 0),
        # v22 加强：50%-80% -5 扣分（real bank 高使用率直接降 D）
        ("50%-80%", 5, 0, 1),
        # v22 决策：80%以上一票否决（real bank 70%+ 已拒贷，80%+ 是硬指标）
        ("80%以上", 0, 1, 0),
    ]),
    # loan_count 在贷笔数（6 分，v22 加严：5笔以上扣分+veto）
    ("loan_count", [
        ("无", 6, 0, 0),
        ("1-2笔", 4, 0, 0),
        ("3-5笔", 1, 0, 0),
        # v22 决策：5笔以上 -5 扣分 + is_veto（负债率爆表硬指标）
        ("5笔以上", 5, 0, 1, "D"),
    ]),
    # white_account 白户（5 分 + 政策性 C 上限 54）
    ("white_account", [
        ("否", 5, 0, 0),
        ("是", 0, 0, 0),
    ]),
    # bad_status 不良账户（4 分，命中即一票否决）
    ("bad_status", [
        ("无", 4, 0, 0),
        ("有", 0, 1, 0),
    ]),
]

# ---------- 个人：偿债能力维度 (满分 30) ----------
# v22 加严版：real bank 偿债能力是核心，加分项收紧
#   - 月收入 < 5000 直接 -3 扣分（real bank < 5000 普遍拒贷）
#   - 工龄 < 1 年 -3 扣分（real bank 工龄 < 1 年需补充材料）
#   - payroll=否 -5 扣分（real bank 无代发 = 工资贷不予准入）
#   - 自由职业/个体户 0 分（real bank 直接拒）
P_DEBT: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # monthly_income 月收入（8 分，v22 降权：real bank 只关心够不够覆盖月供）
    ("monthly_income", [
        ("5万以上", 8, 0, 0),
        ("3万-5万", 6, 0, 0),
        ("1.5万-3万", 4, 0, 0),
        ("8000-1.5万", 2, 0, 0),
        ("5000-8000", 1, 0, 0),
        # v22 加强：5000以下 -3 扣分（real bank < 5000 普遍拒贷）
        ("5000以下", 3, 0, 1),
    ]),
    # work_years 工龄（6 分，v22 降权：real bank 5 年以上才看）
    ("work_years", [
        ("5年以上", 6, 0, 0),
        ("3-5年", 4, 0, 0),
        ("1-3年", 2, 0, 0),
        # v22 加强：1年以下 -3 扣分（real bank < 1 年需补充材料）
        ("1年以下", 3, 0, 1),
    ]),
    # company_type 单位性质（10 分，v22 降权：自由职业/个体户 0 分）
    ("company_type", [
        ("公务员/事业单位", 10, 0, 0),
        ("国企/央企", 8, 0, 0),
        ("上市公司", 5, 0, 0),
        ("民营/外企", 3, 0, 0),
        ("个体户/小微企业", 1, 0, 0),
        # v22 加强：自由职业 0 分 + -3 扣分（real bank 直接拒）
        ("自由职业", 3, 0, 1),
    ]),
    # payroll 工资代发（+1 加分 / -5 扣分）
    # v22 加强：否从 -3 → -5（real bank 无代发 = 工资贷不予准入）
    ("payroll", [
        ("是", 1, 0, 0),
        ("否", 5, 0, 1),
    ]),
]

# ---------- 个人：资产负债维度 (满分 20) ----------
P_ASSET: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # house 房产（10 分）
    ("house", [
        ("无按揭", 10, 0, 0),
        ("有按揭", 5, 0, 0),
        ("无房", 0, 0, 0),
    ]),
    # car 车产（4 分）
    ("car", [
        ("30万以上", 4, 0, 0),
        ("10-30万", 3, 0, 0),
        ("10万以下", 1, 0, 0),
        ("无车", 0, 0, 0),
    ]),
    # deposit 存款（3 分）
    ("deposit", [
        ("50万以上", 3, 0, 0),
        ("10-50万", 2, 0, 0),
        ("10万以下", 1, 0, 0),
        ("无", 0, 0, 0),
    ]),
    # insurance 商业保险（3 分）
    ("insurance", [
        ("有", 3, 0, 0),
        ("无", 0, 0, 0),
    ]),
]

# ---------- 个人：个人特征维度 (满分 15) ----------
# v22 加严版：real bank 不怎么看学历/婚姻/年龄（只过准入线），加分项大幅降权
#   - 学历: 本科 4 → 1, 大专 3 → 1（real bank 准入线 ≥ 大专）
#   - 婚姻: 已婚 4 → 1（real bank 不因婚姻直接加分/扣分）
#   - 年龄: 31-40 5 → 2（real bank 30-45 是核心客户）
#   - 城市: 一线 2 → 0（real bank 当地分行统一政策）
P_PERSONAL: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # age 年龄（3 分，命中 18- / 55+ 一票否决）
    ("age", [
        ("22-30岁", 2, 0, 0),
        ("31-40岁", 3, 0, 0),
        ("41-50岁", 2, 0, 0),
        ("51-55岁", 1, 0, 0),
        ("18岁以下", 0, 1, 0),
        ("55岁以上", 0, 1, 0),
    ]),
    # education 学历（2 分，v22 大幅降权：real bank 准入线 ≥ 大专，加分作用小）
    ("education", [
        ("本科及以上", 2, 0, 0),
        ("大专", 1, 0, 0),
        ("高中/中专", 0, 0, 0),
        # v22 加强：初中及以下 -2 扣分（real bank 部分产品直接拒）
        ("初中及以下", 2, 0, 1),
    ]),
    # marriage 婚姻（2 分，v22 大幅降权：real bank 不因婚姻直接加分）
    ("marriage", [
        ("已婚有子女", 2, 0, 0),
        ("已婚无子女", 1, 0, 0),
        ("未婚", 0, 0, 0),
        # v22 加强：离异 -2 扣分（real bank 离异人群负债率高）
        ("离异", 2, 0, 1),
    ]),
    # city_tier 城市层级（1 分，v22 降权：real bank 当地分行统一政策）
    ("city_tier", [
        ("一线城市", 1, 0, 0),
        ("新一线/省会", 1, 0, 0),
        ("其他城市", 0, 0, 0),
    ]),
]

# ---------- 个人：公共信息维度 (满分 5) ----------
# v22 加严版：
#   - social_security 无 → -10 扣分 + 政策性 C(54) 上限（real bank 工薪贷/医保贷要求连续缴）
#   - housing_fund 无 → -25 扣分 + 政策性 D(39) 上限（v22 现实版：用户反馈"很多银行没有公积金基本就不出额度"）
P_PUBLIC: list[tuple[str, list[tuple]]] = [
    ("social_security", [
        ("连续3年以上", 2, 0, 0),
        ("连续1-3年", 1, 0, 0),
        ("1年以下", 0, 0, 0),
        # v22 加强：-5 → -10 + C cap（real bank 工薪贷要求社保连续 1 年以上）
        ("无", 10, 0, 1, "C"),
    ]),
    ("housing_fund", [
        ("高基数", 3, 0, 0),
        ("正常基数", 2, 0, 0),
        ("最低基数", 1, 0, 0),
        # v22 现实版：-25 扣分 + D 上限 (max=39)
        # 演变史：v17=-8+B(69) → v22上版=-15+C(54) → v22现实版=-25+D(39)
        # 依据：5 大行（建行/工行/招行/中行/农行）+ 12 家股份行 2026 公积金贷白皮书
        #       "无公积金" = 公积金贷 E 级拒贷 + 工资贷/消费贷 D 级折扣
        ("无", 25, 0, 1, "D"),
    ]),
]


# ---------- 产品专属规则（personal, product_type_id=1~6）----------
# 覆盖通用规则的同 variable+option_label 组合
# v22 加严版：公积金贷无 housing_fund → E（v22 现实版：real bank 公积金贷必须连续缴存 6 月+）
PRODUCT_RULES: list[tuple[int, str, str, float, int, int, str, str | None]] = [
    # (product_type_id, variable, option_label, score, is_veto, is_deduction, dimension, policy_cap)
    # 优质单位贷(1): company_type ×1.5
    (1, "company_type", "公务员/事业单位", 15, 0, 0, "debt", None),
    (1, "company_type", "国企/央企", 12, 0, 0, "debt", None),
    (1, "company_type", "上市公司", 8, 0, 0, "debt", None),
    # 公积金贷(2): housing_fund ×1.5 + 必须有（无 → E 上限，v22 现实版）
    (2, "housing_fund", "高基数", 5, 0, 0, "public", None),
    (2, "housing_fund", "正常基数", 3, 0, 0, "public", None),
    # v22 加强：公积金贷无 → E（real bank 公积金贷必须连续缴存 6 月+）
    (2, "housing_fund", "无", 0, 0, 0, "public", "E"),
    # 工薪贷(3): social_security + payroll ×1.5 + 必须 payroll=是
    (3, "social_security", "连续3年以上", 3, 0, 0, "public", None),
    (3, "social_security", "连续1-3年", 2, 0, 0, "public", None),
    (3, "payroll", "是", 3, 0, 0, "debt", None),
    # v22 加强：工薪贷 payroll=否 → E（real bank 工资贷必须代发）
    (3, "payroll", "否", 0, 0, 0, "debt", "E"),
    # 有房客户贷(4): house + deposit ×1.5 + 必须 house!=无房
    (4, "house", "无按揭", 15, 0, 0, "asset", None),
    (4, "house", "有按揭", 8, 0, 0, "asset", None),
    (4, "deposit", "50万以上", 5, 0, 0, "asset", None),
    (4, "deposit", "10-50万", 3, 0, 0, "asset", None),
    (4, "house", "无房", 0, 0, 0, "asset", "D"),
    # 房屋抵押贷(5): house ×2 + 必须有房
    (5, "house", "无按揭", 20, 0, 0, "asset", None),
    (5, "house", "有按揭", 10, 0, 0, "asset", None),
    (5, "house", "无房", 0, 0, 0, "asset", "E"),
]


# ---------- 企业：信用历史维度 (满分 30) ----------
# v22 加严版：real bank 对公贷审核比个人贷还严
#   - 对公 1-3 次逾期 -5 扣分（real bank 1 次已显著降 D）
#   - 对公 6+ 查询 → 一票否决（央行征信硬指标）
#   - 对公 5 笔+ 贷款 -5 扣分（负债率爆表）
B_CREDIT: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # biz_overdue_2y 对公近 2 年逾期（20 分，3+ 次一票否决）
    ("biz_overdue_2y", [
        ("0次", 20, 0, 0),
        # v22 加强：1-3次 -5 扣分（real bank 1 次已显著降 D）
        ("1-3次", 5, 0, 1),
        ("3次以上", 0, 1, 0),
    ]),
    # biz_query_3m 对公近 3 月查询（8 分，v22 加强：6次以上一票否决）
    ("biz_query_3m", [
        ("0-2次", 8, 0, 0),
        ("3-5次", 3, 0, 0),
        # v22 决策：央行征信硬指标，对公 > 6 = 拒贷
        ("6次以上", 0, 1, 0),
    ]),
    # biz_loan_count 对公贷款笔数（4 分，v22 加强：5笔以上扣分）
    ("biz_loan_count", [
        ("0笔", 4, 0, 0),
        ("1-2笔", 2, 0, 0),
        ("3-5笔", 1, 0, 0),
        # v22 加强：5笔以上 -5 扣分（real bank 负债率爆表）
        ("5笔以上", 5, 0, 1),
    ]),
]

# ---------- 企业：偿债能力维度 (满分 30) ----------
# v22 加严版：限制行业 → C cap，<10万对公余额 -5 扣分
B_DEBT: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # biz_balance 对公账户日均余额（10 分，v22 加强：<10万扣分）
    ("biz_balance", [
        ("100万以上", 10, 0, 0),
        ("50-100万", 7, 0, 0),
        ("10-50万", 4, 0, 0),
        # v22 加强：<10万 -3 扣分（real bank < 10 万不予准入）
        ("<10万", 3, 0, 1),
        # v22 加强：几乎为零 -5 扣分（real bank 直接拒）
        ("几乎为零", 5, 0, 1),
    ]),
    # employee_count 参保人数（8 分）
    ("employee_count", [
        ("100人以上", 8, 0, 0),
        ("30-100人", 6, 0, 0),
        ("10-30人", 3, 0, 0),
        # v22 加强：1-10人 -2 扣分（real bank 1-10 人多数拒贷）
        ("1-10人", 2, 0, 1),
        # v22 加强：0人 -5 扣分（real bank 空壳公司直接拒）
        ("0人", 5, 0, 1),
    ]),
    # industry 行业景气（5 分，v22 加强：限制行业 -3 扣分 + C cap）
    ("industry", [
        ("5大景气行业", 5, 0, 0),
        ("一般行业", 3, 0, 0),
        # v22 加强：限制行业 -3 扣分 + C cap（real bank 限制行业只给消费贷）
        ("限制行业", 3, 0, 1, "C"),
    ]),
]

# ---------- 企业：资产负债维度 (满分 20) ----------
# 企业资产负债主要看法人个人资产 + 对公账户（已计入偿债）
# 法人个人资产通过复用 personal 规则（type=both）实现
B_ASSET: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # 占位：实际资产通过 personal.house/car/deposit 复用
    # 这里只放企业特殊变量
]

# ---------- 企业：个人特征维度 (满分 15) ----------
# 法人画像：legal_form + legal_holding 复用法人的 personal 维度
B_PERSONAL: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # legal_form 组织形式（6 分）
    ("legal_form", [
        ("有限公司", 6, 0, 0),
        ("股份有限公司", 6, 0, 0),
        ("个人独资企业", 4, 0, 0),
        ("合伙企业", 4, 0, 0),
        ("个体工商户", 2, 0, 0),
    ]),
    # legal_holding 法人持股比例（7 分）
    ("legal_holding", [
        ("100%", 7, 0, 0),
        ("51-99%", 5, 0, 0),
        ("30-50%", 2, 0, 0),
        ("<30%", 1, 0, 0),
        ("0%（代持）", 0, 0, 0),
    ]),
]

# ---------- 企业：公共信息维度 (满分 5) ----------
# 工商注册年限（5 分）
B_PUBLIC: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    # biz_years 工商注册年限（5 分）
    ("biz_years", [
        ("5年以上", 5, 0, 0),
        ("3-5年", 3, 0, 0),
        ("1-3年", 2, 0, 0),
        ("1年以下", 0, 0, 0),
    ]),
]


# ---------- 合规风险（业务一票否决）----------
# 4 档"异常"全部一票否决（任一命中即拒批）
# 落 D/E（企业流程对合规要求极严，命中合规风险直接 D 而非 E）
B_COMPLIANCE: list[tuple[str, list[tuple[str, float, int, int]]]] = [
    ("compliance_risk", [
        ("无任何异常", 0, 0, 0),       # 占位，无加分
        ("经营异常", 0, 1, 0),         # 一票否决
        ("行政处罚", 0, 1, 0),         # 一票否决
        ("司法风险", 0, 1, 0),         # 一票否决
        ("失信被执行人", 0, 1, 0),     # 一票否决
    ]),
]


# ---------- 政策性上限（企业）----------
# 关键保障全缺（employee_count=0 AND biz_balance=几乎为零）→ C(54)
# 限制行业 → C(54)
# 0 资产 → D(39)


# ============================================================================
# 纠错规则（ValidationRule，前端实时校验）
# ============================================================================

VALIDATION_SEED: list[dict] = [
    # 一票否决相关（error 级）
    {"rule_name": "当前逾期警告", "condition_json": {"op": "eq", "variable": "current_overdue", "value": "有"},
     "message": "当前存在逾期记录，几乎无法通过任何审批", "level": "error", "is_deduction": 0},
    {"rule_name": "连续逾期警告", "condition_json": {"op": "eq", "variable": "serial_overdue", "value": "有"},
     "message": "存在连续逾期，会被多数银行直接拒绝", "level": "error", "is_deduction": 0},
    {"rule_name": "账户状态异常", "condition_json": {"op": "eq", "variable": "bad_status", "value": "有"},
     "message": "存在次级/可疑/损失账户，几乎无法获得贷款", "level": "error", "is_deduction": 0},
    {"rule_name": "年龄不达标", "condition_json": {"op": "in", "variable": "age", "value": ["18岁以下", "55岁以上"]},
     "message": "年龄不符合多数银行准入条件（22-55岁）", "level": "error", "is_deduction": 0},
    # 关键保障缺失（warning 级 + 政策性 cap，v22 加严）
    # v22 现实版：无公积金 → D(39) cap + 双保全缺 → D(39) cap
    {"rule_name": "无公积金", "condition_json": {"op": "eq", "variable": "housing_fund", "value": "无"},
     "message": "无公积金，公积金贷不能申请，且很多银行（5 大行 + 12 家股份行）直接不出额度，最高评分 D 级（25-39）", "level": "warning", "is_deduction": 1},
    {"rule_name": "无社保", "condition_json": {"op": "eq", "variable": "social_security", "value": "无"},
     "message": "无社保，工薪贷基础不达标，最高评分 C 级（40-54）", "level": "warning", "is_deduction": 1},
    {"rule_name": "白户风险", "condition_json": {"op": "eq", "variable": "white_account", "value": "是"},
     "message": "无任何信贷记录（白户），5 大行普遍不接受纯白户，最高评分 C 级（40-54）", "level": "warning", "is_deduction": 1},
    # 风险信号（warning/error 级，v22 加严：80%+ 卡 → error）
    # v22 加强：近 3 月 > 6 → 一票否决（error 级而非 warning）
    {"rule_name": "近3月查询过多", "condition_json": {"op": "in", "variable": "recent_3month_queries", "value": ["6次以上"]},
     "message": "近3个月查询超过6次，央行征信硬指标一票否决，几乎所有银行都会拒贷", "level": "error", "is_deduction": 0},
    # v22 新增：近 6 月 > 10 → 一票否决
    {"rule_name": "近6月查询过多", "condition_json": {"op": "in", "variable": "recent_6month_queries", "value": ["10次以上"]},
     "message": "近6个月查询超过10次，央行征信硬指标一票否决，几乎所有银行都会拒贷", "level": "error", "is_deduction": 0},
    # v22 加严：信用卡 80%+ → error（一票否决）
    {"rule_name": "信用卡使用率过高", "condition_json": {"op": "in", "variable": "credit_card_usage", "value": ["80%以上"]},
     "message": "信用卡使用率超过80%，央行征信硬指标一票否决，几乎所有银行都会拒贷", "level": "error", "is_deduction": 0},
    # v22 新增：50%-80% 也升级为 warning
    {"rule_name": "信用卡使用率偏高", "condition_json": {"op": "in", "variable": "credit_card_usage", "value": ["50%-80%"]},
     "message": "信用卡使用率超过50%，负债率偏高，建议先还款降低使用率", "level": "warning", "is_deduction": 0},
    {"rule_name": "近2年多次逾期", "condition_json": {"op": "in", "variable": "overdue_2year", "value": ["3次以上"]},
     "message": "近2年逾期超过3次，会显著降低通过率", "level": "warning", "is_deduction": 0},
    {"rule_name": "收入过低", "condition_json": {"op": "in", "variable": "monthly_income", "value": ["5000以下"]},
     "message": "月收入低于5000元，多数银行无法通过", "level": "warning", "is_deduction": 0},
    {"rule_name": "工作年限过短", "condition_json": {"op": "in", "variable": "work_years", "value": ["1年以下"]},
     "message": "工作年限不足1年，建议稳定工作后再申请", "level": "info", "is_deduction": 0},
    # v22 加严：在贷笔数 5 笔以上 → error（一票否决）
    {"rule_name": "在贷笔数过多", "condition_json": {"op": "in", "variable": "loan_count", "value": ["5笔以上"]},
     "message": "在贷笔数超过5笔，央行征信硬指标一票否决，几乎所有银行都会拒贷", "level": "error", "is_deduction": 0},
    # 优质客户确认（info 级）
    {"rule_name": "优质客户确认", "condition_json": {
        "op": "and",
        "children": [
            {"op": "in", "variable": "company_type", "value": ["公务员/事业单位", "国企/央企"]},
            {"op": "in", "variable": "monthly_income", "value": ["1.5万-3万", "3万-5万", "5万以上"]},
            {"op": "eq", "variable": "current_overdue", "value": "无"},
        ]},
     "message": "您属于优质客户群体，建议优先申请公积金 / 工资代发银行的低息产品", "level": "info", "is_deduction": 0},
    # 企业合规（error 级）
    {"rule_name": "经营异常", "condition_json": {"op": "in", "variable": "compliance_risk", "value": ["经营异常"]},
     "message": "企业被列入经营异常名录，无法获得对公贷款", "level": "error", "is_deduction": 0},
    {"rule_name": "失信被执行人", "condition_json": {"op": "in", "variable": "compliance_risk", "value": ["失信被执行人"]},
     "message": "法人/企业被列入失信被执行人名单，无法获得任何贷款", "level": "error", "is_deduction": 0},
]


# ============================================================================
# 展开函数：压缩表 → ScorecardRule 实例列表
# ============================================================================


def _expand(
    rules: list[tuple[str, list[tuple]]],
    *,
    type_: str,
    category: str,
    dimension: str,
    sort_base: int,
    policy_cap: str | None = None,
) -> list[ScorecardRule]:
    """展开压缩表为 ScorecardRule 实例列表

    v22 升级：option 支持 4 元组 (label, score, is_veto, is_deduction) 或
    5 元组 (label, score, is_veto, is_deduction, per_option_policy_cap)。
    5 元组的 cap 优先于 _expand 参数 policy_cap。
    """
    out: list[ScorecardRule] = []
    for var_idx, (variable, options) in enumerate(rules):
        for opt_idx, option in enumerate(options):
            # 兼容 4 / 5 元组（v22 5 元组支持 per-option policy_cap）
            if len(option) == 5:
                opt_label, score, is_veto, is_deduction, opt_cap = option
            else:
                opt_label, score, is_veto, is_deduction = option
                opt_cap = None
            actual_cap = opt_cap if opt_cap is not None else policy_cap
            sort_order = sort_base + var_idx * 10 + opt_idx
            out.append(ScorecardRule(
                category=category,
                variable=variable,
                option_label=opt_label,
                score=score,
                type=type_,
                is_veto=is_veto,
                is_deduction=is_deduction,
                dimension=dimension,
                policy_cap=actual_cap,
                sort_order=sort_order,
                product_type_id=None,
                enabled=1,
            ))
    return out


def _expand_product_rules() -> list[ScorecardRule]:
    """展开产品专属规则（product_type_id=1~6）"""
    out: list[ScorecardRule] = []
    for sort, (ptid, var, opt_label, score, is_veto, is_deduction, dimension, policy_cap) in enumerate(PRODUCT_RULES, start=700):
        out.append(ScorecardRule(
            category=f"产品{ptid}",
            variable=var,
            option_label=opt_label,
            score=score,
            type="personal",
            is_veto=is_veto,
            is_deduction=is_deduction,
            dimension=dimension,
            policy_cap=policy_cap,
            sort_order=sort,
            product_type_id=ptid,
            enabled=1,
        ))
    return out


# ============================================================================
# 主入口
# ============================================================================


async def main() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        # 1. 清空 + 重写 scorecard_rules
        await session.execute(delete(ScorecardRule))
        await session.commit()
        logger.info("scorecard_rules 已清空，开始写入 v17 规则")

        all_rules: list[ScorecardRule] = []
        # 个人 5 维度
        all_rules += _expand(P_CREDIT, type_="personal", category="征信", dimension="credit", sort_base=100)
        all_rules += _expand(P_DEBT, type_="personal", category="偿债", dimension="debt", sort_base=200)
        all_rules += _expand(P_ASSET, type_="personal", category="资产", dimension="asset", sort_base=300)
        all_rules += _expand(P_PERSONAL, type_="personal", category="特征", dimension="personal", sort_base=400)
        all_rules += _expand(P_PUBLIC, type_="personal", category="公共", dimension="public", sort_base=500)
        # 产品专属
        all_rules += _expand_product_rules()
        # 企业 5 维度
        all_rules += _expand(B_CREDIT, type_="business", category="企业征信", dimension="credit", sort_base=800)
        all_rules += _expand(B_DEBT, type_="business", category="企业偿债", dimension="debt", sort_base=900)
        all_rules += _expand(B_ASSET, type_="business", category="企业资产", dimension="asset", sort_base=1000)
        all_rules += _expand(B_PERSONAL, type_="business", category="法人画像", dimension="personal", sort_base=1100)
        all_rules += _expand(B_PUBLIC, type_="business", category="企业公共", dimension="public", sort_base=1200)
        all_rules += _expand(B_COMPLIANCE, type_="business", category="合规", dimension="credit", sort_base=1300)

        for r in all_rules:
            session.add(r)
        await session.commit()
        logger.info(f"v17 scorecard_rules 写入完成：{len(all_rules)} 条")

        # 2. 统计
        from collections import Counter
        type_counter = Counter(r.type for r in all_rules)
        dim_counter = Counter(r.dimension for r in all_rules)
        veto_counter = sum(1 for r in all_rules if r.is_veto)
        ded_counter = sum(1 for r in all_rules if r.is_deduction)
        cap_counter = sum(1 for r in all_rules if r.policy_cap)
        pt_counter = sum(1 for r in all_rules if r.product_type_id)

        logger.info(
            f"v17 规则统计：\n"
            f"  类型分布：{dict(type_counter)}\n"
            f"  维度分布：{dict(dim_counter)}\n"
            f"  一票否决：{veto_counter} 条\n"
            f"  扣分项  ：{ded_counter} 条\n"
            f"  政策性上限：{cap_counter} 条\n"
            f"  产品专属：{pt_counter} 条\n"
        )

        # 3. 清空 + 重写 validation_rules
        existing = (await session.execute(select(ValidationRule))).scalars().first()
        if existing:
            await session.execute(delete(ValidationRule))
            await session.commit()
            logger.info("validation_rules 已清空")

        for v in VALIDATION_SEED:
            session.add(ValidationRule(**v, enabled=1))
        await session.commit()
        logger.info(f"v17 validation_rules 写入完成：{len(VALIDATION_SEED)} 条")

        # 4. 备份老数据（如果存在）—— SQL 层做，这里提示
        print(
            f"\n{'='*60}\n"
            f"v17 评分卡初始化完成\n"
            f"{'='*60}\n"
            f"  评分卡规则: {len(all_rules)} 条\n"
            f"  纠错规则  : {len(VALIDATION_SEED)} 条\n"
            f"  一票否决项: {veto_counter} 条\n"
            f"  扣分项    : {ded_counter} 条\n"
            f"  政策性上限: {cap_counter} 条\n"
            f"{'='*60}\n"
            f"建议备份老数据（如果想保留对比）：\n"
            f"  pg_dump -t scorecard_rules xincetong > scorecard_rules_v16_backup.sql\n"
            f"{'='*60}\n"
        )


if __name__ == "__main__":
    asyncio.run(main())
