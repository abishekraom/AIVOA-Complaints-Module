import uuid

import pytest

from app.core.audit import record_transition, write_audited_field
from app.core.security import hash_password
from app.models.audit import AuditLogEntry, AuditSource
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import Role, User

def _make_user(db_session, role):
    user = User(id=uuid.uuid4(), email=f"{role}@x.com", password_hash=hash_password("pw"), full_name="U", role=role)
    db_session.add(user)
    db_session.commit()
    return user

def test_write_audited_field_sets_value_and_logs_entry(db_session):
    actor = _make_user(db_session, Role.coordinator)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=actor.id)
    db_session.add(complaint)
    db_session.commit()

    write_audited_field(db_session, complaint, "product_name", "Amoxicillin Capsules", actor, AuditSource.ai)
    db_session.commit()

    assert complaint.product_name == "Amoxicillin Capsules"
    entries = db_session.query(AuditLogEntry).filter_by(complaint_id=complaint.id, field_name="product_name").all()
    assert len(entries) == 1
    assert entries[0].old_value is None
    assert entries[0].new_value == "Amoxicillin Capsules"
    assert entries[0].source == AuditSource.ai

def test_write_audited_field_captures_old_value_on_correction(db_session):
    actor = _make_user(db_session, Role.coordinator)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=actor.id, batch_lot_number="AMX240602")
    db_session.add(complaint)
    db_session.commit()

    write_audited_field(db_session, complaint, "batch_lot_number", "BMX240602", actor, AuditSource.ai, reason="user correction via chat")
    db_session.commit()

    entry = db_session.query(AuditLogEntry).filter_by(complaint_id=complaint.id, field_name="batch_lot_number").one()
    assert entry.old_value == "AMX240602"
    assert entry.new_value == "BMX240602"
    assert entry.reason == "user correction via chat"

def test_record_transition_logs_status_change(db_session):
    actor = _make_user(db_session, Role.approver)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=actor.id)
    db_session.add(complaint)
    db_session.commit()

    record_transition(db_session, complaint, ComplaintStatus.pending_approval, ComplaintStatus.pending_rework_triage, actor, reason="Missing batch number")
    db_session.commit()

    assert complaint.status == ComplaintStatus.pending_rework_triage
    entry = db_session.query(AuditLogEntry).filter_by(complaint_id=complaint.id, action="status_transition").one()
    assert entry.old_value == "pending_approval"
    assert entry.new_value == "pending_rework_triage"
    assert entry.reason == "Missing batch number"

def test_write_audited_field_flushes_unpersisted_complaint_to_get_id(db_session):
    """Complaint.id is populated by a Python-side default only at flush
    time. Calling write_audited_field on a Complaint that was never
    explicitly given an id and never flushed must not produce an audit
    entry with a null complaint_id."""
    actor = _make_user(db_session, Role.coordinator)
    complaint = Complaint(status=ComplaintStatus.pending_approval, created_by=actor.id)
    db_session.add(complaint)

    write_audited_field(db_session, complaint, "product_name", "Amoxicillin Capsules", actor, AuditSource.ai)
    db_session.commit()

    assert complaint.id is not None
    entry = db_session.query(AuditLogEntry).filter_by(field_name="product_name").one()
    assert entry.complaint_id is not None
    assert entry.complaint_id == complaint.id

def test_record_transition_rejects_mismatched_from_status(db_session):
    actor = _make_user(db_session, Role.approver)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=actor.id)
    db_session.add(complaint)
    db_session.commit()

    with pytest.raises(ValueError):
        record_transition(
            db_session,
            complaint,
            ComplaintStatus.approved_closed,  # wrong: actual status is pending_approval
            ComplaintStatus.pending_rework_triage,
            actor,
        )

    assert complaint.status == ComplaintStatus.pending_approval
    assert db_session.query(AuditLogEntry).filter_by(complaint_id=complaint.id, action="status_transition").count() == 0
