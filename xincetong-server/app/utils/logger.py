"""
日志：控制台 + 文件双输出，自动按天切分

Vercel Serverless 兼容：
- /var/task/ 是只读文件系统，写文件会 OSError
- 检测到 VERCEL=1 或 ENV=production 时，只输出到 stdout
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

from app.config import settings


def _make_logger() -> logging.Logger:
    logger = logging.getLogger("xincetong")
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 文件（按天切分，保留 30 天）
    # Vercel Serverless：/var/task 只读，跳过文件 handler（用 stdout 代替）
    is_vercel = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    is_serverless = is_vercel or settings.ENV == "production"

    if settings.ENV != "test" and not is_serverless:
        try:
            os.makedirs(settings.LOG_DIR, exist_ok=True)
            fh = TimedRotatingFileHandler(
                filename=os.path.join(settings.LOG_DIR, "xincetong.log"),
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
            )
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except OSError as e:
            # 只读文件系统等：降级到 stdout
            logger.warning(f"文件日志不可用，仅控制台输出: {e}")

    logger.propagate = False
    return logger


logger = _make_logger()
