# 信测通 · Vercel 部署指南

> 整套应用（FastAPI 后端 + UniApp H5 前端）部署到 Vercel 免费层
> 优点：永不睡、全球 CDN、自动 HTTPS、永久免费

---

## 前提
- ✅ 代码已推送到 https://github.com/tatasun-vip/xinceutong
- ✅ Vercel 账号（用 GitHub 登录即可）

## 步骤（5 分钟）

### 1. 用 GitHub 登录 Vercel
👉 https://vercel.com/login
- 选 `Continue with GitHub`
- 授权 Vercel 访问你的仓库

### 2. 创建项目
- 进 https://vercel.com/new
- 选 `Import` 旁边的 `tatasun-vip/xinceutong`
- 点 `Import`

### 3. 配置项目
- **Project Name**：`xinceutong`（最终 URL 是 `xinceutong.vercel.app`）
- **Framework Preset**：`Other`
- **Root Directory**：留空（默认是仓库根）
- **Build Command**：已经在 `vercel.json` 里写好，不用改
- **Output Directory**：留空
- **Install Command**：留空

### 4. 配置环境变量（关键！）
点 `Environment Variables` 区域，添加：

| Key | Value |
|---|---|
| `DATABASE_URL` | （见下，数据库连接串） |
| `JWT_SECRET` | （点 `Generate` 自动生成随机值） |

**DATABASE_URL 选哪个？** —— **推荐 Neon 免费层**：

#### 方案 A：Neon（推荐，永久免费 512MB）
1. 去 https://neon.tech 用 GitHub 注册
2. New Project → 选 region（Singapore）
3. 复制 Connection String（形如 `postgresql://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`）
4. 在 Vercel 环境变量里：
   - Key: `DATABASE_URL`
   - Value: 把上面 URL 里的 `postgresql://` 改成 `postgresql+asyncpg://`，加 `?ssl=require`
   - 例：`postgresql+asyncpg://user:pass@ep-xxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&ssl=require`
5. 在 Neon 控制台 SQL Editor 跑 `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`（可选）

#### 方案 B：Vercel Postgres（集成度最高，但 256MB）
- Vercel 项目页 → `Storage` 标签 → `Create Database` → `Postgres`
- 自动注入 `POSTGRES_URL` 环境变量
- 我们要的是 `DATABASE_URL`，所以把它值拷贝到 `DATABASE_URL`

#### 方案 C：Supabase（推荐如果以后想要管理面板）
- https://supabase.com 创建项目
- Settings → Database → Connection String → `Direct connection`
- 改 `postgresql://` → `postgresql+asyncpg://`

### 5. 首次部署
- 点 `Deploy`
- ⏳ 等 3-5 分钟（Vercel 会跑 `npm install` + `uni build` + 装 Python 依赖）
- 部署过程实时显示 Logs

### 6. 验证
部署成功会跳转到项目页，给你一个 URL：
- 假设叫 `https://xinceutong.vercel.app`

测一下：
- 打开 `https://xinceutong.vercel.app` → 应看到测评问卷
- 打开 `https://xinceutong.vercel.app/api/health` → 应返回 `{"status":"ok"}`
- 打开 `https://xinceutong.vercel.app/docs` → 应看到 FastAPI Swagger 文档

### 7. 初始化数据库数据
部署成功后，需要在 Neon 控制台跑初始化脚本：

```sql
-- 复制 xinceutong-server/sql/migrations/0001_6_products.sql 的内容到 Neon SQL Editor 执行
-- 复制 xinceutong-server/scripts/init_product_types.py / init_site_config.py / init_scorecard.py 的内容
-- 逐个跑（或改用 psql 跑）
```

或者我帮你写个一次性初始化 API（部署后访问一次就建好数据）。

---

## 自定义域名

Vercel 项目页 → `Settings` → `Domains` → 输入 `test.xinceutong.com`
到 DNS 加 CNAME：`test` → `cname.vercel-dns.com`

## 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| 部署失败：`pip install` 超时 | Python 依赖太多 | Vercel 免费层 install 有 5min 限制，必要时精简 requirements |
| 部署失败：`uni build` 失败 | npm install 慢 | 等待（首次 5-8 分钟）；后续用缓存就快 |
| 访问首页 404 | `dist/build/h5` 还没生成 | 看 Build Logs 是否 buildCommand 跑成功 |
| 测评提交 500 | DB 还没初始化数据 | 在 Neon 跑 SQL 初始化脚本 |
| API 报 504 超时 | Serverless 10s 限制 | 测评若超过 10s 需优化算法；或升级 Pro |

## 免费层限制

- **100 GB 带宽/月**（够用）
- **100 GB-Hours 函数执行时间/月**
- **10s 函数超时**（Hobby 层）
- **512 MB 函数内存**

## 切换到 Render 的备份方案

如果 Vercel 跑不起来，render.yaml 还保留着，一行 `git push` 后到 Render 用 Blueprint 即可。
