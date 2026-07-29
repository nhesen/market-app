from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.domain import CameraEvent,IncidentSource,IncidentStatus
from app.services.incidents import create_incident,transition_incident


@dataclass
class PersistenceRule:
    detection_frames:int=3
    clear_frames:int=3


RULE_COPY={
    "FLOOR_HAZARD":("FLOOR_HAZARD","Controlled floor-hazard signal","A rule-based OpenCV segmentation signal persisted inside the configured ROI. Human review is required."),
    "BLOCKED_AISLE":("BLOCKED_AISLE","Possible blocked aisle","Object coverage persisted inside the aisle ROI. This is not a safety conclusion and requires human review."),
    "PROMO_DEPLETION":("PROMO_DEPLETION","Possible depleted promo zone","Low visual coverage persisted inside the configured promo ROI. Human review is required."),
    "QUEUE":("QUEUE","Queue threshold exceeded","YOLO person count persisted inside the configured queue ROI. Human review is required."),
}


class VisionEventSimulator:
    """State machine fed by rule-specific analyzers; it does not perform detection itself."""
    def __init__(self,db:Session,organisation_id:str,branch_id:str,rule:PersistenceRule|None=None,*,rule_type:str="FLOOR_HAZARD",engine:str="OPENCV_RULE_BASED",roi:str="0,0,1,1",threshold:float=0):
        self.db=db;self.organisation_id=organisation_id;self.branch_id=branch_id
        self.rule=rule or PersistenceRule();self.rule_type=rule_type;self.engine=engine;self.roi=roi;self.threshold=threshold
        self.detected=0;self.clear=0;self.event:CameraEvent|None=None;self.state="CLEAR";self.opened_now=False;self.resolved_now=False;self.resolved=False

    def observe(self,hazard_visible:bool,score:float|None=None)->CameraEvent|None:
        self.opened_now=False;self.resolved_now=False
        if self.resolved:
            self.state="AUTO_RESOLVED";return self.event
        self.detected=self.detected+1 if hazard_visible else 0
        self.clear=self.clear+1 if not hazard_visible else 0
        if not self.event:
            self.state="TRIGGER_PENDING" if self.detected else "CLEAR"
        if not self.event and self.detected>=self.rule.detection_frames:
            category,title,description=RULE_COPY.get(self.rule_type,(self.rule_type,"Camera rule signal",f"{self.engine} signal persisted inside the configured ROI. Human review is required."))
            incident=create_incident(self.db,organisation_id=self.organisation_id,branch_id=self.branch_id,source=IncidentSource.CAMERA_EVENT,category=category,title=title,description=description,priority="HIGH",status=IncidentStatus.IN_PROGRESS)
            self.db.flush()
            self.event=CameraEvent(organisation_id=self.organisation_id,branch_id=self.branch_id,incident_id=incident.id,rule=self.rule_type,detection_engine=self.engine,roi=self.roi,threshold=self.threshold,trigger_score=score,detected_frames=self.detected)
            self.db.add(self.event);self.db.commit();self.state="ACTIVE";self.opened_now=True
        elif self.event and hazard_visible:
            self.state="ACTIVE"
        elif self.event and self.clear:
            self.state="CLEAR_PENDING"
        if self.event and self.clear==self.rule.clear_frames:
            from app.models.domain import Incident
            incident=self.db.get(Incident,self.event.incident_id);self.event.clear_frames=self.clear
            transition_incident(self.db,incident,IncidentStatus.RESOLUTION_CANDIDATE,actor=None,internal_note="Configured clear persistence reached.",resolution_reason=None,automatic=True)
            transition_incident(self.db,incident,IncidentStatus.AUTO_RESOLVED,actor=None,internal_note="Camera rule remained clear after the resolution candidate was created.",resolution_reason="The configured ROI remained clear for the required persistence period.",automatic=True)
            self.state="AUTO_RESOLVED";self.resolved_now=True;self.resolved=True
        return self.event
