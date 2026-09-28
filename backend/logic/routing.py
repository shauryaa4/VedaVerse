"""
ROUTE-01 — Deterministic routing engine.

Implements build spec section 5:
    (jurisdiction, classification.category, objective[]) -> corpus_filter

v3 CHANGE — this is a real correctness fix, not a style change:
Shau's corpus task doc (section 1) FREEZES the exact legal_regime vocabulary
every corpus document is tagged with: patent_law, biodiversity_abs,
food_regulation, trademark_law, treaty_patent, treaty_abs. v2 of this file
used regime names invented independently of that schema (biodiversity_law,
drugs_cosmetics_law, fssai_ayurveda_aahar, separate "trips"/"pct" and
"cbd"/"nagoya_protocol" tags) — those never matched anything in the real
corpus and would have silently returned zero results for almost every route
except patent_law/trademark_law, which happened to match by coincidence.
Confirmed by checking IN-4's actual committed frontmatter: legal_regime is
"biodiversity_abs", not "biodiversity_law".

Corrected mapping used below:
  - biodiversity_law        -> biodiversity_abs
  - drugs_cosmetics_law    -> drug_regulation
  - fssai_ayurveda_aahar   -> food_regulation
  - "trips" + "pct"        -> treaty_patent
  - "cbd" + "nagoya_protocol" -> treaty_abs
  - wipo_gratk             -> kept as its own tag

DELIBERATE DESIGN CHOICE, unchanged since v1:
This module knows NOTHING about whether a regime's documents actually have
real content yet. Per spec section 5, "no chunks found -> fall back to
jurisdiction-only retrieval -> abstain" is the RETRIEVER's job, not routing's.
Routing only answers "which regimes/types are supposed to be relevant" and
stays a pure, corpus-independent function. Do not add corpus-completion
checks here.

Category values match backend.logic.classification.Category exactly.
Objective values match the frozen PIP schema, build spec section 2.
"""

from typing import Literal, Optional

from pydantic import BaseModel

from backend.logic.classification import (
    Category,
    apply_classification_to_pip,
)

Jurisdiction = Literal["india", "international"]

Objective = Literal[
    "patentability",
    "regulatory_category",
    "trademark",
    "prior_art",
    "abs_relevance",
    "legal_pathway",
    "general",
]

# (legal_regime, document_types)
# document_types=None means "any type in this regime".
RegimeSpec = tuple[str, Optional[list[str]]]


class RegimeFilter(BaseModel):
    legal_regime: str
    document_types: Optional[list[str]] = None


class RoutingResult(BaseModel):
    jurisdiction: Jurisdiction

    # AUTHORITATIVE:
    # use this for actual retrieval filtering.
    regime_filters: list[RegimeFilter]

    # Convenience/debug summary only.
    legal_regimes: list[str]

    # Human-readable rule descriptions.
    matched_rows: list[str]

    # e.g. WIPO GRATK not-in-force flag.
    status_notes: list[str] = []

    fallback_order: list[str] = [
        "metadata_filtered_retrieval",
        "jurisdiction_only_retrieval",
        "abstain",
    ]


# ---------------------------------------------------------------------------
# India routing rows
# ---------------------------------------------------------------------------

# "*" as category means the row applies regardless of classification category.
_INDIA_ROWS: list[tuple[str, Objective, list[RegimeSpec], str]] = [
    (
        "classical_generic",
        "patentability",
        [
            ("patent_law", ["act"]),
            ("biodiversity_abs", None),
        ],
        (
            "India + Classical/Generic + patentability -> "
            "Patents Act s.3(p) ONLY (not Rules), Biological Diversity Act, "
            "TKDL archive search"
        ),
    ),
    (
        "proprietary",
        "patentability",
        [
            ("patent_law", None),
            ("biodiversity_abs", None),
        ],
        (
            "India + Proprietary + patentability -> "
            "Patents Act (novelty/inventive step) + Patents Rules "
            "(both under patent_law), BDA (ABS)"
        ),
    ),
    (
        "new_drug",
        "regulatory_category",
        [
            ("drug_regulation", None),
        ],
        (
            "India + New Drug + regulatory_category -> "
            "Drugs and Cosmetics Act/Rules (both, no restriction)"
        ),
    ),
    (
        "phytopharmaceutical",
        "regulatory_category",
        [
            ("drug_regulation", None),
        ],
        (
            "India + Phytopharmaceutical + regulatory_category -> "
            "D&C Act + Rules (phytopharma definition) (both, no restriction)"
        ),
    ),
    (
        "nutraceutical_ayurveda_aahar",
        "regulatory_category",
        [
            ("food_regulation", None),
        ],
        (
            "India + Nutraceutical + regulatory_category -> "
            "FSSAI Ayurveda-Aahar regulations"
        ),
    ),
    (
        "cosmetic",
        "regulatory_category",
        [
            ("drug_regulation", ["act"]),
        ],
        (
            "India + Cosmetic + regulatory_category -> "
            "Drugs and Cosmetics Act ONLY "
            "(spec explicitly says Act, not Rules, for this row)"
        ),
    ),
    (
        "*",
        "trademark",
        [
            ("trademark_law", None),
        ],
        "India + * + trademark -> Trade Marks Act",
    ),
    (
        "*",
        "abs_relevance",
        [
            ("biodiversity_abs", None),
        ],
        (
            "India + * + abs_relevance -> "
            "Biological Diversity Act + Rules 2024 "
            "(both, no restriction)"
        ),
    ),
]


