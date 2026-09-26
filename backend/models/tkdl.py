"""
Data models for the offline, source-derived TKDL archive search.

Saved records are not a live TKDL query. Search results are informational
prior-art matches, not a patentability decision.

INGREDIENT CLASSIFICATION DESIGN (source: team's TKDL research notes):
Rather than inventing a new category vocabulary, TKDLIngredient.source_category
reuses `IngredientSource` from backend.models.pip (plant | animal | mineral |
microbial | synthetic) — the same "one enum, imported everywhere" rule the
project already applies to Category (classification.py) and Objective
(routing.py / pip.py). Do not add a second, competing category enum here.

On top of that shared category, this model layers the TKDL-specific detail
that a bare category can't express (per the research notes' worked example:
Mercury and Sulphur are both "mineral" but are meaningfully different
substances) — traditional_name, part_used, and processing. This mirrors how
the real TKDL documents ingredients (scientific identity + Ayurvedic name +
part/processing) while still giving VedaVerse's own similarity logic a clean
category to filter/compare on.

NOT in scope: a live TKDL API client, authentication, or an external
government data source.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.models.pip import IngredientSource

RiskLevel = Literal["high", "medium", "low", "none"]


class TKDLIngredient(BaseModel):
    """One ingredient as documented in a saved TKDL record.

    `name` is the common/English identifier used for matching against a
    user's free-text composition entries. `scientific_name` and
    `traditional_name` are optional richer detail, TKDL-style, and are also
    used as matching signals (see logic/tkdl_search.py::_ingredient_tokens).
    """

    name: str
    scientific_name: Optional[str] = None
    traditional_name: Optional[str] = None
    # Some source pages do not identify a category, so preserve that absence.
    source_category: Optional[IngredientSource] = None
    part_used: Optional[str] = None  # e.g. "Leaf (Patra)", "Root", "Fruit"
    processing: Optional[str] = None  # e.g. "Purified (Shuddha)"


class TKDLRecord(BaseModel):
    """One source-derived traditional-knowledge formulation record.

    Source-derived records preserve source identifiers when they are unique.
    Missing or conflicting source IDs receive clearly project-generated IDs,
    documented in the provenance sidecar. This model does not imply live
    TKDL access.
    """

    record_id: str
    formulation_name: str  # traditional/Sanskrit name of the formulation
    source_text: Optional[str] = None  # citation as captured from the source page, when available
    formulation_type: Optional[str] = None  # e.g. "Gutika (tablet/pill)", "Churna (powder)"
    knowledge_known_since_years: Optional[int] = None
    ingredients: list[TKDLIngredient]
    therapeutic_use: list[str] = Field(default_factory=list)


class TKDLMatchResult(BaseModel):
    """Result of comparing one submitted composition against one TKDL record."""

    record: TKDLRecord
    matched_ingredient_names: list[str]  # TKDL ingredients found in the user's composition
    unmatched_tkdl_ingredient_names: list[str]  # TKDL ingredients NOT found in the user's composition
    extra_user_ingredient_names: list[str]  # user's ingredients NOT found in this TKDL record
    overlap_ratio: float  # matched / total TKDL ingredients in this record, 0.0-1.0


class PriorArtAssessment(BaseModel):
    """
    The overall prior-art read-out for a submitted composition, built from the
    best-matching TKDLMatchResult (if any).

    Deliberately mirrors the "Case 1 / Case 2 / Case 3" reasoning from the
    team's TKDL research notes:
      - Case 1 (exact copy)              -> risk_level="high"
      - Case 2 (small addition/omission) -> risk_level="medium"
      - Case 3 (same core + real novelty signal) -> risk_level can still be
        "high" for the ingredient overlap, WITH potential_novel_features
        populated separately — ingredient prior-art and process/technical
        novelty are two different questions and must not be collapsed into
        one number (see logic/tkdl_search.py for why).

    This NEVER resolves to a patent grant/reject verdict — see reasoning
    strings, which always point to human examination for anything beyond
    "is the core formulation already documented in the sample dataset."
    """

    risk_level: RiskLevel
    closest_record: Optional[TKDLRecord] = None
    what_was_already_known: list[str] = Field(default_factory=list)
    what_appears_different: list[str] = Field(default_factory=list)
    potential_novel_features: list[str] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Compared against an offline archive of source-derived TKDL records. "
        "This is NOT a live connection to the TKDL database and NOT a "
        "patentability opinion — verify with a "
        "qualified patent professional before relying on this for any real filing."
    )
