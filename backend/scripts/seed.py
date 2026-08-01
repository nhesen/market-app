from datetime import date,datetime,timedelta
from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import Base,SessionLocal,engine
from app.models.audit import AuditTask
from app.models.customer import Notification
from app.models.domain import Branch,CustomerMarketMembership,CustomerReport,Incident,IncidentSource,IncidentStatus,IncidentStatusHistory,LoyaltyCard,News,Organisation,Product,Role,User
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

PRODUCT_ASSETS={
    "təzə süd":"https://imageproxy.wolt.com/assets/69983ffe3eb3341f036e615d",
    "kefir":"https://imageproxy.wolt.com/assets/688b9ee3a3eb62eeb95c4f96",
    "qatıq":"https://imageproxy.wolt.com/wolt-prod-production-wm-assortment-images/categories/3d48852b-d8b4-4e49-b436-b5625aff6e3e.png",
    "kərə yağı":"https://imageproxy.wolt.com/assets/688b9cffb2b18bf1da5377ee",
    "yulaf lopası":"https://imageproxy.wolt.com/assets/6888bc6023fa16f725a98263",
    "düyü":"https://imageproxy.wolt.com/assets/67bdcc1c7d14106f0111657e",
    "makaron":"https://imageproxy.wolt.com/assets/67d93f1e9f3f5515b9d9e15e",
    "zeytun yağı":"https://imageproxy.wolt.com/assets/67f8e1ca5e06813d12110b46",
    "alma şirəsi":"https://imageproxy.wolt.com/assets/688b9bdab2b18bf1da536fb4",
    "mineral su":"https://imageproxy.wolt.com/assets/688b9b0223fa16f725af9537",
    "qara çay":"https://imageproxy.wolt.com/assets/688b98eca3eb62eeb95c1f59",
    "qəhvə":"https://imageproxy.wolt.com/assets/6888c4e023fa16f725a9feb9",
    "alma 1":"https://imageproxy.wolt.com/assets/688b9c9923fa16f725afb09b",
    "banan":"https://imageproxy.wolt.com/assets/688b98e9a3eb62eeb95c1ed3",
    "pomidor":"https://imageproxy.wolt.com/assets/6888b9f21f0cac713af61952",
    "xiyar":"https://imageproxy.wolt.com/assets/6888bb6523fa16f725a9720a",
    "qabyuyan maye":"https://imageproxy.wolt.com/assets/688b9bdeb2b18bf1da537047",
    "paltar yuyucu":"https://imageproxy.wolt.com/assets/688b98e0a3eb62eeb95c1cfd",
    "kağız dəsmal":"https://imageproxy.wolt.com/assets/6888be27a3eb62eeb95622f8",
    "zibil torbası":"https://imageproxy.wolt.com/assets/69d2c3258e6190d55ea88d18",
    "şampun":"https://imageproxy.wolt.com/assets/68f0be7f37e9a5025614f465",
    "sabun":"https://imageproxy.wolt.com/assets/688b9dcb23fa16f725afc247",
    "uşaq bezi":"https://imageproxy.wolt.com/assets/6888bc2e1f0cac713af64b4c",
    "nəm salfet":"https://imageproxy.wolt.com/assets/688b9e69b2b18bf1da5388df",
}

def product_asset(name:str,category:str)->str:
    normalized=name.casefold()
    for product_name,image_url in PRODUCT_ASSETS.items():
        if product_name in normalized:return image_url
    return "/assets/retail-products-v2.png"

