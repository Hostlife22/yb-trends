from app.config import settings
from app.services.providers.base import TrendsProvider
from app.services.providers.managed_provider import ManagedTrendsProvider
from app.services.providers.mock_provider import MockTrendsProvider
from app.services.providers.pytrends_provider import PyTrendsProvider


def build_trends_provider() -> TrendsProvider:
    provider_name = settings.google_provider.lower().strip()
    if provider_name == "pytrends":
        return PyTrendsProvider()
    if provider_name == "managed":
        return ManagedTrendsProvider()
    return MockTrendsProvider()
