"""
信测通 v11 部署包上传到 catbox（备用方案，包 > 50MB 时用）

正常部署走 SSH 直传（scripts/upload_to_cvm.sh），只有包太大时才用此脚本中转。
"""
import os
import sys
import json
import urllib.request
from pathlib import Path

ROOT = Path("/Users/suntata/CodeBuddy/20260907155240")
DIST_DIR = ROOT / "dist"

# 自动找最新 zip
if len(sys.argv) > 1:
    ZIP_FILE = Path(sys.argv[1])
else:
    candidates = sorted(DIST_DIR.glob("xincetong-cvm-deploy-*.zip"), reverse=True)
    if not candidates:
        print("ERR: dist/xincetong-cvm-deploy-*.zip not found")
        sys.exit(1)
    ZIP_FILE = candidates[0]

ENDPOINTS = [
    ("catbox.moe", "catbox"),
    ("0x0.st", "0x0"),
    ("file.io", "fileio"),
]


def upload_catbox(path):
    boundary = "----FB" + os.urandom(16).hex()
    with open(path, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"reqtype\"\r\n\r\nfileupload\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"fileToUpload\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        "https://catbox.moe/user/api.php", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    return urllib.request.urlopen(req, timeout=300).read().decode().strip()


def upload_0x0(path):
    with open(path, "rb") as f:
        req = urllib.request.Request("https://0x0.st", data=f.read())
        req.add_header("Content-Type", "application/octet-stream")
        return urllib.request.urlopen(req, timeout=300).read().decode().strip()


def upload_fileio(path):
    with open(path, "rb") as f:
        req = urllib.request.Request("https://file.io", data=f.read(), method="POST")
        req.add_header("Content-Type", "application/octet-stream")
        data = json.loads(urllib.request.urlopen(req, timeout=300).read().decode())
        return data.get("link", "")


def main():
    if not ZIP_FILE.exists():
        print(f"ERR: file not found: {ZIP_FILE}")
        sys.exit(1)

    size_mb = ZIP_FILE.stat().st_size / 1024 / 1024
    print(f"==> Uploading: {ZIP_FILE} ({size_mb:.2f} MB)\n")

    if size_mb < 50:
        print("Tip: package < 50MB, prefer scp:")
        print(f"  bash scripts/upload_to_cvm.sh {ZIP_FILE.name}\n")
        try:
            input("Press Enter to upload to catbox anyway, Ctrl+C to cancel: ")
        except KeyboardInterrupt:
            sys.exit(0)

    for name, method in ENDPOINTS:
        try:
            print(f"==> Trying {name}...")
            if method == "catbox":
                result = upload_catbox(ZIP_FILE)
            elif method == "0x0":
                result = upload_0x0(ZIP_FILE)
            else:
                result = upload_fileio(ZIP_FILE)
            if result.startswith("http"):
                print(f"\nOK: {result}")
                print(f"\n=== CVM one-liner deploy ===")
                print(f"ssh root@82.156.166.188")
                print(f"wget -O /tmp/{ZIP_FILE.name} '{result}'")
                print(f"unzip -o /tmp/{ZIP_FILE.name} -d /tmp/xincetong-new/")
                print(f"bash /tmp/cvm_deploy.sh /tmp/{ZIP_FILE.name}")
                return
        except Exception as e:
            print(f"  WARN: {name} failed: {e}")
            continue

    print("\nERR: all endpoints failed, try scp instead")


if __name__ == "__main__":
    main()
