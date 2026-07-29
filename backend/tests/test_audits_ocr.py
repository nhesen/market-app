from app.services.ocr import extract_date_candidates


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_ocr_candidate_formats_and_empty():
    assert extract_date_candidates("EXP 31.12.2027 LOT 2; 2028-01-15") == ["31.12.2027", "2028-01-15"]
    assert extract_date_candidates("no readable date") == []


def test_staff_camera_audit_quality_and_incident(client, staff_token, admin_token):
    task = client.get("/api/v1/staff/audits", headers=auth(staff_token)).json()[0]
    dashboard = client.get("/api/v1/staff/dashboard", headers=auth(staff_token))
    assert dashboard.status_code == 200
    assert {"today", "overdue", "completed", "re_audits", "quality_flags", "recent_findings", "average_duration_minutes", "completion_rate"} <= dashboard.json().keys()
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/start', headers=auth(staff_token)).status_code == 200
    products = client.get("/api/v1/products", headers=auth(staff_token)).json()

    missing_image = {"barcode": products[0]["barcode"], "confirmed_date": "01.01.2025", "date_confirmed": True, "condition": "EXPIRED"}
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items', headers=auth(staff_token), json=missing_image).status_code == 422
    invalid = {**missing_image, "photo_key": "asset-1", "confirmed_date": "not-a-date"}
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items', headers=auth(staff_token), json=invalid).status_code == 422

    first = {"barcode": products[0]["barcode"], "confirmed_date": "01.01.2025", "date_confirmed": True,
             "condition": "EXPIRED", "note": "Expiry confirmed by staff.", "ocr_corrected": True,
             "ocr_engine": "easyocr", "ocr_candidates": ["01.01.2025"], "correction_count": 3, "photo_key": "asset-1"}
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items', headers=auth(staff_token), json=first).status_code == 201
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items', headers=auth(staff_token), json=first).status_code == 409
    detail = client.get(f'/api/v1/staff/audits/{task["id"]}', headers=auth(staff_token)).json()
    assert detail["unique_products"] is True
    assert detail["items"][0]["date_confirmed"] is True and detail["items"][0]["ocr_candidates"] == ["01.01.2025"]
    lookup = client.get(f'/api/v1/staff/products/barcode/{products[1]["barcode"]}', headers=auth(staff_token))
    assert lookup.status_code == 200 and lookup.json()["id"] == products[1]["id"]

    second = {"barcode": products[1]["barcode"], "confirmed_date": "31.12.2027", "date_confirmed": True,
              "condition": "NORMAL", "note": "Normal", "ocr_corrected": False,
              "ocr_engine": "manual-fallback", "ocr_candidates": [], "photo_key": "asset-2"}
    assert client.post(f'/api/v1/staff/audits/{task["id"]}/items', headers=auth(staff_token), json=second).status_code == 201
    done = client.post(f'/api/v1/staff/audits/{task["id"]}/complete', headers=auth(staff_token))
    assert done.status_code == 200 and done.json()["status"] == "COMPLETED" and done.json()["started_at"] and done.json()["completed_at"]
    assert any(item["source"] == "STAFF_AUDIT" for item in client.get("/api/v1/admin/incidents", headers=auth(admin_token)).json())
    flags = client.get("/api/v1/admin/audit-quality-flags", headers=auth(admin_token))
    assert flags.status_code == 200
    assert {"MISSING_IMAGE", "INVALID_DATE", "EXCESSIVE_OCR_CORRECTIONS", "DUPLICATE_BARCODE", "UNREADABLE_IMAGE"} <= {flag["code"] for flag in flags.json()}
    quality = client.get("/api/v1/staff/quality-summary", headers=auth(staff_token))
    assert quality.status_code == 200 and 0 <= quality.json()["score"] <= 100 and "completion_rate" in quality.json()
