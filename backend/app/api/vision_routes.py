from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import roles
from app.db.session import get_db
from app.models.domain import Branch,CameraEvent,Incident,IncidentStatus,Role,User
from app.models.vision import Camera,CameraRule
from app.services.incidents import set_status
from app.services.video_pipeline import MP4Pipeline

router=APIRouter(prefix="/api/v1")
ADMINS=(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)
class CameraIn(BaseModel):branch_id:str;name:str;source_path:str;source_type:str="DEMO_MP4";enabled:bool=True
class RuleIn(BaseModel):camera_id:str;rule_type:str;roi:str=Field(pattern=r"^\d?(?:\.\d+)?,\d?(?:\.\d+)?,\d?(?:\.\d+)?,\d?(?:\.\d+)?$");threshold:float=Field(ge=0,le=1);trigger_frames:int=Field(ge=1,le=10000);clear_frames:int=Field(ge=1,le=10000);enabled:bool=True

def scoped(stmt,user,model):
    if user.role!=Role.PLATFORM_ADMIN:stmt=stmt.where(model.organisation_id==user.organisation_id)
    if user.role==Role.BRANCH_ADMIN and hasattr(model,"branch_id"):stmt=stmt.where(model.branch_id==user.branch_id)
    return stmt
@router.get("/admin/cameras")
def cameras(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):return db.scalars(scoped(select(Camera),user,Camera)).all()
@router.post("/admin/cameras",status_code=201)
def create_camera(data:CameraIn,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    branch=db.get(Branch,data.branch_id);allowed=branch and (user.role==Role.PLATFORM_ADMIN or branch.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or branch.id==user.branch_id)
    if not allowed:raise HTTPException(404,"Branch not found")
    item=Camera(organisation_id=branch.organisation_id,**data.model_dump());db.add(item);db.commit();db.refresh(item);return item
@router.get("/admin/camera-rules")
def rules(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    stmt=select(CameraRule).join(Camera,Camera.id==CameraRule.camera_id)
    if user.role!=Role.PLATFORM_ADMIN:stmt=stmt.where(CameraRule.organisation_id==user.organisation_id)
    if user.role==Role.BRANCH_ADMIN:stmt=stmt.where(Camera.branch_id==user.branch_id)
    return db.scalars(stmt).all()
@router.post("/admin/camera-rules",status_code=201)
def create_rule(data:RuleIn,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    camera=db.get(Camera,data.camera_id);allowed=camera and (user.role==Role.PLATFORM_ADMIN or camera.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or camera.branch_id==user.branch_id)
    if not allowed:raise HTTPException(404,"Camera not found")
    item=CameraRule(organisation_id=camera.organisation_id,**data.model_dump());db.add(item);db.commit();db.refresh(item);return item
@router.post("/admin/camera-rules/{rule_id}/process")
def process(rule_id:str,max_frames:int=300,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    rule=db.get(CameraRule,rule_id);camera=db.get(Camera,rule.camera_id) if rule else None;allowed=camera and (user.role==Role.PLATFORM_ADMIN or camera.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or camera.branch_id==user.branch_id)
    if not allowed:raise HTTPException(404,"Rule not found")
    return MP4Pipeline(db,camera,rule).process(max_frames=min(max_frames,3000))
@router.get("/admin/camera-events")
def events(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    stmt=select(CameraEvent)
    if user.role!=Role.PLATFORM_ADMIN:stmt=stmt.where(CameraEvent.organisation_id==user.organisation_id)
    if user.role==Role.BRANCH_ADMIN:stmt=stmt.where(CameraEvent.branch_id==user.branch_id)
    return db.scalars(stmt).all()
@router.post("/admin/camera-events/{event_id}/false-alert")
def false_alert(event_id:str,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    event=db.get(CameraEvent,event_id);incident=db.get(Incident,event.incident_id) if event else None;allowed=event and (user.role==Role.PLATFORM_ADMIN or event.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or event.branch_id==user.branch_id)
    if not allowed:raise HTTPException(404,"Event not found")
    return set_status(db,incident,IncidentStatus.REJECTED,"Kamera hadisəsi insan yoxlaması ilə yanlış siqnal kimi işarələndi.",user)
@router.get("/admin/vision-health")
def health(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    rows=db.scalars(scoped(select(Camera),user,Camera)).all();return [{"camera_id":x.id,"name":x.name,"source_type":x.source_type,"source_active":x.enabled and not x.last_error,"last_processed_frame":x.last_frame_at,"fps_estimate":x.fps_estimate,"processing_error":x.last_error} for x in rows]
