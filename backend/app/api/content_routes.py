from datetime import date
from fastapi import APIRouter,Depends,File,HTTPException,UploadFile
from pydantic import BaseModel,Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import current_user,roles
from app.db.session import get_db
from app.models.domain import Branch,News,Product,Role,User
from app.models.retail import AuditLog,BranchService,DiscountCampaign,DiscountCampaignProduct,FileAsset,LoyaltyRewardOffer,LoyaltyTransaction,ProductCategory,ProductPrice
from app.services.storage import storage

router=APIRouter(prefix="/api/v1")
ADMINS=(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)
CONTENT_ADMINS=(Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)
class ProductIn(BaseModel): name:str=Field(min_length=2,max_length=180);brand:str=Field(min_length=2,max_length=120);barcode:str=Field(min_length=6,max_length=32);category:str;price:float=Field(gt=0);discount_price:float|None=None;image_url:str="/assets/retail-products-v2.png"
class NewsIn(BaseModel): title_az:str;title_en:str;summary_az:str;summary_en:str;branch_id:str|None=None;image_url:str="/assets/retail-news-v2.png"
class PriceIn(BaseModel): branch_id:str;product_id:str;price:float=Field(gt=0);previous_price:float|None=None;available:bool=True
class CampaignIn(BaseModel): title:str;description:str;starts_on:date;ends_on:date;published:bool=True
class CampaignProductIn(BaseModel): product_id:str;branch_id:str;discount_price:float=Field(gt=0)
class CategoryIn(BaseModel): name:str=Field(min_length=2,max_length=100)

def org_filter(user:User,model): return True if user.role==Role.PLATFORM_ADMIN else model.organisation_id==user.organisation_id
def log(db:Session,user:User,action:str,kind:str,entity_id:str):db.add(AuditLog(organisation_id=user.organisation_id,actor_id=user.id,action=action,entity_type=kind,entity_id=entity_id))

@router.post("/uploads",status_code=201)
async def upload(file:UploadFile=File(...),user:User=Depends(current_user),db:Session=Depends(get_db)):
    key,size,mime=await storage.save(file);item=FileAsset(organisation_id=user.organisation_id,owner_id=user.id,storage_key=key,original_name=file.filename or "upload",mime_type=mime,size=size);db.add(item);db.commit();db.refresh(item);return {"id":item.id,"name":item.original_name,"mime_type":mime,"size":size,"url":f"/uploads/{key}"}

