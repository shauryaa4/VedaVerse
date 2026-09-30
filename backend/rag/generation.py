"""
RAG-03 — the real /query logic.

Ties the already-working classify -> route -> retrieve chain to an actual
LLM call and returns the RagResponse contract.

CITE-01->08 and CONF-01->05 both consume RagResponse directly; nothing
downstream should ever touch a raw LLM response or a raw Chroma result,
only this shape.

LLM: Google Gemini (google-genai SDK).
Fallback LLM: OpenRouter (OpenAI-compatible API).

Language architecture:
- The query route owns Bhashini input/output translation.
- This module performs legal/RAG reasoning on normalized English text.
- The original user text and language metadata are preserved in RagResponse.
- Legal reasoning must never depend on the translated output language.
- Citation identifiers and legal source identifiers are never translated.
"""

import os
from pathlib import Path
from typing import Literal, Optional

import httpx
from dotenv import dotenv_values, load_dotenv
from google import genai
from google.genai.errors import APIError as GeminiAPIError
from pydantic import BaseModel, Field

from backend.logic.classification import apply_classification_to_pip
from backend.logic.languages import normalize_language_code
from backend.logic.routing import route_pip
from backend.models.evidence import EvidenceRecord
from backend.services.vector_store import build_where_clause
from backend.services.vector_store import query as vector_query


# ----------------------------------------------------------------------
# Environment / Gemini / OpenRouter configuration
# ----------------------------------------------------------------------

# Resolve the local .env from the repository root regardless of the process
# working directory. Keep this path so a key added after the backend starts is
# also picked up on the next Gemini client initialization.
_REPO_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(_REPO_ENV_PATH)

_GEMINI_MODEL = "gemini-3.6-flash"

# OpenRouter provides an OpenAI-compatible API. The free router chooses from
# currently available free models.
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_OPENROUTER_MODEL = "openrouter/free"

_client: Optional["genai.Client"] = None


def _get_client() -> "genai.Client":
    """
    Lazily creates the Gemini client on first real use, not at import time.

    This means importing generation.py in tests never requires a real API key.
    Only actually calling answer_query() with real chunks requires the key.
    """

    global _client

    if _client is None:
        # Prefer the hosting environment, but fall back to the repo .env file.
        # The file is read here as well as at import time because developers
        # often add the key while the API server is already running.
        api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()

        if not api_key:
            api_key = (
                dotenv_values(_REPO_ENV_PATH).get("GEMINI_API_KEY") or ""
            ).strip()

        if not api_key:
            raise RuntimeError(
                "Gemini answer generation is not configured. Set GEMINI_API_KEY "
                "in the repository-root .env for local use, or in the backend's "
                "environment/secrets for deployment. Then restart the backend."
            )

        _client = genai.Client(api_key=api_key)

    return _client


def _generate_with_openrouter(prompt: str) -> str:
    """
    Generate an answer through OpenRouter.

    This is used only as a fallback when Gemini returns HTTP 429
    (rate limit / quota exhaustion).

    The same legal/RAG prompt produced for Gemini is sent to OpenRouter,
    so the retrieval and legal grounding pipeline remains unchanged.
    """

    api_key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()

    if not api_key:
        # Also support the local repository .env for development.
        api_key = (
            dotenv_values(_REPO_ENV_PATH).get("OPENROUTER_API_KEY") or ""
        ).strip()

    if not api_key:
        raise RuntimeError(
            "OpenRouter fallback is not configured. "
            "Set OPENROUTER_API_KEY in the backend environment."
        )

    response = httpx.post(
        _OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": _OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        },
        timeout=60.0,
    )

    response.raise_for_status()

    data = response.json()

    answer = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    if not answer:
        raise RuntimeError(
            "OpenRouter returned an empty answer."
        )

    print(
        "[query] OpenRouter fallback generated the legal answer."
    )

    return answer


# ----------------------------------------------------------------------
# Retrieved evidence contract
# ----------------------------------------------------------------------


