"""Pydantic schemas for note and triage overlays."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnalystNoteCreate(BaseModel):
    content: str
    author_id: str | None = None


class AnalystNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    wazuh_alert_id: str | None = None
    case_id: str | None = None
    author_id: str | None = None
    content: str
    created_at: datetime
