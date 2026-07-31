from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.domain import IncidentSource, IncidentStatus, Role


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    role: Role
    organisation_id: str | None
    selected_organisation_id: str | None = None
    branch_id: str | None
    phone: str | None = None
    language: str = "az"
    profile_image_url: str | None = None
    preferred_branch_id: str | None = None


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    user: UserOut


class ReportCreate(BaseModel):
    branch_id: str
    category: str = Field(min_length=2, max_length=80)
    subcategory: str | None = Field(default=None,max_length=80)
    product_id: str | None = None
    barcode: str | None = Field(default=None,max_length=32)
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=10, max_length=3000)
    attachment_ids: list[str] = Field(default_factory=list, max_length=5)


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    from_status: IncidentStatus | None = None
    status: str
    note: str
    internal_note: str | None = None
    customer_note: str | None = None
    actor_id: str | None = None
    actor_type: str = "MANUAL"
    created_at: datetime


class ReportOut(BaseModel):
    id: str
    tracking_number: str
    branch_id: str
    category: str
    subcategory: str | None = None
    product_id: str | None = None
    barcode: str | None = None
    title: str
    description: str
    status: IncidentStatus
    customer_status: str
    created_at: datetime
    history: list[HistoryOut]
    notes: list[dict] = Field(default_factory=list)
    media: list[dict] = Field(default_factory=list)
    rejection_reason: str | None = None
    resolution_note: str | None = None
    reopening_reason: str | None = None


class IncidentOut(BaseModel):
    id: str
    report_id: str | None
    branch_id: str
    organisation_id: str
    source: IncidentSource
    category: str
    title: str
    description: str
    priority: str
    status: IncidentStatus
    department: str | None
    responsible_department: str | None = None
    assigned_staff_id: str | None = None
    assigned_admin_id: str | None = None
    sla_due_at: datetime | None = None
    is_overdue: bool = False
    rejection_reason: str | None = None
    resolution_reason: str | None = None
    reopening_reason: str | None = None
    resolution_actor_type: str | None = None
    updated_at: datetime
    allowed_transitions: list[str] = Field(default_factory=list)
    notes: list[dict] = Field(default_factory=list)
    attachments: list[dict] = Field(default_factory=list)
    created_at: datetime
    history: list[HistoryOut]


class IncidentUpdate(BaseModel):
    status: IncidentStatus
    responsible_department: str | None = None
    department: str | None = None
    assigned_staff_id: str | None = None
    assigned_admin_id: str | None = None
    sla_hours: int | None = Field(default=None,ge=1,le=720)
    internal_note: str | None = Field(default=None,min_length=2,max_length=1000)
    note: str | None = Field(default=None,min_length=2,max_length=1000)
    customer_note: str | None = Field(default=None,max_length=1000)
    rejection_reason: str | None = Field(default=None,max_length=1000)
    resolution_reason: str | None = Field(default=None,max_length=1000)
    reopening_reason: str | None = Field(default=None,max_length=1000)
    attachment_ids: list[str] = Field(default_factory=list,max_length=10)


class ManualIncidentCreate(BaseModel):
    branch_id: str
    category: str = Field(min_length=2,max_length=80)
    title: str = Field(min_length=4,max_length=180)
    description: str = Field(min_length=5,max_length=3000)
    priority: str = Field(default="MEDIUM",pattern="^(LOW|MEDIUM|HIGH)$")
    customer_note: str | None = Field(default=None,max_length=1000)
