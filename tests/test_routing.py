"""
Tests for ROUTE-01 v3. Run with: pytest -v tests/test_routing.py

Regime names here match Shau's corpus task doc section 1 EXACTLY:
patent_law, biodiversity_abs, drug_regulation, food_regulation,
trademark_law, treaty_patent, treaty_abs, wipo_gratk (see routing.py's
module docstring for why wipo_gratk stays its own tag).
"""

from backend.logic.routing import route


def _filter_for(result, regime):
    for f in result.regime_filters:
        if f.legal_regime == regime:
            return f
    return None


# --- The one row the demo slice actually depends on today ---

def test_india_classical_patentability_restricts_patent_law_to_act_only():
    result = route("india", "classical_generic", ["patentability"])
    patent = _filter_for(result, "patent_law")
    assert patent is not None
    assert patent.document_types == ["act"]  # must NOT pull in Patents Rules
    assert _filter_for(result, "biodiversity_abs") is not None
    assert len(result.matched_rows) == 1


def test_india_proprietary_patentability_does_not_restrict_patent_law():
    result = route("india", "proprietary", ["patentability"])
    patent = _filter_for(result, "patent_law")
    assert patent is not None
    assert patent.document_types is None  # unrestricted = includes "rule" docs too
    assert _filter_for(result, "biodiversity_abs") is not None


# --- Remaining India rows ---

def test_india_new_drug_regulatory_category():
    result = route("india", "new_drug", ["regulatory_category"])
    assert result.legal_regimes == ["drug_regulation"]
    assert _filter_for(result, "drug_regulation").document_types is None


def test_india_phytopharmaceutical_regulatory_category_unrestricted():
    result = route("india", "phytopharmaceutical", ["regulatory_category"])
    f = _filter_for(result, "drug_regulation")
    assert f is not None
    assert f.document_types is None  # wants both Act and Rules


def test_india_nutraceutical_regulatory_category():
    result = route("india", "nutraceutical_ayurveda_aahar", ["regulatory_category"])
    assert result.legal_regimes == ["food_regulation"]


def test_india_cosmetic_regulatory_category_restricts_to_act_only():
    result = route("india", "cosmetic", ["regulatory_category"])
    f = _filter_for(result, "drug_regulation")
    assert f is not None
    assert f.document_types == ["act"]


# --- Wildcard rows ---

def test_trademark_wildcard_applies_to_any_category():
    for category in ("classical_generic", "proprietary", "new_drug", "cosmetic"):
        result = route("india", category, ["trademark"])
        assert result.legal_regimes == ["trademark_law"], f"failed for category={category}"


def test_abs_relevance_wildcard_india_unrestricted():
    result = route("india", "cosmetic", ["abs_relevance"])
    f = _filter_for(result, "biodiversity_abs")
    assert f is not None
    assert f.document_types is None


# --- Multiple objectives merge into a union ---

def test_multiple_objectives_union_and_list_each_matched_row():
    result = route("india", "proprietary", ["patentability", "trademark"])
    assert _filter_for(result, "patent_law") is not None
    assert _filter_for(result, "trademark_law") is not None
    assert len(result.matched_rows) == 2


def test_merge_widens_restriction_when_unrestricted_row_also_matches():
    result = route("india", "unresolved", ["patentability"])
    f = _filter_for(result, "patent_law")
    assert f is not None
    assert f.document_types == ["act"]


# --- International rows: TRIPS+PCT share treaty_patent, CBD+Nagoya share treaty_abs ---

def test_international_patentability_uses_shared_treaty_patent_tag():
    result = route("international", "proprietary", ["patentability"])
    assert result.legal_regimes == ["treaty_patent"]
    assert result.status_notes == []


def test_international_abs_relevance_uses_shared_treaty_abs_plus_gratk():
    result = route("international", "classical_generic", ["abs_relevance"])
    assert set(result.legal_regimes) == {"treaty_abs", "wipo_gratk"}
    assert any("NOT YET IN FORCE" in note for note in result.status_notes)


def test_international_prior_art_flags_gratk_not_in_force():
    result = route("international", "proprietary", ["prior_art"])
    assert result.legal_regimes == ["wipo_gratk"]
    assert any("NOT YET IN FORCE" in note for note in result.status_notes)


# --- Edge cases ---

def test_no_objectives_returns_empty_and_a_note():
    result = route("india", "proprietary", [])
    assert result.regime_filters == []
    assert result.matched_rows == []
    assert len(result.status_notes) == 1


def test_unresolved_category_still_routes_narrowly_instead_of_nothing():
    result = route("india", "unresolved", ["patentability"])
    assert result.legal_regimes == ["patent_law"]
    assert "unresolved" in result.matched_rows[0].lower()


def test_unmatched_combination_notes_fallback_instead_of_crashing():
    result = route("india", "classical_generic", ["regulatory_category"])
    assert result.regime_filters == []
    assert result.matched_rows == []
    assert len(result.status_notes) == 1
    assert "No routing row matched" in result.status_notes[0]


def test_fallback_order_always_present():
    result = route("india", "proprietary", ["patentability"])
    assert result.fallback_order == [
        "metadata_filtered_retrieval",
        "jurisdiction_only_retrieval",
        "abstain",
    ]
