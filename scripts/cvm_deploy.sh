#!/bin/bash
###############################################################################
# 信测通 v11 CVM 端部署脚本
#
# 用法（在 CVM 上跑）：
#   bash /tmp/cvm_deploy.sh /tmp/xincetong-cvm-deploy-YYYYMMDD-HHMM.zip
#
# 流程：
#   1. 解压 zip 到 /tmp/xincetong-new/
#   2. 同步后端代码到 /opt/xincetong/（保留 .env / venv / logs）
#   3. 同步 web 静态到 /var/www/xincetong/
#   4. 同步 h5 静态到 /var/www/xincetong/h5/
#   5. 重启 systemd 服务 xincetong-api
#   6. 重载 nginx
#   7. 健康检查
###############################################################################

set -e

ZIP_FILE=$1
CVM_IP="82.156.166.188"
APP_DIR="/opt/xincetong"
WEB_DIR="/var/www/xincetong"
BACKEND_PORT=8000

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$ZIP_FILE" ] || [ ! -f "$ZIP_FILE" ]; then
  echo -e "${RED}❌ 用法：$0 /path/to/zip${NC}"
  echo "  示例：$0 /tmp/xincetong-cvm-deploy-20260914-1530.zip"
  exit 1
fi

echo -e "${GREEN}==== 信测通 CVM 部署（v11）===="
echo -e "  CVM IP:  $CVM_IP"
echo -e "  后端:    $APP_DIR (端口 $BACKEND_PORT)"
echo -e "  Web:     $WEB_DIR"
echo -e "  Zip:     $ZIP_FILE"
echo -e "  时间:    $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "=================================${NC}\n"

# 1) 解压
echo "==> 1) 解压 zip..."
rm -rf /tmp/xincetong-new
mkdir -p /tmp/xincetong-new
unzip -q -o "$ZIP_FILE" -d /tmp/xincetong-new/
echo "  ✅ 解压完成"

# 2) 部署后端
echo -e "\n==> 2) 同步后端代码到 $APP_DIR ..."
mkdir -p "$APP_DIR" "$APP_DIR/logs"
mkdir -p /var/www

# 首次部署：建 venv
if [ ! -d "$APP_DIR/.venv" ]; then
  echo "  首次部署：创建 venv..."
  if ! command -v python3.10 &> /dev/null && ! command -v python3.11 &> /dev/null; then
    echo -e "  ${YELLOW}⚠️  未检测到 Python 3.10+，尝试 python3${NC}"
  fi
  PYTHON_BIN=$(command -v python3.10 || command -v python3.11 || command -v python3)
  $PYTHON_BIN -m venv "$APP_DIR/.venv"
  source "$APP_DIR/.venv/bin/activate"
  pip install --upgrade pip -q
  if [ -f /tmp/xincetong-new/xincetong-server/requirements.txt ]; then
    pip install -r /tmp/xincetong-new/xincetong-server/requirements.txt -q
  fi
  echo "  ✅ venv 创建完成"
else
  echo "  增量部署：更新依赖..."
  source "$APP_DIR/.venv/bin/activate"
  if [ -f /tmp/xincetong-new/xincetong-server/requirements.txt ]; then
    pip install -r /tmp/xincetong-new/xincetong-server/requirements.txt -q
  fi
fi

# 同步代码（保留 .env / venv / logs / *.db）
rsync -a --delete \
  --exclude='.venv' \
  --exclude='.env' \
  --exclude='logs' \
  --exclude='*.db' \
  --exclude='*.sqlite' \
  --exclude='__pycache__' \
  /tmp/xincetong-new/xincetong-server/ "$APP_DIR/"
echo "  ✅ 后端代码同步完成"