# ---------------------------------------------------------------------------
# International routing rows
# ---------------------------------------------------------------------------

# Category is always "*" per build spec section 5.
_INTERNATIONAL_ROWS: list[
    tuple[str, Objective, list[RegimeSpec], str, list[str]]
] = [
    (
        "*",
        "patentability",
        [
            ("treaty_patent", None),
        ],
        (
            "International + * + patentability -> "
            "TRIPS Art.27, PCT basics (both tagged treaty_patent)"
        ),
        [],
    ),
    (
        "*",
        "abs_relevance",
        [
            ("treaty_abs", None),
            ("wipo_gratk", None),
        ],
        (
            "International + * + abs_relevance -> "
            "CBD Art.15 + Nagoya Protocol (treaty_abs), WIPO GRATK"
        ),
        [
            (
                "WIPO GRATK Treaty adopted 24 May 2024 but NOT YET IN FORCE "
                "(needs 15 ratifications/accessions) — must be displayed "
                "to the user as such, not cited as binding law."
            )
        ],
    ),
    (
        "*",
        "prior_art",
        [
            ("wipo_gratk", None),
        ],
        (
            "International + * + prior_art -> "
            "WIPO GRATK disclosure provisions"
        ),
        [
            (
                "WIPO GRATK Treaty adopted 24 May 2024 but NOT YET IN FORCE "
                "— status-flag this in the UI."
            )
        ],
    ),
]


# ---------------------------------------------------------------------------
# Fallback for unresolved classification
# ---------------------------------------------------------------------------

# ROUTE-04 DECISION:
#
# "legal_pathway" and "general" deliberately have no narrow fallback.
# They are broad requests and narrowing them to a single regime would risk
# hiding relevant law.
#
# Other objectives have a narrow deterministic fallback when classification
# is unresolved.

