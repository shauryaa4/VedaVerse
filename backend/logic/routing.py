"""
ROUTE-01 — Deterministic routing engine.

Implements build spec section 5 exactly:
    (jurisdiction, classification.category, objective[]) -> corpus_filter

DELIBERATE DESIGN CHOICE — read before changing anything:
This module knows NOTHING about whether a given legal_regime's documents
actually have real content yet (e.g. Biological Diversity Act is currently
empty stub files in the corpus). That is intentional. Per build spec section 5:

    "Always retrieve top-k from the filtered set first; if filtered set
    returns nothing above the relevance threshold, fall back to unfiltered
    jurisdiction-only retrieval, then to abstention if still nothing usable."

Handling "this regime has no real chunks yet" is the RETRIEVER's job
(VEC/RAG-03), not routing's. Routing only ever answers "which regimes are
*supposed* to be relevant" — it is a pure function and stays testable
without the corpus existing at all. Do not add corpus-completion checks here.

Category values match backend.logic.classification.Category exactly.
Objective values match the frozen PIP schema, build spec section 2.
"""

from typing import Literal
from pydantic import BaseModel

from backend.logic.classification import Category

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


class RoutingResult(BaseModel):
    jurisdiction: Jurisdiction
    legal_regimes: list[str]       # union across every objective that matched
    matched_rows: list[str]        # human-readable rule descriptions, for debugging/explainability
    status_notes: list[str] = []   # e.g. WIPO GRATK not-in-force flag
    fallback_order: list[str] = [
        "metadata_filtered_retrieval",
        "jurisdiction_only_retrieval",
        "abstain",
    ]


# --- India rows: (category, objective) -> legal regimes ---
# "*" as category means the row applies regardless of classification category.
_INDIA_ROWS: list[tuple[str, Objective, list[str], str]] = [
    ("classical_generic", "patentability",
     ["patent_law", "biodiversity_law"],
     "India + Classical/Generic + patentability -> Patents Act s.3(p), Biological Diversity Act, TKDL mock"),

    ("proprietary", "patentability",
     ["patent_law", "patent_rules", "biodiversity_law"],
     "India + Proprietary + patentability -> Patents Act (novelty/inventive step), Patents Rules, BDA (ABS)"),

    ("new_drug", "regulatory_category",
     ["drugs_cosmetics_law"],
     "India + New Drug + regulatory_category -> Drugs and Cosmetics Act/Rules"),

    ("phytopharmaceutical", "regulatory_category",
     ["drugs_cosmetics_rules", "drugs_cosmetics_law"],
     "India + Phytopharmaceutical + regulatory_category -> D&C Rules (phytopharma definition), D&C Act"),

    ("nutraceutical_ayurveda_aahar", "regulatory_category",
     ["fssai_ayurveda_aahar"],
     "India + Nutraceutical + regulatory_category -> FSSAI Ayurveda-Aahar regulations"),

    ("cosmetic", "regulatory_category",
     ["drugs_cosmetics_law"],
     "India + Cosmetic + regulatory_category -> Drugs and Cosmetics Act (cosmetic provisions)"),

    ("*", "trademark",
     ["trademark_law"],
     "India + * + trademark -> Trade Marks Act"),

    ("*", "abs_relevance",
     ["biodiversity_law", "biodiversity_rules"],
     "India + * + abs_relevance -> Biological Diversity Act + Rules 2024"),
]

# --- International rows: category is always "*" per build spec section 5 ---
_INTERNATIONAL_ROWS: list[tuple[str, Objective, list[str], str, list[str]]] = [
    ("*", "patentability",
     ["trips", "pct"],
     "International + * + patentability -> TRIPS Art.27, PCT basics",
     []),

    ("*", "abs_relevance",
     ["cbd", "nagoya_protocol", "wipo_gratk"],
     "International + * + abs_relevance -> CBD Art.15, Nagoya Protocol, WIPO GRATK",
     ["WIPO GRATK Treaty adopted 24 May 2024 but NOT YET IN FORCE (needs 15 ratifications/accessions) — "
      "must be displayed to the user as such, not cited as binding law."]),

    ("*", "prior_art",
     ["wipo_gratk"],
     "International + * + prior_art -> WIPO GRATK disclosure provisions",
     ["WIPO GRATK Treaty adopted 24 May 2024 but NOT YET IN FORCE — status-flag this in the UI."]),
]

# Fallback for CLS-01's "unresolved" category: route narrowly rather than not at all.
_UNRESOLVED_FALLBACK_REGIME = {
    "patentability": "patent_law",
    "regulatory_category": "drugs_cosmetics_law",
    "trademark": "trademark_law",
    "abs_relevance": "biodiversity_law",
    "prior_art": "patent_law",
}


def route(jurisdiction: Jurisdiction, category: Category, objectives: list[Objective]) -> RoutingResult:
    if not objectives:
        return RoutingResult(
            jurisdiction=jurisdiction,
            legal_regimes=[],
            matched_rows=[],
            status_notes=["No objective supplied — nothing to route on. Retriever should abstain."],
        )

    legal_regimes: list[str] = []
    matched_rows: list[str] = []
    status_notes: list[str] = []

    if jurisdiction == "india":
        for row_category, row_objective, regimes, description in _INDIA_ROWS:
            for objective in objectives:
                if objective != row_objective:
                    continue
                if row_category != "*" and row_category != category:
                    continue
                matched_rows.append(description)
                for regime in regimes:
                    if regime not in legal_regimes:
                        legal_regimes.append(regime)

        if not matched_rows and category == "unresolved":
            for objective in objectives:
                fallback_regime = _UNRESOLVED_FALLBACK_REGIME.get(objective)
                if fallback_regime:
                    matched_rows.append(
                        f"Classification unresolved — narrowly routing '{objective}' to "
                        f"'{fallback_regime}' only, pending clarified category."
                    )
                    if fallback_regime not in legal_regimes:
                        legal_regimes.append(fallback_regime)

    elif jurisdiction == "international":
        for row_category, row_objective, regimes, description, notes in _INTERNATIONAL_ROWS:
            for objective in objectives:
                if objective != row_objective:
                    continue
                # row_category is always "*" for international per spec, kept for symmetry/future rows.
                if row_category != "*" and row_category != category:
                    continue
                matched_rows.append(description)
                status_notes.extend(notes)
                for regime in regimes:
                    if regime not in legal_regimes:
                        legal_regimes.append(regime)

    if not matched_rows:
        status_notes.append(
            f"No routing row matched jurisdiction={jurisdiction!r}, category={category!r}, "
            f"objectives={objectives!r}. Retriever should fall back to jurisdiction-only retrieval "
            f"or abstain per build spec section 5/9."
        )

    return RoutingResult(
        jurisdiction=jurisdiction,
        legal_regimes=legal_regimes,
        matched_rows=matched_rows,
        status_notes=status_notes,
    )
