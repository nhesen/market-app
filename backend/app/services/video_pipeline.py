from app.core.time import utc_now
from pathlib import Path
from time import perf_counter
import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.models.domain import Incident,IncidentStatus
from app.models.vision import Camera,CameraRule
from app.services.vision import PersistenceRule,VisionEventSimulator

class MP4Pipeline:
    """Processes a pre-recorded MP4 continuously as a simulated live source; it is not RTSP."""
    def __init__(self,db:Session,camera:Camera,rule:CameraRule):self.db=db;self.camera=camera;self.rule=rule;self.sim=VisionEventSimulator(db,camera.organisation_id,camera.branch_id,PersistenceRule(rule.trigger_frames,rule.clear_frames));self.last_event_id=None
    def roi_frame(self,frame:np.ndarray)->np.ndarray:
        x1,y1,x2,y2=[float(x) for x in self.rule.roi.split(",")];h,w=frame.shape[:2];return frame[int(y1*h):max(int(y2*h),1),int(x1*w):max(int(x2*w),1)]
    def score(self,frame:np.ndarray)->float:
        roi=self.roi_frame(frame);gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
        if self.rule.rule_type=="PROMO_DEPLETION":return 1-float(np.count_nonzero(gray>45))/gray.size
        edges=cv2.Canny(gray,60,160);return float(np.count_nonzero(edges))/edges.size
    def process(self,max_frames:int=300,loop:bool=False)->dict:
        path=Path(self.camera.source_path);cap=cv2.VideoCapture(str(path));processed=0;started=perf_counter();last_score=0.0
        if not cap.isOpened():self.camera.last_error=f"Cannot open demo MP4: {path}";self.db.commit();return {"status":"error","error":self.camera.last_error,"processed_frames":0}
        while processed<max_frames:
            ok,frame=cap.read()
            if not ok:
                if loop:cap.set(cv2.CAP_PROP_POS_FRAMES,0);continue
                break
            last_score=self.score(frame);hazard=last_score>=self.rule.threshold;event=self.sim.observe(hazard);processed+=1;self.camera.last_frame_at=utc_now()
            if event:self.last_event_id=event.id
        elapsed=max(perf_counter()-started,.001);self.camera.fps_estimate=processed/elapsed;self.camera.last_error=None;self.db.commit();cap.release();return {"status":"ok","processed_frames":processed,"fps":round(self.camera.fps_estimate,2),"last_score":round(last_score,4),"event_id":self.last_event_id,"mode":"simulated live MP4"}
