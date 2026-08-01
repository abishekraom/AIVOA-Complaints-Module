"""add server defaults for timestamps and switch embedding index to hnsw

Revision ID: b1f2c3d4e5a6
Revises: c857b50e7b65
Create Date: 2026-08-01 20:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'b1f2c3d4e5a6'
down_revision = 'c857b50e7b65'
branch_labels = None
depends_on = None

_TIMESTAMP_COLUMNS = [
    ('users', 'created_at'),
    ('complaints', 'created_at'),
    ('complaints', 'updated_at'),
    ('attachments', 'uploaded_at'),
    ('audit_log_entries', 'created_at'),
]

def upgrade() -> None:
    for table, column in _TIMESTAMP_COLUMNS:
        op.alter_column(table, column, server_default=sa.func.now())

    # ivfflat trains its centroids on the rows present at build time, so an
    # index built on an empty table gives degraded recall until a manual
    # REINDEX. hnsw needs no training step.
    op.drop_index('complaints_embedding_idx', table_name='complaints')
    op.execute(
        "CREATE INDEX complaints_embedding_idx ON complaints "
        "USING hnsw (embedding vector_cosine_ops)"
    )

def downgrade() -> None:
    op.drop_index('complaints_embedding_idx', table_name='complaints')
    op.execute(
        "CREATE INDEX complaints_embedding_idx ON complaints "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    for table, column in _TIMESTAMP_COLUMNS:
        op.alter_column(table, column, server_default=None)
