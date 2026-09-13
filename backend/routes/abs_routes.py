"""
NEW FILE — POST /abs/assess.

Same pattern as routes/tkdl.py and routes/classify.py: resolve a session_id
to a stored PIP, call the existing (pure, deterministic) logic, return the
result. All real logic lives in backend/logic/abs_helper.py — this file
adds no logic of its own.

Per build spec section 20, this never claims to contact the NBA, any SBB,
or any other government system — see ABSAssessment.disclaimer.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.logic.abs_helper import assess_abs
from backend.models.abs_models import ABSAssessment
from backend.services.pip_session_store import get_session

router = APIRouter()


class ABSAssessRequest(BaseModel):
    session_id: str


@router.post("/abs/assess", response_model=ABSAssessment)
def abs_assess_endpoint(body: ABSAssessRequest) -> ABSAssessment:
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")

    return assess_abs(pip)