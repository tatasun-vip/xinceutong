"""
Run init scripts with explicit cwd and env.
Used because CodeBuddy's shell tool ignores `cd` in execute_command.
"""
import os
import sys
import subprocess

# 强制切到 server 目录
os.chdir("/Users/suntata/CodeBuddy/20260907155240/xinceutong-server")
os.environ["PYTHONPATH"] = "/Users/suntata/CodeBuddy/20260907155240/xinceutong-server"
os.environ["REDIS_DISABLED"] = "1"

print(f"cwd: {os.getcwd()}")
print(f".env exists: {os.path.exists('.env')}")

# 跑 3 个 init
for script in ["init_product_types", "init_site_config", "init_scorecard"]:
    print(f"\n=== Running {script} ===")
    result = subprocess.run(
        ["/Users/suntata/CodeBuddy/20260907155240/xinceutong-server/.venv/bin/python", "-m", f"scripts.{script}"],
        cwd="/Users/suntata/CodeBuddy/20260907155240/xinceutong-server",
        env={**os.environ},
        capture_output=True,
        text=True,
    )
    print(result.stdout[-500:] if result.stdout else "(no stdout)")
    if result.returncode != 0:
        print(f"STDERR: {result.stderr[-500:]}")
        print(f"FAIL: {script}")
    else:
        print(f"OK: {script}")