class RetrievedChunkRef(BaseModel):
    """
    One legal source chunk actually retrieved and passed into the LLM prompt.
    """

    chunk_id: str
    text: str
    source_url: str | None
    doc_id: str | None
    document_name: str | None = None
    document_type: str | None = None
    section_or_article: str | None
    date_enacted: str | None = None
    last_verified_date: str | None = None
    legal_regime: str | None = None


# ----------------------------------------------------------------------
# Confidence contract
# ----------------------------------------------------------------------


class ConfidenceComponent(BaseModel):
    """
    One weighted input to the numeric confidence score.

    Returned to the frontend so the score can be drawn as a breakdown
    chart, not just a single opaque number.
    """

    key: str
    # "citation_support" | "classification" | "retrieved_evidence_coverage"

    label: str
    # Human-readable name for the chart row.

    value: float
    # Raw signal, 0.0-1.0.

    weight: float
    # This signal's weight in the score, 0.0-1.0.

    contribution: float
    # value * weight, 0.0-1.0.

    detail: str = ""
    # Plain-language explanation of where value came from.

    explanation: str = ""
    # Meaning of this metric; all values are heuristic pipeline/evidence signals.


# ----------------------------------------------------------------------
# RAG response contract
# ----------------------------------------------------------------------


class RagResponse(BaseModel):
    """
    Canonical response contract shared by RAG, citation verification,
    confidence evaluation, API routes, and the frontend.

    Multilingual metadata is kept separate from legal reasoning so that:

        original_text
            -> what the user actually submitted

        detected_language
            -> language associated with the request

        normalized_text
            -> English text used for legal/RAG reasoning

        translation_status
            -> explicit state of the language-processing layer

    The legal answer itself remains in answer_text.
    """

    # ------------------------------------------------------------------
    # Multilingual traceability
    # ------------------------------------------------------------------

    original_text: str = ""

    detected_language: str = "en"

    normalized_text: str = ""

    translation_status: Literal[
        "not_required",
        "translated",
        "translation_failed",
        "output_translation_failed",
        "unknown",
    ] = "not_required"

    # ------------------------------------------------------------------
    # Existing RAG contract
    # ------------------------------------------------------------------

    answer_text: str = ""
    # Generated answer. It may later be localized by routes/query.py.

    used_chunks: list[RetrievedChunkRef] = Field(
        default_factory=list
    )
    # Every chunk actually passed into the prompt.

    retrieval_where_clause: dict | None = None
    # What build_where_clause() produced, for debugging.

    abstained: bool = False
    # True if no relevant chunks were found or confidence logic abstained.

    abstain_reason: str | None = None

    status_notes: list[str] = Field(
        default_factory=list
    )

    evidence_records: list[EvidenceRecord] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Confidence contract
    # ------------------------------------------------------------------

    # CONF-01/05: frontend renders a 4-state badge:
    # HIGH / MEDIUM / LOW / ABSTAIN.
    confidence: Literal[
        "high",
        "medium",
        "low",
        "abstain",
    ] = "high"

    confidence_reason: str | None = None

    # System Confidence Score: heuristic pipeline-support measure, never a
    # probability that the legal conclusion is correct.
    confidence_score: float = 0.0

    confidence_score_label: Literal["System Confidence Score"] = "System Confidence Score"
    confidence_score_explanation: str = (
        "Heuristic measure of how strongly the current pipeline supports "
        "returning this result. It is not a probability that the legal "
        "conclusion is correct."
    )

    # Citation Support Score remains an independently exposed answer-level metric.
    citation_support_score: float = 0.0
    citation_support_label: Literal["Citation Support Score"] = "Citation Support Score"
    citation_support_explanation: str = (
        "Percentage of answer claims supported by the retrieved legal evidence "
        "under the citation-verification rules."
    )

    # Three weighted pipeline-support signals behind confidence_score.
    confidence_breakdown: list[ConfidenceComponent] = Field(
        default_factory=list
    )


