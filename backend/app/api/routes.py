from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_refresh_token, create_token, current_user, hash_password, roles, verify_password
from jose import JWTError, jwt
from pydantic import BaseModel,Field
from app.db.session import get_db
from app.models.domain import Branch, CustomerReport, Incident, IncidentSource, LoyaltyCard, News, Organisation, Product, Role, User
from app.schemas.api import IncidentOut, IncidentUpdate, LoginIn, ManualIncidentCreate, ReportCreate, ReportOut, TokenOut, UserOut
from app.services.incidents import add_note,create_customer_report,create_incident,incident_view,report_view,transition_incident
from app.services.customer_context import market_id
from app.services.score import smart_store_score

router = APIRouter(prefix="/api/v1")
class RefreshIn(BaseModel): refresh_token:str
class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str
class ReportAIReviewIn(BaseModel):
    title: str
    description: str
    category: str | None = None

@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(status_code=401, detail="Email or password is incorrect")
    return {"access_token": create_token(user),"refresh_token":create_refresh_token(user), "user": user}

@router.post("/auth/refresh",response_model=TokenOut)
def refresh(data:RefreshIn,db:Session=Depends(get_db)):
    try:
        payload=jwt.decode(data.refresh_token,settings.jwt_refresh_secret,algorithms=["HS256"])
        if payload.get("type")!="refresh": raise JWTError()
    except JWTError: raise HTTPException(401,"Invalid refresh token")
    user=db.get(User,payload["sub"])
    if not user or not user.is_active: raise HTTPException(401,"Inactive user")
    return {"access_token":create_token(user),"refresh_token":create_refresh_token(user),"user":user}

@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)): return user

@router.post("/auth/logout",status_code=204)
def logout(user:User=Depends(current_user)):
    """The mobile clients delete both tokens; this endpoint validates the active session."""
    return None

