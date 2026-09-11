"""
CITE-07 — citation detail endpoint.

Returns citation information previously produced during /query.

Important:
The `verified` field comes from the stored verification result.
This endpoint does NOT perform a fresh citation-support check.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.citation_cache import get_citation


router = APIRouter()


class CitationResponse(BaseModel):
    doc_name: str
    section: str
    excerpt_text: str
    verified: bool


@router.get(
    "/citation/{doc_id}/{section}",
    response_model=CitationResponse,
)
def citation_endpoint(
    doc_id: str,
    section: str,
    session_id: str,
) -> CitationResponse:

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