# 信测通 v11 部署文档（腾讯云 CVM）

> 本文档说明如何把本地代码部署到生产 CVM（`82.156.166.188`，域名 `xincetong.cn`）。
> 不依赖 GitHub Actions / Vercel / Render，**纯本地直传**。

---

## 1. 环境信息

| 项 | 值 |
|---|---|
| CVM IP | `82.156.166.188`（公网） |
| 系统 | TencentOS Server 4（CentOS 兼容） |
| 用户 | `root` |
| 域名 | `xincetong.cn`（CN 域名，已 ICP 备案） |
| 后端端口 | `8000`（uvicorn） |
| Web 静态 | `/var/www/xincetong/`（nginx 反代到 80/443） |
| 后端代码 | `/opt/xincetong/`（systemd unit: `xincetong-api`） |
| 数据库 | PostgreSQL（自建，yum 安装） |
| 鉴权 | ssh key（推荐） / 密码（备用） |

---

## 2. 首次部署（环境搭建）

### 2.1 CVM 端预装
```bash
ssh root@82.156.166.188
yum install -y python3.11 python3.11-devel postgresql postgresql-server nginx git zip rsync
postgresql-setup initdb
systemctl enable --now postgresql
sudo -u postgres psql -c "CREATE DATABASE xincetong;"
sudo -u postgres psql -c "CREATE USER xincetong WITH PASSWORD '你的密码';"
sudo -u postgres psql -c "GRANT ALL ON DATABASE xincetong TO xincetong;"
```

### 2.2 nginx 配置（`/etc/nginx/conf.d/xincetong.conf`）
```nginx
server {
    listen 80;
    server_name xincetong.cn www.xincetong.cn;

    root /var/www/xincetong;
    index index.html;

    location /h5/ {
        alias /var/www/xincetong/h5/;
        try_files $uri $uri/ /h5/index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / { try_files $uri $uri/ /index.html; }
}
```

### 2.3 首次上传
```bash
# Mac 端
cd /Users/suntata/CodeBuddy/20260907155240
python3 scripts/build_deploy_zip.py    # 打包 → dist/...
bash scripts/upload_to_cvm.sh dist/xincetong-cvm-deploy-*.zip
```

### 2.4 配置 `.env`（**首次必须手动**）
```bash
ssh root@82.156.166.188
vim /opt/xincetong/.env
```
填入：
```
DATABASE_URL=postgresql+asyncpg://xincetong:你的密码@localhost/xincetong
JWT_SECRET=随机长字符串
API_BASE_URL=https://xincetong.cn
WECHAT_APPID=...
WECHAT_SECRET=...
```
然后：
```bash
cd /opt/xincetong
source .venv/bin/activate
alembic upgrade head
systemctl restart xincetong-api
```

---

## 3. 日常部署（代码更新）

```bash
# Mac 端
cd /Users/suntata/CodeBuddy/20260907155240
python3 scripts/build_deploy_zip.py
bash scripts/upload_to_cvm.sh dist/xincetong-cvm-deploy-*.zip
```

整个流程 **3-5 分钟**（含 npm build + 依赖更新 + 重启）。

---

## 4. 数据库迁移

```bash
# 1) 写新迁移文件到 xincetong-server/sql/migrations/0003_xxx.sql
# 2) 打包上传
python3 scripts/build_deploy_zip.py
bash scripts/upload_to_cvm.sh dist/...zip
# 3) CVM 端手动跑迁移
ssh root@82.156.166.188
cd /opt/xincetong
psql "$DATABASE_URL" -f sql/migrations/0003_xxx.sql
systemctl restart xincetong-api
```

---

## 5. 故障排查

### 5.1 后端 502 / 启动失败
```bash
ssh root@82.156.166.188
systemctl status xincetong-api
journalctl -u xincetong-api -n 100
tail -100 /opt/xincetong/logs/error.log
```

### 5.2 依赖冲突
```bash
ssh root@82.156.166.188
cd /opt/xincetong
source .venv/bin/activate
pip install -r sql/migrations/requirements.txt --force-reinstall
systemctl restart xincetong-api
```

### 5.3 静态资源 404
```bash
ls -la /var/www/xincetong/        # web 产物
ls -la /var/www/xincetong/h5/     # h5 产物
nginx -t && systemctl reload nginx
```

### 5.4 数据库连接失败
```bash
sudo -u postgres psql -c "\l"
cat /opt/xincetong/.env | grep DATABASE_URL
```

### 5.5 端口占用
```bash
lsof -i :8000    # 后端
lsof -i :80      # nginx
ss -tlnp
```

### 5.6 滚回上一版
```bash
ssh root@82.156.166.188
cd /opt/xincetong
# 找上一版 zip（保留最近 5 个）
ls -lt /tmp/xincetong-cvm-deploy-*.zip
# 重新部署旧版
bash /tmp/cvm_deploy.sh /tmp/xincetong-cvm-deploy-20260914-1200.zip
```

---

## 6. SSH Key 推荐配置（免密部署）

```bash
# Mac 端生成（如果还没有）
ls ~/.ssh/id_rsa.pub || ssh-keygen -t rsa -b 4096

# 推到 CVM
ssh-copy-id -p 22 root@82.156.166.188

# 验证
ssh root@82.156.166.188 "echo OK"
```

之后 `upload_to_cvm.sh` 自动检测 key 鉴权，不再要密码。

---

## 7. v11 升级内容

| 维度 | v9 → v11 |
|---|---|
| 字体 | web 端 Noto Serif SC / Sans SC / JetBrains Mono → **苹果系统栈**（-apple-system / PingFang SC / Songti SC） |
| 额度 | "X.X 万"（带小数）→ **"50,000 元"**（纯元数 + 3 位千分位） |
| 评估路由 | 通用 6 大产品模型 → **按 bank_code 走 bank_scorecard.py**（10 家银行差异化评分） |
| 部署 | GitHub + Vercel + Render → **本地直传 CVM**（`upload_to_cvm.sh`） |
| 字体范围 | 仅 web 端改（miniapp 已是苹果字体栈） |

详细 changelog 见 `verify-report-2026-09-14-v11-font-credit-bank.md`。
