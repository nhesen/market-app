import io
from datetime import timedelta
from sqlalchemy import func,select
from app.core.time import utc_now
from app.db.session import SessionLocal
from app.models.domain import Branch,News,Organisation,User

def auth(token):return {"Authorization":f"Bearer {token}"}

def test_news_publish_branch_and_tenant_scope(client,customer_token):
    headers=auth(customer_token)
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email=="customer@demo.az"));nova=db.scalar(select(Organisation).where(Organisation.name=="Nova Market"));city=db.scalar(select(Organisation).where(Organisation.name=="CityMart"));branches=db.scalars(select(Branch).where(Branch.organisation_id==nova.id).order_by(Branch.name)).all()
        user.selected_organisation_id=nova.id;user.preferred_branch_id=branches[0].id
        rows=[News(organisation_id=nova.id,title_az="Ümumi xəbər",title_en="Scoped global news",summary_az="Hamı üçün",summary_en="For everyone",body_az="Bütün filiallar üçün məzmun.",body_en="Content for every branch.",status="PUBLISHED"),News(organisation_id=nova.id,branch_id=branches[0].id,title_az="Seçilmiş filial",title_en="Selected branch news",summary_az="Bu filial",summary_en="This branch",body_az="Seçilmiş filial məzmunu.",body_en="Selected branch content.",status="PUBLISHED"),News(organisation_id=nova.id,branch_id=branches[1].id,title_az="Başqa filial",title_en="Other branch news",summary_az="Başqa filial",summary_en="Other branch",body_az="Gizli filial məzmunu.",body_en="Hidden branch content.",status="PUBLISHED"),News(organisation_id=city.id,title_az="Başqa market",title_en="Other market news",summary_az="Başqa market",summary_en="Other market",body_az="Gizli market məzmunu.",body_en="Hidden market content.",status="PUBLISHED"),News(organisation_id=nova.id,title_az="Qaralama",title_en="Draft news",summary_az="Qaralama",summary_en="Draft",body_az="Müştəriyə görünməməlidir.",body_en="Must not be customer visible.",status="DRAFT"),News(organisation_id=nova.id,title_az="Arxiv",title_en="Archived news",summary_az="Arxiv",summary_en="Archived",body_az="Arxiv məzmunu.",body_en="Archived content.",status="ARCHIVED"),News(organisation_id=nova.id,title_az="Bitmiş elan",title_en="Expired announcement",summary_az="Bitib",summary_en="Expired",body_az="Müddəti bitmiş məzmun.",body_en="Expired content.",status="PUBLISHED",valid_until=utc_now()-timedelta(days=1))]
        db.add_all(rows);db.commit();ids={row.title_en:row.id for row in rows}
    feed=client.get("/api/v1/news",headers=headers);assert feed.status_code==200
    titles={row["title_en"] for row in feed.json()}
    assert {"Scoped global news","Selected branch news"}<=titles
    assert not {"Other branch news","Other market news","Draft news","Archived news","Expired announcement"}&titles
    assert client.get(f'/api/v1/news/{ids["Selected branch news"]}',headers=headers).status_code==200
    for title in ("Other branch news","Other market news","Draft news","Archived news","Expired announcement"):
        assert client.get(f'/api/v1/news/{ids[title]}',headers=headers).status_code==404

def test_seed_news_inventory_is_idempotent(client):
    from scripts.seed import run
    with SessionLocal() as db:before=db.scalar(select(func.count()).select_from(News))
    run();run()
    with SessionLocal() as db:
        after=db.scalar(select(func.count()).select_from(News));nova=db.scalar(select(Organisation).where(Organisation.name=="Nova Market"));city=db.scalar(select(Organisation).where(Organisation.name=="CityMart"))
        assert after==before
        assert db.scalar(select(func.count()).select_from(News).where(News.organisation_id==nova.id))>=10
        assert db.scalar(select(func.count()).select_from(News).where(News.organisation_id==city.id))>=6

def test_customer_media_requires_owner_authentication(client,customer_token):
    uploaded=client.post("/api/v1/uploads",headers=auth(customer_token),files={"file":("private.jpg",io.BytesIO(b"private-evidence"),"image/jpeg")})
    assert uploaded.status_code==201 and uploaded.json()["url"].startswith("/api/v1/media/")
    path=uploaded.json()["url"]
    assert client.get(path).status_code in (401,403)
    assert client.get(path,headers=auth(customer_token)).status_code==200
    assert client.get("/uploads/private.jpg").status_code==404
