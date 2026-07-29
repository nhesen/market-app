from datetime import datetime
import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import roles
from app.core.time import as_utc, utc_now
from app.db.session import get_db
from app.models.audit import AuditQualityFlag, AuditResultItem, AuditStatus, AuditTask, Condition, ReAudit
from app.models.domain import IncidentSource, IncidentStatus, Product, Role, User
from app.services.incidents import create_incident
from app.services.ocr import process_demo_text, process_image_bytes

router = APIRouter(prefix="/api/v1")


class ItemIn(BaseModel):
    barcode: str
    confirmed_date: str | None = None
    date_confirmed: bool = False
    ocr_corrected: bool = False
    ocr_engine: str | None = None
    ocr_candidates: list[str] = []
    correction_count: int = Field(default=0, ge=0)
    condition: Condition
    note: str | None = None
    photo_key: str | None = None


class OCRIn(BaseModel):
    demo_text: str = Field(default="", max_length=500)


class ReAuditIn(BaseModel):
    condition: Condition


def item_view(item: AuditResultItem, db: Session):
    product = db.get(Product, item.product_id)
    return {
        "id": item.id, "product_id": item.product_id,
        "product": product.name if product else "Unknown product", "barcode": item.barcode,
        "confirmed_date": item.confirmed_date, "date_confirmed": item.date_confirmed,
        "condition": item.condition, "note": item.note, "photo_key": item.photo_key,
        "ocr_engine": item.ocr_engine, "ocr_candidates": json.loads(item.ocr_candidates_json or "[]"),
        "ocr_corrected": item.ocr_corrected, "correction_count": item.correction_count,
        "created_at": item.created_at,
    }


def task_view(task: AuditTask, db: Session, include_items: bool = False):
    items = db.scalars(select(AuditResultItem).where(AuditResultItem.task_id == task.id).order_by(AuditResultItem.created_at)).all()
    result = {
        "id": task.id, "title": task.title, "instructions": task.instructions,
        "required_count": task.required_count, "unique_products": task.unique_products,
        "priority": task.priority, "status": task.status, "due_at": task.due_at,
        "started_at": task.started_at, "completed_at": task.completed_at,
        "item_count": len(items), "progress": round(len(items) / max(task.required_count, 1) * 100),
    }
    if include_items:
        result["items"] = [item_view(item, db) for item in items]
    return result


def add_flag(db: Session, task: AuditTask, code: str, message: str, severity: str = "WARNING"):
    db.add(AuditQualityFlag(organisation_id=task.organisation_id, branch_id=task.branch_id,
                            task_id=task.id, code=code, message=message, severity=severity))


def valid_date(value: str | None):
    if not value:
        return False
    for pattern in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            datetime.strptime(value, pattern)
            return True
        except ValueError:
            pass
    return False


@router.post("/ocr/date-candidates")
def ocr_candidates(data: OCRIn, user: User = Depends(roles(Role.CUSTOMER, Role.STAFF))):
    return process_demo_text(data.demo_text).__dict__


@router.post("/ocr/image")
async def ocr_image(file: UploadFile = File(...), user: User = Depends(roles(Role.CUSTOMER, Role.STAFF))):
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(415, "Image required")
    data = await file.read(10_485_761)
    if len(data) > 10_485_760:
        raise HTTPException(413, "Image is too large")
    return process_image_bytes(data).__dict__


