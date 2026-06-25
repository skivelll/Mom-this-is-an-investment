from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET_KEY = "change-me-to-a-long-random-secret-key"


class Settings(BaseSettings):
    """Настройки приложения"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "mom-this-is-an-investment"
    app_env: Literal["local", "dev", "test", "prod"] = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")

    database_url: str = Field(
        default="postgresql+asyncpg://mti:mti@127.0.0.1:5433/mom_this_is_an_investment",
    )
    sql_echo: bool = False

    jwt_secret_key: str = DEFAULT_JWT_SECRET_KEY
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24

    cors_allow_origins: str = "*"
    admin_title: str = "MTI Admin"
    admin_base_url: str = "/admin"
    admin_session_secret: str = ""
    admin_allowed_emails: str = ""
    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_admin_password: str = "admin"

    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BROKERS: str = "localhost:9092"
    enable_metrics: bool = False

    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "mom-investment-media"
    s3_region: str = "us-east-1"
    s3_public_base_url: str = ""
    s3_use_ssl: bool = False
    media_max_upload_size_bytes: int = 10 * 1024 * 1024
    media_presigned_url_ttl_seconds: int = 15 * 60

    create_reserved_catalogs_on_company_create: bool = False

    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        if self.app_env == "prod":
            if self.jwt_secret_key == DEFAULT_JWT_SECRET_KEY:
                raise ValueError("JWT_SECRET_KEY must be changed in production.")
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must contain at least 32 characters.")
            if self.debug:
                raise ValueError("APP_DEBUG must be false in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Возвращает кэшированный объект настроек"""

    return Settings()
