"""
Tests for ROUTE-01. Run with: pytest -v tests/test_routing.py

Per Execution Board's own note: "ROUTE-04's unit tests can be written
test-first before ROUTE-01's full implementation lands" — these tests are
written directly against build spec section 5's table, row by row, so
whoever reviews this can check each test against the spec line it covers.
"""

from backend.logic.routing import route


# --- The one row the demo slice actually depends on today ---

def test_india_classical_patentability_hits_patent_and_biodiversity():
    result = route("india", "classical_generic", ["patentability"])
    assert "patent_law" in result.legal_regimes
    assert "biodiversity_law" in result.legal_regimes
    assert len(result.matched_rows) == 1


def test_india_proprietary_patentability_includes_patent_rules():
    result = route("india", "proprietary", ["patentability"])
    assert set(result.legal_regimes) == {"patent_law", "patent_rules", "biodiversity_law"}


# --- Remaining India rows ---

def test_india_new_drug_regulatory_category():
    result = route("india", "new_drug", ["regulatory_category"])
    assert result.legal_regimes == ["drugs_cosmetics_law"]


def test_india_phytopharmaceutical_regulatory_category():
    result = route("india", "phytopharmaceutical", ["regulatory_category"])
    assert set(result.legal_regimes) == {"drugs_cosmetics_rules", "drugs_cosmetics_law"}


def test_india_nutraceutical_regulatory_category():
    result = route("india", "nutraceutical_ayurveda_aahar", ["regulatory_category"])
    assert result.legal_regimes == ["fssai_ayurveda_aahar"]


def test_india_cosmetic_regulatory_category():
    result = route("india", "cosmetic", ["regulatory_category"])
    assert result.legal_regimes == ["drugs_cosmetics_law"]


# --- Wildcard rows: apply regardless of category ---

def test_trademark_wildcard_applies_to_any_category():
    for category in ("classical_generic", "proprietary", "new_drug", "cosmetic"):
        result = route("india", category, ["trademark"])
        assert result.legal_regimes == ["trademark_law"], f"failed for category={category}"


def test_abs_relevance_wildcard_india():
    result = route("india", "cosmetic", ["abs_relevance"])
    assert set(result.legal_regimes) == {"biodiversity_law", "biodiversity_rules"}


# --- Multiple objectives merge into a union, each contributing its own matched row ---

def test_multiple_objectives_union_and_list_each_matched_row():
    result = route("india", "proprietary", ["patentability", "trademark"])
    assert "patent_law" in result.legal_regimes
    assert "trademark_law" in result.legal_regimes
    assert len(result.matched_rows) == 2


# --- International rows ---

def test_international_patentability():
    result = route("international", "proprietary", ["patentability"])
    assert set(result.legal_regimes) == {"trips", "pct"}
    assert result.status_notes == []  # no status caveat needed for TRIPS/PCT


def test_international_abs_relevance_flags_gratk_not_in_force():
    result = route("international", "classical_generic", ["abs_relevance"])
    assert "wipo_gratk" in result.legal_regimes
    assert any("NOT YET IN FORCE" in note for note in result.status_notes)


def test_international_prior_art_flags_gratk_not_in_force():
    result = route("international", "proprietary", ["prior_art"])
    assert result.legal_regimes == ["wipo_gratk"]
    assert any("NOT YET IN FORCE" in note for note in result.status_notes)


# --- Edge cases ---

def test_no_objectives_returns_empty_and_a_note():
    result = route("india", "proprietary", [])
    assert result.legal_regimes == []
    assert result.matched_rows == []
    assert len(result.status_notes) == 1


def test_unresolved_category_still_routes_narrowly_instead_of_nothing():
    result = route("india", "unresolved", ["patentability"])
    assert result.legal_regimes == ["patent_law"]
    assert "unresolved" in result.matched_rows[0].lower()


def test_unmatched_combination_notes_fallback_instead_of_crashing():
    # india + classical_generic + regulatory_category has no row in section 5's table
    result = route("india", "classical_generic", ["regulatory_category"])
    assert result.legal_regimes == []
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
