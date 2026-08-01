import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

class AttachmentKind(StrEnum):
    source_document = "source_document"
    evidence = "evidence"

class Attachment(Base):
    __tablename__ = "attachments"
    # DB-level enforcement of valid AttachmentKind values, in addition to Python-level StrEnum
    __table_args__ = (
        CheckConstraint("kind IN ('source_document', 'evidence')", name="ck_attachments_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[AttachmentKind] = mapped_column(String(20), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
