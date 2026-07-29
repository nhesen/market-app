import secrets
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc, utc_now
from app.models.domain import CustomerReport, Incident, IncidentNote, IncidentSource, IncidentStatus, IncidentStatusHistory, Role, User
from app.models.retail import FileAsset, IncidentAttachment
from app.schemas.api import ReportCreate

CLOSED={IncidentStatus.AUTO_RESOLVED,IncidentStatus.MANUALLY_RESOLVED,IncidentStatus.REJECTED,IncidentStatus.CANCELLED}
BASE={
    IncidentStatus.NEW:{IncidentStatus.PRECHECK,IncidentStatus.CANCELLED},
    IncidentStatus.PRECHECK:{IncidentStatus.VERIFICATION_REQUIRED,IncidentStatus.VERIFIED,IncidentStatus.REJECTED,IncidentStatus.CANCELLED},
    IncidentStatus.VERIFICATION_REQUIRED:{IncidentStatus.VERIFIED,IncidentStatus.REJECTED,IncidentStatus.CANCELLED},
    IncidentStatus.VERIFIED:{IncidentStatus.ASSIGNED,IncidentStatus.IN_PROGRESS,IncidentStatus.REJECTED,IncidentStatus.CANCELLED},
    IncidentStatus.ASSIGNED:{IncidentStatus.IN_PROGRESS,IncidentStatus.CANCELLED},
    IncidentStatus.IN_PROGRESS:{IncidentStatus.RESOLUTION_CANDIDATE,IncidentStatus.CANCELLED},
    IncidentStatus.RESOLUTION_CANDIDATE:{IncidentStatus.MANUALLY_RESOLVED,IncidentStatus.IN_PROGRESS},
    IncidentStatus.AUTO_RESOLVED:{IncidentStatus.REOPENED},
    IncidentStatus.MANUALLY_RESOLVED:{IncidentStatus.REOPENED},
    IncidentStatus.REJECTED:{IncidentStatus.REOPENED},
    IncidentStatus.REOPENED:{IncidentStatus.ASSIGNED,IncidentStatus.IN_PROGRESS,IncidentStatus.CANCELLED},
    IncidentStatus.CANCELLED:{IncidentStatus.REOPENED},
}


def allowed_transitions(incident:Incident):
    result=set(BASE.get(incident.status,set()))
    if incident.source==IncidentSource.CAMERA_EVENT and incident.status in {IncidentStatus.VERIFICATION_REQUIRED,IncidentStatus.VERIFIED,IncidentStatus.IN_PROGRESS,IncidentStatus.RESOLUTION_CANDIDATE}:
        result.add(IncidentStatus.AUTO_RESOLVED)
    return result


def customer_status(status:IncidentStatus):
    if status in {IncidentStatus.NEW,IncidentStatus.PRECHECK,IncidentStatus.VERIFICATION_REQUIRED}:return "RECEIVED"
    if status in {IncidentStatus.VERIFIED,IncidentStatus.ASSIGNED}:return "CONFIRMED"
    if status in {IncidentStatus.IN_PROGRESS,IncidentStatus.RESOLUTION_CANDIDATE,IncidentStatus.REOPENED}:return "IN_PROGRESS"
    if status in {IncidentStatus.AUTO_RESOLVED,IncidentStatus.MANUALLY_RESOLVED}:return "RESOLVED"
    if status==IncidentStatus.REJECTED:return "REJECTED"
    return "CANCELLED"


def serialize_history(incident:Incident,customer:bool=False):
    rows=[]
    for item in incident.history:
        rows.append({"from_status":item.from_status,"status":customer_status(item.status) if customer else item.status,
                     "note":(item.customer_note or "") if customer else item.note,"internal_note":None if customer else item.internal_note,
                     "customer_note":item.customer_note,"actor_id":None if customer else item.actor_id,
                     "actor_type":item.actor_type,"created_at":item.created_at})
    return rows


def _media(db:Session,incident:Incident,customer_only=False):
    stmt=select(IncidentAttachment,FileAsset).join(FileAsset,FileAsset.id==IncidentAttachment.file_asset_id).where(IncidentAttachment.incident_id==incident.id)
    if customer_only:stmt=stmt.where(IncidentAttachment.customer_visible==True)
    return [{"id":asset.id,"name":asset.original_name,"mime_type":asset.mime_type,"url":f"/uploads/{asset.storage_key}","customer_visible":link.customer_visible} for link,asset in db.execute(stmt).all()]


