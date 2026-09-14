"""
信测通 v11 CVM 部署打包脚本（纯 stdlib，不依赖 fastapi/sqlalchemy）

打包内容：
  - xincetong-server/  （后端源码，排除 .env / __pycache__ / *.db / .venv / logs）
  - xincetong-web/dist/  （Vite build 后的静态产物，npm run build 现场跑）
  - xincetong-miniapp/dist/build/h5/  （H5 构建产物，npm run build:h5 现场跑，可选）
  - scripts/cvm_deploy.sh  （CVM 端部署脚本）
  - DEPLOY_CVM.md         （部署文档）

排除规则：
  - node_modules / dist（除 web 和 miniapp 的 dist） / unpackage / .vercel
  - __pycache__ / .venv / venv / .env / *.db / *.sqlite
  - .DS_Store / Thumbs.db / .git / .idea / .vscode
  - logs/（运行时生成）
  - *.log

用法：
  cd /Users/suntata/CodeBuddy/20260907155240
  python3 scripts/build_deploy_zip.py

输出：
  ./dist/xincetong-cvm-deploy-YYYYMMDD-HHMM.zip  （一般 3-5 MB）

下一步：
  bash scripts/upload_to_cvm.sh dist/xincetong-cvm-deploy-YYYYMMDD-HHMM.zip
"""
import os
import sys
import zipfile
import fnmatch
import subprocess
from pathlib import Path
from datetime import datetime


# ===== 配置 =====
ROOT = Path("/Users/suntata/CodeBuddy/20260907155240")
DIST_DIR = ROOT / "dist"
TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M")
OUTPUT_ZIP = DIST_DIR / f"xincetong-cvm-deploy-{TIMESTAMP}.zip"
TIMESTAMP_FILE = "BUILD_INFO.txt"

# 排除规则（支持 glob）
EXCLUDE_PATTERNS = [
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
    # 旧部署包
    "**/xincetong-v*.zip",
    "**/xincetong-deploy*.zip",
    "**/xincetong-cvm-deploy*.zip",
    "**/deploy-report-*.md",
    "**/verify-report-*.md",
    "**/report-*.md",
    # 备份/测试产物
    "**/*.bak",
    "**/*.tmp",
    "**/.legacy-config/**",
]

# 顶层要打包的目录/文件（白名单）
INCLUDE_TOP = [
    "xincetong-server",
    "scripts",
    "DEPLOY_CVM.md",
    "README.md",
]


def should_exclude(rel_path: str) -> bool:
    """判断相对路径是否应排除"""
    p = rel_path.replace(os.sep, "/")
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(p, pat):
            return True
    return False


def collect_files():
    """收集所有要打包的文件"""
    files = []
    total_size = 0

    for entry in INCLUDE_TOP:
        src = ROOT / entry
        if not src.exists():
            print(f"  [SKIP] 不存在: {entry}")
            continue

        if src.is_file():
            rel = entry
            if not should_exclude(rel):
                sz = src.stat().st_size
                files.append((rel, str(src), sz))
                total_size += sz
        else:
            for path in src.rglob("*"):
                if path.is_file():
                    rel = str(path.relative_to(ROOT))
                    if should_exclude(rel):
                        continue
                    sz = path.stat().st_size
                    if sz > 50 * 1024 * 1024:
                        print(f"  [SKIP] 过大文件 ({sz/1024/1024:.1f}MB): {rel}")
                        continue
                    files.append((rel, str(path), sz))
                    total_size += sz

    return files, total_size


def run_build_step(name, cmd, cwd):
    """跑一个 build 步骤（不抛错，失败只警告）"""
    print(f"\n==> 1.{name} build: {cmd} (cwd={cwd.name})")
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            print(f"  ✅ {name} build 成功")
        else:
            print(f"  ⚠️  {name} build 失败 (rc={result.returncode})")
            print(f"  stdout: {result.stdout[-500:]}")
            print(f"  stderr: {result.stderr[-500:]}")
        return result.returncode == 0
    except Exception as e:
        print(f"  ⚠️  {name} build 异常: {e}")
        return False


