"""Case management API endpoints."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import AnalystNote, AuditLog, Case, CaseAlert, CaseSeverity, CaseStatus
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.schemas.note import AnalystNoteCreate, AnalystNoteResponse

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """Create a new incident investigation case with optional attached alerts."""
    case = Case(
        title=payload.title,
        description=payload.description,
        status=payload.status,
        severity=payload.severity,
        assigned_to_id=payload.assigned_to_id,
    )
    db.add(case)
    db.flush()

    # Attach initial alerts
    for alert_id in payload.wazuh_alert_ids:
        case_alert = CaseAlert(case_id=case.id, wazuh_alert_id=alert_id)
        db.add(case_alert)

    # Log audit entry
    audit = AuditLog(
        actor_id=payload.assigned_to_id,
        action="case.created",
        target_type="case",
        target_id=case.id,
        details={"title": case.title, "severity": case.severity.value},
    )
    db.add(audit)

    db.commit()
    db.refresh(case)

    return CaseResponse.model_validate(case)


@router.get("", response_model=list[CaseResponse])
def list_cases(
    status_filter: CaseStatus | None = Query(default=None, alias="status"),
    severity_filter: CaseSeverity | None = Query(default=None, alias="severity"),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> list[CaseResponse]:
    """List investigation cases with optional status and severity filtering."""
    query = (
        db.query(Case)
        .options(joinedload(Case.case_alerts), joinedload(Case.notes))
        .order_by(Case.created_at.desc())
    )
    if status_filter:
        query = query.filter(Case.status == status_filter)
    if severity_filter:
        query = query.filter(Case.severity == severity_filter)

    cases = query.offset(offset).limit(limit).all()
    return [CaseResponse.model_validate(c) for c in cases]


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: str,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """Fetch single case detail by ID."""
    case = (
        db.query(Case)
        .options(joinedload(Case.case_alerts), joinedload(Case.notes))
        .filter(Case.id == case_id)
        .first()
    )
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found",
        )
    return CaseResponse.model_validate(case)


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: str,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
) -> CaseResponse:
    """Update case status, severity, title, or assignee."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found",
        )

    updates = payload.model_dump(exclude_unset=True, exclude={"resolved"})
    for field, value in updates.items():
        setattr(case, field, value)

    if payload.status == CaseStatus.CLOSED or payload.resolved is True:
        case.resolved_at = datetime.now(timezone.utc)
    elif payload.status in (CaseStatus.OPEN, CaseStatus.IN_PROGRESS):
        case.resolved_at = None

    audit = AuditLog(
        actor_id=case.assigned_to_id,
        action="case.updated",
        target_type="case",
        target_id=case.id,
        details=payload.model_dump(exclude_unset=True),
    )
    db.add(audit)

    db.commit()
    db.refresh(case)

    return CaseResponse.model_validate(case)


@router.post("/{case_id}/notes", response_model=AnalystNoteResponse, status_code=status.HTTP_201_CREATED)
def add_case_note(
    case_id: str,
    payload: AnalystNoteCreate,
    db: Session = Depends(get_db),
) -> AnalystNoteResponse:
    """Attach an analyst note to a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found",
        )

    note = AnalystNote(
        case_id=case_id,
        wazuh_alert_id=None,
        author_id=payload.author_id,
        content=payload.content,
    )
    db.add(note)

    audit = AuditLog(
        actor_id=payload.author_id,
        action="note.created",
        target_type="case",
        target_id=case_id,
        details={"content_preview": payload.content[:100]},
    )
    db.add(audit)

    db.commit()
    db.refresh(note)

    return AnalystNoteResponse.model_validate(note)
