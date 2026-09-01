"""Pydantic schemas for alerts and triage state."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict

from app.models import TriageStatus
from app.schemas.note import AnalystNoteResponse


class AlertTriageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    wazuh_alert_id: str
    status: TriageStatus
    severity_override: int | None = None
    assigned_to_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AlertTriageUpdate(BaseModel):
    status: TriageStatus | None = None
    severity_override: int | None = None
    assigned_to_id: str | None = None
    actor_id: str | None = None  # User performing the action (for audit log)


class MitreAttack(BaseModel):
    id: list[str] = []
    tactic: list[str] = []


class AlertRule(BaseModel):
    id: str
    description: str
    level: int
    mitre: MitreAttack | None = None


class AlertAgent(BaseModel):
    id: str
    name: str
    ip: str | None = None


class AlertListItem(BaseModel):
    id: str
    timestamp: str
    rule: AlertRule
    agent: AlertAgent
    location: str | None = None
    triage: AlertTriageResponse | None = None
    triage_status: TriageStatus = TriageStatus.NEW


class AlertListResponse(BaseModel):
    items: list[AlertListItem]
    total: int
    limit: int
    offset: int


class AlertDetailResponse(BaseModel):
    id: str
    timestamp: str
    rule: dict[str, Any]
    agent: dict[str, Any]
    location: str | None = None
    full_log: str | None = None
    data: dict[str, Any] | None = None
    triage: AlertTriageResponse | None = None
    notes: list[AnalystNoteResponse] = []
