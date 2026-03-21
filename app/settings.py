from datetime import timedelta
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.containers.enums import Environment, LogLevel


class SettingsBase(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class AppSettings(SettingsBase):
    env: Environment = Environment.DEV
    version: str = "0.1.0"
    name: str = "Auth Service"
    app_host: str
    app_port: str

    encryption_current_key: str
    encryption_previous_key: str | None = None
    bcrypt_cost: int = 12

    log_level: LogLevel = LogLevel.INFO

    @model_validator(mode="after")
    def validate_security(self):
        if self.env == Environment.PROD:
            if self.log_level == LogLevel.DEBUG:
                raise ValueError("DEBUG logging not allowed in production")
            if not (10 <= self.bcrypt_cost <= 14):
                raise ValueError(f"bcrypt_cost={self.bcrypt_cost} is too small for PROD (min 10)")

        return self


class DB_Settings(SettingsBase):
    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str
    port: int
    user: str
    password: str
    name: str

    # Connection pool settings
    connection_pool_size: int = 5  # Number of connections to keep open
    connection_max_overflow: int = 10  # Extra connections allowed during peak load
    connection_pool_timeout: int = 30  # Seconds to wait for available connection
    connection_pool_recycle: int = 1800  # Recycle connections after 30 minutes

    # Echo SQL statements for debugging (disable in production)
    echo: bool = False

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def url_async(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class SMTP_Settings(SettingsBase):
    model_config = SettingsConfigDict(env_prefix="SMTP_")

    token: str
    host: str
    port: int
    web_port: int


class RedisSettings(SettingsBase):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str
    port: int


class TokenSettings(SettingsBase):
    jwt_algorithm: str = "HS256"
    secret_key: str

    refresh_ttl: timedelta = timedelta(days=7)
    access_ttl: timedelta = timedelta(seconds=30)
    reset_ttl: timedelta = timedelta(minutes=10)
    mfa_setup_ttl: timedelta = timedelta(seconds=300)
    mfa_challenge_ttl: timedelta = timedelta(seconds=120)

    @model_validator(mode="after")
    def validate_security(self):
        if len(self.secret_key) < 32:
            raise ValueError("SECRET_KEY too short")

        return self


class Settings(SettingsBase):
    app: AppSettings = Field(default_factory=AppSettings)
    token: TokenSettings = Field(default_factory=TokenSettings)
    db: DB_Settings = Field(default_factory=DB_Settings)
    smtp: SMTP_Settings = Field(default_factory=SMTP_Settings)
    redis: RedisSettings = Field(default_factory=RedisSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
