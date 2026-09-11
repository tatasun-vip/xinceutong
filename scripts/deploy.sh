#!/bin/bash
###############################################################################
# 信测通 - 一键部署助手
# 用法：
#   1. 解压 xinceutong-deploy.zip 后进入 xinceutong-deploy/ 目录
#   2. 编辑本文件，填入 GITHUB_USER / REPO_NAME / GITHUB_TOKEN
#   3. 运行：bash scripts/deploy.sh
###############################################################################

set -e

# ============ 在此填入你的 GitHub 信息 ============
GITHUB_USER=""        # 例如：suntata
REPO_NAME=""          # 例如：xinceutong
GITHUB_TOKEN=""       # https://github.com/settings/tokens （需要 repo 权限）
# ==============================================

if [ -z "$GITHUB_USER" ] || [ -z "$REPO_NAME" ] || [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ 请先编辑本脚本，填入 GITHUB_USER / REPO_NAME / GITHUB_TOKEN"
  echo "   GitHub Token 获取：https://github.com/settings/tokens"
  exit 1
fi

echo "==== 1. 初始化 git 仓库 ===="
if [ ! -d ".git" ]; then
  git init
  git config user.email "deploy@xinceutong.local"
  git config user.name "xinceutong-deploy"
fi

echo "==== 2. 添加并提交所有文件 ===="
git add .
git commit -m "feat: 信测通完整代码 + Render 一键部署" || echo "  (无新改动)"

echo "==== 3. 推送到 GitHub ===="
git remote remove origin 2>/dev/null || true
git remote add origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git branch -M main
git push -u origin main

echo ""
echo "============================================="
echo "✅ 代码已推送到 GitHub："
echo "   https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo ""
echo "==== 下一步：Render 一键部署 ===="
echo "  1. 用 GitHub 账号登录 https://render.com"
echo "  2. 点 New → Blueprint"
echo "  3. 选 ${GITHUB_USER}/${REPO_NAME} 仓库"
echo "  4. 点 Apply，等 5-8 分钟"
echo ""
echo "==== 部署完后会拿到 2 个 URL ===="
echo "  后端 API: https://xinceutong-api.onrender.com"
echo "  前端 H5:  https://xinceutong-web.onrender.com"
echo "============================================="
