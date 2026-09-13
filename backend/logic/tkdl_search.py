"""
TKDL-02 — Deterministic TKDL search + prior-art comparison engine.

Implements the reasoning from the team's TKDL research notes as a RULE
ENGINE, not an LLM call and not ML similarity — same "deterministic,
first-match-wins, explain the rule that fired" philosophy as CLS-01
(backend/logic/classification.py) and ROUTE-01 (backend/logic/routing.py).
Never present this module's output as an LLM guess, and never collapse it
into "ingredients found in TKDL -> patent rejected" — see assess_prior_art()
below for why that's explicitly wrong.

THE CORE IDEA (from the research notes):
TKDL tells you what was already known. The submitted formulation is then
compared against that knowledge to find what, if anything, is actually
different. Two separate questions must stay separate:

  1. Ingredient/use overlap with a traditional record -> prior-art signal
     for the CORE formulation. This is what risk_level measures.
  2. A claimed process/manufacturing/bioavailability improvement -> a
     SEPARATE patentability question that ingredient matching cannot
     answer at all. This is what potential_novel_features flags.

A formulation can score "high" on (1) and still legitimately have novel
features under (2) — the classic "same A+B+C, but a new controlled-release
process" case. Collapsing these into one number would misrepresent exactly
the nuance the research notes insist on.

MATCHING METHOD: token-overlap on normalised ingredient identifiers (name +
scientific_name + traditional_name), stopword-filtered. This is intentionally
simple and deterministic — good enough to demo the CONCEPT of TKDL-based
prior art search against a ~6-record mock dataset. It is NOT a fuzzy-matching
or embedding-based system; do not oversell its matching quality past
"same rule-based standard as the rest of the app" in the demo script.
"""

import re

from backend.data.tkdl_mock_records import TKDL_MOCK_RECORDS
from backend.models.classification_input import CompositionItem
from backend.models.pip import ProductIntelligenceProfile
from backend.models.tkdl import PriorArtAssessment, TKDLIngredient, TKDLMatchResult, TKDLRecord

