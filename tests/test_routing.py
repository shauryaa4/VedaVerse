"""
Tests for ROUTE-01 and ROUTE-02.

Run with:

    pytest -v tests/test_routing.py

Regime names here match the repository's frozen corpus vocabulary:

    patent_law
    biodiversity_abs
    drug_regulation
    food_regulation
    trademark_law
    treaty_patent
    treaty_abs
    wipo_gratk
"""

from backend.logic.routing import route, route_pip
from backend.models.pip import ProductIntelligenceProfile


def _filter_for(result, regime):
    for f in result.regime_filters:
        if f.legal_regime == regime:
            return f
    return None


# ---------------------------------------------------------------------------
# ROUTE-01 — Direct deterministic routing tests
# ---------------------------------------------------------------------------

# --- The one row the demo slice actually depends on today ---

def test_india_classical_patentability_restricts_patent_law_to_act_only():
    result = route(
        "india",
        "classical_generic",
        ["patentability"],
    )

    patent = _filter_for(result, "patent_law")

    assert patent is not None
    assert patent.document_types == ["act"]
    assert _filter_for(result, "biodiversity_abs") is not None
    assert len(result.matched_rows) == 1


def test_india_proprietary_patentability_does_not_restrict_patent_law():
    result = route(
        "india",
        "proprietary",
        ["patentability"],
    )

    patent = _filter_for(result, "patent_law")

    assert patent is not None
    assert patent.document_types is None
    assert _filter_for(result, "biodiversity_abs") is not None


# --- Remaining India rows ---

def test_india_new_drug_regulatory_category():
    result = route(
        "india",
        "new_drug",
        ["regulatory_category"],
    )

    assert result.legal_regimes == ["drug_regulation"]
    assert (
        _filter_for(result, "drug_regulation").document_types
        is None
    )


def test_india_phytopharmaceutical_regulatory_category_unrestricted():
    result = route(
        "india",
        "phytopharmaceutical",
        ["regulatory_category"],
    )

    f = _filter_for(result, "drug_regulation")

    assert f is not None
    assert f.document_types is None


def test_india_nutraceutical_regulatory_category():
    result = route(
        "india",
        "nutraceutical_ayurveda_aahar",
        ["regulatory_category"],
    )

    assert result.legal_regimes == ["food_regulation"]


def test_india_cosmetic_regulatory_category_restricts_to_act_only():
    result = route(
        "india",
        "cosmetic",
        ["regulatory_category"],
    )

    f = _filter_for(result, "drug_regulation")

    assert f is not None
    assert f.document_types == ["act"]


# --- Wildcard rows ---

def test_trademark_wildcard_applies_to_any_category():
    for category in (
        "classical_generic",
        "proprietary",
        "new_drug",
        "cosmetic",
    ):
        result = route(
            "india",
            category,
            ["trademark"],
        )

        assert result.legal_regimes == [
            "trademark_law"
        ], f"failed for category={category}"


def test_abs_relevance_wildcard_india_unrestricted():
    result = route(
        "india",
        "cosmetic",
        ["abs_relevance"],
    )

    f = _filter_for(
        result,
        "biodiversity_abs",
    )

    assert f is not None
    assert f.document_types is None


# --- Multiple objectives merge into a union ---

def test_multiple_objectives_union_and_list_each_matched_row():
    result = route(
        "india",
        "proprietary",
        ["patentability", "trademark"],
    )

    assert _filter_for(
        result,
        "patent_law",
    ) is not None

    assert _filter_for(
        result,
        "trademark_law",
    ) is not None

    assert len(result.matched_rows) == 2


def test_merge_widens_restriction_when_unrestricted_row_also_matches():
    result = route(
        "india",
        "unresolved",
        ["patentability"],
    )

    f = _filter_for(
        result,
        "patent_law",
    )

    assert f is not None
    assert f.document_types == ["act"]


# --- International rows ---

def test_international_patentability_uses_shared_treaty_patent_tag():
    result = route(
        "international",
        "proprietary",
        ["patentability"],
    )

    assert result.legal_regimes == [
        "treaty_patent"
    ]

    assert result.status_notes == []


