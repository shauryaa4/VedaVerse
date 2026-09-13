"""
ABS-02 — Deterministic ABS-relevance rule engine.

Same philosophy as CLS-01 (backend/logic/classification.py), ROUTE-01
(backend/logic/routing.py) and TKDL-02 (backend/logic/tkdl_search.py):
explicit, ordered, deterministic rules over the frozen PIP — no ML, no LLM
call, every branch names the rule that fired. Consumes ONLY fields already
in backend/models/pip.py (per build spec section 9: "check whether it can
consume information already captured in the profile" before adding new
intake questions) — specifically `product.ingredient_sources`,
`product.biological_origin_known`, `product.biological_origin_region`,
`product.classical_basis`, `objective`, and `protection_target`.

THE LAW THIS ENCODES (kept short and explicit here — full text belongs in
the India legal corpus, not duplicated into code comments at length):

  - Biological Diversity Act, 2002 (BDA), as amended by the Biological
    Diversity (Amendment) Act, 2023, with Rules notified in 2024.
  - Section 3/3A: a "foreign entity" — a non-Indian citizen, a body
    corporate not incorporated in India, or (post-2023 amendment) a body
    corporate incorporated in India with certain non-Indian shareholding —
    needs prior NATIONAL BIODIVERSITY AUTHORITY (NBA) approval before
    obtaining any Indian biological resource for research, commercial
    use, bio-survey or bio-utilization.
  - Section 7: Indian citizens / companies / non-foreign entities need
    only give PRIOR INTIMATION to the relevant STATE BIODIVERSITY BOARD
    (SBB) for the same activities (a lighter-touch requirement than NBA
    approval).
  - Section 6: before applying for any IP right (patent or otherwise),
    IN INDIA OR OUTSIDE INDIA, based on an invention using a biological
    resource obtained from India, prior NBA approval is required — this
    applies regardless of where the patent will ultimately be filed, which
    is why this rule below does NOT gate on pip.jurisdiction.
  - The 2023 amendment / 2024 Rules introduced eased/simplified pathways
    for: AYUSH practitioners and the Indian systems-of-medicine industry,
    codified traditional knowledge, cultivated (vs wild-collected)
    medicinal plants, and a "normally traded commodities" exemption list
    notified separately by the NBA. This module does NOT have that
    notified list as data (no dataset to check it against — see build
    spec section 32, "do not invent facts") and says so explicitly rather
    than guessing whether a given ingredient is on it.

WHAT THIS MODULE CANNOT DO (say so, don't guess — abstention philosophy,
build spec section 18):
  - It has no field for "is the user's company foreign-owned" (not in the
    frozen PIP), so it can point at "NBA vs SBB" as parallel possibilities
    rather than resolve which one applies.
  - `biological_origin_region` is free text, not a controlled country/state
    list — matching below is a simple keyword heuristic, not authoritative.
  - It cannot check the NBA's "normally traded commodities" exemption list,
    because no such list is loaded as data anywhere in this codebase.
"""

from backend.models.abs_models import ABSAssessment
from backend.models.pip import ProductIntelligenceProfile

_INDIA_KEYWORDS = ("india", "bharat", "indian")
_NON_INDIA_HINTS = ("imported", "sourced from outside india", "not india", "abroad", "outside india")
# Explicit vague/non-answer phrases. Checked BEFORE the generic short-string
# non-India fallback below, so a genuinely ambiguous one-word answer like
# "unclear" or "unknown" falls through to the ambiguous/"possible" branch in
# assess_abs() instead of being misread as a confident non-India signal just
# because it's short and doesn't mention India.
_AMBIGUOUS_HINTS = ("unclear", "unknown", "unsure", "not sure", "n/a", "na", "unspecified", "tbd", "don't know", "dont know")

# Biological Diversity Act "biological resource" (s.2(c)) covers plants, animals
# and micro-organisms (and their parts/genetic material) — it does NOT cover
# minerals or purely synthetic substances. Mirrors the same IngredientSource
# enum already used everywhere else (pip.py / tkdl.py) — no new vocabulary.
_BIOLOGICAL_SOURCE_TYPES = {"plant", "animal", "microbial"}


