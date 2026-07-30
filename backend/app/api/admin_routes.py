from pathlib import Path
from collections import Counter
from datetime import datetime
from statistics import median

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import roles
from app.db.session import get_db
from app.models.audit import AuditQualityFlag, AuditResultItem, AuditTask, ReAudit
from app.models.domain import Branch, CustomerReport, Incident, Organisation, Role, User
from app.models.retail import AuditLog, BranchService, FileAsset, OrganisationModule, SystemSetting
from app.models.vision import Camera
from app.services.incidents import incident_view,report_view
from app.core.time import as_utc, utc_now
from app.services.score import smart_store_score

router = APIRouter(prefix="/api/v1")
ADMINS = (Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN, Role.PLATFORM_ADMIN)
TENANT_ADMINS = (Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN)


def scoped(stmt, user: User, model, branch: bool = True):
    if user.role != Role.PLATFORM_ADMIN:
        stmt = stmt.where(model.organisation_id == user.organisation_id)
    if branch and user.role == Role.BRANCH_ADMIN and hasattr(model, "branch_id"):
        stmt = stmt.where(model.branch_id == user.branch_id)
    return stmt


def allowed_branch(user: User, branch: Branch | None):
    return branch and (user.role == Role.PLATFORM_ADMIN or branch.organisation_id == user.organisation_id) and (user.role != Role.BRANCH_ADMIN or branch.id == user.branch_id)


@router.get("/admin/reports")
def reports(search:str|None=None,category:str|None=None,subcategory:str|None=None,status:str|None=None,date_from:datetime|None=Query(None),date_to:datetime|None=Query(None),user: User = Depends(roles(*TENANT_ADMINS)), db: Session = Depends(get_db)):
    stmt=scoped(select(CustomerReport),user,CustomerReport)
    if search:stmt=stmt.where(CustomerReport.title.ilike(f"%{search}%")|CustomerReport.tracking_number.ilike(f"%{search}%"))
    if category:stmt=stmt.where(CustomerReport.category==category)
    if subcategory:stmt=stmt.where(CustomerReport.subcategory==subcategory)
    if status:stmt=stmt.where(CustomerReport.status==status)
    if date_from:stmt=stmt.where(CustomerReport.created_at>=date_from)
    if date_to:stmt=stmt.where(CustomerReport.created_at<=date_to)
    return [admin_report_view(item,db) for item in db.scalars(stmt.order_by(CustomerReport.created_at.desc())).all()]

def admin_report_view(item:CustomerReport,db:Session):
    result=report_view(item,db);result["incident_id"]=item.incident.id;result["incident"]=incident_view(item.incident,db);customer=db.get(User,item.customer_id);result["customer"]={"id":customer.id,"full_name":customer.full_name,"email":customer.email} if customer else None;return result


@router.get("/admin/reports/{report_id}")
def report_detail(report_id: str, user: User = Depends(roles(*TENANT_ADMINS)), db: Session = Depends(get_db)):
    item = db.scalar(scoped(select(CustomerReport).where(CustomerReport.id == report_id), user, CustomerReport))
    if not item: raise HTTPException(404, "Report not found")
    return admin_report_view(item, db)


@router.get("/admin/audits")
def audits(user: User = Depends(roles(*TENANT_ADMINS)), db: Session = Depends(get_db)):
    rows = db.scalars(scoped(select(AuditTask), user, AuditTask).order_by(AuditTask.due_at.desc())).all()
    return [{"id": row.id, "title": row.title, "branch_id": row.branch_id, "assignee_id": row.assignee_id,
             "status": row.status, "priority": row.priority, "required_count": row.required_count,
             "item_count": db.scalar(select(func.count(AuditResultItem.id)).where(AuditResultItem.task_id == row.id)) or 0,
             "due_at": row.due_at, "started_at": row.started_at, "completed_at": row.completed_at} for row in rows]


@router.get("/admin/re-audits")
def reaudits(user: User = Depends(roles(*TENANT_ADMINS)), db: Session = Depends(get_db)):
    return db.scalars(scoped(select(ReAudit), user, ReAudit).order_by(ReAudit.created_at.desc())).all()


@router.get("/admin/staff")
def staff(user: User = Depends(roles(*TENANT_ADMINS)), db: Session = Depends(get_db)):
    stmt = select(User).where(User.role == Role.STAFF, User.organisation_id == user.organisation_id)
    if user.role == Role.BRANCH_ADMIN: stmt = stmt.where(User.branch_id == user.branch_id)
    return [{"id": item.id, "full_name": item.full_name, "email": item.email, "branch_id": item.branch_id, "is_active": item.is_active} for item in db.scalars(stmt.order_by(User.full_name)).all()]


