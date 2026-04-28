"""TMDB-backed metadata enricher.

Resolves a free-text title (e.g. ``"Minecraft Movie Trailer"``) to validated
metadata via the TMDB ``/search/multi`` endpoint. Results are cached for
``settings.tmdb_cache_ttl_seconds`` (default: 30 days) since film metadata is
practically immutable.

Auth: prefers v4 Read Access Token (Bearer header); falls back to v3 ``api_key``
query param when the token isn't configured.

Error handling: any network/parse error degrades to an empty ``MovieMetadata``
— never raises. ``TrendsService._enrich`` already protects the pipeline from
exceptions, but degrading here means we don't blow the cache or log noise.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from app.config import settings
from app.services.cache import TTLCache
from app.services.enrichers.base import MetadataEnricher, MovieMetadata

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.themoviedb.org/3"

# Strip common YouTube/SEO clutter so search hits the actual title.
# These tokens routinely appear in Google Trends queries about movies but are
# noise for TMDB title matching ("minecraft movie trailer" → "minecraft").
_NOISE_TOKENS_RE = re.compile(
    r"\b(?:trailer|teaser|official|hd|2160p|1080p|4k|"
    r"full\s*movie|movie|film|cinema|review|reaction|"
    r"release\s*date|box\s*office|"
    r"part\s*\d+|season\s*\d+|episode\s*\d+)\b",
    flags=re.IGNORECASE,
)
_WHITESPACE_RE = re.compile(r"\s+")

# TMDB animation genre id. Used as a hint when ``media_type`` doesn't already
# spell out the type. See https://developer.themoviedb.org/reference/genre-movie-list
_ANIMATION_GENRE_ID = 16


def _normalize_query(title: str) -> str:
    cleaned = _NOISE_TOKENS_RE.sub(" ", title)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned or title.strip()


def _extract_year(date_str: str | None) -> int | None:
    if not date_str or len(date_str) < 4:
        return None
    try:
        return int(date_str[:4])
    except ValueError:
        return None


def _origin_country(result: dict[str, Any]) -> str | None:
    countries = result.get("origin_country") or []
    if isinstance(countries, list) and countries:
        return str(countries[0])
    return None


def _is_animation_hint(media_type: str, genre_ids: list[int]) -> bool | None:
    if media_type == "movie" or media_type == "tv":
        return _ANIMATION_GENRE_ID in (genre_ids or [])
    return None


class TmdbEnricher(MetadataEnricher):
    """Enrich titles using TMDB's ``/search/multi`` endpoint."""

    def __init__(
        self,
        *,
        read_access_token: str | None = None,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        cache: TTLCache[MovieMetadata] | None = None,
    ) -> None:
        token = read_access_token if read_access_token is not None else settings.tmdb_read_access_token
        api_v3 = api_key if api_key is not None else settings.tmdb_api_key
        # Treat empty strings as "not configured" so callers can pass "" to
        # explicitly disable a credential (useful in tests where settings may
        # already contain a token from .env).
        self._token = token or None
        self._api_key = api_v3 or None
        self._cache = cache or TTLCache[MovieMetadata](ttl_seconds=settings.tmdb_cache_ttl_seconds)
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=_BASE_URL,
            timeout=settings.tmdb_request_timeout_seconds,
            headers=self._auth_headers(),
        )

    def _auth_headers(self) -> dict[str, str]:
        if self._token:
            return {"Authorization": f"Bearer {self._token}", "accept": "application/json"}
        return {"accept": "application/json"}

    def _auth_params(self) -> dict[str, str]:
        # Only used when no Bearer token is available. Returning an empty dict
        # when the v3 key is also missing is intentional — the request will
        # come back 401 and we'll degrade gracefully.
        if self._token or not self._api_key:
            return {}
        return {"api_key": self._api_key}

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def enrich(self, title: str, *, region: str | None = None) -> MovieMetadata:
        if not title:
            return MovieMetadata()

        cache_key = f"{(region or 'GLOBAL').upper()}::{title.strip().lower()}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        query = _normalize_query(title)
        if not query:
            self._cache.set(cache_key, MovieMetadata())
            return MovieMetadata()

        try:
            search_results = self._search_multi(query)
        except Exception:  # noqa: BLE001 — boundary; degrade rather than propagate
            logger.warning("tmdb_search_failed", extra={"query": query}, exc_info=True)
            return MovieMetadata()

        match = _pick_best_match(search_results)
        if match is None:
            empty = MovieMetadata()
            self._cache.set(cache_key, empty)
            return empty

        try:
            details = self._fetch_details(match["id"], match["media_type"])
        except Exception:  # noqa: BLE001
            logger.warning(
                "tmdb_details_failed",
                extra={"tmdb_id": match.get("id"), "media_type": match.get("media_type")},
                exc_info=True,
            )
            details = None

        metadata = _build_metadata(match, details)
        self._cache.set(cache_key, metadata)
        return metadata

    def _search_multi(self, query: str) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "query": query,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
            **self._auth_params(),
        }
        response = self._client.get("/search/multi", params=params)
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        if not isinstance(results, list):
            return []
        return [r for r in results if isinstance(r, dict)]

    def _fetch_details(self, tmdb_id: int, media_type: str) -> dict[str, Any] | None:
        if media_type not in ("movie", "tv"):
            return None
        path = f"/{media_type}/{tmdb_id}"
        response = self._client.get(path, params=self._auth_params())
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else None


