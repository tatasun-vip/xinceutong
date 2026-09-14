# verify-report-2026-09-14-cvm-deploy.md

> **部署对象**：信测通（xincetong）v11
> **目标**：腾讯云 CVM `82.156.166.188`（TencentOS Server 4，root）
> **域名**：`xincetong.cn`（已 ICP 备案）
> **部署时间**：2026-09-14 18:35 - 18:52（共 17 分钟）
> **方法**：方案 A 就地升级

---

## 一、部署前状态（CVM 探活）

| 项 | 探活值 |
|---|---|
| 域名 | `xincetong.cn` → 82.156.166.188 ✅ |
| 旧后端 | `/opt/xinceutong/api/_server/`（多 u） |
| 旧 systemd | `xinceutong-backend.service` enabled |
| 旧 nginx | `xinceutong.conf` default_server |
| 旧数据库 | SQLite `xinceutong.db` 4MB |
| 8000 端口 | 旧 uvicorn pid 73833 |
| PG 状态 | ❌ 未装 |

---

## 二、9 步部署

| # | 步骤 | 结果 |
|---|---|---|
| 1 | 清理旧部署（备份 + 移走 unit/conf + kill 73833） | ✅ 104M 备份，10 秒断服 |
| 2 | 装 PostgreSQL 15 | ✅ `active (running)` |
| 3 | 创库 + 创用户 + 授权 public schema + pg_hba.md5 | ✅ 密码连 OK |
| 4 | 同步后端代码（zip 0.93 MB） + venv + 装依赖 | ✅ 4 关键依赖 OK |
| 5 | 写 `.env` + 16 张表 `Base.metadata.create_all` + 跑 0002 SQL | ✅ |
| 6 | 写 `xincetong-api.service` + 启服务 | ✅ pid 95747 |
| 7 | 首次健康检查 | ❌ SSL error 500 |
| 8 | `.env` 加 `?ssl=disable` + restart | ✅ 4 URL 全 200 |
| 9 | 跑 6 个 seed 脚本 | ✅ 180 规则 + 6 产品 + 10 银行 |

---

## 三、关键 Bug 修复（Bug Investigation skill）

### Bug 1：旧部署混乱（多 u / SQLite / 旧 systemd / 旧 nginx）

- **现象**：xincetong.cn 跑的是 Vercel 风格的旧版
- **根因**：Vercel → CVM 迁移只完成"装 nginx + 跑通 sqlite 后端"3 步，PG/新 unit/新 .env 全没做
- **修复**：方案 A（备份 + 重做）

### Bug 2：PG 15+ `permission denied for schema public`

- **现象**：`alembic upgrade head` → `InsufficientPrivilegeError`
- **根因**：PG 15+ 默认 `public` schema 不允许普通用户建表
- **修复**：
  ```sql
  GRANT ALL ON SCHEMA public TO xincetong;
  ALTER SCHEMA public OWNER TO xincetong;
  GRANT CREATE ON SCHEMA public TO xincetong;
  ```

### Bug 3：本地 PG 不支持 SSL 连接

- **现象**：`/api/site/config 500` + `ConnectionError: PostgreSQL server rejected SSL upgrade`
- **根因**：`app/database.py:88-92` 自动给 PG dsn 拼 `ssl=require`，但本地 PG `pg_hba.conf` 没配 hostssl
- **修复**：`.env` 的 `DATABASE_URL` 加 `?ssl=disable`

### Bug 4：`alembic/versions/` 是空的

- **现象**：`alembic upgrade head` 跑完没建任何业务表
- **根因**：v11 不用 alembic，靠 `init_db()` 自动建表。但 `init_db()` 对**非 SQLite** 不做 `create_all`（line 109-117）
- **修复**：写 `init_pg_tables.py` 手动 `Base.metadata.create_all` + 跑 `0002_business_dimensions.sql`

### Bug 5：`init.sql` 是 MySQL 语法

