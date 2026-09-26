"""POST /tkdl/search for the saved, source-derived TKDL archive."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.logic.tkdl_search import assess_prior_art, search_tkdl
from backend.models.tkdl import PriorArtAssessment, TKDLMatchResult
from backend.services.pip_session_store import get_session

router = APIRouter()


class TKDLSearchRequest(BaseModel):
    session_id: str


class TKDLSearchResponse(BaseModel):
    assessment: PriorArtAssessment
    matches: list[TKDLMatchResult]  # all candidate records, for judges to inspect (Scenario 3-style)


@router.post("/tkdl/search", response_model=TKDLSearchResponse)
def tkdl_search_endpoint(body: TKDLSearchRequest) -> TKDLSearchResponse:
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")

    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    return TKDLSearchResponse(assessment=assessment, matches=matches)
