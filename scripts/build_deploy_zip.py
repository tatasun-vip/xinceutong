"""
信测通 v5 P0 部署打包脚本（纯 stdlib，不依赖 fastapi/sqlalchemy）

打包内容：
  - xinceutong-server/  （后端，排除 .env / __pycache__ / *.db / .venv）
  - xinceutong-miniapp/ （前端，排除 node_modules / dist / unpackage）
  - xinceutong-web/     （Web 子项目，排除同上）
  - sql/migrations/     （0002 迁移）
  - verify-report-2026-09-12-v5-business.md
  - DEPLOY.md / VERCEL_DEPLOY.md / README.md

排除规则：
  - node_modules / dist / .vercel / .next / build / coverage
  - __pycache__ / .venv / venv / .env / *.db / *.sqlite
  - .DS_Store / Thumbs.db / .git / .idea / .vscode
  - logs/（运行时生成）
  - miniprogram_npm/（小程序构建产物）

用法：
  cd /Users/suntata/CodeBuddy/20260907155240
  python3 scripts/build_deploy_zip.py

输出：
  ./xinceutong-v5.zip  （一般 3-5 MB）
"""
import os
import sys
import zipfile
import fnmatch
from pathlib import Path
from datetime import datetime


# ===== 配置 =====
ROOT = Path("/Users/suntata/CodeBuddy/20260907155240")
OUTPUT_ZIP = ROOT / "xinceutong-v5.zip"
TIMESTAMP_FILE = "BUILD_INFO.txt"

# 排除规则（支持 glob）
EXCLUDE_PATTERNS = [
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/.next/**",
    "**/.vercel/**",
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
    "**/xinceutong-v5.zip",
    "**/xinceutong-deploy.zip",
    "**/deploy-report-*.md",
    "**/verify-report-*.md",   # 报告不进 zip（单独上 Git）
    "**/report-*.md",
]

# 顶层要打包的目录/文件（白名单模式，安全性更高）
INCLUDE_TOP = [
    "xinceutong-server",
    "xinceutong-miniapp",
    "xinceutong-web",
    "sql",
    "api",
    "scripts",
    "DEPLOY.md",
    "VERCEL_DEPLOY.md",
    "README.md",
    "vercel.json",
    "render.yaml",
    "package.json",
    "package-lock.json",
]


def should_exclude(rel_path: str) -> bool:
    """判断相对路径是否应排除"""
    # 统一用正斜杠
    p = rel_path.replace(os.sep, "/")
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(p, pat):
            return True
    # 单文件大小超 50MB 跳过（node_modules 大文件残留）
    return False


def collect_files():
    """收集所有要打包的文件，返回 (rel_path, abs_path, size) 列表"""
    files = []
    total_size = 0

    for entry in INCLUDE_TOP:
        src = ROOT / entry
        if not src.exists():
            print(f"  [SKIP] 不存在: {entry}")
            continue

        if src.is_file():
            rel = entry
            sz = src.stat().st_size
            if not should_exclude(rel):
                files.append((rel, str(src), sz))
                total_size += sz
        else:
            # 目录递归
            for path in src.rglob("*"):
                if path.is_file():
                    rel = str(path.relative_to(ROOT))
                    if should_exclude(rel):
                        continue
                    sz = path.stat().st_size
                    # 跳过 > 50MB 单文件
                    if sz > 50 * 1024 * 1024:
                        print(f"  [SKIP] 过大文件 ({sz/1024/1024:.1f}MB): {rel}")
                        continue
                    files.append((rel, str(path), sz))
                    total_size += sz

    return files, total_size


def build_zip():
    """执行打包"""
    print(f"\n{'='*60}")
    print(f"信测通 v5 P0 部署打包")
    print(f"{'='*60}\n")
    print(f"源目录: {ROOT}")
    print(f"输出:   {OUTPUT_ZIP}\n")

    if not ROOT.exists():
        print(f"❌ 源目录不存在: {ROOT}")
        sys.exit(1)

    files, total_size = collect_files()
    print(f"已收集 {len(files)} 个文件，总大小 {total_size/1024/1024:.2f} MB\n")

    # 写入时间戳
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    build_info = (
        f"信测通 v5 P0 部署包\n"
        f"构建时间: {ts}\n"
        f"文件数:   {len(files)}\n"
        f"大小:     {total_size/1024/1024:.2f} MB\n"
        f"\n"
        f"升级内容:\n"
        f"  - business 类型录入从 7 字段扩到 15 字段\n"
        f"  - 4 维度加权（法人 30% + 企业 40% + 合规 20% + 行业 10%）\n"
        f"  - 5 条一票否决（compliance_risk 4 + biz_overdue_2y 1）\n"
        f"  - personal 流程完全不受影响\n"
        f"\n"
        f"部署步骤见 verify-report-2026-09-12-v5-business.md\n"
    )

    # 删除旧 zip
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()
        print(f"已删除旧 zip: {OUTPUT_ZIP.name}\n")

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        # 1. 写 BUILD_INFO.txt 到 zip 根
        zf.writestr(TIMESTAMP_FILE, build_info)
        print(f"  [+ ] {TIMESTAMP_FILE}")

        # 2. 写所有源文件
        for i, (rel, abs_path, sz) in enumerate(files, 1):
            arcname = rel
            zf.write(abs_path, arcname=arcname)
            if i % 50 == 0 or i == len(files):
                print(f"  [{i:4d}/{len(files)}] {arcname}  ({sz/1024:.1f} KB)")

    final_size = OUTPUT_ZIP.stat().st_size
    print(f"\n{'='*60}")
    print(f"✅ 打包完成: {OUTPUT_ZIP}")
    print(f"   压缩前: {total_size/1024/1024:.2f} MB")
    print(f"   压缩后: {final_size/1024/1024:.2f} MB")
    print(f"   压缩率: {(1 - final_size/total_size)*100:.1f}%")
    print(f"{'='*60}\n")

    # catbox.moe 限制 200MB，肯定够
    if final_size > 100 * 1024 * 1024:
        print(f"⚠️  警告：包大于 100MB，catbox.moe 可能限制，建议分卷")

    print(f"下一步：运行上传脚本")
    print(f"  python3 scripts/upload_to_catbox.py\n")


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
