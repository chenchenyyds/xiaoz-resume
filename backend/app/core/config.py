"""配置管理 - 全部从环境变量读"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ---------- 运行环境 ----------
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_NAME: str = "xiaoz-resume"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_BASE_URL: str = "http://localhost:8000"
    APP_FRONTEND_USER_URL: str = "http://localhost:5173"
    APP_FRONTEND_ADMIN_URL: str = "http://localhost:5174"

    # ---------- 数据库 ----------
    DATABASE_URL: str = (
        "postgresql+psycopg2://xiaoz:xiaoz_pwd@localhost:5432/xiaoz_resume"
    )

    # ---------- Redis ----------
    REDIS_URL: str = "redis://localhost:6379/0"

    # ---------- JWT ----------
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # ---------- 阿里云 OSS ----------
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_ENDPOINT: str = ""
    OSS_BUCKET: str = ""
    OSS_BASE_URL: str = ""

    # ---------- 阿里云短信 ----------
    SMS_ACCESS_KEY_ID: str = ""
    SMS_ACCESS_KEY_SECRET: str = ""
    SMS_SIGN_NAME: str = "小Z简历"
    SMS_TEMPLATE_CODE: str = ""
    SMS_REGION: str = "cn-hangzhou"
    SMS_DEV_MODE: bool = True  # 开发模式验证码固定 123456

    # ---------- 虎皮椒支付 ----------
    HUPIIJIAO_API_URL: str = "https://api.hupijiao.com/v1"
    HUPIIJIAO_MERCHANT_ID: str = ""
    HUPIIJIAO_MERCHANT_KEY: str = ""
    HUPIIJIAO_NOTIFY_URL: str = ""
    HUPIIJIAO_RETURN_URL: str = ""
    HUPIIJIAO_SANDBOX: bool = True

    # ---------- DeepSeek ----------
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ---------- 管理员 ----------
    ADMIN_DEFAULT_PHONE: str = "13800000000"

    # ---------- CORS ----------
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:5174"]
    )


settings = Settings()
