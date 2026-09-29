"""
POST /intake — Product Intake / PIP update endpoint.

The endpoint accepts questionnaire answers and merges them into the
existing ProductIntelligenceProfile stored for the supplied session_id.

Important behavior:
- All intake fields are optional.
- Missing fields are NOT guessed or invented.
- A field is updated only when it was explicitly supplied by the caller.
- Enum-like fields are validated at the API boundary.
- The endpoint returns the complete updated PIP.
- Classification remains a separate downstream step.
"""

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from backend.logic.languages import normalize_language_code

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
    """
    Request model for POST /intake.

    session_id is required so the submitted answers can be merged into
    the correct Product Intelligence Profile.

    All other fields are optional because the user may provide only part
    of the questionnaire at a time.
    """

    session_id: str

    # ------------------------------------------------------------------
    # Top-level PIP fields
    # ------------------------------------------------------------------

    jurisdiction: Optional[Literal["india", "international"]] = None
    language: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_language_code(value)

    protection_target: Optional[ProtectionTarget] = None
    objective: Optional[list[Objective]] = None

    # ------------------------------------------------------------------
    # Product fields
    # ------------------------------------------------------------------

    product_name: Optional[str] = None
    composition: Optional[list[CompositionItem]] = None

    intended_use: Optional[
        Literal[
            "therapeutic",
            "food_supplement",
            "cosmetic",
            "agricultural",
            "research",
            "other",
        ]
    ] = None

    classical_basis: Optional[
        Literal["yes", "no", "partial", "unknown"]
    ] = None

    classical_reference: Optional[str] = None

    novelty: Optional[
        Literal[
            "existing",
            "modified",
            "new_combination",
            "unknown",
        ]
    ] = None

    ingredient_sources: Optional[list[IngredientSource]] = None

    biological_origin_known: Optional[
        Literal["yes", "no"]
    ] = None

    biological_origin_region: Optional[str] = None

    development_status: Optional[
        Literal[
            "concept",
            "prototype",
            "developed",
            "marketed",
            "filed_ip",
        ]
    ] = None


def _apply_intake(
    pip: ProductIntelligenceProfile,
    body: IntakeRequest,
) -> None:
    """
    Merge explicitly supplied intake fields into an existing PIP.

    IMPORTANT:
    We use model_fields_set instead of checking whether a value is None.

    This distinguishes:

        field omitted
            -> leave the existing PIP value unchanged

    from:

        field explicitly supplied as null
            -> update the PIP field to None

    This prevents the intake layer from inventing information or
    accidentally overwriting previously collected information.
    """

    # ------------------------------------------------------------------
    # Top-level PIP fields
    # ------------------------------------------------------------------

    if "jurisdiction" in body.model_fields_set:
        pip.jurisdiction = body.jurisdiction

    if "language" in body.model_fields_set:
        pip.language = body.language

    if "protection_target" in body.model_fields_set:
        pip.protection_target = body.protection_target

    if "objective" in body.model_fields_set:
        pip.objective = body.objective

    # ------------------------------------------------------------------
    # Product fields
    # ------------------------------------------------------------------

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


@router.post(
    "/intake",
    response_model=ProductIntelligenceProfile,
)
def intake_endpoint(
    body: IntakeRequest,
    user: dict | None = Depends(optional_current_user),
) -> ProductIntelligenceProfile:
    """
    Update the PIP associated with an existing session.

    Returns:
        The complete updated ProductIntelligenceProfile.

    Errors:
        404 if the supplied session_id does not exist.
        422 if the request contains invalid enum values or malformed
        structured fields.
    """

    ensure_session_access(body.session_id, user)

    pip = get_session(body.session_id)

    if pip is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown session_id. Call POST /session first.",
        )

    _apply_intake(pip, body)

    # Update modification timestamp after applying the new answers.
    from datetime import datetime, timezone

    pip.updated_at = datetime.now(timezone.utc)

    save_session(pip)

    return pip