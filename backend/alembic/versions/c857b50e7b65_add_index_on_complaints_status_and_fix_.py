"""add index on complaints status and fix FK ondelete behavior

Revision ID: c857b50e7b65
Revises: 0001
Create Date: 2026-08-01 19:20:23.623134
"""
from alembic import op
import sqlalchemy as sa


revision = 'c857b50e7b65'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Note: autogenerate also proposed dropping and recreating
    # complaints_embedding_idx (the ivfflat vector index). That's a false
    # positive - autogenerate doesn't understand pgvector's custom index
    # type and misreads it as changed - so those lines were removed by
    # hand; that index is untouched by this migration.
    op.drop_constraint('attachments_complaint_id_fkey', 'attachments', type_='foreignkey')
    op.create_foreign_key('attachments_complaint_id_fkey', 'attachments', 'complaints', ['complaint_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('audit_log_entries_complaint_id_fkey', 'audit_log_entries', type_='foreignkey')
    op.create_foreign_key('audit_log_entries_complaint_id_fkey', 'audit_log_entries', 'complaints', ['complaint_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_complaints_status'), 'complaints', ['status'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_complaints_status'), table_name='complaints')
    op.drop_constraint('audit_log_entries_complaint_id_fkey', 'audit_log_entries', type_='foreignkey')
    op.create_foreign_key('audit_log_entries_complaint_id_fkey', 'audit_log_entries', 'complaints', ['complaint_id'], ['id'])
    op.drop_constraint('attachments_complaint_id_fkey', 'attachments', type_='foreignkey')
    op.create_foreign_key('attachments_complaint_id_fkey', 'attachments', 'complaints', ['complaint_id'], ['id'])