def report_view(report:CustomerReport,db:Session|None=None):
    incident=report.incident;history=serialize_history(incident,True)
    notes=[]
    if db:notes=[{"note":item.note,"created_at":item.created_at} for item in db.scalars(select(IncidentNote).where(IncidentNote.incident_id==incident.id,IncidentNote.visibility=="CUSTOMER").order_by(IncidentNote.created_at)).all()]
    return {"id":report.id,"tracking_number":report.tracking_number,"branch_id":report.branch_id,"category":report.category,"subcategory":report.subcategory,"product_id":report.product_id,"barcode":report.barcode,"title":report.title,"description":report.description,"status":report.status,"customer_status":customer_status(incident.status),"created_at":report.created_at,"history":history,"notes":notes,"media":_media(db,incident,True) if db else [],"rejection_reason":incident.rejection_reason,"resolution_note":incident.resolution_reason,"reopening_reason":incident.reopening_reason}


def incident_view(incident:Incident,db:Session|None=None):
    now=utc_now();due=as_utc(incident.sla_due_at) if incident.sla_due_at else None
    notes=[]
    if db:notes=[{"id":item.id,"visibility":item.visibility,"note":item.note,"actor_id":item.actor_id,"created_at":item.created_at} for item in db.scalars(select(IncidentNote).where(IncidentNote.incident_id==incident.id).order_by(IncidentNote.created_at)).all()]
    return {"id":incident.id,"report_id":incident.report_id,"organisation_id":incident.organisation_id,"branch_id":incident.branch_id,"source":incident.source,"category":incident.category,"title":incident.title,"description":incident.description,"priority":incident.priority,"status":incident.status,"responsible_department":incident.responsible_department,"department":incident.responsible_department,"assigned_staff_id":incident.assigned_staff_id,"assigned_admin_id":incident.assigned_admin_id,"sla_due_at":incident.sla_due_at,"is_overdue":bool(due and due<now and incident.status not in CLOSED),"rejection_reason":incident.rejection_reason,"resolution_reason":incident.resolution_reason,"reopening_reason":incident.reopening_reason,"resolution_actor_type":incident.resolution_actor_type,"created_at":incident.created_at,"updated_at":incident.updated_at,"allowed_transitions":[item.value for item in allowed_transitions(incident)],"history":serialize_history(incident),"notes":notes,"attachments":_media(db,incident) if db else []}


def create_incident(db:Session,*,organisation_id:str,branch_id:str,source:IncidentSource,category:str,title:str,description:str,priority:str="MEDIUM",actor:User|None=None,report:CustomerReport|None=None,status:IncidentStatus|None=None,customer_note:str|None=None):
    initial=status or (IncidentStatus.NEW if source in {IncidentSource.CUSTOMER_REPORT,IncidentSource.MANUAL_ADMIN_ENTRY} else IncidentStatus.VERIFICATION_REQUIRED)
    item=Incident(organisation_id=organisation_id,branch_id=branch_id,report=report,source=source,category=category,title=title,description=description,priority=priority,status=initial)
    item.history.append(IncidentStatusHistory(status=initial,from_status=None,note=customer_note or f"Incident created from {source.value}.",customer_note=customer_note,actor_id=actor.id if actor else None,actor_type="MANUAL" if actor else "AUTOMATIC"))
    db.add(item);return item