NEWS_INVENTORY={
"Nova Market":[
("BRAVO İsmayıl Hidayətzadə küçəsində yeni mağaza açdı","BRAVO opens a new store on Ismayil Hidayatzade Street","Yeni mağaza 7/24 işləyir və açılışa özəl 500 məhsula 50%-dək endirim təqdim edir.","The new store operates 24/7 and offers opening discounts of up to 50% on 500 products.","BRAVO-nun İsmayıl Hidayətzadə küçəsi 130 ünvanında yerləşən yeni mağazası fəaliyyətə başlayıb. Rəsmi məlumata görə, mağaza müasir dizayn, geniş məhsul seçimi və gecə-gündüz xidmət təqdim edir. Mənbə: https://bravosupermarket.az/news/exibition/bravo-supermarketl-r-s-b-k-si-i-smayil-hiday-tzad-kuc-sind-yeni-magazasini-acdi/","BRAVO's new store at 130 Ismayil Hidayatzade Street is now open. According to the official announcement, it offers a modern shopping environment, a broad product range and 24/7 service. Source: https://bravosupermarket.az/news/exibition/bravo-supermarketl-r-s-b-k-si-i-smayil-hiday-tzad-kuc-sind-yeni-magazasini-acdi/",None,"OPENING","https://bravosupermarket.az/site/assets/files/4117/bravo_market_nerimanov-2.png","2026-07-24T10:00:00+00:00"),
("BRAVO müştərilərlə növbəti “Qonağımız ol” görüşünü keçirdi","BRAVO holds another customer meeting","Müştərilər məhsullar, xidmət keyfiyyəti və alış təcrübəsi ilə bağlı fikirlərini rəhbərliklə bölüşüblər.","Customers shared feedback on products, service quality and their shopping experience with management.","BRAVO-nun baş ofisində keçirilən görüşdə müştərilərin təklifləri dinlənilib və yeni nəsil BRAVO BREND məhsulları təqdim olunub. Şirkət görüşləri mütəmadi davam etdirməyi planlaşdırır. Mənbə: https://bravosupermarket.az/news/layiheler/bravo-da-novbeti-qonagimiz-ol/","At a meeting in BRAVO's head office, customers shared suggestions and were introduced to new-generation BRAVO BRAND products. The company plans to continue these meetings regularly. Source: https://bravosupermarket.az/news/layiheler/bravo-da-novbeti-qonagimiz-ol/",None,"CUSTOMER_EXPERIENCE","https://bravosupermarket.az/site/assets/files/4027/qonaqol-1.jpg","2026-07-18T10:00:00+00:00"),
("AL Market-də “Siyəzən Dadlı Toyuq Al, Qazan” lotereyası keçirildi","AL Market runs the Siyazan chicken prize lottery","Alış-veriş qəbzindəki QR-kodla qeydiyyatdan keçən müştərilər üç tirajda hədiyyələr qazanmaq imkanı əldə ediblər.","Customers registering through the receipt QR code could enter three prize draws.","AL Market-in 7 aprel–7 may 2026 tarixlərini əhatə edən rəsmi lotereyasında hər 10 AZN-lik uyğun alışa bir iştirak şansı verilib. Kampaniyanın final tirajı mayda başa çatıb. Mənbə: https://almarket.az/az/almedia/al-marketd-siyzn-dadli-toyuq-al-qazan-lotereyasi-basladi","AL Market's official lottery ran from 7 April to 7 May 2026, granting one entry for each eligible AZN 10 purchase. The final draw concluded in May. Source: https://almarket.az/az/almedia/al-marketd-siyzn-dadli-toyuq-al-qazan-lotereyasi-basladi",None,"CAMPAIGN","https://almarket.az/files/medias/26803aa207.webp","2026-04-07T10:00:00+00:00"),
("Nərimanov filialında self-checkout zonası genişləndirildi","Self-checkout area expanded at Narimanov branch","Pik saatlarda yeni terminallar istifadəyə verilib.","New terminals are available during peak hours.","Nərimanov filialında self-checkout zonası yenilənib. İlk günlərdə əməkdaşlarımız terminallardan istifadə üçün kömək edəcək.","The self-checkout area at Narimanov has been upgraded. Staff will help customers use the new terminals.",0,"NEW_SERVICE","/assets/retail-news-v2.png"),
("Yay mövsümü üçün iş saatlarımız yeniləndi","Our summer opening hours have been updated","Seçilmiş filiallar saat 23:00-dək açıqdır.","Selected branches are open until 23:00.","Nərimanov, Yasamal və Xətai filiallarında alış-verişi saat 23:00-dək edə bilərsiniz. Bayram günləri üçün ayrıca bildiriş göndəriləcək.","Narimanov, Yasamal and Khatai branches remain open until 23:00. Separate notices will cover holiday schedules.",None,"HOLIDAY_HOURS","/assets/news-hours.svg"),
("Plastik və şüşə üçün yeni təkrar emal nöqtəsi","New recycling point for plastic and glass","Təmiz qablaşdırmaları çeşidləmə qutularına yerləşdirə bilərsiniz.","Clean packaging can now be placed in sorting bins.","Yeni nöqtə plastik və şüşə qablaşdırmaların ayrıca toplanmasına kömək edir. Qablaşdırmanı boş və təmiz gətirməyiniz xahiş olunur.","The new point collects plastic and glass separately. Please bring packaging empty and clean.",0,"SUSTAINABILITY","/assets/news-recycling.svg"),
("Təzə meyvə və tərəvəz bölməsi yeniləndi","Fresh produce section refreshed","Mövsümi məhsullar daha aydın məlumatla təqdim olunur.","Seasonal produce now has clearer information.","Yasamal filialındakı bölmənin düzülüşü yenilənib. Qiymət, mənşə və çəki məlumatları rəflərdə daha rahat görünür.","The Yasamal produce layout has been refreshed. Price, origin and weight details are easier to read.",1,"BRANCH_UPDATE","/assets/retail-branch-v2.png"),
("Bu həftənin seçilmiş məhsulları","This week's selected products","Gündəlik məhsullar üzrə kampaniyaları tətbiqdən yoxlayın.","Check this week's campaigns for everyday essentials.","İştirak edən məhsullar və filial qiymətləri Endirimlər bölməsində göstərilir. Təkliflər stok mövcudluğuna görə dəyişə bilər.","Participating products and branch prices are listed in Discounts. Offers may vary with stock.",None,"CAMPAIGN","/assets/retail-campaign-v2.png"),
("Yasamal filialında qısa texniki xidmət","Short maintenance window at Yasamal branch","Bazar günü bəzi kassalarda qısa fasilə olacaq.","Some checkouts will have a short Sunday maintenance window.","Saat 09:00–10:00 arasında iki terminalda planlı baxış keçiriləcək. Digər kassalar normal işləyəcək.","Two terminals will undergo maintenance between 09:00 and 10:00. Other checkouts will operate normally.",1,"MAINTENANCE","/assets/news-hours.svg"),
("Çatdırılma sifarişləri üçün yeni təhvil nöqtəsi","New pickup point for delivery orders","Hazır sifarişləri ayrılmış masadan götürmək mümkündür.","Completed orders can be collected from a dedicated point.","Sifariş nömrənizi göstərərək paketinizi sürətli ala bilərsiniz. Böyük sifarişlər üçün əməkdaş dəstəyi mövcuddur.","Show your order number for quick collection. Staff support is available for larger orders.",2,"NEW_SERVICE","/assets/retail-news-v2.png"),
("Əlçatan giriş sahəsi təkmilləşdirildi","Accessibility entrance area improved","Xətai filialının girişində hərəkət sahəsi genişləndirilib.","The entrance area at Khatai has been widened.","Pandus ətrafındakı keçid genişləndirilib və nişanlar yenilənib. Kömək üçün xidmət masasına müraciət edə bilərsiniz.","The passage around the ramp has been widened and signs updated. Ask the service desk if you need help.",2,"BRANCH_UPDATE","/assets/retail-branch-v2.png"),
("Bonus kart sahibləri üçün yeni mükafatlar","New rewards for loyalty card members","Bonusları demo kuponlara dəyişmək mümkündür.","Points can now be exchanged for demo vouchers.","Kartlar bölməsində aktiv mükafatları görə bilərsiniz. Bu, simulyasiya edilmiş demo inteqrasiyadır.","Open Cards to see active rewards. This is a simulated demo integration.",None,"ANNOUNCEMENT","/assets/reward.svg"),
("Bayram günlərində filialların iş qrafiki","Branch opening hours during the holiday period","Filial detallarında yenilənmiş saatları yoxlayın.","Check Branch Details for updated hours.","Bayram dövründə saatlar filiallara görə fərqlənə bilər. Səfərdən əvvəl seçilmiş filialı yoxlayın.","Hours may differ by branch during holidays. Check your selected branch before visiting.",None,"ANNOUNCEMENT","/assets/news-hours.svg")],
"CityMart":[
("Gənclik filialında xidmət masası yeniləndi","Customer service desk refreshed at Ganjlik","Müraciətlər üçün daha aydın növbə sistemi qurulub.","A clearer queue system is available for customer requests.","Müraciət növləri ayrıca işarələnib və doğru əməkdaşa daha sürətli yönləndirilir.","Request types are now clearly marked so customers reach the right colleague faster.",0,"BRANCH_UPDATE","/assets/retail-branch-v2.png"),
("Səhər alış-verişi üçün təzə çörək saatları","Fresh bakery times for morning shopping","İlk isti çörək partiyası saat 08:30-da rəfə çıxır.","The first fresh bread batch reaches shelves at 08:30.","Günorta ikinci bişirmə də planlaşdırılır. Çeşid günə görə dəyişə bilər.","A second bake is planned around midday. The selection may vary by day.",None,"NEWS","/assets/product-food.svg"),
("Kağız qəbzə alternativ seçimi","An alternative to paper receipts","Demo elektron qəbz seçimi haqqında kassada məlumat alın.","Ask at checkout about the demo electronic receipt option.","Elektron qəbz sınağı kağız istifadəsini azaltmaq məqsədi daşıyır və tətbiq demosunda simulyasiya olunur.","The electronic receipt trial aims to reduce paper use and is simulated in this app demo.",0,"SUSTAINABILITY","/assets/news-recycling.svg"),
("Həftəsonu ailə səbəti təklifləri","Weekend family basket offers","Seçilmiş ərzaq və ev məhsullarında yeni qiymətlər aktivdir.","Weekend prices are active for selected essentials.","Tam siyahını Endirimlər bölməsində görə bilərsiniz. Qiymətlər Gənclik filialındakı stoka əsaslanır.","See the full list in Discounts. Prices reflect stock at the Ganjlik branch.",0,"CAMPAIGN","/assets/retail-campaign-v2.png"),
("Soyuducu bölməsində planlı yoxlama","Planned inspection in the chilled section","Axşam bir koridorda qısa xidmət işi aparılacaq.","A short evening service check will take place in one aisle.","Saat 21:00-dan sonra süd bölməsinin sensorları yoxlanacaq. Məhsullar digər rəflərdə qalacaq.","After 21:00, dairy temperature sensors will be checked. Products remain available nearby.",0,"MAINTENANCE","/assets/retail-camera-v2.png"),
("City Bonus üçün yeni demo kuponlar","New demo vouchers for City Bonus","Mükafatları Kartlar bölməsində görün.","See current rewards in Cards.","Təkliflər yalnız Baxish demo ssenarisidir və real loyallıq provayderi ilə əlaqəni ifadə etmir.","Offers are part of the Baxish demo and do not imply a real loyalty-provider connection.",None,"ANNOUNCEMENT","/assets/reward.svg")]
}