@router.post("/auth/change-password",status_code=204)
def change_password(data:ChangePasswordIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not verify_password(data.current_password,user.password_hash):raise HTTPException(400,"Current password is incorrect")
    if len(data.new_password)<8:raise HTTPException(422,"New password must contain at least 8 characters")
    user.password_hash=hash_password(data.new_password);db.commit();return None

@router.get("/branches")
def branches(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows=db.scalars(select(Branch).where(Branch.organisation_id==market_id(user))).all()
    return [{"id":x.id,"name":x.name,"address":x.address,"hours":x.hours,"distance_km":x.distance_km,"is_open":x.is_open,"image_url":"/assets/retail-branch-v2.png"} for x in rows]

@router.get("/home")
def home(branch_id:str|None=Query(None),user: User = Depends(roles(Role.CUSTOMER)), db: Session = Depends(get_db)):
    org = market_id(user)
    news = db.scalars(select(News).where(News.organisation_id == org).order_by(News.published_at.desc())).all()
    products = db.scalars(select(Product).where(Product.organisation_id == org)).all()
    branches_data = db.scalars(select(Branch).where(Branch.organisation_id == org)).all()
    if branch_id and not any(branch.id==branch_id for branch in branches_data):raise HTTPException(404,"Branch not found in your organisation")
    loyalty = db.scalar(select(LoyaltyCard).where(LoyaltyCard.user_id == user.id,LoyaltyCard.organisation_id==org))
    reports = db.scalars(select(CustomerReport).where(CustomerReport.customer_id == user.id,CustomerReport.organisation_id==org).order_by(CustomerReport.created_at.desc()).limit(4)).all()
    effective_branch=branch_id or user.preferred_branch_id
    selected=next((branch for branch in branches_data if branch.id==effective_branch),branches_data[0] if branches_data else None)
    organisation=db.get(Organisation,org)
    return {"user": user,"organisation":organisation,"selected_branch":selected,"news": news, "products": products, "discounts": [p for p in products if p.discount_price], "branches": branches_data, "loyalty": loyalty, "reports": [report_view(r,db) for r in reports]}

@router.post("/reports/ai-review")
def ai_review(data:ReportAIReviewIn,user:User=Depends(roles(Role.CUSTOMER))):
    text=f"{data.title} {data.description}".lower()
    rules=(("PRICE",("qiymət","kassa","etiket")),("SAFETY",("təhlükə","şüşə","sürüş","su","maye")),("CLEANLINESS",("çirk","təmiz","zibil")),("SHELF",("rəf","stok","boş")),("PRODUCT",("məhsul","tarix","qablaşdırma","xarab")),("CUSTOMER_SERVICE",("növbə","xidmət")))
    suggested=next((category for category,words in rules if any(word in text for word in words)),data.category or "OTHER")
    urgent=any(word in text for word in ("təhlükə","şüşə","yanğın","təcili","maye"))
    warnings=[]
    if len(data.description.strip())<20:warnings.append("Problemin yeri və görünən detalları daha ətraflı yazın.")
    if not data.category:warnings.append("Kateqoriya seçilməyib.")
    return {"suggested_category":suggested,"suggested_priority":"HIGH" if urgent else "MEDIUM","summary":f"Müraciət {suggested} kateqoriyasına uyğun görünür və filial yoxlaması tələb edir.","warnings":warnings,"requires_human_verification":True}

@router.post("/reports", response_model=ReportOut, status_code=201)
def create_report(data: ReportCreate, user: User = Depends(roles(Role.CUSTOMER)), db: Session = Depends(get_db)):
    branch = db.scalar(select(Branch).where(Branch.id == data.branch_id, Branch.organisation_id == market_id(user)))
    if not branch: raise HTTPException(status_code=404, detail="Branch not found in your organisation")
    if data.product_id:
        product=db.scalar(select(Product).where(Product.id==data.product_id,Product.organisation_id==market_id(user)))
        if not product:raise HTTPException(404,"Product not found in your market")
        if data.barcode and data.barcode!=product.barcode:raise HTTPException(422,"Barcode does not match product")
    return report_view(create_customer_report(db, user, data),db)

@router.get("/reports", response_model=list[ReportOut])
def own_reports(user: User = Depends(roles(Role.CUSTOMER)), db: Session = Depends(get_db)):
    return [report_view(r,db) for r in db.scalars(select(CustomerReport).where(CustomerReport.customer_id == user.id).order_by(CustomerReport.created_at.desc())).all()]

@router.get("/reports/{report_id}", response_model=ReportOut)
def own_report(report_id: str, user: User = Depends(roles(Role.CUSTOMER)), db: Session = Depends(get_db)):
    record = db.scalar(select(CustomerReport).where(CustomerReport.id == report_id, CustomerReport.customer_id == user.id))
    if not record: raise HTTPException(status_code=404, detail="Report not found")
    return report_view(record,db)

ADMIN_ROLES = (Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN, Role.PLATFORM_ADMIN)

@router.get("/admin/incidents", response_model=list[IncidentOut])
def incidents(search:str|None=None,source:str|None=None,category:str|None=None,priority:str|None=None,status:str|None=None,department:str|None=None,overdue_only:bool=False,date_from:datetime|None=None,date_to:datetime|None=None,user: User = Depends(roles(*ADMIN_ROLES)), db: Session = Depends(get_db)):
    query = select(Incident).order_by(Incident.created_at.desc())
    if user.role != Role.PLATFORM_ADMIN: query = query.where(Incident.organisation_id == user.organisation_id)
    if user.role == Role.BRANCH_ADMIN: query = query.where(Incident.branch_id == user.branch_id)
    if search:query=query.where(Incident.title.ilike(f"%{search}%")|Incident.description.ilike(f"%{search}%"))
    if source:query=query.where(Incident.source==source)
    if category:query=query.where(Incident.category==category)
    if priority:query=query.where(Incident.priority==priority)
    if status:query=query.where(Incident.status==status)
    if department:query=query.where(Incident.responsible_department==department)
    if date_from:query=query.where(Incident.created_at>=date_from)
    if date_to:query=query.where(Incident.created_at<=date_to)
    rows=[incident_view(i,db) for i in db.scalars(query).all()]
    return [x for x in rows if not overdue_only or x["is_overdue"]]

@router.post("/admin/incidents",response_model=IncidentOut,status_code=201)
def create_manual_incident(data:ManualIncidentCreate,user:User=Depends(roles(*ADMIN_ROLES)),db:Session=Depends(get_db)):
    branch=db.get(Branch,data.branch_id);allowed=branch and (user.role==Role.PLATFORM_ADMIN or branch.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or branch.id==user.branch_id)
    if not allowed:raise HTTPException(404,"Branch not found")
    item=create_incident(db,organisation_id=branch.organisation_id,branch_id=branch.id,source=IncidentSource.MANUAL_ADMIN_ENTRY,category=data.category,title=data.title,description=data.description,priority=data.priority,actor=user,customer_note=data.customer_note)
    db.commit();db.refresh(item);return incident_view(item,db)

@router.patch("/admin/incidents/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: str, data: IncidentUpdate, user: User = Depends(roles(*ADMIN_ROLES)), db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    allowed = incident and (user.role == Role.PLATFORM_ADMIN or incident.organisation_id == user.organisation_id) and (user.role != Role.BRANCH_ADMIN or incident.branch_id == user.branch_id)
    if not allowed: raise HTTPException(status_code=404, detail="Incident not found")
    note=data.internal_note or data.note
    if not note:raise HTTPException(422,"Internal note is required")
    return incident_view(transition_incident(db,incident,data.status,actor=user,internal_note=note,customer_note=data.customer_note,responsible_department=data.responsible_department or data.department,assigned_staff_id=data.assigned_staff_id,assigned_admin_id=data.assigned_admin_id,sla_hours=data.sla_hours,rejection_reason=data.rejection_reason,resolution_reason=data.resolution_reason,reopening_reason=data.reopening_reason,attachment_ids=data.attachment_ids),db)

class IncidentNoteIn(BaseModel):
    note:str=Field(min_length=2,max_length=3000)
    customer_visible:bool=False

@router.post("/admin/incidents/{incident_id}/notes",status_code=201)
def create_incident_note(incident_id:str,data:IncidentNoteIn,user:User=Depends(roles(*ADMIN_ROLES)),db:Session=Depends(get_db)):
    incident=db.get(Incident,incident_id);allowed=incident and (user.role==Role.PLATFORM_ADMIN or incident.organisation_id==user.organisation_id) and (user.role!=Role.BRANCH_ADMIN or incident.branch_id==user.branch_id)
    if not allowed:raise HTTPException(404,"Incident not found")
    return add_note(db,incident,user,data.note,data.customer_visible)

@router.get("/admin/dashboard")
def dashboard(user: User = Depends(roles(*ADMIN_ROLES)), db: Session = Depends(get_db)):
    query = select(Incident)
    if user.role != Role.PLATFORM_ADMIN: query = query.where(Incident.organisation_id == user.organisation_id)
    if user.role == Role.BRANCH_ADMIN: query = query.where(Incident.branch_id == user.branch_id)
    rows = db.scalars(query).all(); open_rows = [i for i in rows if i.status.value not in ("MANUALLY_RESOLVED", "AUTO_RESOLVED", "REJECTED", "CANCELLED")]; high = sum(i.priority in ("HIGH","CRITICAL") for i in open_rows)
    score=smart_store_score(db,user.branch_id) if user.role==Role.BRANCH_ADMIN and user.branch_id else {"score":0,"deductions":[],"additions":[],"explanation":"Select a branch for a canonical score."}
    return {"open_incidents": len(open_rows),"critical_incidents":sum(i.priority=="CRITICAL" for i in open_rows), "high_risk": high, "resolved": len(rows) - len(open_rows), "smart_store_score": score["score"],"score_detail":score, "score_explanation": score["explanation"]}

@router.get("/health/database")
def database_health(db: Session = Depends(get_db)): db.execute(text("SELECT 1")); return {"status": "ok"}

@router.get("/health/vision")
def vision_health(): return {"status":"demo-ready" if settings.vision_demo_enabled else "disabled","mode":"controlled MP4 hybrid rules","rtsp":False,"accuracy_claim":"No universal or 100% accuracy claim. Every signal requires rule-specific validation and human review."}
