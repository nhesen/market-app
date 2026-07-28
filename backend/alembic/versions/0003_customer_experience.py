"""Customer preferences, profile and campaign favourites.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("profile_image_url", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("preferred_branch_id", sa.String(36), nullable=True))
    op.add_column("users", sa.Column("preferences_json", sa.Text(), nullable=False, server_default="{}"))
    op.create_foreign_key("fk_users_preferred_branch", "users", "branches", ["preferred_branch_id"], ["id"])
    op.add_column("loyalty_cards", sa.Column("label", sa.String(80), nullable=False, server_default="Bonus kartı"))
    op.add_column("loyalty_cards", sa.Column("card_number", sa.String(24), nullable=False, server_default="9900000000000000"))
    op.add_column("loyalty_cards", sa.Column("expiring_on", sa.DateTime(), nullable=True))
    op.create_table(
        "favourite_campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organisation_id", sa.String(36), sa.ForeignKey("organisations.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("campaign_id", sa.String(36), sa.ForeignKey("discount_campaigns.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "campaign_id"),
    )
    op.create_index("ix_favourite_campaigns_organisation_id", "favourite_campaigns", ["organisation_id"])
    op.create_index("ix_favourite_campaigns_user_id", "favourite_campaigns", ["user_id"])
    op.create_index("ix_favourite_campaigns_campaign_id", "favourite_campaigns", ["campaign_id"])


def downgrade():
    op.drop_table("favourite_campaigns")
    op.drop_constraint("fk_users_preferred_branch", "users", type_="foreignkey")
    op.drop_column("loyalty_cards", "expiring_on")
    op.drop_column("loyalty_cards", "card_number")
    op.drop_column("loyalty_cards", "label")
    op.drop_column("users", "preferences_json")
    op.drop_column("users", "preferred_branch_id")
    op.drop_column("users", "profile_image_url")
