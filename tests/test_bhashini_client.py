import requests
import pytest

from backend.logic import bhashini_client


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._body


@pytest.fixture(autouse=True)
def configure_ulca(monkeypatch):
    monkeypatch.setenv("BHASHINI_USER_ID", "test-user")
    monkeypatch.setenv("BHASHINI_ULCA_API_KEY", "test-ulca-key")
    monkeypatch.setenv("BHASHINI_PIPELINE_ID", "test-pipeline")
    bhashini_client._resolve_cached.cache_clear()
    yield
    bhashini_client._resolve_cached.cache_clear()


def test_compute_resolves_service_and_inference_key_from_config(monkeypatch):
    calls = []
    config = {
        "pipelineResponseConfig": [{
            "taskType": "translation",
            "config": [{
                "language": {"sourceLanguage": "en", "targetLanguage": "ta"},
                "serviceId": "resolved/nmt-service",
            }],
        }],
        "pipelineInferenceAPIEndPoint": {
            "callbackUrl": "https://compute.example/pipeline",
            "inferenceApiKey": {"name": "X-Inference-Key", "value": "resolved-key"},
        },
    }

    def post(url, **kwargs):
        calls.append((url, kwargs))
        if url == bhashini_client.CONFIG_URL:
            return FakeResponse(200, config)
        return FakeResponse(200, {"pipelineResponse": [{"output": [{"target": "வணக்கம்"}]}]})

    monkeypatch.setattr(bhashini_client.requests, "post", post)
    result = bhashini_client.compute(
        {"pipelineTasks": [{"taskType": "translation", "config": {"language": {
            "sourceLanguage": "en", "targetLanguage": "ta",
        }}}]},
        "translation", "en", "ta",
    )

    assert result["pipelineResponse"][0]["output"][0]["target"] == "வணக்கம்"
    assert calls[0][1]["headers"]["userID"] == "test-user"
    assert calls[0][1]["headers"]["ulcaApiKey"] == "test-ulca-key"
    assert calls[1][0] == "https://compute.example/pipeline"
    assert calls[1][1]["headers"]["X-Inference-Key"] == "resolved-key"
    assert calls[1][1]["json"]["pipelineTasks"][0]["config"]["serviceId"] == "resolved/nmt-service"


def test_bad_ulca_credentials_have_clear_sanitized_error(monkeypatch):
    monkeypatch.setattr(
        bhashini_client.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(400, {"message": "not authenticated"}),
    )
    with pytest.raises(bhashini_client.BhashiniError, match="matching pair"):
        bhashini_client.resolve_pipeline("translation", "en", "hi")