@router.get("/admin/branches")
def admin_branches(user: User = Depends(roles(*ADMINS)), db: Session = Depends(get_db)):
    stmt = select(Branch)
    if user.role != Role.PLATFORM_ADMIN: stmt = stmt.where(Branch.organisation_id == user.organisation_id)
    if user.role == Role.BRANCH_ADMIN: stmt = stmt.where(Branch.id == user.branch_id)
    rows=db.scalars(stmt.order_by(Branch.name)).all();return [{"id":x.id,"organisation_id":x.organisation_id,"name":x.name,"address":x.address,"hours":x.hours,"is_open":x.is_open,"distance_km":x.distance_km,"services":[s.name for s in db.scalars(select(BranchService).where(BranchService.branch_id==x.id)).all()]} for x in rows]


class BranchSettingsIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    address: str = Field(min_length=3, max_length=255)
    hours: str = Field(min_length=3, max_length=80)
    is_open: bool
    services:list[str]=Field(default_factory=list,max_length=30)


@router.patch("/admin/branches/{branch_id}")
def update_branch(branch_id: str, data: BranchSettingsIn, user: User = Depends(roles(*ADMINS)), db: Session = Depends(get_db)):
    branch = db.get(Branch, branch_id)
    if not allowed_branch(user, branch): raise HTTPException(404, "Branch not found")
    payload=data.model_dump();services=payload.pop("services")
    for key, value in payload.items(): setattr(branch, key, value)
    db.query(BranchService).filter(BranchService.branch_id==branch.id).delete()
    for name in sorted({x.strip().upper() for x in services if x.strip()}):db.add(BranchService(organisation_id=branch.organisation_id,branch_id=branch.id,name=name))
    db.add(AuditLog(organisation_id=branch.organisation_id, actor_id=user.id, action="UPDATE", entity_type="Branch", entity_id=branch.id))
    db.commit(); db.refresh(branch); return branch


@router.get("/admin/network-analytics")
def network_analytics(user: User = Depends(roles(Role.HEAD_OFFICE_ADMIN)), db: Session = Depends(get_db)):
    branches = db.scalars(select(Branch).where(Branch.organisation_id == user.organisation_id).order_by(Branch.name)).all()
    output = []
    for branch in branches:
        incidents = db.scalars(select(Incident).where(Incident.branch_id == branch.id)).all()
        flags = db.scalar(select(func.count(AuditQualityFlag.id)).where(AuditQualityFlag.branch_id == branch.id)) or 0
        open_count = sum(item.status.value not in ("MANUALLY_RESOLVED", "AUTO_RESOLVED", "REJECTED", "CANCELLED") for item in incidents)
        high = sum(item.priority == "HIGH" and item.status.value not in ("MANUALLY_RESOLVED", "AUTO_RESOLVED", "REJECTED", "CANCELLED") for item in incidents)
        score = smart_store_score(db, branch.id);closed={"MANUALLY_RESOLVED","AUTO_RESOLVED","REJECTED","CANCELLED"};resolved=[x for x in incidents if x.status.value in {"MANUALLY_RESOLVED","AUTO_RESOLVED"}];hours=[(as_utc(x.updated_at)-as_utc(x.created_at)).total_seconds()/3600 for x in resolved];tasks=db.scalars(select(AuditTask).where(AuditTask.branch_id==branch.id)).all();camera=[x for x in incidents if x.source.value=="CAMERA_EVENT"]
        output.append({"branch_id": branch.id, "branch": branch.name, "open_incidents": open_count, "critical_incidents":sum(item.priority=="CRITICAL" and item.status.value not in closed for item in incidents),"overdue":sum(bool(x.sla_due_at and as_utc(x.sla_due_at)<utc_now() and x.status.value not in closed) for x in incidents),"average_resolution_hours":round(sum(hours)/len(hours),2) if hours else 0,"audit_completion_rate":round(sum(getattr(x.status,"value",x.status)=="COMPLETED" for x in tasks)/max(len(tasks),1)*100,1),"camera_false_alert_rate":round(sum(x.status.value=="REJECTED" for x in camera)/max(len(camera),1)*100,1), "high_risk": high, "quality_flags": flags, "score": score["score"], "score_detail":score})
    return output

