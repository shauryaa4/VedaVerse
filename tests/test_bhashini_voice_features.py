from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_bhashini_translate_endpoint(monkeypatch):
    from backend.routes import bhashini_routes
    monkeypatch.setattr(bhashini_routes, "_translate", lambda text, source_language, target_language: "नमस्ते")
    res = client.post(
        "/bhashini/translate",
        json={"text": "Hello", "lang": "hi", "source_lang": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "translated_text" in data
    assert data["target_lang"] == "hi"


def test_bhashini_translate_batch_endpoint(monkeypatch):
    from backend.routes import bhashini_routes
    monkeypatch.setattr(
        bhashini_routes,
        "translate_many_from_english",
        lambda texts, target_language, source_language: [
            f"{target_language}:{text}" for text in texts
        ],
    )
    res = client.post(
        "/bhashini/translate_batch",
        json={"texts": ["Hello", "Welcome"], "target_lang": "hi", "source_lang": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["translations"] == ["hi:Hello", "hi:Welcome"]


def test_bhashini_in_out_endpoints(monkeypatch):
    from backend.routes import bhashini_routes
    monkeypatch.setattr(bhashini_routes, "translate_to_english", lambda text, source_language: "Hello")
    monkeypatch.setattr(bhashini_routes, "translate_from_english", lambda text, target_language: "नमस्ते दुनिया")
    res_in = client.post("/bhashini/in", json={"text": "नमस्ते", "lang": "hi"})
    assert res_in.status_code == 200
    assert "translated_text" in res_in.json()

    res_out = client.post(
        "/bhashini/out", json={"text": "Hello world", "lang": "hi"}
    )
    assert res_out.status_code == 200
    assert "translated_text" in res_out.json()


def test_bhashini_failure_is_reported_instead_of_succeeding_with_english(monkeypatch):
    from backend.routes import bhashini_routes
    from backend.logic.language import TranslationError
    monkeypatch.setattr(
        bhashini_routes,
        "_translate",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TranslationError("auth rejected")),
    )

    response = client.post(
        "/bhashini/translate",
        json={"text": "Hello", "lang": "ta", "source_lang": "en"},
    )
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "BHASHINI_TRANSLATION_FAILED"
