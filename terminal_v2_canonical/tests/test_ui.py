from terminal_v2.app.main import app

def test_index():

    from fastapi.testclient import TestClient

    c=TestClient(app)

    r=c.get("/")

    assert r.status_code==200

def test_health():

    from fastapi.testclient import TestClient

    c=TestClient(app)

    r=c.get("/health")

    assert r.status_code==200
