"""Abstract interface for Wazuh SIEM client."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class WazuhClient(ABC):
    """Abstract interface defining required methods for Wazuh integration (mock or real)."""

    @abstractmethod
    async def get_alerts(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        severity_min: int | None = None,
        status: str | None = None,
        agent_id: str | None = None,
        rule_id: str | None = None,
        since: datetime | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Fetch paginated alerts with filtering. Returns (alerts_list, total_count)."""
        pass

    @abstractmethod
    async def get_alert(self, wazuh_alert_id: str) -> dict[str, Any] | None:
        """Fetch a single alert by its Wazuh alert ID."""
        pass

    @abstractmethod
    async def get_agents(self) -> list[dict[str, Any]]:
        """Fetch all registered Wazuh agents and their status."""
        pass

    @abstractmethod
    async def get_stats_overview(self) -> dict[str, Any]:
        """Fetch overview statistics: alerts_last_24h, severity_breakdown, top_rules, top_agents."""
        pass
