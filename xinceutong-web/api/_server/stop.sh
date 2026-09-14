#!/bin/bash
# 停服脚本
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "停 uvicorn..."
pkill -f "uvicorn app.main:app" 2>/dev/null

echo "停 H5 dev server..."
pkill -f "uni" 2>/dev/null
pkill -f "vite" 2>/dev/null

# 兜底：按端口
kill -9 $(lsof -ti:8000) 2>/dev/null
kill -9 $(lsof -ti:5173) 2>/dev/null

echo "✅ 已停"
