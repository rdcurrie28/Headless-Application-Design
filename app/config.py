from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Mode = Literal["live", "fake"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CI_", extra="ignore")

    snowflake_mode: Mode = "fake"
    postgres_mode: Mode = "fake"
    s3_mode: Mode = "fake"

    api_keys: str = ""
    cors_origins: str = "http://localhost:3000"
    cache_ttl_seconds: int = 300
    section_timeout_seconds: float = 10.0

    churn_threshold: float = 0.6
    expansion_threshold: float = 0.6

    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_private_key_path: str = ""
    snowflake_role: str = ""
    snowflake_warehouse: str = ""
    snowflake_database: str = ""
    snowflake_schema: str = "SALES_INSIGHTS"

    postgres_dsn: str = "postgresql://insights:insights@localhost:5432/insights"
    postgres_pool_min: int = 1
    postgres_pool_max: int = 10

    s3_bucket: str = "customer-insights"
    s3_region: str = "us-east-1"
    s3_endpoint_url: str | None = None
    s3_prefix: str = "customers"
    s3_presign_seconds: int = 900

    @property
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
