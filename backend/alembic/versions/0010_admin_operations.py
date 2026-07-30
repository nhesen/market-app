"""admin operations completeness

Revision ID: 0010
Revises: 0009
"""
from alembic import op
import sqlalchemy as sa

revision="0010";down_revision="0009";branch_labels=None;depends_on=None

def upgrade():
    inspector=sa.inspect(op.get_bind());tables=set(inspector.get_table_names())
    if "audit_templates" not in tables:op.create_table("audit_templates",
        sa.Column("id",sa.String(36),primary_key=True),sa.Column("organisation_id",sa.String(36),sa.ForeignKey("organisations.id"),nullable=False),sa.Column("branch_id",sa.String(36),sa.ForeignKey("branches.id"),nullable=True),sa.Column("name",sa.String(180),nullable=False),sa.Column("description",sa.Text(),nullable=False),sa.Column("category",sa.String(80),nullable=False),sa.Column("required_product_count",sa.Integer(),nullable=False,server_default="3"),sa.Column("require_unique_products",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("require_photo",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("require_expiry_date",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("default_priority",sa.String(20),nullable=False,server_default="MEDIUM"),sa.Column("expected_min_duration_seconds",sa.Integer(),nullable=False,server_default="60"),sa.Column("recurrence_type",sa.String(30),nullable=False,server_default="NONE"),sa.Column("active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_by",sa.String(36),sa.ForeignKey("users.id"),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("updated_at",sa.DateTime(),nullable=False),sa.UniqueConstraint("organisation_id","branch_id","name",name="uq_audit_template_scope_name"))
    if "audit_templates" not in tables:
        op.create_index("ix_audit_templates_organisation_id","audit_templates",["organisation_id"]);op.create_index("ix_audit_templates_branch_id","audit_templates",["branch_id"])
    if "template_id" not in {x["name"] for x in inspector.get_columns("audit_tasks")}:
        op.add_column("audit_tasks",sa.Column("template_id",sa.String(36),sa.ForeignKey("audit_templates.id"),nullable=True));op.create_index("ix_audit_tasks_template_id","audit_tasks",["template_id"])
    if "resolved" not in {x["name"] for x in inspector.get_columns("audit_quality_flags")}:op.add_column("audit_quality_flags",sa.Column("resolved",sa.Boolean(),nullable=False,server_default=sa.false()))
    if "due_at" not in {x["name"] for x in inspector.get_columns("re_audits")}:op.add_column("re_audits",sa.Column("due_at",sa.DateTime(),nullable=True))
    unique_names={x.get("name") for x in inspector.get_unique_constraints("products")}
    if "uq_product_org_barcode" not in unique_names:
        if "products_barcode_key" in unique_names:op.drop_constraint("products_barcode_key","products",type_="unique")
        op.create_unique_constraint("uq_product_org_barcode","products",["organisation_id","barcode"])

def downgrade():
    op.drop_constraint("uq_product_org_barcode","products",type_="unique");op.create_unique_constraint("products_barcode_key","products",["barcode"])
    op.drop_column("re_audits","due_at");op.drop_column("audit_quality_flags","resolved");op.drop_index("ix_audit_tasks_template_id",table_name="audit_tasks");op.drop_column("audit_tasks","template_id");op.drop_table("audit_templates")
