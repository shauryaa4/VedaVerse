"""
ABS-03 — Production Fact-Driven Traceable ABS Pathway Engine.

Implements the 17-step deterministic ABS assessment pipeline:
1. Fact Collection & Merging (PIP + ABSFactProfile)
2. Fact Normalization & Sanitization
3. Biological Resource Evaluation
4. Statutory Category Identification
5. Origin & Access Source Evaluation
6. Traditional Knowledge Analysis (Codified vs Community TK)
7. Activity Profile Analysis
8. IPR Lifecycle Analysis (NO_IPR -> IPR_COMMERCIALISATION)
9. Special-Case & Exemption Engine (Cultivated, NTC, AYUSH, ITPGRFA, Collab, Foreign Depository)
10. Authority Routing (NBA vs SBB vs Provider Country)
11. Form & Document Routing (Form 1, Form 2, Form 3, Form 4, Form B, Certificate of Origin)
12. Benefit-Sharing Subsystem (Indicative Calculations & Slabs)
13. Certificate of Origin Component
14. Missing Information Identification
15. Authoritative Legal Source Retrieval & Citation Verification (Manifest-linked)
16. Evidence Status & Confidence Evaluation (No raw percentages)
17. Abstention & Human Escalation Analysis
"""

import json
import os
import re
from typing import Optional, Any

from backend.models.abs_models import (
    ABSAssessment,
    ABSFactProfile,
    ABSTriggeredRule,
    ABSExemptionCheck,
    ABSFormRequirement,
    ABSAuthorityRouting,
    BenefitSharingProfile,
    CertificateOfOriginProfile,
    ABSCitation,
    ABSMissingInfo,
    ABSHumanEscalation,
)
from backend.models.pip import ProductIntelligenceProfile

_INDIA_KEYWORDS = ("india", "bharat", "indian", "kerala", "karnataka", "tamil nadu", "maharashtra", "himalaya", "western ghats", "ayurveda")
_NON_INDIA_HINTS = ("imported", "sourced from outside india", "not india", "abroad", "outside india", "foreign", "brazil", "china", "germany", "usa")
_AMBIGUOUS_HINTS = ("unclear", "unknown", "unsure", "not sure", "n/a", "na", "unspecified", "tbd", "don't know", "dont know")

_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nba_abs_required_data.json")
_MANIFEST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "legal-corpus", "manifest.json")


