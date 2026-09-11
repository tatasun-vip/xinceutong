# 信测通后端 · FastAPI

> **信用贷模拟评审工具**（不查征信、不碰真实放贷）

## 阶段 2 验收清单 ✅

| 验收项 | 状态 | 说明 |
| --- | --- | --- |
| 评分规则全走 `scorecard_rules` 表（不硬编码） | ✅ | `_load_rules` 走 DB + Redis 缓存 |
| 一票否决单独判断，不进入评分 | ✅ | `_check_veto` → 直接 E 级 + 额度归零 |
| 4 种额度测算方法取最小值 | ✅ | 收入倍数 / 公积金倍数 / 资产 / DSR |
| 通过概率基于 PD 违约概率映射 | ✅ | logistic 函数 → 高/中高/中/低/极低 |
| 7 个单元测试用例 | ✅ | **37 个测试全过**（含核心 7 个 + 30 个补充） |
| 接口返回统一 `{code, message, data}` 格式 | ✅ | `register_exception_handlers` + `utils/response.py` |
| 覆盖率 > 80% | ✅ | **89%**（scorecard_engine 87% / condition_dsl 96% / money 95%） |
| 金额用 `INT(分)` 或 `DECIMAL(元)`，禁止 `FLOAT` | ✅ | DB 字段 `limit_min/max` 用 INT，DB `rate_min/max` 用 DECIMAL(5,2) |

## 银行 A 卡四层逻辑

```
┌─────────────────────────────────────────────────────┐
│ L1 准入层（一票否决）                                 │
│   - age 18以下 / 55以上                              │
│   - current_overdue = 有                             │
│   - serial_overdue = 有                             │
│   - bad_status = 有                                 │
│   命中 → 直接 E 级 + 额度归零                         │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ L2 反欺诈层（阶段 6 接入）                            │
│   预留：手机号黑名单 / 设备指纹 / IP 集中度           │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ L3 A 卡层（评分卡 5 大类 24 个变量）                  │
│   基础（4 变量） + 职业（5 变量） + 收入（1 变量）     │
│   + 资产（4 变量） + 征信（10 变量）                  │
│   归一化到 0~100 → 等级 S/A/B/C/D/E                 │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ L4 额度/利率层（4 种方法取最小）                      │
│   ① 收入倍数法：月收入 × 12 × 等级倍数（24/18/12/8/5/3）│
│   ② 公积金倍数法：月公积金 × 12 × 等级倍数           │
│   ③ 资产法：(无按揭房价 + 车价) × 等级抵押率         │
│   ④ DSR 约束：(月收入 - 月负债) × 0.5 反算 36 期额度  │
│   等级 → 利率区间下限 S=3.5% → E=18%                 │
└─────────────────────────────────────────────────────┘
                       ↓
              PD 违约概率 → 通过概率
              (高 / 中高 / 中 / 低 / 极低)
```

## 评分变量（24 个，5 大类）

| 类别 | 变量 | 含义 |
| --- | --- | --- |
| 基础 | `age` | 年龄段（22-30 / 31-40 / 41-50 / 51-55） |
| 基础 | `education` | 学历 |
| 基础 | `marriage` | 婚姻状况 |
| 基础 | `city_tier` | 城市等级 |
| 职业 | `company_type` | 单位性质（6 类） |
| 职业 | `work_years` | 工作年限 |
| 职业 | `social_security` | 社保连续缴存 |
| 职业 | `housing_fund` | 公积金基数 |
| 职业 | `payroll` | 工资代发 |
| 收入 | `monthly_income` | 月收入区间（6 档） |
| 资产 | `house` | 房产（有按揭/无按揭/无房） |
| 资产 | `car` | 车辆（4 档） |
| 资产 | `deposit` | 存款（4 档） |
| 资产 | `insurance` | 商业保险 |
| 征信 | `credit_card_count` | 信用卡数 |
| 征信 | `credit_card_usage` | 信用卡使用率 |
| 征信 | `loan_count` | 在贷笔数 |
| 征信 | `recent_3month_queries` | 近 3 月查询 |
| 征信 | `overdue_2year` | 近 2 年逾期次数 |
| 征信 | `current_overdue` | 当前是否有逾期（一票否决） |
| 征信 | `serial_overdue` | 连续逾期（一票否决） |
| 征信 | `white_account` | 白户风险 |
| 征信 | `bad_status` | 账户状态异常（一票否决） |