def test_international_abs_relevance_uses_shared_treaty_abs_plus_gratk():
    result = route(
        "international",
        "classical_generic",
        ["abs_relevance"],
    )

    assert set(result.legal_regimes) == {
        "treaty_abs",
        "wipo_gratk",
    }

    assert any(
        "NOT YET IN FORCE" in note
        for note in result.status_notes
    )


def test_international_prior_art_flags_gratk_not_in_force():
    result = route(
        "international",
        "proprietary",
        ["prior_art"],
    )

    assert result.legal_regimes == [
        "wipo_gratk"
    ]

    assert any(
        "NOT YET IN FORCE" in note
        for note in result.status_notes
    )


# --- Edge cases ---

def test_no_objectives_returns_empty_and_a_note():
    result = route(
        "india",
        "proprietary",
        [],
    )

    assert result.regime_filters == []
    assert result.matched_rows == []
    assert len(result.status_notes) == 1


def test_unresolved_category_still_routes_narrowly_instead_of_nothing():
    result = route(
        "india",
        "unresolved",
        ["patentability"],
    )

    assert result.legal_regimes == [
        "patent_law"
    ]

    assert "unresolved" in (
        result.matched_rows[0].lower()
    )


def test_unmatched_combination_notes_fallback_instead_of_crashing():
    result = route(
        "india",
        "classical_generic",
        ["regulatory_category"],
    )

    assert result.regime_filters == []
    assert result.matched_rows == []
    assert len(result.status_notes) == 1
    assert "No routing row matched" in (
        result.status_notes[0]
    )


def test_fallback_order_always_present():
    result = route(
        "india",
        "proprietary",
        ["patentability"],
    )

    assert result.fallback_order == [
        "metadata_filtered_retrieval",
        "jurisdiction_only_retrieval",
        "abstain",
    ]


# ---------------------------------------------------------------------------
# ROUTE-03 — overlapping regimes across multiple real rows
# ---------------------------------------------------------------------------

def test_multiple_objectives_both_touching_biodiversity_abs_stay_unrestricted():
    """
    classical_generic + patentability wants biodiversity_abs unrestricted,
    and the wildcard abs_relevance row also wants it unrestricted.

    Both objectives together must not narrow each other.
    """
    result = route(
        "india",
        "classical_generic",
        ["patentability", "abs_relevance"],
    )

    bio = _filter_for(
        result,
        "biodiversity_abs",
    )

    assert bio is not None
    assert bio.document_types is None

    patent = _filter_for(
        result,
        "patent_law",
    )

    assert patent is not None
    assert patent.document_types == ["act"]
    assert len(result.matched_rows) == 2


def test_proprietary_patentability_plus_abs_relevance_keeps_patent_law_unrestricted():
    """
    proprietary + patentability already wants patent_law unrestricted.

    Adding abs_relevance must not accidentally restrict patent_law.
    """
    result = route(
        "india",
        "proprietary",
        ["patentability", "abs_relevance"],
    )

    patent = _filter_for(
        result,
        "patent_law",
    )

    assert patent is not None
    assert patent.document_types is None


# ---------------------------------------------------------------------------
# ROUTE-04 — unresolved fallback behavior
# ---------------------------------------------------------------------------

def test_unresolved_legal_pathway_falls_through_to_jurisdiction_only_note():
    """
    legal_pathway deliberately has no unresolved fallback.

    It must not silently invent a legal regime.
    """
    result = route(
        "india",
        "unresolved",
        ["legal_pathway"],
    )

    assert result.regime_filters == []
    assert result.matched_rows == []

    assert any(
        "No routing row matched" in note
        for note in result.status_notes
    )


def test_unresolved_general_falls_through_to_jurisdiction_only_note():
    result = route(
        "india",
        "unresolved",
        ["general"],
    )

    assert result.regime_filters == []
    assert result.matched_rows == []

    assert any(
        "No routing row matched" in note
        for note in result.status_notes
    )


