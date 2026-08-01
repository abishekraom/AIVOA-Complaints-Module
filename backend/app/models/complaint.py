import uuid
from datetime import date, datetime, timezone
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

class ComplaintStatus(StrEnum):
    pending_approval = "pending_approval"
    pending_rework_triage = "pending_rework_triage"
    approved_closed = "approved_closed"
    trashed = "trashed"

class Complaint(Base):
    __tablename__ = "complaints"
    # DB-level enforcement of valid ComplaintStatus values, in addition to Python-level StrEnum
    __table_args__ = (
        CheckConstraint("status IN ('pending_approval', 'pending_rework_triage', 'approved_closed', 'trashed')", name="ck_complaints_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_number: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True, index=True)
    status: Mapped[ComplaintStatus] = mapped_column(String(30), nullable=False)

    # Section 1: Origin & Customer Details
    complaint_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Section 2: Product & Batch Identification
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_strength_grade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    batch_lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    manufacturing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity_affected: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    quantity_affected_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Section 3: Complaint Details
    complaint_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    complaint_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    complaint_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Section 4: Initial Assessment & Priority
    initial_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # AI outputs (populated by Plans 2-3)
    ai_risk_severity_suggested: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_risk_next_action_suggested: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_risk_assessment_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_root_cause_hypotheses: Mapped[list | None] = mapped_column(JSON, nullable=True)
    root_cause_accepted: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_capa_corrective_suggested: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_capa_preventive_suggested: Mapped[str | None] = mapped_column(Text, nullable=True)
    capa_accepted: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Per-field provenance: {"product_name": "ai_extracted" | "user_corrected", ...}
    field_provenance: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Duplicate-detection embedding (all-MiniLM-L6-v2, 384 dims)
    embedding: Mapped[list | None] = mapped_column(Vector(384), nullable=True)

    # Workflow metadata
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trashed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    trashed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purge_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
