# 信测通 · 信用贷模拟评审工具

> **不查征信 · 不碰真实放贷 · 模拟结果仅供参考**

## 项目结构

```
20260907155240/
├── xincetong-server/         # 后端（FastAPI + MySQL + Redis）
└── xincetong-miniapp/        # 小程序端（UniApp Vue3 + TypeScript）
```

## 角色

| 角色 | 入口 | 权限 |
| --- | --- | --- |
| `user` 普通用户 | 小程序 | 测评、付费、查报告 |
| `promoter` 推广员 | 小程序工作台 | 推广获客、看客户、拿分佣 |
| `admin` 管理员 | H5 后台（独立项目） | 配置评分卡、审核推广员、看数据 |

## 技术栈

| 维度 | 选型 |
| --- | --- |
| 小程序 | **UniApp 3.x + Vue 3 + TypeScript + Vite**（跨端，主战场微信小程序，H5/App 可复用） |
| 后端 | Python 3.11 + FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 异步 |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis 7 |
| 迁移 | Alembic |
| 支付 | 微信支付 JSAPI |
| 部署 | Docker + docker-compose |
| 前端状态 | Pinia + uni.setStorageSync 持久化 |
| 加密 | AES（敏感字段，身份证号等） |
| 金额 | DB `INT(分)` 或 `DECIMAL(元)`，前端 `formatMoney()` |
| 单元测试 | pytest 覆盖率 > 80% |

## 核心原则

1. **不收集敏感信息**：身份证号、银行卡号、人脸、征信账号密码一律不收
2. **所有评分皆模拟**：评分卡、额度、利率均为模拟结果
3. **顶部固定合规条**：所有页面必须显示「模拟测评 · 非银行官方 · 不查征信」
4. **隐私保护**：用户信息未经授权，推广员不可见

## 8 阶段路线

| 阶段 | 内容 | 估时 | 状态 |
| --- | --- | --- | --- |
| 1 | 搭架子（后端 + 小程序） | 1 天 | ✅ 完成 |
| 2 | 评分卡引擎（A 卡逻辑） | 2 天 | 🔜 下一步 |
| 3 | 用户端测评流程（5 步填写） | 3 天 | |
| 4 | 微信登录 + 支付 + 完整报告 | 2 天 | |
| 5 | 分享 + 免费体验 | 1 天 | |
| 6 | 推广员系统 | 3 天 | |
| 7 | 管理后台 H5（独立项目） | 2 天 | |
| 8 | 合规 + 上线 | 1 天 | |

## 快速启动

### 后端

```bash
cd xincetong-server
cp .env.example .env
docker compose up -d --build
docker compose exec api python scripts/init_scorecard.py
curl http://localhost:8000/
```

打开 http://localhost:8000/docs 查看 API 文档。

### 小程序（UniApp）

```bash
cd xincetong-miniapp
npm install
npm run dev:mp-weixin
# 微信开发者工具 → 导入 unpackage/dist/dev/mp-weixin

# 修改 src/manifest.json 的 mp-weixin.appid
# 修改 .env.development 的 VITE_API_BASE_URL=http://localhost:8000
```

## 关键约束

- 金额：DB `DECIMAL(8,2)` 或 `INT(分)`，禁止 `FLOAT`
- 评分：全部走 `scorecard_rules` 表，禁止硬编码
- 评分模型：按银行 A 卡四层逻辑（准入 → 反欺诈 → A 卡 → 额度/利率）
- 额度测算：收入倍数法 / 公积金倍数法 / 资产法 / DSR 约束，取最小值
- 通过概率：基于违约概率 PD 映射，不直接按总分给
- 支付：微信回调必须验签
- 推广员价格区间：6.99 ~ 19.99
- 分佣：事务保证订单/分佣/余额一致
- 敏感字段：身份证号 AES 加密存储

## 免责声明

本项目所有评分、额度、利率均为**模拟结果**，仅供学习和参考。
**不查征信、不构成贷款承诺**。实际审批以金融机构为准。

