import pytest

pytest.importorskip("pydantic")

from app.services.providers.pytrends_provider import PyTrendsProvider


def test_parse_traffic_values() -> None:
    p = PyTrendsProvider()
    assert p._parse_traffic("200K+") == 200000
    assert p._parse_traffic("1M+") == 1000000
    assert p._parse_traffic("12,345+") == 12345
