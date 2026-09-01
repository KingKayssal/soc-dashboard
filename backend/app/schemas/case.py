"""Pydantic schemas for case management."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models import CaseSeverity, CaseStatus
from app.schemas.note import AnalystNoteResponse


class CaseAlertItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    case_id: str
    wazuh_alert_id: str
    added_at: datetime


class CaseCreate(BaseModel):
    title: str
    description: str | None = None
    status: CaseStatus = CaseStatus.OPEN
    severity: CaseSeverity = CaseSeverity.MEDIUM
    assigned_to_id: str | None = None
    wazuh_alert_ids: list[str] = []


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: CaseStatus | None = None
    severity: CaseSeverity | None = None
    assigned_to_id: str | None = None
    resolved: bool | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None = None
    status: CaseStatus
    severity: CaseSeverity
    assigned_to_id: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    case_alerts: list[CaseAlertItem] = []
    notes: list[AnalystNoteResponse] = []
