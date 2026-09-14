"""
信测通 SSOT 部署包打包脚本

**重要约定（2026-09-14 立）**：
  - 这台 Mac 上的 `/Users/suntata/CodeBuddy/20260907155240/dist/xincetong-ssot-*.zip`
    是**唯一可信源（Single Source of Truth）**。
  - 以后所有改动 → 在这个 zip 解压出的源码上做 → 改完**重新跑这个脚本打新 zip**。
  - CVM 部署时只解这个 zip（不直接编辑 CVM 上代码，避免漂移）。

打包内容：
  - xincetong-server/      （后端 FastAPI 源码，含 SQL migrations + init 脚本）
  - xincetong-miniapp/     （uni-app 前端源码，H5 + 小程序双端）
  - xincetong-web/         （Vue3 + Vite 桌面端源码）
  - scripts/               （部署/打包/上传脚本）
  - DEPLOY_CVM.md / README.md  （文档）
  - package.json           （根 npm scripts：dev/build/deploy）
  - 已构建产物 web dist + miniapp H5 dist（可选；方便纯部署不解源码）

排除：
  - node_modules / .venv / __pycache__ / *.db / *.pyc / .DS_Store
  - dist/ 里此脚本之前打的旧 zip（避免自包含）
  - 所有 verify-report-*.md（运行时报告不放包）
  - 备份 .bak / .tmp

用法：
  cd /Users/suntata/CodeBuddy/20260907155240
  python3 scripts/build_ssot_zip.py            # 默认：打 SSOT 包（源码 + 已构建产物）
  python3 scripts/build_ssot_zip.py --src-only  # 只源码不打前端构建（更快）

输出：
  ./dist/xincetong-ssot-YYYYMMDD-HHMM.zip       （约 5-15 MB）

下一步：
  bash scripts/upload_to_cvm.sh dist/xincetong-ssot-YYYYMMDD-HHMM.zip
"""
import os
import sys
import argparse
import zipfile
import fnmatch
import subprocess
from pathlib import Path
from datetime import datetime


# ===== 配置 =====
ROOT = Path("/Users/suntata/CodeBuddy/20260907155240")
DIST_DIR = ROOT / "dist"

# 排除规则（支持 glob，** 匹配任意层级）
EXCLUDE_PATTERNS = [
    # 通用
    "**/node_modules/**",
    "**/__pycache__/**",
    "**/.venv/**",
    "**/venv/**",
    "**/.env",
    "**/.env.*",
    "**/*.db",
    "**/*.sqlite",
    "**/*.sqlite3",
    "**/.DS_Store",
    "**/Thumbs.db",
    "**/.git/**",
    "**/.idea/**",
    "**/.vscode/**",
    "**/logs/**",
    "**/miniprogram_npm/**",
    "**/unpackage/**",
    "**/coverage/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.pyd",
    "**/.mypy_cache/**",
    "**/.pytest_cache/**",
    "**/.ruff_cache/**",
    "**/*.log",
    # 旧部署包 / 自身
    "**/xincetong-v*.zip",
    "**/xincetong-deploy*.zip",
    "**/xincetong-cvm-deploy*.zip",
    "**/xincetong-ssot-*.zip",
    # 运行时报告 / 备份
    "**/verify-report-*.md",
    "**/report-*.md",
    "**/deploy-report-*.md",
    "**/*.bak",
    "**/*.tmp",
    "**/.legacy-config/**",
    # 浏览器自动化（万一有）
    "**/.playwright/**",
    "**/playwright-report/**",
    "**/test-results/**",
]

# 顶层白名单（要打进 zip 的目录/文件）
INCLUDE_TOP = [
    "xincetong-server",
    "xincetong-miniapp",
    "xincetong-web",
    "scripts",
    "DEPLOY_CVM.md",
    "DEPLOY_CVM_FINAL.md",
    "README.md",
    "package.json",
    "package-lock.json",
    ".gitignore",
    ".env.example",
]

