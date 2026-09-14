/**
 * constants/assess-options.ts - 测评选项配置
 *
 * 选项 label 与后端 init_scorecard.py SCORECARD_SEED 的 option_label 完全一致
 * 选项顺序即用户在前端看到的展示顺序
 */
import type { Product, Level } from '@/types'

// ============================================================================
// step1 - 基础信息
// ============================================================================

export const AGE_OPTIONS = [
  { label: '22-30 岁', desc: '黄金年龄段，评分最高' },
  { label: '31-40 岁', desc: '稳定收入期，评分最高' },
  { label: '41-50 岁', desc: '事业成熟期' },
  { label: '51-55 岁', desc: '临近退休，评分略降' },
] as const

export const EDUCATION_OPTIONS = [
  { label: '本科及以上', desc: '学历加分' },
  { label: '大专', desc: '常规学历' },
  { label: '高中/中专', desc: '基础学历' },
  { label: '初中及以下', desc: '学历较低' },
] as const

export const MARRIAGE_OPTIONS = [
  { label: '已婚有子女', desc: '家庭稳定加分' },
  { label: '已婚无子女', desc: '已婚状态加分' },
  { label: '未婚', desc: '基础分' },
  { label: '离异', desc: '不加分' },
] as const

export const CITY_TIER_OPTIONS = [
  { label: '一线城市', desc: '北上广深' },
  { label: '新一线/省会', desc: '成都杭州武汉等' },
  { label: '其他城市', desc: '基础分' },
] as const

// ============================================================================
// step2 - 职业 / 收入
// ============================================================================

export const COMPANY_TYPE_OPTIONS = [
  { label: '公务员/事业单位', desc: '最高权重，优质客群' },
  { label: '国企/央企', desc: '稳定客群' },
  { label: '上市公司', desc: '合规企业' },
  { label: '民营/外企', desc: '常规客群' },
  { label: '个体户/小微企业', desc: '经营类' },
  { label: '自由职业', desc: '收入浮动大' },
] as const

export const WORK_YEARS_OPTIONS = [
  { label: '5 年以上', desc: '工作稳定' },
  { label: '3-5 年', desc: '稳步上升' },
  { label: '1-3 年', desc: '成长期' },
  { label: '1 年以下', desc: '新人' },
] as const

export const SOCIAL_SECURITY_OPTIONS = [
  { label: '连续 3 年以上', desc: '社保优质' },
  { label: '连续 1-3 年', desc: '社保正常' },
  { label: '1 年以下', desc: '社保较短' },
  { label: '无', desc: '无社保记录' },
] as const

export const HOUSING_FUND_OPTIONS = [
  { label: '高基数', desc: '优质客群标志' },
  { label: '正常基数', desc: '常规客群' },
  { label: '最低基数', desc: '基础分' },
  { label: '无', desc: '无公积金' },
] as const

export const PAYROLL_OPTIONS = [
  { label: '是', desc: '工资代发 / 流水可查' },
  { label: '否', desc: '现金发放' },
] as const

export const MONTHLY_INCOME_OPTIONS = [
  { label: '5 万以上', desc: '高净值客群' },
  { label: '3 万-5 万', desc: '中高收入' },
  { label: '1.5 万-3 万', desc: '中产客群' },
  { label: '8000-1.5 万', desc: '常规客群' },
  { label: '5000-8000', desc: '工薪阶层' },
  { label: '5000 以下', desc: '收入较低' },
] as const

// ============================================================================
// step3 - 资产
// ============================================================================

export const HOUSE_OPTIONS = [
  { label: '无按揭', desc: '自有房产 / 全款购入' },
  { label: '有按揭', desc: '贷款购房中' },
  { label: '无房', desc: '租房居住' },
] as const

export const CAR_OPTIONS = [
  { label: '30 万以上', desc: '豪华品牌' },
  { label: '10-30 万', desc: '中端车型' },
  { label: '10 万以下', desc: '经济车型' },
  { label: '无车', desc: '无车记录' },
] as const

