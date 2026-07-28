from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.domain import Organisation, Product

def auth(token): return {"Authorization":f"Bearer {token}"}

def test_registration_and_product_tenant_search(client,database):
    with SessionLocal() as db: org=db.scalar(select(Organisation).where(Organisation.name=="Nova Market"))
    response=client.post("/api/v1/auth/register",json={"first_name":"Nigar","last_name":"Rzayeva","phone":"+994501112233","email":"nigar@example.az","password":"SafePass1!","password_confirmation":"SafePass1!","organisation_id":org.id,"privacy_accepted":True})
    assert response.status_code==201
    token=response.json()["access_token"]
    products=client.get("/api/v1/products?q=süd",headers=auth(token))
    assert products.status_code==200 and len(products.json())==1

def test_favourite_suggestion_and_admin_notification(client,customer_token,admin_token):
    product=client.get("/api/v1/products",headers=auth(customer_token)).json()[0]
    assert client.post(f'/api/v1/favourites/products/{product["id"]}',headers=auth(customer_token)).status_code==201
    assert any(x["id"]==product["id"] for x in client.get("/api/v1/favourites/products",headers=auth(customer_token)).json())
    branch=client.get("/api/v1/branches",headers=auth(customer_token)).json()[0]
    made=client.post("/api/v1/suggestions",headers=auth(customer_token),json={"branch_id":branch["id"],"category":"RECYCLING","title":"Batareya toplama qutusu","description":"Filialda istifadə olunmuş batareyalar üçün ayrıca qutu yerləşdirilsin.","anonymous":False})
    assert made.status_code==201
    item=made.json()
    updated=client.patch(f'/api/v1/admin/suggestions/{item["id"]}',headers=auth(admin_token),json={"status":"PLANNED","admin_note":"Növbəti ay üçün plana daxil edildi."})
    assert updated.status_code==200
    notes=client.get("/api/v1/notifications",headers=auth(customer_token)).json()
    assert any(n["kind"]=="SUGGESTION_STATUS" for n in notes)

def test_customer_cannot_list_admin_suggestions(client,customer_token):
    assert client.get("/api/v1/admin/suggestions",headers=auth(customer_token)).status_code==403

def test_customer_detail_endpoints_and_selected_branch(client,customer_token):
    headers=auth(customer_token);branches=client.get("/api/v1/branches",headers=headers).json();branch=branches[1]
    home=client.get(f'/api/v1/home?branch_id={branch["id"]}',headers=headers)
    assert home.status_code==200 and home.json()["selected_branch"]["id"]==branch["id"]
    detail=client.get(f'/api/v1/branches/{branch["id"]}',headers=headers)
    assert detail.status_code==200 and isinstance(detail.json()["services"],list)
    product=client.get("/api/v1/products",headers=headers).json()[0]
    product_detail=client.get(f'/api/v1/products/{product["id"]}',headers=headers)
    assert product_detail.status_code==200 and len(product_detail.json()["branches"])==3
    campaigns=client.get("/api/v1/discounts",headers=headers).json()
    assert campaigns and client.get(f'/api/v1/discounts/{campaigns[0]["id"]}',headers=headers).status_code==200
    assert client.get("/api/v1/home?branch_id=not-this-tenant",headers=headers).status_code==404
