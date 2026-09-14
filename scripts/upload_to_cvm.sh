#!/bin/bash
###############################################################################
# 信测通 v11 - Mac 本地上传部署包到 CVM
#
# 用法：
#   bash scripts/upload_to_cvm.sh dist/xincetong-cvm-deploy-20260914-1530.zip
#
# 流程：
#   1. scp 上传 zip 到 CVM /tmp/
#   2. scp 上传 cvm_deploy.sh 到 CVM /tmp/
#   3. ssh 到 CVM 执行部署
#   4. 实时回显日志
#
# 鉴权：
#   - 优先用 ssh key（推荐：ssh-copy-id root@82.156.166.188）
#   - 备用：交互式输入密码（用 expect 或 sshpass）
###############################################################################

set -e

ZIP_FILE=$1
CVM_IP="82.156.166.188"
CVM_USER="root"
CVM_PORT=22

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$ZIP_FILE" ] || [ ! -f "$ZIP_FILE" ]; then
  echo -e "${RED}❌ 用法：$0 /path/to/zip${NC}"
  echo "  示例：$0 dist/xincetong-cvm-deploy-20260914-1530.zip"
  echo ""
  echo "  如果还没打包，请先跑："
  echo "    python3 scripts/build_deploy_zip.py"
  exit 1
fi

ZIP_NAME=$(basename "$ZIP_FILE")
ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)

echo -e "${GREEN}==== 信测通 v11 - CVM 上传部署 ===="
echo -e "  CVM:    ssh://$CVM_USER@$CVM_IP:$CVM_PORT"
echo -e "  Zip:    $ZIP_FILE ($ZIP_SIZE)"
echo -e "  时间:   $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "===================================${NC}\n"

# 1) 检测 SSH 鉴权方式
echo "==> 1) 检测 SSH 鉴权..."

SSH_AUTH_METHOD="key"
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 -p $CVM_PORT $CVM_USER@$CVM_IP "echo 'SSH KEY OK'" 2>/dev/null; then
  SSH_AUTH_METHOD="password"
  echo -e "  ${YELLOW}⚠️  未检测到免密 key，将使用密码鉴权${NC}"

  # 检测 sshpass
  if ! command -v sshpass &> /dev/null; then
    echo -e "  ${RED}❌ 未安装 sshpass${NC}"
    echo "  安装方法（任选一）："
    echo "    brew install sshpass"
    echo "    或：用 expect（macOS 自带）"
    echo "    或：手动复制（见下方说明）"
    echo ""
    echo "  手动部署步骤："
    echo "    scp $ZIP_FILE $CVM_USER@$CVM_IP:/tmp/"
    echo "    scp scripts/cvm_deploy.sh $CVM_USER@$CVM_IP:/tmp/"
    echo "    ssh $CVM_USER@$CVM_IP 'bash /tmp/cvm_deploy.sh /tmp/$ZIP_NAME'"
    exit 1
  fi
fi

# 2) 上传 zip
echo -e "\n==> 2) 上传 zip 到 /tmp/$ZIP_NAME ..."
if [ "$SSH_AUTH_METHOD" = "key" ]; then
  scp -P $CVM_PORT "$ZIP_FILE" $CVM_USER@$CVM_IP:/tmp/$ZIP_NAME
else
  read -s -p "  请输入 CVM root 密码：" CVM_PASS
  echo ""
  SSHPASS=$CVM_PASS sshpass -e scp -P $CVM_PORT "$ZIP_FILE" $CVM_USER@$CVM_IP:/tmp/$ZIP_NAME
fi
echo "  ✅ zip 上传完成"

# 3) 上传 cvm_deploy.sh
echo -e "\n==> 3) 上传 cvm_deploy.sh 到 /tmp/ ..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$SSH_AUTH_METHOD" = "key" ]; then
  scp -P $CVM_PORT "$SCRIPT_DIR/cvm_deploy.sh" $CVM_USER@$CVM_IP:/tmp/cvm_deploy.sh
else
  SSHPASS=$CVM_PASS sshpass -e scp -P $CVM_PORT "$SCRIPT_DIR/cvm_deploy.sh" $CVM_USER@$CVM_IP:/tmp/cvm_deploy.sh
fi
echo "  ✅ 脚本上传完成"

# 4) 远程执行部署
echo -e "\n==> 4) 远程执行部署（实时回显）..."
echo -e "  ${YELLOW}提示：部署约需 30-60 秒（含依赖更新）${NC}\n"

if [ "$SSH_AUTH_METHOD" = "key" ]; then
  ssh -p $CVM_PORT $CVM_USER@$CVM_IP "bash /tmp/cvm_deploy.sh /tmp/$ZIP_NAME"
else
  SSHPASS=$CVM_PASS sshpass -e ssh -p $CVM_PORT $CVM_USER@$CVM_IP "bash /tmp/cvm_deploy.sh /tmp/$ZIP_NAME"
fi

# 5) 验证域名
echo -e "\n==> 5) 域名验证..."
sleep 2
DOMAIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://xincetong.cn/ 2>/dev/null || echo "000")
API_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://xincetong.cn/api/site/config 2>/dev/null || echo "000")
echo "  http://xincetong.cn/             HTTP $DOMAIN_CODE"
echo "  http://xincetong.cn/api/...      HTTP $API_CODE"

echo -e "\n${GREEN}================================="
echo -e "✅ 全流程完成！"
echo -e "  生产地址：http://xincetong.cn"
echo -e "  API 文档：暂无（FastAPI 自动生成 /docs 可访问）"
echo -e "  运维命令："
echo -e "    ssh $CVM_USER@$CVM_IP 'systemctl status xincetong-api'"
echo -e "    ssh $CVM_USER@$CVM_IP 'tail -f /opt/xincetong/logs/error.log'"
echo -e "=================================${NC}\n"
