"""
CLS-01 — Deterministic product classification decision tree.

Implements build spec section 4, verbatim, first-match-wins.
This is a RULE ENGINE, not ML. Never present its output as "the model guessed" —
every category comes with the exact rule that fired, in plain language.

Categories: classical_generic | nutraceutical_ayurveda_aahar | cosmetic |
            proprietary | new_drug | phytopharmaceutical | unresolved
"""

from typing import TYPE_CHECKING, Literal
from datetime import datetime, timezone
from pydantic import BaseModel

from backend.models.classification_input import ClassificationInput

# CLS-06: only imported for type checkers, never at runtime. pip.py imports
# Category from THIS module at module load time, so this module importing
# pip.py at module load time would be a circular import. apply_classification_to_pip()
# below does the real import lazily, inside the function body, once both
# modules are already fully loaded.
if TYPE_CHECKING:
    from backend.models.pip import ProductIntelligenceProfile

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


def apply_classification_to_pip(pip: "ProductIntelligenceProfile") -> "ProductIntelligenceProfile":
    """
    CLS-06 — Runs classify() against pip's own product data and writes the
    result into pip.classification IN PLACE, then returns the same pip object
    (so callers can do either `apply_classification_to_pip(pip)` or
    `pip = apply_classification_to_pip(pip)`).

    Before this function existed, ProductIntelligenceProfile.classification
    was created empty by PIP-01 and nothing ever filled it in — classify()
    only ever ran against a standalone ClassificationInput in tests. RAG-03
    needs pip.classification.category to call route(), so this is the piece
    that makes a PIP object actually complete end-to-end.

    Local imports below are required, not a style choice: backend.models.pip
    imports Category from this module at module load time, so this module
    cannot import backend.models.pip at module load time without a circular
    import. Importing inside the function body works because by the time
    this function is actually CALLED, both modules have already finished
    loading.
    """
    from backend.models.pip import Classification, extract_classification_input

    classification_input = extract_classification_input(pip)
    result = classify(classification_input)

    pip.classification = Classification(
        category=result.category,
        reasons=result.reasons,
        confidence=result.confidence,
        unresolved_flags=result.unresolved_flags,
    )
    pip.updated_at = datetime.now(timezone.utc)
    return pip


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