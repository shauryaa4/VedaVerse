"""
Tests for ABS-02 / Phase 4 PIP -> ABS integration.

These tests verify:
- Existing ABS rule branches continue to work.
- Known PIP facts reach the deterministic ABS engine.
- Known facts are not redundantly requested as missing information.
- Missing PIP facts remain missing/unknown rather than being guessed.
- PIP objectives are correctly consumed by the ABS engine.
"""

from backend.logic.abs_helper import assess_abs
from backend.logic.abs_engine import build_fact_profile_from_pip
from backend.models.pip import ProductIntelligenceProfile, Product


def _pip(**product_kwargs) -> ProductIntelligenceProfile:
    return ProductIntelligenceProfile(product=Product(**product_kwargs))


def test_no_ingredient_sources_is_possible():
    result = assess_abs(_pip())

    assert result.relevance == "possible"
    assert result.ip_filing_flag is False


def test_mineral_only_is_not_applicable():
    result = assess_abs(
        _pip(ingredient_sources=["mineral", "synthetic"])
    )

    assert result.relevance == "not_applicable"


def test_biological_origin_unknown_is_possible():
    result = assess_abs(
        _pip(
            ingredient_sources=["plant"],
            biological_origin_known="no",
        )
    )

    assert result.relevance == "possible"


def test_india_origin_is_likely():
    result = assess_abs(
        _pip(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Western Ghats, India",
        )
    )

    assert result.relevance == "likely"
    assert result.applicable_authority_guidance


def test_non_india_origin_is_unlikely():
    result = assess_abs(
        _pip(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Sourced from outside India (Brazil)",
        )
    )

    assert result.relevance == "unlikely"


def test_section6_ip_filing_flag_fires_independently_of_relevance():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
    )
    pip.objective = ["patentability"]

    result = assess_abs(pip)

    assert result.relevance == "likely"
    assert result.ip_filing_flag is True
    assert "Section 6" in result.ip_filing_note


def test_ip_filing_flag_does_not_fire_without_ip_objective():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
    )

    result = assess_abs(pip)

    assert result.ip_filing_flag is False


def test_ambiguous_region_is_possible():
    result = assess_abs(
        _pip(
            ingredient_sources=["animal"],
            biological_origin_known="yes",
            biological_origin_region="unclear",
        )
    )

    assert result.relevance == "possible"


# ---------------------------------------------------------------------------
# Phase 4 — PIP -> ABS integration tests
# ---------------------------------------------------------------------------

def test_pip_facts_are_mapped_into_abs_fact_profile():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
        classical_basis="yes",
        classical_reference="Ayurvedic Pharmacopoeia",
        development_status="developed",
    )
    pip.objective = ["patentability"]

    facts = build_fact_profile_from_pip(pip)

    # Biological resource facts from PIP
    assert facts.resource.biological_resource_involved is True
    assert facts.resource.resource_type == "plant"

    # Origin facts from PIP
    assert facts.resource.origin_status == "india"
    assert facts.resource.country_of_origin == "India"
    assert facts.resource.geographical_location == "Kerala, India"

    # Classical/codified TK facts from PIP
    assert facts.tk.tk_codified is True
    assert facts.tk.tk_type == "codified"
    assert facts.tk.tk_source == "Ayurvedic Pharmacopoeia"

    # Objective/development facts from PIP
    assert "ipr_application" in facts.activity.activities
    assert "commercial_utilisation" in facts.activity.activities
    assert facts.ipr.ipr_stage == "CONSIDERING_IPR"


def test_known_pip_ingredient_source_is_not_requested_again():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
    )

    result = assess_abs(pip)

    missing_fields = {
        item.field_name for item in result.missing_information
    }

    assert "ingredient_sources" not in missing_fields


def test_known_pip_origin_is_not_requested_again():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
    )

    result = assess_abs(pip)

    missing_fields = {
        item.field_name for item in result.missing_information
    }

    assert "biological_origin_region" not in missing_fields


def test_missing_pip_origin_remains_missing_instead_of_being_guessed():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="no",
    )

    result = assess_abs(pip)

    missing_fields = {
        item.field_name for item in result.missing_information
    }

    assert "biological_origin_region" in missing_fields
    assert result.relevance == "possible"


def test_pip_known_origin_determines_abs_pathway_without_reasking_origin():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
    )

    result = assess_abs(pip)

    assert result.relevance == "likely"
    assert result.pathway != "UNRESOLVED"

    missing_fields = {
        item.field_name for item in result.missing_information
    }

    assert "ingredient_sources" not in missing_fields
    assert "biological_origin_region" not in missing_fields


def test_pip_objective_reaches_abs_ipr_logic():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
    )
    pip.objective = ["patentability"]

    result = assess_abs(pip)

    assert result.ip_filing_flag is True
    assert result.ip_filing_note is not None
    assert "Section 6" in result.ip_filing_note


def test_pip_abs_facts_override_is_preserved():
    pip = _pip(
        ingredient_sources=["plant"],
        biological_origin_known="yes",
        biological_origin_region="Kerala, India",
    )

    # Explicit ABS facts are an existing supported input path.
    pip.abs_facts = pip.abs_facts.model_copy(deep=True) if pip.abs_facts else None

    result = assess_abs(pip)

    assert result.relevance == "likely"


def test_empty_pip_does_not_invent_biological_origin():
    pip = ProductIntelligenceProfile()

    result = assess_abs(pip)

    missing_fields = {
        item.field_name for item in result.missing_information
    }

    assert "ingredient_sources" in missing_fields
    assert result.abstained is True