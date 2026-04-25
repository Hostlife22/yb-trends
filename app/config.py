from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "YB Trends"
    default_region: str = "US"
    default_period: str = "7d"
    default_limit: int = 20

    google_provider: str = Field(default="mock", description="mock|pytrends")
    gemini_api_key: str | None = Field(default=None)

    api_key: str | None = Field(default=None, description="Optional API key for protected routes")
    sqlite_path: str = Field(default=".data/trends.db")
    cache_ttl_seconds: int = Field(default=600)

    model_config = SettingsConfigDict(env_prefix="YBT_", env_file=".env", extra="ignore")


settings = Settings()
