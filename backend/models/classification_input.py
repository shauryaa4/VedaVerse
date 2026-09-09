"""
Minimal input shape for the classification engine (CLS-01).

WHY THIS FILE EXISTS SEPARATELY FROM THE FULL PIP MODEL:
Per the build spec, CLS-01 doesn't need to wait for PIP-01 to be fully
merged — it only needs the *shape* of the fields relevant to classification,
which are already frozen in build spec section 2. This file defines just
those fields as a standalone Pydantic model so you can build and test the
decision tree in total isolation today.

WHEN PIP-01 LANDS FOR REAL:
Whoever builds the full Product Intelligence Profile model should either:
  (a) make the full PIP model include all these same field names/types, so
      you can pass a full PIP object straight into classify() unchanged, or
  (b) add a small adapter function that extracts a ClassificationInput from
      a full PIP object.
Either way, DO NOT change the field names below without checking build spec
section 2 first — classifier logic depends on these exact names/values.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class CompositionItem(BaseModel):
    ingredient: str
    quantity: Optional[str] = None
    unit: Optional[str] = None
    is_active: bool = False


class ClassificationInput(BaseModel):
    # --- product basics ---
    composition: list[CompositionItem] = Field(default_factory=list)
    intended_use: Optional[
        Literal["therapeutic", "food_supplement", "cosmetic", "agricultural", "research", "other"]
    ] = None
    classical_basis: Optional[Literal["yes", "no", "partial", "unknown"]] = None
    classical_reference: Optional[str] = None
    novelty: Optional[Literal["existing", "modified", "new_combination", "unknown"]] = None
    development_status: Optional[
        Literal["concept", "prototype", "developed", "marketed", "filed_ip"]
    ] = None

    # --- what the user is trying to find out (affects the nutraceutical branch) ---
    objective: list[
        Literal[
            "patentability",
            "regulatory_category",
            "trademark",
            "prior_art",
            "abs_relevance",
            "legal_pathway",
            "general",
        ]
    ] = Field(default_factory=list)

    # --- explicit safety-evidence flag, needed to distinguish Proprietary vs New Drug ---
    # Build spec §4 says the Proprietary/New Drug split assumes "no clinical/safety
    # evidence claimed." There's no field for this anywhere else in the frozen PIP
    # schema (§2) — flag this gap to the team; for now default to False (assume no
    # evidence claimed) so the branch isn't silently skipped.
    has_clinical_safety_evidence: bool = False
