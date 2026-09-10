"""
PIP-01 — Product Intelligence Profile.

Implements build spec section 2 EXACTLY. Do not add, rename, or remove
fields without re-checking that section first and syncing with the team —
every downstream module (classifier, router, RAG filter, TKDL mock, ABS
mock) reads from this object only, per the spec's own rule.

Nested structure matches the spec's JSON shape (product.*, classification.*),
which is why this looks different from CLS-01's flatter ClassificationInput —
see extract_classification_input() below for the adapter between the two.
"""

import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.logic.classification import Category
from backend.models.classification_input import ClassificationInput
from backend.models.classification_input import CompositionItem as ClassificationCompositionItem

IngredientSource = Literal["plant", "animal", "mineral", "microbial", "synthetic"]

Objective = Literal[
    "patentability",
    "regulatory_category",
    "trademark",
    "prior_art",
    "abs_relevance",
    "legal_pathway",
    "general",
]

ProtectionTarget = Literal[
    "formulation", "brand", "process", "biological_resource", "traditional_knowledge", "unsure"
]


class CompositionItem(BaseModel):
    ingredient: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    is_active: bool = False


class Product(BaseModel):
    name: Optional[str] = None
    composition: list[CompositionItem] = Field(default_factory=list)
    intended_use: Optional[
        Literal["therapeutic", "food_supplement", "cosmetic", "agricultural", "research", "other"]
    ] = None
    classical_basis: Optional[Literal["yes", "no", "partial", "unknown"]] = None
    classical_reference: Optional[str] = None
    novelty: Optional[Literal["existing", "modified", "new_combination", "unknown"]] = None
    ingredient_sources: list[IngredientSource] = Field(default_factory=list)
    biological_origin_known: Optional[Literal["yes", "no"]] = None
    biological_origin_region: Optional[str] = None
    development_status: Optional[
        Literal["concept", "prototype", "developed", "marketed", "filed_ip"]
    ] = None


class Classification(BaseModel):
    # NOTE: reuses Category from CLS-01 (backend.logic.classification) as the single
    # source of truth for valid category names, plus "unresolved" which CLS-01 can return.
    category: Optional[Category] = None
    reasons: list[str] = Field(default_factory=list)
    confidence: Optional[Literal["high", "medium", "low"]] = None
    unresolved_flags: list[str] = Field(default_factory=list)


class ProductIntelligenceProfile(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    jurisdiction: Optional[Literal["india", "international"]] = None
    language: Literal["en", "hi"] = "en"

    product: Product = Field(default_factory=Product)
    protection_target: Optional[ProtectionTarget] = None
    objective: list[Objective] = Field(default_factory=list)
    classification: Classification = Field(default_factory=Classification)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def extract_classification_input(pip: ProductIntelligenceProfile) -> ClassificationInput:
    """
    Adapter between PIP-01's nested shape and CLS-01's flatter ClassificationInput.

    KNOWN DUPLICATION: CompositionItem is defined separately in this file and in
    classification_input.py, since CLS-01 was built before PIP-01 existed. They
    have identical fields today. Worth consolidating into one shared model later
    (low priority — not worth a risky refactor of already-tested/committed code
    this close to the deadline).

    KNOWN GAP (same one flagged in classification_input.py): PIP has no field for
    "has_clinical_safety_evidence", so it always defaults to False here. Raise
    with the team if the Proprietary/New Drug split needs it to be a real signal.
    """
    p = pip.product
    return ClassificationInput(
        composition=[
            ClassificationCompositionItem(
                ingredient=c.ingredient, quantity=c.quantity, unit=c.unit, is_active=c.is_active
            )
            for c in p.composition
        ],
        intended_use=p.intended_use,
        classical_basis=p.classical_basis,
        classical_reference=p.classical_reference,
        novelty=p.novelty,
        development_status=p.development_status,
        objective=list(pip.objective),
        has_clinical_safety_evidence=False,
    )
