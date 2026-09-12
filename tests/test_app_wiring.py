from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_session_intake_classify_are_reachable():
    session = client.post("/session").json()
    sid = session["session_id"]
    assert client.post("/intake", json={"session_id": sid, "jurisdiction": "india"}).status_code == 200
    assert client.post("/classify", json={"session_id": sid}).status_code == 200