# 信测通（xincetong）CVM 部署总结

> **版本**：v11 终极版
> **部署时间**：2026-09-14 18:51
> **目标**：把"以前杂乱的"一次性清掉，让 CVM 跑一份干净、可维护、有备份的 v11。
> **不再依赖** Vercel / Render / GitHub Actions / Vercel-dns hash CNAME。

---

## § 0 Bug 排查：旧 CVM 部署为什么"以前很乱"

按 Bug Investigation skill 流程定位。

### 现象
- 访问 `xincetong.cn` 看到的是 Vercel 风格的旧版（多 u 命名 + SQLite + 旧 systemd + 旧 nginx）
- 端口 8000 旧 uvicorn 一直在跑，但**没人记得为啥**
- 项目名一会儿 `xinceutong`（多 u）一会儿 `xincetong`（少 u），两边并存
- 域名 `xincetong.cn` → 82.156.166.188 解析正常，**但不知道是谁部署的**

### 复现
```bash
nslookup xincetong.cn → 82.156.166.188
curl -I http://xincetong.cn → 200（来自 xinceutong.conf）
cat /etc/nginx/conf.d/xinceutong.conf | grep proxy_pass → http://127.0.0.1:8000
ls -l /proc/<pid>/cwd → /opt/xinceutong/api/_server
cat /opt/xinceutong/.env | grep DATABASE_URL → 留空（走 SQLite）
ss -tlnp | grep 8000 → 旧 uvicorn 占着
```

### 假设与验证
| 假设 | 验证 | 结果 |
|---|---|---|
| H1: Vercel → CVM 迁移没做完 | 看 systemd + /opt | ✅ 只做了"装 nginx"+"跑通 sqlite 后端"，PG / 新 unit 全没做 |
| H2: 2 套并行的"xinceutong" | 看 .env + 路径 | ✅ `xinceutong`（多 u，Vercel 旧版）+ `xincetong`（少 u，本地新版）并存 |
| H3: 数据从 SQLite → PG 没迁 | 看 db + DATABASE_URL | ✅ 旧 db 4MB，新 unit 不存在 |
| H4: 域名被人偷偷用过 | 看 nginx conf | ✅ `xinceutong.conf` 是 default_server，`server_name _` |

### 根因
**位置**：`/opt/xinceutong/api/_server/`（旧后端）+ `xinceutong-backend.service`（旧 unit）+ `xinceutong.conf`（旧 nginx）
**原因**：从 Vercel 迁移到 CVM 时只完成"开通 CVM + 装 nginx + 把 Vercel 版本 scp 过来"3 步，**PG / 新 unit / 新 .env / 数据迁移 / 域名切换**全没做。

### 修复方案
**方案 A：就地升级**（用户已选，2026-09-14 执行）
1. 旧 `/opt/xinceutong/` 整体备份到 `/opt/xinceutong.bak.20260914/`（rollback 用）
2. 装 PostgreSQL + 创 `xincetong` 库 + 用户
3. 部署 v11 代码到 `/opt/xincetong/`（少 u，**新目录**）
4. 写 `xincetong-api.service`（少 u，新 unit），关掉旧 `xinceutong-backend.service`（多 u）
5. 写 `xincetong.conf`（少 u，新 conf），移走旧 conf
6. 起新服务 + 健康检查

---

## § 1 部署概览

| 项 | 值 |
|---|---|
| CVM IP | `82.156.166.188`（公网） |
| 系统 | TencentOS Server 4（CentOS 兼容） |
| 用户 | `root` |
| 域名 | `xincetong.cn`（已 ICP 备案） |
| 后端 systemd | `xincetong-api.service`（`/etc/systemd/system/`） |
| 后端端口 | `8000`（systemd 绑 `127.0.0.1:8000`） |
| 后端代码 | `/opt/xincetong/` |
| 前端 Web | `/var/www/xincetong/`（nginx 80） |
| 前端 H5 | `/var/www/xincetong/h5/` |
| 数据库 | PostgreSQL 15（`postgresql-15`）`127.0.0.1:5432` |
| 库名 | `xincetong`（用户 `xincetong`） |
| 备份 | `/opt/xinceutong.bak.20260914/`（104M，30 天后自动清） |
| 日志 | `/var/log/xincetong/{api.log, api.err, nginx.*.log}` |
| 部署 zip | `dist/xincetong-cvm-deploy-<时间戳>.zip`（本机 `scripts/build_deploy_zip.py` 打包） |