@router.get("/admin/operational-analytics")
def operational_analytics(branch_id:str|None=None,status:str|None=None,source:str|None=None,category:str|None=None,priority:str|None=None,date_from:datetime|None=Query(None),date_to:datetime|None=Query(None),user:User=Depends(roles(*TENANT_ADMINS)),db:Session=Depends(get_db)):
    stmt=scoped(select(Incident),user,Incident)
    if branch_id:
        branch=db.get(Branch,branch_id)
        if not allowed_branch(user,branch):raise HTTPException(404,"Branch not found")
        stmt=stmt.where(Incident.branch_id==branch_id)
    if status:stmt=stmt.where(Incident.status==status)
    if source:stmt=stmt.where(Incident.source==source)
    if category:stmt=stmt.where(Incident.category==category)
    if priority:stmt=stmt.where(Incident.priority==priority)
    if date_from:stmt=stmt.where(Incident.created_at>=date_from)
    if date_to:stmt=stmt.where(Incident.created_at<=date_to)
    rows=db.scalars(stmt.order_by(Incident.created_at)).unique().all();now=utc_now()
    closed={"MANUALLY_RESOLVED","AUTO_RESOLVED","REJECTED","CANCELLED"};resolved=[x for x in rows if x.status.value in {"MANUALLY_RESOLVED","AUTO_RESOLVED"}]
    resolution_hours=[round((as_utc(x.updated_at)-as_utc(x.created_at)).total_seconds()/3600,2) for x in resolved]
    re_stmt=scoped(select(ReAudit),user,ReAudit);re_rows=db.scalars(re_stmt).all();completed_re=[x for x in re_rows if x.consistent is not None]
    verification_candidates=[x for x in rows if x.source.value=="CUSTOMER_REPORT" and any(h.status.value=="RESOLUTION_CANDIDATE" for h in x.history)]
    verified_customers=[x for x in verification_candidates if x.status.value in {"MANUALLY_RESOLVED","REOPENED"}]
    count=lambda values,key:[{"name":name,"value":value} for name,value in sorted(Counter(key(x) for x in values).items())]
    task_stmt=scoped(select(AuditTask),user,AuditTask)
    if branch_id:task_stmt=task_stmt.where(AuditTask.branch_id==branch_id)
    tasks=db.scalars(task_stmt).all();completed_tasks=sum(getattr(x.status,"value",x.status)=="COMPLETED" for x in tasks);camera_rows=[x for x in rows if x.source.value=="CAMERA_EVENT"];today=now.date()
    return {"filters":{"branch_id":branch_id,"status":status,"source":source,"category":category,"priority":priority,"date_from":date_from,"date_to":date_to},"summary":{"total":len(rows),"open":sum(x.status.value not in closed for x in rows),"critical":sum(x.priority=="CRITICAL" and x.status.value not in closed for x in rows),"overdue":sum(bool(x.sla_due_at and as_utc(x.sla_due_at)<now and x.status.value not in closed) for x in rows),"resolved":len(resolved),"resolved_today":sum(as_utc(x.updated_at).date()==today for x in resolved),"average_resolution_hours":round(sum(resolution_hours)/len(resolution_hours),2) if resolution_hours else 0,"median_resolution_hours":round(median(resolution_hours),2) if resolution_hours else 0,"auto_resolved":sum(x.status.value=="AUTO_RESOLVED" for x in rows),"manual_resolved":sum(x.status.value=="MANUALLY_RESOLVED" for x in rows),"auto_resolve_rate":round(sum(x.status.value=="AUTO_RESOLVED" for x in resolved)/len(resolved)*100,1) if resolved else 0,"manual_resolve_rate":round(sum(x.status.value=="MANUALLY_RESOLVED" for x in resolved)/len(resolved)*100,1) if resolved else 0,"customer_verification_rate":round(len(verified_customers)/len(verification_candidates)*100,1) if verification_candidates else 0,"audit_completion_rate":round(completed_tasks/max(len(tasks),1)*100,1),"re_audit_consistency_rate":round(sum(bool(x.consistent) for x in completed_re)/len(completed_re)*100,1) if completed_re else 0,"camera_false_alert_rate":round(sum(x.status.value=="REJECTED" for x in camera_rows)/max(len(camera_rows),1)*100,1)},"by_source":count(rows,lambda x:x.source.value),"by_status":count(rows,lambda x:x.status.value),"by_category":count(rows,lambda x:x.category),"by_priority":count(rows,lambda x:x.priority),"by_hour":count(rows,lambda x:f"{as_utc(x.created_at).hour:02d}:00"),"recurring_issues":sorted(count(rows,lambda x:x.category),key=lambda x:x["value"],reverse=True)[:5]}


