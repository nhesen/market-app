from fastapi import APIRouter,Depends,File,HTTPException,UploadFile
from pydantic import BaseModel,Field
from sqlalchemy import func,select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import roles
from app.db.session import get_db
from app.models.audit import AuditQualityFlag,AuditResultItem,AuditStatus,AuditTask,Condition,ReAudit
from app.models.domain import Incident,IncidentStatus,IncidentStatusHistory,Product,Role,User
from app.services.ocr import process_demo_text,process_image_bytes
from app.core.time import as_utc, utc_now

router=APIRouter(prefix="/api/v1")
class ItemIn(BaseModel):
    barcode:str;confirmed_date:str|None=None;ocr_corrected:bool=False;condition:Condition;note:str|None=None;photo_key:str|None=None
class OCRIn(BaseModel): demo_text:str=Field(default="",max_length=500)
class ReAuditIn(BaseModel):condition:Condition

def task_view(t:AuditTask,db:Session):
    return {"id":t.id,"title":t.title,"instructions":t.instructions,"required_count":t.required_count,"priority":t.priority,"status":t.status,"due_at":t.due_at,"started_at":t.started_at,"completed_at":t.completed_at,"item_count":db.scalar(select(func.count(AuditResultItem.id)).where(AuditResultItem.task_id==t.id))}

@router.post("/ocr/date-candidates")
def ocr_candidates(data:OCRIn,user:User=Depends(roles(Role.CUSTOMER,Role.STAFF))): return process_demo_text(data.demo_text).__dict__
@router.post("/ocr/image")
async def ocr_image(file:UploadFile=File(...),user:User=Depends(roles(Role.CUSTOMER,Role.STAFF))):
    if file.content_type not in ("image/jpeg","image/png","image/webp"):raise HTTPException(415,"Image required")
    data=await file.read(10_485_761)
    if len(data)>10_485_760:raise HTTPException(413,"Image is too large")
    return process_image_bytes(data).__dict__

@router.get("/staff/audits")
def staff_audits(user:User=Depends(roles(Role.STAFF)),db:Session=Depends(get_db)):
    return [task_view(t,db) for t in db.scalars(select(AuditTask).where(AuditTask.assignee_id==user.id).order_by(AuditTask.due_at)).all()]

@router.get("/staff/quality-summary")
def staff_quality_summary(user:User=Depends(roles(Role.STAFF)),db:Session=Depends(get_db)):
    tasks=db.scalars(select(AuditTask).where(AuditTask.assignee_id==user.id)).all();task_ids=[task.id for task in tasks]
    flags=db.scalars(select(AuditQualityFlag).where(AuditQualityFlag.task_id.in_(task_ids))).all() if task_ids else []
    durations=[(as_utc(task.completed_at)-as_utc(task.started_at)).total_seconds()/60 for task in tasks if task.started_at and task.completed_at]
    completed=sum(task.status==AuditStatus.COMPLETED for task in tasks);rate=round(completed/max(len(tasks),1)*100,1);score=max(0,min(100,round(70+30*rate/100-len(flags)*8)))
    return {"score":score,"completion_rate":rate,"average_duration_minutes":round(sum(durations)/len(durations),1) if durations else 0,"quality_flags":[{"id":flag.id,"code":flag.code,"message":flag.message,"severity":flag.severity,"created_at":flag.created_at} for flag in flags],"explanation":"Proses keyfiyyəti göstəricisidir; avtomatik cəza qərarı deyil."}

@router.post("/staff/audits/{task_id}/start")
def start(task_id:str,user:User=Depends(roles(Role.STAFF)),db:Session=Depends(get_db)):
    task=db.scalar(select(AuditTask).where(AuditTask.id==task_id,AuditTask.assignee_id==user.id));
    if not task: raise HTTPException(404,"Audit not found")
    if task.status==AuditStatus.ASSIGNED: task.status=AuditStatus.IN_PROGRESS;task.started_at=utc_now();db.commit()
    return task_view(task,db)

@router.post("/staff/audits/{task_id}/items",status_code=201)
def add_item(task_id:str,data:ItemIn,user:User=Depends(roles(Role.STAFF)),db:Session=Depends(get_db)):
    task=db.scalar(select(AuditTask).where(AuditTask.id==task_id,AuditTask.assignee_id==user.id,AuditTask.status==AuditStatus.IN_PROGRESS));
    if not task: raise HTTPException(404,"Active audit not found")
    product=db.scalar(select(Product).where(Product.barcode==data.barcode,Product.organisation_id==user.organisation_id));
    if not product: raise HTTPException(404,"Product not found")
    item=AuditResultItem(task_id=task.id,product_id=product.id,**data.model_dump());db.add(item)
    try: db.commit()
    except IntegrityError:
        db.rollback();db.add(AuditQualityFlag(organisation_id=task.organisation_id,branch_id=task.branch_id,task_id=task.id,code="DUPLICATE_BARCODE",message="Eyni məhsul barkodu təkrar istifadə edildi."));db.commit();raise HTTPException(409,"Duplicate product is not allowed")
    return {"id":item.id,"product":product.name,"condition":item.condition}

