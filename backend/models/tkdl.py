"""
TKDL-01 — Data models for the MOCK TKDL (Traditional Knowledge Digital Library)
prior-art module.

Per build spec section 19 and PROJECT_INSTRUCTIONS section 19/28:
    "TKDL must NOT be represented as a live integration unless authorised
    access actually exists. For the demo: TKDL Search — DEMO / MOCK."

Everything in this file backs a small, hand-curated sample dataset
(backend/data/tkdl_mock_records.py) — NOT a connection to the real TKDL
database. Every top-level response object below carries `mock: bool = True`
so this can never silently be mistaken for a live result downstream (FE,
demo script, judges' screen).

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

NOT in scope for this file: any live TKDL API client, any authentication,
any real government data source. If real TKDL access is ever authorised,
that would be a NEW module (e.g. backend/services/tkdl_live_client.py) —
this mock module should NOT be silently repointed at it; the UI-facing
"mock" flag and disclaimer text would need to change too.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.models.pip import IngredientSource

RiskLevel = Literal["high", "medium", "low", "none"]


class TKDLIngredient(BaseModel):
    """One ingredient as documented in a (mock) TKDL record.

    `name` is the common/English identifier used for matching against a
    user's free-text composition entries. `scientific_name` and
    `traditional_name` are optional richer detail, TKDL-style, and are also
    used as matching signals (see logic/tkdl_search.py::_ingredient_tokens).
    """

    name: str
    scientific_name: Optional[str] = None
    traditional_name: Optional[str] = None
    source_category: IngredientSource
    part_used: Optional[str] = None  # e.g. "Leaf (Patra)", "Root", "Fruit"
    processing: Optional[str] = None  # e.g. "Purified (Shuddha)"


class TKDLRecord(BaseModel):
    """One mock traditional-knowledge formulation record.

    `record_id` mirrors TKDL's own record-ID style (e.g. "BP/1025") purely
    for demo realism — these are NOT real TKDL record IDs and must not be
    presented as such outside the mock-labelled UI.
    """

    record_id: str
    formulation_name: str  # traditional/Sanskrit name of the formulation
    source_text: str  # e.g. "Bhaisajya Ratnavali" — the classical text it's drawn from
    formulation_type: Optional[str] = None  # e.g. "Gutika (tablet/pill)", "Churna (powder)"
    knowledge_known_since_years: int
    ingredients: list[TKDLIngredient]
    therapeutic_use: list[str] = Field(default_factory=list)
    is_mock: Literal[True] = True


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
    mock: Literal[True] = True
    disclaimer: str = (
        "TKDL Search — DEMO / MOCK. Compared against a small hand-curated sample "
        "dataset for demonstration purposes only. This is NOT a connection to the "
        "live TKDL database and NOT a patentability opinion — verify with a "
        "qualified patent professional before relying on this for any real filing."
    )
