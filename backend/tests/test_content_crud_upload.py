import io

def auth(t):return {"Authorization":f"Bearer {t}"}
def head_token(client):return client.post("/api/v1/auth/login",json={"email":"head@demo.az","password":"Demo123!"}).json()["access_token"]

def test_head_office_content_reflects_to_customer(client,customer_token):
    head=head_token(client)
    created=client.post("/api/v1/admin/news",headers=auth(head),json={"title_az":"Yeni xidmət","title_en":"New service","summary_az":"Filialda yeni xidmət aktivdir.","summary_en":"A new branch service is active.","image_url":"/assets/news.svg"})
    assert created.status_code==201
    assert any(x["id"]==created.json()["id"] for x in client.get("/api/v1/news",headers=auth(customer_token)).json())
    product=client.post("/api/v1/admin/products",headers=auth(head),json={"name":"Test məhsulu","brand":"Demo","barcode":"9999991234567","category":"Ərzaq","price":3.25})
    assert product.status_code==201
    assert any(x["id"]==product.json()["id"] for x in client.get("/api/v1/products?q=Test",headers=auth(customer_token)).json())

def test_upload_validation(client,customer_token):
    good=client.post("/api/v1/uploads",headers=auth(customer_token),files={"file":("evidence.jpg",io.BytesIO(b"demo-image"),"image/jpeg")})
    assert good.status_code==201 and good.json()["mime_type"]=="image/jpeg"
    bad=client.post("/api/v1/uploads",headers=auth(customer_token),files={"file":("unsafe.exe",io.BytesIO(b"bad"),"application/octet-stream")})
    assert bad.status_code==415