@router.post("/staff/audits/{task_id}/complete")
def complete(task_id:str,user:User=Depends(roles(Role.STAFF)),db:Session=Depends(get_db)):
    task=db.scalar(select(AuditTask).where(AuditTask.id==task_id,AuditTask.assignee_id==user.id,AuditTask.status==AuditStatus.IN_PROGRESS));
    if not task: raise HTTPException(404,"Active audit not found")
    items=db.scalars(select(AuditResultItem).where(AuditResultItem.task_id==task.id)).all()
    if len(items)<task.required_count: raise HTTPException(422,"Required product count is incomplete")
    task.status=AuditStatus.COMPLETED;task.completed_at=utc_now()
    if task.started_at and (as_utc(task.completed_at)-as_utc(task.started_at)).total_seconds()<60: db.add(AuditQualityFlag(organisation_id=task.organisation_id,branch_id=task.branch_id,task_id=task.id,code="SHORT_DURATION",message="Audit gözləniləndən çox qısa müddətdə tamamlandı."))
    for item in items:
        if item.condition!=Condition.NORMAL:
            product=db.get(Product,item.product_id);incident=Incident(organisation_id=task.organisation_id,branch_id=task.branch_id,source="STAFF_AUDIT",category="PRODUCT",title=f"Audit tapıntısı: {product.name}",description=item.note or item.condition.value,priority="HIGH" if item.condition==Condition.EXPIRED else "MEDIUM",status=IncidentStatus.VERIFIED);incident.history.append(IncidentStatusHistory(status=IncidentStatus.VERIFIED,note="Əməkdaş auditi ilə təsdiqlənmiş tapıntı.",actor_id=user.id));db.add(incident)
    db.commit();return task_view(task,db)

@router.get("/admin/audit-quality-flags")
def flags(user:User=Depends(roles(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    stmt=select(AuditQualityFlag)
    if user.role!=Role.PLATFORM_ADMIN: stmt=stmt.where(AuditQualityFlag.organisation_id==user.organisation_id)
    if user.role==Role.BRANCH_ADMIN: stmt=stmt.where(AuditQualityFlag.branch_id==user.branch_id)
    return db.scalars(stmt.order_by(AuditQualityFlag.created_at.desc())).all()

@router.post("/admin/audits/{task_id}/re-audit",status_code=201)
def create_reaudit(task_id:str,assignee_id:str,user:User=Depends(roles(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN)),db:Session=Depends(get_db)):
    task=db.scalar(select(AuditTask).where(AuditTask.id==task_id,AuditTask.organisation_id==user.organisation_id));items=db.scalars(select(AuditResultItem).where(AuditResultItem.task_id==task_id)).all()
    if not task or not items:raise HTTPException(404,"Completed audit result not found")
    if user.role==Role.BRANCH_ADMIN and task.branch_id!=user.branch_id:raise HTTPException(403,"Branch access denied")
    if assignee_id==task.assignee_id:raise HTTPException(422,"Re-audit must be assigned to another employee")
    staff=db.scalar(select(User).where(User.id==assignee_id,User.organisation_id==user.organisation_id,User.branch_id==task.branch_id,User.role==Role.STAFF))
    if not staff:raise HTTPException(404,"Staff assignee not found")
    item=ReAudit(organisation_id=task.organisation_id,branch_id=task.branch_id,original_task_id=task.id,assignee_id=staff.id,original_condition=items[0].condition.value);db.add(item);db.commit();db.refresh(item);return item

@router.get("/staff/re-audits")
def staff_reaudits(user:User=Depends(roles(Role.STAFF)),db:Session=Depends(get_db)):return db.scalars(select(ReAudit).where(ReAudit.assignee_id==user.id).order_by(ReAudit.created_at.desc())).all()

@router.post("/staff/re-audits/{item_id}/complete")
def complete_reaudit(item_id:str,data:ReAuditIn,user:User=Depends(roles(Role.STAFF)),db:Session=Depends(get_db)):
    item=db.scalar(select(ReAudit).where(ReAudit.id==item_id,ReAudit.assignee_id==user.id,ReAudit.status=="ASSIGNED"))
    if not item:raise HTTPException(404,"Re-audit not found")
    item.re_audit_condition=data.condition.value;item.consistent=item.original_condition==data.condition.value;item.status="COMPLETED";item.completed_at=utc_now()
    if not item.consistent:db.add(AuditQualityFlag(organisation_id=item.organisation_id,branch_id=item.branch_id,task_id=item.original_task_id,code="RE_AUDIT_MISMATCH",message="Təkrar audit nəticəsi ilkin nəticə ilə uyğun gəlmədi."))
    db.commit();return item

@router.get("/admin/staff/{staff_id}/quality-score")
def quality_score(staff_id:str,user:User=Depends(roles(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN)),db:Session=Depends(get_db)):
    tasks=db.scalars(select(AuditTask).where(AuditTask.assignee_id==staff_id,AuditTask.organisation_id==user.organisation_id)).all()
    if user.role==Role.BRANCH_ADMIN and any(t.branch_id!=user.branch_id for t in tasks):raise HTTPException(403,"Branch access denied")
    task_ids=[t.id for t in tasks];flags_count=sum(len(db.scalars(select(AuditQualityFlag).where(AuditQualityFlag.task_id==tid)).all()) for tid in task_ids);completed=sum(t.status==AuditStatus.COMPLETED for t in tasks);rate=completed/max(len(tasks),1);score=max(0,min(100,round(70+30*rate-flags_count*8)))
    return {"staff_id":staff_id,"score":score,"completion_rate":round(rate*100,1),"quality_flags":flags_count,"explanation":"Proses keyfiyyəti göstəricisidir; avtomatik cəza qərarı deyil."}
