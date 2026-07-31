import json,secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import create_refresh_token, create_token, current_user, hash_password, roles
from app.db.session import get_db
from app.models.customer import AccountDeletionRequest, FavouriteCampaign, FavouriteProduct, ManagementSuggestion, Notification,SuggestionAttachment,SuggestionStatusHistory
from app.models.domain import Branch, CustomerMarketMembership, News, Organisation, Product, Role, User
from app.models.retail import BranchService,DiscountCampaign,FavouriteBranch,FileAsset,ProductCategory,ProductPrice
from app.schemas.api import TokenOut, UserOut
from app.schemas.customer import DeleteRequestIn,ForgotPasswordIn,PreferencesUpdate,PreferredBranchIn,PreferredMarketIn,ProfileUpdate, RegisterIn, SuggestionCreate, SuggestionOut, SuggestionUpdate
from app.services.customer_context import market_id

router=APIRouter(prefix="/api/v1")

@router.get("/organisations")
def organisations(db:Session=Depends(get_db)):
    return db.scalars(select(Organisation).order_by(Organisation.name)).all()

@router.get("/market")
def current_market(user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    market=db.get(Organisation,market_id(user))
    if not market:raise HTTPException(404,"Market not found")
    return market

@router.post("/auth/register",response_model=TokenOut,status_code=201)
def register(data:RegisterIn,db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==data.email.lower())): raise HTTPException(409,"Email already registered")
    org=db.get(Organisation,data.organisation_id)
    if not org: raise HTTPException(404,"Organisation not found")
    user=User(organisation_id=org.id,selected_organisation_id=org.id,email=data.email.lower(),full_name=f"{data.first_name} {data.last_name}",phone=data.phone,role=Role.CUSTOMER,password_hash=hash_password(data.password))
    db.add(user);db.flush();db.add(CustomerMarketMembership(customer_id=user.id,organisation_id=org.id));db.commit();db.refresh(user)
    return {"access_token":create_token(user),"refresh_token":create_refresh_token(user),"user":user}

