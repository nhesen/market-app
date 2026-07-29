def auth(token): return {"Authorization": f"Bearer {token}"}

def test_ai_assisted_report_review_requires_customer(client,customer_token,admin_token):
    payload={"title":"Döşəmədə maye var","description":"Girişdə döşəməyə maye tökülüb və sürüşmə təhlükəsi yaradır.","category":"SAFETY"}
    response=client.post("/api/v1/reports/ai-review",json=payload,headers=auth(customer_token))
    assert response.status_code==200
    data=response.json();assert data["suggested_category"]=="SAFETY" and data["suggested_priority"]=="HIGH" and data["requires_human_verification"] is True
    assert client.post("/api/v1/reports/ai-review",json=payload,headers=auth(admin_token)).status_code==403

def test_customer_admin_customer_report_flow(client, customer_token, admin_token):
    branch = client.get("/api/v1/branches", headers=auth(customer_token)).json()[0]
    created = client.post("/api/v1/reports", headers=auth(customer_token), json={"branch_id": branch["id"], "category":"EMPTY_SHELF", "title":"Məhsul rəfdə yoxdur", "description":"Süd bölməsində məhsul üçün etiket var, amma rəf boşdur."})
    assert created.status_code == 201
    report = created.json(); assert report["status"] == "NEW" and report["customer_status"] == "RECEIVED"
    incident = next(i for i in client.get("/api/v1/admin/incidents", headers=auth(admin_token)).json() if i["report_id"] == report["id"])
    admin=client.get("/api/v1/auth/me",headers=auth(admin_token)).json()
    steps=[{"status":"PRECHECK","internal_note":"Initial precheck.","customer_note":"Müraciət ilkin yoxlamadadır."},{"status":"VERIFICATION_REQUIRED","internal_note":"Branch evidence required.","customer_note":"Filial yoxlaması aparılır."},{"status":"VERIFIED","internal_note":"Finding verified.","customer_note":"Problem təsdiqləndi."},{"status":"ASSIGNED","internal_note":"Assigned to operations.","customer_note":"İcraçı təyin edildi.","responsible_department":"Operations","assigned_admin_id":admin["id"],"sla_hours":24},{"status":"IN_PROGRESS","internal_note":"Work started.","customer_note":"Problem həll edilir."}]
    for payload in steps:
        changed=client.patch(f'/api/v1/admin/incidents/{incident["id"]}',headers=auth(admin_token),json=payload)
        assert changed.status_code==200,changed.text
    refreshed = client.get(f'/api/v1/reports/{report["id"]}', headers=auth(customer_token)).json()
    assert refreshed["status"] == "IN_PROGRESS" and refreshed["customer_status"]=="IN_PROGRESS" and len(refreshed["history"]) == 6

def test_customer_cannot_access_admin(client, customer_token):
    assert client.get("/api/v1/admin/incidents", headers=auth(customer_token)).status_code == 403
