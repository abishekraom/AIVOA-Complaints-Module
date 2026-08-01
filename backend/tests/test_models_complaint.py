import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models.attachment import Attachment, AttachmentKind
from app.models.audit import AuditLogEntry, AuditSource
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import Role, User


def _make_coordinator(db_session):
    user = User(id=uuid.uuid4(), email="c@example.com", password_hash=hash_password("pw"), full_name="Coord", role=Role.coordinator)
    db_session.add(user)
    db_session.commit()
    return user


def test_complaint_persists_all_reference_ui_fields(db_session):
    coordinator = _make_coordinator(db_session)
    complaint = Complaint(
        id=uuid.uuid4(),
        complaint_number="CMP-2026-0001",
        status=ComplaintStatus.pending_approval,
        complaint_source="Apollo Pharmacy",
        customer_name="Apollo Pharmacy",
        product_name="Amoxicillin Capsules",
        product_strength_grade="500 mg",
        batch_lot_number="AMX240602",
        manufacturing_date=date(2026, 3, 1),
        expiry_date=date(2028, 2, 1),
        quantity_affected=48,
        quantity_affected_unit="capsules",
        complaint_type="Discoloration",
        complaint_date=date(2026, 8, 1),
        complaint_description="Discolored capsules reported.",
        initial_severity="Critical",
        priority="High",
        created_by=coordinator.id,
    )
    db_session.add(complaint)
    db_session.commit()

    fetched = db_session.get(Complaint, complaint.id)
    assert fetched.complaint_number == "CMP-2026-0001"
    assert fetched.status == ComplaintStatus.pending_approval
    assert fetched.quantity_affected == 48


def test_complaint_status_enum_has_expected_values():
    assert {s.value for s in ComplaintStatus} == {
        "pending_approval",
        "pending_rework_triage",
        "approved_closed",
        "trashed",
    }


def test_complaint_status_check_constraint_rejects_invalid_values(db_session):
    coordinator = _make_coordinator(db_session)
    # Bypass Python enum by passing raw string to trigger DB constraint
    complaint = Complaint(
        id=uuid.uuid4(),
        status="invalid_status",  # type: ignore
        created_by=coordinator.id,
    )
    db_session.add(complaint)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_attachment_links_to_complaint(db_session):
    coordinator = _make_coordinator(db_session)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=coordinator.id)
    db_session.add(complaint)
    db_session.commit()

    attachment = Attachment(
        id=uuid.uuid4(),
        complaint_id=complaint.id,
        kind=AttachmentKind.source_document,
        filename="complaint.pdf",
        storage_path="/data/complaint.pdf",
        uploaded_by=coordinator.id,
    )
    db_session.add(attachment)
    db_session.commit()

    fetched = db_session.get(Attachment, attachment.id)
    assert fetched.complaint_id == complaint.id
    assert fetched.kind == AttachmentKind.source_document


def test_attachment_kind_enum_has_expected_values():
    assert {k.value for k in AttachmentKind} == {
        "source_document",
        "evidence",
    }


def test_attachment_kind_check_constraint_rejects_invalid_values(db_session):
    coordinator = _make_coordinator(db_session)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=coordinator.id)
    db_session.add(complaint)
    db_session.commit()

    # Bypass Python enum by passing raw string to trigger DB constraint
    attachment = Attachment(
        id=uuid.uuid4(),
        complaint_id=complaint.id,
        kind="invalid_kind",  # type: ignore
        filename="complaint.pdf",
        storage_path="/data/complaint.pdf",
        uploaded_by=coordinator.id,
    )
    db_session.add(attachment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_audit_log_entry_records_field_change(db_session):
    coordinator = _make_coordinator(db_session)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=coordinator.id)
    db_session.add(complaint)
    db_session.commit()

    entry = AuditLogEntry(
        id=uuid.uuid4(),
        complaint_id=complaint.id,
        actor_id=coordinator.id,
        action="field_update",
        field_name="product_name",
        old_value=None,
        new_value="Amoxicillin Capsules",
        source=AuditSource.ai,
    )
    db_session.add(entry)
    db_session.commit()

    fetched = db_session.get(AuditLogEntry, entry.id)
    assert fetched.field_name == "product_name"
    assert fetched.source == AuditSource.ai


def test_audit_source_enum_has_expected_values():
    assert {s.value for s in AuditSource} == {
        "ai",
        "human",
        "system",
    }


def test_audit_source_check_constraint_rejects_invalid_values(db_session):
    coordinator = _make_coordinator(db_session)
    complaint = Complaint(id=uuid.uuid4(), status=ComplaintStatus.pending_approval, created_by=coordinator.id)
    db_session.add(complaint)
    db_session.commit()

    # Bypass Python enum by passing raw string to trigger DB constraint
    entry = AuditLogEntry(
        id=uuid.uuid4(),
        complaint_id=complaint.id,
        actor_id=coordinator.id,
        action="field_update",
        field_name="product_name",
        old_value=None,
        new_value="Amoxicillin Capsules",
        source="invalid",  # type: ignore
    )
    db_session.add(entry)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