def seed_rich_news(db,organisation,branches):
    inventory=NEWS_INVENTORY[organisation.name]
    if organisation.name=="CityMart":inventory=NEWS_INVENTORY["Nova Market"][:3]+inventory
    for index,item in enumerate(inventory):
        existing=db.scalar(select(News).where(News.organisation_id==organisation.id,News.title_en==item[1]))
        branch=branches[item[6]] if item[6] is not None and item[6]<len(branches) else None
        published_at=datetime.fromisoformat(item[9]) if len(item)>9 else datetime.fromisoformat("2026-01-01T10:00:00+00:00")-timedelta(days=index)
        values={"branch_id":branch.id if branch else None,"title_az":item[0],"title_en":item[1],"summary_az":item[2],"summary_en":item[3],"body_az":item[4],"body_en":item[5],"content_type":item[7],"status":"PUBLISHED","image_url":item[8],"published_at":published_at}
        if existing:
            for key,value in values.items():setattr(existing,key,value)
        else:db.add(News(organisation_id=organisation.id,**values))

def remove_retired_demo_news(db):
    retired_titles={
        "Summer hours updated",
        "Our summer opening hours have been updated",
        "New recycling point",
        "New recycling point for plastic and glass",
    }
    for item in db.scalars(select(News).where(News.title_en.in_(retired_titles))).all():
        db.delete(item)

