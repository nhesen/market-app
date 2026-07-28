import enum
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


def uid() -> str:
    return str(uuid.uuid4())


class Role(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    STAFF = "STAFF"
    BRANCH_ADMIN = "BRANCH_ADMIN"
    HEAD_OFFICE_ADMIN = "HEAD_OFFICE_ADMIN"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class IncidentStatus(str, enum.Enum):
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    AUTO_RESOLVED = "AUTO_RESOLVED"
    REOPENED = "REOPENED"


class Organisation(Base):
    __tablename__ = "organisations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    balance: Mapped[int] = mapped_column(Integer, default=0)
    monthly_earned: Mapped[int] = mapped_column(Integer, default=0)
    expiring: Mapped[int] = mapped_column(Integer, default=0)


class CustomerReport(Base):
    __tablename__ = "customer_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tracking_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.VERIFICATION_REQUIRED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    incident: Mapped["Incident"] = relationship(back_populates="report", uselist=False)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    report_id: Mapped[str | None] = mapped_column(ForeignKey("customer_reports.id"), unique=True, nullable=True)
    source: Mapped[str] = mapped_column(String(32))
    category: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(24), default="MEDIUM")
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus), default=IncidentStatus.VERIFICATION_REQUIRED)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    report: Mapped[CustomerReport | None] = relationship(back_populates="incident")
    history: Mapped[list["IncidentStatusHistory"]] = relationship(cascade="all, delete-orphan", order_by="IncidentStatusHistory.created_at")


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus))
    note: Mapped[str] = mapped_column(String(255))
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CameraEvent(Base):
    __tablename__ = "camera_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    organisation_id: Mapped[str] = mapped_column(ForeignKey("organisations.id"), index=True)
    branch_id: Mapped[str] = mapped_column(ForeignKey("branches.id"), index=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), unique=True)
    rule: Mapped[str] = mapped_column(String(80))
    detected_frames: Mapped[int] = mapped_column(Integer)
    clear_frames: Mapped[int] = mapped_column(Integer, default=0)
