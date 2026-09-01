"""Real Wazuh SIEM client communicating with Wazuh Manager API and Wazuh Indexer (OpenSearch)."""
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.wazuh.client import WazuhClient

logger = logging.getLogger(__name__)


class RealWazuhClient(WazuhClient):
    """Client for live Wazuh instances: talks to Wazuh Manager API (55000) and Indexer (9200)."""

    def __init__(self):
        self.api_url = settings.WAZUH_API_URL.rstrip("/")
        self.api_user = settings.WAZUH_API_USER
        self.api_password = settings.WAZUH_API_PASSWORD
        self.indexer_url = settings.WAZUH_INDEXER_URL.rstrip("/")
        self.indexer_user = settings.WAZUH_INDEXER_USER
        self.indexer_password = settings.WAZUH_INDEXER_PASSWORD
        self.verify_ssl = settings.WAZUH_VERIFY_SSL
        self._jwt_token: str | None = None

        if not self.verify_ssl:
            logger.warning("Wazuh SSL certificate verification is DISABLED (WAZUH_VERIFY_SSL=false)")

    async def _get_auth_token(self) -> str:
        """Authenticate with Wazuh API and retrieve JWT token."""
        if self._jwt_token:
            return self._jwt_token

        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=10.0) as client:
            resp = await client.post(
                f"{self.api_url}/security/user/authenticate",
                auth=(self.api_user, self.api_password),
            )
            resp.raise_for_status()
            data = resp.json()
            # Wazuh returns {"data": {"token": "..."}}
            self._jwt_token = data.get("data", {}).get("token") or data.get("token")
            return self._jwt_token

    async def _api_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Perform authenticated request against Wazuh API with automatic 401 retry."""
        token = await self._get_auth_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=15.0) as client:
            resp = await client.request(method, f"{self.api_url}{endpoint}", headers=headers, **kwargs)
            if resp.status_code == 401:
                # Token expired, refresh and retry once
                self._jwt_token = None
                token = await self._get_auth_token()
                headers["Authorization"] = f"Bearer {token}"
                resp = await client.request(method, f"{self.api_url}{endpoint}", headers=headers, **kwargs)

            resp.raise_for_status()
            return resp.json()

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
        """Query Wazuh Indexer (OpenSearch) for wazuh-alerts-* index."""
        must_clauses: list[dict[str, Any]] = []

        if severity_min is not None:
            must_clauses.append({"range": {"rule.level": {"gte": severity_min}}})
        if agent_id is not None:
            must_clauses.append({"term": {"agent.id": agent_id}})
        if rule_id is not None:
            must_clauses.append({"term": {"rule.id": rule_id}})
        if since is not None:
            must_clauses.append({"range": {"timestamp": {"gte": since.isoformat()}}})

        query: dict[str, Any] = {
            "from": offset,
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}},
        }

        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=15.0) as client:
                resp = await client.post(
                    f"{self.indexer_url}/wazuh-alerts-*/_search",
                    json=query,
                    auth=(self.indexer_user, self.indexer_password),
                )
                resp.raise_for_status()
                data = resp.json()
                hits = data.get("hits", {})
                total = hits.get("total", {}).get("value", 0)
                alerts = [
                    {"id": hit.get("_id"), **hit.get("_source", {})}
                    for hit in hits.get("hits", [])
                ]
                return alerts, total
        except Exception as e:
            logger.error(f"Error querying Wazuh Indexer: {e}")
            return [], 0

    async def get_alert(self, wazuh_alert_id: str) -> dict[str, Any] | None:
        """Fetch alert document by _id from Wazuh indexer."""
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=10.0) as client:
                resp = await client.get(
                    f"{self.indexer_url}/wazuh-alerts-*/_doc/{wazuh_alert_id}",
                    auth=(self.indexer_user, self.indexer_password),
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                hit = resp.json()
                return {"id": hit.get("_id"), **hit.get("_source", {})}
        except Exception as e:
            logger.error(f"Error fetching alert {wazuh_alert_id} from Indexer: {e}")
            return None

    async def get_agents(self) -> list[dict[str, Any]]:
        """Fetch agents list from Wazuh Manager API."""
        try:
            data = await self._api_request("GET", "/agents?limit=100")
            items = data.get("data", {}).get("affected_items", [])
            return items
        except Exception as e:
            logger.error(f"Error fetching agents from Wazuh API: {e}")
            return []

    async def get_stats_overview(self) -> dict[str, Any]:
        """Fetch high-level statistics from Wazuh."""
        # Query indexer with aggregations over last 24h
        now = datetime.now(timezone.utc)
        since = now.replace(hour=now.hour - 24 if now.hour >= 24 else 0)
        alerts, total = await self.get_alerts(limit=1000, since=since)
        
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for a in alerts:
            lvl = a.get("rule", {}).get("level", 0)
            if lvl <= 4:
                severity_counts["low"] += 1
            elif lvl <= 7:
                severity_counts["medium"] += 1
            elif lvl <= 11:
                severity_counts["high"] += 1
            else:
                severity_counts["critical"] += 1

        return {
            "alerts_last_24h": total,
            "severity_breakdown": severity_counts,
            "top_rules": [],
            "top_agents": [],
        }
