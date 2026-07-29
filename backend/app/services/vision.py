from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.domain import CameraEvent,IncidentSource,IncidentStatus
from app.services.incidents import create_incident,transition_incident

@dataclass
class PersistenceRule:
    detection_frames: int = 3
    clear_frames: int = 3

class VisionEventSimulator:
    """Deterministic frame-state processor; an MP4 decoder can feed booleans into it."""
    def __init__(self, db: Session, organisation_id: str, branch_id: str, rule: PersistenceRule | None = None):
        self.db, self.organisation_id, self.branch_id = db, organisation_id, branch_id
        self.rule = rule or PersistenceRule(); self.detected = 0; self.clear = 0; self.event: CameraEvent | None = None

    def observe(self, hazard_visible: bool) -> CameraEvent | None:
        self.detected = self.detected + 1 if hazard_visible else 0
        self.clear = self.clear + 1 if not hazard_visible else 0
        if not self.event and self.detected >= self.rule.detection_frames:
            incident=create_incident(self.db,organisation_id=self.organisation_id,branch_id=self.branch_id,source=IncidentSource.CAMERA_EVENT,category="FLOOR_HAZARD",title="Görünən döşəmə riski",description="Demo kamera axınında davamlı görünən risk; insan yoxlaması tələb olunur.",priority="HIGH",status=IncidentStatus.VERIFIED)
            self.db.flush()
            self.event = CameraEvent(organisation_id=self.organisation_id, branch_id=self.branch_id, incident_id=incident.id, rule="FLOOR_HAZARD", detected_frames=self.detected)
            self.db.add(self.event); self.db.commit()
        if self.event and self.clear == self.rule.clear_frames:
            from app.models.domain import Incident
            incident=self.db.get(Incident,self.event.incident_id);self.event.clear_frames=self.clear
            transition_incident(self.db,incident,IncidentStatus.AUTO_RESOLVED,actor=None,internal_note="Clear-frame threshold reached.",customer_note=None,resolution_reason="The visible camera condition cleared for the configured frame threshold.",automatic=True)
        return self.event