def enrich_customer_demo(db):
    nova=db.scalar(select(Organisation).where(Organisation.name=="Nova Market"));city=db.scalar(select(Organisation).where(Organisation.name=="CityMart"));customer=db.scalar(select(User).where(User.email=="customer@demo.az"))
    if not nova or not city or not customer:return
    if not customer.selected_organisation_id:customer.selected_organisation_id=nova.id
    for org in (nova,city):
        if not db.scalar(select(CustomerMarketMembership).where(CustomerMarketMembership.customer_id==customer.id,CustomerMarketMembership.organisation_id==org.id)):db.add(CustomerMarketMembership(customer_id=customer.id,organisation_id=org.id))
    for product in db.scalars(select(Product)).all():
        product.image_url=product_asset(product.name,product.category)
        if not product.package_size:
            parts=product.name.rsplit(" ",2);tail=" ".join(parts[-2:]);product.package_size=tail if any(char.isdigit() for char in tail) else None
    nova_branches=db.scalars(select(Branch).where(Branch.organisation_id==nova.id).order_by(Branch.name)).all()
    city_branches=db.scalars(select(Branch).where(Branch.organisation_id==city.id).order_by(Branch.name)).all()
    seed_rich_news(db,nova,nova_branches);seed_rich_news(db,city,city_branches)
    city_branch=city_branches[0]
    city_products=db.scalars(select(Product).where(Product.organisation_id==city.id)).all()
    if not city_products:
        city_catalog=[("City süd 1 L","City Fresh","Süd məhsulları",2.65),("Portağal şirəsi","Sun City","İçkilər",3.25),("Düyü 1 kq","City Choice","Ərzaq",3.55),("Maye sabun","Pure City","Şəxsi qulluq",4.2),("Kağız dəsmal","Home City","Ev məhsulları",2.95),("Mineral su","City Spring","İçkilər",1.1)]
        for index,(name,brand,category,price) in enumerate(city_catalog,1):
            item=Product(organisation_id=city.id,name=name,brand=brand,barcode=f"86900000{index:05d}",category=category,price=price,discount_price=round(price*.82,2) if index%2==0 else None,image_url=product_asset(name,category));db.add(item);city_products.append(item)
        db.flush();db.add_all([ProductCategory(organisation_id=city.id,name=x) for x in sorted({p.category for p in city_products})])
        for p in city_products:db.add(ProductPrice(organisation_id=city.id,branch_id=city_branch.id,product_id=p.id,price=p.price,previous_price=round(p.price*1.08,2),available=True))
    if not db.scalar(select(News).where(News.organisation_id==city.id)):db.add(News(organisation_id=city.id,branch_id=city_branch.id,title_az="CityMart Gənclik yeniləndi",title_en="CityMart Ganjlik refreshed",summary_az="Yeni self-checkout zonası və təkrar emal nöqtəsi istifadəyə verildi.",summary_en="A new self-checkout area and recycling point are now available.",image_url="/assets/retail-news-v2.png"))
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
            platform=db.scalar(select(User).where(User.email=="platform@baxish.az"))
            if platform:platform.email="platform@baxish.az";platform.full_name="Baxish Admin"
            customer=db.scalar(select(User).where(User.email=="customer@demo.az"))
            if customer:
                customer.full_name="Həsən Nurməmmədov"
                cards=db.scalars(select(LoyaltyCard).where(LoyaltyCard.user_id==customer.id)).all()
                for index,card in enumerate(cards,1):
                    card.label="Nova Bonus" if index==1 else "Ailə kartı";card.card_number=f"990012340000{index:04d}";card.expiring_on=utc_now()+timedelta(days=30+index)
                if len(cards)<2:
                    extra=LoyaltyCard(organisation_id=customer.organisation_id,user_id=customer.id,label="Ailə kartı",card_number="9900123400000002",balance=460,monthly_earned=75,expiring=20,expiring_on=utc_now()+timedelta(days=45));db.add(extra);db.flush();db.add(LoyaltyTransaction(organisation_id=customer.organisation_id,card_id=extra.id,amount=75,description="Ailə kartı üzrə alış bonusu"))
                enrich_customer_demo(db);remove_retired_demo_news(db);db.commit()
            print("Demo data already exists");return
        nova=Organisation(name="Nova Market");city=Organisation(name="CityMart");db.add_all([nova,city]);db.flush()
        branches=[Branch(organisation_id=nova.id,name="Nova Market — Nərimanov",address="Təbriz küçəsi 42",distance_km=1.2),Branch(organisation_id=nova.id,name="Nova Market — Yasamal",address="Mətbuat prospekti 18",distance_km=3.4),Branch(organisation_id=nova.id,name="Nova Market — Xətai",address="Xocalı prospekti 15",distance_km=4.8),Branch(organisation_id=city.id,name="CityMart — Gənclik",address="Fətəli xan Xoyski 90",distance_km=2.1)];db.add_all(branches);db.flush()
        users=[User(organisation_id=nova.id,selected_organisation_id=nova.id,branch_id=branches[0].id,email="customer@demo.az",full_name="Aylin Məmmədova",phone="+994501112233",role=Role.CUSTOMER,password_hash=hash_password(PASSWORD)),User(organisation_id=nova.id,branch_id=branches[0].id,email="branch@demo.az",full_name="Elvin Əliyev",role=Role.BRANCH_ADMIN,password_hash=hash_password(PASSWORD)),User(organisation_id=nova.id,email="head@demo.az",full_name="Leyla Qasımova",role=Role.HEAD_OFFICE_ADMIN,password_hash=hash_password(PASSWORD)),User(organisation_id=nova.id,branch_id=branches[0].id,email="staff@demo.az",full_name="Murad Həsənli",role=Role.STAFF,password_hash=hash_password(PASSWORD)),User(email="platform@baxish.az",full_name="Baxish Admin",role=Role.PLATFORM_ADMIN,password_hash=hash_password(PASSWORD)),User(organisation_id=city.id,branch_id=branches[3].id,email="cityadmin@demo.az",full_name="CityMart Admin",role=Role.BRANCH_ADMIN,password_hash=hash_password(PASSWORD))];db.add_all(users);db.flush()
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
        report=CustomerReport(tracking_number="MQ-DEMO1024",organisation_id=nova.id,branch_id=branches[0].id,customer_id=users[0].id,category="PRICE_MISMATCH",title="Rəfdə qiymət fərqlidir",description="Südün rəf etiketi tətbiqdəki cari qiymətdən fərqlənir.",status=IncidentStatus.NEW);incident=Incident(organisation_id=nova.id,branch_id=branches[0].id,report=report,source=IncidentSource.CUSTOMER_REPORT,category=report.category,title=report.title,description=report.description,status=IncidentStatus.NEW);incident.history.append(IncidentStatusHistory(status=IncidentStatus.NEW,note="Customer report received.",customer_note="Müraciətiniz qəbul edildi.",actor_id=users[0].id,actor_type="MANUAL"));db.add(incident);db.flush();enrich_customer_demo(db);remove_retired_demo_news(db);db.commit();print("Seeded 2 organisations, 4 branches and 30 products")

if __name__=="__main__":run()