export const DEPOSIT_OPTIONS = [
  { label: '50 万以上', desc: '高净值' },
  { label: '10-50 万', desc: '中产储蓄' },
  { label: '10 万以下', desc: '基础储蓄' },
  { label: '无', desc: '无存款' },
] as const

export const INSURANCE_OPTIONS = [
  { label: '有', desc: '商业保险 / 寿险等' },
  { label: '无', desc: '无商业保险' },
] as const

// ============================================================================
// step4 - 征信
// ============================================================================

export const CREDIT_CARD_COUNT_OPTIONS = [
  { label: '无', desc: '无信用卡' },
  { label: '1-3 张', desc: '信用卡少量' },
  { label: '3-5 张', desc: '信用卡较多' },
  { label: '5 张以上', desc: '多头授信' },
] as const

export const CREDIT_CARD_USAGE_OPTIONS = [
  { label: '30% 以下', desc: '使用率低，评分高' },
  { label: '30%-50%', desc: '使用率适中' },
  { label: '50%-80%', desc: '使用率偏高' },
  { label: '80% 以上', desc: '使用率过高，评分低' },
] as const

export const LOAN_COUNT_OPTIONS = [
  { label: '无', desc: '无在贷' },
  { label: '1-2 笔', desc: '少量负债' },
  { label: '3-5 笔', desc: '多头借贷' },
  { label: '5 笔以上', desc: '严重多头借贷' },
] as const

export const RECENT_3M_QUERIES_OPTIONS = [
  { label: '0-2 次', desc: '查询较少' },
  { label: '3-5 次', desc: '查询适中' },
  // v22 加强：6次以上是一票否决，描述强化
  { label: '6 次以上', desc: '央行一票否决，几乎所有银行拒贷' },
] as const

// v22 新增：近 6 月查询（央行硬指标 > 10 = 拒贷）
export const RECENT_6M_QUERIES_OPTIONS = [
  { label: '0-3 次', desc: '查询稀少（加分）' },
  { label: '4-6 次', desc: '查询适中' },
  { label: '7-10 次', desc: '查询较多' },
  { label: '10 次以上', desc: '央行一票否决，几乎所有银行拒贷' },
] as const

export const OVERDUE_2Y_OPTIONS = [
  { label: '0 次', desc: '无逾期' },
  { label: '1-3 次', desc: '少量逾期' },
  { label: '3 次以上', desc: '严重逾期' },
] as const

export const CURRENT_OVERDUE_OPTIONS = [
  { label: '无', desc: '当前无逾期' },
  { label: '有', desc: '一票否决，几乎无法通过' },
] as const

export const SERIAL_OVERDUE_OPTIONS = [
  { label: '无', desc: '无连续逾期' },
  { label: '有', desc: '存在连续 60 天+ 逾期' },
] as const

export const WHITE_ACCOUNT_OPTIONS = [
  { label: '否', desc: '有信贷记录' },
  { label: '是', desc: '白户（无任何信贷记录）' },
] as const

export const BAD_STATUS_OPTIONS = [
  { label: '无', desc: '账户状态正常' },
  { label: '有', desc: '存在次级/可疑/损失账户' },
] as const

// ============================================================================
// step2b - 企业信息（v4 P0 补全 business 类型问卷）
// 选项 label 与后端 init_business_rules.py 的 option_label 完全一致
// ============================================================================

export const TAX_GRADE_OPTIONS = [
  { label: 'A 级',         desc: '最高等级（连续 2 年 A）' },
  { label: 'B 级',         desc: '优质纳税户' },
  { label: 'M 级',         desc: '中等' },
  { label: 'C 级',         desc: '一般' },
  { label: 'D 级/未评级',  desc: 'D 级或未参与纳税评级' },
] as const

