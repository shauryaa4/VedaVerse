"""
RAG-03 — the real /query logic.

Ties the already-working classify -> route -> retrieve chain to an actual
LLM call and returns the RagResponse contract (agreed with Sri before either
side wrote code — see the team workflow doc). CITE-01->08 and CONF-01->05
both consume RagResponse directly; nothing downstream should ever touch a
raw LLM response or a raw Chroma result, only this shape.

LLM: Google Gemini (google-genai SDK), chosen because it has a genuinely
free API tier with no billing setup — see .env.example for the required
GEMINI_API_KEY. Swapping providers later only means changing _get_client()
and the one generate_content() call below; the RagResponse contract and
everything that calls answer_query() stays the same.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

from backend.logic.classification import apply_classification_to_pip
from backend.logic.routing import route
from backend.services.vector_store import build_where_clause
from backend.services.vector_store import query as vector_query

# Load .env from repo root regardless of where this module is imported from.
load_dotenv(Path(__file__).parent.parent.parent / ".env")

_GEMINI_MODEL = "gemini-3.6-flash"
_client: Optional["genai.Client"] = None


def _get_client() -> "genai.Client":
    """Lazily creates the Gemini client on first real use, not at import time —
    this means importing generation.py (e.g. in tests) never requires a real
    API key; only actually calling answer_query() with real chunks does."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and add "
                "your real key (see scripts/test_llm_connection.py to verify)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


class RetrievedChunkRef(BaseModel):
    chunk_id: str          # matches Chunk.chunk_id from chunking.py, e.g. "IN-1:3(p)"
    text: str               # full chunk text, not truncated — CITE needs to diff against it
    source_url: str | None
    doc_id: str | None
    section_or_article: str | None


class RagResponse(BaseModel):
    answer_text: str                       # the generated answer, unverified
    used_chunks: list[RetrievedChunkRef]    # every chunk actually passed into the prompt
    retrieval_where_clause: dict | None     # what build_where_clause() produced, for debugging
    abstained: bool = False                 # True if no relevant chunks were found
    abstain_reason: str | None = None


def _build_prompt(question: str, chunks: list[RetrievedChunkRef]) -> str:
    """
    Deliberately blunt instructions, repeated: this is a legal-answers tool,
    so 'don't invent law' matters more than a nicely-worded prompt. Each
    chunk gets a bracketed label matching its chunk_id so the model can (and
    is told to) cite inline — CITE-01->08 later checks whether it actually did.
    """
    context_blocks = []
    for c in chunks:
        label = f"[{c.doc_id or '?'}:{c.section_or_article or '?'}]"
        context_blocks.append(f"{label}\n{c.text}")
    context = "\n\n---\n\n".join(context_blocks)

    return f"""You are a legal information assistant helping someone understand \
Indian and international law around traditional-knowledge and biodiversity \
IP protection. Answer the question using ONLY the legal text provided below. \
Do not use outside knowledge, and do not invent section numbers, case law, \
or facts that are not in the provided text.

If the provided text does not fully answer the question, say so explicitly \
rather than filling the gap with an assumption.

When you state something drawn from a specific source, cite it inline in \
brackets exactly as labeled below, e.g. [IN-1:3(p)].

RETRIEVED LEGAL TEXT:
{context}

QUESTION:
{question}

ANSWER:"""


def _results_to_chunk_refs(results: dict) -> list[RetrievedChunkRef]:
    """Converts a raw Chroma query() result (nested one-query-batch lists) into
    the flat RetrievedChunkRef list the rest of the system actually works with."""
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    refs = []
    for chunk_id, text, meta in zip(ids, documents, metadatas):
        refs.append(RetrievedChunkRef(
            chunk_id=chunk_id,
            text=text,
            source_url=meta.get("source_url") or None,
            doc_id=meta.get("doc_id") or None,
            section_or_article=meta.get("section_or_article") or None,
        ))
    return refs


def answer_query(pip, question: str, collection, top_k: int = 5) -> RagResponse:
    """
    The full chain: classify (if not already done) -> route -> build_where_clause
    -> retrieve -> generate. Returns RagResponse either way — including the
    abstain path, which is a normal, expected outcome (per build spec section
    5/9: "no chunks found -> abstain" is not an error condition).

    `pip` may already be classified or not — if pip.classification.category is
    still None, this runs apply_classification_to_pip() itself, so callers can
    hand in a freshly-built PIP straight from intake without a separate step.
    """
    if pip.classification.category is None:
        apply_classification_to_pip(pip)

    routing = route(pip.jurisdiction, pip.classification.category, pip.objective)
    where = build_where_clause(routing)

    results = vector_query(collection, question, where=where, top_k=top_k)
    used_chunks = _results_to_chunk_refs(results)

    if not used_chunks:
        return RagResponse(
            answer_text="",
            used_chunks=[],
            retrieval_where_clause=where,
            abstained=True,
            abstain_reason=(
                "No relevant legal text was found for this question under the "
                "matched jurisdiction/regime filters. The system should fall back "
                "to jurisdiction-only retrieval or escalate to a human reviewer "
                "rather than answer without grounding."
            ),
        )

    prompt = _build_prompt(question, used_chunks)
    client = _get_client()
    response = client.models.generate_content(model=_GEMINI_MODEL, contents=prompt)
    answer_text = response.text or ""

    return RagResponse(
        answer_text=answer_text,
        used_chunks=used_chunks,
        retrieval_where_clause=where,
        abstained=False,
    )