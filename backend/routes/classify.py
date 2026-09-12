"""
NEW FILE — POST /classify.

Per API contract (build spec §13): "POST /classify → runs rule engine on
PIP, returns {category, reasons[], confidence}." All the actual logic
already exists and is untouched by this file: CLS-01's classify() and its
apply_classification_to_pip() adapter, both in
backend/logic/classification.py. This route is deliberately thin (same
pattern as routes/citation.py and routes/query.py) — it only resolves a
session_id to a stored PIP, calls the existing classifier, persists the
result back onto that PIP, and returns the classification.

Never presents this as an LLM guess — build spec §4 is explicit that this
is a deterministic rule engine, and CLS-01's own docstring repeats that.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.logic.classification import Category, Confidence, apply_classification_to_pip
from backend.services.pip_session_store import get_session, save_session

router = APIRouter()


class ClassifyRequest(BaseModel):
    session_id: str


class ClassifyResponse(BaseModel):
    category: Category
    reasons: list[str]
    confidence: Confidence
    unresolved_flags: list[str] = []


@router.post("/classify", response_model=ClassifyResponse)
def classify_endpoint(body: ClassifyRequest) -> ClassifyResponse:
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")

    pip = apply_classification_to_pip(pip)
    save_session(pip)

    c = pip.classification
    return ClassifyResponse(
        category=c.category,
        reasons=c.reasons,
        confidence=c.confidence,
        unresolved_flags=c.unresolved_flags,
    )
