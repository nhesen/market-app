"""Retail content, storage and operational metadata.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
from app.db.session import Base
import app.models
revision="0002";down_revision="0001";branch_labels=None;depends_on=None
def upgrade():Base.metadata.create_all(bind=op.get_bind())
def downgrade():pass