def _pick_best_match(results: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the most relevant film/TV match from a /search/multi response.

    TMDB's relevance order is generally good, but we still skip:
    - ``person`` results (no movie metadata)
    - results with no ``id``

    We do NOT skip TV: animated shows and series are routinely re-uploaded as
    "movies" on YouTube, and the user's research scope explicitly covers
    мультсериалы and дорамы.
    """
    for result in results:
        media_type = result.get("media_type")
        if media_type not in ("movie", "tv"):
            continue
        if "id" not in result:
            continue
        return result
    return None


def _build_metadata(match: dict[str, Any], details: dict[str, Any] | None) -> MovieMetadata:
    media_type = str(match.get("media_type") or "")
    tmdb_id = int(match["id"])

    release_year = _extract_year(
        match.get("release_date") or match.get("first_air_date")
    )
    original_language = match.get("original_language") or None
    if isinstance(original_language, str):
        original_language = original_language.lower()
    else:
        original_language = None

    origin_country = _origin_country(match)
    genre_ids = match.get("genre_ids") or []
    if not isinstance(genre_ids, list):
        genre_ids = []

    is_animation = _is_animation_hint(media_type, [int(g) for g in genre_ids if isinstance(g, int)])

    studios: tuple[str, ...] = ()
    genres: tuple[str, ...] = ()

    if details is not None:
        # Year/country/language are more authoritative on the details endpoint.
        release_year = release_year or _extract_year(
            details.get("release_date") or details.get("first_air_date")
        )
        det_lang = details.get("original_language")
        if isinstance(det_lang, str) and det_lang:
            original_language = det_lang.lower()
        det_countries = details.get("origin_country") or []
        if isinstance(det_countries, list) and det_countries and not origin_country:
            origin_country = str(det_countries[0])

        companies = details.get("production_companies") or []
        if isinstance(companies, list):
            studios = tuple(
                str(c["name"]) for c in companies if isinstance(c, dict) and c.get("name")
            )

        det_genres = details.get("genres") or []
        if isinstance(det_genres, list):
            genres = tuple(
                str(g["name"]) for g in det_genres if isinstance(g, dict) and g.get("name")
            )
            if is_animation is None:
                is_animation = any(
                    isinstance(g, dict) and g.get("id") == _ANIMATION_GENRE_ID
                    for g in det_genres
                )

    tmdb_details = _summarize_details(match, details, media_type=media_type)

    return MovieMetadata(
        tmdb_id=tmdb_id,
        release_year=release_year,
        original_language=original_language,
        origin_country=origin_country,
        studios=studios,
        genres=genres,
        is_animation=is_animation,
        tmdb_details=tmdb_details,
    )


# Whitelisted scalar fields that are safe to pass through to the UI without
# bloating the snapshot payload. Anything not in this list is dropped.
_DETAIL_SCALAR_FIELDS = (
    "title",
    "name",
    "original_title",
    "original_name",
    "overview",
    "tagline",
    "homepage",
    "status",
    "release_date",
    "first_air_date",
    "last_air_date",
    "runtime",
    "number_of_seasons",
    "number_of_episodes",
    "poster_path",
    "backdrop_path",
    "popularity",
    "vote_average",
    "vote_count",
    "adult",
)


def _summarize_details(
    match: dict[str, Any], details: dict[str, Any] | None, *, media_type: str
) -> dict[str, Any]:
    """Build a compact, UI-friendly subset of TMDB fields.

    Pulls the fields actually rendered on the detail page. Falls back to
    search-result data when the details call failed (e.g. timeout).
    """
    source: dict[str, Any] = {}
    if isinstance(details, dict):
        source.update(details)
    # Search result is a fallback for the few fields it carries (poster, overview)
    for key in ("poster_path", "backdrop_path", "overview", "title", "name"):
        if key not in source and match.get(key):
            source[key] = match[key]

    out: dict[str, Any] = {"media_type": media_type or match.get("media_type")}
    for key in _DETAIL_SCALAR_FIELDS:
        if key in source and source[key] not in (None, "", []):
            out[key] = source[key]

    # Spoken languages — list[str] of ISO codes
    spoken = source.get("spoken_languages")
    if isinstance(spoken, list):
        codes = [
            str(s["iso_639_1"]).lower()
            for s in spoken
            if isinstance(s, dict) and s.get("iso_639_1")
        ]
        if codes:
            out["spoken_languages"] = codes

    # Production countries — list[str] of ISO codes
    countries = source.get("production_countries")
    if isinstance(countries, list):
        codes = [
            str(c["iso_3166_1"]).upper()
            for c in countries
            if isinstance(c, dict) and c.get("iso_3166_1")
        ]
        if codes:
            out["production_countries"] = codes

    return out
