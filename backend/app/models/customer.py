import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.domain import uid
from app.core.time import utc_now

class SuggestionStatus(str, enum.Enum):
    SUBMITTED="SUBMITTED"; UNDER_REVIEW="UNDER_REVIEW"; PLANNED="PLANNED"; IMPLEMENTED="IMPLEMENTED"; REJECTED="REJECTED"

class FavouriteProduct(Base):
    __tablename__="favourite_products"; __table_args__=(UniqueConstraint("user_id","product_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True)
    user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
    product_id:Mapped[str]=mapped_column(ForeignKey("products.id"),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class ManagementSuggestion(Base):
    __tablename__="management_suggestions"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    tracking_number:Mapped[str]=mapped_column(String(32),unique=True,index=True)
    organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True)
    branch_id:Mapped[str|None]=mapped_column(ForeignKey("branches.id"),nullable=True,index=True)
    customer_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
    category:Mapped[str]=mapped_column(String(80)); title:Mapped[str]=mapped_column(String(180)); description:Mapped[str]=mapped_column(Text)
    anonymous:Mapped[bool]=mapped_column(Boolean,default=False)
    status:Mapped[SuggestionStatus]=mapped_column(Enum(SuggestionStatus),default=SuggestionStatus.SUBMITTED)
    admin_note:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)
    updated_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now,onupdate=utc_now)

class SuggestionStatusHistory(Base):
    __tablename__="suggestion_status_history"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    suggestion_id:Mapped[str]=mapped_column(ForeignKey("management_suggestions.id"),index=True)
    status:Mapped[SuggestionStatus]=mapped_column(Enum(SuggestionStatus))
    note:Mapped[str]=mapped_column(Text)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class SuggestionAttachment(Base):
    __tablename__="suggestion_attachments";__table_args__=(UniqueConstraint("suggestion_id","file_asset_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True)
    suggestion_id:Mapped[str]=mapped_column(ForeignKey("management_suggestions.id"),index=True)
    file_asset_id:Mapped[str]=mapped_column(ForeignKey("file_assets.id"),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class Notification(Base):
    __tablename__="notifications"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True)
    user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
    kind:Mapped[str]=mapped_column(String(40)); title:Mapped[str]=mapped_column(String(180)); body:Mapped[str]=mapped_column(Text)
    is_read:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class AccountDeletionRequest(Base):
    __tablename__="account_deletion_requests"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
    reason:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class FavouriteCampaign(Base):
    __tablename__="favourite_campaigns"; __table_args__=(UniqueConstraint("user_id","campaign_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True)
    user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
    campaign_id:Mapped[str]=mapped_column(ForeignKey("discount_campaigns.id"),index=True)
    created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)
