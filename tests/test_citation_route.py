from fastapi.testclient import TestClient

from backend.main import app
from backend.services.citation_cache import (
    clear_citation_cache,
    store_citation,
)
from backend.rag.generation import RagResponse, RetrievedChunkRef
from backend.models.pip import ProductIntelligenceProfile

client = TestClient(app)


def setup_function():
    clear_citation_cache()


def test_citation_endpoint_returns_cached_citation():
    store_citation(
        session_id="session-1",
        citation_id="IN-1:3(p)",
        doc_name="Patents Act, 1970",
        section="3(p)",
        excerpt_text="traditional knowledge exclusion text",
        verified=True,
    )

    response = client.get(
        "/citation/IN-1/3(p)",
        params={"session_id": "session-1"},
    )

    assert response.status_code == 200

    assert response.json() == {
        "doc_name": "Patents Act, 1970",
        "section": "3(p)",
        "excerpt_text": "traditional knowledge exclusion text",
        "verified": True,
    }


def test_citation_endpoint_returns_404_when_missing():
    response = client.get(
        "/citation/IN-1/999",
        params={"session_id": "session-1"},
    )

    assert response.status_code == 404


def test_citation_endpoint_preserves_stored_verified_value():
    store_citation(
        session_id="session-1",
        citation_id="IN-1:3(p)",
        doc_name="Patents Act, 1970",
        section="3(p)",
        excerpt_text="some legal text",
        verified=False,
    )

    response = client.get(
        "/citation/IN-1/3(p)",
        params={"session_id": "session-1"},
    )

    assert response.status_code == 200
    assert response.json()["verified"] is False

def test_cache_citations_stores_real_verified_citation(monkeypatch):
    from backend.routes.query import _cache_citations

    chunk = RetrievedChunkRef(
        chunk_id="IN-1:3(p)",
        text="Traditional knowledge is excluded from patentability.",
        source_url=None,
        doc_id="IN-1",
        document_name="Patents Act, 1970",
        section_or_article="3(p)",
    )

    rag_response = RagResponse(
        answer_text=(
            "Traditional knowledge is excluded from patentability "
            "[IN-1:3(p)]."
        ),
        used_chunks=[chunk],
        retrieval_where_clause=None,
        abstained=False,
    )

    _cache_citations("session-real", rag_response)

    response = client.get(
        "/citation/IN-1/3(p)",
        params={"session_id": "session-real"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["doc_name"] == "Patents Act, 1970"
    assert data["section"] == "3(p)"
    assert data["excerpt_text"] == chunk.text
    assert data["verified"] is True

def test_cache_citations_marks_unsupported_claim_as_unverified():
    from backend.routes.query import _cache_citations

    chunk = RetrievedChunkRef(
        chunk_id="IN-1:3(p)",
        text="This section concerns patentability requirements.",
        source_url=None,
        doc_id="IN-1",
        document_name="Patents Act, 1970",
        section_or_article="3(p)",
    )

    rag_response = RagResponse(
        answer_text=(
            "This law creates a 25-year exclusive monopoly for traditional "
            "knowledge [IN-1:3(p)]."
        ),
        used_chunks=[chunk],
        retrieval_where_clause=None,
        abstained=False,
    )

    _cache_citations("session-unsupported", rag_response)

    response = client.get(
        "/citation/IN-1/3(p)",
        params={"session_id": "session-unsupported"},
    )

    assert response.status_code == 200
    assert response.json()["verified"] is False

def test_query_then_citation_endpoint_returns_cached_verification(monkeypatch):
    from backend.routes import query as query_route

    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        objective=["patentability"],
        product={
            "classical_basis": "yes",
            "intended_use": "therapeutic",
            "novelty": "existing",
        },
    )

    chunk = RetrievedChunkRef(
        chunk_id="IN-1:3(p)",
        text="Traditional knowledge is excluded from patentability.",
        source_url=None,
        doc_id="IN-1",
        document_name="Patents Act, 1970",
        section_or_article="3(p)",
    )

    rag_response = RagResponse(
        answer_text=(
            "Traditional knowledge is excluded from patentability "
            "[IN-1:3(p)]."
        ),
        used_chunks=[chunk],
        retrieval_where_clause=None,
        abstained=False,
    )

    monkeypatch.setattr(
        query_route,
        "answer_query",
        lambda *args, **kwargs: rag_response,
    )

    monkeypatch.setattr(
        query_route,
        "_get_collection",
        lambda: None,
    )

    query_response = client.post(
        "/query",
        json={
            "pip": pip.model_dump(mode="json"),
            "question": "Can traditional knowledge be patented?",
        },
    )

    assert query_response.status_code == 200

    citation_response = client.get(
        "/citation/IN-1/3(p)",
        params={"session_id": pip.session_id},
    )

    assert citation_response.status_code == 200

    data = citation_response.json()

    assert data["doc_name"] == "Patents Act, 1970"
    assert data["section"] == "3(p)"
    assert data["excerpt_text"] == chunk.text
    assert data["verified"] is True

def test_query_strips_unsupported_citation_end_to_end(monkeypatch):
    """End-to-end test to ensure that unsupported citations are stripped from the answer."""

    from backend.routes import query as query_route

    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        objective=["patentability"],
        product={
            "classical_basis": "yes",
            "intended_use": "therapeutic",
            "novelty": "existing",
        },
    )

    supported_chunk = RetrievedChunkRef(
        chunk_id="IN-1:3(p)",
        text="Traditional knowledge is excluded from patentability.",
        source_url=None,
        doc_id="IN-1",
        document_name="Patents Act, 1970",
        section_or_article="3(p)",
    )

    unsupported_chunk = RetrievedChunkRef(
        chunk_id="IN-1:4",
        text="This section concerns patentability requirements.",
        source_url=None,
        doc_id="IN-1",
        document_name="Patents Act, 1970",
        section_or_article="4",
    )

    rag_response = RagResponse(
        answer_text=(
            "Traditional knowledge is excluded from patentability "
            "[IN-1:3(p)]. "
            "This law creates a 25-year exclusive monopoly for traditional "
            "knowledge [IN-1:4]."
        ),
        used_chunks=[supported_chunk, unsupported_chunk],
        retrieval_where_clause=None,
        abstained=False,
    )

    monkeypatch.setattr(
        query_route,
        "answer_query",
        lambda *args, **kwargs: rag_response,
    )

    monkeypatch.setattr(
        query_route,
        "_get_collection",
        lambda: None,
    )

    response = client.post(
        "/query",
        json={
            "pip": pip.model_dump(mode="json"),
            "question": "Can traditional knowledge be patented?",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # The supported claim must remain.
    assert (
        "Traditional knowledge is excluded from patentability "
        "[IN-1:3(p)]."
        in data["answer_text"]
    )

    # The unsupported claim must be stripped from the final answer.
    assert "25-year exclusive monopoly" not in data["answer_text"]

    # The citation cache must still record that the bad citation was unverified.
    citation_response = client.get(
        "/citation/IN-1/4",
        params={"session_id": pip.session_id},
    )

    assert citation_response.status_code == 200
    assert citation_response.json()["verified"] is False
    
