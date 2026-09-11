# 信测通 · 部署指南（免费版）

> 信测通 = 信用贷模拟评审工具。整套代码 = FastAPI 后端 + UniApp 跨端 H5 前端。
> 下面 3 种方案任选一种，全部 **零成本**。

---

## 方案 A：Render 一键部署（推荐，5 分钟搞定）

### 准备
- GitHub 账号（推代码用）
- Render 账号（https://render.com ，用 GitHub 一键登录）

### 步骤
1. **把代码推到 GitHub**
   ```bash
   cd /Users/suntata/CodeBuddy/20260907155240
   git init
   git add .
   git commit -m "feat: 信测通完整代码 + Render 一键部署配置"
   # 在 GitHub 新建空仓库 xinceutong，然后：
   git remote add origin git@github.com:你的用户名/xinceutong.git
   git branch -M main
   git push -u origin main
   ```

2. **Render 一键拉起**
   - 进 https://dashboard.render.com
   - 点 **New** → **Blueprint**
   - 选刚才推上去的 `xinceutong` 仓库
   - Render 会自动识别 `render.yaml`，列出 3 个服务：
     - `xinceutong-api`（后端 Web Service）
     - `xinceutong-web`（前端 Static Site）
     - `xinceutong-db`（PostgreSQL 1GB）
   - 点 **Apply**，等 5-8 分钟

3. **拿到两个 URL**
   - 后端 API：`https://xinceutong-api.onrender.com`
   - 前端 H5：`https://xinceutong-web.onrender.com`

4. **首次访问会自动初始化数据**
   - 进 `https://xinceutong-api.onrender.com/docs` 看 API 文档
   - 进 `https://xinceutong-web.onrender.com` 直接测问卷

### Render 免费层注意
- **Web Service 休眠**：15 分钟没人访问会睡，下次访问冷启动 30 秒（首次会慢）
- **PostgreSQL 90 天到期**：到期前 7 天邮件提醒，登录后台点 "Extend" 续 90 天
- **磁盘不持久**：除了 PostgreSQL 之外的本地文件，重启会丢（无影响，重要数据都在 PG）

---

## 方案 B：纯 GitHub Pages 部署（只前端，无后端）

> 只适合「让用户看页面 + 本地填问卷」的纯静态演示。
> 不能保存测评数据、不能接入支付。

### 步骤
1. 在 `xinceutong-miniapp/package.json` 加：
   ```json
   "deploy:h5:gh": "uni build -p h5 && npx gh-pages -d dist/build/h5 -m 'chore: deploy h5'"
   ```
2. 安装 gh-pages：`npm i -D gh-pages --prefix xinceutong-miniapp`
3. GitHub 仓库 Settings → Pages → Source 选 `gh-pages` 分支
4. `npm run deploy:h5:gh`

---

## 方案 C：Vercel + Supabase（前后端分离）

> 比 Render 启动快（无休眠），但需要注册 2 个平台。

### 后端到 Vercel
- 改 `xinceutong-server` 为 Vercel Serverless（FastAPI on Vercel 文档）
- DB 用 Supabase 免费层 PostgreSQL
- 此方案较复杂，**不推荐非工程师使用**。

---

## 部署后必做清单

- [ ] 访问 `https://xinceutong-api.onrender.com/health` 应返回 `{"status":"ok"}`
- [ ] 访问 `https://xinceutong-web.onrender.com` 能看到问卷入口
- [ ] 提交一份完整问卷，看免费版结果页是否正常
- [ ] 修改 `render.yaml` 里 `VITE_API_BASE_URL` 改为实际后端 URL（如 `xinceutong-api.onrender.com`）
- [ ] 改 `JWT_SECRET` 为强随机值（Render 已自动生成，确认下）

## 自定义域名

### 前端（H5）
- 在 Render → `xinceutong-web` → Settings → Custom Domains → 加 `test.yourdomain.com`
- 到域名 DNS 加 CNAME：`test` → `xinceutong-web.onrender.com`
- Render 自动签发 Let's Encrypt 证书

### 后端（API）
- 同上，加 `api.yourdomain.com` → `xinceutong-api.onrender.com`

## 数据备份

```bash
# 从 Render 备份 PostgreSQL 到本地
# Render → xinceutong-db → Backups → 选 "Create Manual Backup"
# 或用 psql：
PGPASSWORD=xxx psql -h xxx.onrender.com -U xinceutong xinceutong > backup_$(date +%Y%m%d).sql
```

## 故障排查

| 现象 | 原因 | 解决 |
|---|---|---|
| 前端访问 404 | Static Site 路径错 | 确认 `staticPublishPath: dist/build/h5`（编译后目录） |
| 后端 502 / 启动失败 | 看 Render → Logs | 多半是 alembic 失败 / PG 连不上 |
| API 报 CORS 错 | `CORS_ORIGINS` 没放开 | 后端环境变量 `CORS_ORIGINS=["*"]` |
| 首次访问 30s 慢 | 免费层冷启动 | 属正常，加 Cron Job 定时 ping 即可保活 |
| 数据库连接 "ssl required" | Render 强制 SSL | 代码已自动加 `?ssl=require` |

## 监控 / 持续部署

- Render 已自带 GitHub 集成：push 代码 → 自动重新部署
- 加 GitHub Action 跑 `pytest` 防止坏代码上线（`xinceutong-server/tests/` 已就位）
