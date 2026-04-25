from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "YB Trends"
    default_region: str = "US"
    default_period: str = "7d"
    default_limit: int = 20

    google_provider: str = Field(default="mock", description="mock|pytrends|managed")
    managed_provider_url: str | None = Field(default=None)
    managed_provider_api_key: str | None = Field(default=None)

    gemini_api_key: str | None = Field(default=None)

    api_key: str | None = Field(default=None, description="Optional API key for protected routes")
    sqlite_path: str = Field(default=".data/trends.db")
    cache_ttl_seconds: int = Field(default=600)

    sync_interval_seconds: int = Field(default=21600, description="Background sync interval")
    max_snapshot_age_seconds: int = Field(default=43200, description="Data freshness threshold")
    lock_ttl_seconds: int = Field(default=1200, description="Sync lock TTL")

    quality_min_items: int = Field(default=5, description="Minimum items required from provider")
    quality_min_relevant_ratio: float = Field(default=0.2, description="Minimum relevant ratio")

    alert_snapshot_age_seconds: int = Field(default=21600, description="Alert threshold for stale snapshot")
    alert_quality_failures_24h: int = Field(default=3, description="Alert threshold for quality gate failures")

    enable_inprocess_scheduler: bool = Field(
        default=False,
        description="Enable in-process scheduler. Keep false in production and use external scheduler.",
    )

    model_config = SettingsConfigDict(env_prefix="YBT_", env_file=".env", extra="ignore")


settings = Settings()