# ----------------------------------------------------------------------
# Prompt construction
# ----------------------------------------------------------------------


def _build_prompt(
    question: str,
    chunks: list[RetrievedChunkRef],
) -> str:
    """
    Build the legal/RAG prompt.

    Important language boundary:

    This function always generates the legal reasoning prompt in English.

    Bhashini translation belongs to the HTTP language layer, not the legal
    reasoning layer. This prevents language localization from affecting
    classification, routing, retrieval, citation identifiers, or legal
    interpretation.
    """

    by_regime: dict[str, list[RetrievedChunkRef]] = {}

    for chunk in chunks:
        regime = chunk.legal_regime or "unspecified regime"
        by_regime.setdefault(regime, []).append(chunk)

    regime_blocks = []

    for regime, regime_chunks in by_regime.items():

        chunk_texts = []

        for chunk in regime_chunks:

            label = (
                f"[{chunk.doc_id or '?'}:"
                f"{chunk.section_or_article or '?'}]"
            )

            chunk_texts.append(
                f"{label}\n{chunk.text}"
            )

        regime_blocks.append(
            f"--- LEGAL AREA: {regime} ---\n"
            + "\n\n".join(chunk_texts)
        )

    context = "\n\n".join(regime_blocks)

    return f"""
You are a legal information assistant helping someone understand
Indian and international law around traditional-knowledge and biodiversity
IP protection.

Answer the question using ONLY the legal text provided below.

Do not use outside knowledge.

Do not invent:
- legal provisions
- section numbers
- article numbers
- case law
- authorities
- exemptions
- procedural requirements
- facts
- conclusions that are not supported by the provided text

If the provided text does not fully answer the question, say so explicitly
rather than filling the gap with an assumption.

When you state something drawn from a specific source, cite it inline in
brackets exactly as labeled below.

For example:

[IN-1:3(p)]

IMPORTANT:
- Keep citation labels exactly as provided.
- Do not translate citation labels.
- Do not alter document IDs.
- Do not alter section/article identifiers.
- Do not create citations that are not present in the retrieved text.
- Distinguish clearly between information directly supported by the
  retrieved text and information that cannot be established from it.

RETRIEVED LEGAL TEXT:

{context}

QUESTION:

{question}

ANSWER:

Write your answer in English.
""".strip()


# ----------------------------------------------------------------------
# Chroma result conversion
# ----------------------------------------------------------------------


def _results_to_chunk_refs(
    results: dict,
) -> list[RetrievedChunkRef]:
    """
    Convert a raw Chroma query() result into the flat
    RetrievedChunkRef list used by the rest of the system.
    """

    ids = results.get("ids", [[]])[0]

    documents = results.get("documents", [[]])[0]

    metadatas = results.get("metadatas", [[]])[0]

    refs = []

    for chunk_id, text, meta in zip(
        ids,
        documents,
        metadatas,
    ):
        refs.append(
            RetrievedChunkRef(
                chunk_id=chunk_id,
                text=text,
                source_url=meta.get("source_url") or None,
                doc_id=meta.get("doc_id") or None,
                document_name=meta.get("document_name") or None,
                document_type=meta.get("document_type") or None,
                section_or_article=(
                    meta.get("section_or_article") or None
                ),
                date_enacted=meta.get("date_enacted") or None,
                last_verified_date=meta.get("last_verified_date") or None,
                legal_regime=(
                    meta.get("legal_regime") or None
                ),
            )
        )

    return refs


# ----------------------------------------------------------------------
# Main RAG pipeline
# ----------------------------------------------------------------------


