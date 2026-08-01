import os
os.environ["DATABASE_URL"] = "sqlite:///./test_baxish.db"
import pytest
from fastapi.testclient import TestClient
from app.db.session import Base, engine
from app.main import app
from scripts.seed import run

@pytest.fixture(scope="session", autouse=True)
def database():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine); run(); yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def client(): return TestClient(app)

@pytest.fixture
def customer_token(client):
    return client.post("/api/v1/auth/login", json={"email":"customer@demo.az","password":"Demo123!"}).json()["access_token"]

@pytest.fixture
def admin_token(client):
    return client.post("/api/v1/auth/login", json={"email":"branch@demo.az","password":"Demo123!"}).json()["access_token"]

@pytest.fixture
def staff_token(client):
    return client.post("/api/v1/auth/login", json={"email":"staff@demo.az","password":"Demo123!"}).json()["access_token"]
