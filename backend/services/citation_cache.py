"""
CITE-07 — in-memory citation cache.

Stores citation details produced during /query so the frontend can later
request the details for a citation without performing a new verification.

This is intentionally in-memory for the hackathon/demo.
A persistent database can replace it later without changing the API contract.
"""

from typing import Optional


# session_id -> citation_id -> citation details
_CITATION_CACHE: dict[str, dict[str, dict]] = {}


def store_citation(
    session_id: str,
    citation_id: str,
    doc_name: str,
    section: str,
    excerpt_text: str,
    verified: bool,
) -> None:
    """Store the result of citation verification for a session."""

    session_cache = _CITATION_CACHE.setdefault(session_id, {})

    session_cache[citation_id] = {
        "doc_name": doc_name,
        "section": section,
        "excerpt_text": excerpt_text,
        "verified": verified,
    }


def get_citation(
    session_id: str,
    citation_id: str,
) -> Optional[dict]:
    """Return a previously stored citation, or None if it does not exist."""

    return _CITATION_CACHE.get(session_id, {}).get(citation_id)


def clear_citation_cache() -> None:
    """Clear the cache. Primarily useful for tests."""

    _CITATION_CACHE.clear()