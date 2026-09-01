"""Pydantic schema for overview statistics."""
from typing import Any
from pydantic import BaseModel


class StatsOverviewResponse(BaseModel):
    alerts_last_24h: int
    severity_breakdown: dict[str, int]
    top_rules: list[dict[str, Any]]
    top_agents: list[dict[str, Any]]
