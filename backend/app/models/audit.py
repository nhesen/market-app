import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.domain import uid
from app.core.time import utc_now

class AuditStatus(str,enum.Enum): ASSIGNED="ASSIGNED";IN_PROGRESS="IN_PROGRESS";COMPLETED="COMPLETED";OVERDUE="OVERDUE"
class Condition(str,enum.Enum): NORMAL="NORMAL";EXPIRING_SOON="EXPIRING_SOON";EXPIRED="EXPIRED";DAMAGED="DAMAGED";INVALID_PRODUCT="INVALID_PRODUCT";UNREADABLE="UNREADABLE";OTHER="OTHER"

class AuditTask(Base):
    __tablename__="audit_tasks"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True);assignee_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
    title:Mapped[str]=mapped_column(String(180));instructions:Mapped[str]=mapped_column(Text);required_count:Mapped[int]=mapped_column(Integer,default=3);unique_products:Mapped[bool]=mapped_column(Boolean,default=True);priority:Mapped[str]=mapped_column(String(20),default="MEDIUM");status:Mapped[AuditStatus]=mapped_column(Enum(AuditStatus),default=AuditStatus.ASSIGNED);due_at:Mapped[datetime]=mapped_column(DateTime);started_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True);completed_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)

class AuditResultItem(Base):
    __tablename__="audit_result_items";__table_args__=(UniqueConstraint("task_id","product_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);task_id:Mapped[str]=mapped_column(ForeignKey("audit_tasks.id"),index=True);product_id:Mapped[str]=mapped_column(ForeignKey("products.id"),index=True);barcode:Mapped[str]=mapped_column(String(32));confirmed_date:Mapped[str|None]=mapped_column(String(10),nullable=True);date_confirmed:Mapped[bool]=mapped_column(Boolean,default=False);ocr_corrected:Mapped[bool]=mapped_column(Boolean,default=False);ocr_engine:Mapped[str|None]=mapped_column(String(60),nullable=True);ocr_candidates_json:Mapped[str]=mapped_column(Text,default="[]");correction_count:Mapped[int]=mapped_column(Integer,default=0);condition:Mapped[Condition]=mapped_column(Enum(Condition));note:Mapped[str|None]=mapped_column(Text,nullable=True);photo_key:Mapped[str|None]=mapped_column(String(255),nullable=True);created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class AuditQualityFlag(Base):
    __tablename__="audit_quality_flags"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True);task_id:Mapped[str]=mapped_column(ForeignKey("audit_tasks.id"),index=True);code:Mapped[str]=mapped_column(String(60));message:Mapped[str]=mapped_column(String(255));severity:Mapped[str]=mapped_column(String(20),default="WARNING");created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class ReAudit(Base):
    __tablename__="re_audits"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True);original_task_id:Mapped[str]=mapped_column(ForeignKey("audit_tasks.id"),index=True);assignee_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True);status:Mapped[str]=mapped_column(String(30),default="ASSIGNED");original_condition:Mapped[str]=mapped_column(String(30));re_audit_condition:Mapped[str|None]=mapped_column(String(30),nullable=True);consistent:Mapped[bool|None]=mapped_column(Boolean,nullable=True);created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now);completed_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
