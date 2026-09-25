"""
POST /abs/assess — ABS Fact-Driven Decision Support Endpoint.

Resolves a session_id to a stored ProductIntelligenceProfile, attaches any
optional ABSFactProfile provided in the request body, executes the deterministic
17-step fact-driven ABS pathway engine, and returns a detailed ABSAssessment.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.logic.abs_helper import assess_abs
from backend.models.abs_models import ABSAssessment, ABSFactProfile
from backend.services.pip_session_store import get_session, save_session

router = APIRouter()


class ABSAssessRequest(BaseModel):
    session_id: str
    abs_facts: Optional[ABSFactProfile] = None


@router.post("/abs/assess", response_model=ABSAssessment)
def abs_assess_endpoint(body: ABSAssessRequest) -> ABSAssessment:
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")

    if body.abs_facts is not None:
        pip.abs_facts = body.abs_facts
        save_session(pip)

    return assess_abs(pip)