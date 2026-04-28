import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.api.routes_trends import get_trends_service
from app.config import settings
from app.main import app


def _configure_test_settings(tmp_path) -> None:
    settings.google_provider = "mock"
    # Force noop enrichers so integration tests stay offline. Phase 4
    # validation requires a YouTube signal — we provide one by overriding
    # the service after the factory builds it (see _force_offline_enrichers).
    settings.metadata_provider = "noop"
    settings.youtube_stats_provider = "noop"
    settings.api_key = None
    settings.sqlite_path = str(tmp_path / "trends.db")
    get_trends_service.cache_clear()
    _force_offline_enrichers()


def _force_offline_enrichers() -> None:
    """Replace the cached service's YouTube enricher with one that emits a
    constant signal, so the validation filter doesn't reject every item.

    This keeps the integration tests fully offline while still exercising the
    Phase 4 pipeline end-to-end.
    """
    from app.services.enrichers.base import YouTubeStatsEnricher
    from app.services.scoring import YouTubeStats

    class _ConstantYouTube(YouTubeStatsEnricher):
        def fetch_stats(self, query, *, region, lookback_days=14):  # type: ignore[override]
            return YouTubeStats(videos_published=3, total_views=900, median_views=300, channels_count=2)

    service = get_trends_service()
    service.youtube_stats_enricher = _ConstantYouTube()


def test_sync_and_top_summary_flow(tmp_path) -> None:
    _configure_test_settings(tmp_path)
    client = TestClient(app)

    sync_resp = client.post("/api/v1/admin/sync")
    assert sync_resp.status_code == 200
    assert sync_resp.json()["saved"] > 0

    top_resp = client.get("/api/v1/trends/top")
    assert top_resp.status_code == 200
    payload = top_resp.json()
    assert payload["region"] == "US"
    assert isinstance(payload["items"], list)
    assert len(payload["items"]) > 0

    summary_resp = client.get("/api/v1/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert "summary" in summary
    assert isinstance(summary["top_titles"], list)


def test_timeseries_and_snapshots_contract(tmp_path) -> None:
    _configure_test_settings(tmp_path)
    client = TestClient(app)

    client.post("/api/v1/admin/sync")

    top_resp = client.get("/api/v1/trends/top")
    top_payload = top_resp.json()
    query = top_payload["items"][0]["query"]

    ts_resp = client.get(f"/api/v1/trends/{query}/timeseries")
    assert ts_resp.status_code == 200
    ts_payload = ts_resp.json()
    assert ts_payload["query"] == query
    assert len(ts_payload["points"]) > 0

    timestamps = [point["timestamp"] for point in ts_payload["points"]]
    assert timestamps == sorted(timestamps)

    snapshots_resp = client.get("/api/v1/admin/snapshots")
    assert snapshots_resp.status_code == 200
    snap_payload = snapshots_resp.json()
    assert isinstance(snap_payload["snapshots"], list)
    assert len(snap_payload["snapshots"]) >= 1
    assert "created_at" in snap_payload["snapshots"][0]
    assert "item_count" in snap_payload["snapshots"][0]


def test_sync_runs_and_metrics_contract(tmp_path) -> None:
    _configure_test_settings(tmp_path)
    client = TestClient(app)

    client.post("/api/v1/admin/sync")

    runs_resp = client.get("/api/v1/admin/sync-runs")
    assert runs_resp.status_code == 200
    runs_payload = runs_resp.json()
    assert isinstance(runs_payload["runs"], list)
    assert len(runs_payload["runs"]) >= 1
    assert "quality_passed" in runs_payload["runs"][0]
    assert "reason" in runs_payload["runs"][0]

    metrics_resp = client.get("/api/v1/admin/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "latest_sync_quality_passed" in metrics
    assert "sync_runs_last_24h" in metrics
    assert "quality_failures_last_24h" in metrics


def test_prometheus_metrics_endpoint(tmp_path) -> None:
    _configure_test_settings(tmp_path)
    client = TestClient(app)

    client.post("/api/v1/admin/sync")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "yb_sync_runs_total" in body
    assert "yb_quality_failures_total" in body
    assert "yb_latest_snapshot_age_seconds" in body


def test_alerts_contract(tmp_path) -> None:
    _configure_test_settings(tmp_path)
    client = TestClient(app)

    client.post("/api/v1/admin/sync")
    resp = client.get("/api/v1/admin/alerts")
    assert resp.status_code == 200
    payload = resp.json()
    assert "alerts" in payload
    assert isinstance(payload["alerts"], list)