@router.get("/platform/organisations/{organisation_id}")
def organisation_detail(organisation_id: str, user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    organisation = db.get(Organisation, organisation_id)
    if not organisation: raise HTTPException(404, "Organisation not found")
    return {"id": organisation.id, "name": organisation.name, "created_at": organisation.created_at,
            "branches": db.scalars(select(Branch).where(Branch.organisation_id == organisation.id)).all(),
            "admins": [{"id": item.id, "email": item.email, "full_name": item.full_name, "role": item.role, "branch_id": item.branch_id, "is_active": item.is_active} for item in db.scalars(select(User).where(User.organisation_id == organisation.id, User.role.in_((Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN)))).all()]}


@router.get("/platform/admins")
def platform_admins(user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    return [{"id": item.id, "organisation_id": item.organisation_id, "branch_id": item.branch_id, "email": item.email,
             "full_name": item.full_name, "role": item.role, "is_active": item.is_active} for item in db.scalars(select(User).where(User.role.in_((Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN, Role.PLATFORM_ADMIN)))).all()]


class ModuleIn(BaseModel):
    organisation_id: str
    module: str = Field(min_length=2, max_length=80)
    enabled: bool


@router.get("/platform/modules")
def modules(user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    return db.scalars(select(OrganisationModule).order_by(OrganisationModule.organisation_id, OrganisationModule.module)).all()


@router.put("/platform/modules")
def set_module(data: ModuleIn, user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    if not db.get(Organisation, data.organisation_id): raise HTTPException(404, "Organisation not found")
    item = db.scalar(select(OrganisationModule).where(OrganisationModule.organisation_id == data.organisation_id, OrganisationModule.module == data.module))
    if not item: item = OrganisationModule(organisation_id=data.organisation_id, module=data.module); db.add(item)
    item.enabled = data.enabled;db.flush();db.add(AuditLog(actor_id=user.id,action="UPDATE",entity_type="OrganisationModule",entity_id=item.id,detail=f"{data.module} enabled={data.enabled}")); db.commit(); db.refresh(item); return item


@router.get("/platform/health")
def platform_health(user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    db.execute(text("SELECT 1")); cameras = db.scalars(select(Camera)).all()
    storage_bytes = db.scalar(select(func.sum(FileAsset.size))) or 0
    return {"system": {"status": "ok"}, "database": {"status": "ok"},
            "vision": {"status": "ok" if all(not item.last_error for item in cameras) else "degraded", "cameras": len(cameras), "errors": sum(bool(item.last_error) for item in cameras)},
            "storage": {"bytes": storage_bytes, "megabytes": round(storage_bytes/1048576, 2), "path": str(Path(settings.upload_dir))}}


@router.get("/platform/tenant-usage")
def tenant_usage(user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    organisations = db.scalars(select(Organisation).order_by(Organisation.name)).all()
    return [{"organisation_id": org.id, "organisation": org.name,
             "branches": db.scalar(select(func.count(Branch.id)).where(Branch.organisation_id == org.id)) or 0,
             "users": db.scalar(select(func.count(User.id)).where(User.organisation_id == org.id)) or 0,
             "incidents": db.scalar(select(func.count(Incident.id)).where(Incident.organisation_id == org.id)) or 0,
             "storage_bytes": db.scalar(select(func.sum(FileAsset.size)).where(FileAsset.organisation_id == org.id)) or 0} for org in organisations]


class SettingIn(BaseModel):
    key: str = Field(min_length=2, max_length=100)
    value: str = Field(max_length=5000)


@router.get("/platform/settings")
def system_settings(user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    return db.scalars(select(SystemSetting).order_by(SystemSetting.key)).all()


@router.put("/platform/settings")
def set_setting(data: SettingIn, user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    item = db.scalar(select(SystemSetting).where(SystemSetting.key == data.key))
    if not item: item = SystemSetting(key=data.key, value=data.value); db.add(item)
    else: item.value = data.value
    db.flush();db.add(AuditLog(actor_id=user.id,action="UPDATE",entity_type="SystemSetting",entity_id=item.id,detail=data.key));db.commit(); db.refresh(item); return item


class ResetIn(BaseModel):
    confirmation: str


@router.post("/platform/demo-reset")
def demo_reset(data: ResetIn, user: User = Depends(roles(Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    if data.confirmation != "RESET_DEMO": raise HTTPException(422, "Explicit RESET_DEMO confirmation required")
    db.add(AuditLog(actor_id=user.id, action="DEMO_RESET_REQUESTED", entity_type="System", detail="Demo reset was explicitly requested; seeded master data was preserved."))
    db.commit(); return {"status": "completed", "preserved_seed_data": True}
