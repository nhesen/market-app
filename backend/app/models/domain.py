import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.core.time import utc_now


def uid() -> str:
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"
    BRANCH_ADMIN = "BRANCH_ADMIN"
    HEAD_OFFICE_ADMIN = "HEAD_OFFICE_ADMIN"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    PRECHECK = "PRECHECK"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    VERIFIED = "VERIFIED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLUTION_CANDIDATE = "RESOLUTION_CANDIDATE"
    AUTO_RESOLVED = "AUTO_RESOLVED"
    MANUALLY_RESOLVED = "MANUALLY_RESOLVED"
    RESOLVED = "MANUALLY_RESOLVED"  # compatibility alias; API serialises MANUALLY_RESOLVED
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"
    CANCELLED = "CANCELLED"


class IncidentSource(str, enum.Enum):
    CUSTOMER_REPORT = "CUSTOMER_REPORT"
    STAFF_AUDIT = "STAFF_AUDIT"
    CAMERA_EVENT = "CAMERA_EVENT"
    MANUAL_ADMIN_ENTRY = "MANUAL_ADMIN_ENTRY"


class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    address: Mapped[str] = mapped_column(String(255))
    hours: Mapped[str] = mapped_column(String(80), default="08:00–23:00")
    distance_km: Mapped[float] = mapped_column(Float, default=1.2)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str | None] = mapped_column(ForeignKey("organisations.id"), index=True, nullable=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="az")
    profile_image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), nullable=True)
    preferences_json: Mapped[str] = mapped_column(Text, default="{}")
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class News(Base):
    __tablename__ = "news"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), nullable=True)
    title_az: Mapped[str] = mapped_column(String(180))
    title_en: Mapped[str] = mapped_column(String(180))
    summary_az: Mapped[str] = mapped_column(Text)
    summary_en: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(String(255), default="/assets/news-market.svg")
    published_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    name: Mapped[str] = mapped_column(String(180))
    brand: Mapped[str] = mapped_column(String(120))
    barcode: Mapped[str] = mapped_column(String(32), unique=True)
    category: Mapped[str] = mapped_column(String(80))
    price: Mapped[float] = mapped_column(Float)
    discount_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str] = mapped_column(String(255), default="/assets/product.svg")


class LoyaltyCard(Base):
    __tablename__ = "loyalty_cards"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(80), default="Bonus kartı")
    card_number: Mapped[str] = mapped_column(String(24), default="9900000000000000")
    balance: Mapped[int] = mapped_column(Integer, default=0)
    monthly_earned: Mapped[int] = mapped_column(Integer, default=0)
    expiring: Mapped[int] = mapped_column(Integer, default=0)
    expiring_on: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CustomerReport(Base):
    __tablename__ = "customer_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tracking_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(80))
    subcategory: Mapped[str | None] = mapped_column(String(80), nullable=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.NEW)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    incident: Mapped["Incident"] = relationship(back_populates="report", uselist=False)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("customer_reports.id"), unique=True, nullable=True)
    source: Mapped[IncidentSource] = mapped_column(Enum(IncidentSource))
    category: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(24), default="MEDIUM")
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.NEW)
    responsible_department: Mapped[str | None] = mapped_column("department",String(120), nullable=True)
    assigned_staff_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"),nullable=True,index=True)
    assigned_admin_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"),nullable=True,index=True)
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True,index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text,nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(Text,nullable=True)
    reopening_reason: Mapped[str | None] = mapped_column(Text,nullable=True)
    resolution_actor_type: Mapped[str | None] = mapped_column(String(20),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    report: Mapped[CustomerReport | None] = relationship(back_populates="incident")
    history: Mapped[list["IncidentStatusHistory"]] = relationship(cascade="all, delete-orphan", order_by="IncidentStatusHistory.created_at")


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus))
    from_status: Mapped[IncidentStatus | None] = mapped_column(Enum(IncidentStatus),nullable=True)
    note: Mapped[str] = mapped_column(String(255))
    internal_note: Mapped[str | None] = mapped_column(Text,nullable=True)
    customer_note: Mapped[str | None] = mapped_column(Text,nullable=True)
    actor_type: Mapped[str] = mapped_column(String(20),default="MANUAL")
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class IncidentNote(Base):
    __tablename__="incident_notes"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    incident_id:Mapped[str]=mapped_column(ForeignKey("incidents.id"),index=True)
    actor_id:Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True)
    visibility:Mapped[str]=mapped_column(String(20))
    note:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)


class CameraEvent(Base):
    __tablename__ = "camera_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), unique=True)
    rule: Mapped[str] = mapped_column(String(80))
    detected_frames: Mapped[int] = mapped_column(Integer)
    clear_frames: Mapped[int] = mapped_column(Integer, default=0)
