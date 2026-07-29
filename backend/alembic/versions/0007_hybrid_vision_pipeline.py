"""Hybrid vision rule telemetry and evidence metadata.

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision="0007";down_revision="0006";branch_labels=None;depends_on=None

def upgrade():
    bind=op.get_bind();inspector=sa.inspect(bind)
    rule_columns={x["name"] for x in inspector.get_columns("camera_rules")}
    event_columns={x["name"] for x in inspector.get_columns("camera_events")}
    clip_info={x["name"]:x for x in inspector.get_columns("camera_clip_metadata")};clip_columns=set(clip_info)
    for name,column in (
        ("detection_engine",sa.Column("detection_engine",sa.String(50),nullable=False,server_default="OPENCV_RULE_BASED")),
        ("current_state",sa.Column("current_state",sa.String(30),nullable=False,server_default="CLEAR")),
        ("last_frame_at",sa.Column("last_frame_at",sa.DateTime(timezone=True),nullable=True)),
        ("last_event_id",sa.Column("last_event_id",sa.String(36),nullable=True)),
        ("processing_error",sa.Column("processing_error",sa.Text(),nullable=True)),
        ("fps_estimate",sa.Column("fps_estimate",sa.Float(),nullable=True)),
    ):
        if name not in rule_columns:op.add_column("camera_rules",column)
    for name,column in (
        ("detection_engine",sa.Column("detection_engine",sa.String(50),nullable=False,server_default="OPENCV_RULE_BASED")),
        ("roi",sa.Column("roi",sa.String(120),nullable=False,server_default="0,0,1,1")),
        ("threshold",sa.Column("threshold",sa.Float(),nullable=False,server_default="0")),
        ("trigger_score",sa.Column("trigger_score",sa.Float(),nullable=True)),
    ):
        if name not in event_columns:op.add_column("camera_events",column)
    for name,column in (
        ("frame_number",sa.Column("frame_number",sa.Integer(),nullable=True)),
        ("source_timestamp_ms",sa.Column("source_timestamp_ms",sa.Float(),nullable=True)),
        ("engine",sa.Column("engine",sa.String(50),nullable=False,server_default="OPENCV_RULE_BASED")),
    ):
        if name not in clip_columns:op.add_column("camera_clip_metadata",column)
    if bind.dialect.name=="postgresql" and not getattr(clip_info["created_at"]["type"],"timezone",False):
        op.alter_column("camera_clip_metadata","created_at",existing_type=sa.DateTime(),type_=sa.DateTime(timezone=True),postgresql_using="created_at AT TIME ZONE 'UTC'")

def downgrade():
    for name in ("engine","source_timestamp_ms","frame_number"):op.drop_column("camera_clip_metadata",name)
    for name in ("trigger_score","threshold","roi","detection_engine"):op.drop_column("camera_events",name)
    for name in ("fps_estimate","processing_error","last_event_id","last_frame_at","current_state","detection_engine"):op.drop_column("camera_rules",name)
