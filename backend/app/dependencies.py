"""FastAPI dependencies."""
from functools import lru_cache

from app.config import settings
from app.wazuh.client import WazuhClient
from app.wazuh.mock_client import MockWazuhClient
from app.wazuh.real_client import RealWazuhClient

_wazuh_client_instance: WazuhClient | None = None


def get_wazuh_client() -> WazuhClient:
    """Dependency providing a singleton WazuhClient (Mock or Real depending on settings)."""
    global _wazuh_client_instance
    if _wazuh_client_instance is None:
        if settings.WAZUH_MODE.lower() == "real":
            _wazuh_client_instance = RealWazuhClient()
        else:
            _wazuh_client_instance = MockWazuhClient()
    return _wazuh_client_instance