def _region_signals_india(region: str) -> bool:
    r = region.lower()
    return any(k in r for k in _INDIA_KEYWORDS)


def _region_signals_ambiguous(region: str) -> bool:
    r = region.lower().strip()
    return any(k in r for k in _AMBIGUOUS_HINTS)


def _region_signals_non_india(region: str) -> bool:
    r = region.lower()
    if any(k in r for k in _NON_INDIA_HINTS):
        return True
    # A region string that names a country/place but never mentions India at all
    # is treated as a (weak) non-India signal only if it's non-trivially specific
    # (avoids misreading a blank/one-word ambiguous entry as "not India", and
    # avoids misreading an explicit vague answer like "unclear" as non-India --
    # both should fall through to the ambiguous/"possible" branch instead).
    return (
        bool(r.strip())
        and not _region_signals_india(r)
        and not _region_signals_ambiguous(r)
        and len(r.split()) <= 4
    )


def _has_biological_ingredients(pip: ProductIntelligenceProfile) -> bool:
    return any(s in _BIOLOGICAL_SOURCE_TYPES for s in pip.product.ingredient_sources)


def _wants_ip_protection(pip: ProductIntelligenceProfile) -> bool:
    ip_objectives = {"patentability", "prior_art"}
    ip_targets = {"formulation", "process"}
    return (
        any(o in ip_objectives for o in pip.objective)
        or pip.protection_target in ip_targets
    )


