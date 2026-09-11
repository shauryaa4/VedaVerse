from backend.services.citation_cache import (
    clear_citation_cache,
    get_citation,
    store_citation,
)


def setup_function():
    clear_citation_cache()


def test_store_and_get_citation():
    store_citation(
        session_id="session-1",
        citation_id="IN-1:3(p)",
        doc_name="Patents Act, 1970",
        section="3(p)",
        excerpt_text="traditional knowledge exclusion text",
        verified=True,
    )

    citation = get_citation("session-1", "IN-1:3(p)")

    assert citation == {
        "doc_name": "Patents Act, 1970",
        "section": "3(p)",
        "excerpt_text": "traditional knowledge exclusion text",
        "verified": True,
    }


def test_missing_citation_returns_none():
    citation = get_citation(
        "session-1",
        "IN-1:999",
    )

    assert citation is None


def test_sessions_are_isolated():
    store_citation(
        session_id="session-1",
        citation_id="IN-1:3(p)",
        doc_name="Document A",
        section="3(p)",
        excerpt_text="text A",
        verified=True,
    )

    store_citation(
        session_id="session-2",
        citation_id="IN-1:3(p)",
        doc_name="Document B",
        section="3(p)",
        excerpt_text="text B",
        verified=False,
    )

    citation_a = get_citation("session-1", "IN-1:3(p)")
    citation_b = get_citation("session-2", "IN-1:3(p)")

    assert citation_a["doc_name"] == "Document A"
    assert citation_a["verified"] is True

    assert citation_b["doc_name"] == "Document B"
    assert citation_b["verified"] is False