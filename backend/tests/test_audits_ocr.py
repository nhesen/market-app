from app.services.ocr import extract_date_candidates

def auth(token): return {"Authorization":f"Bearer {token}"}

def test_ocr_candidate_formats_and_empty():
    assert extract_date_candidates("EXP 31.12.2027 LOT 2; 2028-01-15") == ["31.12.2027","2028-01-15"]
    assert extract_date_candidates("no readable date") == []

def test_staff_audit_duplicate_and_finding_incident(client,staff_token,admin_token):
    task=client.get("/api/v1/staff/audits",headers=auth(staff_token)).json()[0]
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/start',headers=auth(staff_token)).status_code==200
    products=client.get("/api/v1/products",headers=auth(staff_token)).json()
    first={"barcode":products[0]["barcode"],"confirmed_date":"01.01.2025","condition":"EXPIRED","note":"Tarix əməkdaş tərəfindən təsdiqləndi.","ocr_corrected":True}
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items',headers=auth(staff_token),json=first).status_code==201
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items',headers=auth(staff_token),json=first).status_code==409
    second={"barcode":products[1]["barcode"],"confirmed_date":"31.12.2027","condition":"NORMAL","note":"Normal","ocr_corrected":False}
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items',headers=auth(staff_token),json=second).status_code==201
    done=client.post(f'/api/v1/staff/audits/{task["id"]}/complete',headers=auth(staff_token))
    assert done.status_code==200 and done.json()["status"]=="COMPLETED"
    assert any(i["source"]=="STAFF_AUDIT" for i in client.get("/api/v1/admin/incidents",headers=auth(admin_token)).json())
    assert client.get("/api/v1/admin/audit-quality-flags",headers=auth(admin_token)).status_code==200

