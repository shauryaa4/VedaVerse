from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_bhashini_translate_endpoint():
    res = client.post(
        "/bhashini/translate",
        json={"text": "Hello", "lang": "hi", "source_lang": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "translated_text" in data
    assert data["target_lang"] == "hi"


def test_bhashini_translate_batch_endpoint():
    res = client.post(
        "/bhashini/translate_batch",
        json={"texts": ["Hello", "Welcome"], "target_lang": "hi", "source_lang": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "translations" in data
    assert len(data["translations"]) == 2


def test_bhashini_in_out_endpoints():
    res_in = client.post("/bhashini/in", json={"text": "नमस्ते", "lang": "hi"})
    assert res_in.status_code == 200
    assert "translated_text" in res_in.json()

    res_out = client.post(
        "/bhashini/out", json={"text": "Hello world", "lang": "hi"}
    )
    assert res_out.status_code == 200
    assert "translated_text" in res_out.json()