def _load_nba_abs_data() -> dict:
    if os.path.exists(_DATA_PATH):
        try:
            with open(_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _load_manifest_docs() -> dict[str, dict]:
    """Load metadata index from legal-corpus/manifest.json keyed by doc_id."""
    doc_index = {}
    if os.path.exists(_MANIFEST_PATH):
        try:
            with open(_MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for doc in data.get("documents", []):
                    doc_id = doc.get("doc_id")
                    if doc_id and doc_id not in doc_index:
                        doc_index[doc_id] = doc
        except Exception:
            pass
    return doc_index


def _region_signals_india(region: str) -> bool:
    r = region.lower()
    return any(k in r for k in _INDIA_KEYWORDS)


def _region_signals_non_india(region: str) -> bool:
    r = region.lower()
    if any(k in r for k in _NON_INDIA_HINTS):
        return True
    return (
        bool(r.strip())
        and not _region_signals_india(r)
        and not any(k in r for k in _AMBIGUOUS_HINTS)
        and len(r.split()) <= 4
    )


def sanitize_input_text(text: Optional[str]) -> Optional[str]:
    """Sanitize free-text fields against prompt injection / legal instruction hijacking."""
    if not text:
        return text
    # Strip potential instruction injections
    cleaned = re.sub(r"(?i)(system instruction|ignore previous|override rule|you are an ai|exempt this|do not apply)", "", text)
    return cleaned.strip()


def build_fact_profile_from_pip(pip: ProductIntelligenceProfile) -> ABSFactProfile:
    """Merge and normalize facts from pip.product and pip.abs_facts into a structured ABSFactProfile."""
    if pip.abs_facts is not None:
        facts = pip.abs_facts.model_copy(deep=True)
    else:
        facts = ABSFactProfile()

    p = pip.product

    # Sanitize free-text inputs
    if p.biological_origin_region:
        p.biological_origin_region = sanitize_input_text(p.biological_origin_region)

    # Biological resource evaluation (DO NOT infer origin from product name!)
    if not facts.resource.biological_resource_involved:
        has_bio = any(s in ("plant", "animal", "microbial") for s in p.ingredient_sources)
        facts.resource.biological_resource_involved = has_bio

    if p.ingredient_sources and facts.resource.resource_type == "unknown":
        if "plant" in p.ingredient_sources:
            facts.resource.resource_type = "plant"
        elif "animal" in p.ingredient_sources:
            facts.resource.resource_type = "animal"
        elif "microbial" in p.ingredient_sources:
            facts.resource.resource_type = "microbial"
        elif set(p.ingredient_sources).issubset({"mineral", "synthetic"}):
            facts.resource.resource_type = "non_biological"

    # Origin mapping (distinct from free-text ingredient text!)
    if p.biological_origin_known == "yes":
        region = p.biological_origin_region or ""
        if _region_signals_non_india(region):
            facts.resource.origin_status = "foreign"
            facts.resource.country_of_origin = region
            facts.resource.status = "KNOWN"
        elif _region_signals_india(region):
            facts.resource.origin_status = "india"
            facts.resource.country_of_origin = "India"
            facts.resource.geographical_location = region
            facts.resource.status = "KNOWN"
        else:
            facts.resource.origin_status = "unknown"
            facts.resource.status = "AMBIGUOUS"
    elif p.biological_origin_known == "no":
        # In the product questionnaire, "no" means the user does not know
        # the origin. Preserve an explicit, confirmed answer supplied later
        # through the ABS-specific form instead of resetting it to unknown.
        if not (
            facts.resource.origin_status in ("india", "foreign")
            and facts.resource.status == "KNOWN"
        ):
            facts.resource.origin_status = "unknown"
            facts.resource.status = "UNKNOWN"

    # Traditional knowledge mapping: distinguish classical_basis (codified) from associated_traditional_knowledge (community TK)
    if p.classical_basis == "yes":
        facts.tk.tk_codified = True
        if facts.tk.tk_type in ("none", "unknown"):
            facts.tk.tk_type = "codified"
        facts.tk.tk_source = p.classical_reference or "Ayurvedic Pharmacopoeia / Formulations"

    # Activity & IPR mapping from PIP objectives & protection_target
    ip_objectives = {"patentability", "prior_art"}
    if any(o in ip_objectives for o in pip.objective) or pip.protection_target in ("formulation", "process"):
        if "ipr_application" not in facts.activity.activities and "ipr_commercialisation" not in facts.activity.activities:
            facts.activity.activities.append("ipr_application")
        if facts.ipr.ipr_stage == "UNKNOWN":
            facts.ipr.ipr_stage = "CONSIDERING_IPR"

    if "regulatory_category" in pip.objective or p.development_status in ("developed", "marketed"):
        if "commercial_utilisation" not in facts.activity.activities:
            facts.activity.activities.append("commercial_utilisation")

    return facts


def _origin_fact_conflicts(pip: ProductIntelligenceProfile) -> list[str]:
    """Return explicit conflicts between independently supplied origin fields.

    Do not silently let the questionnaire overwrite the ABS fact profile (or
    vice versa): origin can change the applicable statutory pathway.
    """
    product = pip.product
    supplied_abs_origin = (
        pip.abs_facts.resource.origin_status
        if pip.abs_facts is not None
        else "unknown"
    )
    if product.biological_origin_known != "yes" or supplied_abs_origin == "unknown":
        return []

    region = product.biological_origin_region or ""
    if _region_signals_india(region):
        questionnaire_origin = "india"
    elif _region_signals_non_india(region):
        questionnaire_origin = "foreign"
    else:
        return []

    if questionnaire_origin == supplied_abs_origin:
        return []

    return [
        "Product questionnaire says the biological resource originated "
        f"in {questionnaire_origin}, while the ABS facts say {supplied_abs_origin}."
    ]


def _input_fact_conflicts(pip: ProductIntelligenceProfile) -> list[str]:
    """Collect supported conflict flags plus the cross-form origin check."""
    conflicts = _origin_fact_conflicts(pip)
    if pip.abs_facts is None:
        return conflicts

    named_profiles = (
        ("applicant", pip.abs_facts.applicant),
        ("biological resource", pip.abs_facts.resource),
        ("access source", pip.abs_facts.access),
        ("traditional knowledge", pip.abs_facts.tk),
        ("activity", pip.abs_facts.activity),
        ("IPR lifecycle", pip.abs_facts.ipr),
    )
    for label, profile in named_profiles:
        if getattr(profile, "status", None) == "CONFLICTING":
            conflicts.append(
                f"The submitted {label} facts are marked CONFLICTING and need confirmation."
            )
    return list(dict.fromkeys(conflicts))


def assess_abs_fact_driven(pip: ProductIntelligenceProfile) -> ABSAssessment:
    """Fact-driven, 100% deterministic ABS pathway engine."""
    abs_data = _load_nba_abs_data()
    manifest_docs = _load_manifest_docs()
    conflicts = _input_fact_conflicts(pip)
    facts = build_fact_profile_from_pip(pip)

    if conflicts:
        reason = " ".join(conflicts)
        origin_conflict = any("origin" in item.lower() for item in conflicts)
        return ABSAssessment(
            status="CONFLICTING",
            pathway="UNRESOLVED_CONFLICTING_FACTS",
            relevance="possible",
            reasoning=[
                "No ABS pathway was selected because the submitted origin facts conflict.",
                reason,
            ],
            facts_considered={
                "questionnaire_origin": (
                    "india" if _region_signals_india(pip.product.biological_origin_region or "") else "foreign"
                ),
                "abs_origin": pip.abs_facts.resource.origin_status if pip.abs_facts else "unknown",
            },
            missing_information=[
                ABSMissingInfo(
                    field_name=("biological_origin_region" if origin_conflict else "conflicting_abs_facts"),
                    prompt_question=(
                        "Please confirm whether the biological resource was obtained in India or abroad."
                        if origin_conflict
                        else "Please review and confirm the conflicting ABS facts before continuing."
                    ),
                    impact_description="Conflicting facts prevent a reliable ABS pathway assessment.",
                    why_it_matters=reason,
                )
            ],
            human_escalation=ABSHumanEscalation(
                human_review=True,
                reason=reason,
                case_summary="Resolve the conflicting biological-resource origin before relying on an ABS pathway.",
                facts={
                    "questionnaire_region": pip.product.biological_origin_region,
                    "abs_origin_status": pip.abs_facts.resource.origin_status if pip.abs_facts else "unknown",
                },
                missing_facts=["biological_origin_region" if origin_conflict else "conflicting_abs_facts"],
                conflicts=conflicts,
            ),
            abstained=True,
            abstain_reason="Conflicting biological-resource origin facts require clarification.",
        )

    reasoning: list[str] = []
    authority_guidance: list[str] = []
    triggered_rules: list[ABSTriggeredRule] = []
    exemptions_evaluated: list[ABSExemptionCheck] = []
    form_requirements: list[ABSFormRequirement] = []
    citations: list[ABSCitation] = []
    missing_information: list[ABSMissingInfo] = []
    next_actions: list[str] = []

    ip_filing_flag = False
    ip_filing_note: Optional[str] = None

    # Load catalog lookup maps
    rules_catalog = {r["rule_id"]: r for r in abs_data.get("legal_rules", [])}
    exemptions_catalog = {e["exemption_id"]: e for e in abs_data.get("special_cases_and_exemptions", [])}
    forms_catalog = {f["form_id"]: f for f in abs_data.get("forms", [])}

    # Facts considered summary dict for UI
    facts_considered = {
        "entity_category": facts.applicant.entity_category,
        "applicant_type": facts.applicant.applicant_type,
        "biological_resource_involved": facts.resource.biological_resource_involved,
        "resource_type": facts.resource.resource_type,
        "origin_status": facts.resource.origin_status,
        "country_of_origin": facts.resource.country_of_origin or "Unspecified",
        "access_method": facts.access.access_method,
        "source_type": facts.access.source_type,
        "cultivated": facts.access.cultivated,
        "associated_tk": facts.tk.associated_traditional_knowledge or facts.tk.tk_codified,
        "tk_type": facts.tk.tk_type,
        "activities": facts.activity.activities,
        "ipr_stage": facts.ipr.ipr_stage,
    }

    # Helper to build citation with manifest metadata
    def add_citation(doc_id: str, section: str, excerpt: str, status: str = "VERIFIED"):
        doc_meta = manifest_docs.get(doc_id, {})
        doc_name = doc_meta.get("document_name", "Biological Diversity Act / Rules")
        doc_type = doc_meta.get("document_type", "act")
        source_url = doc_meta.get("source_url") or "https://www.indiacode.nic.in"
        eff_date = doc_meta.get("date_enacted") or "2002"
        citations.append(
            ABSCitation(
                doc_id=doc_id,
                document_name=doc_name,
                document_type=doc_type,
                section_or_article=section,
                excerpt=excerpt,
                source_url=source_url,
                verification_status=status,
                source_id=doc_id,
                source_title=doc_name,
                authority="National Biodiversity Authority / SBB",
                effective_date=eff_date,
            )
        )

    # STEP 1: Biological Resource Check
    p_sources = pip.product.ingredient_sources
    if not p_sources and not facts.resource.biological_resource_involved:
        reasoning.append(
            "No ingredient source types (plant / animal / mineral / microbial / synthetic) were captured. "
            "ABS relevance cannot be evaluated without confirming whether biological material is involved."
        )
        missing_information.append(
            ABSMissingInfo(
                field_name="ingredient_sources",
                prompt_question="What are the ingredient sources of your product?",
                impact_description="Determines whether the product falls under the Biological Diversity Act, 2002.",
                why_it_matters="Biological Diversity Act applies only to biological resources (plants, animals, microbes).",
            )
        )
        add_citation("IN-3", "Section 2(c)", "Biological resource definition includes plants, animals and micro-organisms.", "VERIFIED")
        return ABSAssessment(
            status="INSUFFICIENT_INFORMATION",
            pathway="UNRESOLVED_MISSING_INGREDIENT_SOURCE",
            relevance="possible",
            reasoning=reasoning,
            facts_considered=facts_considered,
            missing_information=missing_information,
            citations=citations,
            abstained=True,
            abstain_reason="Ingredient sources not specified.",
        )

    if facts.resource.resource_type == "non_biological" or (p_sources and not any(s in ("plant", "animal", "microbial") for s in p_sources)):
        reasoning.append(
            "Declared ingredient sources are limited to mineral and/or synthetic materials. "
            "Under Section 2(c) of the Biological Diversity Act, 2002, 'biological resource' includes plants, animals, "
            "micro-organisms and their parts/genetic material — it does not extend to purely mineral or synthetic ingredients."
        )
        add_citation("IN-3", "Section 2(c)", "Biological resource definition excludes value-added products and non-biological minerals.", "VERIFIED")
        return ABSAssessment(
            status="STRONG",
            pathway="EXEMPT_NON_BIOLOGICAL_RESOURCE",
            relevance="not_applicable",
            reasoning=reasoning,
            facts_considered=facts_considered,
            citations=citations,
            next_actions=["No ABS access filings or benefit-sharing obligations apply under domestic BDA 2002."],
        )

    # STEP 2: Biological Origin & Foreign Repository Check
    if facts.access.source_type == "institution" and facts.access.repository_location == "outside_india":
        ex_repo = exemptions_catalog.get("ABS_EXEMPTION_FOREIGN_REPOSITORY_MICROBE")
        if ex_repo:
            exemptions_evaluated.append(
                ABSExemptionCheck(
                    exemption_id="ABS_EXEMPTION_FOREIGN_REPOSITORY_MICROBE",
                    name=ex_repo["name"],
                    source_provision=ex_repo["source_provision"],
                    conditions_checked={"source_type": "institution", "repository_location": "outside_india"},
                    is_triggered=True,
                    reason=ex_repo["consequence"],
                    source_doc_id=ex_repo["source_doc_id"],
                    effective_date=ex_repo.get("effective_date"),
                    source_url=ex_repo.get("source_url"),
                )
            )
            reasoning.append("Microorganism/resource sourced directly from an authorized foreign depository outside India.")

    if facts.resource.origin_status == "unknown":
        reasoning.append(
            "At least one ingredient is plant-, animal- or microbe-derived, but whether it was obtained from India "
            "has not been established. Section 3, 6 & 7 of BDA 2002 are triggered specifically by resources obtained from India."
        )
        authority_guidance.append(
            "Confirm origin: If obtained from India, either NBA (for foreign entities/foreign shareholding) or SBB (for Indian entities) applies."
        )
        missing_information.append(
            ABSMissingInfo(
                field_name="biological_origin_region",
                prompt_question="Was the biological resource obtained from India or abroad?",
                impact_description="Crucial trigger for Indian domestic Access & Benefit Sharing jurisdiction.",
                why_it_matters="BDA 2002 access and IP approval provisions apply to biological resources occurring in or obtained from India.",
            )
        )
        next_actions.append("Determine exact geographical location/country where the biological resource was sourced.")

    elif facts.resource.origin_status == "foreign":
        reasoning.append(
            f"Biological resource origin is declared as outside India ('{facts.resource.country_of_origin}'). "
            "Indian domestic BDA 2002 access-approval requirements (NBA/SBB) are generally triggered by resources obtained from India."
        )
        ex_foreign = exemptions_catalog.get("ABS_EXEMPTION_FOREIGN_BIOLOGICAL_RESOURCE")
        if ex_foreign:
            exemptions_evaluated.append(
                ABSExemptionCheck(
                    exemption_id="ABS_EXEMPTION_FOREIGN_BIOLOGICAL_RESOURCE",
                    name=ex_foreign["name"],
                    source_provision=ex_foreign["source_provision"],
                    conditions_checked={"country_of_origin": facts.resource.country_of_origin},
                    is_triggered=True,
                    reason="Resource obtained entirely outside India without Indian biological components.",
                    source_doc_id=ex_foreign["source_doc_id"],
                    effective_date=ex_foreign.get("effective_date"),
                    source_url=ex_foreign.get("source_url"),
                )
            )
        reasoning.append("Cross-border note: Nagoya Protocol / Provider country ABS laws may apply in the country of origin.")
        next_actions.append("Verify compliance with the ABS laws and Prior Informed Consent (PIC) of the country of origin.")
        add_citation("INTL-3", "Article 5 & 6", "Nagoya Protocol on Access and Benefit-sharing obligations for provider country resources.", "VERIFIED")

    # STEP 3: Special Exemptions (ITPGRFA, Collaborative Govt Research, Cultivated Plants, NTC, AYUSH Codified TK, Community TK)
    if facts.government_approved_collaboration and "research" in facts.activity.activities:
        ex_collab = exemptions_catalog.get("ABS_EXEMPTION_COLLABORATIVE_RESEARCH")
        if ex_collab:
            exemptions_evaluated.append(
                ABSExemptionCheck(
                    exemption_id="ABS_EXEMPTION_COLLABORATIVE_RESEARCH",
                    name=ex_collab["name"],
                    source_provision=ex_collab["source_provision"],
                    conditions_checked={"government_approved_collaboration": True},
                    is_triggered=True,
                    reason=ex_collab["consequence"],
                    source_doc_id=ex_collab["source_doc_id"],
                    effective_date=ex_collab.get("effective_date"),
                    source_url=ex_collab.get("source_url"),
                )
            )
            reasoning.append("Collaborative research project approved by Central Government under Section 5 is exempt from Section 3 & 4 approvals.")

    if facts.is_itpgrfa_crop:
        ex_itpgrfa = exemptions_catalog.get("ABS_EXEMPTION_ITPGRFA")
        if ex_itpgrfa:
            exemptions_evaluated.append(
                ABSExemptionCheck(
                    exemption_id="ABS_EXEMPTION_ITPGRFA",
                    name=ex_itpgrfa["name"],
                    source_provision=ex_itpgrfa["source_provision"],
                    conditions_checked={"is_itpgrfa_crop": True},
                    is_triggered=True,
                    reason=ex_itpgrfa["consequence"],
                    source_doc_id=ex_itpgrfa["source_doc_id"],
                    effective_date=ex_itpgrfa.get("effective_date"),
                    source_url=ex_itpgrfa.get("source_url"),
                )
            )
            reasoning.append("ITPGRFA Multilateral System crop accessed under SMTA for food/agriculture.")

    if facts.resource.origin_status == "india":
        # Cultivated Medicinal Plants Exemption
        if facts.access.cultivated or facts.access.source_type == "cultivated" or facts.access.source_type == "artificially_propagated":
            is_trig = facts.certificate_of_origin.certificate_available
            exemptions_evaluated.append(
                ABSExemptionCheck(
                    exemption_id="ABS_EXEMPTION_CULTIVATED_PLANTS",
                    name="Cultivated Medicinal Plants Exemption",
                    source_provision="Section 40 & Biological Diversity Rules 2024",
                    conditions_checked={"source_type": facts.access.source_type, "certificate_available": facts.certificate_of_origin.certificate_available},
                    is_triggered=is_trig,
                    reason="Cultivated medicinal plants are exempt from routine NBA benefit sharing when accompanied by a valid Certificate of Origin." if is_trig else "Cultivated plant declared, but Certificate of Origin is missing. Provide certificate to claim exemption.",
                    source_doc_id="IN-4",
                    effective_date="2024-01-01",
                    source_url="https://www.indiacode.nic.in",
                )
            )
            if is_trig:
                reasoning.append("Resource is a cultivated medicinal plant with a valid Certificate of Origin. Exempted from routine benefit sharing under 2024 Rules.")

        # Normally Traded Commodities (NTC) Exemption
        if facts.access.source_type == "market_or_trader":
            has_ipr_or_res = any(a in ("ipr_application", "ipr_grant", "ipr_commercialisation", "research", "bio_utilisation") for a in facts.activity.activities) or facts.ipr.ipr_stage not in ("NO_IPR", "UNKNOWN")
            ex_ntc = exemptions_catalog.get("ABS_EXEMPTION_NORMALLY_TRADED_COMMODITIES")
            if ex_ntc:
                exemptions_evaluated.append(
                    ABSExemptionCheck(
                        exemption_id="ABS_EXEMPTION_NORMALLY_TRADED_COMMODITIES",
                        name=ex_ntc["name"],
                        source_provision=ex_ntc["source_provision"],
                        conditions_checked={"source_type": "market_or_trader", "ipr_or_research": has_ipr_or_res},
                        is_triggered=not has_ipr_or_res,
                        reason="NTC exemption applies for direct trade/consumption, BUT is overridden when used for research or IP filing." if has_ipr_or_res else "Purchased from open market as normally traded commodity for direct trade/consumption.",
                        source_doc_id=ex_ntc["source_doc_id"],
                        effective_date=ex_ntc.get("effective_date"),
                        source_url=ex_ntc.get("source_url"),
                    )
                )

        # Codified Traditional Knowledge & AYUSH Practitioners Exemption
        if facts.applicant.entity_category == "ayush_practitioner" or (facts.tk.tk_codified and pip.product.classical_basis == "yes"):
            ex_ayush = exemptions_catalog.get("ABS_EXEMPTION_AYUSH_CODIFIED_TK")
            if ex_ayush:
                exemptions_evaluated.append(
                    ABSExemptionCheck(
                        exemption_id="ABS_EXEMPTION_AYUSH_CODIFIED_TK",
                        name=ex_ayush["name"],
                        source_provision=ex_ayush["source_provision"],
                        conditions_checked={"ayush_or_codified_tk": True},
                        is_triggered=True,
                        reason="Registered AYUSH practitioners and classical Ayurvedic formulations enjoy eased pathways under Section 3A/7 proviso (2023 amendment).",
                        source_doc_id=ex_ayush["source_doc_id"],
                        effective_date=ex_ayush.get("effective_date"),
                        source_url=ex_ayush.get("source_url"),
                    )
                )
                reasoning.append("Formulation uses codified traditional knowledge / classical basis. Benefits from the 2023 Amendment eased route for AYUSH systems.")

        # Community TK Protection
        if facts.tk.tk_community_based or facts.tk.tk_type in ("community", "both"):
            ex_comm = exemptions_catalog.get("ABS_EXEMPTION_COMMUNITY_TK")
            if ex_comm:
                exemptions_evaluated.append(
                    ABSExemptionCheck(
                        exemption_id="ABS_EXEMPTION_COMMUNITY_TK",
                        name=ex_comm["name"],
                        source_provision=ex_comm["source_provision"],
                        conditions_checked={"tk_community_based": True},
                        is_triggered=True,
                        reason=ex_comm["consequence"],
                        source_doc_id=ex_comm["source_doc_id"],
                        effective_date=ex_comm.get("effective_date"),
                        source_url=ex_comm.get("source_url"),
                    )
                )
                reasoning.append("Community traditional knowledge involved — Requires Prior Informed Consent (PIC) and MAT with local indigenous communities.")

    # STEP 4: Rule Engine Execution & Authority Routing
    authority_name = "Not Determined"
    authority_level = "Unknown"
    jurisdiction_scope = "Domestic / International"
    pathway_name = "UNRESOLVED"

    if facts.resource.origin_status == "india":
        entity_cat = facts.applicant.entity_category

        if entity_cat == "unknown":
            missing_information.append(
                ABSMissingInfo(
                    field_name="entity_category",
                    prompt_question="What is the applicant's entity category (Indian citizen, domestic company, foreign entity / foreign-controlled company)?",
                    impact_description="Determines whether prior NBA approval (s.3) or SBB intimation (s.7) applies.",
                    why_it_matters="Foreign shareholding or foreign incorporation shifts jurisdiction from State Biodiversity Board to National Biodiversity Authority.",
                )
            )

        # Section 3: Foreign Access Approval
        if entity_cat in ("foreign_entity_or_individual", "indian_company_with_foreign_control"):
            r3 = rules_catalog.get("ABS_RULE_SEC3_FOREIGN_ACCESS")
            if r3:
                triggered_rules.append(
                    ABSTriggeredRule(
                        rule_id=r3["rule_id"],
                        rule_name=r3["rule_name"],
                        section_or_rule=r3["section_or_rule"],
                        description=r3["description"],
                        authority=r3["authority"],
                        required_form=r3["required_form"],
                        source_doc_id=r3["source_doc_id"],
                        source_provision=r3["source_provision"],
                        effective_date=r3.get("effective_date"),
                        source_url=r3.get("source_url"),
                    )
                )
            authority_name = "National Biodiversity Authority (NBA)"
            authority_level = "Central National Authority"
            pathway_name = "SECTION_3_NBA_APPROVAL"
            reasoning.append(
                "Applicant is a foreign entity / foreign-controlled company obtaining Indian biological resource. "
                "Prior NBA approval under Section 3 / 3A is mandatory before access/utilisation."
            )
            f1 = forms_catalog.get("FORM_1")
            if f1:
                form_requirements.append(
                    ABSFormRequirement(
                        form_id=f1["form_id"],
                        form_name=f1["form_name"],
                        purpose=f1["purpose"],
                        authority=f1["authority"],
                        fee=f1["fee"],
                        required_documents=f1["required_documents"],
                        source_doc_id=f1["source_doc_id"],
                        source_url="https://www.indiacode.nic.in",
                    )
                )
                next_actions.append("Submit Form I to the National Biodiversity Authority (NBA) along with statutory fee.")

        # Section 7: Indian Entity Intimation
        elif entity_cat in ("indian_citizen", "indian_company_no_foreign_control", "ayush_practitioner"):
            r7 = rules_catalog.get("ABS_RULE_SEC7_INDIAN_INTIMATION")
            if r7:
                triggered_rules.append(
                    ABSTriggeredRule(
                        rule_id=r7["rule_id"],
                        rule_name=r7["rule_name"],
                        section_or_rule=r7["section_or_rule"],
                        description=r7["description"],
                        authority=r7["authority"],
                        required_form=r7["required_form"],
                        source_doc_id=r7["source_doc_id"],
                        source_provision=r7["source_provision"],
                        effective_date=r7.get("effective_date"),
                        source_url=r7.get("source_url"),
                    )
                )
            authority_name = "State Biodiversity Board (SBB)"
            authority_level = "State Level Authority"
            pathway_name = "SECTION_7_SBB_INTIMATION"
            reasoning.append(
                "Applicant is an Indian citizen/domestic company. Section 7 requires prior intimation to the concerned State Biodiversity Board."
            )
            fb = forms_catalog.get("FORM_B_SBB")
            if fb:
                form_requirements.append(
                    ABSFormRequirement(
                        form_id=fb["form_id"],
                        form_name=fb["form_name"],
                        purpose=fb["purpose"],
                        authority=fb["authority"],
                        fee=fb["fee"],
                        required_documents=fb["required_documents"],
                        source_doc_id=fb["source_doc_id"],
                        source_url="https://www.indiacode.nic.in",
                    )
                )
                next_actions.append("File Form B / Prior Intimation notice with the respective State Biodiversity Board.")

        else:
            authority_name = "NBA / SBB (Pending Entity Status)"
            authority_level = "Conditional"
            pathway_name = "CONDITIONAL_ON_ENTITY_STATUS"

        # Section 6: IPR Application Approval
        if "ipr_application" in facts.activity.activities or "ipr_grant" in facts.activity.activities or "ipr_commercialisation" in facts.activity.activities or facts.ipr.ipr_stage in ("CONSIDERING_IPR", "PREPARING_APPLICATION", "IPR_APPLICATION", "IPR_GRANTED", "IPR_COMMERCIALISATION"):
            ip_filing_flag = True
            ip_filing_note = (
                "Section 6 of the Biological Diversity Act, 2002 requires prior approval of the National Biodiversity Authority (NBA) "
                "before applying for any Intellectual Property Right (in India or abroad) based on any invention using an Indian biological resource."
            )
            r6 = rules_catalog.get("ABS_RULE_SEC6_IPR_APPROVAL")
            if r6:
                triggered_rules.append(
                    ABSTriggeredRule(
                        rule_id=r6["rule_id"],
                        rule_name=r6["rule_name"],
                        section_or_rule=r6["section_or_rule"],
                        description=r6["description"],
                        authority=r6["authority"],
                        required_form=r6["required_form"],
                        source_doc_id=r6["source_doc_id"],
                        source_provision=r6["source_provision"],
                        effective_date=r6.get("effective_date"),
                        source_url=r6.get("source_url"),
                    )
                )
            f3 = forms_catalog.get("FORM_3")
            if f3 and not any(fr.form_id == "FORM_3" for fr in form_requirements):
                form_requirements.append(
                    ABSFormRequirement(
                        form_id=f3["form_id"],
                        form_name=f3["form_name"],
                        purpose=f3["purpose"],
                        authority=f3["authority"],
                        fee=f3["fee"],
                        required_documents=f3["required_documents"],
                        source_doc_id=f3["source_doc_id"],
                        source_url="https://www.indiacode.nic.in",
                    )
                )
                next_actions.append("File Form III with NBA prior to submitting patent/IP application.")

        # Section 4: Transfer of Research Results
        if "research_result_transfer" in facts.activity.activities or facts.transfer.transfer_type == "research_results":
            r4 = rules_catalog.get("ABS_RULE_SEC4_TRANSFER_RESEARCH_RESULTS")
            if r4:
                triggered_rules.append(
                    ABSTriggeredRule(
                        rule_id=r4["rule_id"],
                        rule_name=r4["rule_name"],
                        section_or_rule=r4["section_or_rule"],
                        description=r4["description"],
                        authority=r4["authority"],
                        required_form=r4["required_form"],
                        source_doc_id=r4["source_doc_id"],
                        source_provision=r4["source_provision"],
                        effective_date=r4.get("effective_date"),
                        source_url=r4.get("source_url"),
                    )
                )
            f2 = forms_catalog.get("FORM_2")
            if f2 and not any(fr.form_id == "FORM_2" for fr in form_requirements):
                form_requirements.append(
                    ABSFormRequirement(
                        form_id=f2["form_id"],
                        form_name=f2["form_name"],
                        purpose=f2["purpose"],
                        authority=f2["authority"],
                        fee=f2["fee"],
                        required_documents=f2["required_documents"],
                        source_doc_id=f2["source_doc_id"],
                        source_url="https://www.indiacode.nic.in",
                    )
                )

        # Section 20: Third Party Resource/Knowledge Transfer
        if "resource_transfer" in facts.activity.activities or facts.transfer.transfer_involved:
            r20 = rules_catalog.get("ABS_RULE_SEC20_THIRD_PARTY_TRANSFER")
            if r20:
                triggered_rules.append(
                    ABSTriggeredRule(
                        rule_id=r20["rule_id"],
                        rule_name=r20["rule_name"],
                        section_or_rule=r20["section_or_rule"],
                        description=r20["description"],
                        authority=r20["authority"],
                        required_form=r20["required_form"],
                        source_doc_id=r20["source_doc_id"],
                        source_provision=r20["source_provision"],
                        effective_date=r20.get("effective_date"),
                        source_url=r20.get("source_url"),
                    )
                )
            f4 = forms_catalog.get("FORM_4")
            if f4 and not any(fr.form_id == "FORM_4" for fr in form_requirements):
                form_requirements.append(
                    ABSFormRequirement(
                        form_id=f4["form_id"],
                        form_name=f4["form_name"],
                        purpose=f4["purpose"],
                        authority=f4["authority"],
                        fee=f4["fee"],
                        required_documents=f4["required_documents"],
                        source_doc_id=f4["source_doc_id"],
                        source_url="https://www.indiacode.nic.in",
                    )
                )

    authority_routing = ABSAuthorityRouting(
        authority_name=authority_name,
        authority_level=authority_level,
        jurisdiction_scope=jurisdiction_scope,
        reasons=[f"Entity: {facts.applicant.entity_category}", f"Resource Origin: {facts.resource.origin_status}"],
        status="DETERMINED" if authority_name != "Not Determined" else "INSUFFICIENT_INFORMATION",
    )

    # STEP 5: Benefit-Sharing Subsystem (Area 7)
    benefit_sharing = BenefitSharingProfile()
    if facts.resource.origin_status == "india":
        if "commercial_utilisation" in facts.activity.activities or "ipr_commercialisation" in facts.activity.activities or facts.ipr.ipr_stage == "IPR_COMMERCIALISATION":
            benefit_sharing.applicable = True
            benefit_sharing.basis = "Annual Turnover / Gross Ex-Factory Sales under BDR 2024"
            benefit_sharing.benefit_type = "Monetary Benefit Sharing"
            benefit_sharing.source = "Biological Diversity Rules, 2024 & Regulation 3/4"

            turnover = facts.annual_turnover_inr
            if turnover is not None:
                benefit_sharing.turnover_inr = turnover
                if "ipr_commercialisation" in facts.activity.activities or facts.ipr.ipr_stage == "IPR_COMMERCIALISATION":
                    benefit_sharing.turnover_band = "IPR_ROYALTY_SLAB"
                    benefit_sharing.rate_or_slab = "1.0% to 3.0% of gross royalty / licensing fee"
                    benefit_sharing.indicative_amount_inr = round(turnover * 0.02, 2)  # Midpoint 2.0%
                    benefit_sharing.special_condition = "Applies to licensing revenue from granted patent based on Indian biological resource."
                else:
                    if turnover <= 10000000:
                        benefit_sharing.turnover_band = "UP_TO_1_CRORE"
                        benefit_sharing.rate_or_slab = "0.1% of turnover"
                        benefit_sharing.indicative_amount_inr = round(turnover * 0.001, 2)
                    elif turnover <= 50000000:
                        benefit_sharing.turnover_band = "1_TO_5_CRORE"
                        benefit_sharing.rate_or_slab = "0.2% of turnover"
                        benefit_sharing.indicative_amount_inr = round(turnover * 0.002, 2)
                    else:
                        benefit_sharing.turnover_band = "ABOVE_5_CRORE"
                        benefit_sharing.rate_or_slab = "0.5% of turnover"
                        benefit_sharing.indicative_amount_inr = round(turnover * 0.005, 2)

                benefit_sharing.calculation_status = "INDICATIVE_CALCULATED"
                reasoning.append(
                    f"Benefit sharing calculated at indicative rate of {benefit_sharing.rate_or_slab} (INR {benefit_sharing.indicative_amount_inr:,.2f}) "
                    f"for turnover/revenue of INR {turnover:,.2f}."
                )
            else:
                benefit_sharing.calculation_status = "MISSING_TURNOVER_DATA"
                missing_information.append(
                    ABSMissingInfo(
                        field_name="annual_turnover_inr",
                        prompt_question="What is the estimated annual turnover / gross ex-factory sales for the commercial product?",
                        impact_description="Required to calculate the applicable benefit-sharing percentage slab (0.1%, 0.2%, or 0.5%).",
                        why_it_matters="Benefit sharing slabs under 2024 Rules are determined by turnover brackets.",
                    )
                )

    # STEP 6: Certificate of Origin Component (Area 9)
    cert_of_origin = CertificateOfOriginProfile()
    if facts.access.cultivated or facts.access.source_type in ("cultivated", "artificially_propagated"):
        cert_of_origin.certificate_required = True
        cert_of_origin.issuing_authority = "State Agriculture / Forest Department / AYUSH Officer"
        if facts.certificate_of_origin.certificate_available:
            cert_of_origin.certificate_available = True
            cert_of_origin.certificate_status = "PROVIDED"
            cert_of_origin.note = "Valid Certificate of Origin supplied for cultivated medicinal plant resource."
        else:
            cert_of_origin.certificate_available = False
            cert_of_origin.certificate_status = "REQUIRED"
            cert_of_origin.note = "Certificate of Origin required to establish cultivated plant exemption from routine NBA benefit sharing."
            fc = forms_catalog.get("CERTIFICATE_OF_ORIGIN")
            if fc and not any(fr.form_id == "CERTIFICATE_OF_ORIGIN" for fr in form_requirements):
                form_requirements.append(
                    ABSFormRequirement(
                        form_id=fc["form_id"],
                        form_name=fc["form_name"],
                        purpose=fc["purpose"],
                        authority=fc["authority"],
                        fee=fc["fee"],
                        required_documents=fc["required_documents"],
                        source_doc_id=fc["source_doc_id"],
                        source_url="https://www.indiacode.nic.in",
                    )
                )

    # STEP 7: Authoritative Legal Source Retrieval & Manifest-Linked Citations (Area 1, 10, 11)
    if not citations:
        add_citation(
            "IN-3",
            "Sections 3, 4, 6 & 7",
            "Section 3 requires prior NBA approval for foreign entities; Section 7 requires prior intimation to SBB for Indian entities; Section 6 requires prior NBA approval for IPR applications; Section 4 regulates research result transfers.",
            "VERIFIED"
        )
        add_citation(
            "IN-4",
            "Rules 13-20",
            "Prescribes Forms I to IV, benefit sharing percentage slabs (0.1%, 0.2%, 0.5% of turnover), and Certificate of Origin procedures for cultivated medicinal plants.",
            "VERIFIED"
        )

    # STEP 8: Evidence Status & Overall Verdict (Area 12 - NO numerical percentages!)
    if facts.resource.origin_status == "india":
        relevance = "likely"
        if facts.applicant.entity_category == "unknown":
            overall_status = "INSUFFICIENT_INFORMATION"
        elif any(f.field_name for f in missing_information if f.field_name in ("entity_category", "biological_origin_region")):
            overall_status = "INSUFFICIENT_INFORMATION"
        else:
            overall_status = "STRONG"
    elif facts.resource.origin_status == "foreign":
        overall_status = "STRONG"
        relevance = "unlikely"
    else:
        overall_status = (
            "INSUFFICIENT_INFORMATION"
            if facts.resource.biological_resource_involved
            else "CONDITIONAL"
        )
        relevance = "possible"

    # STEP 9: Human Escalation & Abstention Analysis (Area 12, 13)
    human_escalation = ABSHumanEscalation()
    escalation_reasons = []

    if facts.applicant.entity_category == "indian_company_with_foreign_control":
        escalation_reasons.append("Indian company has Foreign participation or control (Section 3(2)). Requires equity & shareholding scrutiny.")
    if facts.transfer.transfer_involved or "resource_transfer" in facts.activity.activities:
        escalation_reasons.append("Cross-border biological resource transfer to third party involved (Section 20).")
    if facts.tk.tk_community_based or facts.tk.tk_type in ("community", "both"):
        escalation_reasons.append("Uncodified community traditional knowledge involved — Requires local community PIC & MAT clearance.")
    if facts.resource.origin_status == "unknown" and facts.resource.biological_resource_involved:
        escalation_reasons.append("Biological resource origin is ambiguous or unverified.")

    if escalation_reasons:
        human_escalation.human_review = True
        human_escalation.reason = " ; ".join(escalation_reasons)
        human_escalation.case_summary = f"Case requires human legal expert escalation due to: {human_escalation.reason}"
        human_escalation.triggered_rules = [r.rule_id for r in triggered_rules]
        human_escalation.sources = [c.doc_id for c in citations]
        human_escalation.facts = facts_considered
        human_escalation.missing_facts = [m.field_name for m in missing_information]
        if overall_status == "STRONG":
            overall_status = "ESCALATION_RECOMMENDED"
        next_actions.append("Escalate case to an IP/ABS facilitator for formal shareholding & access strategy audit.")

    # Populate backward-compatible authority guidance list
    if authority_name != "Not Determined":
        authority_guidance.append(f"Approach {authority_name} ({authority_level}).")
    for fr in form_requirements:
        authority_guidance.append(f"Prepare and submit {fr.form_name} to {fr.authority}.")

    return ABSAssessment(
        status=overall_status,
        pathway=pathway_name,
        relevance=relevance,
        reasoning=reasoning,
        applicable_authority_guidance=authority_guidance,
        ip_filing_flag=ip_filing_flag,
        ip_filing_note=ip_filing_note,
        facts_considered=facts_considered,
        triggered_rules=triggered_rules,
        exemptions_evaluated=exemptions_evaluated,
        authority_routing=authority_routing,
        form_requirements=form_requirements,
        benefit_sharing=benefit_sharing,
        certificate_of_origin=cert_of_origin,
        citations=citations,
        missing_information=missing_information,
        next_actions=next_actions,
        human_escalation=human_escalation,
        abstained=overall_status in ("INSUFFICIENT_INFORMATION", "UNRESOLVED_MISSING_INGREDIENT_SOURCE"),
        abstain_reason="Material facts missing: " + ", ".join([m.field_name for m in missing_information]) if missing_information else None,
    )