- **现象**：`mysql < sql/init.sql` 在 PG 跑不了（`` ` `` 引用 + `ENGINE=InnoDB`）
- **根因**：v11 之前只在 MySQL 测试过
- **修复**：用 ORM `Base.metadata.create_all` 代替 init.sql

### Bug 6：`upload_to_cvm.sh` password 分支又 read 一次密码

- **现象**：IDE 跑 upload_to_cvm.sh 时在 line 88 又弹密码输入
- **根因**：分支 else 里写 `read -s` 而 `CVM_PASS` 已在前面设好
- **修复**：去掉重复 read，直接 `SSHPASS="$CVM_PASS" sshpass -e scp ...`

---

## 四、最终健康检查（2026-09-14 18:52）

| URL | 内部（127.0.0.1） | 公网（xincetong.cn） |
|---|---|---|
| `/` | - | ✅ 200（web SPA） |
| `/h5/` | - | ✅ 200（H5 SPA） |
| `/health` | ✅ 200 | - |
| `/api/site/config` | ✅ 200 | ✅ 200 |
| `/api/banks` | ✅ 200 | ✅ 200 |
| `/api/banks/ICBC/products` | ✅ 200 | - |

---

## 五、数据库状态

| 表 | 行数 | 备注 |
|---|---|---|
| banks | 10 | 工商银行、建设银行、... |
| bank_products | 14 | - |
| product_types | 6 | 优质单位贷 / 公积金贷 / 工薪贷 / 有房客户贷 / 纳税贷 / 开票贷 |
| scorecard_rules | 180 | 94 基础 + 51 business v4 + 35 business v5 |
| validation_rules | 12 | - |
| site_config | 19 | number 8 + text 7 + compliance 4 |
| assessments | 0 | 等用户提交 |
| users | 0 | 等用户登录 |

---

## 六、部署产物

| 文件 | 位置 | 用途 |
|---|---|---|
| 部署 zip | `dist/xincetong-cvm-deploy-20260914-1847.zip`（0.93 MB） | 2026-09-14 部署用 |
| 后端代码 | `/opt/xincetong/` | 跑 v11 FastAPI |
| 前端 web | `/var/www/xincetong/` | nginx 80 serve |
| 前端 h5 | `/var/www/xincetong/h5/` | nginx /h5/ serve |
| 旧部署备份 | `/opt/xinceutong.bak.20260914/`（104M） | rollback 用，30 天后自动清 |
| systemd unit | `/etc/systemd/system/xincetong-api.service` | 后端守护 |
| nginx conf | `/etc/nginx/conf.d/xincetong.conf` | 80 端口 |
| 日志 | `/var/log/xincetong/{api.log, api.err, nginx.*.log}` | - |
| 完整 doc | `DEPLOY_CVM_FINAL.md`（workspace 根） | 运维手册 |
| 部署报告 | `verify-report-2026-09-14-cvm-deploy.md`（本文件） | 部署验证 |

---

## 七、用户待办

1. **`/opt/xincetong/.env` 必填**：
   - `WECHAT_APPID`（从微信公众平台拿）
   - `WECHAT_SECRET`（从微信公众平台拿）
   - 缺了 → 微信登录不可用
2. **可选**：
   - `WECHAT_MCH_ID` / `WECHAT_PAY_KEY`（开微信支付）
   - `DEEPSEEK_API_KEY`（开 AI 顾问）
3. **运维建议**：
   - 加 crontab 自动备份 DB（见 `DEPLOY_CVM_FINAL.md` § 9.3）
   - `certbot --nginx` 上 HTTPS
   - 重启 nginx 用 `systemctl` 而非旧 master 进程

---

**作者**：CodeBuddy 2026-09-14 18:55
**部署时长**：17 分钟（备份 2 分钟 + PG 5 分钟 + 部署 7 分钟 + seed 1 分钟 + 修 bug 2 分钟）
**最终状态**：✅ 4 公网 URL 全 200 + DB 16 表 + 180 规则 + 10 银行就绪
