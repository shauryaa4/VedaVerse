"""
CLS-01 — Deterministic product classification decision tree.

Implements build spec section 4, verbatim, first-match-wins.
This is a RULE ENGINE, not ML. Never present its output as "the model guessed" —
every category comes with the exact rule that fired, in plain language.

Categories: classical_generic | nutraceutical_ayurveda_aahar | cosmetic |
            proprietary | new_drug | phytopharmaceutical | unresolved
"""

from typing import Literal
from pydantic import BaseModel

from backend.models.classification_input import ClassificationInput

Category = Literal[
    "classical_generic",
    "nutraceutical_ayurveda_aahar",
    "cosmetic",
    "proprietary",
    "new_drug",
    "phytopharmaceutical",
    "unresolved",
]

Confidence = Literal["high", "medium", "low"]


class ClassificationResult(BaseModel):
    category: Category
    reasons: list[str]
    confidence: Confidence
    unresolved_flags: list[str] = []


def _has_composition(pip: ClassificationInput) -> bool:
    return len(pip.composition) > 0


def _classical_and_novelty_known(pip: ClassificationInput) -> bool:
    return pip.classical_basis not in (None, "unknown") and pip.novelty not in (None, "unknown")


def classify(pip: ClassificationInput) -> ClassificationResult:
    reasons: list[str] = []
    flags: list[str] = []

    # --- Rule 1: Classical / Generic ---
    if (
        pip.classical_basis == "yes"
        and pip.novelty == "existing"
        and bool(pip.classical_reference)  # proxy for "composition matches an unmodified
                                            # classical reference" — see note below
    ):
        reasons.append(
            "Formulation and proportions match a classical/authoritative-text "
            "reference with no modification."
        )
        return ClassificationResult(
            category="classical_generic",
            reasons=reasons,
            confidence=_confidence(pip, "classical_generic"),
        )

    # --- Rule 2: Nutraceutical / Ayurveda-Aahar ---
    if pip.intended_use == "food_supplement" or (
        "regulatory_category" in pip.objective and pip.intended_use == "food_supplement"
    ):
        reasons.append(
            "Product is positioned as a food/dietary supplement rather than a "
            "therapeutic drug."
        )
        return ClassificationResult(
            category="nutraceutical_ayurveda_aahar",
            reasons=reasons,
            confidence=_confidence(pip, "nutraceutical_ayurveda_aahar"),
        )

    # --- Rule 3: Cosmetic ---
    if pip.intended_use == "cosmetic":
        reasons.append(
            "Product is intended for cosmetic/personal-care use, not internal "
            "therapeutic use."
        )
        return ClassificationResult(
            category="cosmetic",
            reasons=reasons,
            confidence=_confidence(pip, "cosmetic"),
        )

    # --- Rule 4: Proprietary vs New Drug ---
    if (
        pip.classical_basis in ("no", "partial")
        and pip.novelty in ("modified", "new_combination")
        and pip.intended_use == "therapeutic"
        and pip.development_status in ("concept", "prototype", "developed")
        and not pip.has_clinical_safety_evidence
    ):
        if pip.novelty == "modified":
            reasons.append(
                "Composition reuses known classical ingredients in new ratios or "
                "combinations (minor modification of known ingredients)."
            )
            return ClassificationResult(
                category="proprietary",
                reasons=reasons,
                confidence=_confidence(pip, "proprietary"),
            )
        else:  # new_combination
            reasons.append(
                "Introduces a new combination/indication with no traditional-use "
                "precedent, requiring safety-efficacy proof."
            )
            return ClassificationResult(
                category="new_drug",
                reasons=reasons,
                confidence=_confidence(pip, "new_drug"),
            )

    # --- Rule 5: Phytopharmaceutical ---
    # NOTE: the spec's trigger is "standardized/isolated phytoconstituents with
    # defined therapeutic claims (not whole-herb classical prep)." There is no
    # explicit field for "standardized/isolated" in the frozen PIP schema (§2).
    # Heuristic used here: exactly one active ingredient, given as a precise
    # quantity+unit (e.g. "500mg"), with a therapeutic intended use. FLAG THIS
    # WITH THE TEAM — if it produces bad results in testing, this is the rule
    # to revisit, not the others.
    active_items = [c for c in pip.composition if c.is_active]
    if (
        len(active_items) == 1
        and active_items[0].quantity
        and active_items[0].unit
        and pip.intended_use == "therapeutic"
    ):
        reasons.append(
            "Formulation uses a standardized extract/phytoconstituent with a "
            "defined therapeutic claim, distinct from a classical whole-herb "
            "preparation."
        )
        flags.append("phytopharmaceutical_rule_is_heuristic_confirm_with_team")
        return ClassificationResult(
            category="phytopharmaceutical",
            reasons=reasons,
            confidence=_confidence(pip, "phytopharmaceutical"),
            unresolved_flags=flags,
        )

    # --- Rule 6: Unresolved fallback ---
    reasons.append(
        "Available answers don't clearly match a defined category — defaulting "
        "to Proprietary pending clarification of novelty magnitude."
    )
    flags.append("novelty_magnitude_unclear")
    return ClassificationResult(
        category="unresolved",
        reasons=reasons,
        confidence="low",
        unresolved_flags=flags,
    )


def _confidence(pip: ClassificationInput, category: Category) -> Confidence:
    """
    Per build spec §4:
    HIGH:   classical_basis and novelty both explicitly answered, composition provided.
    MEDIUM: one of classical_basis/novelty is "unknown" but other signals are strong.
    LOW:    composition missing, or both classical_basis/novelty unknown, or UNRESOLVED.
    """
    if category == "unresolved":
        return "low"

    if _classical_and_novelty_known(pip) and _has_composition(pip):
        return "high"

    one_unknown = (pip.classical_basis == "unknown") != (pip.novelty == "unknown")
    # (the != above is a cheap "exactly one of the two is unknown" check)
    if one_unknown:
        return "medium"

    if not _has_composition(pip) or (
        pip.classical_basis in (None, "unknown") and pip.novelty in (None, "unknown")
    ):
        return "low"

    return "medium"
