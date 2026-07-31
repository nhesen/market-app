"""customer companion completeness

Revision ID: 0011
Revises: 0010
"""
from alembic import op
import sqlalchemy as sa

revision="0011";down_revision="0010";branch_labels=None;depends_on=None

def _add(table:str,name:str,column:sa.Column)->None:
    columns={item["name"] for item in sa.inspect(op.get_bind()).get_columns(table)}
    if name not in columns:op.add_column(table,column)

def upgrade():
    _add("branches","image_url",sa.Column("image_url",sa.String(255),nullable=False,server_default="/assets/retail-branch-v2.png"))
    _add("branches","latitude",sa.Column("latitude",sa.Float(),nullable=True))
    _add("branches","longitude",sa.Column("longitude",sa.Float(),nullable=True))
    _add("products","package_size",sa.Column("package_size",sa.String(80),nullable=True))
    _add("news","body_az",sa.Column("body_az",sa.Text(),nullable=False,server_default=""))
    _add("news","body_en",sa.Column("body_en",sa.Text(),nullable=False,server_default=""))
    _add("news","content_type",sa.Column("content_type",sa.String(40),nullable=False,server_default="NEWS"))
    _add("news","status",sa.Column("status",sa.String(20),nullable=False,server_default="PUBLISHED"))
    _add("news","valid_until",sa.Column("valid_until",sa.DateTime(),nullable=True))
    _add("news","created_at",sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.func.now()))
    _add("news","updated_at",sa.Column("updated_at",sa.DateTime(),nullable=False,server_default=sa.func.now()))
    _add("notifications","related_entity_type",sa.Column("related_entity_type",sa.String(40),nullable=True))
    _add("notifications","related_entity_id",sa.Column("related_entity_id",sa.String(36),nullable=True))
    inspector=sa.inspect(op.get_bind())
    for table,column in (("news","content_type"),("news","status")):
        index=f"ix_{table}_{column}"
        if index not in {item["name"] for item in inspector.get_indexes(table)}:op.create_index(index,table,[column])

def downgrade():
    op.drop_index("ix_news_status",table_name="news");op.drop_index("ix_news_content_type",table_name="news")
    for table,names in (("notifications",("related_entity_id","related_entity_type")),("news",("updated_at","created_at","valid_until","status","content_type","body_en","body_az")),("products",("package_size",)),("branches",("longitude","latitude","image_url"))):
        for name in names:op.drop_column(table,name)
