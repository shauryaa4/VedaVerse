"""
ROUTE-01 — Deterministic routing engine.

Implements build spec section 5:
    (jurisdiction, classification.category, objective[]) -> corpus_filter

v2 CHANGE — why this file looks different from the first version:
The first version invented separate legal_regime tags for an Act vs its
Rules (e.g. "patent_law" vs "patent_rules"). The actual corpus doesn't tag
things that way — Shau's Patents Rules metadata uses legal_regime="patent_law"
(same as the Patents Act), distinguished only by document_type: "act" | "rule".
Rather than ask corpus work to be retagged, this version matches the corpus's
actual convention: one legal_regime per act-family, optionally narrowed by
document_type where the build spec explicitly wants only the Act and not its
Rules (or vice versa). See _INDIA_ROWS below — most rows don't restrict
document_type at all (None = match any type in that regime).

DELIBERATE DESIGN CHOICE, unchanged from v1:
This module knows NOTHING about whether a regime's documents actually have
real content yet. Per spec section 5, "no chunks found -> fall back to
jurisdiction-only retrieval -> abstain" is the RETRIEVER's job, not routing's.
Routing only answers "which regimes/types are *supposed* to be relevant" and
stays a pure, corpus-independent function. Do not add corpus-completion
checks here.

Category values match backend.logic.classification.Category exactly.
Objective values match the frozen PIP schema, build spec section 2.
"""

from typing import Literal, Optional
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

# (legal_regime, document_types) — document_types=None means "any type in this regime".
RegimeSpec = tuple[str, Optional[list[str]]]


class RegimeFilter(BaseModel):
    legal_regime: str
    document_types: Optional[list[str]] = None  # None = no restriction


class RoutingResult(BaseModel):
    jurisdiction: Jurisdiction
    regime_filters: list[RegimeFilter]   # AUTHORITATIVE — use this for actual retrieval filtering
    legal_regimes: list[str]             # convenience/debug summary only — names alone, no type nuance
    matched_rows: list[str]              # human-readable rule descriptions, for debugging/explainability
    status_notes: list[str] = []         # e.g. WIPO GRATK not-in-force flag
    fallback_order: list[str] = [
        "metadata_filtered_retrieval",
        "jurisdiction_only_retrieval",
        "abstain",
    ]


# --- India rows ---
# "*" as category means the row applies regardless of classification category.
_INDIA_ROWS: list[tuple[str, Objective, list[RegimeSpec], str]] = [
    ("classical_generic", "patentability",
     [("patent_law", ["act"]), ("biodiversity_law", None)],
     "India + Classical/Generic + patentability -> Patents Act s.3(p) ONLY (not Rules), Biological Diversity Act, TKDL mock"),

    ("proprietary", "patentability",
     [("patent_law", None), ("biodiversity_law", None)],
     "India + Proprietary + patentability -> Patents Act (novelty/inventive step) + Patents Rules (both under patent_law), BDA (ABS)"),

    ("new_drug", "regulatory_category",
     [("drugs_cosmetics_law", None)],
     "India + New Drug + regulatory_category -> Drugs and Cosmetics Act/Rules (both, no restriction)"),

    ("phytopharmaceutical", "regulatory_category",
     [("drugs_cosmetics_law", None)],
     "India + Phytopharmaceutical + regulatory_category -> D&C Act + Rules (phytopharma definition) (both, no restriction)"),

    ("nutraceutical_ayurveda_aahar", "regulatory_category",
     [("fssai_ayurveda_aahar", None)],
     "India + Nutraceutical + regulatory_category -> FSSAI Ayurveda-Aahar regulations"),

    ("cosmetic", "regulatory_category",
     [("drugs_cosmetics_law", ["act"])],
     "India + Cosmetic + regulatory_category -> Drugs and Cosmetics Act ONLY (spec explicitly says Act, not Rules, for this row)"),

    ("*", "trademark",
     [("trademark_law", None)],
     "India + * + trademark -> Trade Marks Act"),

    ("*", "abs_relevance",
     [("biodiversity_law", None)],
     "India + * + abs_relevance -> Biological Diversity Act + Rules 2024 (both, no restriction)"),
]

