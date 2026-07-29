from datetime import date,timedelta
from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import Base,SessionLocal,engine
from app.models.audit import AuditTask
from app.models.customer import Notification
from app.models.domain import Branch,CustomerReport,Incident,IncidentStatus,IncidentStatusHistory,LoyaltyCard,News,Organisation,Product,Role,User
from app.models.retail import BranchService,DiscountCampaign,DiscountCampaignProduct,LoyaltyRewardOffer,LoyaltyTransaction,OrganisationModule,ProductCategory,ProductPrice
from app.core.time import utc_now

PASSWORD="Demo123!"
CATALOG=[
("Təzə süd 1 L","Səhər","Süd məhsulları",2.79),("Kefir 1 L","Səhər","Süd məhsulları",3.19),("Qatıq 500 q","Bərəkət","Süd məhsulları",2.39),("Kərə yağı 200 q","Yaylaq","Süd məhsulları",5.99),
("Yulaf lopası 500 q","Dən","Ərzaq",4.60),("Düyü 1 kq","Dən","Ərzaq",3.80),("Makaron 500 q","Masa","Ərzaq",1.89),("Zeytun yağı 500 ml","Lalə","Ərzaq",11.90),
("Alma şirəsi 1 L","Bağça","İçkilər",3.40),("Mineral su 1 L","Bulaq","İçkilər",1.20),("Qara çay 100 q","Xəzər","İçkilər",4.25),("Qəhvə 200 q","Səma","İçkilər",9.80),
("Alma 1 kq","Bağça","Meyvə və tərəvəz",2.49),("Banan 1 kq","Tropik","Meyvə və tərəvəz",3.89),("Pomidor 1 kq","Yaşıl","Meyvə və tərəvəz",2.99),("Xiyar 1 kq","Yaşıl","Meyvə və tərəvəz",2.69),
("Qabyuyan maye 750 ml","Saf","Təmizlik",4.90),("Paltar yuyucu 2 kq","Saf","Təmizlik",12.40),("Kağız dəsmal 2-li","Evra","Ev məhsulları",3.30),("Zibil torbası 20-li","Evra","Ev məhsulları",2.20),
("Şampun 400 ml","İnci","Şəxsi qulluq",6.90),("Sabun 4-lü","İnci","Şəxsi qulluq",3.50),("Uşaq bezi 24-lü","Balaca","Uşaq məhsulları",14.90),("Nəm salfet 72-li","Balaca","Uşaq məhsulları",3.90),
]

def product_asset(category:str)->str:
    if "Süd" in category:return "/assets/product-dairy.svg"
    if "İçki" in category:return "/assets/product-beverage.svg"
    if "qulluq" in category or "Təmizlik" in category:return "/assets/product-care.svg"
    return "/assets/product-food.svg"

def enrich_customer_demo(db):
    nova=db.scalar(select(Organisation).where(Organisation.name=="Nova Market"));city=db.scalar(select(Organisation).where(Organisation.name=="CityMart"));customer=db.scalar(select(User).where(User.email=="customer@demo.az"))
    if not nova or not city or not customer:return
    for product in db.scalars(select(Product).where(Product.organisation_id==nova.id)).all():product.image_url=product_asset(product.category)
    news=db.scalars(select(News).where(News.organisation_id==nova.id).order_by(News.published_at)).all()
    for index,item in enumerate(news):item.image_url="/assets/news-hours.svg" if index==0 else "/assets/news-recycling.svg"
    city_branch=db.scalar(select(Branch).where(Branch.organisation_id==city.id))
    city_products=db.scalars(select(Product).where(Product.organisation_id==city.id)).all()
    if not city_products:
        city_catalog=[("City süd 1 L","City Fresh","Süd məhsulları",2.65),("Portağal şirəsi","Sun City","İçkilər",3.25),("Düyü 1 kq","City Choice","Ərzaq",3.55),("Maye sabun","Pure City","Şəxsi qulluq",4.2),("Kağız dəsmal","Home City","Ev məhsulları",2.95),("Mineral su","City Spring","İçkilər",1.1)]
        for index,(name,brand,category,price) in enumerate(city_catalog,1):
            item=Product(organisation_id=city.id,name=name,brand=brand,barcode=f"86900000{index:05d}",category=category,price=price,discount_price=round(price*.82,2) if index%2==0 else None,image_url=product_asset(category));db.add(item);city_products.append(item)
        db.flush();db.add_all([ProductCategory(organisation_id=city.id,name=x) for x in sorted({p.category for p in city_products})])
        for p in city_products:db.add(ProductPrice(organisation_id=city.id,branch_id=city_branch.id,product_id=p.id,price=p.price,previous_price=round(p.price*1.08,2),available=True))
    if not db.scalar(select(News).where(News.organisation_id==city.id)):db.add(News(organisation_id=city.id,branch_id=city_branch.id,title_az="CityMart Gənclik yeniləndi",title_en="CityMart Ganjlik refreshed",summary_az="Yeni self-checkout zonası və təkrar emal nöqtəsi istifadəyə verildi.",summary_en="A new self-checkout area and recycling point are now available.",image_url="/assets/news-recycling.svg"))
    if not db.scalar(select(DiscountCampaign).where(DiscountCampaign.organisation_id==city.id)):
        campaign=DiscountCampaign(organisation_id=city.id,title="City həftəsonu",description="Seçilmiş məhsullarda həftəsonu qiymətləri",starts_on=date.today()-timedelta(days=1),ends_on=date.today()+timedelta(days=12));db.add(campaign);db.flush();db.add_all([DiscountCampaignProduct(organisation_id=city.id,campaign_id=campaign.id,product_id=p.id,branch_id=city_branch.id,discount_price=round(p.price*.82,2)) for p in city_products[:4]])
    if not db.scalar(select(LoyaltyCard).where(LoyaltyCard.user_id==customer.id,LoyaltyCard.organisation_id==city.id)):db.add(LoyaltyCard(organisation_id=city.id,user_id=customer.id,label="City Bonus",card_number="8800123400000001",balance=680,monthly_earned=95,expiring=35,expiring_on=utc_now()+timedelta(days=40)))
    for org,prefix in ((nova,"Nova"),(city,"City")):
        if not db.scalar(select(LoyaltyRewardOffer).where(LoyaltyRewardOffer.organisation_id==org.id)):
            db.add_all([LoyaltyRewardOffer(organisation_id=org.id,title_az=f"{prefix} qəhvə hədiyyəsi",title_en=f"{prefix} coffee reward",description_az="Bonuslarınızı isti içki kuponuna dəyişin.",description_en="Exchange your points for a hot drink voucher.",points_cost=250,image_url="/assets/reward.svg",valid_until=date.today()+timedelta(days=60)),LoyaltyRewardOffer(organisation_id=org.id,title_az="Alış-veriş kuponu",title_en="Shopping voucher",description_az="Növbəti alışda istifadə üçün 5 ₼ kupon.",description_en="A 5 AZN voucher for your next purchase.",points_cost=500,image_url="/assets/reward.svg",valid_until=date.today()+timedelta(days=90))])

