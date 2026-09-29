"""Unified PIP-to-legal/ABS/TKDL assessment API."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.logic.classification import apply_classification_to_pip
from backend.logic.language import TranslationError, translate_from_english
from backend.logic.languages import normalize_language_code
from backend.logic.routing import RoutingResult, route
from backend.models.abs_models import ABSAssessment
from backend.models.evidence import EvidenceRecord
from backend.rag.generation import RagResponse
from backend.routes.abs_routes import ABSAssessRequest, abs_assess_endpoint
from backend.routes.auth import ensure_session_access, optional_current_user
from backend.routes.classify import ClassifyResponse
from backend.routes.query import QueryRequest, query_endpoint
from backend.routes.tkdl_routes import TKDLSearchRequest, TKDLSearchResponse, tkdl_search_endpoint
from backend.services.pip_session_store import get_session, save_session


router = APIRouter(prefix="/assessment", tags=["Unified Assessment"])


def _final_answer(
    legal: RagResponse | None,
    abs_result: ABSAssessment | None,
    tkdl_result: TKDLSearchResponse | None,
    language: str,
) -> str | None:
    """Assemble the exact module outputs into one clearly labelled answer."""
    sections: list[str] = []
    if legal:
        legal_text = legal.answer_text or legal.abstain_reason or "The legal assistant abstained."
        sections.append(legal_text)
    if abs_result:
        lines = [
            f"Access and benefit sharing: {abs_result.status} ({abs_result.pathway}).",
            *abs_result.reasoning,
        ]
        sections.append("\n".join(lines))
    if tkdl_result:
        assessment = tkdl_result.assessment
        lines = [
            f"Traditional knowledge prior-art check: {assessment.risk_level} risk.",
            *assessment.reasoning,
        ]
        sections.append("\n".join(lines))
    if not sections:
        return None
    answer = "\n\n".join(sections)
    # /query already localizes its verified legal answer. Only the additional
    # deterministic assessment sections need output localization here.
    if language != "en":
        english_sections = sections[1:] if legal else sections
        if english_sections:
            try:
                localized = translate_from_english("\n\n".join(english_sections), language)
            except TranslationError as exc:
                raise HTTPException(
                    status_code=502,
                    detail={"code": "LANGUAGE_PROCESSING_FAILED", "message": str(exc)},
                ) from exc
            if legal:
                answer = f"{sections[0]}\n\n{localized}"
            else:
                answer = localized
    return answer


def _collect_evidence(
    legal: RagResponse | None,
    abs_result: ABSAssessment | None,
    tkdl_result: TKDLSearchResponse | None,
) -> list[EvidenceRecord]:
    """Expose module evidence through one stable, inspectable response field."""
    records = list(legal.evidence_records) if legal else []

    if abs_result:
        for citation in abs_result.citations:
            records.append(
                EvidenceRecord(
                    module="abs",
                    evidence_type="rule",
                    claim_or_finding=citation.excerpt,
                    status=citation.verification_status,
                    source_id=citation.source_id or citation.doc_id,
                    source_title=citation.source_title or citation.document_name,
                    document_type=citation.document_type,
                    authority=citation.authority,
                    provision=citation.section_or_article,
                    effective_date=citation.effective_date,
                    source_url=citation.source_url,
                    excerpt=citation.excerpt,
                )
            )

    if tkdl_result:
        for match in tkdl_result.matches:
            records.append(
                EvidenceRecord(
                    module="tkdl",
                    evidence_type="prior_art_match",
                    claim_or_finding=(
                        f"Candidate archive match for {match.record.formulation_name}; "
                        f"overlap ratio {match.overlap_ratio:.3f}."
                    ),
                    status="UNVERIFIED",
                    source_id=match.record.record_id,
                    source_title=match.record.formulation_name,
                    excerpt=match.record.source_text,
                    overlap_score=match.overlap_ratio,
                )
            )

    return records


class UnifiedAssessmentRequest(BaseModel):
    session_id: str
    question: str | None = None
    language: str | None = None
    include_abs: bool | None = None
    include_tkdl: bool | None = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str | None) -> str | None:
        return normalize_language_code(value) if value else None


class UnifiedAssessmentResponse(BaseModel):
    session_id: str
    classification: ClassifyResponse
    routing: RoutingResult
    legal_answer: RagResponse | None = None
    abs_assessment: ABSAssessment | None = None
    tkdl_assessment: TKDLSearchResponse | None = None
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    final_answer: str | None = None
    abstained: bool | None = None
    human_review_required: bool = False


@router.post("", response_model=UnifiedAssessmentResponse)
def unified_assessment_endpoint(
    body: UnifiedAssessmentRequest,
    user: dict | None = Depends(optional_current_user),
) -> UnifiedAssessmentResponse:
    """Classify and route one saved PIP, then run applicable evidence modules."""
    ensure_session_access(body.session_id, user)
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")
    if not pip.jurisdiction:
        raise HTTPException(status_code=422, detail="Set a jurisdiction before assessment.")

    pip = apply_classification_to_pip(pip)
    save_session(pip)
    category = pip.classification.category
    classification = ClassifyResponse(
        category=category,
        reasons=pip.classification.reasons,
        confidence=pip.classification.confidence or "low",
        unresolved_flags=pip.classification.unresolved_flags,
    )
    routing = route(pip.jurisdiction, category, pip.objective)

    legal_answer = None
    if body.question and body.question.strip():
        legal_answer = query_endpoint(
            QueryRequest(
                session_id=body.session_id,
                question=body.question,
                language=body.language or pip.language,
            ),
            user=user,
        )

    should_run_abs = body.include_abs if body.include_abs is not None else (
        "biodiversity_abs" in routing.legal_regimes or pip.abs_facts is not None
    )
    should_run_tkdl = body.include_tkdl if body.include_tkdl is not None else (
        "prior_art" in pip.objective
        or pip.protection_target == "traditional_knowledge"
        or any("TKDL archive search" in item for item in routing.matched_rows)
    )

    abs_assessment = (
        abs_assess_endpoint(ABSAssessRequest(session_id=body.session_id), user=user)
        if should_run_abs else None
    )
    tkdl_assessment = (
        tkdl_search_endpoint(TKDLSearchRequest(session_id=body.session_id), user=user)
        if should_run_tkdl else None
    )

    return UnifiedAssessmentResponse(
        session_id=body.session_id,
        classification=classification,
        routing=routing,
        legal_answer=legal_answer,
        abs_assessment=abs_assessment,
        tkdl_assessment=tkdl_assessment,
        evidence=_collect_evidence(legal_answer, abs_assessment, tkdl_assessment),
        final_answer=_final_answer(
            legal_answer,
            abs_assessment,
            tkdl_assessment,
            body.language or pip.language,
        ),
        abstained=legal_answer.abstained if legal_answer else None,
        human_review_required=bool(
            abs_assessment and abs_assessment.human_escalation.human_review
        ),
    )