def collect_built_files(label, src_dir, arc_prefix):
    """收集 build 后的产物到 zip 暂存目录"""
    if not src_dir.exists():
        print(f"  [SKIP] {label} build 产物不存在: {src_dir}")
        return [], 0
    files = []
    total_size = 0
    for path in src_dir.rglob("*"):
        if path.is_file():
            rel_under = str(path.relative_to(src_dir))
            arc_name = f"{arc_prefix}/{rel_under}"
            sz = path.stat().st_size
            if sz > 50 * 1024 * 1024:
                continue
            files.append((arc_name, str(path), sz))
            total_size += sz
    print(f"  ✅ {label} 产物 {len(files)} 文件，{total_size/1024/1024:.2f} MB")
    return files, total_size


def build_zip():
    """执行打包"""
    print(f"\n{'='*60}")
    print(f"信测通 v11 CVM 部署打包")
    print(f"{'='*60}\n")
    print(f"源目录: {ROOT}")
    print(f"输出:   {OUTPUT_ZIP}\n")

    DIST_DIR.mkdir(exist_ok=True)

    # 1. Web 前端 build
    run_build_step(
        "web (vite)",
        "npm run build 2>&1 | tail -20",
        ROOT / "xincetong-web",
    )

    # 2. Miniapp H5 build（可选，失败不阻塞）
    run_build_step(
        "miniapp-h5 (uni)",
        "npm run build:h5 2>&1 | tail -20",
        ROOT / "xincetong-miniapp",
    )

    # 3. 收集源码
    print(f"\n==> 2. 收集后端源码...")
    source_files, source_size = collect_files()
    print(f"  ✅ {len(source_files)} 文件，{source_size/1024/1024:.2f} MB")

    # 4. 收集 web dist
    print(f"\n==> 3. 收集 web 静态产物...")
    web_files, web_size = collect_built_files(
        "web dist",
        ROOT / "xincetong-web" / "dist",
        "xincetong-web-dist",
    )

    # 5. 收集 miniapp h5 dist
    print(f"\n==> 4. 收集 miniapp h5 产物...")
    miniapp_h5 = ROOT / "xincetong-miniapp" / "dist" / "build" / "h5"
    miniapp_files, miniapp_size = collect_built_files(
        "miniapp h5",
        miniapp_h5,
        "xincetong-miniapp-h5",
    )

    # 6. 合并所有文件
    all_files = source_files + web_files + miniapp_files
    total_size = source_size + web_size + miniapp_size
    print(f"\n==> 5. 合并: 共 {len(all_files)} 文件，{total_size/1024/1024:.2f} MB")

    # 7. 写 zip
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    build_info = (
        f"信测通 v11 CVM 部署包\n"
        f"构建时间: {ts}\n"
        f"文件数:   {len(all_files)}\n"
        f"大小:     {total_size/1024/1024:.2f} MB\n"
        f"\n"
        f"v11 升级内容:\n"
        f"  - 字体: 苹果系统字体栈（web 端删 Google Fonts）\n"
        f"  - 额度: 纯元数 + 3 位千分位 + 元（去掉 X.X 万）\n"
        f"  - 评估: 前端传 bank_code 触发 bank_scorecard.py 10 家银行差异化评分\n"
        f"  - 部署: 本地 Mac 直传 CVM (82.156.166.188)，不走 GHA/Vercel\n"
        f"\n"
        f"部署步骤见 DEPLOY_CVM.md\n"
    )

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr(TIMESTAMP_FILE, build_info)
        for i, (arc, abs_path, sz) in enumerate(all_files, 1):
            zf.write(abs_path, arcname=arc)
            if i % 50 == 0 or i == len(all_files):
                print(f"  [{i:4d}/{len(all_files)}] {arc}  ({sz/1024:.1f} KB)")

    final_size = OUTPUT_ZIP.stat().st_size
    print(f"\n{'='*60}")
    print(f"✅ 打包完成: {OUTPUT_ZIP}")
    print(f"   压缩前: {total_size/1024/1024:.2f} MB")
    print(f"   压缩后: {final_size/1024/1024:.2f} MB")
    print(f"   压缩率: {(1 - final_size/total_size)*100:.1f}%")
    print(f"{'='*60}\n")

    if final_size > 100 * 1024 * 1024:
        print(f"⚠️  警告：包大于 100MB，建议改用 catbox 中转")
    else:
        print(f"包较小（< 100MB），可直接 scp 上传。\n")

    print(f"下一步：")
    print(f"  bash scripts/upload_to_cvm.sh {OUTPUT_ZIP.name}\n")


if __name__ == "__main__":
    try:
        build_zip()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 打包失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
