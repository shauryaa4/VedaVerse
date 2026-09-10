# backend/rag/generation.py

from pydantic import BaseModel
from backend.rag.chunking import Chunk

class RetrievedChunkRef(BaseModel):
    chunk_id: str          # matches Chunk.chunk_id from chunking.py, e.g. "IN-1:3(p)"
    text: str              # full chunk text, not truncated — CITE needs to diff against it
    source_url: str | None
    doc_id: str | None
    section_or_article: str | None

class RagResponse(BaseModel):
    answer_text: str                       # the generated answer, unverified
    used_chunks: list[RetrievedChunkRef]    # every chunk actually passed into the prompt
    retrieval_where_clause: dict | None     # what build_where_clause() produced, for debugging
    abstained: bool = False                # True if no relevant chunks were found
    abstain_reason: str | None = None