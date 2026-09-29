"""
CITE-07 — citation detail endpoint.

Returns citation information previously produced during /query.

Important:
The `verified` field comes from the stored verification result.
This endpoint does NOT perform a fresh citation-support check.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.services.citation_cache import get_citation
from backend.routes.auth import ensure_session_access, optional_current_user


router = APIRouter()


class CitationResponse(BaseModel):
    doc_name: str
    section: str
    excerpt_text: str
    verified: bool
    citation_overlap_score: float = 0.0
    citation_overlap_label: str = "Citation Overlap Score"
    citation_overlap_explanation: str = (
        "Proportion of meaningful claim keywords found in the cited retrieved "
        "chunk. This is a lexical heuristic, not semantic or legal correctness."
    )


@router.get(
    "/citation/{doc_id}/{section}",
    response_model=CitationResponse,
)
def citation_endpoint(
    doc_id: str,
    section: str,
    session_id: str,
    user: dict | None = Depends(optional_current_user),
) -> CitationResponse:

    ensure_session_access(session_id, user)

    citation_id = f"{doc_id}:{section}"

    citation = get_citation(
        session_id=session_id,
        citation_id=citation_id,
    )

    if citation is None:
        raise HTTPException(
            status_code=404,
            detail="Citation not found for this session.",
        )

    return CitationResponse(**citation)
