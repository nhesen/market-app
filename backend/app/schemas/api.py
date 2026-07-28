from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.domain import IncidentStatus, Role


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
    title: str = Field(min_length=4, max_length=180)
    description: str = Field(min_length=10, max_length=3000)
    attachment_ids: list[str] = Field(default_factory=list, max_length=5)


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: IncidentStatus
    note: str
    created_at: datetime


class ReportOut(BaseModel):
    id: str
    tracking_number: str
    branch_id: str
    category: str
    title: str
    description: str
    status: IncidentStatus
    created_at: datetime
    history: list[HistoryOut]
    media: list[dict] = Field(default_factory=list)
    rejection_reason: str | None = None
    resolution_note: str | None = None


class IncidentOut(BaseModel):
    id: str
    report_id: str | None
    branch_id: str
    source: str
    category: str
    title: str
    description: str
    priority: str
    status: IncidentStatus
    department: str | None
    created_at: datetime
    history: list[HistoryOut]


class IncidentUpdate(BaseModel):
    status: IncidentStatus
    department: str | None = None
    note: str = Field(min_length=2, max_length=255)
