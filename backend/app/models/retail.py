from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.domain import uid
from app.core.time import utc_now

class ProductCategory(Base):
    __tablename__="product_categories";__table_args__=(UniqueConstraint("organisation_id","name"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);name:Mapped[str]=mapped_column(String(100));created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class ProductPrice(Base):
    __tablename__="product_prices";__table_args__=(UniqueConstraint("branch_id","product_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True);product_id:Mapped[str]=mapped_column(ForeignKey("products.id"),index=True);price:Mapped[float]=mapped_column(Float);previous_price:Mapped[float|None]=mapped_column(Float,nullable=True);available:Mapped[bool]=mapped_column(Boolean,default=True);updated_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now,onupdate=utc_now)

class DiscountCampaign(Base):
    __tablename__="discount_campaigns"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);title:Mapped[str]=mapped_column(String(180));description:Mapped[str]=mapped_column(Text);starts_on:Mapped[date]=mapped_column(Date);ends_on:Mapped[date]=mapped_column(Date);published:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class DiscountCampaignProduct(Base):
    __tablename__="discount_campaign_products";__table_args__=(UniqueConstraint("campaign_id","product_id","branch_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);campaign_id:Mapped[str]=mapped_column(ForeignKey("discount_campaigns.id"),index=True);product_id:Mapped[str]=mapped_column(ForeignKey("products.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True);discount_price:Mapped[float]=mapped_column(Float)

class FavouriteBranch(Base):
    __tablename__="favourite_branches";__table_args__=(UniqueConstraint("user_id","branch_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True)

class LoyaltyTransaction(Base):
    __tablename__="loyalty_transactions"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);card_id:Mapped[str]=mapped_column(ForeignKey("loyalty_cards.id"),index=True);amount:Mapped[int]=mapped_column(Integer);description:Mapped[str]=mapped_column(String(180));created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class LoyaltyRewardOffer(Base):
    __tablename__="loyalty_reward_offers"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid)
    organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True)
    title_az:Mapped[str]=mapped_column(String(180));title_en:Mapped[str]=mapped_column(String(180))
    description_az:Mapped[str]=mapped_column(Text);description_en:Mapped[str]=mapped_column(Text)
    points_cost:Mapped[int]=mapped_column(Integer);image_url:Mapped[str]=mapped_column(String(255),default="/assets/reward.svg")
    valid_until:Mapped[date]=mapped_column(Date);active:Mapped[bool]=mapped_column(Boolean,default=True)

class BranchService(Base):
    __tablename__="branch_services";__table_args__=(UniqueConstraint("branch_id","name"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True);name:Mapped[str]=mapped_column(String(100))

class FileAsset(Base):
    __tablename__="file_assets"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);owner_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True);storage_key:Mapped[str]=mapped_column(String(255),unique=True);original_name:Mapped[str]=mapped_column(String(255));mime_type:Mapped[str]=mapped_column(String(100));size:Mapped[int]=mapped_column(Integer);created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class OrganisationModule(Base):
    __tablename__="organisation_modules";__table_args__=(UniqueConstraint("organisation_id","module"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);module:Mapped[str]=mapped_column(String(80));enabled:Mapped[bool]=mapped_column(Boolean,default=True)

class SystemSetting(Base):
    __tablename__="system_settings"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);key:Mapped[str]=mapped_column(String(100),unique=True);value:Mapped[str]=mapped_column(Text);updated_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now,onupdate=utc_now)

class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str|None]=mapped_column(ForeignKey("organisations.id"),nullable=True,index=True);actor_id:Mapped[str|None]=mapped_column(ForeignKey("users.id"),nullable=True,index=True);action:Mapped[str]=mapped_column(String(100));entity_type:Mapped[str]=mapped_column(String(80));entity_id:Mapped[str|None]=mapped_column(String(36),nullable=True);detail:Mapped[str|None]=mapped_column(Text,nullable=True);created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)

class IncidentAttachment(Base):
    __tablename__="incident_attachments";__table_args__=(UniqueConstraint("incident_id","file_asset_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);incident_id:Mapped[str]=mapped_column(ForeignKey("incidents.id"),index=True);file_asset_id:Mapped[str]=mapped_column(ForeignKey("file_assets.id"),index=True);customer_visible:Mapped[bool]=mapped_column(Boolean,default=True);created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)
