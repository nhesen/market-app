import cv2
import numpy as np
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.domain import Branch,CameraEvent,Incident,IncidentStatus
from app.models.vision import Camera,CameraClipMetadata,CameraRule
from app.services.video_pipeline import MP4Pipeline


def write_video(path,frames):
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*"mp4v"),5,(160,120))
    for frame in frames:writer.write(frame)
    writer.release()


def run_rule(database,tmp_path,rule_type,frames,threshold=.05,trigger=2,clear=2):
    path=tmp_path/f"{rule_type.lower()}.mp4";write_video(path,frames)
    with SessionLocal() as db:
        branch=db.scalar(select(Branch));camera=Camera(organisation_id=branch.organisation_id,branch_id=branch.id,name=f"{rule_type} controlled QA",source_path=str(path),source_type="DEMO_MP4");db.add(camera);db.flush()
        rule=CameraRule(organisation_id=branch.organisation_id,camera_id=camera.id,rule_type=rule_type,roi="0,0,1,1",threshold=threshold,trigger_frames=trigger,clear_frames=clear);db.add(rule);db.commit()
        result=MP4Pipeline(db,camera,rule).process(max_frames=30)
        event=db.get(CameraEvent,result.get("event_id")) if result.get("event_id") else None
        incident=db.get(Incident,event.incident_id) if event else None
        evidence=db.scalar(select(CameraClipMetadata).where(CameraClipMetadata.camera_event_id==event.id)) if event else None
        history=[x.status for x in incident.history] if incident else []
        return result,incident,evidence,history


def blank():return np.zeros((120,160,3),dtype=np.uint8)


def test_normal_scene_never_opens_from_clear_frames(tmp_path,database):
    result,incident,evidence,_=run_rule(database,tmp_path,"FLOOR_HAZARD",[blank() for _ in range(6)],.03)
    assert result["status"]=="ok" and result["event_id"] is None and result["current_state"]=="CLEAR"
    assert incident is None and evidence is None


def test_controlled_spill_segmentation_persists_stores_evidence_and_resolves(tmp_path,database):
    spill=[]
    for _ in range(3):
        frame=blank();cv2.ellipse(frame,(80,75),(42,18),0,0,360,(255,80,10),-1);spill.append(frame)
    result,incident,evidence,history=run_rule(database,tmp_path,"FLOOR_HAZARD",spill+[blank() for _ in range(3)],.03)
    assert result["detection_engine"]=="OPENCV_HSV_SEGMENTATION" and incident.status==IncidentStatus.AUTO_RESOLVED
    assert history[-2:]==[IncidentStatus.RESOLUTION_CANDIDATE,IncidentStatus.AUTO_RESOLVED]
    assert evidence and evidence.engine=="OPENCV_HSV_SEGMENTATION" and evidence.frame_number>=2


def test_controlled_blocked_aisle_uses_contour_support(tmp_path,database):
    blocked=[]
    for _ in range(3):
        frame=blank();cv2.rectangle(frame,(35,25),(125,105),(220,220,220),-1);blocked.append(frame)
    result,incident,evidence,_=run_rule(database,tmp_path,"BLOCKED_AISLE",blocked+[blank() for _ in range(3)],.15)
    assert result["detection_engine"]=="OPENCV_CONTOUR_SUPPORT" and incident.status==IncidentStatus.AUTO_RESOLVED and evidence


def test_controlled_promo_depletion_uses_roi_coverage(tmp_path,database):
    stocked=np.full((120,160,3),220,dtype=np.uint8);depleted=blank()
    result,incident,evidence,_=run_rule(database,tmp_path,"PROMO_DEPLETION",[stocked,depleted,depleted,depleted,stocked,stocked,stocked],.7)
    assert result["detection_engine"]=="OPENCV_COVERAGE_RULE" and incident.status==IncidentStatus.AUTO_RESOLVED and evidence.score>=.7


def test_queue_fails_honestly_without_real_yolo_weights(tmp_path,database,monkeypatch):
    monkeypatch.delenv("MARTIQ_YOLO_WEIGHTS",raising=False)
    result,incident,_,_=run_rule(database,tmp_path,"QUEUE",[blank(),blank()],1)
    assert result["status"]=="error" and "real YOLO weights" in result["error"] and incident is None


def test_admin_marks_camera_event_false_alert_with_history(tmp_path,database,client,admin_token):
    blocked=[]
    for _ in range(3):
        frame=blank();cv2.rectangle(frame,(35,25),(125,105),(220,220,220),-1);blocked.append(frame)
    result,incident,_,_=run_rule(database,tmp_path,"BLOCKED_AISLE",blocked+[blank() for _ in range(3)],.15)
    response=client.post(f'/api/v1/admin/camera-events/{result["event_id"]}/false-alert',headers={"Authorization":f"Bearer {admin_token}"})
    assert response.status_code==200 and response.json()["status"]=="REJECTED"
    with SessionLocal() as db:
        stored=db.get(Incident,incident.id)
        assert [x.status for x in stored.history][-2:]==[IncidentStatus.REOPENED,IncidentStatus.REJECTED]


def test_rule_health_exposes_engine_roi_persistence_and_telemetry(tmp_path,database,client,admin_token):
    frame=blank();cv2.ellipse(frame,(80,75),(42,18),0,0,360,(255,80,10),-1)
    run_rule(database,tmp_path,"FLOOR_HAZARD",[frame,frame,blank(),blank()],.03)
    response=client.get("/api/v1/admin/vision-health",headers={"Authorization":f"Bearer {admin_token}"})
    assert response.status_code==200
    rule=next(x for camera in response.json() for x in camera["rules"] if x["rule_type"]=="FLOOR_HAZARD" and x["last_event"])
    assert rule["detection_engine"]=="OPENCV_HSV_SEGMENTATION" and rule["roi"]=="0,0,1,1"
    assert rule["trigger_persistence"]==2 and rule["clear_persistence"]==2 and rule["last_event"]
    assert rule["current_state"]=="AUTO_RESOLVED" and rule["approximate_fps"]>0
