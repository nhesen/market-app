import io
from datetime import datetime,timedelta
from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.audit import AuditResultItem,AuditStatus,AuditTask,Condition,ReAudit
from app.models.domain import Branch,Incident,Organisation,Product,Role,User
from app.models.retail import IncidentAttachment

def auth(token):return {"Authorization":f"Bearer {token}"}
def token(client,email):return client.post("/api/v1/auth/login",json={"email":email,"password":"Demo123!"}).json()["access_token"]

def test_cross_tenant_and_cross_branch_incidents_are_isolated(client,admin_token):
    city=token(client,"cityadmin@demo.az")
    nova_rows=client.get("/api/v1/admin/incidents",headers=auth(admin_token)).json()
    city_rows=client.get("/api/v1/admin/incidents",headers=auth(city)).json()
    assert nova_rows and city_rows==[]
    incident_id=nova_rows[0]["id"]
    assert client.patch(f"/api/v1/admin/incidents/{incident_id}",headers=auth(city),json={"status":"IN_PROGRESS","note":"Forbidden cross tenant"}).status_code==404
    with SessionLocal() as db:
        nova=db.scalar(select(Organisation).where(Organisation.name=="Nova Market"));other_branch=db.scalar(select(Branch).where(Branch.organisation_id==nova.id,Branch.name.contains("Yasamal")))
        other=Incident(organisation_id=nova.id,branch_id=other_branch.id,source="MANUAL_ADMIN_ENTRY",category="OTHER",title="Other branch only",description="Must not be visible to Narimanov branch admin");db.add(other);db.commit();other_id=other.id
    ids={x["id"] for x in client.get("/api/v1/admin/incidents",headers=auth(admin_token)).json()}
    assert other_id not in ids

def test_uploaded_asset_is_linked_only_to_owners_report(client,customer_token):
    uploaded=client.post("/api/v1/uploads",headers=auth(customer_token),files={"file":("floor.jpg",io.BytesIO(b"jpeg-evidence"),"image/jpeg")})
    assert uploaded.status_code==201
    branch=client.get("/api/v1/branches",headers=auth(customer_token)).json()[0]
    report=client.post("/api/v1/reports",headers=auth(customer_token),json={"branch_id":branch["id"],"category":"FLOOR_LIQUID","title":"Döşəmədə maye var","description":"Girişə yaxın hissədə sürüşmə riski yaradan maye görünür.","attachment_ids":[uploaded.json()["id"]]})
    assert report.status_code==201
    with SessionLocal() as db:
        incident=db.scalar(select(Incident).where(Incident.report_id==report.json()["id"]));links=db.scalars(select(IncidentAttachment).where(IncidentAttachment.incident_id==incident.id)).all()
        assert len(links)==1 and links[0].file_asset_id==uploaded.json()["id"]

def test_reaudit_mismatch_creates_quality_flag(client,admin_token):
    with SessionLocal() as db:
        branch=db.scalar(select(Branch).where(Branch.name.contains("Nərimanov")));product=db.scalar(select(Product).where(Product.organisation_id==branch.organisation_id));original=db.scalar(select(User).where(User.email=="staff@demo.az"))
        reviewer=User(organisation_id=branch.organisation_id,branch_id=branch.id,email="reviewer@demo.az",full_name="Re-audit Reviewer",role=Role.STAFF,password_hash=hash_password("Demo123!"));db.add(reviewer);db.flush()
        task=AuditTask(organisation_id=branch.organisation_id,branch_id=branch.id,assignee_id=original.id,title="Completed source audit",instructions="Re-audit source",required_count=1,status=AuditStatus.COMPLETED,due_at=datetime.utcnow(),started_at=datetime.utcnow()-timedelta(minutes=5),completed_at=datetime.utcnow());db.add(task);db.flush();db.add(AuditResultItem(task_id=task.id,product_id=product.id,barcode=product.barcode,confirmed_date="01.01.2025",condition=Condition.EXPIRED));db.commit();task_id=task.id;reviewer_id=reviewer.id
    made=client.post(f"/api/v1/admin/audits/{task_id}/re-audit?assignee_id={reviewer_id}",headers=auth(admin_token));assert made.status_code==201
    reviewer_token=token(client,"reviewer@demo.az")
    completed=client.post(f'/api/v1/staff/re-audits/{made.json()["id"]}/complete',headers=auth(reviewer_token),json={"condition":"NORMAL"})
    assert completed.status_code==200 and completed.json()["consistent"] is False
    flags=client.get("/api/v1/admin/audit-quality-flags",headers=auth(admin_token)).json();assert any(x["code"]=="RE_AUDIT_MISMATCH" for x in flags)

