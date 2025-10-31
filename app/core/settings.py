from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyUrl, BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlaidSettings(BaseModel):
    model_config = SettingsConfigDict(extra="ignore")

    client_id: str = Field(default="PLAID_CLIENT_ID_PLACEHOLDER", validation_alias="PLAID_CLIENT_ID")
    secret: str = Field(default="PLAID_SECRET_PLACEHOLDER", validation_alias="PLAID_SECRET")
    environment: str = Field(default="sandbox", validation_alias="PLAID_ENV")
    products: List[str] = Field(default_factory=lambda: ["transactions", "investments"], validation_alias="PLAID_PRODUCTS")
    country_codes: List[str] = Field(default_factory=lambda: ["US"], validation_alias="PLAID_COUNTRY_CODES")
    redirect_uri: str | None = Field(default=None, validation_alias="PLAID_REDIRECT_URI")

    @field_validator("products", "country_codes", mode="before")
    @classmethod
    def split_csv(cls, value: List[str] | str) -> List[str]:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


class SchedulerSettings(BaseModel):
    model_config = SettingsConfigDict(extra="ignore")

    timezone: str = Field(default="UTC", validation_alias="SCHEDULER_TIMEZONE")
    initial_backfill_days: int = Field(default=730, validation_alias="SYNC_INITIAL_BACKFILL_DAYS")
    balance_refresh_cron: str = Field(
        default="0 5 * * *",
        validation_alias="SCHED_BALANCE_REFRESH_CRON",
    )
    holdings_refresh_cron: str = Field(
        default="30 5 * * *",
        validation_alias="SCHED_HOLDINGS_REFRESH_CRON",
    )


class SecuritySettings(BaseModel):
    model_config = SettingsConfigDict(extra="ignore")

    encryption_key_base64: str = Field(
        default="XumNsZM3Rp3XIanFkFJxuxMxDPZWS9Vyhi3F7S-Mw7A=",
        validation_alias="ENCRYPTION_KEY_BASE64",
    )
    jwt_secret_key: str = Field(default="change-me", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )


class APISettings(BaseModel):
    model_config = SettingsConfigDict(extra="ignore")

    allowed_origins: List[str] = Field(default_factory=list, validation_alias="ALLOWED_ORIGINS")
    rate_limit: str = Field(default="60/minute", validation_alias="API_RATE_LIMIT")

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: List[str] | str) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/finance",
        validation_alias="DATABASE_URL",
    )

    plaid: PlaidSettings = Field(default_factory=PlaidSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings)
    api: APISettings = Field(default_factory=APISettings)

    sentry_dsn: AnyUrl | None = Field(default=None, alias="SENTRY_DSN")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()  # type: ignore[arg-type]


settings = get_settings()
