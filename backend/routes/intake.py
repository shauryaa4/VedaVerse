"""
NEW FILE — POST /intake.

Per API contract (build spec §13): "POST /intake → submit questionnaire
answers, returns updated Product Intelligence Profile." Fields accepted
here are a flattened view of the questionnaire in build spec §3, mapped
onto PIP-01's nested product.* shape (see IntakeRequest -> _apply_intake
below).

SCOPE NOTE (intentional): this endpoint does plain field merging only. It
does NOT implement the progressive-disclosure / conditional-question
gating described in §3 and tracked separately as PIP-04
(backend/logic/intake_gating.py, currently "NOT YET BUILT" per the repo
tree notes) — that's a distinct task with its own owner. All fields here
are optional and merged in as given; nothing is required or skipped based
on protection_target. Whoever picks up PIP-04 can layer gating on top of
this endpoint (or the frontend can simply choose not to send fields for
skipped questions) without needing this file to change.

Every field the person supplies is treated as authoritative and simply
written into the stored PIP — no re-asking, per the "no module re-asks"
rule in build spec §2.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.models.pip import (
    CompositionItem,
    IngredientSource,
    Objective,
    ProductIntelligenceProfile,
    ProtectionTarget,
)
from backend.services.pip_session_store import get_session, save_session
from backend.routes.auth import ensure_session_access, optional_current_user

router = APIRouter()


class IntakeRequest(BaseModel):
    session_id: str

    # --- top-level PIP fields (§3 Q1, Q2, Q9) ---
    jurisdiction: Optional[str] = None  # "india" | "international"
    language: Optional[str] = None  # "en" | "hi"
    protection_target: Optional[ProtectionTarget] = None
    objective: Optional[list[Objective]] = None

    # --- product.* fields (§3 Q3-Q8) ---
    product_name: Optional[str] = None
    composition: Optional[list[CompositionItem]] = None
    intended_use: Optional[str] = None
    classical_basis: Optional[str] = None
    classical_reference: Optional[str] = None
    novelty: Optional[str] = None
    ingredient_sources: Optional[list[IngredientSource]] = None
    biological_origin_known: Optional[str] = None
    biological_origin_region: Optional[str] = None
    development_status: Optional[str] = None


def _apply_intake(pip: ProductIntelligenceProfile, body: IntakeRequest) -> None:
    """Mutates pip in place, writing only the fields the caller actually sent."""

    if "jurisdiction" in body.model_fields_set:
        pip.jurisdiction = body.jurisdiction
    if "language" in body.model_fields_set:
        pip.language = body.language
    if "protection_target" in body.model_fields_set:
        pip.protection_target = body.protection_target
    if "objective" in body.model_fields_set:
        pip.objective = body.objective

    if "product_name" in body.model_fields_set:
        pip.product.name = body.product_name
    if "composition" in body.model_fields_set:
        pip.product.composition = body.composition
    if "intended_use" in body.model_fields_set:
        pip.product.intended_use = body.intended_use
    if "classical_basis" in body.model_fields_set:
        pip.product.classical_basis = body.classical_basis
    if "classical_reference" in body.model_fields_set:
        pip.product.classical_reference = body.classical_reference
    if "novelty" in body.model_fields_set:
        pip.product.novelty = body.novelty
    if "ingredient_sources" in body.model_fields_set:
        pip.product.ingredient_sources = body.ingredient_sources
    if "biological_origin_known" in body.model_fields_set:
        pip.product.biological_origin_known = body.biological_origin_known
    if "biological_origin_region" in body.model_fields_set:
        pip.product.biological_origin_region = body.biological_origin_region
    if "development_status" in body.model_fields_set:
        pip.product.development_status = body.development_status


@router.post("/intake", response_model=ProductIntelligenceProfile)
def intake_endpoint(body: IntakeRequest, user: dict | None = Depends(optional_current_user)) -> ProductIntelligenceProfile:
    ensure_session_access(body.session_id, user)
    pip = get_session(body.session_id)
    if pip is None:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call POST /session first.")

    _apply_intake(pip, body)

    from datetime import datetime, timezone

    pip.updated_at = datetime.now(timezone.utc)

    save_session(pip)
    return pip