def test_unresolved_mixed_objectives_only_narrows_the_ones_with_a_fallback():
    """
    If unresolved fires with both:

        patentability
        general

    only patentability has an approved narrow fallback.
    """
    result = route(
        "india",
        "unresolved",
        ["patentability", "general"],
    )

    patent = _filter_for(
        result,
        "patent_law",
    )

    assert patent is not None
    assert patent.document_types == ["act"]

    assert len(result.matched_rows) == 1


# ---------------------------------------------------------------------------
# ROUTE-02 — Classification → Routing integration
# ---------------------------------------------------------------------------

def test_route_pip_uses_existing_classification_output():
    """
    Proves the actual integration path:

        PIP
          -> existing classifier
          -> PIP.classification.category
          -> route()
    """

    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        product={
            "composition": [
                {
                    "ingredient": "Ashwagandha extract",
                    "quantity": "500",
                    "unit": "mg",
                    "is_active": True,
                }
            ],
            "intended_use": "therapeutic",
            "classical_basis": "partial",
            "novelty": "modified",
            "development_status": "prototype",
        },
        objective=["patentability"],
    )

    assert pip.classification.category is None

    result = route_pip(pip)

    assert result is not None

    # Classification must have happened before routing.
    assert pip.classification.category is not None

    # The classifier's category must actually drive the route.
    assert result.jurisdiction == "india"
    assert result.legal_regimes == [
        "patent_law",
        "biodiversity_abs",
    ]


def test_route_pip_preserves_existing_classification():
    """
    If classification has already been produced, route_pip() must use it
    rather than replacing it with an LLM/frontend decision.
    """

    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        product={
            "composition": [
                {
                    "ingredient": "X",
                    "quantity": "1",
                    "unit": "g",
                    "is_active": True,
                }
            ]
        },
        objective=["trademark"],
        classification={
            "category": "proprietary",
            "reasons": ["Existing deterministic classification."],
            "confidence": "high",
            "unresolved_flags": [],
        },
    )

    original_category = pip.classification.category

    result = route_pip(pip)

    assert result is not None
    assert pip.classification.category == original_category

    assert result.legal_regimes == [
        "trademark_law"
    ]


def test_route_pip_uses_unresolved_classification_safely():
    """
    An unresolved classification is still a structured classifier result.

    Routing may use only the explicitly defined narrow fallback and must not
    invent a more specific category.
    """

    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        objective=["patentability"],
        classification={
            "category": "unresolved",
            "reasons": [
                "Insufficient information to determine a specific category."
            ],
            "confidence": "low",
            "unresolved_flags": [
                "insufficient_product_information"
            ],
        },
    )

    result = route_pip(pip)

    assert result is not None
    assert pip.classification.category == "unresolved"

    assert result.legal_regimes == [
        "patent_law"
    ]

    patent = _filter_for(
        result,
        "patent_law",
    )

    assert patent is not None
    assert patent.document_types == ["act"]


def test_route_pip_does_not_invent_missing_jurisdiction():
    """
    Missing jurisdiction must remain missing.

    The router must not guess India or international jurisdiction.
    """

    pip = ProductIntelligenceProfile(
        objective=["patentability"],
        classification={
            "category": "proprietary",
            "reasons": ["Classification already known."],
            "confidence": "high",
            "unresolved_flags": [],
        },
    )

    result = route_pip(pip)

    assert result is None
    assert pip.jurisdiction is None


def test_route_pip_does_not_invent_missing_category():
    """
    If the deterministic classifier still cannot produce a category,
    route_pip() must not invent one.
    """

    pip = ProductIntelligenceProfile(
        jurisdiction="india",
        objective=["general"],
    )

    # No product facts and a broad objective should not result in a
    # fabricated category.
    result = route_pip(pip)

    # The classifier may produce "unresolved"; if it does, the router
    # handles that structured state. What must never happen is an invented
    # specific category.
    assert pip.classification.category in (
        None,
        "unresolved",
    )

    if pip.classification.category is None:
        assert result is None