export const ANNUAL_TAX_OPTIONS = [
  { label: '100万以上', desc: '高纳税户' },
  { label: '50-100万',  desc: '中高纳税' },
  { label: '20-50万',   desc: '中等纳税' },
  { label: '5-20万',    desc: '小微纳税' },
  { label: '1-5万',     desc: '初创纳税' },
  { label: '1万以下',   desc: '起步阶段' },
] as const

export const TAX_CONTINUITY_OPTIONS = [
  { label: '连续3年',     desc: '纳税稳定（关键加分项）' },
  { label: '连续2年',     desc: '正常连续' },
  { label: '连续1年',     desc: '新近开始' },
  { label: '断过/未缴',   desc: '未连续纳税' },
] as const

export const BUSINESS_YEARS_OPTIONS = [
  { label: '5年以上', desc: '成熟企业' },
  { label: '3-5年',   desc: '稳步经营' },
  { label: '1-3年',   desc: '成长期' },
  { label: '1年以下', desc: '初创' },
] as const

export const ANNUAL_INVOICE_OPTIONS = [
  { label: '1000万以上', desc: '高开票企业' },
  { label: '500-1000万', desc: '中高开票' },
  { label: '200-500万',  desc: '中等开票' },
  { label: '50-200万',   desc: '小微开票' },
  { label: '50万以下',   desc: '小规模' },
] as const

export const INVOICE_CONTINUITY_OPTIONS = [
  { label: '连续3年',     desc: '开票稳定' },
  { label: '连续2年',     desc: '正常连续' },
  { label: '连续1年',     desc: '新近开始' },
  { label: '断过/未开',   desc: '未连续开票' },
] as const

export const INDUSTRY_OPTIONS = [
  { label: '制造业',      desc: '实体经济（加分）' },
  { label: '批发零售',    desc: '商贸流通' },
  { label: '服务业',      desc: '现代服务' },
  { label: '科技/互联网', desc: '高新技术企业（最高加分）' },
  { label: '建筑/工程',   desc: '传统行业' },
  { label: '物流/运输',   desc: '运输业' },
  { label: '其他',        desc: '其他行业' },
] as const

// ============================================================================
// v5 P0 补全：8 个企业专属变量选项（与后端 init_business_v5_rules.py 对齐）
// ============================================================================

/** 法人画像：组织形式（5 档） */
export const LEGAL_FORM_OPTIONS = [
  { label: '有限公司',     desc: '标准有限公司（最优）' },
  { label: '股份有限公司', desc: '股份制（加分）' },
  { label: '个人独资企业', desc: '个人独资（责任大）' },
  { label: '合伙企业',     desc: '合伙制' },
  { label: '个体工商户',   desc: '个体户（评分较低）' },
] as const

/** 法人画像：法人持股比例（5 档） */
export const LEGAL_HOLDING_OPTIONS = [
  { label: '100%',         desc: '完全控股（还款意愿最强）' },
  { label: '51-99%',       desc: '绝对控股' },
  { label: '30-50%',       desc: '相对控股' },
  { label: '<30%',         desc: '小股东' },
  { label: '0%（代持）',   desc: '代持（不推荐）' },
] as const

/** 企业画像：参保人数（5 档） */
export const EMPLOYEE_COUNT_OPTIONS = [
  { label: '100人以上',    desc: '中大型企业' },
  { label: '30-100人',     desc: '中型企业' },
  { label: '10-30人',      desc: '小微企业' },
  { label: '1-10人',       desc: '微型企业' },
  { label: '0人',          desc: '未参保（高风险）' },
] as const

/** 企业画像：对公账户日均余额（5 档） */
export const BIZ_BALANCE_OPTIONS = [
  { label: '100万以上',    desc: '现金流充裕' },
  { label: '50-100万',     desc: '现金流良好' },
  { label: '10-50万',      desc: '现金流一般' },
  { label: '<10万',        desc: '现金流紧张' },
  { label: '几乎为零',     desc: '高风险' },
] as const

