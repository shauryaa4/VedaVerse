"""
RAG-03 — the real /query HTTP endpoint.

Deliberately thin: all the actual logic lives in backend.rag.generation.

This file's only job is turning an HTTP request into a call to
answer_query() and the result back into an HTTP response. Keeping the
Chroma collection at module scope (not per-request) avoids reopening the
persistent client on every single call, which is unnecessary the moment
there's real traffic to handle (even hackathon-demo traffic).

Language handling:
- Request languages are validated against the canonical language config.
- Input is translated to English before legal/RAG reasoning.
- Legal reasoning is never performed on an untranslated multilingual input.
- Citation verification and confidence evaluation happen before output
  localization.
- Output is translated only after the verified legal answer is finalized.
- If input translation fails, legal/RAG reasoning is not performed.
- If output translation fails, the verified English answer is preserved.
"""

from fastapi import APIRouter, Depends, HTTPException
import httpx
from pydantic import BaseModel, field_validator
from pathlib import Path
from google.genai.errors import APIError as GeminiAPIError

from backend.logic.languages import normalize_language_code
from backend.models.pip import ProductIntelligenceProfile
from backend.models.evidence import EvidenceRecord
from backend.rag.generation import RagResponse, answer_query

from backend.logic.citation_verification import (
    calculate_support_score,
    classify_citation_support,
    extract_claim_citation_pairs,
    get_chunk_text,
    score_overlap,
    strip_unsupported_sentences,
)

from backend.rag.confidence import evaluate_confidence
from backend.services.citation_cache import store_citation
from backend.services.pip_session_store import get_session
from backend.services.vector_store import (
    get_client,
    get_or_create_collection,
)
from backend.db.query_log import log_query

from backend.logic.language import (
    TranslationError,
    translate_to_english,
    translate_from_english,
)

from backend.routes.auth import (
    ensure_session_access,
    optional_current_user,
)


router = APIRouter()


_PERSIST_DIR = str(Path(__file__).resolve().parents[2] / "chroma_data")
_collection = None


