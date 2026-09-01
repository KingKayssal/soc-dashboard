"""Alerts and triage API endpoints."""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_wazuh_client
from app.models import AlertTriage, AnalystNote, AuditLog, TriageStatus
from app.schemas.alert import (
    AlertDetailResponse,
    AlertListItem,
    AlertListResponse,
    AlertTriageResponse,
    AlertTriageUpdate,
)
from app.schemas.note import AnalystNoteCreate, AnalystNoteResponse
from app.wazuh.client import WazuhClient

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    severity_min: int | None = Query(default=None, ge=1, le=15),
    status: str | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    rule_id: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    wazuh_client: WazuhClient = Depends(get_wazuh_client),
) -> AlertListResponse:
    """Fetch paginated alerts from Wazuh with PostgreSQL triage overlay status."""
    # When filtering by triage status, fetch a larger batch to join with DB
    fetch_limit = limit if not status else 500
    fetch_offset = offset if not status else 0

    alerts_raw, total_count = await wazuh_client.get_alerts(
        limit=fetch_limit,
        offset=fetch_offset,
        severity_min=severity_min,
        status=status,
        agent_id=agent_id,
        rule_id=rule_id,
        since=since,
    )

    alert_ids = [a["id"] for a in alerts_raw]
    triages_by_alert_id: dict[str, AlertTriage] = {}
    if alert_ids:
        db_triages = (
            db.query(AlertTriage)
            .filter(AlertTriage.wazuh_alert_id.in_(alert_ids))
            .all()
        )
        triages_by_alert_id = {t.wazuh_alert_id: t for t in db_triages}

    items: list[AlertListItem] = []
    for raw in alerts_raw:
        a_id = raw["id"]
        triage_record = triages_by_alert_id.get(a_id)
        current_status = triage_record.status if triage_record else TriageStatus.NEW

        if status and current_status.value != status:
            continue

        triage_resp = (
            AlertTriageResponse.model_validate(triage_record)
            if triage_record
            else None
        )

        items.append(
            AlertListItem(
                id=a_id,
                timestamp=raw.get("timestamp", ""),
                rule=raw.get("rule", {}),
                agent=raw.get("agent", {}),
                location=raw.get("location"),
                triage=triage_resp,
                triage_status=current_status,
            )
        )

    if status:
        total_count = len(items)
        items = items[offset : offset + limit]

    return AlertListResponse(
        items=items,
        total=total_count,
        limit=limit,
        offset=offset,
    )


@router.get("/{wazuh_alert_id}", response_model=AlertDetailResponse)
async def get_alert_detail(
    wazuh_alert_id: str,
    db: Session = Depends(get_db),
    wazuh_client: WazuhClient = Depends(get_wazuh_client),
) -> AlertDetailResponse:
    """Fetch full alert detail, combined with Postgres triage state and analyst notes."""
    alert_raw = await wazuh_client.get_alert(wazuh_alert_id)
    if not alert_raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wazuh alert '{wazuh_alert_id}' not found",
        )

    triage = (
        db.query(AlertTriage)
        .filter(AlertTriage.wazuh_alert_id == wazuh_alert_id)
        .first()
    )
    notes = (
        db.query(AnalystNote)
        .filter(AnalystNote.wazuh_alert_id == wazuh_alert_id)
        .order_by(AnalystNote.created_at.desc())
        .all()
    )

    return AlertDetailResponse(
        id=alert_raw["id"],
        timestamp=alert_raw.get("timestamp", ""),
        rule=alert_raw.get("rule", {}),
        agent=alert_raw.get("agent", {}),
        location=alert_raw.get("location"),
        full_log=alert_raw.get("full_log"),
        data=alert_raw.get("data"),
        triage=AlertTriageResponse.model_validate(triage) if triage else None,
        notes=[AnalystNoteResponse.model_validate(n) for n in notes],
    )


@router.patch("/{wazuh_alert_id}/triage", response_model=AlertTriageResponse)
async def update_alert_triage(
    wazuh_alert_id: str,
    payload: AlertTriageUpdate,
    db: Session = Depends(get_db),
    wazuh_client: WazuhClient = Depends(get_wazuh_client),
) -> AlertTriageResponse:
    """Upsert alert triage state (status, severity override, assigned analyst) and log to audit."""
    alert_raw = await wazuh_client.get_alert(wazuh_alert_id)
    if not alert_raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wazuh alert '{wazuh_alert_id}' not found",
        )

    triage = (
        db.query(AlertTriage)
        .filter(AlertTriage.wazuh_alert_id == wazuh_alert_id)
        .first()
    )

    if not triage:
        triage = AlertTriage(wazuh_alert_id=wazuh_alert_id)
        db.add(triage)

    updates = payload.model_dump(exclude_unset=True, exclude={"actor_id"})
    for field, value in updates.items():
        setattr(triage, field, value)

    # Write audit log entry
    audit = AuditLog(
        actor_id=payload.actor_id,
        action="triage.updated",
        target_type="alert",
        target_id=wazuh_alert_id,
        details=payload.model_dump(exclude_unset=True),
    )
    db.add(audit)

    db.commit()
    db.refresh(triage)

    return AlertTriageResponse.model_validate(triage)


@router.post("/{wazuh_alert_id}/notes", response_model=AnalystNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_alert_note(
    wazuh_alert_id: str,
    payload: AnalystNoteCreate,
    db: Session = Depends(get_db),
    wazuh_client: WazuhClient = Depends(get_wazuh_client),
) -> AnalystNoteResponse:
    """Attach an analyst note to an alert."""
    alert_raw = await wazuh_client.get_alert(wazuh_alert_id)
    if not alert_raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wazuh alert '{wazuh_alert_id}' not found",
        )

    # Ensure parent AlertTriage row exists to satisfy foreign key
    triage = (
        db.query(AlertTriage)
        .filter(AlertTriage.wazuh_alert_id == wazuh_alert_id)
        .first()
    )
    if not triage:
        triage = AlertTriage(wazuh_alert_id=wazuh_alert_id)
        db.add(triage)
        db.flush()

    note = AnalystNote(
        wazuh_alert_id=wazuh_alert_id,
        case_id=None,
        author_id=payload.author_id,
        content=payload.content,
    )
    db.add(note)

    # Write audit log
    audit = AuditLog(
        actor_id=payload.author_id,
        action="note.created",
        target_type="alert",
        target_id=wazuh_alert_id,
        details={"content_preview": payload.content[:100]},
    )
    db.add(audit)

    db.commit()
    db.refresh(note)

    return AnalystNoteResponse.model_validate(note)