## 8 条核心原则（必须遵守）

1. **评分规则全走 `scorecard_rules` 表**（不硬编码）
2. **一票否决单独判断**，不进入评分
3. **4 种额度测算方法取最小值**
4. **通过概率基于 PD 违约概率映射**
5. **接口返回统一 `{code, message, data}` 格式**
6. **AES 加密身份证号**（`app/core/security.py` 阶段 6 完善）
7. **金额用 `INT(分)` 或 `DECIMAL(元)`**，禁止 `FLOAT`
8. **推广员价格区间 6.99 ~ 19.99**，分佣事务保证

## 项目结构

```
xinceutong-server/
├── app/
│   ├── main.py                      # FastAPI 入口
│   ├── config.py                    # pydantic-settings
│   ├── database.py                  # SQLAlchemy 2.0 异步
│   ├── redis_client.py              # Redis 异步 client
│   ├── core/
│   │   ├── deps.py                  # 依赖注入（JWT / DB / 可选用户）
│   │   ├── exceptions.py            # 业务异常 + 全局 handler
│   │   └── security.py              # JWT / 密码哈希
│   ├── api/
│   │   └── assessment.py            # /api/assessment/{validate,submit,free/{id},report/{id}}
│   ├── models/
│   │   ├── user.py                  # users
│   │   ├── assessment.py            # assessments（input_data JSON）
│   │   ├── scorecard.py             # scorecard_rules + validation_rules + shares + free_trials
│   │   ├── promoter.py
│   │   ├── order.py
│   │   └── commission.py
│   ├── schemas/
│   │   └── assessment.py            # Pydantic v2 模型
│   ├── services/
│   │   ├── scorecard_engine.py      # ⭐ 核心引擎（500+ 行）
│   │   ├── validation_engine.py     # 实时纠错（DSL）
│   │   ├── report_service.py        # 报告生成
│   │   ├── commission_service.py
│   │   └── wechat_service.py
│   └── utils/
│       ├── response.py              # 统一 {code, message, data}
│       ├── condition_dsl.py         # 纠错规则 DSL 评估器
│       ├── money.py                 # 收入/公积金/房价中位数
│       ├── redis_client_safe.py     # 缓存（带降级）
│       ├── id_generator.py          # report_no / order_no / share_code
│       ├── dict_helper.py
│       └── logger.py
├── alembic/                         # 迁移（阶段 2 已具备，生成首版见下方）
├── scripts/
│   └── init_scorecard.py            # 初始化评分卡 + 验证规则
├── tests/
│   ├── conftest.py                  # fixtures（sample_rules / GOOD/BAD_PROFILE）
│   ├── test_health.py
│   └── test_scorecard.py            # ⭐ 37 个测试，覆盖率 89%
├── sql/
│   └── init.sql                     # 12 张表
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## API 路由

### 阶段 2 已启用

| Method | Path | 说明 |
| --- | --- | --- |
| GET  | `/`                       | 根路径探活 |
| GET  | `/health`                 | 健康检查 |
| POST | `/api/assessment/validate`     | 实时纠错 |
| POST | `/api/assessment/submit`       | 提交测评，返回免费结果 |
| GET  | `/api/assessment/free/{id}`    | 查免费结果 |
| GET  | `/api/assessment/report/{id}`  | 查完整报告（阶段 4 完善） |

### 阶段 3-6 待启用（占位）

| Method | Path | 说明 |
| --- | --- | --- |
| POST | `/api/auth/wechat-login`     | 微信登录 |
| GET  | `/api/auth/profile`          | 当前用户 |
| POST | `/api/order/create`          | 创建订单 |
| GET  | `/api/order/status/{no}`     | 订单状态 |
| POST | `/api/promoter/apply`        | 推广员申请 |
| GET  | `/api/promoter/dashboard`    | 工作台 |
| POST | `/api/share/generate`        | 生成分享码 |
| GET  | `/api/share/check/{code}`    | 校验分享码 |

## 快速启动

```bash
# 1. 启动 MySQL + Redis + 后端
docker compose up -d --build

