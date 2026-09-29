from fastapi.testclient import TestClient

from backend.main import app
from backend.models.abs_models import ABSAssessment
from backend.models.tkdl import PriorArtAssessment
from backend.rag.generation import RagResponse
from backend.routes.tkdl_routes import TKDLSearchResponse
from backend.services.pip_session_store import clear_sessions, create_session


client = TestClient(app)


def test_unified_assessment_runs_classification_and_routing():
    clear_sessions()
    pip = create_session()
    intake = client.post("/intake", json={
        "session_id": pip.session_id,
        "jurisdiction": "india",
        "language": "en",
        "objective": ["general"],
        "product_name": "Herbal wellness blend",
        "composition": [{"ingredient": "Tulsi", "is_active": True}],
        "intended_use": "other",
        "novelty": "unknown",
    })
    assert intake.status_code == 200

    response = client.post("/assessment", json={
        "session_id": pip.session_id,
        "include_abs": False,
        "include_tkdl": False,
    })

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == pip.session_id
    assert data["classification"]["category"]
    assert data["routing"]["jurisdiction"] == "india"
    assert data["legal_answer"] is None
    assert data["abs_assessment"] is None
    assert data["tkdl_assessment"] is None
    clear_sessions()


def test_unified_assessment_requires_jurisdiction():
    clear_sessions()
    pip = create_session()
    response = client.post("/assessment", json={"session_id": pip.session_id})
    assert response.status_code == 422
    clear_sessions()


def test_unified_assessment_composes_legal_abs_tkdl_and_escalation(monkeypatch):
    from backend.routes import assessment

    clear_sessions()
    pip = create_session()
    client.post("/intake", json={
        "session_id": pip.session_id,
        "jurisdiction": "india",
        "language": "en",
        "objective": ["patentability", "abs_relevance", "prior_art"],
        "composition": [{"ingredient": "Tulsi", "is_active": True}],
        "intended_use": "therapeutic",
        "novelty": "modified",
    })
    monkeypatch.setattr(
        assessment,
        "query_endpoint",
        lambda *_args, **_kwargs: RagResponse(
            answer_text="Legal answer [IN-1:3(p)].",
            used_chunks=[],
            retrieval_where_clause=None,
            status_notes=[],
        ),
    )
    monkeypatch.setattr(
        assessment,
        "abs_assess_endpoint",
        lambda *_args, **_kwargs: ABSAssessment(
            status="CONDITIONAL",
            pathway="NBA",
            reasoning=["ABS review is needed."],
            human_escalation={"human_review": True},
        ),
    )
    monkeypatch.setattr(
        assessment,
        "tkdl_search_endpoint",
        lambda *_args, **_kwargs: TKDLSearchResponse(
            assessment=PriorArtAssessment(risk_level="medium", reasoning=["Review prior art."]),
            matches=[],
        ),
    )

    response = client.post("/assessment", json={
        "session_id": pip.session_id,
        "question": "Can I protect this?",
        "include_abs": True,
        "include_tkdl": True,
    })

    assert response.status_code == 200
    data = response.json()
    assert "Legal answer" in data["final_answer"]
    assert "ABS review is needed" in data["final_answer"]
    assert "Review prior art" in data["final_answer"]
    assert data["human_review_required"] is True
    clear_sessions()
