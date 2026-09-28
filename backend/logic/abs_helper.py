"""
ABS helper adapter.

- assess_abs(): delegates to backend.logic.abs_engine's deterministic, fact-driven
  ABS pathway engine (the 34-scenario-tested engine).
- ground_abs_citations(): ABS-03, kept from main. Optional, additive post-step that
  grounds each reasoning line against the shared biodiversity_abs Chroma collection
  using citation_verification.score_overlap. Never raises for a single line and never
  changes the deterministic verdict.
"""

from backend.logic.abs_engine import assess_abs_fact_driven
from backend.logic.citation_verification import score_overlap, OVERLAP_SUPPORT_THRESHOLD
from backend.models.abs_models import ABSAssessment, ABSGroundedCitation
from backend.models.pip import ProductIntelligenceProfile
from backend.services.vector_store import query as vector_query

# Frozen legal_regime tag for the BD Act / Rules (see routing.py docstring).
_ABS_LEGAL_REGIME = "biodiversity_abs"


def assess_abs(pip: ProductIntelligenceProfile) -> ABSAssessment:
    """Entry point for ABS assessment, delegating to the fact-driven ABS engine."""
    return assess_abs_fact_driven(pip)


def ground_abs_citations(assessment: ABSAssessment, collection, top_k: int = 1) -> ABSAssessment:
    """Ground each line of assessment.reasoning in the shared Chroma corpus (ABS-03)."""
    if collection is None:
        return assessment

    for reasoning_text in assessment.reasoning:
        try:
            results = vector_query(
                collection,
                reasoning_text,
                where={"legal_regime": _ABS_LEGAL_REGIME},
                top_k=top_k,
            )
        except Exception:
            continue  # one failed line must never break the whole assessment

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        if not ids:
            continue

        chunk_text = documents[0]
        meta = metadatas[0]
        score = score_overlap(reasoning_text, chunk_text)

        assessment.grounded_reasoning.append(
            ABSGroundedCitation(
                reasoning_text=reasoning_text,
                doc_id=meta.get("doc_id") or None,
                document_name=meta.get("document_name") or None,
                section_or_article=meta.get("section_or_article") or None,
                source_url=meta.get("source_url") or None,
                excerpt=chunk_text,
                verified=score >= OVERLAP_SUPPORT_THRESHOLD,
            )
        )

    return assessment
