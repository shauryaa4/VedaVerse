"""
RAG-03 — the real /query HTTP endpoint.

Deliberately thin: all the actual logic lives in backend.rag.generation.
This file's only job is turning an HTTP request into a call to
answer_query() and the result back into an HTTP response. Keeping the
Chroma collection at module scope (not per-request) avoids reopening the
persistent client on every single call, which is unnecessary the moment
there's real traffic to handle (even hackathon-demo traffic).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.pip import ProductIntelligenceProfile
from backend.rag.generation import RagResponse, answer_query
from backend.logic.citation_verification import (
    classify_citation_support,
    extract_claim_citation_pairs,
    get_chunk_text,
    score_overlap,
    strip_unsupported_sentences,
)
from backend.services.citation_cache import store_citation
from backend.services.pip_session_store import get_session
from backend.services.vector_store import get_client, get_or_create_collection
from backend.db.query_log import log_query

router = APIRouter()

_PERSIST_DIR = "./chroma_data"
_collection = None


def _get_collection():
    """Lazy singleton — the Chroma collection is opened once, on first real
    request, not at import time (so importing this module in tests never
    touches disk unless a test actually calls the endpoint)."""
    global _collection
    if _collection is None:
        client = get_client(_PERSIST_DIR)
        _collection = get_or_create_collection(client)
    return _collection


def _cache_citations(
    session_id: str,
    rag_response: RagResponse,
) -> list[str]:
    """
    Runs the existing citation verification pipeline on the generated answer
    and stores citation details for the CITE-07 endpoint.

    Returns one classification for every sentence, in the same order as
    CITE-01 sentence extraction. This keeps the classifications aligned with
    CITE-06 sentence stripping.
    """
    pairs = extract_claim_citation_pairs(rag_response.answer_text)
    classifications = []

    for sentence, citation_id in pairs:
        if citation_id is None:
            classifications.append("UNCITED")
            continue

        chunk_text = get_chunk_text(
            citation_id,
            rag_response.used_chunks,
        )

        score = score_overlap(
            sentence,
            chunk_text,
        )

        classification = classify_citation_support(
            sentence,
            chunk_text,
            score,
        )

        classifications.append(classification)

        # Find the actual retrieved chunk so we can expose its metadata.
        matching_chunk = next(
            (
                chunk
                for chunk in rag_response.used_chunks
                if chunk.chunk_id == citation_id
            ),
            None,
        )

        if matching_chunk is None:
            continue

        store_citation(
            session_id=session_id,
            citation_id=citation_id,
            doc_name=matching_chunk.document_name or matching_chunk.doc_id or "Unknown",
            section=matching_chunk.section_or_article or "",
            excerpt_text=matching_chunk.text,
            verified=(classification == "SUPPORTED"),
        )

    return classifications


class QueryRequest(BaseModel):
    session_id: str | None = None
    pip: ProductIntelligenceProfile | None = None
    question: str


@router.post("/query", response_model=RagResponse)
def query_endpoint(request: QueryRequest) -> RagResponse:
    if request.session_id is not None:
        pip = get_session(request.session_id)
        if pip is None:
            raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")
    elif request.pip is not None:
        pip = request.pip
    else:
        raise HTTPException(status_code=422, detail="Provide either session_id or pip.")

    try:
        result = answer_query(
            pip,
            request.question,
            _get_collection(),
        )

        classifications = []

        if not result.abstained:
            classifications = _cache_citations(
                pip.session_id,
                result,
            )

            filtered_answer, should_abstain = strip_unsupported_sentences(
                result.answer_text,
                classifications,
            )

            result.answer_text = filtered_answer

            if should_abstain:
                result.abstained = True
                result.abstain_reason = (
                    "The generated answer did not contain enough citation-supported "
                    "content to return safely."
                )

        # API-04: log every query for post-demo debugging. Never let a
        # logging failure break the actual response the user is waiting on.
        try:
            log_query(
                session_id=pip.session_id,
                question=request.question,
                jurisdiction=pip.jurisdiction,
                category=pip.classification.category,
                objectives=list(pip.objective),
                where_clause=result.retrieval_where_clause,
                used_chunk_ids=[c.chunk_id for c in result.used_chunks],
                answer_text=result.answer_text,
                abstained=result.abstained,
                abstain_reason=result.abstain_reason,
            )
        except Exception as log_error:
            print(f"[query_log] failed to log query (non-fatal): {log_error}")

        return result

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))