# 单文件大小上限
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def should_exclude(rel_path: str) -> bool:
    """判断相对路径是否应排除"""
    p = rel_path.replace(os.sep, "/")
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(p, pat):
            return True
    return False


def collect_files(label: str, paths: list[str]) -> tuple[list, int]:
    """收集白名单文件"""
    files = []
    total_size = 0
    skipped = 0
    for entry in paths:
        src = ROOT / entry
        if not src.exists():
            print(f"  [SKIP] 不存在: {entry}")
            continue

        if src.is_file():
            rel = entry
            if should_exclude(rel):
                skipped += 1
                continue
            sz = src.stat().st_size
            if sz > MAX_FILE_SIZE:
                print(f"  [SKIP] 过大 ({sz/1024/1024:.1f}MB): {rel}")
                skipped += 1
                continue
            files.append((rel, str(src), sz))
            total_size += sz
        else:
            for path in src.rglob("*"):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(ROOT))
                if should_exclude(rel):
                    skipped += 1
                    continue
                sz = path.stat().st_size
                if sz > MAX_FILE_SIZE:
                    print(f"  [SKIP] 过大 ({sz/1024/1024:.1f}MB): {rel}")
                    skipped += 1
                    continue
                files.append((rel, str(path), sz))
                total_size += sz

    print(f"  ✅ {label}: {len(files)} 文件 / 跳过 {skipped} / 共 {total_size/1024/1024:.2f} MB")
    return files, total_size


