import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLogEntry, AuditSource
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User

def write_audited_field(
    db: Session,
    complaint: Complaint,
    field_name: str,
    new_value,
    actor: User,
    source: AuditSource,
    reason: str | None = None,
) -> None:
    old_value = getattr(complaint, field_name)
    setattr(complaint, field_name, new_value)
    db.add(
        AuditLogEntry(
            id=uuid.uuid4(),
            complaint_id=complaint.id,
            actor_id=actor.id,
            action="field_update",
            field_name=field_name,
            old_value=None if old_value is None else str(old_value),
            new_value=None if new_value is None else str(new_value),
            source=source,
            reason=reason,
        )
    )

def record_transition(
    db: Session,
    complaint: Complaint,
    from_status: ComplaintStatus,
    to_status: ComplaintStatus,
    actor: User,
    reason: str | None = None,
) -> None:
    complaint.status = to_status
    db.add(
        AuditLogEntry(
            id=uuid.uuid4(),
            complaint_id=complaint.id,
            actor_id=actor.id,
            action="status_transition",
            field_name=None,
            old_value=from_status.value,
            new_value=to_status.value,
            source=AuditSource.human,
            reason=reason,
        )
    )
