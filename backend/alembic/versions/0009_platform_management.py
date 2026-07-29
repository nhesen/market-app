"""platform organisation lifecycle

Revision ID: 0009
Revises: 0008
"""
from alembic import op
import sqlalchemy as sa
revision="0009";down_revision="0008";branch_labels=None;depends_on=None
def upgrade():op.add_column("organisations",sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()))
def downgrade():op.drop_column("organisations","is_active")
