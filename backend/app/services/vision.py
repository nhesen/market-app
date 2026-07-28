from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models.domain import CameraEvent, Incident, IncidentStatus, IncidentStatusHistory

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
            incident = Incident(organisation_id=self.organisation_id, branch_id=self.branch_id, source="CAMERA", category="FLOOR_HAZARD", title="Görünən döşəmə riski", description="Demo kamera axınında davamlı görünən risk; insan yoxlaması tələb olunur.", priority="HIGH", status=IncidentStatus.VERIFIED)
            incident.history.append(IncidentStatusHistory(status=IncidentStatus.VERIFIED, note="Görünən vəziyyət davamlılıq həddini keçdi."))
            self.db.add(incident); self.db.flush()
            self.event = CameraEvent(organisation_id=self.organisation_id, branch_id=self.branch_id, incident_id=incident.id, rule="FLOOR_HAZARD", detected_frames=self.detected)
            self.db.add(self.event); self.db.commit()
        if self.event and self.clear >= self.rule.clear_frames:
            incident = self.db.get(Incident, self.event.incident_id); incident.status = IncidentStatus.AUTO_RESOLVED
            incident.history.append(IncidentStatusHistory(status=IncidentStatus.AUTO_RESOLVED, note="Aydın dövr həddi keçildi; görünən vəziyyət artıq müşahidə edilmir."))
            self.event.clear_frames = self.clear; self.db.commit()
        return self.event