# --- International rows: category is always "*" per build spec section 5 ---
_INTERNATIONAL_ROWS: list[tuple[str, Objective, list[RegimeSpec], str, list[str]]] = [
    ("*", "patentability",
     [("trips", None), ("pct", None)],
     "International + * + patentability -> TRIPS Art.27, PCT basics",
     []),

    ("*", "abs_relevance",
     [("cbd", None), ("nagoya_protocol", None), ("wipo_gratk", None)],
     "International + * + abs_relevance -> CBD Art.15, Nagoya Protocol, WIPO GRATK",
     ["WIPO GRATK Treaty adopted 24 May 2024 but NOT YET IN FORCE (needs 15 ratifications/accessions) — "
      "must be displayed to the user as such, not cited as binding law."]),

    ("*", "prior_art",
     [("wipo_gratk", None)],
     "International + * + prior_art -> WIPO GRATK disclosure provisions",
     ["WIPO GRATK Treaty adopted 24 May 2024 but NOT YET IN FORCE — status-flag this in the UI."]),
]

# Fallback for CLS-01's "unresolved" category: route narrowly rather than not at all.
_UNRESOLVED_FALLBACK_REGIME: dict[str, RegimeSpec] = {
    "patentability": ("patent_law", ["act"]),
    "regulatory_category": ("drugs_cosmetics_law", None),
    "trademark": ("trademark_law", None),
    "abs_relevance": ("biodiversity_law", None),
    "prior_art": ("patent_law", ["act"]),
}


def _merge_regime_specs(existing: list[RegimeFilter], new_specs: list[RegimeSpec]) -> None:
    """Merge new (regime, types) specs into existing list in place, unioning by regime name.
    If either occurrence has document_types=None (unrestricted), the merged entry is unrestricted —
    unrestricted always wins, since narrowing an already-broad match would silently drop results."""
    by_regime = {f.legal_regime: f for f in existing}
    for regime, doc_types in new_specs:
        if regime not in by_regime:
            new_filter = RegimeFilter(legal_regime=regime, document_types=doc_types)
            by_regime[regime] = new_filter
            existing.append(new_filter)
        else:
            current = by_regime[regime]
            if current.document_types is None or doc_types is None:
                current.document_types = None
            else:
                merged = sorted(set(current.document_types) | set(doc_types))
                current.document_types = merged


def route(jurisdiction: Jurisdiction, category: Category, objectives: list[Objective]) -> RoutingResult:
    if not objectives:
        return RoutingResult(
            jurisdiction=jurisdiction,
            regime_filters=[],
            legal_regimes=[],
            matched_rows=[],
            status_notes=["No objective supplied — nothing to route on. Retriever should abstain."],
        )

    regime_filters: list[RegimeFilter] = []
    matched_rows: list[str] = []
    status_notes: list[str] = []

    if jurisdiction == "india":
        for row_category, row_objective, regime_specs, description in _INDIA_ROWS:
            for objective in objectives:
                if objective != row_objective:
                    continue
                if row_category != "*" and row_category != category:
                    continue
                matched_rows.append(description)
                _merge_regime_specs(regime_filters, regime_specs)

        if not matched_rows and category == "unresolved":
            for objective in objectives:
                fallback = _UNRESOLVED_FALLBACK_REGIME.get(objective)
                if fallback:
                    regime, doc_types = fallback
                    matched_rows.append(
                        f"Classification unresolved — narrowly routing '{objective}' to "
                        f"'{regime}' only, pending clarified category."
                    )
                    _merge_regime_specs(regime_filters, [fallback])

    elif jurisdiction == "international":
        for row_category, row_objective, regime_specs, description, notes in _INTERNATIONAL_ROWS:
            for objective in objectives:
                if objective != row_objective:
                    continue
                if row_category != "*" and row_category != category:
                    continue
                matched_rows.append(description)
                status_notes.extend(notes)
                _merge_regime_specs(regime_filters, regime_specs)

    if not matched_rows:
        status_notes.append(
            f"No routing row matched jurisdiction={jurisdiction!r}, category={category!r}, "
            f"objectives={objectives!r}. Retriever should fall back to jurisdiction-only retrieval "
            f"or abstain per build spec section 5/9."
        )

    return RoutingResult(
        jurisdiction=jurisdiction,
        regime_filters=regime_filters,
        legal_regimes=[f.legal_regime for f in regime_filters],
        matched_rows=matched_rows,
        status_notes=status_notes,
    )
