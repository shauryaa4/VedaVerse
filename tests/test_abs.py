"""
Tests for ABS-02 (backend/logic/abs_helper.py). One test per rule branch,
named after the rule so a failure points straight at which BDA provision's
logic broke.
"""

from backend.logic.abs_helper import assess_abs
from backend.models.pip import ProductIntelligenceProfile, Product


def _pip(**product_kwargs) -> ProductIntelligenceProfile:
    return ProductIntelligenceProfile(product=Product(**product_kwargs))


def test_no_ingredient_sources_is_possible():
    result = assess_abs(_pip())
    assert result.relevance == "possible"
    assert result.ip_filing_flag is False


def test_mineral_only_is_not_applicable():
    result = assess_abs(_pip(ingredient_sources=["mineral", "synthetic"]))
    assert result.relevance == "not_applicable"


def test_biological_origin_unknown_is_possible():
    result = assess_abs(_pip(ingredient_sources=["plant"], biological_origin_known="no"))
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
    assert result.applicable_authority_guidance  # NBA/SBB pointer present


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
    result = assess_abs(pip)  # no objective set
    assert result.ip_filing_flag is False


def test_ambiguous_region_is_possible():
    result = assess_abs(
        _pip(ingredient_sources=["animal"], biological_origin_known="yes", biological_origin_region="unclear")
    )
    assert result.relevance == "possible"
