from datetime import date,datetime,timedelta
from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import Base,SessionLocal,engine
from app.models.audit import AuditTask
from app.models.customer import Notification
from app.models.domain import Branch,CustomerReport,Incident,IncidentStatus,IncidentStatusHistory,LoyaltyCard,News,Organisation,Product,Role,User
from app.models.retail import BranchService,DiscountCampaign,DiscountCampaignProduct,LoyaltyTransaction,OrganisationModule,ProductCategory,ProductPrice

PASSWORD="Demo123!"
CATALOG=[
("Təzə süd 1 L","Səhər","Süd məhsulları",2.79),("Kefir 1 L","Səhər","Süd məhsulları",3.19),("Qatıq 500 q","Bərəkət","Süd məhsulları",2.39),("Kərə yağı 200 q","Yaylaq","Süd məhsulları",5.99),
("Yulaf lopası 500 q","Dən","Ərzaq",4.60),("Düyü 1 kq","Dən","Ərzaq",3.80),("Makaron 500 q","Masa","Ərzaq",1.89),("Zeytun yağı 500 ml","Lalə","Ərzaq",11.90),
("Alma şirəsi 1 L","Bağça","İçkilər",3.40),("Mineral su 1 L","Bulaq","İçkilər",1.20),("Qara çay 100 q","Xəzər","İçkilər",4.25),("Qəhvə 200 q","Səma","İçkilər",9.80),
("Alma 1 kq","Bağça","Meyvə və tərəvəz",2.49),("Banan 1 kq","Tropik","Meyvə və tərəvəz",3.89),("Pomidor 1 kq","Yaşıl","Meyvə və tərəvəz",2.99),("Xiyar 1 kq","Yaşıl","Meyvə və tərəvəz",2.69),
("Qabyuyan maye 750 ml","Saf","Təmizlik",4.90),("Paltar yuyucu 2 kq","Saf","Təmizlik",12.40),("Kağız dəsmal 2-li","Evra","Ev məhsulları",3.30),("Zibil torbası 20-li","Evra","Ev məhsulları",2.20),
("Şampun 400 ml","İnci","Şəxsi qulluq",6.90),("Sabun 4-lü","İnci","Şəxsi qulluq",3.50),("Uşaq bezi 24-lü","Balaca","Uşaq məhsulları",14.90),("Nəm salfet 72-li","Balaca","Uşaq məhsulları",3.90),
]

