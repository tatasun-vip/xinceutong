"""
信测通 v5 P0 部署包上传脚本（纯 stdlib urllib）

上传到 catbox.moe / 0x0.st / file.io（按优先级 fallback）。
24h 有效（catbox）/ 1h 有效（0x0.st）/ 一次性（file.io）。

用法：
  cd /Users/suntata/CodeBuddy/20260907155240
  python3 scripts/upload_to_catbox.py

输出：URL + 服务器 wget 一行命令（直接复制粘贴）
"""
import os
import sys
import json
import mimetypes
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

ROOT = Path("/Users/suntata/CodeBuddy/20260907155240")
ZIP_FILE = ROOT / "xinceutong-v5.zip"

# 按优先级排序的临时文件空间
ENDPOINTS = [
    {
        "name": "litter.catbox.moe",
        "url": "https://litter.catbox.moe/resources/internals/api.php",
        "type": "catbox",
        "expire": "24h",
    },
    {
        "name": "catbox.moe 主站",
        "url": "https://catbox.moe/user/api.php",
        "type": "catbox",
        "expire": "24h",
    },
    {
        "name": "0x0.st",
        "url": "https://0x0.st",
        "type": "0x0st",
        "expire": "1h（仅应急）",
    },
]


def make_multipart(file_path: Path, field_name: str, extra_fields: dict | None = None):
    """构造 multipart/form-data（纯 stdlib）"""
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    parts: list[bytes] = []
    extra_fields = extra_fields or {}

    # 额外字段
    for k, v in extra_fields.items():
        parts.append(f"--{boundary}".encode())
        parts.append(f'Content-Disposition: form-data; name="{k}"'.encode())
        parts.append(b"")
        parts.append(v.encode() if isinstance(v, str) else v)

    # 文件字段
    mime, _ = mimetypes.guess_type(str(file_path))
    mime = mime or "application/zip"
    parts.append(f"--{boundary}".encode())
    parts.append(
        f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"'.encode()
    )
    parts.append(f"Content-Type: {mime}".encode())
    parts.append(b"")
    parts.append(file_path.read_bytes())

    parts.append(f"--{boundary}--".encode())
    parts.append(b"")

    body = b"\r\n".join(parts)
    return body, f"multipart/form-data; boundary={boundary}"


def upload_catbox(file_path: Path, endpoint_url: str) -> str | None:
    """catbox.moe 系列（返回纯文本 URL）"""
    body, ct = make_multipart(file_path, "fileToUpload", {"reqtype": "fileupload"})
    req = urllib.request.Request(
        endpoint_url,
        data=body,
        headers={"Content-Type": ct, "User-Agent": "xinceutong-deploy/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode("utf-8", errors="replace").strip()
    return text if text.startswith("http") else None


def upload_0x0st(file_path: Path) -> str | None:
    """0x0.st（POST 整个 body 即可）"""
    with open(file_path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(
        "https://0x0.st",
        data=data,
        headers={"Content-Type": "application/octet-stream", "User-Agent": "xinceutong-deploy/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode("utf-8", errors="replace").strip()
    return text if text.startswith("http") else None


def upload_one(file_path: Path, ep: dict) -> str | None:
    """根据 ep['type'] 调度"""
    try:
        if ep["type"] == "catbox":
            return upload_catbox(file_path, ep["url"])
        elif ep["type"] == "0x0st":
            return upload_0x0st(file_path)
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP {e.code}: {e.reason}")
        # 读 body
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:300]
            print(f"         {err_body}")
        except Exception:
            pass
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {e}")
    return None


def main():
    print("=" * 60)
    print("信测通 v5 P0 部署包上传")
    print("=" * 60)
    print()

    if not ZIP_FILE.exists():
        print(f"❌ 部署包不存在: {ZIP_FILE}")
        print(f"   请先跑：python3 scripts/build_deploy_zip.py")
        sys.exit(1)

    size_mb = ZIP_FILE.stat().st_size / 1024 / 1024
    print(f"📦 部署包: {ZIP_FILE.name}")
    print(f"   大小:   {size_mb:.2f} MB")
    print(f"   路径:   {ZIP_FILE}\n")

    # 按优先级尝试
    for ep in ENDPOINTS:
        print(f"⬆️  尝试 {ep['name']}（{ep['expire']}）...")
        url = upload_one(ZIP_FILE, ep)
        if url:
            print()
            print("=" * 60)
            print(f"✅ 上传成功！")
            print(f"   URL:    {url}")
            print(f"   有效:   {ep['expire']}")
            print()
            print("📋 服务器部署命令（直接复制）：")
            print("=" * 60)
            print()
            print(f"# 1. 下载部署包")
            print(f"wget -O /opt/xinceutong-v5.zip '{url}'")
            print()
            print(f"# 2. 备份旧版")
            print(f"cd /opt && cp -r xinceutong-server xinceutong-server.v4.bak 2>/dev/null")
            print()
            print(f"# 3. 解压覆盖")
            print(f"cd /opt && unzip -oq xinceutong-v5.zip")
            print()
            print(f"# 4. 安装依赖（首次部署）")
            print(f"cd /opt/xinceutong-server && pip install -r requirements.txt")
            print()
            print(f"# 5. 数据库迁移（加 dimensions 字段）")
            db_paths = ["/opt/xinceutong-server/server/db/salion.db", "/opt/xinceutong-server/server/db/xinceutong.db", "/opt/xinceutong-server/salion.db"]
            for dbp in db_paths:
                print(f"# 检查 DB: ls -la {dbp}")
            print(f"# 然后根据实际 DB 路径跑迁移：")
            print(f"sqlite3 <DB路径> < /opt/xinceutong-server/sql/migrations/0002_business_dimensions.sql")
            print()
            print(f"# 6. 补 v5 规则（38 条）")
            print(f"cd /opt/xinceutong-server && python3 -m scripts.init_business_v5_rules")
            print()
            print(f"# 7. 跑自检")
            print(f"cd /opt/xinceutong-server && python3 -m scripts.selfcheck_v5")
            print()
            print(f"# 8. 重启服务")
            print(f"pm2 restart xinceutong-server")
            print()
            print("=" * 60)
            return 0

    print()
    print("=" * 60)
    print("❌ 所有上传点都失败，请检查网络后重试")
    print("   或手动上传：scp / rsync / git push")
    print("=" * 60)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(1)