def run():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(Organisation).where(Organisation.name=="Nova Market")):
            customer=db.scalar(select(User).where(User.email=="customer@demo.az"))
            if customer:
                customer.full_name="Həsən Nurməmmədov"
                cards=db.scalars(select(LoyaltyCard).where(LoyaltyCard.user_id==customer.id)).all()
                for index,card in enumerate(cards,1):
                    card.label="Nova Bonus" if index==1 else "Ailə kartı";card.card_number=f"990012340000{index:04d}";card.expiring_on=utc_now()+timedelta(days=30+index)
                if len(cards)<2:
                    extra=LoyaltyCard(organisation_id=customer.organisation_id,user_id=customer.id,label="Ailə kartı",card_number="9900123400000002",balance=460,monthly_earned=75,expiring=20,expiring_on=utc_now()+timedelta(days=45));db.add(extra);db.flush();db.add(LoyaltyTransaction(organisation_id=customer.organisation_id,card_id=extra.id,amount=75,description="Ailə kartı üzrə alış bonusu"))
                enrich_customer_demo(db);db.commit()
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
        card=LoyaltyCard(organisation_id=nova.id,user_id=users[0].id,label="Nova Bonus",card_number="9900123400000001",balance=1280,monthly_earned=240,expiring=90,expiring_on=utc_now()+timedelta(days=31));db.add(card);db.flush();db.add_all([LoyaltyTransaction(organisation_id=nova.id,card_id=card.id,amount=120,description="Nərimanov filialında alış"),LoyaltyTransaction(organisation_id=nova.id,card_id=card.id,amount=-50,description="Demo bonus təklifi")]);family=LoyaltyCard(organisation_id=nova.id,user_id=users[0].id,label="Ailə kartı",card_number="9900123400000002",balance=460,monthly_earned=75,expiring=20,expiring_on=utc_now()+timedelta(days=45));db.add(family);db.flush();db.add(LoyaltyTransaction(organisation_id=nova.id,card_id=family.id,amount=75,description="Ailə kartı üzrə alış bonusu"))
        campaign=DiscountCampaign(organisation_id=nova.id,title="Həftənin seçilmişləri",description="Seçilmiş gündəlik məhsullarda filial endirimləri",starts_on=date.today()-timedelta(days=2),ends_on=date.today()+timedelta(days=10));db.add(campaign);db.flush();db.add_all([DiscountCampaignProduct(organisation_id=nova.id,campaign_id=campaign.id,product_id=p.id,branch_id=branches[0].id,discount_price=round(p.price*.8,2)) for p in products[:8]])
        db.add_all([OrganisationModule(organisation_id=nova.id,module=x,enabled=True) for x in ("REPORTS","AUDITS","VISION","LOYALTY")]);db.add(Notification(organisation_id=nova.id,user_id=users[0].id,kind="DISCOUNT",title="Yeni endirim",body="Həftənin seçilmiş məhsullarına baxın."));db.add(AuditTask(organisation_id=nova.id,branch_id=branches[0].id,assignee_id=users[3].id,title="Süd məhsullarının tarix auditi",instructions="İki fərqli süd məhsulunun barkodunu və son istifadə tarixini yoxlayın.",required_count=2,due_at=utc_now()+timedelta(hours=6),priority="HIGH"))
        report=CustomerReport(tracking_number="MQ-DEMO1024",organisation_id=nova.id,branch_id=branches[0].id,customer_id=users[0].id,category="PRICE_MISMATCH",title="Rəfdə qiymət fərqlidir",description="Südün rəf etiketi tətbiqdəki cari qiymətdən fərqlənir.");incident=Incident(organisation_id=nova.id,branch_id=branches[0].id,report=report,source="CUSTOMER",category=report.category,title=report.title,description=report.description);incident.history.append(IncidentStatusHistory(status=IncidentStatus.VERIFICATION_REQUIRED,note="Müştəri siqnalı qəbul edildi; filial təsdiqi gözlənilir.",actor_id=users[0].id));db.add(incident);db.flush();enrich_customer_demo(db);db.commit();print("Seeded 2 organisations, 4 branches and 30 products")

if __name__=="__main__":run()
