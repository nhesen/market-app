from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.domain import Branch, Incident, IncidentStatus, Organisation


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def login(client, email):
    return client.post("/api/v1/auth/login", json={"email": email, "password": "Demo123!"}).json()["access_token"]


def test_branch_admin_is_hard_scoped_to_own_branch(client, admin_token):
    branches = client.get("/api/v1/admin/branches", headers=auth(admin_token))
    assert branches.status_code == 200 and len(branches.json()) == 1
    own = branches.json()[0]
    with SessionLocal() as db:
        other = db.scalar(select(Branch).where(Branch.organisation_id == own["organisation_id"], Branch.id != own["id"]))
        assert other
        other_id = other.id
    assert client.patch(f"/api/v1/admin/branches/{other_id}", headers=auth(admin_token), json={"name":"Forbidden","address":"Forbidden","hours":"09:00-18:00","is_open":True}).status_code == 404
    assert client.get("/api/v1/admin/products", headers=auth(admin_token)).status_code == 403
    assert client.get("/api/v1/platform/organisations", headers=auth(admin_token)).status_code == 403


def test_head_office_cannot_cross_organisation(client):
    head = login(client, "head@demo.az")
    with SessionLocal() as db:
        city = db.scalar(select(Organisation).where(Organisation.name == "CityMart"))
        city_branch = db.scalar(select(Branch).where(Branch.organisation_id == city.id))
        incident = Incident(organisation_id=city.id, branch_id=city_branch.id, source="QA", category="SECURITY", title="Cross tenant secret", description="Must never leak", priority="HIGH", status=IncidentStatus.VERIFIED)
        db.add(incident); db.commit(); incident_id = incident.id; city_id = city.id
    rows = client.get("/api/v1/admin/incidents", headers=auth(head))
    assert rows.status_code == 200 and all(item["id"] != incident_id for item in rows.json())
    assert client.patch(f"/api/v1/admin/incidents/{incident_id}", headers=auth(head), json={"status":"RESOLVED","note":"forbidden"}).status_code == 404
    assert client.get(f"/api/v1/platform/organisations/{city_id}", headers=auth(head)).status_code == 403
    assert client.get("/api/v1/platform/health", headers=auth(head)).status_code == 403
    network = client.get("/api/v1/admin/network-analytics", headers=auth(head))
    assert network.status_code == 200 and all(row["branch"] != "CityMart Gənclik" for row in network.json())
    with SessionLocal() as db:
        created = db.get(Incident, incident_id)
        if created:
            db.delete(created); db.commit()


def test_platform_admin_authorised_cross_tenant_access(client):
    platform = login(client, "platform@martiq.az")
    organisations = client.get("/api/v1/platform/organisations", headers=auth(platform))
    assert organisations.status_code == 200 and len(organisations.json()) >= 2
    for organisation in organisations.json():
        detail = client.get(f'/api/v1/platform/organisations/{organisation["id"]}', headers=auth(platform))
        assert detail.status_code == 200 and detail.json()["id"] == organisation["id"]
    assert client.get("/api/v1/platform/health", headers=auth(platform)).status_code == 200
    assert client.get("/api/v1/platform/tenant-usage", headers=auth(platform)).status_code == 200
