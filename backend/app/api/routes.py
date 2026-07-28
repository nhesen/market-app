from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_refresh_token, create_token, current_user, hash_password, roles, verify_password
from jose import JWTError, jwt
from pydantic import BaseModel
from app.db.session import get_db
from app.models.domain import Branch, CustomerReport, Incident, LoyaltyCard, News, Product, Role, User
from app.schemas.api import IncidentOut, IncidentUpdate, LoginIn, ReportCreate, ReportOut, TokenOut, UserOut
from app.services.incidents import create_customer_report, incident_view, report_view, set_status

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
    return db.scalars(select(Branch).where(Branch.organisation_id == user.organisation_id)).all()

@router.get("/home")
def home(branch_id:str|None=Query(None),user: User = Depends(roles(Role.CUSTOMER)), db: Session = Depends(get_db)):
    org = user.organisation_id
    news = db.scalars(select(News).where(News.organisation_id == org).order_by(News.published_at.desc())).all()
    products = db.scalars(select(Product).where(Product.organisation_id == org)).all()
    branches_data = db.scalars(select(Branch).where(Branch.organisation_id == org)).all()
    if branch_id and not any(branch.id==branch_id for branch in branches_data):raise HTTPException(404,"Branch not found in your organisation")
    loyalty = db.scalar(select(LoyaltyCard).where(LoyaltyCard.user_id == user.id))
    reports = db.scalars(select(CustomerReport).where(CustomerReport.customer_id == user.id).order_by(CustomerReport.created_at.desc()).limit(4)).all()
    selected=next((branch for branch in branches_data if branch.id==branch_id),branches_data[0] if branches_data else None)
    return {"user": user,"selected_branch":selected,"news": news, "products": products, "discounts": [p for p in products if p.discount_price], "branches": branches_data, "loyalty": loyalty, "reports": [report_view(r) for r in reports]}

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
    branch = db.scalar(select(Branch).where(Branch.id == data.branch_id, Branch.organisation_id == user.organisation_id))
    if not branch: raise HTTPException(status_code=404, detail="Branch not found in your organisation")
    return report_view(create_customer_report(db, user, data))

@router.get("/reports", response_model=list[ReportOut])
def own_reports(user: User = Depends(roles(Role.CUSTOMER)), db: Session = Depends(get_db)):
    return [report_view(r) for r in db.scalars(select(CustomerReport).where(CustomerReport.customer_id == user.id).order_by(CustomerReport.created_at.desc())).all()]

@router.get("/reports/{report_id}", response_model=ReportOut)
def own_report(report_id: str, user: User = Depends(roles(Role.CUSTOMER)), db: Session = Depends(get_db)):
    record = db.scalar(select(CustomerReport).where(CustomerReport.id == report_id, CustomerReport.customer_id == user.id))
    if not record: raise HTTPException(status_code=404, detail="Report not found")
    return report_view(record)

ADMIN_ROLES = (Role.BRANCH_ADMIN, Role.HEAD_OFFICE_ADMIN, Role.PLATFORM_ADMIN)

@router.get("/admin/incidents", response_model=list[IncidentOut])
def incidents(user: User = Depends(roles(*ADMIN_ROLES)), db: Session = Depends(get_db)):
    query = select(Incident).order_by(Incident.created_at.desc())
    if user.role != Role.PLATFORM_ADMIN: query = query.where(Incident.organisation_id == user.organisation_id)
    if user.role == Role.BRANCH_ADMIN: query = query.where(Incident.branch_id == user.branch_id)
    return [incident_view(i) for i in db.scalars(query).all()]

@router.patch("/admin/incidents/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: str, data: IncidentUpdate, user: User = Depends(roles(*ADMIN_ROLES)), db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    allowed = incident and (user.role == Role.PLATFORM_ADMIN or incident.organisation_id == user.organisation_id) and (user.role != Role.BRANCH_ADMIN or incident.branch_id == user.branch_id)
    if not allowed: raise HTTPException(status_code=404, detail="Incident not found")
    return incident_view(set_status(db, incident, data.status, data.note, user, data.department))

@router.get("/admin/dashboard")
def dashboard(user: User = Depends(roles(*ADMIN_ROLES)), db: Session = Depends(get_db)):
    query = select(Incident)
    if user.role != Role.PLATFORM_ADMIN: query = query.where(Incident.organisation_id == user.organisation_id)
    if user.role == Role.BRANCH_ADMIN: query = query.where(Incident.branch_id == user.branch_id)
    rows = db.scalars(query).all(); open_rows = [i for i in rows if i.status.value not in ("RESOLVED", "AUTO_RESOLVED", "REJECTED")]; high = sum(i.priority == "HIGH" for i in open_rows)
    score = max(0, min(100, 100 - high * 10 - max(0, len(open_rows) - high) * 3))
    return {"open_incidents": len(open_rows), "high_risk": high, "resolved": len(rows) - len(open_rows), "smart_store_score": score, "score_explanation": "100 − 10 × open high-risk − 3 × other open issues"}

@router.get("/health/database")
def database_health(db: Session = Depends(get_db)): db.execute(text("SELECT 1")); return {"status": "ok"}

@router.get("/health/vision")
def vision_health(): return {"status": "demo-ready" if settings.vision_demo_enabled else "disabled", "mode": "simulated MP4 continuous source"}
