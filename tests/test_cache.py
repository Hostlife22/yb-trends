from app.services.cache import TTLCache


def test_cache_set_get() -> None:
    cache = TTLCache[int](ttl_seconds=5)
    cache.set("k", 1)
    assert cache.get("k") == 1