def answer_query(
    pip,
    question: str,
    collection,
    top_k: int = 5,
    *,
    original_text: str | None = None,
    detected_language: str = "en",
    translation_status: Literal[
        "not_required",
        "translated",
        "translation_failed",
        "output_translation_failed",
        "unknown",
    ] = "not_required",
) -> RagResponse:
    """
    Full legal/RAG chain:

        classify
            ->
        route
            ->
        build_where_clause
            ->
        retrieve
            ->
        generate

    The function returns RagResponse either way, including the abstain path.

    Language handling:
    - question is the normalized English question used for legal reasoning.
    - original_text preserves what the user actually submitted.
    - detected_language records the request language.
    - translation_status records whether input normalization occurred.

    IMPORTANT:

    This function does not perform Bhashini translation itself.

    The HTTP route is responsible for:
        user language -> English
        English verified answer -> user language

    This keeps language processing separate from legal reasoning.
    """

    # ------------------------------------------------------------------
    # Normalize / validate language metadata
    # ------------------------------------------------------------------

    normalized_language = normalize_language_code(
        detected_language
    )

    if original_text is None:
        original_text = question

    # ------------------------------------------------------------------
    # Validate question
    # ------------------------------------------------------------------

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    if pip.classification.category is None:
        apply_classification_to_pip(pip)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    routing = route_pip(pip)

    if routing is None:
        return RagResponse(
            original_text=original_text,
            detected_language=detected_language,
            normalized_text=question,
            translation_status=translation_status,
            answer_text="",
            used_chunks=[],
            retrieval_where_clause=None,
            abstained=True,
            abstain_reason=(
                "Jurisdiction is required before legal routing can be performed."
            ),
            status_notes=[
                "Legal reasoning was not performed because jurisdiction is unknown."
            ],
            confidence="abstain",
            confidence_reason="Jurisdiction is missing.",
            confidence_score=0.0,
            confidence_breakdown=[],
        )

    # ------------------------------------------------------------------
    # Retrieval filter
    # ------------------------------------------------------------------

    where = build_where_clause(routing)

    # ------------------------------------------------------------------
    # Vector retrieval
    # ------------------------------------------------------------------

    results = vector_query(
        collection,
        question,
        where=where,
        top_k=top_k,
    )

    used_chunks = _results_to_chunk_refs(results)

    # ------------------------------------------------------------------
    # Abstain when no evidence is retrieved
    # ------------------------------------------------------------------

    if not used_chunks:

        return RagResponse(
            original_text=original_text,
            detected_language=normalized_language,
            normalized_text=question,
            translation_status=translation_status,
            answer_text="",
            used_chunks=[],
            retrieval_where_clause=where,
            abstained=True,
            abstain_reason=(
                "No relevant legal text was found for this question "
                "under the matched jurisdiction/regime filters. "
                "The system should fall back to jurisdiction-only "
                "retrieval or escalate to a human reviewer rather than "
                "answer without grounding."
            ),
            status_notes=routing.status_notes,
            confidence="abstain",
            confidence_reason=(
                "No relevant chunks were retrieved for this query."
            ),
            confidence_score=0.0,
        )

    # ------------------------------------------------------------------
    # Legal prompt
    # ------------------------------------------------------------------

    prompt = _build_prompt(
        question,
        used_chunks,
    )

    # ------------------------------------------------------------------
    # LLM generation
    # ------------------------------------------------------------------

    client = _get_client()

    try:
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=prompt,
        )

        answer_text = response.text or ""

    except GeminiAPIError as exc:
        provider_status = getattr(exc, "code", None)

        if provider_status not in (429, 503):
            raise

        print(
            f"[query] Gemini provider returned {provider_status}; "
            "falling back to OpenRouter."
        )
        answer_text = _generate_with_openrouter(prompt)

    # ------------------------------------------------------------------
    # Final RagResponse
    # ------------------------------------------------------------------

    return RagResponse(
        original_text=original_text,
        detected_language=normalized_language,
        normalized_text=question,
        translation_status=translation_status,
        answer_text=answer_text,
        used_chunks=used_chunks,
        retrieval_where_clause=where,
        abstained=False,
        status_notes=routing.status_notes,
    )