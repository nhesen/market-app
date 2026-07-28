from datetime import datetime
from sqlalchemy import Boolean,DateTime,Float,ForeignKey,Integer,String,Text
from sqlalchemy.orm import Mapped,mapped_column
from app.db.session import Base
from app.models.domain import uid
from app.core.time import utc_now

class Camera(Base):
    __tablename__="cameras"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);branch_id:Mapped[str]=mapped_column(ForeignKey("branches.id"),index=True);name:Mapped[str]=mapped_column(String(120));source_type:Mapped[str]=mapped_column(String(30),default="DEMO_MP4");source_path:Mapped[str]=mapped_column(String(255));enabled:Mapped[bool]=mapped_column(Boolean,default=True);last_frame_at:Mapped[datetime|None]=mapped_column(DateTime,nullable=True);last_error:Mapped[str|None]=mapped_column(Text,nullable=True);fps_estimate:Mapped[float|None]=mapped_column(Float,nullable=True)
class CameraRule(Base):
    __tablename__="camera_rules"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);camera_id:Mapped[str]=mapped_column(ForeignKey("cameras.id"),index=True);rule_type:Mapped[str]=mapped_column(String(50));roi:Mapped[str]=mapped_column(String(120),default="0,0,1,1");threshold:Mapped[float]=mapped_column(Float,default=.3);trigger_frames:Mapped[int]=mapped_column(Integer,default=15);clear_frames:Mapped[int]=mapped_column(Integer,default=30);enabled:Mapped[bool]=mapped_column(Boolean,default=True)
class CameraClipMetadata(Base):
    __tablename__="camera_clip_metadata"
    id:Mapped[str]=mapped_column(String(36),primary_key=True,default=uid);organisation_id:Mapped[str]=mapped_column(ForeignKey("organisations.id"),index=True);camera_id:Mapped[str]=mapped_column(ForeignKey("cameras.id"),index=True);camera_event_id:Mapped[str]=mapped_column(ForeignKey("camera_events.id"),index=True);frame_path:Mapped[str|None]=mapped_column(String(255),nullable=True);clip_path:Mapped[str|None]=mapped_column(String(255),nullable=True);roi:Mapped[str]=mapped_column(String(120));score:Mapped[float]=mapped_column(Float);created_at:Mapped[datetime]=mapped_column(DateTime,default=utc_now)
