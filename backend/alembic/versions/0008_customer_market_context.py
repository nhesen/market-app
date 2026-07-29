"""separate customer market context from tenant ownership

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision="0008"
down_revision="0007"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("users",sa.Column("selected_organisation_id",sa.String(36),sa.ForeignKey("organisations.id"),nullable=True))
    op.create_index("ix_users_selected_organisation_id","users",["selected_organisation_id"])
    op.create_table("customer_market_memberships",
        sa.Column("id",sa.String(36),primary_key=True),
        sa.Column("customer_id",sa.String(36),sa.ForeignKey("users.id"),nullable=False),
        sa.Column("organisation_id",sa.String(36),sa.ForeignKey("organisations.id"),nullable=False),
        sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),
        sa.Column("joined_at",sa.DateTime(),nullable=False),
        sa.UniqueConstraint("customer_id","organisation_id",name="uq_customer_market_membership"))
    op.create_index("ix_customer_market_memberships_customer_id","customer_market_memberships",["customer_id"])
    op.create_index("ix_customer_market_memberships_organisation_id","customer_market_memberships",["organisation_id"])
    op.execute("UPDATE users SET selected_organisation_id = organisation_id WHERE role = 'CUSTOMER'")
    op.execute("INSERT INTO customer_market_memberships (id, customer_id, organisation_id, is_active, joined_at) SELECT md5(id || organisation_id), id, organisation_id, true, CURRENT_TIMESTAMP FROM users WHERE role = 'CUSTOMER' AND organisation_id IS NOT NULL")

def downgrade():
    op.drop_table("customer_market_memberships")
    op.drop_index("ix_users_selected_organisation_id",table_name="users")
    op.drop_column("users","selected_organisation_id")