def _get_collection():
    """
    Lazy singleton — the Chroma collection is opened once, on first real
    request, not at import time.

    This means importing this module in tests never touches disk unless
    a test actually calls the endpoint.
    """
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
    Runs the existing citation verification pipeline on the generated
    answer and stores citation details for the CITE-07 endpoint.

    Returns one classification for every sentence, in the same order as
    CITE-01 sentence extraction. This keeps the classifications aligned
    with CITE-06 sentence stripping.
    """
    pairs = extract_claim_citation_pairs(rag_response.answer_text)

    classifications = []
    evidence_records = []

    for sentence, citation_id in pairs:
        if citation_id is None:
            classifications.append("UNCITED")
            evidence_records.append(
                EvidenceRecord(
                    module="legal_rag",
                    evidence_type="claim",
                    claim_or_finding=sentence,
                    status="UNCITED",
                )
            )
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
            evidence_records.append(
                EvidenceRecord(
                    module="legal_rag",
                    evidence_type="claim",
                    claim_or_finding=sentence,
                    status="UNSUPPORTED",
                    source_id=citation_id,
                )
            )
            continue

        evidence_records.append(
            EvidenceRecord(
                module="legal_rag",
                evidence_type="claim",
                claim_or_finding=sentence,
                status=classification,
                source_id=matching_chunk.doc_id or citation_id,
                source_title=matching_chunk.document_name,
                document_type=matching_chunk.document_type,
                provision=matching_chunk.section_or_article,
                date_enacted=matching_chunk.date_enacted,
                last_verified_date=matching_chunk.last_verified_date,
                source_url=matching_chunk.source_url,
                excerpt=matching_chunk.text,
                overlap_score=score,
            )
        )

        store_citation(
            session_id=session_id,
            citation_id=citation_id,
            doc_name=(
                matching_chunk.document_name
                or matching_chunk.doc_id
                or "Unknown"
            ),
            section=matching_chunk.section_or_article or "",
            excerpt_text=matching_chunk.text,
            verified=(classification == "SUPPORTED"),
            overlap_score=score,
        )

    rag_response.evidence_records = evidence_records
    return classifications


class QueryRequest(BaseModel):
    """
    Request model for POST /query.

    Either session_id or pip must be supplied.

    language is normalized through the canonical language configuration
    before any translation or legal reasoning occurs.
    """

    session_id: str | None = None
    pip: ProductIntelligenceProfile | None = None
    question: str
    language: str = "en"

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        return normalize_language_code(value)


@router.post(
    "/query",
    response_model=RagResponse,
)
def query_endpoint(
    request: QueryRequest,
    user: dict | None = Depends(optional_current_user),
) -> RagResponse:

    if request.session_id is not None:
        ensure_session_access(
            request.session_id,
            user,
        )

        pip = get_session(request.session_id)

        if pip is None:
            raise HTTPException(
                status_code=404,
                detail="Unknown session_id. Call POST /session first.",
            )

    elif request.pip is not None:
        pip = request.pip

    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either session_id or pip.",
        )

    try:
        # --------------------------------------------------------------
        # LANGUAGE LAYER — INPUT
        # --------------------------------------------------------------
        # Translate the user's original question into English before
        # sending it to legal/RAG reasoning.
        #
        # If translation fails, answer_query() is never called.
        # --------------------------------------------------------------

        try:
            english_question = translate_to_english(
                request.question,
                request.language,
            )

        except TranslationError as exc:
            raise HTTPException(
                status_code=502,
                detail={
                    "code": "LANGUAGE_PROCESSING_FAILED",
                    "message": str(exc),
                    "original_text": request.question,
                    "language": request.language,
                },
            ) from exc

        # --------------------------------------------------------------
        # LEGAL / RAG LAYER
        # --------------------------------------------------------------
        # From this point onward, legal reasoning receives only the
        # English normalized question.
        # --------------------------------------------------------------

        try:
            result = answer_query(
                pip,
                english_question,
                _get_collection(),
                original_text=request.question,
                detected_language=request.language,
                translation_status=(
                    "not_required"
                    if request.language == "en"
                    else "translated"
                ),
            )
        except GeminiAPIError as exc:
            provider_status = getattr(exc, "code", None)
            print(
                "[query] Gemini provider request failed "
                f"(status={provider_status or 'unknown'})"
            )
            if provider_status == 429:
                detail = (
                    "The legal-answer service has reached its Gemini API quota. "
                    "Check the backend project's quota or billing, then try again."
                )
            else:
                detail = (
                    "The legal-answer service is temporarily unavailable. "
                    "Check the backend logs and Gemini service configuration, then try again."
                )
            raise HTTPException(status_code=503, detail=detail) from exc
        except httpx.HTTPError as exc:
            print(
                "[query] Could not connect to Gemini "
                f"({type(exc).__name__})"
            )
            raise HTTPException(
                status_code=503,
                detail=(
                    "The backend could not connect to the legal-answer service. "
                    "Check backend network access and try again."
                ),
            ) from exc

        classifications = []

        if not result.abstained:

            # ----------------------------------------------------------
            # CITATION VERIFICATION
            # ----------------------------------------------------------

            classifications = _cache_citations(
                pip.session_id,
                result,
            )

            filtered_answer, citation_forced_abstain = (
                strip_unsupported_sentences(
                    result.answer_text,
                    classifications,
                )
            )

            result.answer_text = filtered_answer

            # ----------------------------------------------------------
            # CONFIDENCE / ABSTENTION
            # ----------------------------------------------------------
            # Combine classification confidence, citation support, and
            # routing status into the final answer/hedge/abstain decision.
            # ----------------------------------------------------------

            citation_support_score = calculate_support_score(
                classifications
            )

            result = evaluate_confidence(
                pip.classification.confidence,
                citation_support_score,
                citation_forced_abstain,
                result,
            )

            # ----------------------------------------------------------
            # LANGUAGE LAYER — OUTPUT
            # ----------------------------------------------------------
            # Translation happens ONLY after citation verification and
            # confidence/abstention processing are complete.
            #
            # If output translation fails, DO NOT discard the verified
            # English answer. Keep it and explicitly mark the translation
            # failure.
            # ----------------------------------------------------------

            if (
                not result.abstained
                and result.answer_text.strip()
            ):
                try:
                    result.answer_text = translate_from_english(
                        result.answer_text,
                        request.language,
                    )

                except TranslationError as exc:
                    result.translation_status = (
                        "output_translation_failed"
                    )

                    result.status_notes.append(
                        "The verified legal answer could not be "
                        "localized. The verified English answer is "
                        "shown instead."
                    )

                    print(
                        f"[language] output translation failed: {exc}"
                    )

        # --------------------------------------------------------------
        # QUERY LOGGING
        # --------------------------------------------------------------
        # Logging must never break the actual user response.
        # --------------------------------------------------------------

        try:
            log_query(
                session_id=pip.session_id,
                question=request.question,
                jurisdiction=pip.jurisdiction,
                category=pip.classification.category,
                objectives=list(pip.objective),
                where_clause=result.retrieval_where_clause,
                used_chunk_ids=[
                    c.chunk_id
                    for c in result.used_chunks
                ],
                answer_text=result.answer_text,
                abstained=result.abstained,
                abstain_reason=result.abstain_reason,
            )

        except Exception as log_error:
            print(
                f"[query_log] failed to log query "
                f"(non-fatal): {log_error}"
            )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e),
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
