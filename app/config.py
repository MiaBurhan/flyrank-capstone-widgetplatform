"""Settings, loaded once from environment variables / .env."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    admin_api_key: str = Field(min_length=16)
    public_base_url: str = "http://localhost:8000"

    rate_limit_per_minute: int = 5
    spam_threshold: int = 5
    max_body_bytes: int = 10_000
    duplicate_window_minutes: int = 10
    trust_proxy: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
