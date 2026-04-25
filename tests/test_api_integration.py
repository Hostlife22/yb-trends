import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def _configure_test_settings(tmp_path) -> None:
    settings.google_provider = "mock"
    settings.api_key = None
    settings.sqlite_path = str(tmp_path / "trends.db")


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
