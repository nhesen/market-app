from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import roles
from app.db.session import get_db
from app.models.domain import Branch,CameraEvent,Incident,IncidentStatus,Role,User
from app.models.vision import Camera,CameraClipMetadata,CameraRule
from app.services.incidents import transition_incident
from app.services.video_pipeline import MP4Pipeline,RULE_ENGINES

router=APIRouter(prefix="/api/v1");ADMINS=(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)
class CameraIn(BaseModel):branch_id:str;name:str;source_path:str;source_type:str="DEMO_MP4";enabled:bool=True
class RuleIn(BaseModel):camera_id:str;rule_type:str=Field(pattern="^(FLOOR_HAZARD|BLOCKED_AISLE|PROMO_DEPLETION|QUEUE)$");roi:str=Field(pattern=r"^\d?(?:\.\d+)?,\d?(?:\.\d+)?,\d?(?:\.\d+)?,\d?(?:\.\d+)?$");threshold:float=Field(ge=0,le=100);trigger_frames:int=Field(ge=2,le=10000);clear_frames:int=Field(ge=2,le=10000);enabled:bool=True

def scoped(stmt,user,model):
    if user.role!=Role.PLATFORM_ADMIN:stmt=stmt.where(model.organisation_id==user.organisation_id)
    if user.role==Role.BRANCH_ADMIN and hasattr(model,"branch_id"):stmt=stmt.where(model.branch_id==user.branch_id)
    return stmt

def allowed_camera(camera,user):return camera and (user.role==Role.PLATFORM_ADMIN or camera.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or camera.branch_id==user.branch_id)

@router.get("/admin/cameras")
def cameras(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):return db.scalars(scoped(select(Camera),user,Camera)).all()

@router.post("/admin/cameras",status_code=201)
def create_camera(data:CameraIn,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    branch=db.get(Branch,data.branch_id)
    if not branch or not allowed_camera(type("Scope",(),{"organisation_id":branch.organisation_id,"branch_id":branch.id})(),user):raise HTTPException(404,"Branch not found")
    item=Camera(organisation_id=branch.organisation_id,**data.model_dump());db.add(item);db.commit();db.refresh(item);return item

@router.get("/admin/camera-rules")
def rules(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    stmt=select(CameraRule).join(Camera,Camera.id==CameraRule.camera_id)
    if user.role!=Role.PLATFORM_ADMIN:stmt=stmt.where(CameraRule.organisation_id==user.organisation_id)
    if user.role==Role.BRANCH_ADMIN:stmt=stmt.where(Camera.branch_id==user.branch_id)
    return db.scalars(stmt).all()

@router.post("/admin/camera-rules",status_code=201)
def create_rule(data:RuleIn,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    camera=db.get(Camera,data.camera_id)
    if not allowed_camera(camera,user):raise HTTPException(404,"Camera not found")
    payload=data.model_dump();item=CameraRule(organisation_id=camera.organisation_id,detection_engine=RULE_ENGINES[payload["rule_type"]],**payload);db.add(item);db.commit();db.refresh(item);return item

@router.post("/admin/camera-rules/{rule_id}/process")
def process(rule_id:str,max_frames:int=300,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    rule=db.get(CameraRule,rule_id);camera=db.get(Camera,rule.camera_id) if rule else None
    if not allowed_camera(camera,user):raise HTTPException(404,"Rule not found")
    return MP4Pipeline(db,camera,rule).process(max_frames=min(max_frames,3000))

@router.get("/admin/camera-events")
def events(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    rows=db.scalars(scoped(select(CameraEvent),user,CameraEvent)).all();result=[]
    for event in rows:
        incident=db.get(Incident,event.incident_id);evidence=db.scalars(select(CameraClipMetadata).where(CameraClipMetadata.camera_event_id==event.id)).all()
        result.append({"id":event.id,"incident_id":event.incident_id,"branch_id":event.branch_id,"rule":event.rule,"detection_engine":event.detection_engine,"roi":event.roi,"threshold":event.threshold,"trigger_score":event.trigger_score,"detected_frames":event.detected_frames,"clear_frames":event.clear_frames,"status":incident.status if incident else None,"created_at":incident.created_at if incident else None,"evidence":[{"frame_path":x.frame_path,"clip_path":x.clip_path,"frame_number":x.frame_number,"source_timestamp_ms":x.source_timestamp_ms,"score":x.score,"engine":x.engine} for x in evidence]})
    return result

@router.post("/admin/camera-events/{event_id}/false-alert")
def false_alert(event_id:str,user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    event=db.get(CameraEvent,event_id);incident=db.get(Incident,event.incident_id) if event else None
    if not event or not allowed_camera(type("Scope",(),{"organisation_id":event.organisation_id,"branch_id":event.branch_id})(),user):raise HTTPException(404,"Event not found")
    reason="Camera event was reviewed by an administrator and marked as a false alert."
    if incident.status in {IncidentStatus.AUTO_RESOLVED,IncidentStatus.MANUALLY_RESOLVED,IncidentStatus.CANCELLED}:
        transition_incident(db,incident,IncidentStatus.REOPENED,actor=user,internal_note=reason,reopening_reason="Administrative false-alert review.")
    return transition_incident(db,incident,IncidentStatus.REJECTED,actor=user,internal_note=reason,rejection_reason=reason)

@router.get("/admin/vision-health")
def health(user:User=Depends(roles(*ADMINS)),db:Session=Depends(get_db)):
    result=[]
    for camera in db.scalars(scoped(select(Camera),user,Camera)).all():
        rules=db.scalars(select(CameraRule).where(CameraRule.camera_id==camera.id)).all()
        result.append({"camera_id":camera.id,"name":camera.name,"source_type":camera.source_type,"source_active":camera.enabled and not camera.last_error,"last_processed_frame":camera.last_frame_at,"approximate_fps":camera.fps_estimate,"processing_error":camera.last_error,"rules":[{"id":x.id,"rule_type":x.rule_type,"detection_engine":x.detection_engine,"roi":x.roi,"threshold":x.threshold,"trigger_persistence":x.trigger_frames,"clear_persistence":x.clear_frames,"current_state":x.current_state,"last_frame_time":x.last_frame_at,"last_event":x.last_event_id,"processing_error":x.processing_error,"approximate_fps":x.fps_estimate} for x in rules]})
    return result
