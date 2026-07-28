import secrets
from sqlalchemy.orm import Session
from app.models.domain import CustomerReport, Incident, IncidentStatus, IncidentStatusHistory, User
from app.schemas.api import ReportCreate
from app.models.retail import FileAsset,IncidentAttachment

def serialize_history(incident: Incident) -> list[dict]:
    return [{"status": h.status, "note": h.note, "created_at": h.created_at} for h in incident.history]

def report_view(report: CustomerReport) -> dict:
    return {"id": report.id, "tracking_number": report.tracking_number, "branch_id": report.branch_id, "category": report.category, "title": report.title, "description": report.description, "status": report.status, "created_at": report.created_at, "history": serialize_history(report.incident)}

def incident_view(incident: Incident) -> dict:
    return {"id": incident.id, "report_id": incident.report_id, "branch_id": incident.branch_id, "source": incident.source, "category": incident.category, "title": incident.title, "description": incident.description, "priority": incident.priority, "status": incident.status, "department": incident.department, "created_at": incident.created_at, "history": serialize_history(incident)}

def create_customer_report(db: Session, user: User, data: ReportCreate) -> CustomerReport:
    report = CustomerReport(tracking_number=f"MQ-{secrets.token_hex(4).upper()}", organisation_id=user.organisation_id, branch_id=data.branch_id, customer_id=user.id, category=data.category, title=data.title, description=data.description)
    incident = Incident(organisation_id=user.organisation_id, branch_id=data.branch_id, report=report, source="CUSTOMER", category=data.category, title=data.title, description=data.description)
    incident.history.append(IncidentStatusHistory(status=IncidentStatus.VERIFICATION_REQUIRED, note="Müştəri siqnalı qəbul edildi; filial təsdiqi tələb olunur.", actor_id=user.id))
    db.add(incident); db.commit(); db.refresh(report)
    for asset_id in data.attachment_ids:
        asset=db.get(FileAsset,asset_id)
        if asset and asset.owner_id==user.id and asset.organisation_id==user.organisation_id:db.add(IncidentAttachment(organisation_id=user.organisation_id,incident_id=incident.id,file_asset_id=asset.id))
    db.commit()
    return report

def set_status(db: Session, incident: Incident, status: IncidentStatus, note: str, actor: User, department: str | None = None):
    incident.status = status
    if department is not None: incident.department = department
    if incident.report: incident.report.status = status
    incident.history.append(IncidentStatusHistory(status=status, note=note, actor_id=actor.id))
    db.commit(); db.refresh(incident)
    return incident
