from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "YB Trends"
    default_region: str = "US"
    default_period: str = "7d"
    default_limit: int = 20

    google_provider: str = Field(default="mock", description="mock|pytrends|gemini|managed")
    managed_provider_url: str | None = Field(default=None)
    managed_provider_api_key: str | None = Field(default=None)

    gemini_api_key: str | None = Field(default=None)
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model id. 2.5-flash supports google_search grounding and has the widest free quota.",
    )

    api_key: str | None = Field(default=None, description="Optional API key for protected routes")
    cors_origins: str = Field(default="http://localhost:3000", description="Comma-separated allowed origins")
    sqlite_path: str = Field(default=".data/trends.db")
    cache_ttl_seconds: int = Field(default=600)

    sync_interval_seconds: int = Field(default=21600, description="Background sync interval")
    max_snapshot_age_seconds: int = Field(default=43200, description="Data freshness threshold")
    lock_ttl_seconds: int = Field(default=1200, description="Sync lock TTL")

    quality_min_items: int = Field(default=5, ge=1, description="Minimum items required from provider")
    quality_min_relevant_ratio: float = Field(default=0.2, ge=0.0, le=1.0, description="Minimum relevant ratio")

    alert_snapshot_age_seconds: int = Field(default=21600, description="Alert threshold for stale snapshot")
    alert_quality_failures_24h: int = Field(default=3, description="Alert threshold for quality gate failures")

    # Enrichers (Phase 1: noop only; tmdb / youtube_api land in Phase 2/3)
    metadata_provider: str = Field(default="noop", description="noop|tmdb")
    youtube_stats_provider: str = Field(default="noop", description="noop|youtube_api")
    tmdb_api_key: str | None = Field(default=None, description="TMDB v3 API key (fallback)")
    tmdb_read_access_token: str | None = Field(
        default=None,
        description="TMDB v4 Read Access Token (Bearer; preferred over tmdb_api_key)",
    )
    tmdb_cache_ttl_seconds: int = Field(default=2_592_000, description="30 days; metadata is stable")
    tmdb_request_timeout_seconds: float = Field(default=8.0, gt=0)
    youtube_api_key: str | None = Field(default=None)
    youtube_cache_ttl_seconds: int = Field(default=21_600, description="6h cache for YouTube stats")
    youtube_request_timeout_seconds: float = Field(default=8.0, gt=0)
    youtube_search_max_results: int = Field(default=25, ge=1, le=50, description="Max videos per query (search.list cap is 50)")
    youtube_lookback_days: int = Field(default=14, ge=1, le=90)

    # Composite final_score weights — must roughly sum to 1.0
    score_weight_search_demand: float = Field(default=0.30, ge=0.0, le=1.0)
    score_weight_search_momentum: float = Field(default=0.20, ge=0.0, le=1.0)
    score_weight_youtube_demand: float = Field(default=0.30, ge=0.0, le=1.0)
    score_weight_youtube_freshness: float = Field(default=0.20, ge=0.0, le=1.0)

    enable_inprocess_scheduler: bool = Field(
        default=False,
        description="Enable in-process scheduler. Keep false in production and use external scheduler.",
    )

    model_config = SettingsConfigDict(env_prefix="YBT_", env_file=".env", extra="ignore")


settings = Settings()