---

## § 2 一次性清理旧部署（已完成 2026-09-14）

```bash
# 1) 备份（rollback 用，30 天后自动清）
mkdir -p /opt/xinceutong.bak.20260914/{systemd,nginx}
rsync -a /opt/xinceutong/ /opt/xinceutong.bak.20260914/root/
cp /etc/systemd/system/xinceutong-backend.service /opt/xinceutong.bak.20260914/systemd/
cp /etc/nginx/conf.d/xinceutong*.conf /opt/xinceutong.bak.20260914/nginx/

# 2) 停旧服务
kill 73833                              # 旧 uvicorn
systemctl stop xinceutong-backend.service
systemctl disable xinceutong-backend.service

# 3) 移走旧 systemd + nginx conf（不删，备份到 .moved-20260914 后缀）
mv /etc/systemd/system/xinceutong-backend.service \
   /opt/xinceutong.bak.20260914/systemd/xinceutong-backend.service.moved-20260914
mv /etc/nginx/conf.d/xinceutong.conf \
   /opt/xinceutong.bak.20260914/nginx/xinceutong.conf.moved-20260914
mv /etc/nginx/conf.d/xinceutong-h5.conf \
   /opt/xinceutong.bak.20260914/nginx/xinceutong-h5.conf.moved-20260914

systemctl daemon-reload
```

---

## § 3 装 PostgreSQL

```bash
yum install -y postgresql postgresql-server
postgresql-setup initdb
systemctl enable --now postgresql
sudo -u postgres psql -c "SELECT version();"
```

### § 3.1 创库 + 用户（PG 15+ 必须显式 GRANT）

```bash
DB_PASS="Xincetong2026!"
sudo -u postgres psql <<EOF
CREATE DATABASE xincetong;
CREATE USER xincetong WITH PASSWORD '$DB_PASS';
GRANT ALL PRIVILEGES ON DATABASE xincetong TO xincetong;
ALTER USER xincetong CREATEDB;  -- alembic 需要
GRANT ALL ON SCHEMA public TO xincetong;       -- PG 15+ 必需
ALTER SCHEMA public OWNER TO xincetong;        -- PG 15+ 必需
ALTER DATABASE xincetong OWNER TO xincetong;
GRANT CREATE ON SCHEMA public TO xincetong;    -- 保险
EOF
```

### § 3.2 允许密码连接

```bash
# /var/lib/pgsql/data/pg_hba.conf 改 IPv4 local 为 md5
sed -i 's|host    all             all             127.0.0.1/32.*|host    all             all             127.0.0.1/32            md5|' /var/lib/pgsql/data/pg_hba.conf
sed -i 's|host    all             all             ::1/128.*|host    all             all             ::1/128                 md5|' /var/lib/pgsql/data/pg_hba.conf
systemctl restart postgresql
PGPASSWORD="$DB_PASS" psql -h 127.0.0.1 -U xincetong -d xincetong -c "SELECT 1;"
```

---

## § 4 部署后端

### § 4.1 同步代码（从 Mac → CVM）

```bash
# 在 Mac 端：
cd /Users/suntata/CodeBuddy/20260907155240
python3 scripts/build_deploy_zip.py    # 打 dist/xincetong-cvm-deploy-<时间>.zip
# 用 sshpass 传（upload_to_cvm.sh 有 bug 时手动）：
SSHPASS='D.6JV4;Hn{mt(S' sshpass -e scp -o StrictHostKeyChecking=accept-new \
  dist/xincetong-cvm-deploy-*.zip root@82.156.166.188:/tmp/
```