@router.patch("/profile",response_model=UserOut)
def update_profile(data:ProfileUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if data.preferred_branch_id and not db.scalar(select(Branch).where(Branch.id==data.preferred_branch_id,Branch.organisation_id==market_id(user))):raise HTTPException(404,"Branch not found")
    user.full_name=data.full_name;user.phone=data.phone;user.language=data.language;user.profile_image_url=data.profile_image_url;user.preferred_branch_id=data.preferred_branch_id;db.commit();db.refresh(user);return user

@router.post("/profile/delete-request",status_code=202)
def deletion_request(data:DeleteRequestIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    db.add(AccountDeletionRequest(user_id=user.id,reason=data.reason));db.commit();return {"status":"accepted"}

@router.post("/auth/forgot-password",status_code=202)
def forgot_password(data:ForgotPasswordIn):
    return {"status":"accepted","message":"If the account exists, recovery instructions will be sent."}

@router.get("/profile/preferences")
def get_preferences(user:User=Depends(roles(Role.CUSTOMER))):
    return PreferencesUpdate(**json.loads(user.preferences_json or "{}")).model_dump()

@router.patch("/profile/preferences")
def update_preferences(data:PreferencesUpdate,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    user.preferences_json=json.dumps(data.model_dump());db.commit();return data.model_dump()

@router.patch("/profile/preferred-branch")
def update_preferred_branch(data:PreferredBranchIn,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    branch=db.scalar(select(Branch).where(Branch.id==data.branch_id,Branch.organisation_id==market_id(user)))
    if not branch:raise HTTPException(404,"Branch not found")
    user.preferred_branch_id=branch.id;db.commit();return {"branch_id":branch.id}

@router.patch("/profile/preferred-market")
def update_preferred_market(data:PreferredMarketIn,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    market=db.get(Organisation,data.organisation_id)
    if not market:raise HTTPException(404,"Market not found")
    membership=db.scalar(select(CustomerMarketMembership).where(CustomerMarketMembership.customer_id==user.id,CustomerMarketMembership.organisation_id==market.id))
    if not membership:db.add(CustomerMarketMembership(customer_id=user.id,organisation_id=market.id))
    elif not membership.is_active:membership.is_active=True
    user.selected_organisation_id=market.id;user.preferred_branch_id=None;db.commit();return {"organisation_id":market.id,"name":market.name}

@router.get("/news")
def list_news(branch_id:str|None=None,content_type:str|None=None,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    selected_branch=branch_id or user.preferred_branch_id
    stmt=select(News).where(News.organisation_id==market_id(user),News.status=="PUBLISHED",or_(News.valid_until.is_(None),News.valid_until>=datetime.now()),or_(News.branch_id.is_(None),News.branch_id==selected_branch))
    if content_type:stmt=stmt.where(News.content_type==content_type)
    return db.scalars(stmt.order_by(News.published_at.desc())).all()

@router.get("/news/{news_id}")
def news_detail(news_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    item=db.scalar(select(News).where(News.id==news_id,News.organisation_id==market_id(user),News.status=="PUBLISHED",or_(News.valid_until.is_(None),News.valid_until>=datetime.now()),or_(News.branch_id.is_(None),News.branch_id==user.preferred_branch_id)));
    if not item: raise HTTPException(404,"News not found")
    return item

@router.get("/products")
def products(q:str|None=None,category:str|None=None,sort:str="name",branch_id:str|None=None,user:User=Depends(current_user),db:Session=Depends(get_db)):
    stmt=select(Product).where(Product.organisation_id==market_id(user))
    if q: stmt=stmt.where(or_(Product.name.ilike(f"%{q}%"),Product.brand.ilike(f"%{q}%"),Product.barcode==q))
    if category: stmt=stmt.where(Product.category==category)
    order={"name":Product.name.asc(),"price_asc":Product.price.asc(),"price_desc":Product.price.desc(),"discount":Product.discount_price.asc().nullslast()}.get(sort,Product.name.asc())
    items=db.scalars(stmt.order_by(order)).all()
    if not branch_id:return items
    prices={p.product_id:p for p in db.scalars(select(ProductPrice).where(ProductPrice.branch_id==branch_id,ProductPrice.organisation_id==market_id(user))).all()}
    return [{"id":x.id,"name":x.name,"brand":x.brand,"package_size":x.package_size,"barcode":x.barcode,"category":x.category,"price":prices[x.id].price if x.id in prices else x.price,"discount_price":x.discount_price,"image_url":x.image_url,"available":prices[x.id].available if x.id in prices else False} for x in items]

@router.get("/product-categories")
def product_categories(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return [item.name for item in db.scalars(select(ProductCategory).where(ProductCategory.organisation_id==market_id(user)).order_by(ProductCategory.name)).all()]

@router.get("/products/barcode/{barcode}")
def barcode(barcode:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    item=db.scalar(select(Product).where(Product.barcode==barcode,Product.organisation_id==market_id(user)))
    if not item: raise HTTPException(404,"Product not found")
    return item

@router.get("/products/{product_id}")
def product_detail(product_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    item=db.scalar(select(Product).where(Product.id==product_id,Product.organisation_id==market_id(user)))
    if not item:raise HTTPException(404,"Product not found")
    prices=db.execute(select(ProductPrice,Branch).join(Branch,Branch.id==ProductPrice.branch_id).where(ProductPrice.product_id==item.id,ProductPrice.organisation_id==market_id(user))).all()
    return {"id":item.id,"name":item.name,"brand":item.brand,"package_size":item.package_size,"barcode":item.barcode,"category":item.category,"price":item.price,"discount_price":item.discount_price,"image_url":item.image_url,"branches":[{"branch_id":price.branch_id,"branch_name":branch.name,"price":price.price,"previous_price":price.previous_price,"available":price.available} for price,branch in prices]}

@router.get("/branches/{branch_id}")
def branch_detail(branch_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    branch=db.scalar(select(Branch).where(Branch.id==branch_id,Branch.organisation_id==market_id(user)))
    if not branch:raise HTTPException(404,"Branch not found")
    services=db.scalars(select(BranchService).where(BranchService.branch_id==branch.id,BranchService.organisation_id==market_id(user))).all()
    return {"id":branch.id,"name":branch.name,"address":branch.address,"hours":branch.hours,"distance_km":branch.distance_km,"is_open":branch.is_open,"image_url":branch.image_url,"latitude":branch.latitude,"longitude":branch.longitude,"services":[item.name for item in services]}

@router.get("/favourites/products")
def favourites(user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    return db.scalars(select(Product).join(FavouriteProduct,FavouriteProduct.product_id==Product.id).where(FavouriteProduct.user_id==user.id,Product.organisation_id==market_id(user))).all()

@router.post("/favourites/products/{product_id}",status_code=201)
def favourite(product_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    product=db.scalar(select(Product).where(Product.id==product_id,Product.organisation_id==market_id(user)))
    if not product: raise HTTPException(404,"Product not found")
    record=FavouriteProduct(organisation_id=market_id(user),user_id=user.id,product_id=product.id);db.add(record)
    try: db.commit()
    except IntegrityError: db.rollback()
    return {"favourite":True}

@router.delete("/favourites/products/{product_id}")
def unfavourite(product_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    db.execute(delete(FavouriteProduct).where(FavouriteProduct.user_id==user.id,FavouriteProduct.product_id==product_id));db.commit();return {"favourite":False}

@router.get("/favourites/branches")
def favourite_branches(user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    return db.scalars(select(Branch).join(FavouriteBranch,FavouriteBranch.branch_id==Branch.id).where(FavouriteBranch.user_id==user.id,Branch.organisation_id==market_id(user))).all()

@router.post("/favourites/branches/{branch_id}",status_code=201)
def favourite_branch(branch_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    branch=db.scalar(select(Branch).where(Branch.id==branch_id,Branch.organisation_id==market_id(user)))
    if not branch:raise HTTPException(404,"Branch not found")
    if not db.scalar(select(FavouriteBranch).where(FavouriteBranch.user_id==user.id,FavouriteBranch.branch_id==branch_id)):
        db.add(FavouriteBranch(organisation_id=market_id(user),user_id=user.id,branch_id=branch_id));db.commit()
    return {"favourite":True}

@router.delete("/favourites/branches/{branch_id}")
def unfavourite_branch(branch_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    db.execute(delete(FavouriteBranch).where(FavouriteBranch.user_id==user.id,FavouriteBranch.branch_id==branch_id));db.commit();return {"favourite":False}

@router.get("/favourites/campaigns")
def favourite_campaigns(user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    return [x.id for x in db.scalars(select(DiscountCampaign).join(FavouriteCampaign,FavouriteCampaign.campaign_id==DiscountCampaign.id).where(FavouriteCampaign.user_id==user.id,DiscountCampaign.organisation_id==market_id(user))).all()]

@router.post("/favourites/campaigns/{campaign_id}",status_code=201)
def favourite_campaign(campaign_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    campaign=db.scalar(select(DiscountCampaign).where(DiscountCampaign.id==campaign_id,DiscountCampaign.organisation_id==market_id(user)))
    if not campaign:raise HTTPException(404,"Campaign not found")
    if not db.scalar(select(FavouriteCampaign).where(FavouriteCampaign.user_id==user.id,FavouriteCampaign.campaign_id==campaign_id)):
        db.add(FavouriteCampaign(organisation_id=market_id(user),user_id=user.id,campaign_id=campaign_id));db.commit()
    return {"favourite":True}

@router.delete("/favourites/campaigns/{campaign_id}")
def unfavourite_campaign(campaign_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    db.execute(delete(FavouriteCampaign).where(FavouriteCampaign.user_id==user.id,FavouriteCampaign.campaign_id==campaign_id));db.commit();return {"favourite":False}

@router.post("/suggestions",response_model=SuggestionOut,status_code=201)
def create_suggestion(data:SuggestionCreate,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    if data.branch_id and not db.scalar(select(Branch).where(Branch.id==data.branch_id,Branch.organisation_id==market_id(user))): raise HTTPException(404,"Branch not found")
    payload=data.model_dump(exclude={"attachment_ids"});item=ManagementSuggestion(tracking_number=f"MS-{secrets.token_hex(4).upper()}",organisation_id=market_id(user),customer_id=user.id,**payload);db.add(item);db.flush();db.add(SuggestionStatusHistory(suggestion_id=item.id,status=item.status,note="Təklif qəbul edildi"))
    for asset_id in data.attachment_ids:
        asset=db.scalar(select(FileAsset).where(FileAsset.id==asset_id,FileAsset.owner_id==user.id,FileAsset.organisation_id==market_id(user)))
        if asset:db.add(SuggestionAttachment(organisation_id=market_id(user),suggestion_id=item.id,file_asset_id=asset.id))
    db.commit();db.refresh(item);return suggestion_view(item,db)

def suggestion_view(item:ManagementSuggestion,db:Session):
    history=db.scalars(select(SuggestionStatusHistory).where(SuggestionStatusHistory.suggestion_id==item.id).order_by(SuggestionStatusHistory.created_at)).all()
    media_rows=db.execute(select(SuggestionAttachment,FileAsset).join(FileAsset,FileAsset.id==SuggestionAttachment.file_asset_id).where(SuggestionAttachment.suggestion_id==item.id)).all()
    return {"id":item.id,"tracking_number":item.tracking_number,"branch_id":item.branch_id,"category":item.category,"title":item.title,"description":item.description,"anonymous":item.anonymous,"status":item.status,"admin_note":item.admin_note,"created_at":item.created_at,"updated_at":item.updated_at,"history":[{"status":x.status,"note":x.note,"created_at":x.created_at} for x in history],"media":[{"id":asset.id,"url":f"/api/v1/media/{asset.id}","mime_type":asset.mime_type,"name":asset.original_name} for _,asset in media_rows]}

@router.get("/suggestions",response_model=list[SuggestionOut])
def own_suggestions(user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    return [suggestion_view(x,db) for x in db.scalars(select(ManagementSuggestion).where(ManagementSuggestion.customer_id==user.id).order_by(ManagementSuggestion.created_at.desc())).all()]

@router.get("/suggestions/{suggestion_id}",response_model=SuggestionOut)
def own_suggestion(suggestion_id:str,user:User=Depends(roles(Role.CUSTOMER)),db:Session=Depends(get_db)):
    item=db.scalar(select(ManagementSuggestion).where(ManagementSuggestion.id==suggestion_id,ManagementSuggestion.customer_id==user.id))
    if not item:raise HTTPException(404,"Suggestion not found")
    return suggestion_view(item,db)

@router.get("/notifications")
def notifications(user:User=Depends(current_user),db:Session=Depends(get_db)):
    return db.scalars(select(Notification).where(Notification.user_id==user.id,Notification.organisation_id==market_id(user)).order_by(Notification.created_at.desc())).all()

@router.patch("/notifications/read-all")
def mark_all_read(user:User=Depends(current_user),db:Session=Depends(get_db)):
    items=db.scalars(select(Notification).where(Notification.user_id==user.id,Notification.organisation_id==market_id(user),Notification.is_read==False)).all()
    for item in items:item.is_read=True
    db.commit();return {"updated":len(items)}

@router.patch("/notifications/{notification_id}/read")
def mark_read(notification_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
    item=db.scalar(select(Notification).where(Notification.id==notification_id,Notification.user_id==user.id))
    if not item: raise HTTPException(404,"Notification not found")
    item.is_read=True;db.commit();return {"is_read":True}

ADMIN=(Role.BRANCH_ADMIN,Role.HEAD_OFFICE_ADMIN,Role.PLATFORM_ADMIN)
@router.get("/admin/suggestions",response_model=list[SuggestionOut])
def admin_suggestions(user:User=Depends(roles(*ADMIN)),db:Session=Depends(get_db)):
    stmt=select(ManagementSuggestion).order_by(ManagementSuggestion.created_at.desc())
    if user.role!=Role.PLATFORM_ADMIN: stmt=stmt.where(ManagementSuggestion.organisation_id==market_id(user))
    if user.role==Role.BRANCH_ADMIN: stmt=stmt.where(or_(ManagementSuggestion.branch_id==user.branch_id,ManagementSuggestion.branch_id.is_(None)))
    return [suggestion_view(x,db) for x in db.scalars(stmt).all()]

@router.patch("/admin/suggestions/{item_id}",response_model=SuggestionOut)
def admin_update_suggestion(item_id:str,data:SuggestionUpdate,user:User=Depends(roles(*ADMIN)),db:Session=Depends(get_db)):
    item=db.get(ManagementSuggestion,item_id)
    allowed=item and (user.role==Role.PLATFORM_ADMIN or item.organisation_id==market_id(user)) and (user.role!=Role.BRANCH_ADMIN or item.branch_id in (None,user.branch_id))
    if not allowed: raise HTTPException(404,"Suggestion not found")
    item.status=data.status;item.admin_note=data.admin_note;db.add(SuggestionStatusHistory(suggestion_id=item.id,status=data.status,note=data.admin_note))
    db.add(Notification(organisation_id=item.organisation_id,user_id=item.customer_id,kind="SUGGESTION_STATUS",title="Təklifiniz yeniləndi",body=f"{item.tracking_number}: {item.status.value}",related_entity_type="SUGGESTION",related_entity_id=item.id));db.commit();db.refresh(item);return suggestion_view(item,db)