# 2. 初始化评分卡（首次）
docker compose exec api python scripts/init_scorecard.py

# 3. 访问 API
curl http://localhost:8000/
# {"code":0,"message":"success","data":{"app":"xinceutong",...}}

# 4. 跑测试
ENV=test python -m pytest tests/test_scorecard.py -v
# 37 passed

# 5. 跑覆盖率
ENV=test python -m pytest tests/test_scorecard.py \
  --cov=app.services.scorecard_engine \
  --cov=app.utils.condition_dsl \
  --cov=app.utils.money \
  --cov-report=term-missing
# TOTAL 89%
```

## 阶段 2 演示用例

```bash
# 1. 实时纠错（当前逾期 → error 级）
curl -X POST http://localhost:8000/api/assessment/validate \
  -H "Content-Type: application/json" \
  -d '{"step": 4, "type": "personal", "data": {"current_overdue": "有"}}'
# {"code":0,"data":{"valid":false,"has_error":true,"items":[
#   {"rule_name":"当前逾期警告","level":"error","message":"当前存在逾期记录..."}]}}

# 2. 提交测评（高分客户）
curl -X POST http://localhost:8000/api/assessment/submit \
  -H "Content-Type: application/json" \
  -d '{
    "type":"personal",
    "input_data":{
      "age":"31-40岁","education":"本科及以上","marriage":"已婚有子女",
      "city_tier":"一线城市","company_type":"公务员/事业单位",
      "work_years":"5年以上","social_security":"连续3年以上",
      "housing_fund":"高基数","payroll":"是","monthly_income":"5万以上",
      "house":"无按揭","car":"30万以上","deposit":"50万以上","insurance":"有",
      "credit_card_count":"1-3张","credit_card_usage":"30%以下",
      "loan_count":"无","recent_3month_queries":"0-2次",
      "overdue_2year":"0次","current_overdue":"无",
      "serial_overdue":"无","white_account":"否","bad_status":"无"
    }
  }'
# 返回：score ~85, level="A" 或 "S", limit_min/max ~50-80万, pass_probability="高"

# 3. 查免费结果
curl http://localhost:8000/api/assessment/free/1

# 4. 查完整报告
curl http://localhost:8000/api/assessment/report/1
```

## 7 个核心测试用例

| # | 测试名 | 验证核心原则 |
| --- | --- | --- |
| 1 | `test_veto_age_under_18` | 一票否决（年龄） |
| 2 | `test_veto_current_overdue` | 一票否决（当前逾期） |
| 3 | `test_veto_serial_overdue` | 一票否决（连续逾期） |
| 4 | `test_veto_bad_status` | 一票否决（账户状态） |
| 5 | `test_good_profile_s_level` | 高分场景 → S/A 级 |
| 6 | `test_bad_profile_e_level` | 低分场景 → D/E 级 |
| 7 | `test_high_income_bad_credit` | 高收入但征信差 → B/C/D |
| 8 | `test_housing_fund_increases_limit` | 公积金提升额度 |
| 9 | `test_dsr_caps_limit` | DSR 约束压低额度 |
| 10 | `test_pd_monotonic` | PD 单调性 |

## 评分卡调参

`scripts/init_scorecard.py` 的 `SCORECARD_SEED` 改完，重跑：

```bash
docker compose exec api python scripts/init_scorecard.py
# 会先清空再写入最新版本
# 缓存 10 分钟后自动失效，或手动：
docker compose exec redis redis-cli DEL scorecard:rules:v1
```

## 下一步：阶段 3

- 前端 5 步填写页面用 `OptionCard` + `ProgressBar` + 顶部 `<ComplianceBar />`
- 每步 watch 调用 `/api/assessment/validate` 做实时纠错
- 评估动画 + 调 `/api/assessment/submit` 拿免费结果
- 数据存 Pinia + 自动恢复
- 底部按钮 `padding-bottom: env(safe-area-inset-bottom)`

详见 `xinceutong-miniapp/README.md` 阶段 3-6 对齐说明。
