"""
Tests for PIP-01. Run with: pytest -v tests/test_pip.py
"""

import pytest
from pydantic import ValidationError

from backend.models.pip import ProductIntelligenceProfile, CompositionItem, extract_classification_input
from backend.logic.classification import apply_classification_to_pip


def test_full_pip_round_trips_without_data_loss():
    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        language="en",
        product={
            "name": "Ashwagandha+Shatavari Complex",
            "composition": [
                {"ingredient": "Ashwagandha extract", "quantity": "500", "unit": "mg", "is_active": True},
                {"ingredient": "Shatavari extract", "quantity": "250", "unit": "mg", "is_active": True},
            ],
            "intended_use": "therapeutic",
            "classical_basis": "partial",
            "classical_reference": "Ashwagandha Churna",
            "novelty": "modified",
            "ingredient_sources": ["plant"],
            "biological_origin_known": "yes",
            "biological_origin_region": "Rajasthan, India",
            "development_status": "prototype",
        },
        protection_target="formulation",
        objective=["patentability", "regulatory_category"],
        classification={
            "category": "proprietary",
            "reasons": ["Composition reuses known classical ingredients in new ratios."],
            "confidence": "high",
            "unresolved_flags": [],
        },
    )

    dumped = pip.model_dump()
    rehydrated = ProductIntelligenceProfile.model_validate(dumped)

    assert rehydrated.product.composition[0].ingredient == "Ashwagandha extract"
    assert rehydrated.product.composition[1].quantity == "250"
    assert rehydrated.classification.category == "proprietary"
    assert rehydrated.objective == ["patentability", "regulatory_category"]
    assert rehydrated.session_id == pip.session_id  # not regenerated on rehydrate


def test_minimal_pip_does_not_crash():
    """Every field except session_id/language should degrade gracefully to None/empty."""
    pip = ProductIntelligenceProfile()
    assert pip.jurisdiction is None
    assert pip.product.composition == []
    assert pip.objective == []
    assert pip.classification.category is None
    assert pip.language == "en"  # default


def test_partial_pip_only_jurisdiction_and_objective():
    pip = ProductIntelligenceProfile(jurisdiction="india", objective=["trademark"])
    assert pip.jurisdiction == "india"
    assert pip.objective == ["trademark"]
    assert pip.product.name is None


def test_invalid_jurisdiction_rejected():
    with pytest.raises(ValidationError):
        ProductIntelligenceProfile(jurisdiction="mars")


def test_invalid_objective_value_rejected():
    with pytest.raises(ValidationError):
        ProductIntelligenceProfile(objective=["make_it_go_viral"])


def test_invalid_classification_category_rejected():
    with pytest.raises(ValidationError):
        ProductIntelligenceProfile(classification={"category": "definitely_patentable"})


def test_composition_item_defaults_is_active_false():
    item = CompositionItem(ingredient="Starch filler")
    assert item.is_active is False


# --- Adapter to CLS-01's ClassificationInput ---

def test_extract_classification_input_maps_fields_correctly():
    pip = ProductIntelligenceProfile(
        product={
            "composition": [{"ingredient": "X", "quantity": "1", "unit": "g", "is_active": True}],
            "intended_use": "therapeutic",
            "classical_basis": "no",
            "novelty": "new_combination",
            "development_status": "developed",
        },
        objective=["patentability"],
    )
    cls_input = extract_classification_input(pip)
    assert cls_input.intended_use == "therapeutic"
    assert cls_input.classical_basis == "no"
    assert cls_input.novelty == "new_combination"
    assert cls_input.composition[0].ingredient == "X"
    assert cls_input.objective == ["patentability"]
    assert cls_input.has_clinical_safety_evidence is False


# --- CLS-06: a real PIP, fully classified and still round-trip safe ---

def test_apply_classification_to_pip_then_round_trips_clean():
    """The whole point of CLS-06 is a PIP that's complete end-to-end for RAG-03.
    Confirm classifying it doesn't break PIP-01's own round-trip guarantee."""
    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        product={
            "composition": [{"ingredient": "Ashwagandha extract", "quantity": "500", "unit": "mg", "is_active": True}],
            "intended_use": "therapeutic",
            "classical_basis": "partial",
            "novelty": "modified",
            "development_status": "prototype",
        },
        objective=["patentability"],
    )

    apply_classification_to_pip(pip)

    dumped = pip.model_dump()
    rehydrated = ProductIntelligenceProfile.model_validate(dumped)

    assert rehydrated.classification.category == pip.classification.category
    assert rehydrated.classification.confidence == pip.classification.confidence
    assert rehydrated.session_id == pip.session_id