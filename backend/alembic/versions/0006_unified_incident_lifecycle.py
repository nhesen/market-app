"""Unified incident lifecycle, assignment, SLA and immutable notes.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision="0006";down_revision="0005";branch_labels=None;depends_on=None

STATUSES="'NEW','PRECHECK','VERIFICATION_REQUIRED','VERIFIED','ASSIGNED','IN_PROGRESS','RESOLUTION_CANDIDATE','AUTO_RESOLVED','MANUALLY_RESOLVED','REJECTED','REOPENED','CANCELLED'"
SOURCES="'CUSTOMER_REPORT','STAFF_AUDIT','CAMERA_EVENT','MANUAL_ADMIN_ENTRY'"


def upgrade():
    bind=op.get_bind();dialect=bind.dialect.name;inspector=sa.inspect(bind)
    incident_columns={item["name"] for item in inspector.get_columns("incidents")}
    history_columns={item["name"] for item in inspector.get_columns("incident_status_history")}
    if dialect=="postgresql":
        enum_values={row[0] for row in bind.execute(sa.text("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid WHERE t.typname='incidentstatus'"))}
        if "NEW" not in enum_values:
            op.execute(f"CREATE TYPE incidentstatus_v2 AS ENUM ({STATUSES})")
            for table in ("incidents","customer_reports"):
                op.execute(f"ALTER TABLE {table} ALTER COLUMN status DROP DEFAULT")
                op.execute(f"ALTER TABLE {table} ALTER COLUMN status TYPE incidentstatus_v2 USING (CASE WHEN status::text='RESOLVED' THEN 'MANUALLY_RESOLVED' ELSE status::text END)::incidentstatus_v2")
            op.execute("ALTER TABLE incidents ALTER COLUMN status SET DEFAULT 'NEW'::incidentstatus_v2")
            op.execute("ALTER TABLE customer_reports ALTER COLUMN status SET DEFAULT 'NEW'::incidentstatus_v2")
            op.execute("ALTER TABLE incident_status_history ALTER COLUMN status TYPE incidentstatus_v2 USING (CASE WHEN status::text='RESOLVED' THEN 'MANUALLY_RESOLVED' ELSE status::text END)::incidentstatus_v2")
            op.execute("DROP TYPE incidentstatus")
            op.execute("ALTER TYPE incidentstatus_v2 RENAME TO incidentstatus")
        source_type=bind.execute(sa.text("SELECT udt_name FROM information_schema.columns WHERE table_name='incidents' AND column_name='source' AND table_schema=current_schema()" )).scalar()
        if source_type != "incidentsource":
            source_exists=bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname='incidentsource')")).scalar()
            if not source_exists:op.execute(f"CREATE TYPE incidentsource AS ENUM ({SOURCES})")
            op.execute("ALTER TABLE incidents ALTER COLUMN source TYPE incidentsource USING (CASE source::text WHEN 'CUSTOMER' THEN 'CUSTOMER_REPORT' WHEN 'CAMERA' THEN 'CAMERA_EVENT' WHEN 'STAFF_AUDIT' THEN 'STAFF_AUDIT' WHEN 'CUSTOMER_REPORT' THEN 'CUSTOMER_REPORT' WHEN 'CAMERA_EVENT' THEN 'CAMERA_EVENT' ELSE 'MANUAL_ADMIN_ENTRY' END)::incidentsource")
    additions=(
        ("assigned_staff_id",sa.Column("assigned_staff_id",sa.String(36),sa.ForeignKey("users.id"),nullable=True)),
        ("assigned_admin_id",sa.Column("assigned_admin_id",sa.String(36),sa.ForeignKey("users.id"),nullable=True)),
        ("sla_due_at",sa.Column("sla_due_at",sa.DateTime(timezone=True),nullable=True)),
        ("rejection_reason",sa.Column("rejection_reason",sa.Text(),nullable=True)),
        ("resolution_reason",sa.Column("resolution_reason",sa.Text(),nullable=True)),
        ("reopening_reason",sa.Column("reopening_reason",sa.Text(),nullable=True)),
        ("resolution_actor_type",sa.Column("resolution_actor_type",sa.String(20),nullable=True)),
    )
    for name,column in additions:
        if name not in incident_columns:op.add_column("incidents",column)
    for name in ("assigned_staff_id","assigned_admin_id","sla_due_at"):
        if name not in incident_columns:op.create_index(f"ix_incidents_{name}","incidents",[name])
    if "from_status" not in history_columns:
        if dialect=="postgresql":op.execute("ALTER TABLE incident_status_history ADD COLUMN from_status incidentstatus NULL")
        else:op.add_column("incident_status_history",sa.Column("from_status",sa.Enum("NEW","PRECHECK","VERIFICATION_REQUIRED","VERIFIED","ASSIGNED","IN_PROGRESS","RESOLUTION_CANDIDATE","AUTO_RESOLVED","MANUALLY_RESOLVED","REJECTED","REOPENED","CANCELLED",name="incidentstatus"),nullable=True))
    history_additions=(
        ("internal_note",sa.Column("internal_note",sa.Text(),nullable=True)),
        ("customer_note",sa.Column("customer_note",sa.Text(),nullable=True)),
        ("actor_type",sa.Column("actor_type",sa.String(20),nullable=False,server_default="MANUAL")),
    )
    for name,column in history_additions:
        if name not in history_columns:op.add_column("incident_status_history",column)
    if "incident_notes" not in inspector.get_table_names():
        op.create_table("incident_notes",sa.Column("id",sa.String(36),primary_key=True),sa.Column("incident_id",sa.String(36),sa.ForeignKey("incidents.id"),nullable=False),sa.Column("actor_id",sa.String(36),sa.ForeignKey("users.id"),nullable=True),sa.Column("visibility",sa.String(20),nullable=False),sa.Column("note",sa.Text(),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False));op.create_index("ix_incident_notes_incident_id","incident_notes",["incident_id"])


def downgrade():
    op.drop_table("incident_notes")
    for name in ("actor_type","customer_note","internal_note","from_status"):op.drop_column("incident_status_history",name)
    for name in ("resolution_actor_type","reopening_reason","resolution_reason","rejection_reason","sla_due_at","assigned_admin_id","assigned_staff_id"):op.drop_column("incidents",name)
