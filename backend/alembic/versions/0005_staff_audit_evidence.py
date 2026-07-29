"""Persist staff audit OCR evidence and explicit confirmation.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE condition ADD VALUE IF NOT EXISTS 'INVALID_PRODUCT'")
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns("audit_result_items")}
    additions = (
        ("date_confirmed", sa.Column("date_confirmed", sa.Boolean(), nullable=False, server_default=sa.false())),
        ("ocr_engine", sa.Column("ocr_engine", sa.String(60), nullable=True)),
        ("ocr_candidates_json", sa.Column("ocr_candidates_json", sa.Text(), nullable=False, server_default="[]")),
        ("correction_count", sa.Column("correction_count", sa.Integer(), nullable=False, server_default="0")),
    )
    for name, column in additions:
        if name not in columns:
            op.add_column("audit_result_items", column)


def downgrade():
    for name in ("correction_count", "ocr_candidates_json", "ocr_engine", "date_confirmed"):
        op.drop_column("audit_result_items", name)