# 检查 .env（首次部署要新建）
if [ ! -f "$APP_DIR/.env" ]; then
  if [ -f "$APP_DIR/.env.example" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    echo -e "  ${YELLOW}⚠️  首次部署：已从 .env.example 创建 .env，请手动编辑填入真实配置${NC}"
  else
    echo -e "  ${RED}❌ .env 不存在且无 .env.example，请手动创建${NC}"
  fi
fi

# 3) 部署 web 静态
echo -e "\n==> 3) 同步 web 静态到 $WEB_DIR ..."
mkdir -p "$WEB_DIR"
if [ -d /tmp/xincetong-new/xincetong-web-dist ]; then
  rm -rf "$WEB_DIR"/*
  cp -r /tmp/xincetong-new/xincetong-web-dist/. "$WEB_DIR/"
  echo "  ✅ web 静态部署完成"
else
  echo -e "  ${YELLOW}⚠️  无 web 静态产物${NC}"
fi

# 4) 部署 miniapp h5
echo -e "\n==> 4) 同步 miniapp h5 到 $WEB_DIR/h5/ ..."
if [ -d /tmp/xincetong-new/xincetong-miniapp-h5 ]; then
  mkdir -p "$WEB_DIR/h5"
  rm -rf "$WEB_DIR/h5"/*
  cp -r /tmp/xincetong-new/xincetong-miniapp-h5/. "$WEB_DIR/h5/"
  echo "  ✅ miniapp h5 部署完成"
else
  echo "  (跳过：本次无 h5 产物)"
fi

# 5) 重启后端
echo -e "\n==> 5) 重启后端服务..."
if systemctl is-active --quiet xincetong-api 2>/dev/null; then
  systemctl restart xincetong-api
  echo "  ✅ systemd 重启完成"
elif [ -f /etc/init.d/xincetong-api ]; then
  /etc/init.d/xincetong-api restart
  echo "  ✅ init.d 重启完成"
else
  echo "  首次部署：创建 systemd unit..."
  cat > /etc/systemd/system/xincetong-api.service <<EOF
[Unit]
Description=Xincetong API (FastAPI + uvicorn)
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --workers 2
Restart=always
RestartSec=5
StandardOutput=append:$APP_DIR/logs/access.log
StandardError=append:$APP_DIR/logs/error.log

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable xincetong-api
  systemctl start xincetong-api
  echo "  ✅ systemd unit 创建并启动"
fi

# 等服务起来
echo "  等待服务就绪..."
sleep 3
for i in 1 2 3 4 5; do
  if curl -s -o /dev/null -w "" http://localhost:$BACKEND_PORT/api/site/config 2>/dev/null; then
    echo "  ✅ 后端就绪"
    break
  fi
  if [ $i -eq 5 ]; then
    echo -e "  ${RED}❌ 后端 5 次健康检查失败，查看日志：${NC}"
    echo "    tail -50 $APP_DIR/logs/error.log"
    echo "    journalctl -u xincetong-api -n 50"
  fi
  sleep 2
done

# 6) 重载 nginx
echo -e "\n==> 6) 重载 nginx..."
if command -v nginx &> /dev/null; then
  if nginx -t 2>&1 | grep -q "successful"; then
    systemctl reload nginx 2>/dev/null || nginx -s reload
    echo "  ✅ nginx reload 完成"
  else
    echo -e "  ${RED}❌ nginx 配置有误，请检查 /etc/nginx/conf.d/xincetong.conf${NC}"
    nginx -t
  fi
else
  echo "  (跳过：未安装 nginx)"
fi

# 7) 健康检查
echo -e "\n==> 7) 健康检查..."
sleep 1
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$BACKEND_PORT/api/site/config 2>/dev/null || echo "000")
WEB_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")
H5_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/h5/ 2>/dev/null || echo "000")

echo "  后端 API:  HTTP $BACKEND_CODE  (http://localhost:$BACKEND_PORT)"
echo "  Web 静态:  HTTP $WEB_CODE     (http://localhost/)"
echo "  H5 静态:   HTTP $H5_CODE      (http://localhost/h5/)"

# 8) 清理
echo -e "\n==> 8) 清理临时文件..."
rm -rf /tmp/xincetong-new
echo "  ✅ 清理完成"

echo -e "\n${GREEN}================================="
echo -e "✅ 部署完成！"
echo -e "  域名：   http://xincetong.cn"
echo -e "  后端：   http://82.156.166.188:$BACKEND_PORT"
echo -e "  日志：   tail -f $APP_DIR/logs/error.log"
echo -e "  状态：   systemctl status xincetong-api"
echo -e "=================================${NC}\n"