def run():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Organisation).where(Organisation.name=="Nova Market")):
            customer=db.scalar(select(User).where(User.email=="customer@demo.az"))
            if customer:customer.full_name="Həsən Nurməmmədov";db.commit()
            print("Demo data already exists");return
        nova=Organisation(name="Nova Market");city=Organisation(name="CityMart");db.add_all([nova,city]);db.flush()
        branches=[Branch(organisation_id=nova.id,name="Nova Market — Nərimanov",address="Təbriz küçəsi 42",distance_km=1.2),Branch(organisation_id=nova.id,name="Nova Market — Yasamal",address="Mətbuat prospekti 18",distance_km=3.4),Branch(organisation_id=nova.id,name="Nova Market — Xətai",address="Xocalı prospekti 15",distance_km=4.8),Branch(organisation_id=city.id,name="CityMart — Gənclik",address="Fətəli xan Xoyski 90",distance_km=2.1)];db.add_all(branches);db.flush()
        users=[User(organisation_id=nova.id,branch_id=branches[0].id,email="customer@demo.az",full_name="Aylin Məmmədova",phone="+994501112233",role=Role.CUSTOMER,password_hash=hash_password(PASSWORD)),User(organisation_id=nova.id,branch_id=branches[0].id,email="branch@demo.az",full_name="Elvin Əliyev",role=Role.BRANCH_ADMIN,password_hash=hash_password(PASSWORD)),User(organisation_id=nova.id,email="head@demo.az",full_name="Leyla Qasımova",role=Role.HEAD_OFFICE_ADMIN,password_hash=hash_password(PASSWORD)),User(organisation_id=nova.id,branch_id=branches[0].id,email="staff@demo.az",full_name="Murad Həsənli",role=Role.STAFF,password_hash=hash_password(PASSWORD)),User(email="platform@martiq.az",full_name="MARTIQ Admin",role=Role.PLATFORM_ADMIN,password_hash=hash_password(PASSWORD)),User(organisation_id=city.id,branch_id=branches[3].id,email="cityadmin@demo.az",full_name="CityMart Admin",role=Role.BRANCH_ADMIN,password_hash=hash_password(PASSWORD))];db.add_all(users);db.flush()
        users[0].full_name="Həsən Nurməmmədov"
        categories=sorted({x[2] for x in CATALOG});db.add_all([ProductCategory(organisation_id=nova.id,name=x) for x in categories])
        products=[]
        for i,(name,brand,category,price) in enumerate(CATALOG,1):products.append(Product(organisation_id=nova.id,name=name,brand=brand,barcode=f"47600000{i:05d}",category=category,price=price,discount_price=round(price*.8,2) if i%4==0 else None))
        db.add_all(products);db.flush()
        for branch in branches[:3]:
            db.add_all([BranchService(organisation_id=nova.id,branch_id=branch.id,name=s) for s in ("Parkinq","Əlçatan giriş","Özünəxidmət kassası")])
            for i,p in enumerate(products):db.add(ProductPrice(organisation_id=nova.id,branch_id=branch.id,product_id=p.id,price=round(p.price+(0.05 if branch==branches[2] else 0),2),previous_price=round(p.price*1.08,2),available=i%11!=0))
        db.add_all([News(organisation_id=nova.id,title_az="Yay iş saatları yeniləndi",title_en="Summer hours updated",summary_az="Nərimanov filialı artıq hər gün saat 23:00-dək açıqdır.",summary_en="The Narimanov branch is now open until 23:00 every day."),News(organisation_id=nova.id,title_az="Yeni təkrar emal nöqtəsi",title_en="New recycling point",summary_az="Şüşə və plastik üçün çeşidləmə nöqtəsi istifadəyə verildi.",summary_en="A sorting point for glass and plastic is now available."),News(organisation_id=nova.id,branch_id=branches[1].id,title_az="Yasamal filialında texniki xidmət",title_en="Maintenance at Yasamal",summary_az="Bazar günü bəzi kassalarda qısa texniki fasilə olacaq.",summary_en="Some checkouts will have a short maintenance window on Sunday.")])
        card=LoyaltyCard(organisation_id=nova.id,user_id=users[0].id,balance=1280,monthly_earned=240,expiring=90);db.add(card);db.flush();db.add_all([LoyaltyTransaction(organisation_id=nova.id,card_id=card.id,amount=120,description="Nərimanov filialında alış"),LoyaltyTransaction(organisation_id=nova.id,card_id=card.id,amount=-50,description="Demo bonus təklifi")])
        campaign=DiscountCampaign(organisation_id=nova.id,title="Həftənin seçilmişləri",description="Seçilmiş gündəlik məhsullarda filial endirimləri",starts_on=date.today()-timedelta(days=2),ends_on=date.today()+timedelta(days=10));db.add(campaign);db.flush();db.add_all([DiscountCampaignProduct(organisation_id=nova.id,campaign_id=campaign.id,product_id=p.id,branch_id=branches[0].id,discount_price=round(p.price*.8,2)) for p in products[:8]])
        db.add_all([OrganisationModule(organisation_id=nova.id,module=x,enabled=True) for x in ("REPORTS","AUDITS","VISION","LOYALTY")]);db.add(Notification(organisation_id=nova.id,user_id=users[0].id,kind="DISCOUNT",title="Yeni endirim",body="Həftənin seçilmiş məhsullarına baxın."));db.add(AuditTask(organisation_id=nova.id,branch_id=branches[0].id,assignee_id=users[3].id,title="Süd məhsullarının tarix auditi",instructions="İki fərqli süd məhsulunun barkodunu və son istifadə tarixini yoxlayın.",required_count=2,due_at=datetime.utcnow()+timedelta(hours=6),priority="HIGH"))
        report=CustomerReport(tracking_number="MQ-DEMO1024",organisation_id=nova.id,branch_id=branches[0].id,customer_id=users[0].id,category="PRICE_MISMATCH",title="Rəfdə qiymət fərqlidir",description="Südün rəf etiketi tətbiqdəki cari qiymətdən fərqlənir.");incident=Incident(organisation_id=nova.id,branch_id=branches[0].id,report=report,source="CUSTOMER",category=report.category,title=report.title,description=report.description);incident.history.append(IncidentStatusHistory(status=IncidentStatus.VERIFICATION_REQUIRED,note="Müştəri siqnalı qəbul edildi; filial təsdiqi gözlənilir.",actor_id=users[0].id));db.add(incident);db.commit();print("Seeded 2 organisations, 4 branches and 24 products")

if __name__=="__main__":run()