@router.get("/staff/audits")
def staff_audits(user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    return [task_view(task, db) for task in db.scalars(
        select(AuditTask).where(AuditTask.assignee_id == user.id).order_by(AuditTask.due_at)).all()]


@router.get("/staff/audits/{task_id}")
def staff_audit_detail(task_id: str, user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    task = db.scalar(select(AuditTask).where(AuditTask.id == task_id, AuditTask.assignee_id == user.id))
    if not task:
        raise HTTPException(404, "Audit not found")
    return task_view(task, db, True)


@router.get("/staff/products/barcode/{barcode}")
def staff_product_by_barcode(barcode: str, user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    product = db.scalar(select(Product).where(Product.barcode == barcode, Product.organisation_id == user.organisation_id))
    if not product:
        raise HTTPException(404, "Product not found in this market")
    return {"id": product.id, "name": product.name, "brand": product.brand, "barcode": product.barcode,
            "category": product.category, "image_url": product.image_url}


@router.get("/staff/dashboard")
def staff_dashboard(user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    tasks = db.scalars(select(AuditTask).where(AuditTask.assignee_id == user.id)).all()
    ids = [task.id for task in tasks]
    flags = db.scalars(select(AuditQualityFlag).where(AuditQualityFlag.task_id.in_(ids)).order_by(AuditQualityFlag.created_at.desc())).all() if ids else []
    findings = db.scalars(select(AuditResultItem).where(AuditResultItem.task_id.in_(ids), AuditResultItem.condition != Condition.NORMAL).order_by(AuditResultItem.created_at.desc()).limit(8)).all() if ids else []
    now = utc_now(); today = now.date()
    durations = [(as_utc(task.completed_at)-as_utc(task.started_at)).total_seconds()/60 for task in tasks if task.started_at and task.completed_at]
    completed = sum(task.status == AuditStatus.COMPLETED for task in tasks)
    return {
        "today": sum(as_utc(task.due_at).date() == today and task.status != AuditStatus.COMPLETED for task in tasks),
        "overdue": sum(as_utc(task.due_at) < now and task.status != AuditStatus.COMPLETED for task in tasks),
        "completed": completed, "re_audits": db.scalar(select(func.count(ReAudit.id)).where(ReAudit.assignee_id == user.id, ReAudit.status == "ASSIGNED")) or 0,
        "quality_flags": len(flags), "average_duration_minutes": round(sum(durations)/len(durations), 1) if durations else 0,
        "completion_rate": round(completed/max(len(tasks), 1)*100, 1),
        "recent_findings": [item_view(item, db) for item in findings],
        "flags": [{"id": flag.id, "code": flag.code, "message": flag.message, "severity": flag.severity, "created_at": flag.created_at} for flag in flags[:8]],
    }


@router.get("/staff/quality-summary")
def staff_quality_summary(user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    dashboard = staff_dashboard(user, db)
    score = max(0, min(100, round(70 + dashboard["completion_rate"] * .3 - dashboard["quality_flags"] * 8)))
    return {"score": score, "completion_rate": dashboard["completion_rate"],
            "average_duration_minutes": dashboard["average_duration_minutes"], "quality_flags": dashboard["flags"],
            "explanation": "Process quality indicator; it is not an automatic disciplinary decision."}


@router.post("/staff/audits/{task_id}/start")
def start(task_id: str, user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    task = db.scalar(select(AuditTask).where(AuditTask.id == task_id, AuditTask.assignee_id == user.id))
    if not task:
        raise HTTPException(404, "Audit not found")
    if task.status in (AuditStatus.ASSIGNED, AuditStatus.OVERDUE):
        task.status = AuditStatus.IN_PROGRESS; task.started_at = utc_now(); db.commit()
    return task_view(task, db, True)


@router.post("/staff/audits/{task_id}/items", status_code=201)
def add_item(task_id: str, data: ItemIn, user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    task = db.scalar(select(AuditTask).where(AuditTask.id == task_id, AuditTask.assignee_id == user.id, AuditTask.status == AuditStatus.IN_PROGRESS))
    if not task:
        raise HTTPException(404, "Active audit not found")
    product = db.scalar(select(Product).where(Product.barcode == data.barcode, Product.organisation_id == user.organisation_id))
    if not product:
        raise HTTPException(404, "Product not found")
    if not data.photo_key:
        add_flag(db, task, "MISSING_IMAGE", "Expiry-date evidence image is missing.", "ERROR"); db.commit()
        raise HTTPException(422, "Expiry-date image is required")
    if not data.date_confirmed:
        raise HTTPException(422, "Explicit date confirmation is required")
    if not valid_date(data.confirmed_date):
        add_flag(db, task, "INVALID_DATE", "The confirmed expiry date has an invalid format.", "ERROR"); db.commit()
        raise HTTPException(422, "Confirmed date is invalid")
    existing = db.scalar(select(AuditResultItem).where(AuditResultItem.task_id == task.id, AuditResultItem.product_id == product.id))
    if task.unique_products and existing:
        add_flag(db, task, "DUPLICATE_BARCODE", "The same product barcode was scanned more than once."); db.commit()
        raise HTTPException(409, "Duplicate product is not allowed")
    payload = data.model_dump(exclude={"ocr_candidates"})
    item = AuditResultItem(task_id=task.id, product_id=product.id, ocr_candidates_json=json.dumps(data.ocr_candidates), **payload)
    db.add(item)
    if data.ocr_engine in ("unreadable-image", "ocr-error-manual-fallback") or not data.ocr_candidates:
        add_flag(db, task, "UNREADABLE_IMAGE", "OCR could not read a date from the evidence image.")
    if data.correction_count >= 3:
        add_flag(db, task, "EXCESSIVE_OCR_CORRECTIONS", "The OCR date required several manual corrections.")
    try:
        db.commit(); db.refresh(item)
    except IntegrityError:
        db.rollback(); add_flag(db, task, "DUPLICATE_BARCODE", "The same product barcode was scanned more than once."); db.commit()
        raise HTTPException(409, "Duplicate product is not allowed")
    return item_view(item, db)


@router.post("/staff/audits/{task_id}/complete")
def complete(task_id: str, user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    task = db.scalar(select(AuditTask).where(AuditTask.id == task_id, AuditTask.assignee_id == user.id, AuditTask.status == AuditStatus.IN_PROGRESS))
    if not task:
        raise HTTPException(404, "Active audit not found")
    items = db.scalars(select(AuditResultItem).where(AuditResultItem.task_id == task.id)).all()
    if len(items) < task.required_count:
        add_flag(db, task, "INCOMPLETE_PRODUCT_COUNT", f"Only {len(items)} of {task.required_count} required products were saved.", "ERROR"); db.commit()
        raise HTTPException(422, "Required product count is incomplete")
    task.status = AuditStatus.COMPLETED; task.completed_at = utc_now()
    if task.started_at and (as_utc(task.completed_at)-as_utc(task.started_at)).total_seconds() < 60:
        add_flag(db, task, "SHORT_DURATION", "Audit was completed suspiciously quickly.")
    for item in items:
        if item.condition in (Condition.EXPIRED, Condition.DAMAGED, Condition.INVALID_PRODUCT):
            product = db.get(Product, item.product_id)
            create_incident(db,organisation_id=task.organisation_id,branch_id=task.branch_id,source=IncidentSource.STAFF_AUDIT,category="PRODUCT",title=f"Audit finding: {product.name}",description=item.note or item.condition.value,priority="HIGH" if item.condition == Condition.EXPIRED else "MEDIUM",status=IncidentStatus.VERIFIED,actor=user,customer_note=None)
    db.commit()
    return task_view(task, db, True)


@router.get("/admin/audit-quality-flags")
def flags(user: User = Depends(roles(Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN, Role.PLATFORM_ADMIN)), db: Session = Depends(get_db)):
    stmt = select(AuditQualityFlag)
    if user.role != Role.PLATFORM_ADMIN: stmt = stmt.where(AuditQualityFlag.organisation_id == user.organisation_id)
    if user.role == Role.BRANCH_ADMIN: stmt = stmt.where(AuditQualityFlag.branch_id == user.branch_id)
    return db.scalars(stmt.order_by(AuditQualityFlag.created_at.desc())).all()


@router.post("/admin/audits/{task_id}/re-audit", status_code=201)
def create_reaudit(task_id: str, assignee_id: str, user: User = Depends(roles(Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN)), db: Session = Depends(get_db)):
    task = db.scalar(select(AuditTask).where(AuditTask.id == task_id, AuditTask.organisation_id == user.organisation_id))
    items = db.scalars(select(AuditResultItem).where(AuditResultItem.task_id == task_id)).all()
    if not task or not items: raise HTTPException(404, "Completed audit result not found")
    if user.role == Role.BRANCH_ADMIN and task.branch_id != user.branch_id: raise HTTPException(403, "Branch access denied")
    if assignee_id == task.assignee_id: raise HTTPException(422, "Re-audit must be assigned to another employee")
    staff = db.scalar(select(User).where(User.id == assignee_id, User.organisation_id == user.organisation_id, User.branch_id == task.branch_id, User.role == Role.STAFF))
    if not staff: raise HTTPException(404, "Staff assignee not found")
    item = ReAudit(organisation_id=task.organisation_id, branch_id=task.branch_id, original_task_id=task.id,
                   assignee_id=staff.id, original_condition=items[0].condition.value)
    db.add(item); db.commit(); db.refresh(item); return item


def reaudit_view(item: ReAudit, db: Session):
    task = db.get(AuditTask, item.original_task_id)
    original = db.scalar(select(AuditResultItem).where(AuditResultItem.task_id == item.original_task_id).order_by(AuditResultItem.created_at))
    return {"id": item.id, "status": item.status, "original_task_id": item.original_task_id,
            "original_title": task.title if task else "Audit", "original_condition": item.original_condition,
            "original_item": item_view(original, db) if original else None, "re_audit_condition": item.re_audit_condition,
            "consistent": item.consistent, "created_at": item.created_at, "completed_at": item.completed_at}


@router.get("/staff/re-audits")
def staff_reaudits(user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    return [reaudit_view(item, db) for item in db.scalars(select(ReAudit).where(ReAudit.assignee_id == user.id).order_by(ReAudit.created_at.desc())).all()]


@router.post("/staff/re-audits/{item_id}/complete")
def complete_reaudit(item_id: str, data: ReAuditIn, user: User = Depends(roles(Role.STAFF)), db: Session = Depends(get_db)):
    item = db.scalar(select(ReAudit).where(ReAudit.id == item_id, ReAudit.assignee_id == user.id, ReAudit.status == "ASSIGNED"))
    if not item: raise HTTPException(404, "Re-audit not found")
    item.re_audit_condition = data.condition.value; item.consistent = item.original_condition == data.condition.value
    item.status = "COMPLETED"; item.completed_at = utc_now()
    if not item.consistent:
        task = db.get(AuditTask, item.original_task_id)
        add_flag(db, task, "RE_AUDIT_MISMATCH", "Re-audit result does not match the original finding.")
    db.commit(); return reaudit_view(item, db)


@router.get("/admin/staff/{staff_id}/quality-score")
def quality_score(staff_id: str, user: User = Depends(roles(Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN)), db: Session = Depends(get_db)):
    tasks = db.scalars(select(AuditTask).where(AuditTask.assignee_id == staff_id, AuditTask.organisation_id == user.organisation_id)).all()
    if user.role == Role.BRANCH_ADMIN and any(task.branch_id != user.branch_id for task in tasks): raise HTTPException(403, "Branch access denied")
    ids = [task.id for task in tasks]
    flags_count = db.scalar(select(func.count(AuditQualityFlag.id)).where(AuditQualityFlag.task_id.in_(ids))) if ids else 0
    completed = sum(task.status == AuditStatus.COMPLETED for task in tasks); rate = completed/max(len(tasks), 1)
    return {"staff_id": staff_id, "score": max(0, min(100, round(70+30*rate-flags_count*8))),
            "completion_rate": round(rate*100, 1), "quality_flags": flags_count,
            "explanation": "Process quality indicator; it is not an automatic disciplinary decision."}