### § 4.2 解压 + 同步 + venv

```bash
# 在 CVM 端：
unzip -q -o /tmp/xincetong-cvm-deploy.zip -d /tmp/xincetong-new/
mkdir -p /opt/xincetong /opt/xincetong/logs /var/log/xincetong
rsync -a /tmp/xincetong-new/xincetong-server/ /opt/xincetong/

cd /opt/xincetong
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt
deactivate
```

### § 4.3 写 `.env`

```ini
DATABASE_URL=postgresql+asyncpg://xincetong:Xincetong2026!@127.0.0.1:5432/xincetong?ssl=disable
JWT_SECRET=<openssl rand -hex 32>
WECHAT_APPID=<用户填>
WECHAT_SECRET=<用户填>
CORS_ORIGINS=["https://xincetong.cn","https://www.xincetong.cn"]
ENV=production
LOG_LEVEL=INFO
# ... 其他字段见 app/config.py
```

**关键点**：`DATABASE_URL` **必须**带 `?ssl=disable`（本地 PG 不支持 SSL，database.py 88-92 会自动追加 `ssl=require` 但 `ssl=` 已存在时**不**追加）。

### § 4.4 建表（**不用 alembic**！v11 用 `Base.metadata.create_all`）

```bash
cd /opt/xincetong
source .venv/bin/activate

# 写临时 init 脚本
cat > init_pg_tables.py <<'PY'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base
from app import models  # noqa: F401
async def main():
    engine = create_async_engine("postgresql+asyncpg://xincetong:Xincetong2026!@127.0.0.1:5432/xincetong")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("✅ 所有表已建")
asyncio.run(main())
PY
python init_pg_tables.py
rm init_pg_tables.py

# 跑 0002 SQL（幂等，加 dimensions JSONB 列 + 索引）
PGPASSWORD="Xincetong2026!" psql -h 127.0.0.1 -U xincetong -d xincetong \
  -f /opt/xincetong/sql/migrations/0002_business_dimensions.sql
deactivate
```

**为什么不用 alembic**：`alembic/versions/` 是空的（只有 `.gitkeep`），v11 靠 `init_db()` 自动建表。**`init_db()` 对非 SQLite 数据库不做 `create_all`**，所以**首次部署**要手动 `Base.metadata.create_all`。

### § 4.5 Seed 数据（6 个 init 脚本）

```bash
cd /opt/xincetong
source .venv/bin/activate
export PYTHONPATH=/opt/xincetong
export REDIS_DISABLED=1

for s in init_product_types init_site_config init_scorecard \
         init_business_rules init_business_v5_rules seed_banks; do
  echo "==> $s"
  python -m scripts.$s 2>&1 | tail -3
done
deactivate
```

**结果**：
- 6 大产品类型
- 180 条评分卡规则（含 51 条 business v4 + 35 条 business v5 + 94 条基础）
- 12 条 validation_rules + 5 条一票否决
- 19 条 site_config（number/text/compliance 三类）
- 10 家银行 + 50 条 schema + 14 款产品

### § 4.6 systemd unit

`/etc/systemd/system/xincetong-api.service`：
```ini
[Unit]
Description=Xincetong API (FastAPI + uvicorn)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/xincetong
Environment="PATH=/opt/xincetong/.venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/xincetong/.env
ExecStart=/opt/xincetong/.venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 --workers 2 --log-level info
Restart=always
RestartSec=5
StandardOutput=append:/var/log/xincetong/api.log
StandardError=append:/var/log/xincetong/api.err

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable xincetong-api
systemctl start xincetong-api
```

---

## § 5 部署前端

```bash
mkdir -p /var/www/xincetong/h5
rm -rf /var/www/xincetong/*
cp -r /tmp/xincetong-new/xincetong-web-dist/. /var/www/xincetong/
cp -r /tmp/xincetong-new/xincetong-miniapp-h5/. /var/www/xincetong/h5/
```

---

## § 6 nginx 配置

