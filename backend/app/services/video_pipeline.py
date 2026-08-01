import os
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.vision import Camera,CameraClipMetadata,CameraRule
from app.services.vision import PersistenceRule,VisionEventSimulator


RULE_ENGINES={
    "FLOOR_HAZARD":"OPENCV_HSV_SEGMENTATION",
    "PROMO_DEPLETION":"OPENCV_COVERAGE_RULE",
    "BLOCKED_AISLE":"OPENCV_CONTOUR_SUPPORT",
    "QUEUE":"YOLO_PERSON_DETECTION",
}


class YoloPersonDetector:
    """Optional adapter. It is active only when real Ultralytics runtime and weights are supplied."""
    def __init__(self):
        weights=os.getenv("BAXISH_YOLO_WEIGHTS","")
        if not weights or not Path(weights).is_file():
            raise RuntimeError("QUEUE requires BAXISH_YOLO_WEIGHTS pointing to real YOLO weights; no model was bundled or downloaded.")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("QUEUE requires the optional ultralytics package.") from exc
        self.model=YOLO(weights)

    def person_count(self,frame:np.ndarray)->int:
        result=self.model.predict(frame,classes=[0],verbose=False)[0]
        return 0 if result.boxes is None else len(result.boxes)


class MP4Pipeline:
    """Processes a controlled pre-recorded MP4. It is explicitly not an RTSP/NVR processor."""
    def __init__(self,db:Session,camera:Camera,rule:CameraRule):
        self.db=db;self.camera=camera;self.rule=rule;self.last_event_id=None;self.detector=None
        expected=RULE_ENGINES.get(rule.rule_type)
        if expected:rule.detection_engine=expected
        self.sim=VisionEventSimulator(db,camera.organisation_id,camera.branch_id,PersistenceRule(rule.trigger_frames,rule.clear_frames),rule_type=rule.rule_type,engine=rule.detection_engine,roi=rule.roi,threshold=rule.threshold)

    def roi_frame(self,frame:np.ndarray)->np.ndarray:
        x1,y1,x2,y2=[float(x) for x in self.rule.roi.split(",")];h,w=frame.shape[:2]
        left,right=int(x1*w),max(int(x2*w),1);top,bottom=int(y1*h),max(int(y2*h),1)
        if left>=right or top>=bottom:raise ValueError("ROI must have positive width and height")
        return frame[top:bottom,left:right]

    def score(self,frame:np.ndarray)->float:
        roi=self.roi_frame(frame)
        if roi.size==0:raise ValueError("ROI produced an empty frame")
        if self.rule.rule_type=="FLOOR_HAZARD":
            hsv=cv2.cvtColor(roi,cv2.COLOR_BGR2HSV);mask=cv2.inRange(hsv,np.array([85,70,35]),np.array([135,255,255]))
            return float(np.count_nonzero(mask))/mask.size
        gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
        if self.rule.rule_type=="PROMO_DEPLETION":
            return 1-float(np.count_nonzero(gray>45))/gray.size
        if self.rule.rule_type=="BLOCKED_AISLE":
            _,mask=cv2.threshold(gray,65,255,cv2.THRESH_BINARY);contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            return sum(cv2.contourArea(x) for x in contours if cv2.contourArea(x)>=25)/gray.size
        if self.rule.rule_type=="QUEUE":
            self.detector=self.detector or YoloPersonDetector();return float(self.detector.person_count(roi))
        raise ValueError(f"Unsupported camera rule: {self.rule.rule_type}")

    def _store_evidence(self,event,frame_number:int,score:float,cap):
        evidence=CameraClipMetadata(organisation_id=self.camera.organisation_id,camera_id=self.camera.id,camera_event_id=event.id,frame_path=f"{self.camera.source_path}#frame={frame_number}",clip_path=self.camera.source_path,roi=self.rule.roi,score=score,frame_number=frame_number,source_timestamp_ms=float(cap.get(cv2.CAP_PROP_POS_MSEC)),engine=self.rule.detection_engine)
        self.db.add(evidence);self.db.commit()

    def process(self,max_frames:int=300,loop:bool=False)->dict:
        path=Path(self.camera.source_path);cap=cv2.VideoCapture(str(path));processed=0;started=perf_counter();last_score=0.0
        if self.camera.source_type!="DEMO_MP4":
            return self._error("This endpoint accepts controlled DEMO_MP4 sources only; it does not process RTSP.",cap)
        if not cap.isOpened():return self._error(f"Cannot open controlled MP4: {path}",cap)
        try:
            while processed<max_frames:
                ok,frame=cap.read()
                if not ok:
                    if loop:cap.set(cv2.CAP_PROP_POS_FRAMES,0);continue
                    break
                processed+=1;last_score=self.score(frame);signal=last_score>=self.rule.threshold
                event=self.sim.observe(signal,last_score);now=utc_now();self.camera.last_frame_at=now;self.rule.last_frame_at=now;self.rule.current_state=self.sim.state
                if event:
                    self.last_event_id=event.id;self.rule.last_event_id=event.id
                    if self.sim.opened_now:self._store_evidence(event,processed,last_score,cap)
            elapsed=max(perf_counter()-started,.001);fps=processed/elapsed
            self.camera.fps_estimate=fps;self.rule.fps_estimate=fps;self.camera.last_error=None;self.rule.processing_error=None;self.db.commit()
            return {"status":"ok","processed_frames":processed,"approximate_fps":round(fps,2),"last_score":round(last_score,4),"event_id":self.last_event_id,"current_state":self.rule.current_state,"detection_engine":self.rule.detection_engine,"mode":"controlled MP4"}
        except Exception as exc:
            return self._error(str(exc),cap,processed)
        finally:
            cap.release()

    def _error(self,message:str,cap,processed:int=0):
        self.camera.last_error=message;self.rule.processing_error=message;self.rule.current_state="ERROR";self.db.commit();cap.release()
        return {"status":"error","error":message,"processed_frames":processed,"detection_engine":self.rule.detection_engine,"mode":"controlled MP4"}