@router.get("/loyalty/cards")
def cards(user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    from app.models.domain import LoyaltyCard,Organisation
    organisation=db.get(Organisation,user.organisation_id)
    cards=db.scalars(select(LoyaltyCard).where(LoyaltyCard.user_id==user.id,LoyaltyCard.organisation_id==user.organisation_id)).all()
    return [{"id":x.id,"organisation_id":x.organisation_id,"market_name":organisation.name if organisation else "","label":x.label,"card_number":x.card_number,"balance":x.balance,"monthly_earned":x.monthly_earned,"expiring":x.expiring,"expiring_on":x.expiring_on} for x in cards]
@router.get("/loyalty/cards/{card_id}/transactions")
def transactions(card_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    from app.models.domain import LoyaltyCard
    if not db.scalar(select(LoyaltyCard).where(LoyaltyCard.id==card_id,LoyaltyCard.user_id==user.id)):raise HTTPException(404,"Card not found")
    return db.scalars(select(LoyaltyTransaction).where(LoyaltyTransaction.card_id==card_id).order_by(LoyaltyTransaction.created_at.desc())).all()

@router.get("/loyalty/offers")
def loyalty_offers(user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    return db.scalars(select(LoyaltyRewardOffer).where(LoyaltyRewardOffer.organisation_id==user.organisation_id,LoyaltyRewardOffer.active==True).order_by(LoyaltyRewardOffer.points_cost)).all()

@router.get("/loyalty/offers/{offer_id}")
def loyalty_offer(offer_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    item=db.scalar(select(LoyaltyRewardOffer).where(LoyaltyRewardOffer.id==offer_id,LoyaltyRewardOffer.organisation_id==user.organisation_id,LoyaltyRewardOffer.active==True))
    if not item:raise HTTPException(404,"Reward offer not found")
    return item

@router.get("/discounts")
def discounts(category:str|None=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    campaigns=db.scalars(select(DiscountCampaign).where(DiscountCampaign.organisation_id==user.organisation_id,DiscountCampaign.published==True)).all();out=[]
    for c in campaigns:
        stmt=select(DiscountCampaignProduct,Product,Branch).join(Product,Product.id==DiscountCampaignProduct.product_id).join(Branch,Branch.id==DiscountCampaignProduct.branch_id).where(DiscountCampaignProduct.campaign_id==c.id)
        if category:stmt=stmt.where(Product.category==category)
        items=db.execute(stmt).all()
        if category and not items:continue
        branch_map={branch.id:branch.name for _,_,branch in items};out.append({"id":c.id,"title":c.title,"description":c.description,"image_url":"/assets/retail-campaign-v2.png","starts_on":c.starts_on,"ends_on":c.ends_on,"products":[{"id":p.id,"name":p.name,"brand":p.brand,"category":p.category,"image_url":p.image_url,"original_price":p.price,"discount_price":link.discount_price,"branch_id":link.branch_id,"branch_name":branch.name} for link,p,branch in items],"branches":[{"id":key,"name":value} for key,value in branch_map.items()]})
    return out

@router.get("/discounts/{campaign_id}")
def discount_detail(campaign_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    campaigns=discounts(None,user,db)
    item=next((campaign for campaign in campaigns if campaign["id"]==campaign_id),None)
    if not item:raise HTTPException(404,"Campaign not found")
    return item

@router.get("/admin/products")
def admin_products(user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    stmt=select(Product);stmt=stmt if user.role==Role.PLATFORM_ADMIN else stmt.where(Product.organisation_id==user.organisation_id);return db.scalars(stmt.order_by(Product.name)).all()
@router.post("/admin/products",status_code=201)
def create_product(data:ProductIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    if not user.organisation_id:raise HTTPException(422,"Select tenant context")
    item=Product(organisation_id=user.organisation_id,**data.model_dump());db.add(item);db.flush();log(db,user,"CREATE","Product",item.id);db.commit();db.refresh(item);return item
@router.patch("/admin/products/{item_id}")
def update_product(item_id:str,data:ProductIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(Product,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"Product not found")
    for k,v in data.model_dump().items():setattr(item,k,v)
    log(db,user,"UPDATE","Product",item.id);db.commit();db.refresh(item);return item
@router.delete("/admin/products/{item_id}",status_code=204)
def delete_product(item_id:str,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(Product,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"Product not found")
    log(db,user,"DELETE","Product",item.id);db.delete(item);db.commit()

@router.get("/admin/news")
def admin_news(user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    stmt=select(News);stmt=stmt if user.role==Role.PLATFORM_ADMIN else stmt.where(News.organisation_id==user.organisation_id);return db.scalars(stmt.order_by(News.published_at.desc())).all()
@router.post("/admin/news",status_code=201)
def create_news(data:NewsIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    if data.branch_id and not db.scalar(select(Branch).where(Branch.id==data.branch_id,Branch.organisation_id==user.organisation_id)):raise HTTPException(404,"Branch not found in your organisation")
    item=News(organisation_id=user.organisation_id,**data.model_dump());db.add(item);db.flush();log(db,user,"CREATE","News",item.id);db.commit();db.refresh(item);return item
@router.patch("/admin/news/{item_id}")
def update_news(item_id:str,data:NewsIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(News,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"News not found")
    for k,v in data.model_dump().items():setattr(item,k,v)
    log(db,user,"UPDATE","News",item.id);db.commit();db.refresh(item);return item
@router.delete("/admin/news/{item_id}",status_code=204)
def delete_news(item_id:str,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(News,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"News not found")
    log(db,user,"DELETE","News",item.id);db.delete(item);db.commit()

@router.post("/admin/prices",status_code=201)
def set_price(data:PriceIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    branch=db.scalar(select(Branch).where(Branch.id==data.branch_id,Branch.organisation_id==user.organisation_id));product=db.scalar(select(Product).where(Product.id==data.product_id,Product.organisation_id==user.organisation_id))
    if not branch or not product:raise HTTPException(404,"Branch or product not found")
    item=db.scalar(select(ProductPrice).where(ProductPrice.branch_id==branch.id,ProductPrice.product_id==product.id))
    if item:
        for k,v in data.model_dump().items():setattr(item,k,v)
    else:item=ProductPrice(organisation_id=user.organisation_id,**data.model_dump());db.add(item)
    db.commit();db.refresh(item);return item

@router.get("/admin/prices")
def admin_prices(user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    stmt=select(ProductPrice);stmt=stmt if user.role==Role.PLATFORM_ADMIN else stmt.where(ProductPrice.organisation_id==user.organisation_id);return db.scalars(stmt.order_by(ProductPrice.updated_at.desc())).all()

@router.delete("/admin/prices/{item_id}",status_code=204)
def delete_price(item_id:str,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(ProductPrice,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"Price not found")
    db.delete(item);db.commit()

@router.get("/admin/categories")
def admin_categories(user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    stmt=select(ProductCategory);stmt=stmt if user.role==Role.PLATFORM_ADMIN else stmt.where(ProductCategory.organisation_id==user.organisation_id);return db.scalars(stmt.order_by(ProductCategory.name)).all()

@router.post("/admin/categories",status_code=201)
def create_category(data:CategoryIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    if not user.organisation_id:raise HTTPException(422,"Tenant context required")
    if db.scalar(select(ProductCategory).where(ProductCategory.organisation_id==user.organisation_id,ProductCategory.name==data.name)):raise HTTPException(409,"Category already exists")
    item=ProductCategory(organisation_id=user.organisation_id,name=data.name);db.add(item);db.commit();db.refresh(item);return item

@router.delete("/admin/categories/{item_id}",status_code=204)
def delete_category(item_id:str,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(ProductCategory,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"Category not found")
    db.delete(item);db.commit()

@router.get("/admin/campaigns")
def admin_campaigns(user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    stmt=select(DiscountCampaign);stmt=stmt if user.role==Role.PLATFORM_ADMIN else stmt.where(DiscountCampaign.organisation_id==user.organisation_id);return db.scalars(stmt).all()
@router.post("/admin/campaigns",status_code=201)
def create_campaign(data:CampaignIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    if data.ends_on<data.starts_on:raise HTTPException(422,"End date must be after start date")
    item=DiscountCampaign(organisation_id=user.organisation_id,**data.model_dump());db.add(item);db.flush();log(db,user,"CREATE","Campaign",item.id);db.commit();db.refresh(item);return item
@router.patch("/admin/campaigns/{item_id}")
def update_campaign(item_id:str,data:CampaignIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(DiscountCampaign,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"Campaign not found")
    if data.ends_on<data.starts_on:raise HTTPException(422,"End date must be after start date")
    for key,value in data.model_dump().items():setattr(item,key,value)
    log(db,user,"UPDATE","Campaign",item.id);db.commit();db.refresh(item);return item
@router.delete("/admin/campaigns/{item_id}",status_code=204)
def delete_campaign(item_id:str,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    item=db.get(DiscountCampaign,item_id)
    if not item or (user.role!=Role.PLATFORM_ADMIN and item.organisation_id!=user.organisation_id):raise HTTPException(404,"Campaign not found")
    log(db,user,"DELETE","Campaign",item.id);db.delete(item);db.commit()
@router.post("/admin/campaigns/{campaign_id}/products",status_code=201)
def campaign_product(campaign_id:str,data:CampaignProductIn,user:User=Depends(roles(*CONTENT_ADMINS)),db:Session=Depends(get_db)):
    campaign=db.scalar(select(DiscountCampaign).where(DiscountCampaign.id==campaign_id,DiscountCampaign.organisation_id==user.organisation_id));product=db.scalar(select(Product).where(Product.id==data.product_id,Product.organisation_id==user.organisation_id));branch=db.scalar(select(Branch).where(Branch.id==data.branch_id,Branch.organisation_id==user.organisation_id))
    if not campaign or not product or not branch:raise HTTPException(404,"Campaign, product or branch not found")
    item=DiscountCampaignProduct(organisation_id=user.organisation_id,campaign_id=campaign.id,**data.model_dump());db.add(item);db.commit();db.refresh(item);return item

@router.get("/admin/logs")
def logs(user:User=Depends(roles(Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)),db:Session=Depends(get_db)):
    stmt=select(AuditLog);stmt=stmt if user.role==Role.PLATFORM_ADMIN else stmt.where(AuditLog.organisation_id==user.organisation_id);return db.scalars(stmt.order_by(AuditLog.created_at.desc()).limit(200)).all()