`/etc/nginx/conf.d/xincetong.conf`（**完整见 CVM 端**）：
```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name xincetong.cn www.xincetong.cn _;

    access_log /var/log/xincetong/nginx.access.log;
    error_log /var/log/xincetong/nginx.error.log;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript
              text/javascript application/xml image/svg+xml;
    gzip_min_length 1000;

    # 银行 logo
    location ^~ /static/banks/ { alias /var/www/xincetong/banks/; expires 30d; try_files $request_uri =404; }
    location ^~ /banks-logo/  { alias /var/www/xincetong/banks/; expires 30d; try_files $request_uri =404; }

    # H5 静态
    location ^~ /h5/assets/ { alias /var/www/xincetong/h5/assets/; expires 7d; try_files $request_uri =404; }
    location /h5/ { alias /var/www/xincetong/h5/; index index.html; try_files $uri /h5/index.html; }
    location = /h5 { return 301 /h5/; }

    # API 反代
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # 健康检查
    location = /health { proxy_pass http://127.0.0.1:8000/health; }

    # SPA
    location / { root /var/www/xincetong; index index.html; try_files $uri /index.html; }
}
```

```bash
nginx -t
systemctl reload nginx
```

---

## § 7 日常部署（从 Mac 跑）

```bash
cd /Users/suntata/CodeBuddy/20260907155240
python3 scripts/build_deploy_zip.py
SSHPASS='<密码>' sshpass -e scp -o StrictHostKeyChecking=accept-new \
  dist/xincetong-cvm-deploy-*.zip root@82.156.166.188:/tmp/

ssh root@82.156.166.188 <<'BASH'
unzip -q -o /tmp/xincetong-cvm-deploy.zip -d /tmp/xincetong-new/
rsync -a /tmp/xincetong-new/xincetong-server/ /opt/xincetong/
rsync -a /tmp/xincetong-new/xincetong-web-dist/. /var/www/xincetong/
rsync -a --delete /tmp/xincetong-new/xincetong-web-dist/ /var/www/xincetong/
rsync -a --delete /tmp/xincetong-new/xincetong-miniapp-h5/ /var/www/xincetong/h5/
systemctl restart xincetong-api
systemctl reload nginx
curl -s -o /dev/null -w "/api/site/config → %{http_code}\n" http://xincetong.cn/api/site/config
BASH
```

---

## § 8 故障排查

| 现象 | 排查 |
|---|---|
| 502 Bad Gateway | `systemctl status xincetong-api` + `tail /var/log/xincetong/api.err` |
| `Permission denied: schema public` | `GRANT ALL ON SCHEMA public TO xincetong;`（PG 15+ 必需） |
| `ConnectionError: SSL upgrade` | `.env` 的 DATABASE_URL 加 `?ssl=disable` |
| `/api/site/config 500` + DB error | `PGPASSWORD=... psql -h 127.0.0.1 -U xincetong -d xincetong -c "SELECT 1;"` |
| 端口 8000 被占 | `ss -tlnp \| grep 8000` + `kill <pid>` |
| 静态 404 | `ls /var/www/xincetong/` + `nginx -t && systemctl reload nginx` |
| 滚回旧版 | `ls /opt/xinceutong.bak.*` + 把 `.moved-20260914` 还原 |

---

## § 9 运维手册

### § 9.1 重启 / 启停

```bash
# 后端
systemctl restart xincetong-api
systemctl status xincetong-api --no-pager -l

# nginx
nginx -t && systemctl reload nginx

# PostgreSQL
systemctl restart postgresql
```

### § 9.2 实时日志

```bash
journalctl -u xincetong-api -f                 # systemd 日志
tail -f /var/log/xincetong/api.err             # stderr
tail -f /var/log/xincetong/api.log             # stdout
tail -f /var/log/xincetong/nginx.access.log    # nginx 访问
```

### § 9.3 备份策略（建议加 crontab）

