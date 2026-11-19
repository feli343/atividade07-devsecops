from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_get_item():
    r = client.post("/items", json={"name": "caneta", "price": 3.5})
    assert r.status_code == 201
    item_id = r.json()["id"]
    r = client.get(f"/items/{item_id}")
    assert r.status_code == 200
    assert r.json()["name"] == "caneta"


def test_item_not_found():
    assert client.get("/items/99999").status_code == 404


def test_invalid_payload_rejected():
    r = client.post("/items", json={"name": "", "price": -1})
    assert r.status_code == 422


def test_security_headers_present():
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "content-security-policy" in r.headers
