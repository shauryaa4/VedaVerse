"""
Tests for TKDL-02. Run with: pytest -v tests/test_tkdl.py

Covers the three cases from the team's TKDL research notes:
- Case 1: exact ingredient match           -> risk_level == "high"
- Case 2: traditional match + extra add-on -> risk_level == "medium", flagged
- Case 3: same ingredients + declared novelty -> risk stays "high" on the
  ingredient axis, but potential_novel_features is populated separately
- No overlap at all                        -> risk_level == "none" (abstain-style)
"""

from backend.logic.tkdl_search import assess_prior_art, search_tkdl
from backend.models.pip import CompositionItem, Product, ProductIntelligenceProfile


def _pip(composition_strings: list[str], novelty=None) -> ProductIntelligenceProfile:
    return ProductIntelligenceProfile(
        product=Product(
            composition=[CompositionItem(ingredient=s, is_active=True) for s in composition_strings],
            novelty=novelty,
        )
    )


def test_exact_match_is_high_risk_case_1():
    pip = _pip(["Mercury", "Sulphur", "Aloe", "Piper longum", "Terminalia chebula",
                "Anacyclus pyrethrum", "Citrullus colocynthis"])
    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    assert assessment.risk_level == "high"
    assert assessment.closest_record.record_id == "TKDL-BP-1025"


def test_single_herb_matches_ashwagandha_record():
    pip = _pip(["Ashwagandha root powder"])
    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    assert assessment.risk_level == "high"
    assert assessment.closest_record.record_id == "TKDL-AS-0007"


def test_traditional_match_plus_extra_ingredient_is_medium_case_2():
    pip = _pip(["Terminalia chebula", "Terminalia bellirica", "Emblica officinalis", "Ginger extract"])
    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    assert assessment.closest_record.record_id == "TKDL-TR-0014"
    assert assessment.risk_level == "medium"
    assert any("Ginger" in d for d in assessment.what_appears_different)
    assert any("technical improvement" in f for f in assessment.potential_novel_features)


def test_same_ingredients_with_declared_novelty_flags_separately_case_3():
    pip = _pip(["Ashwagandha root powder"], novelty="modified")
    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    # Ingredient-level risk stays high (core formulation is still prior art)...
    assert assessment.risk_level == "high"
    # ...but the process/novelty claim is flagged as a SEPARATE question.
    assert any("modified" in f for f in assessment.potential_novel_features)


def test_no_overlap_returns_none_risk():
    pip = _pip(["Synthetic Compound XJ-9"])
    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    assert matches == []
    assert assessment.risk_level == "none"
    assert assessment.closest_record is None


def test_empty_composition_returns_no_matches():
    pip = _pip([])
    matches = search_tkdl(pip.product.composition)
    assert matches == []


def test_every_response_is_flagged_mock():
    pip = _pip(["Ashwagandha root powder"])
    matches = search_tkdl(pip.product.composition)
    assessment = assess_prior_art(pip, matches)

    assert assessment.mock is True
    for m in matches:
        assert m.record.is_mock is True
