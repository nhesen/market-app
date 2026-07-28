from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.domain import Branch, Incident, IncidentStatus
from app.services.vision import PersistenceRule, VisionEventSimulator

def test_persistence_and_auto_resolve(database):
    with SessionLocal() as db:
        branch = db.scalar(select(Branch)); sim = VisionEventSimulator(db, branch.organisation_id, branch.id, PersistenceRule(2, 2))
        assert sim.observe(True) is None
        event = sim.observe(True); assert event is not None
        sim.observe(False); sim.observe(False)
        assert db.get(Incident, event.incident_id).status == IncidentStatus.AUTO_RESOLVED

