"""Initial schema with overlay tables and enums

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. Create alert_triage table
    op.create_table(
        "alert_triage",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("wazuh_alert_id", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("new", "investigating", "false_positive", "resolved", name="triagestatus"),
            nullable=False,
            server_default="new",
        ),
        sa.Column("severity_override", sa.Integer(), nullable=True),
        sa.Column("assigned_to_id", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alert_triage_wazuh_alert_id", "alert_triage", ["wazuh_alert_id"], unique=True)

    # 3. Create cases table
    op.create_table(
        "cases",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "closed", name="casestatus"),
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "severity",
            sa.Enum("low", "medium", "high", "critical", name="caseseverity"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("assigned_to_id", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 4. Create case_alerts table
    op.create_table(
        "case_alerts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("case_id", sa.String(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wazuh_alert_id", sa.String(length=255), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "wazuh_alert_id", name="uq_case_alert"),
    )
    op.create_index("ix_case_alerts_wazuh_alert_id", "case_alerts", ["wazuh_alert_id"], unique=False)

    # 5. Create analyst_notes table
    op.create_table(
        "analyst_notes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "wazuh_alert_id",
            sa.String(length=255),
            sa.ForeignKey("alert_triage.wazuh_alert_id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("case_id", sa.String(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=True),
        sa.Column("author_id", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analyst_notes_wazuh_alert_id", "analyst_notes", ["wazuh_alert_id"], unique=False)
    op.create_index("ix_analyst_notes_case_id", "analyst_notes", ["case_id"], unique=False)

    # 6. Create audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_index("ix_analyst_notes_case_id", table_name="analyst_notes")
    op.drop_index("ix_analyst_notes_wazuh_alert_id", table_name="analyst_notes")
    op.drop_table("analyst_notes")
    op.drop_index("ix_case_alerts_wazuh_alert_id", table_name="case_alerts")
    op.drop_table("case_alerts")
    op.drop_table("cases")
    op.drop_index("ix_alert_triage_wazuh_alert_id", table_name="alert_triage")
    op.drop_table("alert_triage")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    # Drop enums
    sa.Enum(name="caseseverity").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="casestatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="triagestatus").drop(op.get_bind(), checkfirst=True)
