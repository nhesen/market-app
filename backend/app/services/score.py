from sqlalchemy import func,select
from sqlalchemy.orm import Session
from app.core.time import utc_now
from app.models.audit import AuditStatus,AuditTask
from app.models.domain import Incident,IncidentStatus

CLOSED={IncidentStatus.MANUALLY_RESOLVED,IncidentStatus.AUTO_RESOLVED,IncidentStatus.REJECTED,IncidentStatus.CANCELLED}

def smart_store_score(db:Session,branch_id:str):
    incidents=db.scalars(select(Incident).where(Incident.branch_id==branch_id)).all();now=utc_now()
    open_rows=[x for x in incidents if x.status not in CLOSED];critical=sum(x.priority=="CRITICAL" for x in open_rows);high=sum(x.priority=="HIGH" for x in open_rows);other=len(open_rows)-critical-high
    overdue=db.scalar(select(func.count(AuditTask.id)).where(AuditTask.branch_id==branch_id,AuditTask.due_at<now,AuditTask.status!=AuditStatus.COMPLETED)) or 0
    valid=db.scalar(select(func.count(AuditTask.id)).where(AuditTask.branch_id==branch_id,AuditTask.status==AuditStatus.COMPLETED)) or 0;bonus=min(10,valid)
    deductions=[{"code":"OPEN_CRITICAL","label":"Open critical incidents","count":critical,"points":critical*15},{"code":"OPEN_HIGH","label":"Open high-risk incidents","count":high,"points":high*10},{"code":"OVERDUE_AUDIT","label":"Overdue audits","count":overdue,"points":overdue*5},{"code":"OTHER_OPEN","label":"Other open incidents","count":other,"points":other*3}]
    return {"score":max(0,min(100,100-sum(x["points"] for x in deductions)+bonus)),"deductions":deductions,"additions":[{"code":"VALID_AUDIT","label":"Completed audit coverage","count":valid,"points":bonus}],"explanation":"100 minus open-risk and overdue-audit deductions plus up to 10 points for completed audit coverage."}
