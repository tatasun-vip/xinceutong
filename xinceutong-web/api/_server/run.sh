#!/bin/bash
# 信测通本地开发启动脚本（SQLite + 无 Redis 模式，零依赖）
# 用法：./run.sh
# 停止：./stop.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# 兜底清掉旧进程
kill -9 $(lsof -ti:8000) 2>/dev/null || true
kill -9 $(lsof -ti:5173) 2>/dev/null || true

mkdir -p logs

# ===================== 0. venv =====================
if [ ! -d ".venv" ]; then
  echo "[0/5] 创建 venv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "[0/5] python=$(python --version 2>&1)"

# ===================== 1. deps =====================
echo "[1/5] 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "  依赖装好"

# ===================== 2. 启动后端 (SQLite + 无 Redis) =====================
echo "[2/5] 启动 FastAPI (端口 8000)..."
export REDIS_DISABLED=1
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/server.log 2>&1 &
SERVER_PID=$!
echo "  server pid=$SERVER_PID"

# 等待启动
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "  [OK] 后端 /health 200"
    break
  fi
  sleep 1
done

# ===================== 3. 跑 3 个 init 脚本 =====================
echo "[3/5] 跑 3 个 init 脚本..."
cd "$ROOT"
# 用 -m 模式运行（脚本目录是 cwd），保证能 import app
export PYTHONPATH="$ROOT"
python -m scripts.init_product_types 2>&1 | tail -3
python -m scripts.init_site_config 2>&1 | tail -3
python -m scripts.init_scorecard 2>&1 | tail -3

# ===================== 4. 验证后端 =====================
echo "[4/5] 验证后端 API..."
curl -s http://127.0.0.1:8000/ | head -c 200; echo
curl -s http://127.0.0.1:8000/api/product-types | head -c 200; echo
curl -s http://127.0.0.1:8000/api/site/config | head -c 200; echo

# ===================== 5. 启动 H5 dev server (5173) =====================
echo "[5/5] 启动 H5 dev server (端口 5173)..."
cd "$ROOT/../xinceutong-miniapp"
if [ ! -d "node_modules" ]; then
  echo "  安装前端依赖..."
  npm install --silent
fi
nohup npm run dev:h5 > "$ROOT/logs/h5.log" 2>&1 &
H5_PID=$!
echo "  h5 pid=$H5_PID"

# 等待启动
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  if curl -sf http://127.0.0.1:5173 > /dev/null 2>&1; then
    echo "  [OK] H5 dev server /5173 200"
    break
  fi
  sleep 1
done

# ===================== 总结 =====================
echo "============================================"
echo "[ALL] 全部就绪 ✅"
echo "  - 后端:    http://127.0.0.1:8000"
echo "  - API 文档: http://127.0.0.1:8000/docs"
echo "  - H5:      http://127.0.0.1:5173"
echo "  - 日志:    $ROOT/logs/{server,h5}.log"
echo "============================================"
echo "  进程: $SERVER_PID (server) / $H5_PID (h5)"
echo "  停服: ./stop.sh"