# Words that carry no identifying signal for matching (dosage-form nouns,
# plant-part nouns, common Latin taxonomic authority abbreviations). Kept
# deliberately short and explicit rather than a generic stopword list, since
# over-stripping would start matching unrelated ingredients to each other.
_STOPWORDS = {
    "root", "leaf", "leaves", "fruit", "seed", "seeds", "bark", "stem", "flower",
    "whole", "plant", "rhizome", "powder", "extract", "oil", "juice", "paste",
    "linn", "mill", "l", "churna", "vati", "gutika", "kwath", "kashaya",
    "bhasma", "rasa", "taila", "thailam", "ghrita", "avaleha", "of", "and",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    """Lowercase, strip punctuation, split on whitespace, drop stopwords."""
    if not text:
        return set()
    raw = _TOKEN_RE.findall(text.lower())
    return {t for t in raw if t not in _STOPWORDS}


def _ingredient_tokens(ingredient: TKDLIngredient) -> set[str]:
    """Union of identifying tokens across all of a TKDL ingredient's name fields."""
    tokens: set[str] = set()
    for field in (ingredient.name, ingredient.scientific_name, ingredient.traditional_name):
        tokens |= _tokens(field or "")
    return tokens


def _compare_to_record(
    composition: list[CompositionItem], record: TKDLRecord
) -> TKDLMatchResult:
    """
    BEST-OVERLAP matching, not first-hit matching.

    IMPORTANT: two TKDL ingredients can share a generic token — e.g.
    "Terminalia chebula" and "Terminalia bellirica" both tokenize to include
    "terminalia" once "chebula"/"bellirica" survive stopword filtering. A
    naive "pick the first user entry with ANY shared token" match would
    wrongly assign both TKDL ingredients to whichever user entry happens to
    come first in the list. Instead, for each TKDL ingredient, score every
    user composition entry by the COUNT of shared tokens and take the
    highest-scoring one — "Terminalia bellirica" (2 shared tokens) beats
    "Terminalia chebula" (1 shared token: "terminalia" only) as a match for
    the TKDL "Terminalia bellirica" entry. This was caught by manual
    verification against the Triphala record before shipping — see the
    corresponding test in tests/test_tkdl.py.
    """
    matched: list[str] = []
    unmatched: list[str] = []
    matched_user_texts: set[str] = set()

    for tkdl_ing in record.ingredients:
        tkdl_tokens = _ingredient_tokens(tkdl_ing)
        scored = [
            (c.ingredient, len(tkdl_tokens & _tokens(c.ingredient)))
            for c in composition
        ]
        scored = [s for s in scored if s[1] > 0]

        if scored:
            scored.sort(key=lambda s: s[1], reverse=True)
            matched.append(tkdl_ing.name)
            matched_user_texts.add(scored[0][0])
        else:
            unmatched.append(tkdl_ing.name)

    extra_user = [c.ingredient for c in composition if c.ingredient not in matched_user_texts]

    total = len(record.ingredients)
    overlap_ratio = (len(matched) / total) if total else 0.0

    return TKDLMatchResult(
        record=record,
        matched_ingredient_names=matched,
        unmatched_tkdl_ingredient_names=unmatched,
        extra_user_ingredient_names=extra_user,
        overlap_ratio=overlap_ratio,
    )


def search_tkdl(composition: list[CompositionItem]) -> list[TKDLMatchResult]:
    """
    Compare a submitted composition against every record in the mock TKDL
    dataset. Returns only records with at least one matched ingredient,
    sorted by overlap_ratio descending (best match first), ties broken by
    matched-ingredient count descending.

    Empty composition -> empty list (nothing to search on; caller should
    treat this the same as "no match found", per build spec's abstention
    philosophy — do not guess at a match with no input).
    """
    if not composition:
        return []

    results = [_compare_to_record(composition, record) for record in TKDL_MOCK_RECORDS]
    results = [r for r in results if r.matched_ingredient_names]
    results.sort(key=lambda r: (r.overlap_ratio, len(r.matched_ingredient_names)), reverse=True)
    return results


def assess_prior_art(
    pip: ProductIntelligenceProfile, matches: list[TKDLMatchResult]
) -> PriorArtAssessment:
    """
    Build the human-facing prior-art read-out from the best TKDL match, per
    the Case 1 / Case 2 / Case 3 reasoning in the research notes.

    Thresholds are intentionally coarse and named in the reasoning text
    (not hidden) — this is a demo heuristic over a 6-record mock dataset,
    not a calibrated legal determination. Per build spec section 17, this
    NEVER produces a numeric probability; only HIGH/MEDIUM/LOW/NONE.
    """
    if not matches:
        return PriorArtAssessment(
            risk_level="none",
            reasoning=[
                "No record in the mock TKDL sample dataset shares any ingredient with "
                "this composition. This does not mean no real-world prior art exists — "
                "it means none was found in this small demo dataset."
            ],
        )

    best = matches[0]
    record = best.record

    what_known = [
        f"{ing.name}" + (f" ({ing.traditional_name})" if ing.traditional_name else "")
        for ing in record.ingredients
    ]
    what_known.append(
        f"Traditional use: {', '.join(record.therapeutic_use)}"
        if record.therapeutic_use
        else "No therapeutic use recorded for this entry."
    )
    what_known.append(f"Knowledge known since approximately {record.knowledge_known_since_years} years ({record.source_text}).")

    what_different: list[str] = []
    if best.extra_user_ingredient_names:
        what_different.append(
            "Ingredient(s) in the submitted composition not present in this traditional "
            f"record: {', '.join(best.extra_user_ingredient_names)}."
        )
    if best.unmatched_tkdl_ingredient_names:
        what_different.append(
            "Traditional ingredient(s) not present in the submitted composition: "
            f"{', '.join(best.unmatched_tkdl_ingredient_names)}."
        )
    if not what_different:
        what_different.append("No ingredient-level differences found against this record.")

    # --- Question 2: process/technical novelty signal, kept fully separate
    # from the ingredient-overlap risk_level computed below (see module docstring). ---
    potential_novel: list[str] = []
    novelty = pip.product.novelty
    if novelty in ("modified", "new_combination"):
        potential_novel.append(
            f"User-declared formulation novelty is '{novelty}'. This may point to a claimed "
            "process, ratio, or combination change — ingredient matching alone cannot confirm "
            "or rule this out. Requires human patent-professional review."
        )
    if best.extra_user_ingredient_names:
        potential_novel.append(
            "The additional ingredient(s) above could be an obvious addition or a genuine "
            "technical improvement — this mock tool cannot distinguish the two."
        )
    if not potential_novel:
        potential_novel.append(
            "No specific novelty signal was declared for this composition; nothing beyond "
            "the traditional record to flag for separate examination."
        )

    reasoning: list[str] = []
    if best.overlap_ratio >= 0.999 and not best.extra_user_ingredient_names and not best.unmatched_tkdl_ingredient_names:
        risk = "high"
        reasoning.append(
            "Exact-match pattern: every ingredient in the traditional record was found in the "
            "submitted composition, with no additions and no omissions. The traditional "
            "formulation is likely to qualify as prior art against a claim to this same "
            "formulation and use — but this is not itself a patent rejection; a claim framed "
            "around something other than the base formulation (e.g. a specific process) would "
            "need separate examination (see potential_novel_features)."
        )
    elif best.overlap_ratio >= 0.6:
        risk = "medium"
        reasoning.append(
            "Partial-match pattern: most of the traditional record's ingredients are present, "
            "but differences were found (an addition, an omission, or both). The overlapping "
            "core is still a likely prior-art signal; whether the differences are independently "
            "patentable cannot be determined by ingredient matching alone."
        )
    else:
        risk = "low"
        reasoning.append(
            "Only a minority of this record's ingredients overlap with the submitted "
            "composition. Treat this as a weak signal, not a confirmed prior-art match — "
            "consider it alongside any other closely-related records above."
        )

    reasoning.append(
        f"Closest record: {record.record_id} — {record.formulation_name} "
        f"({record.source_text}, known since ~{record.knowledge_known_since_years} years)."
    )

    return PriorArtAssessment(
        risk_level=risk,
        closest_record=record,
        what_was_already_known=what_known,
        what_appears_different=what_different,
        potential_novel_features=potential_novel,
        reasoning=reasoning,
    )
