"""
ABS API routes.

Keeps the ABS decision logic in backend.logic.abs_helper and exposes the
FastAPI endpoint expected by backend.main. ABS-03 optionally grounds each
reasoning line against the shared biodiversity_abs Chroma corpus.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.logic.abs_helper import assess_abs, ground_abs_citations
from backend.models.abs_models import ABSAssessment
from backend.services.pip_session_store import get_session
from backend.routes.auth import ensure_session_access, optional_current_user
from backend.services.account_store import get_case_owner, save_account_assessment
from backend.services.vector_store import get_default_collection

router = APIRouter()


class ABSAssessRequest(BaseModel):
    session_id: str


@router.post("/abs/assess", response_model=ABSAssessment)
def abs_assess_endpoint(
    body: ABSAssessRequest,
    user: dict | None = Depends(optional_current_user),
) -> ABSAssessment:
    ensure_session_access(body.session_id, user)

    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown session_id. Call POST /session first.",
        )

    # Keep the deterministic ABS assessment pure. Grounding is an additive,
    # optional backend step and must never make /abs/assess fail.
    result = assess_abs(pip)

    try:
        collection = get_default_collection()
        result = ground_abs_citations(result, collection)
    except Exception as exc:
        print(f"[abs_assess] citation grounding failed: {exc!r}")

    if user and get_case_owner(body.session_id) == user["id"]:
        save_account_assessment(
            body.session_id,
            "abs",
            result.model_dump(mode="json"),
        )

    return result
