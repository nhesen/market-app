from datetime import timedelta
from app.core.time import utc_now

def auth(client,email):
    token=client.post("/api/v1/auth/login",json={"email":email,"password":"Demo123!"}).json()["access_token"]
    return {"Authorization":f"Bearer {token}"}

def test_audit_template_assignment_and_staff_visibility(client,admin_token,staff_token):
    headers={"Authorization":f"Bearer {admin_token}"};staff=client.get("/api/v1/admin/staff",headers=headers).json()[0]
    payload={"name":"Admin completion dairy audit","description":"Scan dairy expiry labels","category":"DAIRY","required_product_count":2,"require_unique_products":True,"require_photo":True,"require_expiry_date":True,"default_priority":"HIGH","expected_min_duration_seconds":120,"recurrence_type":"NONE","active":True}
    created=client.post("/api/v1/admin/audit-templates",headers=headers,json=payload);assert created.status_code==201,created.text
    template=created.json();assert template["branch_id"]
    assigned=client.post("/api/v1/admin/audit-tasks",headers=headers,json={"template_id":template["id"],"assignee_id":staff["id"],"due_at":(utc_now()+timedelta(days=1)).isoformat(),"priority":"CRITICAL","instructions":"Check two unique products"});assert assigned.status_code==201,assigned.text
    task=assigned.json();assert task["template_id"]==template["id"] and task["priority"]=="CRITICAL"
    visible=client.get("/api/v1/staff/audits",headers={"Authorization":f"Bearer {staff_token}"}).json();assert task["id"] in {x["id"] for x in visible}
    detail=client.get(f"/api/v1/admin/audits/{task['id']}",headers=headers);assert detail.status_code==200

def test_head_loyalty_crud_and_customer_visibility(client,customer_token):
    headers=auth(client,"head@demo.az");body={"title_az":"Audit bonusu","title_en":"Audit reward","description_az":"Demo təklif","description_en":"Demo offer","points_cost":250,"image_url":"/assets/reward.svg","valid_until":(utc_now()+timedelta(days=30)).date().isoformat(),"active":True}
    created=client.post("/api/v1/admin/loyalty-offers",headers=headers,json=body);assert created.status_code==201,created.text
    item=created.json();offers=client.get("/api/v1/loyalty/offers",headers={"Authorization":f"Bearer {customer_token}"}).json();assert item["id"] in {x["id"] for x in offers}
    body["points_cost"]=300;updated=client.put(f"/api/v1/admin/loyalty-offers/{item['id']}",headers=headers,json=body);assert updated.status_code==200 and updated.json()["points_cost"]==300
    assert client.delete(f"/api/v1/admin/loyalty-offers/{item['id']}",headers=headers).status_code==204

def test_camera_rule_safe_update_and_scope(client,admin_token):
    headers={"Authorization":f"Bearer {admin_token}"};rules=client.get("/api/v1/admin/camera-rules",headers=headers).json()
    if not rules:return
    rule=rules[0];response=client.patch(f"/api/v1/admin/camera-rules/{rule['id']}",headers=headers,json={"threshold":rule["threshold"],"trigger_frames":max(2,rule["trigger_frames"]),"clear_frames":max(2,rule["clear_frames"]),"enabled":False});assert response.status_code==200,response.text;assert response.json()["enabled"] is False

def test_analytics_priority_filter_and_canonical_score(client,admin_token):
    headers={"Authorization":f"Bearer {admin_token}"};me=client.get("/api/v1/auth/me",headers=headers).json();dashboard=client.get("/api/v1/admin/dashboard",headers=headers).json();score=client.get(f"/api/v1/analytics/branches/{me['branch_id']}/score",headers=headers).json();assert dashboard["smart_store_score"]==score["score"]
    analytics=client.get("/api/v1/admin/operational-analytics?priority=HIGH",headers=headers);assert analytics.status_code==200;data=analytics.json();assert data["filters"]["priority"]=="HIGH";assert {"critical","resolved_today","audit_completion_rate","camera_false_alert_rate"}<=set(data["summary"])

def test_platform_cannot_be_reached_by_tenant_admin(client,admin_token):
    headers={"Authorization":f"Bearer {admin_token}"};assert client.get("/api/v1/platform/tenant-usage",headers=headers).status_code==403
