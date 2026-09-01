"""SQLAlchemy ORM models for SOC Dashboard overlay data."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TriageStatus(str, enum.Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class CaseSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    assigned_triages: Mapped[list["AlertTriage"]] = relationship("AlertTriage", back_populates="assigned_to")
    assigned_cases: Mapped[list["Case"]] = relationship("Case", back_populates="assigned_to")
    notes: Mapped[list["AnalystNote"]] = relationship("AnalystNote", back_populates="author")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="actor")


class AlertTriage(Base):
    __tablename__ = "alert_triage"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wazuh_alert_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    status: Mapped[TriageStatus] = mapped_column(
        SAEnum(TriageStatus, name="triagestatus", native_enum=True),
        default=TriageStatus.NEW,
        nullable=False,
    )
    severity_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assigned_to_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    # Relationships
    assigned_to: Mapped[User | None] = relationship("User", back_populates="assigned_triages")
    notes: Mapped[list["AnalystNote"]] = relationship(
        "AnalystNote",
        back_populates="alert_triage",
        cascade="all, delete-orphan",
    )


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        SAEnum(CaseStatus, name="casestatus", native_enum=True),
        default=CaseStatus.OPEN,
        nullable=False,
    )
    severity: Mapped[CaseSeverity] = mapped_column(
        SAEnum(CaseSeverity, name="caseseverity", native_enum=True),
        default=CaseSeverity.MEDIUM,
        nullable=False,
    )
    assigned_to_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assigned_to: Mapped[User | None] = relationship("User", back_populates="assigned_cases")
    case_alerts: Mapped[list["CaseAlert"]] = relationship(
        "CaseAlert", back_populates="case", cascade="all, delete-orphan"
    )
    notes: Mapped[list["AnalystNote"]] = relationship(
        "AnalystNote",
        back_populates="case",
        cascade="all, delete-orphan",
    )


class CaseAlert(Base):
    __tablename__ = "case_alerts"
    __table_args__ = (UniqueConstraint("case_id", "wazuh_alert_id", name="uq_case_alert"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    wazuh_alert_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    case: Mapped[Case] = relationship("Case", back_populates="case_alerts")


class AnalystNote(Base):
    __tablename__ = "analyst_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wazuh_alert_id: Mapped[str | None] = mapped_column(
        String(255), ForeignKey("alert_triage.wazuh_alert_id", ondelete="CASCADE"), nullable=True, index=True
    )
    case_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True
    )
    author_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    author: Mapped[User | None] = relationship("User", back_populates="notes")
    alert_triage: Mapped[AlertTriage | None] = relationship("AlertTriage", back_populates="notes")
    case: Mapped[Case | None] = relationship("Case", back_populates="notes")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "alert" or "case"
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    actor: Mapped[User | None] = relationship("User", back_populates="audit_logs")
