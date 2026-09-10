"""
Integration test: proves the PIP -> classify -> route chain works end to end,
entirely offline (no corpus, no LLM, no DB needed). This is the logic backbone
of the "vertical slice" the Execution Board is building toward.
"""

from backend.models.pip import ProductIntelligenceProfile, extract_classification_input
from backend.logic.classification import classify
from backend.logic.routing import route


def test_full_slice_ashwagandha_shatavari_example():
    """The exact example product used in the build spec's own demo script (§18)."""
    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        product={
            "name": "Ashwagandha+Shatavari Complex",
            "composition": [
                {"ingredient": "Ashwagandha extract", "quantity": "500", "unit": "mg", "is_active": True},
                {"ingredient": "Shatavari extract", "quantity": "250", "unit": "mg", "is_active": True},
            ],
            "intended_use": "therapeutic",
            "classical_basis": "partial",
            "novelty": "modified",
            "development_status": "prototype",
        },
        objective=["patentability"],
    )

    cls_input = extract_classification_input(pip)
    result = classify(cls_input)
    assert result.category == "proprietary"

    routing = route(pip.jurisdiction, result.category, pip.objective)
    assert "patent_law" in routing.legal_regimes
    assert "biodiversity_abs" in routing.legal_regimes
    # Proprietary's patent_law filter must be unrestricted (includes Patents Rules,
    # which the real corpus tags as legal_regime="patent_law", document_type="rule")
    patent_filter = next(f for f in routing.regime_filters if f.legal_regime == "patent_law")
    assert patent_filter.document_types is None