/** 企业画像：现有对公贷款笔数（4 档） */
export const BIZ_LOAN_COUNT_OPTIONS = [
  { label: '0笔',          desc: '首贷户（最优）' },
  { label: '1-2笔',        desc: '少量负债' },
  { label: '3-5笔',        desc: '多头借贷' },
  { label: '5笔以上',      desc: '过度借贷' },
] as const

/** 企业画像：近 2 年对公逾期（3 档；3+ 次一票否决） */
export const BIZ_OVERDUE_2Y_OPTIONS = [
  { label: '0次',          desc: '无逾期（最优）' },
  { label: '1-3次',        desc: '偶有逾期' },
  { label: '3次以上',      desc: '严重逾期（拒贷）' },
] as const

/** 企业画像：近 3 月对公查询（3 档） */
export const BIZ_QUERY_3M_OPTIONS = [
  { label: '0-2次',        desc: '查询正常' },
  { label: '3-5次',        desc: '查询偏多' },
  { label: '6次以上',      desc: '资金紧张信号' },
] as const

/** 合规风险：5 选 1（任一命中即一票否决） */
export const COMPLIANCE_RISK_OPTIONS = [
  { label: '无任何异常',   desc: '信用良好（最优）' },
  { label: '经营异常',     desc: '被列入经营异常名录' },
  { label: '行政处罚',     desc: '近 2 年有行政处罚' },
  { label: '司法风险',     desc: '涉诉/被执行' },
  { label: '失信被执行人', desc: '老赖（拒贷）' },
] as const

// ============================================================================
// step4 - 线下辅助资料（v4 选填上传；不参与评分，只用于人工对接参考）
// ============================================================================

export const OFFLINE_DOC_OPTIONS = [
  { key: 'house_cert',  label: '房本',        desc: '个人/企业名下房产证' },
  { key: 'car_cert',    label: '行驶证',      desc: '车辆行驶证' },
  { key: 'biz_license', label: '营业执照',    desc: '企业营业执照' },
  { key: 'tax_cert',    label: '纳税凭证',    desc: '近 12 个月纳税完税证明' },
  { key: 'biz_flow',    label: '对公流水',    desc: '对公账户近 6 个月流水' },
] as const

// ============================================================================
// 等级文案 / 颜色
// ============================================================================

export const LEVEL_CONFIG: Record<Level, { color: string; bg: string; desc: string }> = {
  S: { color: '#7B1FA2', bg: '#F3E5F5', desc: '极佳客群' },
  A: { color: '#1565C0', bg: '#E3F2FD', desc: '优质客群' },
  B: { color: '#2E7D32', bg: '#E8F5E9', desc: '良好客群' },
  C: { color: '#E65100', bg: '#FFF3E0', desc: '一般客群' },
  D: { color: '#C0392B', bg: '#FFEBEE', desc: '较弱客群' },
  E: { color: '#7F0000', bg: '#FFCDD2', desc: '建议暂缓' },
}

export const PASS_PROB_COLOR: Record<string, string> = {
  '高': '#2E7D32',
  '中高': '#5A9C7C',
  '中': '#E65100',
  '低': '#C0392B',
  '极低': '#7F0000',
}

// ============================================================================
// 推荐产品（前端展示模板 - 阶段 3 占位；阶段 4 由后端返回填充）
// ============================================================================

export const DEMO_PRODUCTS: Product[] = [
  { name: '建行快贷',     limit: '5-50 万',  rate: '3.45%-5.4%',  pass: '高',   recommend: true  },
  { name: '招行闪电贷',   limit: '1-50 万',  rate: '3.6%-7.2%',   pass: '中高', recommend: false },
  { name: '工行融e借',    limit: '1-30 万',  rate: '3.7%-7.0%',   pass: '中高', recommend: false },
  { name: '平安新一贷',   limit: '1-50 万',  rate: '5.4%-17.88%', pass: '中',   recommend: false },
  { name: '中行随心智贷', limit: '1-30 万',  rate: '3.9%-7.2%',   pass: '中高', recommend: false },
]
