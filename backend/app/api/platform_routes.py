from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.core.security import hash_password,roles
from app.db.session import get_db
from app.models.audit import AuditQualityFlag,AuditStatus,AuditTask
from app.models.domain import Branch,Incident,IncidentStatus,Organisation,Role,User
from app.models.retail import AuditLog
from app.core.time import utc_now
from app.services.score import smart_store_score

router=APIRouter(prefix="/api/v1")
def log(db,user,action,kind,entity_id,detail=None):db.add(AuditLog(organisation_id=None,actor_id=user.id,action=action,entity_type=kind,entity_id=entity_id,detail=detail))
class OrganisationIn(BaseModel): name:str=Field(min_length=2,max_length=160)
class OrganisationUpdate(BaseModel): name:str=Field(min_length=2,max_length=160);is_active:bool
class BranchIn(BaseModel): organisation_id:str;name:str=Field(min_length=2,max_length=160);address:str;hours:str="08:00–23:00"
class AdminIn(BaseModel): organisation_id:str;branch_id:str|None=None;email:str;full_name:str;password:str=Field(min_length=8,max_length=72);role:Role
class AdminUpdate(BaseModel): full_name:str=Field(min_length=2,max_length=160);is_active:bool;branch_id:str|None=None

@router.get("/analytics/branches/{branch_id}/score")
def branch_score(branch_id:str,user:User=Depends(roles(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    branch=db.get(Branch,branch_id);allowed=branch and (user.role==Role.PLATFORM_ADMIN or branch.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or branch.id==user.branch_id)
    if not allowed: raise HTTPException(404,"Branch not found")
    return {"branch_id":branch.id,**smart_store_score(db,branch.id),"calculated_at":utc_now()}

@router.get("/platform/organisations")
def list_orgs(user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    return db.scalars(select(Organisation).order_by(Organisation.name)).all()

@router.post("/platform/organisations",status_code=201)
def create_org(data:OrganisationIn,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    item=Organisation(name=data.name);db.add(item);db.flush();log(db,user,"CREATE","Organisation",item.id);db.commit();db.refresh(item);return item

@router.patch("/platform/organisations/{organisation_id}")
def update_org(organisation_id:str,data:OrganisationUpdate,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    item=db.get(Organisation,organisation_id)
    if not item:raise HTTPException(404,"Organisation not found")
    item.name=data.name;item.is_active=data.is_active;log(db,user,"UPDATE","Organisation",item.id,f"active={item.is_active}");db.commit();db.refresh(item);return item

@router.post("/platform/branches",status_code=201)
def create_branch(data:BranchIn,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    if not db.get(Organisation,data.organisation_id):raise HTTPException(404,"Organisation not found")
    item=Branch(**data.model_dump());db.add(item);db.flush();log(db,user,"CREATE","Branch",item.id);db.commit();db.refresh(item);return item

@router.post("/platform/admins",status_code=201)
def create_admin(data:AdminIn,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    if data.role not in (Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN):raise HTTPException(422,"Tenant admin role required")
    if not db.get(Organisation,data.organisation_id):raise HTTPException(404,"Organisation not found")
    if data.role==Role.BRANCH_ADMIN:
        branch=db.get(Branch,data.branch_id) if data.branch_id else None
        if not branch or branch.organisation_id!=data.organisation_id:raise HTTPException(422,"Branch admin requires a branch in the selected organisation")
    elif data.branch_id:raise HTTPException(422,"Head-office admin cannot be assigned to one branch")
    item=User(organisation_id=data.organisation_id,branch_id=data.branch_id,email=data.email.lower(),full_name=data.full_name,role=data.role,password_hash=hash_password(data.password));db.add(item);db.flush();log(db,user,"CREATE","Administrator",item.id);db.commit();db.refresh(item);return {"id":item.id,"email":item.email,"role":item.role}

@router.patch("/platform/admins/{admin_id}")
def update_admin(admin_id:str,data:AdminUpdate,user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    item=db.get(User,admin_id)
    if not item or item.role not in (Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN):raise HTTPException(404,"Administrator not found")
    if data.branch_id:
        branch=db.get(Branch,data.branch_id)
        if not branch or branch.organisation_id!=item.organisation_id:raise HTTPException(422,"Branch is outside administrator organisation")
    item.full_name=data.full_name;item.is_active=data.is_active;item.branch_id=data.branch_id if item.role==Role.BRANCH_ADMIN else None;log(db,user,"UPDATE","Administrator",item.id,f"active={item.is_active}");db.commit();return {"id":item.id,"full_name":item.full_name,"email":item.email,"role":item.role,"branch_id":item.branch_id,"is_active":item.is_active}

@router.get("/platform/usage")
def usage(user:User=Depends(roles(Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    return {"organisations":db.scalar(select(func.count(Organisation.id))),"branches":db.scalar(select(func.count(Branch.id))),"users":db.scalar(select(func.count(User.id))),"incidents":db.scalar(select(func.count(Incident.id)))}