def assess_abs(pip: ProductIntelligenceProfile) -> ABSAssessment:
    reasoning: list[str] = []
    authority_guidance: list[str] = []

    # --- Rule 1: no declared biological ingredient sources at all -----------
    if not pip.product.ingredient_sources:
        reasoning.append(
            "No ingredient source types (plant / animal / mineral / microbial / "
            "synthetic) were captured for this product. ABS relevance cannot be "
            "ruled in or out without this — treat as unresolved, not as "
            "'not applicable'."
        )
        assessment = ABSAssessment(relevance="possible", reasoning=reasoning)
        return _apply_ip_filing_flag(pip, assessment)

    # --- Rule 2: only mineral / synthetic sources -> BDA scope doesn't reach it
    if not _has_biological_ingredients(pip):
        reasoning.append(
            "Declared ingredient sources are limited to mineral and/or synthetic "
            "materials. The Biological Diversity Act, 2002 (s.2(c)) defines "
            "'biological resource' as plants, animals, micro-organisms and their "
            "parts/genetic material — it does not extend to purely mineral or "
            "fully synthetic ingredients on the facts given."
        )
        assessment = ABSAssessment(relevance="not_applicable", reasoning=reasoning)
        return _apply_ip_filing_flag(pip, assessment)

    # From here on, at least one plant/animal/microbial ingredient is declared.

    # --- Rule 3: biological origin not known -> possible, ask to determine --
    if pip.product.biological_origin_known != "yes":
        reasoning.append(
            "At least one ingredient is plant-, animal- or microbe-derived, but "
            "whether it was 'obtained from India' (the BDA's trigger phrase) has "
            "not been established. This is a material fact for ABS purposes and "
            "should be confirmed before proceeding — treat as unresolved rather "
            "than assuming either way."
        )
        authority_guidance.append(
            "Once origin is confirmed: if the resource was obtained from India, "
            "either the National Biodiversity Authority (foreign entities) or the "
            "relevant State Biodiversity Board (Indian citizens/companies, by "
            "prior intimation) may need to be approached before commercial "
            "utilisation."
        )
        assessment = ABSAssessment(
            relevance="possible", reasoning=reasoning, applicable_authority_guidance=authority_guidance
        )
        return _apply_ip_filing_flag(pip, assessment)

    # --- Rule 4: origin known — read the free-text region -------------------
    region = pip.product.biological_origin_region or ""

    # IMPORTANT: non-India must be checked before India. A phrase like "outside
    # India" contains the literal substring "india", so checking the India
    # keyword first would misclassify an explicit non-India statement as
    # India-linked. See _region_signals_non_india's own hint list, which
    # already handles these phrases explicitly for exactly this reason.
    if _region_signals_non_india(region):
        reasoning.append(
            f"Biological origin is declared as outside India ('{region}'). India's "
            "Biological Diversity Act access-approval requirements (NBA/SBB) are "
            "generally triggered by resources obtained from India, so they are unlikely "
            "to apply to this specific resource on the facts given."
        )
        reasoning.append(
            "This does NOT mean no ABS obligation exists at all — the resource's country "
            "of origin may have its own ABS law, and if that country and India are both "
            "parties to the Nagoya Protocol, cross-border obligations (prior informed "
            "consent / mutually agreed terms in the country of origin) can still apply. "
            "This tool only models India's domestic regime."
        )
        assessment = ABSAssessment(relevance="unlikely", reasoning=reasoning)
        return _apply_ip_filing_flag(pip, assessment)

    if _region_signals_india(region):
        reasoning.append(
            f"Biological origin is declared as India-linked ('{region}'). Under the "
            "Biological Diversity Act, 2002, obtaining a biological resource occurring "
            "in India for research, commercial utilisation or bio-survey/bio-utilisation "
            "generally requires either prior National Biodiversity Authority (NBA) "
            "approval (foreign entities / foreign-linked companies, s.3-3A) or prior "
            "intimation to the State Biodiversity Board (Indian citizens/companies, s.7)."
        )
        authority_guidance.append(
            "This tool cannot determine whether your entity counts as 'foreign' under "
            "s.3-3A (that depends on ownership/incorporation details not captured here) "
            "— confirm entity status, then approach the NBA or the relevant SBB accordingly."
        )
        if pip.product.classical_basis == "yes":
            reasoning.append(
                "The product is declared as classical/unmodified. The 2023 amendment and "
                "2024 Rules introduced eased pathways for codified traditional knowledge and "
                "the AYUSH/Indian-systems-of-medicine sector — this may qualify for a "
                "simplified route, but this changed recently and the exact current "
                "conditions must be verified against present NBA guidance rather than "
                "assumed from this tool."
            )
        reasoning.append(
            "Note: this tool has no data on the NBA's separately notified 'normally "
            "traded commodities' exemption list — it cannot check whether a specific "
            "ingredient is exempted on that basis."
        )
        assessment = ABSAssessment(
            relevance="likely", reasoning=reasoning, applicable_authority_guidance=authority_guidance
        )
        return _apply_ip_filing_flag(pip, assessment)

    # Ambiguous / unparseable free-text region.
    reasoning.append(
        f"Biological origin region was provided ('{region}') but could not be read as "
        "either India-linked or clearly non-India. Treat as unresolved rather than "
        "guessing — clarify whether the resource was obtained from India."
    )
    assessment = ABSAssessment(relevance="possible", reasoning=reasoning)
    return _apply_ip_filing_flag(pip, assessment)


def _apply_ip_filing_flag(pip: ProductIntelligenceProfile, assessment: ABSAssessment) -> ABSAssessment:
    """
    Section 6 check: prior NBA approval before applying for ANY IP right — in
    India or outside India — based on an invention using a biological resource
    obtained from India. Deliberately independent of pip.jurisdiction (a patent
    filed abroad using an Indian biological resource still needs this) and
    independent of the relevance verdict above (kept as its own flag, same
    reason TKDL-02 keeps ingredient-overlap risk separate from process-novelty
    signals — these are two different legal questions).
    """
    if not _has_biological_ingredients(pip):
        return assessment
    if pip.product.biological_origin_known != "yes":
        return assessment
    region = pip.product.biological_origin_region or ""
    if not _region_signals_india(region):
        return assessment
    if not _wants_ip_protection(pip):
        return assessment

    assessment.ip_filing_flag = True
    assessment.ip_filing_note = (
        "Section 6 of the Biological Diversity Act, 2002 requires prior NBA approval "
        "before applying for any IP right — whether in India or outside India — based "
        "on an invention that uses a biological resource obtained from India. This "
        "applies in addition to, and separately from, any access/utilisation approval "
        "under s.3-3A or s.7 above."
    )
    return assessment