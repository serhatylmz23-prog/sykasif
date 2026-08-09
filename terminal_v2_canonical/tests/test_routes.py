from fastapi.testclient import TestClient
from terminal_v2.app.main import app

client=TestClient(app)

def test_root():
    r=client.get("/")
    assert r.status_code==200

def test_health():
    r=client.get("/health")
    assert r.status_code==200

def test_api_health():
    r=client.get("/api/health")
    assert r.status_code==200