_UNRESOLVED_FALLBACK_REGIME: dict[str, RegimeSpec] = {
    "patentability": ("patent_law", ["act"]),
    "regulatory_category": ("drug_regulation", None),
    "trademark": ("trademark_law", None),
    "abs_relevance": ("biodiversity_abs", None),
    "prior_art": ("patent_law", ["act"]),
    # "legal_pathway" and "general" intentionally absent.
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _merge_regime_specs(
    existing: list[RegimeFilter],
    new_specs: list[RegimeSpec],
) -> None:
    """
    Merge new (regime, types) specs into existing list in place.

    If either occurrence has document_types=None (unrestricted), the merged
    entry is unrestricted. Unrestricted always wins because narrowing an
    already-broad match would silently drop results.
    """
    by_regime = {f.legal_regime: f for f in existing}

    for regime, doc_types in new_specs:
        if regime not in by_regime:
            new_filter = RegimeFilter(
                legal_regime=regime,
                document_types=doc_types,
            )
            by_regime[regime] = new_filter
            existing.append(new_filter)
        else:
            current = by_regime[regime]

            if current.document_types is None or doc_types is None:
                current.document_types = None
            else:
                merged = sorted(
                    set(current.document_types) | set(doc_types)
                )
                current.document_types = merged


# ---------------------------------------------------------------------------
# ROUTE-01 — Pure deterministic router
# ---------------------------------------------------------------------------

def route(
    jurisdiction: Jurisdiction,
    category: Category,
    objectives: list[Objective],
) -> RoutingResult:
    """
    Deterministically map jurisdiction + classification + objectives
    to legal-regime retrieval filters.

    This function contains the actual routing rules and has no knowledge
    of sessions, HTTP, frontend state, LLM output, or corpus contents.
    """

    if not objectives:
        return RoutingResult(
            jurisdiction=jurisdiction,
            regime_filters=[],
            legal_regimes=[],
            matched_rows=[],
            status_notes=[
                "No objective supplied — nothing to route on. "
                "Retriever should abstain."
            ],
        )

    regime_filters: list[RegimeFilter] = []
    matched_rows: list[str] = []
    status_notes: list[str] = []

    # ------------------------------------------------------------------
    # India
    # ------------------------------------------------------------------

    if jurisdiction == "india":
        for (
            row_category,
            row_objective,
            regime_specs,
            description,
        ) in _INDIA_ROWS:
            for objective in objectives:
                if objective != row_objective:
                    continue

                if row_category != "*" and row_category != category:
                    continue

                matched_rows.append(description)
                _merge_regime_specs(
                    regime_filters,
                    regime_specs,
                )

        # If classification is unresolved, use only explicitly approved
        # narrow fallbacks.
        if not matched_rows and category == "unresolved":
            for objective in objectives:
                fallback = _UNRESOLVED_FALLBACK_REGIME.get(objective)

                if fallback:
                    regime, doc_types = fallback

                    matched_rows.append(
                        f"Classification unresolved — narrowly routing "
                        f"'{objective}' to '{regime}' only, "
                        f"pending clarified category."
                    )

                    _merge_regime_specs(
                        regime_filters,
                        [fallback],
                    )

    # ------------------------------------------------------------------
    # International
    # ------------------------------------------------------------------

    elif jurisdiction == "international":
        for (
            row_category,
            row_objective,
            regime_specs,
            description,
            notes,
        ) in _INTERNATIONAL_ROWS:
            for objective in objectives:
                if objective != row_objective:
                    continue

                if row_category != "*" and row_category != category:
                    continue

                matched_rows.append(description)
                status_notes.extend(notes)

                _merge_regime_specs(
                    regime_filters,
                    regime_specs,
                )

    # ------------------------------------------------------------------
    # No match
    # ------------------------------------------------------------------

    if not matched_rows:
        status_notes.append(
            f"No routing row matched "
            f"jurisdiction={jurisdiction!r}, "
            f"category={category!r}, "
            f"objectives={objectives!r}. "
            f"Retriever should fall back to jurisdiction-only retrieval "
            f"or abstain per build spec section 5/9."
        )

    return RoutingResult(
        jurisdiction=jurisdiction,
        regime_filters=regime_filters,
        legal_regimes=[
            f.legal_regime for f in regime_filters
        ],
        matched_rows=matched_rows,
        status_notes=status_notes,
    )


# ---------------------------------------------------------------------------
# ROUTE-02 — PIP → Classification → Routing integration
# ---------------------------------------------------------------------------

def route_pip(pip) -> Optional[RoutingResult]:
    """
    Connect the structured Product Intelligence Profile to the deterministic
    routing engine.

    Flow:

        PIP
          ↓
        existing deterministic classifier
          ↓
        pip.classification.category
          ↓
        existing deterministic route()
          ↓
        RoutingResult

    Important behavior:

    - Does NOT invent a missing jurisdiction.
    - Does NOT invent a classification.
    - If classification is missing, the existing classifier is run.
    - If classification remains unavailable, routing is not attempted.
    - Existing route() rules remain the single source of truth.
    - Frontend/LLM never selects legal regimes.

    Returns:
        RoutingResult when jurisdiction and classification are available.
        None when jurisdiction is unknown and therefore routing cannot be
        performed safely.
    """

    # Jurisdiction is required for the existing routing contract.
    # Never guess it.
    if pip.jurisdiction is None:
        return None

    # Classification may not have been run yet.
    # Use the existing deterministic classifier rather than inventing
    # a category in the router.
    if pip.classification.category is None:
        apply_classification_to_pip(pip)

    category = pip.classification.category

    # The classifier itself may leave the category unresolved/unknown.
    # "unresolved" is a valid Category and is handled deterministically
    # by route(). A truly absent category must not be invented.
    if category is None:
        return None

    return route(
        jurisdiction=pip.jurisdiction,
        category=category,
        objectives=pip.objective,
    )