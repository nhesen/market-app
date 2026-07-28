import cv2
import numpy as np
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.domain import Branch,Incident,IncidentStatus
from app.models.vision import Camera,CameraRule
from app.services.video_pipeline import MP4Pipeline

def test_synthetic_mp4_opens_and_auto_resolves_incident(tmp_path,database):
    path=tmp_path/"hazard.mp4";writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*"mp4v"),5,(160,120))
    for _ in range(3):
        frame=np.zeros((120,160,3),dtype=np.uint8);cv2.rectangle(frame,(30,30),(130,90),(255,255,255),3);writer.write(frame)
    for _ in range(4):writer.write(np.zeros((120,160,3),dtype=np.uint8))
    writer.release()
    with SessionLocal() as db:
        branch=db.scalar(select(Branch));camera=Camera(organisation_id=branch.organisation_id,branch_id=branch.id,name="Synthetic QA",source_path=str(path));db.add(camera);db.flush();rule=CameraRule(organisation_id=branch.organisation_id,camera_id=camera.id,rule_type="BLOCKED_AISLE",roi="0,0,1,1",threshold=.005,trigger_frames=2,clear_frames=2);db.add(rule);db.commit()
        result=MP4Pipeline(db,camera,rule).process(max_frames=20)
        assert result["status"]=="ok" and result["processed_frames"]==7 and result["event_id"]
        incident=db.scalar(select(Incident).where(Incident.source=="CAMERA").order_by(Incident.created_at.desc()));assert incident.status==IncidentStatus.AUTO_RESOLVED