def transition_incident(db:Session,incident:Incident,target:IncidentStatus,*,actor:User|None,internal_note:str,customer_note:str|None=None,responsible_department:str|None=None,assigned_staff_id:str|None=None,assigned_admin_id:str|None=None,sla_hours:int|None=None,rejection_reason:str|None=None,resolution_reason:str|None=None,reopening_reason:str|None=None,automatic:bool=False,attachment_ids:list[str]|None=None):
    if target not in allowed_transitions(incident):
        allowed=", ".join(sorted(item.value for item in allowed_transitions(incident))) or "none"
        raise HTTPException(409,f"Invalid incident transition {incident.status.value} -> {target.value}. Allowed: {allowed}")
    if automatic and target!=IncidentStatus.AUTO_RESOLVED:raise HTTPException(422,"Automatic actor may only use AUTO_RESOLVED")
    if target==IncidentStatus.AUTO_RESOLVED and (incident.source!=IncidentSource.CAMERA_EVENT or not automatic):raise HTTPException(422,"AUTO_RESOLVED requires an automatic camera actor")
    if target==IncidentStatus.ASSIGNED and not (assigned_staff_id or assigned_admin_id or incident.assigned_staff_id or incident.assigned_admin_id):raise HTTPException(422,"ASSIGNED requires a staff or admin assignee")
    if target==IncidentStatus.ASSIGNED and not (responsible_department or incident.responsible_department):raise HTTPException(422,"ASSIGNED requires a responsible department")
    if assigned_staff_id:
        assignee=db.get(User,assigned_staff_id)
        if not assignee or assignee.role!=Role.STAFF or assignee.organisation_id!=incident.organisation_id or assignee.branch_id!=incident.branch_id:raise HTTPException(422,"Staff assignee must belong to the incident branch")
    if assigned_admin_id:
        assignee=db.get(User,assigned_admin_id)
        if not assignee or assignee.role not in {Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN} or assignee.organisation_id!=incident.organisation_id or (assignee.role==Role.BRANCH_ADMIN and assignee.branch_id!=incident.branch_id):raise HTTPException(422,"Admin assignee is outside incident scope")
    if target==IncidentStatus.REJECTED and not rejection_reason:raise HTTPException(422,"Rejection reason is required")
    if target in {IncidentStatus.AUTO_RESOLVED,IncidentStatus.MANUALLY_RESOLVED} and not resolution_reason:raise HTTPException(422,"Resolution reason is required")
    if target==IncidentStatus.REOPENED and not reopening_reason:raise HTTPException(422,"Reopening reason is required")
    if actor and actor.role!=Role.PLATFORM_ADMIN:
        if actor.organisation_id!=incident.organisation_id or (actor.role==Role.BRANCH_ADMIN and actor.branch_id!=incident.branch_id):raise HTTPException(404,"Incident not found")
    previous=incident.status;incident.status=target
    if responsible_department is not None:incident.responsible_department=responsible_department
    if assigned_staff_id is not None:incident.assigned_staff_id=assigned_staff_id
    if assigned_admin_id is not None:incident.assigned_admin_id=assigned_admin_id
    if sla_hours is not None:incident.sla_due_at=utc_now()+timedelta(hours=sla_hours)
    if rejection_reason:incident.rejection_reason=rejection_reason
    if resolution_reason:incident.resolution_reason=resolution_reason
    if reopening_reason:incident.reopening_reason=reopening_reason
    if target in {IncidentStatus.AUTO_RESOLVED,IncidentStatus.MANUALLY_RESOLVED}:incident.resolution_actor_type="AUTOMATIC" if automatic else "MANUAL"
    if incident.report:incident.report.status=target
    incident.history.append(IncidentStatusHistory(from_status=previous,status=target,note=internal_note,internal_note=internal_note,customer_note=customer_note,actor_id=actor.id if actor else None,actor_type="AUTOMATIC" if automatic else "MANUAL"))
    for asset_id in attachment_ids or []:
        asset=db.get(FileAsset,asset_id)
        if asset and asset.organisation_id==incident.organisation_id:db.add(IncidentAttachment(organisation_id=incident.organisation_id,incident_id=incident.id,file_asset_id=asset.id,customer_visible=bool(customer_note)))
    db.commit();db.refresh(incident);return incident


def add_note(db:Session,incident:Incident,actor:User,note:str,customer_visible:bool):
    item=IncidentNote(incident_id=incident.id,actor_id=actor.id,visibility="CUSTOMER" if customer_visible else "INTERNAL",note=note);db.add(item);db.commit();db.refresh(item);return item


def create_customer_report(db:Session,user:User,data:ReportCreate):
    report=CustomerReport(tracking_number=f"MQ-{secrets.token_hex(4).upper()}",organisation_id=user.organisation_id,branch_id=data.branch_id,customer_id=user.id,category=data.category,subcategory=data.subcategory,product_id=data.product_id,barcode=data.barcode,title=data.title,description=data.description,status=IncidentStatus.NEW)
    incident=create_incident(db,organisation_id=user.organisation_id,branch_id=data.branch_id,report=report,source=IncidentSource.CUSTOMER_REPORT,category=data.category,title=data.title,description=data.description,actor=user,customer_note="Müraciətiniz qəbul edildi.")
    db.commit();db.refresh(report)
    for asset_id in data.attachment_ids:
        asset=db.get(FileAsset,asset_id)
        if asset and asset.owner_id==user.id and asset.organisation_id==user.organisation_id:db.add(IncidentAttachment(organisation_id=user.organisation_id,incident_id=incident.id,file_asset_id=asset.id,customer_visible=True))
    db.commit();return report


def set_status(db:Session,incident:Incident,status:IncidentStatus,note:str,actor:User,department:str|None=None):
    return transition_incident(db,incident,status,actor=actor,internal_note=note,customer_note=note,responsible_department=department,
                               rejection_reason=note if status==IncidentStatus.REJECTED else None,
                               resolution_reason=note if status==IncidentStatus.MANUALLY_RESOLVED else None,
                               reopening_reason=note if status==IncidentStatus.REOPENED else None)