def run_build_step(name: str, cmd: str, cwd: Path) -> bool:
    """跑一个 build 步骤"""
    print(f"\n  ==> {name} build: {cmd} (cwd={cwd.name})")
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode == 0:
            print(f"     ✅ 成功")
            return True
        else:
            print(f"     ⚠️  失败 (rc={result.returncode})")
            print(f"     stdout tail: {result.stdout[-300:]}")
            print(f"     stderr tail: {result.stderr[-300:]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"     ⚠️  超时 (10 分钟)")
        return False
    except Exception as e:
        print(f"     ⚠️  异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="信测通 SSOT 部署包打包")
    parser.add_argument("--src-only", action="store_true", help="只打源码，不跑前端 build")
    parser.add_argument("--no-build", action="store_true", help="跳过所有 build 步骤")
    args = parser.parse_args()

    ts_file = datetime.now().strftime("%Y%m%d-%H%M")
    output_zip = DIST_DIR / f"xincetong-ssot-{ts_file}.zip"

    print(f"\n{'='*64}")
    print(f"信测通 SSOT 部署包 v12 (含 v9 P0 证据链 + v11 字体/银行 + v10 tax/invoice)")
    print(f"{'='*64}")
    print(f"源目录:  {ROOT}")
    print(f"输出:    {output_zip}")
    print(f"模式:    {'源码 only' if args.src_only else '源码 + 前端 build'}")
    print(f"{'='*64}\n")

    DIST_DIR.mkdir(exist_ok=True)

    # 1. 前端构建（可选）
    if not args.src_only and not args.no_build:
        print("==> 步骤 1/3: 前端构建")
        run_build_step(
            "web (vite)",
            "npm run build 2>&1 | tail -10",
            ROOT / "xincetong-web",
        )
        run_build_step(
            "miniapp-h5 (uni)",
            "npx uni build -p h5 2>&1 | tail -10",
            ROOT / "xincetong-miniapp",
        )
    else:
        print("==> 跳过前端构建\n")

    # 2. 收集源码
    print("\n==> 步骤 2/3: 收集源码 + 配置 + 文档")
    source_files, source_size = collect_files("白名单文件", INCLUDE_TOP)

    # 3. 合并写 zip
    print(f"\n==> 步骤 3/3: 写入 zip")
    if output_zip.exists():
        output_zip.unlink()

    ts_human = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    build_info = f"""信测通 SSOT 部署包 (Single Source of Truth)
==============================================

构建时间: {ts_human}
文件数:   {len(source_files)}
大小:     {source_size/1024/1024:.2f} MB (压缩前)

═══════════════════════════════════════════════════════════════
⚠️  重要约定 (2026-09-14 立)
═══════════════════════════════════════════════════════════════
这是**唯一可信源**。以后所有改动:
  1. 解压本 zip → 修改源码
  2. 改完跑: python3 scripts/build_ssot_zip.py
  3. 用新 zip 部署: bash scripts/upload_to_cvm.sh <新 zip>
  4. 不要再直接编辑 CVM 上代码（会漂移）

═══════════════════════════════════════════════════════════════
版本要点
═══════════════════════════════════════════════════════════════
v9  P0 6 大产品独立证据链 (hit_rules / low_rules / improve_vars
    / realistic_limit_min / realistic_limit_max / not_recommend_reason)
v10 个人/企业流程都返回 6 卡 (tax/invoice 无数据时 E 兜底)
v11 苹果系统字体 + 纯元 + 银行差异化评分 (10 家银行 bank_scorecard)
v12 移动端 H5 入口页 v9 金色 banner + 6 卡配色 (manifest base /h5/)

═══════════════════════════════════════════════════════════════
目录结构
═══════════════════════════════════════════════════════════════
xincetong-server/       FastAPI 后端 (含 alembic + 7 init 脚本)
xincetong-miniapp/      uni-app 前端 (H5 + 小程序, 已含已构建 dist)
xincetong-web/          Vue3 + Vite 桌面端 (已含已构建 dist)
scripts/                部署/打包/上传脚本
DEPLOY_CVM.md           部署文档

═══════════════════════════════════════════════════════════════
部署步骤
═══════════════════════════════════════════════════════════════
  cd <解压目录>
  bash scripts/cvm_deploy.sh                # 走 catbox 中转
  # 或
  bash scripts/upload_to_cvm.sh xincetong-ssot-*.zip  # 走 scp 直传

CVM 端: 腾讯云 BF1 / 82.156.166.188 / TencentOS 4
  - /opt/xincetong/        部署目录
  - /var/www/xincetong/    nginx 前端静态目录
  - PostgreSQL 15          本地库 xincetong (用户 xincetong)
  - systemd                xincetong-api.service (绑 127.0.0.1:8000)

═══════════════════════════════════════════════════════════════
URL
═══════════════════════════════════════════════════════════════
  https://xincetong.cn/                   官网（待 ICP 备案）
  https://xincetong.cn/h5/                H5 评估入口（v9 金色 banner）
  https://xincetong.cn/api/assessment/    后端 API
"""

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("BUILD_INFO.txt", build_info)
        for i, (arc, abs_path, sz) in enumerate(source_files, 1):
            zf.write(abs_path, arcname=arc)
            if i % 100 == 0 or i == len(source_files):
                print(f"  [{i:4d}/{len(source_files)}] {arc} ({sz/1024:.1f} KB)")

    final_size = output_zip.stat().st_size

    # 清理旧 SSOT zip（保留最近 5 个）
    ssot_zips = sorted(DIST_DIR.glob("xincetong-ssot-*.zip"), key=lambda p: p.stat().st_mtime)
    if len(ssot_zips) > 5:
        for old in ssot_zips[:-5]:
            print(f"  [CLEAN] 清理旧包: {old.name}")
            old.unlink()

    print(f"\n{'='*64}")
    print(f"✅ SSOT 打包完成")
    print(f"   路径:   {output_zip}")
    print(f"   压缩前: {source_size/1024/1024:.2f} MB")
    print(f"   压缩后: {final_size/1024/1024:.2f} MB")
    print(f"   压缩率: {(1 - final_size/source_size)*100:.1f}%" if source_size else "")
    print(f"{'='*64}\n")

    if final_size > 100 * 1024 * 1024:
        print(f"⚠️  包 > 100MB，建议用 catbox 中转 (scripts/upload_to_catbox.py)")
    else:
        print(f"✅ 包 < 100MB，可直接 scp 上传")

    print(f"\n下一步:")
    print(f"  bash scripts/upload_to_cvm.sh {output_zip.name}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
