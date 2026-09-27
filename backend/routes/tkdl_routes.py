"""POST /tkdl/search for the saved, source-derived TKDL archive."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.logic.tkdl_search import assess_prior_art, search_tkdl
from backend.models.tkdl import PriorArtAssessment, TKDLMatchResult
from backend.services.pip_session_store import get_session
from backend.routes.auth import ensure_session_access, optional_current_user
from backend.services.account_store import get_case_owner, save_account_assessment

router = APIRouter()


class TKDLSearchRequest(BaseModel):
    session_id: str


class TKDLSearchResponse(BaseModel):
    assessment: PriorArtAssessment
    matches: list[TKDLMatchResult]  # all candidate records, for judges to inspect (Scenario 3-style)


@router.post("/tkdl/search", response_model=TKDLSearchResponse)
def tkdl_search_endpoint(body: TKDLSearchRequest, user: dict | None = Depends(optional_current_user)) -> TKDLSearchResponse:
    ensure_session_access(body.session_id, user)
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")

    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    result = TKDLSearchResponse(assessment=assessment, matches=matches)
    if user and get_case_owner(body.session_id) == user["id"]:
        save_account_assessment(body.session_id, "tkdl", result.model_dump(mode="json"))
    return result
