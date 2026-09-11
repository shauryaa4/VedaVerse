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
from backend.services.vector_store import get_client, get_or_create_collection

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


class QueryRequest(BaseModel):
    pip: ProductIntelligenceProfile
    question: str


@router.post("/query", response_model=RagResponse)
def query_endpoint(request: QueryRequest) -> RagResponse:
    try:
        return answer_query(request.pip, request.question, _get_collection())
    except RuntimeError as e:
        # Most likely cause: GEMINI_API_KEY missing/misconfigured — see
        # generation.py's _get_client(). Surface it as a clear 500, not a
        # silent failure or a confusing stack trace to the frontend.
        raise HTTPException(status_code=500, detail=str(e))