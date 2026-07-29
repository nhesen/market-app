"""Complete customer reports, suggestions and loyalty.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision="0004";down_revision="0003";branch_labels=None;depends_on=None

suggestion_status=postgresql.ENUM("SUBMITTED","UNDER_REVIEW","PLANNED","IMPLEMENTED","REJECTED",name="suggestionstatus",create_type=False)

def upgrade():
    bind=op.get_bind();inspector=sa.inspect(bind);tables=set(inspector.get_table_names());columns={x["name"] for x in inspector.get_columns("customer_reports")}
    if "subcategory" not in columns:op.add_column("customer_reports",sa.Column("subcategory",sa.String(80),nullable=True))
    if "product_id" not in columns:
        op.add_column("customer_reports",sa.Column("product_id",sa.String(36),nullable=True));op.create_foreign_key("fk_customer_reports_product","customer_reports","products",["product_id"],["id"]);op.create_index("ix_customer_reports_product_id","customer_reports",["product_id"])
    if "barcode" not in columns:op.add_column("customer_reports",sa.Column("barcode",sa.String(32),nullable=True))
    if "suggestion_status_history" not in tables:
        op.create_table("suggestion_status_history",sa.Column("id",sa.String(36),primary_key=True),sa.Column("suggestion_id",sa.String(36),sa.ForeignKey("management_suggestions.id"),nullable=False),sa.Column("status",suggestion_status,nullable=False),sa.Column("note",sa.Text(),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False));op.create_index("ix_suggestion_status_history_suggestion_id","suggestion_status_history",["suggestion_id"])
    if "suggestion_attachments" not in tables:
        op.create_table("suggestion_attachments",sa.Column("id",sa.String(36),primary_key=True),sa.Column("organisation_id",sa.String(36),sa.ForeignKey("organisations.id"),nullable=False),sa.Column("suggestion_id",sa.String(36),sa.ForeignKey("management_suggestions.id"),nullable=False),sa.Column("file_asset_id",sa.String(36),sa.ForeignKey("file_assets.id"),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.UniqueConstraint("suggestion_id","file_asset_id"))
        for name in ("organisation_id","suggestion_id","file_asset_id"):op.create_index(f"ix_suggestion_attachments_{name}","suggestion_attachments",[name])
    if "loyalty_reward_offers" not in tables:
        op.create_table("loyalty_reward_offers",sa.Column("id",sa.String(36),primary_key=True),sa.Column("organisation_id",sa.String(36),sa.ForeignKey("organisations.id"),nullable=False),sa.Column("title_az",sa.String(180),nullable=False),sa.Column("title_en",sa.String(180),nullable=False),sa.Column("description_az",sa.Text(),nullable=False),sa.Column("description_en",sa.Text(),nullable=False),sa.Column("points_cost",sa.Integer(),nullable=False),sa.Column("image_url",sa.String(255),nullable=False),sa.Column("valid_until",sa.Date(),nullable=False),sa.Column("active",sa.Boolean(),nullable=False));op.create_index("ix_loyalty_reward_offers_organisation_id","loyalty_reward_offers",["organisation_id"])

def downgrade():
    op.drop_table("loyalty_reward_offers");op.drop_table("suggestion_attachments");op.drop_table("suggestion_status_history")
    op.drop_index("ix_customer_reports_product_id",table_name="customer_reports");op.drop_constraint("fk_customer_reports_product","customer_reports",type_="foreignkey")
    op.drop_column("customer_reports","barcode");op.drop_column("customer_reports","product_id");op.drop_column("customer_reports","subcategory")
