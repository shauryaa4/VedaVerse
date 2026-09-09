"""
Tests for CLS-01. Run with: pytest -v tests/test_classification.py

Covers the edge cases the build spec explicitly calls out in section 4:
- empty composition
- composition with only inactive excipients
- classical_basis=yes but user also says "modified"
- multi-purpose product ambiguity (documented limitation, see note below)
"""

import pytest
from backend.models.classification_input import ClassificationInput, CompositionItem
from backend.logic.classification import classify


def test_classical_generic_happy_path():
    pip = ClassificationInput(
        classical_basis="yes",
        novelty="existing",
        classical_reference="Ashwagandha Churna, Sharangadhara Samhita",
        intended_use="therapeutic",
        composition=[CompositionItem(ingredient="Ashwagandha root powder", quantity="3", unit="g", is_active=True)],
    )
    result = classify(pip)
    assert result.category == "classical_generic"
    assert result.confidence in ("high", "medium")


def test_nutraceutical():
    pip = ClassificationInput(intended_use="food_supplement", objective=["regulatory_category"])
    result = classify(pip)
    assert result.category == "nutraceutical_ayurveda_aahar"


def test_cosmetic():
    pip = ClassificationInput(intended_use="cosmetic")
    result = classify(pip)
    assert result.category == "cosmetic"


def test_proprietary_minor_modification():
    pip = ClassificationInput(
        classical_basis="partial",
        novelty="modified",
        intended_use="therapeutic",
        development_status="prototype",
        composition=[CompositionItem(ingredient="Ashwagandha extract", quantity="500", unit="mg", is_active=True)],
    )
    result = classify(pip)
    assert result.category == "proprietary"


def test_new_drug_novel_combination():
    pip = ClassificationInput(
        classical_basis="no",
        novelty="new_combination",
        intended_use="therapeutic",
        development_status="developed",
        composition=[
            CompositionItem(ingredient="Ashwagandha extract", quantity="500", unit="mg", is_active=True),
            CompositionItem(ingredient="Novel synthetic adjuvant", quantity="50", unit="mg", is_active=True),
        ],
    )
    result = classify(pip)
    assert result.category == "new_drug"


def test_phytopharmaceutical_single_standardized_extract():
    pip = ClassificationInput(
        intended_use="therapeutic",
        classical_basis="no",
        novelty="modified",  # deliberately NOT matching rule 4 (needs development_status too)
        development_status="marketed",  # excluded from rule 4's status list on purpose
        composition=[CompositionItem(ingredient="Withanolide extract", quantity="10", unit="mg", is_active=True)],
    )
    result = classify(pip)
    assert result.category == "phytopharmaceutical"
    assert "phytopharmaceutical_rule_is_heuristic_confirm_with_team" in result.unresolved_flags


# --- Explicit edge cases from build spec §4 ---

def test_edge_empty_composition_does_not_crash():
    pip = ClassificationInput(intended_use="therapeutic")
    result = classify(pip)
    assert result.category == "unresolved"
    assert result.confidence == "low"


def test_edge_only_inactive_excipients():
    pip = ClassificationInput(
        intended_use="therapeutic",
        classical_basis="no",
        novelty="modified",
        development_status="concept",
        composition=[CompositionItem(ingredient="Starch filler", is_active=False)],
    )
    result = classify(pip)
    # No active ingredients -> rule 4 still fires (it doesn't check composition),
    # rule 5 (phytopharma) correctly does NOT fire since active_items is empty.
    assert result.category == "proprietary"


def test_edge_classical_basis_yes_but_modified_is_not_classical_generic():
    """
    classical_basis='yes' but novelty='modified' should NOT hit the Classical/Generic
    rule (that rule requires novelty == 'existing'). It should fall through toward
    Proprietary/New Drug instead. This is the explicit edge case from spec §4.
    """
    pip = ClassificationInput(
        classical_basis="yes",
        novelty="modified",
        classical_reference="Ashwagandha Churna",
        intended_use="therapeutic",
        development_status="prototype",
    )
    result = classify(pip)
    assert result.category != "classical_generic"


def test_edge_multi_purpose_product_not_modeled_yet():
    """
    KNOWN GAP, DO NOT SILENTLY FIX: the frozen PIP schema (§2) only allows a single
    `intended_use` value. The build spec's edge case ("multi-purpose product, e.g.
    both therapeutic and cosmetic claims — flag ambiguity, don't silently pick one")
    can't actually be represented with the current schema. This test documents that
    the classifier can only ever see one intended_use and will classify on that alone.
    Raise this with the team before Day 2 — either the schema needs an `additional_uses`
    field, or intake needs to force a single choice with an explicit warning to the user.
    """
    pip = ClassificationInput(intended_use="cosmetic")
    result = classify(pip)
    assert result.category == "cosmetic"  # correct given current schema, but see docstring


def test_confidence_high_when_key_fields_known():
    pip = ClassificationInput(
        classical_basis="no",
        novelty="modified",
        intended_use="therapeutic",
        development_status="prototype",
        composition=[CompositionItem(ingredient="X", quantity="1", unit="g", is_active=True)],
    )
    result = classify(pip)
    assert result.confidence == "high"


def test_confidence_low_when_unresolved():
    pip = ClassificationInput()
    result = classify(pip)
    assert result.confidence == "low"
