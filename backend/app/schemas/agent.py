"""Pydantic schema for Wazuh agents."""
from typing import Any
from pydantic import BaseModel


class AgentResponse(BaseModel):
    id: str
    name: str
    ip: str | None = None
    status: str
    os: dict[str, Any] | None = None
    version: str | None = None
    last_keepalive: str | None = None
