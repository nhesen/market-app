from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.domain import Branch

def auth(t):return {"Authorization":f"Bearer {t}"}
def test_refresh_and_score(client,customer_token,admin_token):
    login=client.post("/api/v1/auth/login",json={"email":"customer@demo.az","password":"Demo123!"}).json()
    refreshed=client.post("/api/v1/auth/refresh",json={"refresh_token":login["refresh_token"]})
    assert refreshed.status_code==200 and refreshed.json()["access_token"]
    with SessionLocal() as db:branch=db.scalar(select(Branch))
    score=client.get(f"/api/v1/analytics/branches/{branch.id}/score",headers=auth(admin_token))
    assert score.status_code==200 and 0<=score.json()["score"]<=100 and score.json()["deductions"]

def test_operational_analytics_metrics_and_filters(client):
    head=client.post("/api/v1/auth/login",json={"email":"head@demo.az","password":"Demo123!"}).json()["access_token"]
    response=client.get("/api/v1/admin/operational-analytics?source=CUSTOMER_REPORT",headers=auth(head))
    assert response.status_code==200
    data=response.json()
    assert {"average_resolution_hours","median_resolution_hours","overdue","auto_resolved","manual_resolved","customer_verification_rate","re_audit_consistency_rate"}<=data["summary"].keys()
    assert all(row["name"]=="CUSTOMER_REPORT" for row in data["by_source"])

def test_platform_access_is_role_protected(client,admin_token):
    assert client.get("/api/v1/platform/organisations",headers=auth(admin_token)).status_code==403
    platform=client.post("/api/v1/auth/login",json={"email":"platform@martiq.az","password":"Demo123!"}).json()["access_token"]
    assert client.get("/api/v1/platform/usage",headers=auth(platform)).status_code==200

def test_platform_can_edit_organisation_and_deactivate_tenant_admin(client):
    platform=client.post("/api/v1/auth/login",json={"email":"platform@martiq.az","password":"Demo123!"}).json()["access_token"];headers=auth(platform)
    org=client.get("/api/v1/platform/organisations",headers=headers).json()[0]
    updated=client.patch(f'/api/v1/platform/organisations/{org["id"]}',headers=headers,json={"name":org["name"],"is_active":False})
    assert updated.status_code==200 and updated.json()["is_active"] is False
    client.patch(f'/api/v1/platform/organisations/{org["id"]}',headers=headers,json={"name":org["name"],"is_active":True})
    admin=next(x for x in client.get("/api/v1/platform/admins",headers=headers).json() if x["role"]=="BRANCH_ADMIN")
    changed=client.patch(f'/api/v1/platform/admins/{admin["id"]}',headers=headers,json={"full_name":admin["full_name"],"is_active":False,"branch_id":admin["branch_id"]})
    assert changed.status_code==200 and changed.json()["is_active"] is False
    client.patch(f'/api/v1/platform/admins/{admin["id"]}',headers=headers,json={"full_name":admin["full_name"],"is_active":True,"branch_id":admin["branch_id"]})

def test_all_demo_roles_login_and_logout(client):
    expected={"customer@demo.az":"CUSTOMER","staff@demo.az":"STAFF","branch@demo.az":"BRANCH_ADMIN","head@demo.az":"HEAD_OFFICE_ADMIN","platform@martiq.az":"PLATFORM_ADMIN"}
    for email,role in expected.items():
        response=client.post("/api/v1/auth/login",json={"email":email,"password":"Demo123!"})
        assert response.status_code==200
        payload=response.json()
        assert payload["access_token"] and payload["refresh_token"] and payload["user"]["role"]==role
        headers=auth(payload["access_token"])
        assert client.get("/api/v1/auth/me",headers=headers).json()["role"]==role
        assert client.post("/api/v1/auth/logout",headers=headers).status_code==204
    assert client.post("/api/v1/auth/login",json={"email":"customer@demo.az","password":"wrong-password"}).status_code==401
