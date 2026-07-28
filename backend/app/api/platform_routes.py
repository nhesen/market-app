from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.core.security import hash_password,roles
from app.db.session import get_db
from app.models.audit import AuditQualityFlag,AuditStatus,AuditTask
from app.models.domain import Branch,Incident,IncidentStatus,Organisation,Role,User
from app.core.time import utc_now

router=APIRouter(prefix="/api/v1")
class OrganisationIn(BaseModel): name:str=Field(min_length=2,max_length=160)
class BranchIn(BaseModel): organisation_id:str;name:str=Field(min_length=2,max_length=160);address:str;hours:str="08:00–23:00"
class AdminIn(BaseModel): organisation_id:str;branch_id:str|None=None;email:str;full_name:str;password:str=Field(min_length=8,max_length=72);role:Role

def score_data(rows:list[Incident],overdue:int,valid_audits:int):
    closed={IncidentStatus.RESOLVED,IncidentStatus.AUTO_RESOLVED,IncidentStatus.REJECTED}
    high=sum(i.priority=="HIGH" and i.status not in closed for i in rows);other=sum(i.priority!="HIGH" and i.status not in closed for i in rows);bonus=min(10,valid_audits)
    deductions=[{"label":"Açıq yüksək risk","count":high,"points":high*10},{"label":"Gecikmiş audit","count":overdue,"points":overdue*5},{"label":"Digər açıq məsələ","count":other,"points":other*3}]
    return {"score":max(0,min(100,100-sum(x["points"] for x in deductions)+bonus)),"deductions":deductions,"additions":[{"label":"Etibarlı audit əhatəsi","points":bonus}],"explanation":"Daxili, konfiqurasiya edilə bilən MVP sağlamlıq göstəricisi."}

@router.get("/analytics/branches/{branch_id}/score")
def branch_score(branch_id:str,user:User=Depends(roles(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    branch=db.get(Branch,branch_id);allowed=branch and (user.role==Role.PLATFORM_ADMIN or branch.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or branch.id==user.branch_id)
    if not allowed: raise HTTPException(404,"Branch not found")
    rows=db.scalars(select(Incident).where(Incident.branch_id==branch.id)).all();now=utc_now();overdue=db.scalar(select(func.count(AuditTask.id)).where(AuditTask.branch_id==branch.id,AuditTask.due_at<now,AuditTask.status!=AuditStatus.COMPLETED)) or 0;valid=db.scalar(select(func.count(AuditTask.id)).where(AuditTask.branch_id==branch.id,AuditTask.status==AuditStatus.COMPLETED)) or 0
    return {"branch_id":branch.id,**score_data(rows,overdue,valid),"calculated_at":now}

@router.get("/platform/organisations")
def list_orgs(user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    return db.scalars(select(Organisation).order_by(Organisation.name)).all()

@router.post("/platform/organisations",status_code=201)
def create_org(data:OrganisationIn,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    item=Organisation(name=data.name);db.add(item);db.commit();db.refresh(item);return item

@router.post("/platform/branches",status_code=201)
def create_branch(data:BranchIn,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    if not db.get(Organisation,data.organisation_id):raise HTTPException(404,"Organisation not found")
    item=Branch(**data.model_dump());db.add(item);db.commit();db.refresh(item);return item

@router.post("/platform/admins",status_code=201)
def create_admin(data:AdminIn,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    if data.role not in (Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN):raise HTTPException(422,"Tenant admin role required")
    if not db.get(Organisation,data.organisation_id):raise HTTPException(404,"Organisation not found")
    item=User(organisation_id=data.organisation_id,branch_id=data.branch_id,email=data.email.lower(),full_name=data.full_name,role=data.role,password_hash=hash_password(data.password));db.add(item);db.commit();db.refresh(item);return {"id":item.id,"email":item.email,"role":item.role}

@router.get("/platform/usage")
def usage(user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    return {"organisations":db.scalar(select(func.count(Organisation.id))),"branches":db.scalar(select(func.count(Branch.id))),"users":db.scalar(select(func.count(User.id))),"incidents":db.scalar(select(func.count(Incident.id)))}
