"""
应用配置中心
所有配置项通过环境变量加载，支持 .env 文件
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """全局应用配置"""

    # ── App ──────────────────────────────────────
    APP_NAME: str = "FastAPI CRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-to-a-random-secret-key"
    ENVIRONMENT: str = "development"

    # ── Database ──────────────────────────────────
    # 开发环境默认使用 SQLite（零依赖），生产环境设置环境变量切换 MySQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./fastapi_crm.db"
    DATABASE_URL_SYNC: str = "sqlite:///./fastapi_crm.db"

    # ── Redis ────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Celery ───────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Qiniu ────────────────────────────────────
    QINIU_ACCESS_KEY: str = ""
    QINIU_SECRET_KEY: str = ""
    QINIU_BUCKET_NAME: str = ""
    QINIU_DOMAIN: str = ""
    QINIU_ENABLED: bool = False

    # ── File Upload ──────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # ── SMTP ─────────────────────────────────────
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@example.com"

    # ── Pagination ───────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """适配不同数据库驱动"""
        # SQLite 不需要额外处理
        if "sqlite" in v:
            return v
        # MySQL 确保使用 asyncmy 异步驱动
        if "asyncmy" not in v and "mysql" in v:
            v = v.replace("mysql://", "mysql+asyncmy://")
            v = v.replace("mysql+pymysql://", "mysql+asyncmy://")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
