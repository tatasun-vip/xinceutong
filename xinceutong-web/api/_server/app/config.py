"""
应用配置：使用 pydantic-settings 从环境变量 / .env 加载
"""
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ===== 应用基础 =====
    APP_NAME: str = "xinceutong"
    ENV: str = Field(default="development", description="development / staging / production")
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ===== MySQL =====
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "xinceutong"
    MYSQL_PASSWORD: str = "xinceutong"
    MYSQL_DATABASE: str = "xinceutong"
    MYSQL_CHARSET: str = "utf8mb4"

    # ===== 数据库覆盖（本地无 MySQL 时设为 sqlite+aiosqlite:///./xinceutong.db）=====
    DATABASE_URL: str = ""

    @property
    def mysql_dsn(self) -> str:
        """SQLAlchemy 异步 DSN（被 DATABASE_URL 覆盖时用覆盖值）"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset={self.MYSQL_CHARSET}"
        )

    # ===== Redis =====
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20

    # ===== JWT =====
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # ===== 微信小程序 =====
    WECHAT_APPID: str = ""
    WECHAT_SECRET: str = ""
    WECHAT_MCH_ID: str = ""                # 商户号
    WECHAT_PAY_KEY: str = ""               # API v2 支付密钥
    WECHAT_PAY_NOTIFY_URL: str = ""        # 支付回调地址
    WECHAT_PAY_CERT_PATH: str = ""         # 退款证书路径（apiclient_cert.pem）
    WECHAT_PAY_KEY_PATH: str = ""          # 退款私钥路径（apiclient_key.pem）

    # ===== 业务开关 =====
    ASSESSMENT_BASE_PRICE: float = 9.99
    PROMOTER_PRICE_MIN: float = 6.99
    PROMOTER_PRICE_MAX: float = 19.99
    PROMOTER_COMMISSION_RATE: float = 0.30
    FREE_TRIAL_PER_USER: int = 1
    FREE_TRIAL_INVITE_LIMIT: int = 10

    # ===== 风控 / 防刷 =====
    RATE_LIMIT_PER_MIN: int = 30
    RATE_LIMIT_PER_HOUR: int = 200

    # ===== CORS =====
    CORS_ORIGINS: List[str] = ["*"]

    # ===== 日志 =====
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # ===== AI 服务（DeepSeek）=====
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    @property
    def mysql_sync_dsn(self) -> str:
        """Alembic 用的同步 DSN（pymysql / psycopg2）"""
        if self.DATABASE_URL:
            # 异步 PG → 同步 PG 转换（alembic 用同步）
            if self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            # 异步 MySQL → 同步 MySQL 转换
            if self.DATABASE_URL.startswith("mysql+aiomysql://"):
                return self.DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://", 1)
            # 异步 SQLite → 同步 SQLite 转换
            if self.DATABASE_URL.startswith("sqlite+aiosqlite:///"):
                return self.DATABASE_URL.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset={self.MYSQL_CHARSET}"
        )


settings = Settings()
