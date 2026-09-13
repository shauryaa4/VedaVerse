"""
NEW FILE — POST /tkdl/search.

Same pattern as routes/classify.py: resolve a session_id to a stored PIP,
call the existing (pure, deterministic) logic, return the result. All real
logic lives in backend/logic/tkdl_search.py and the mock dataset lives in
backend/data/tkdl_mock_records.py — this file adds no logic of its own.

Per build spec section 19, every response is explicitly and permanently
mock=True; there is no code path in this route that can return a live-data
result, because there is no live TKDL client anywhere in this codebase.
"""

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
    mock: bool = True


@router.post("/tkdl/search", response_model=TKDLSearchResponse)
def tkdl_search_endpoint(body: TKDLSearchRequest) -> TKDLSearchResponse:
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")

    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    return TKDLSearchResponse(assessment=assessment, matches=matches)
