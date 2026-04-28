"""Optional smoke test against the real TMDB API.

Skipped by default. To run:

    YBT_TMDB_READ_ACCESS_TOKEN=... PYTEST_RUN_NETWORK=1 pytest -m network -v

Asserts that we can resolve a well-known title to an actual TMDB record.
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("httpx")

from app.config import settings
from app.services.enrichers.tmdb import TmdbEnricher


pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(
        os.environ.get("PYTEST_RUN_NETWORK") != "1",
        reason="set PYTEST_RUN_NETWORK=1 to run network-dependent tests",
    ),
    pytest.mark.skipif(
        not (settings.tmdb_read_access_token or settings.tmdb_api_key),
        reason="TMDB credentials not configured",
    ),
]


def test_real_tmdb_resolves_known_title() -> None:
    enricher = TmdbEnricher()
    try:
        metadata = enricher.enrich("Inside Out 2")
    finally:
        enricher.close()

    assert metadata.tmdb_id is not None, "expected TMDB to know Inside Out 2"
    assert metadata.release_year is not None
    assert metadata.original_language is not None
