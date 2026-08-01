import uuid

from sqlalchemy.orm import Session

from app.models.audit import AuditLogEntry, AuditSource
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User

def _resolve_complaint_id(db: Session, complaint: Complaint) -> uuid.UUID:
    if complaint.id is None:
        # Complaint.id has a Python-side default that only applies at flush
        # time. Flush now so complaint.id is populated before we read it for
        # the audit entry - otherwise the entry ends up with a null
        # complaint_id and is orphaned from the complaint it describes.
        db.flush()
    if complaint.id is None:
        raise ValueError(
            "Cannot write an audit entry for a complaint with no id; "
            "add the complaint to the session before auditing it"
        )
    return complaint.id

def write_audited_field(
    db: Session,
    complaint: Complaint,
    field_name: str,
    new_value,
    actor: User,
    source: AuditSource,
    reason: str | None = None,
) -> None:
    complaint_id = _resolve_complaint_id(db, complaint)
    old_value = getattr(complaint, field_name)
    setattr(complaint, field_name, new_value)
    db.add(
        AuditLogEntry(
            id=uuid.uuid4(),
            complaint_id=complaint_id,
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
    if complaint.status != from_status:
        raise ValueError(
            f"Expected complaint status to be {from_status}, but it is {complaint.status}"
        )
    complaint_id = _resolve_complaint_id(db, complaint)
    complaint.status = to_status
    db.add(
        AuditLogEntry(
            id=uuid.uuid4(),
            complaint_id=complaint_id,
            actor_id=actor.id,
            action="status_transition",
            field_name=None,
            old_value=from_status.value,
            new_value=to_status.value,
            source=AuditSource.human,
            reason=reason,
        )
    )