```bash
# /etc/crontab 末尾加：
# 每天 3 点备份 DB 到 /root/backups/，保留 7 天
0 3 * * * /usr/bin/pg_dump -U xincetong -h 127.0.0.1 xincetong | gzip > /root/backups/xincetong-db-$(date +\%Y\%m\%d).sql.gz
0 4 * * * find /root/backups/ -name "xincetong-db-*.sql.gz" -mtime +7 -delete

# 30 天后清旧部署备份
0 5 1 * * find /opt -maxdepth 1 -name "xinceutong.bak.*" -mtime +30 -exec rm -rf {} \;
```

### § 9.4 升级步骤

```bash
# 1) 拉新代码（git pull 或重新打 zip）
# 2) 重 build 前端（如改 web/miniapp）
# 3) 重打包 + 传 + 同步（同 § 7）
# 4) 如果有 SQL 迁移：
PGPASSWORD="Xincetong2026!" psql -h 127.0.0.1 -U xincetong -d xincetong \
  -f /opt/xincetong/sql/migrations/0003_xxx.sql
# 5) restart
systemctl restart xincetong-api
```

---

## § 10 验证清单（2026-09-14 18:51 实际跑过）

- [x] PG 装好（`SELECT version() → PostgreSQL 15.19`）
- [x] DB 创好（`\l` 看到 `xincetong`）
- [x] 表建好（16 张：assessments/banks/bank_products/product_types/...）
- [x] 数据 seed（180 规则 + 6 产品 + 10 银行 + 19 site_config）
- [x] systemd active（`xincetong-api.service running`）
- [x] 端口 8000 监听
- [x] 端口 80 监听（nginx）
- [x] 端口 5432 监听（postgres）
- [x] `/api/site/config 200`（公网）
- [x] `/api/banks 200`（10 家银行）
- [x] `/api/banks/ICBC/products 200`
- [x] `/health 200`
- [x] `/ 200`（web SPA）
- [x] `/h5/ 200`（miniapp H5）
- [x] 旧 conf 全部移走（`/etc/nginx/conf.d/` 只有 `xincetong.conf` + 2 个旧 backup）
- [x] 旧 systemd unit 移走（`xinceutong-backend.service.moved-20260914`）
- [x] 旧部署备份完整（104M，3 个子目录：root/systemd/nginx）

---

## § 11 待办

1. **用户必填**：
   - `/opt/xincetong/.env` 的 `WECHAT_APPID` / `WECHAT_SECRET`（从微信公众平台拿，缺了微信登录不可用）
   - `/opt/xincetong/.env` 的 `WECHAT_MCH_ID` / `WECHAT_PAY_KEY`（如果要开支付）

2. **运维建议**（非紧急）：
   - 加 crontab 自动备份 DB（见 § 9.3）
   - 加 certbot HTTPS（`yum install certbot && certbot --nginx -d xincetong.cn`）
   - 装 `nginx.service` 而不是用旧 master 进程（之前 `systemctl reload nginx` 失败，但 master 在跑，**功能 OK** 但**不优雅**）

3. **代码层**：
   - `app/database.py:88-92` 的 SSL 自动加 logic 应**尊重** `ssl=disable`（现在是 `if "ssl=" not in dsn` 已经尊重，但需要注释清楚）
   - 缺一个 `app/migrate.py` 把 `alembic/versions/` 用代码写好（现在用 `Base.metadata.create_all` 兜底）
   - `init.sql` 还是 MySQL 语法，应改成 PG 兼容

4. **清理**（按 memory 79184157 规则，待用户确认）：
   - 本机 `dist/xincetong-cvm-deploy-*.zip` 旧包（保留 7 天回滚）
   - 本机 `xincetong-miniapp/h5-build.zip` 旧包
   - 本机 `verify-report-2026-09-14-v5-*.md` / `v6-*.md` / `v7-*.md` 旧报告
   - `DEPLOY_CVM.md`（被 `DEPLOY_CVM_FINAL.md` 替代）

---

**作者**：CodeBuddy 2026-09-14
**关联**：verify-report-2026-09-14-cvm-deploy.md
