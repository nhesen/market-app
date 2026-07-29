from fastapi import HTTPException
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.domain import Branch, Incident, IncidentSource, IncidentStatus, User
from app.services.incidents import create_incident, customer_status, transition_incident


def auth(token): return {"Authorization":f"Bearer {token}"}


def test_valid_manual_resolution_and_immutable_history(database):
    with SessionLocal() as db:
        branch=db.scalar(select(Branch));admin=db.scalar(select(User).where(User.email=="branch@demo.az"));staff=db.scalar(select(User).where(User.email=="staff@demo.az"))
        incident=create_incident(db,organisation_id=branch.organisation_id,branch_id=branch.id,source=IncidentSource.MANUAL_ADMIN_ENTRY,category="OPERATIONS",title="Manual lifecycle QA",description="Full manual lifecycle",actor=admin);db.commit()
        sequence=[
            (IncidentStatus.PRECHECK,{}),(IncidentStatus.VERIFICATION_REQUIRED,{}),(IncidentStatus.VERIFIED,{}),
            (IncidentStatus.ASSIGNED,{"responsible_department":"Operations","assigned_staff_id":staff.id,"assigned_admin_id":admin.id,"sla_hours":4}),
            (IncidentStatus.IN_PROGRESS,{}),(IncidentStatus.RESOLUTION_CANDIDATE,{}),
            (IncidentStatus.MANUALLY_RESOLVED,{"resolution_reason":"Shelf was restored and verified."}),
        ]
        for target,extra in sequence:transition_incident(db,incident,target,actor=admin,internal_note=f"Move to {target.value}",customer_note=f"Customer: {target.value}",**extra)
        assert incident.status==IncidentStatus.MANUALLY_RESOLVED and incident.resolution_actor_type=="MANUAL"
        assert incident.sla_due_at and incident.assigned_staff_id==staff.id and incident.responsible_department=="Operations"
        assert len(incident.history)==8 and [row.from_status for row in incident.history[1:]]==[IncidentStatus.NEW,*[item[0] for item in sequence[:-1]]]
        assert all(row.actor_type=="MANUAL" and row.created_at for row in incident.history)


def test_invalid_transition_returns_clear_409(client,admin_token):
    branch=client.get("/api/v1/admin/branches",headers=auth(admin_token)).json()[0]
    created=client.post("/api/v1/admin/incidents",headers=auth(admin_token),json={"branch_id":branch["id"],"category":"QA","title":"Invalid transition QA","description":"Transition validation"}).json()
    response=client.patch(f'/api/v1/admin/incidents/{created["id"]}',headers=auth(admin_token),json={"status":"IN_PROGRESS","internal_note":"Skip required states"})
    assert response.status_code==409 and "Invalid incident transition NEW -> IN_PROGRESS" in response.json()["detail"] and "PRECHECK" in response.json()["detail"]


def test_rejection_and_reopening_require_reasons(database):
    with SessionLocal() as db:
        branch=db.scalar(select(Branch));admin=db.scalar(select(User).where(User.email=="branch@demo.az"))
        incident=create_incident(db,organisation_id=branch.organisation_id,branch_id=branch.id,source=IncidentSource.CUSTOMER_REPORT,category="QA",title="Reject QA",description="Reason validation",actor=admin);db.commit()
        transition_incident(db,incident,IncidentStatus.PRECHECK,actor=admin,internal_note="Precheck")
        try:transition_incident(db,incident,IncidentStatus.REJECTED,actor=admin,internal_note="Reject")
        except HTTPException as error:assert error.status_code==422 and "Rejection reason" in error.detail
        else:raise AssertionError("Reasonless rejection was accepted")
        transition_incident(db,incident,IncidentStatus.REJECTED,actor=admin,internal_note="Reject",customer_note="Müraciət sübutsuzdur.",rejection_reason="Evidence does not support the report.")
        try:transition_incident(db,incident,IncidentStatus.REOPENED,actor=admin,internal_note="Reopen")
        except HTTPException as error:assert error.status_code==422 and "Reopening reason" in error.detail
        else:raise AssertionError("Reasonless reopening was accepted")
        transition_incident(db,incident,IncidentStatus.REOPENED,actor=admin,internal_note="Reopen",reopening_reason="New evidence received.")
        assert incident.rejection_reason and incident.reopening_reason and incident.status==IncidentStatus.REOPENED


def test_camera_auto_resolution_and_customer_mapping(database):
    with SessionLocal() as db:
        branch=db.scalar(select(Branch));incident=create_incident(db,organisation_id=branch.organisation_id,branch_id=branch.id,source=IncidentSource.CAMERA_EVENT,category="SAFETY",title="Camera QA",description="Persistent hazard",status=IncidentStatus.VERIFIED);db.commit()
        transition_incident(db,incident,IncidentStatus.AUTO_RESOLVED,actor=None,internal_note="Clear threshold",resolution_reason="Condition cleared automatically.",automatic=True)
        assert incident.status==IncidentStatus.AUTO_RESOLVED and incident.resolution_actor_type=="AUTOMATIC"
        assert incident.history[-1].actor_type=="AUTOMATIC" and incident.history[-1].actor_id is None
        assert customer_status(IncidentStatus.AUTO_RESOLVED)=="RESOLVED" and customer_status(IncidentStatus.RESOLUTION_CANDIDATE)=="IN_PROGRESS"


def test_auto_resolution_is_camera_only(database):
    with SessionLocal() as db:
        branch=db.scalar(select(Branch));admin=db.scalar(select(User).where(User.email=="branch@demo.az"));incident=create_incident(db,organisation_id=branch.organisation_id,branch_id=branch.id,source=IncidentSource.STAFF_AUDIT,category="QA",title="Staff QA",description="No auto resolution",status=IncidentStatus.VERIFIED,actor=admin);db.commit()
        try:transition_incident(db,incident,IncidentStatus.AUTO_RESOLVED,actor=None,internal_note="Forbidden",resolution_reason="Forbidden",automatic=True)
        except HTTPException as error:assert error.status_code==409
        else:raise AssertionError("Non-camera incident auto-resolved")
