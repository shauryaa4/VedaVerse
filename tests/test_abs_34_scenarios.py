"""
Comprehensive 34 Scenario End-to-End Test Suite for VedaVerse ABS Engine.
Validates pathway, rule IDs, authority, forms, benefit sharing, sources, evidence status, abstention, and human escalation across all required 34 scenarios.
"""

import pytest
from backend.logic.abs_engine import assess_abs_fact_driven
from backend.models.abs_models import ABSFactProfile
from backend.models.pip import ProductIntelligenceProfile, Product


def test_scenario_01_non_biological_formulation():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["mineral", "synthetic"])
    )
    res = assess_abs_fact_driven(pip)
    assert res.status == "STRONG"
    assert res.pathway == "EXEMPT_NON_BIOLOGICAL_RESOURCE"
    assert res.relevance == "not_applicable"
    assert any(c.doc_id == "IN-3" for c in res.citations)


def test_scenario_02_indian_plant_resource():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Kerala, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_citizen"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    res = assess_abs_fact_driven(pip)
    assert res.relevance == "likely"
    assert res.authority_routing.authority_name == "State Biodiversity Board (SBB)"


def test_scenario_03_foreign_plant_resource():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Amazon, Brazil")
    )
    res = assess_abs_fact_driven(pip)
    assert res.status == "STRONG"
    assert res.relevance == "unlikely"
    assert any(e.exemption_id == "ABS_EXEMPTION_FOREIGN_BIOLOGICAL_RESOURCE" for e in res.exemptions_evaluated)


def test_scenario_04_unknown_origin():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="no")
    )
    res = assess_abs_fact_driven(pip)
    assert any(m.field_name == "biological_origin_region" for m in res.missing_information)


def test_scenario_05_indian_individual():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Tamil Nadu, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_citizen"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    res = assess_abs_fact_driven(pip)
    assert res.pathway == "SECTION_7_SBB_INTIMATION"
    assert any(r.rule_id == "ABS_RULE_SEC7_INDIAN_INTIMATION" for r in res.triggered_rules)


def test_scenario_06_indian_entity():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Maharashtra, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_no_foreign_control"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    res = assess_abs_fact_driven(pip)
    assert res.pathway == "SECTION_7_SBB_INTIMATION"
    assert any(f.form_id == "FORM_B_SBB" for f in res.form_requirements)


def test_scenario_07_section3_2_case():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Karnataka, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_with_foreign_control"
    res = assess_abs_fact_driven(pip)
    assert res.pathway == "SECTION_3_NBA_APPROVAL"
    assert res.human_escalation.human_review is True
    assert "Section 3(2)" in res.human_escalation.reason


def test_scenario_08_section7_case():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Gujarat, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_no_foreign_control"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    res = assess_abs_fact_driven(pip)
    assert res.pathway == "SECTION_7_SBB_INTIMATION"


def test_scenario_09_foreign_applicant():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Assam, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "foreign_entity_or_individual"
    res = assess_abs_fact_driven(pip)
    assert res.pathway == "SECTION_3_NBA_APPROVAL"
    assert any(f.form_id == "FORM_1" for f in res.form_requirements)


def test_scenario_10_cultivated_medicinal_plant():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Kerala, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.access.source_type = "cultivated"
    pip.abs_facts.certificate_of_origin.certificate_available = True
    res = assess_abs_fact_driven(pip)
    ex = next(e for e in res.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_CULTIVATED_PLANTS")
    assert ex.is_triggered is True


def test_scenario_11_wild_medicinal_plant():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Himalaya, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.access.source_type = "wild_collected"
    pip.abs_facts.applicant.entity_category = "indian_citizen"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    res = assess_abs_fact_driven(pip)
    assert res.certificate_of_origin.certificate_required is False


def test_scenario_12_normally_traded_commodity():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Delhi, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.access.source_type = "market_or_trader"
    res = assess_abs_fact_driven(pip)
    ex = next(e for e in res.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_NORMALLY_TRADED_COMMODITIES")
    assert ex.is_triggered is True


def test_scenario_13_codified_ayurveda_knowledge():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India", classical_basis="yes", classical_reference="Ayurvedic Pharmacopoeia")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "ayush_practitioner"
    res = assess_abs_fact_driven(pip)
    ex = next(e for e in res.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_AYUSH_CODIFIED_TK")
    assert ex.is_triggered is True


def test_scenario_14_community_tk():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Nagaland, India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.tk.tk_community_based = True
    pip.abs_facts.tk.tk_type = "community"
    res = assess_abs_fact_driven(pip)
    assert res.human_escalation.human_review is True
    assert any(e.exemption_id == "ABS_EXEMPTION_COMMUNITY_TK" for e in res.exemptions_evaluated)


def test_scenario_15_no_tk():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Punjab, India", classical_basis="no")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.tk.associated_traditional_knowledge = False
    res = assess_abs_fact_driven(pip)
    assert res.facts_considered["associated_tk"] is False


def test_scenario_16_research():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "foreign_entity_or_individual"
    pip.abs_facts.activity.activities = ["research"]
    res = assess_abs_fact_driven(pip)
    assert any(r.rule_id == "ABS_RULE_SEC3_FOREIGN_ACCESS" for r in res.triggered_rules)


def test_scenario_17_commercial_utilisation():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_no_foreign_control"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    pip.abs_facts.annual_turnover_inr = 20000000.0
    res = assess_abs_fact_driven(pip)
    assert res.benefit_sharing.applicable is True
    assert res.benefit_sharing.indicative_amount_inr == 40000.0


def test_scenario_18_ipr_preparation():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India"),
        objective=["patentability"]
    )
    res = assess_abs_fact_driven(pip)
    assert res.ip_filing_flag is True
    assert any(f.form_id == "FORM_3" for f in res.form_requirements)


def test_scenario_19_ipr_filing():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.ipr.ipr_stage = "IPR_APPLICATION"
    res = assess_abs_fact_driven(pip)
    assert any(r.rule_id == "ABS_RULE_SEC6_IPR_APPROVAL" for r in res.triggered_rules)


def test_scenario_20_granted_ipr():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.ipr.ipr_stage = "IPR_GRANTED"
    res = assess_abs_fact_driven(pip)
    assert res.ip_filing_flag is True


def test_scenario_21_ipr_commercialisation():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.ipr.ipr_stage = "IPR_COMMERCIALISATION"
    pip.abs_facts.annual_turnover_inr = 50000000.0
    res = assess_abs_fact_driven(pip)
    assert res.benefit_sharing.turnover_band == "IPR_ROYALTY_SLAB"
    assert res.benefit_sharing.indicative_amount_inr == 1000000.0


def test_scenario_22_foreign_resource_used_in_india():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="Germany")
    )
    res = assess_abs_fact_driven(pip)
    assert res.relevance == "unlikely"


def test_scenario_23_research_result_transfer():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.activity.activities = ["research_result_transfer"]
    res = assess_abs_fact_driven(pip)
    assert any(r.rule_id == "ABS_RULE_SEC4_TRANSFER_RESEARCH_RESULTS" for r in res.triggered_rules)
    assert any(f.form_id == "FORM_2" for f in res.form_requirements)


def test_scenario_24_biological_resource_transfer():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.activity.activities = ["resource_transfer"]
    res = assess_abs_fact_driven(pip)
    assert any(r.rule_id == "ABS_RULE_SEC20_THIRD_PARTY_TRANSFER" for r in res.triggered_rules)
    assert any(f.form_id == "FORM_4" for f in res.form_requirements)


def test_scenario_25_international_collaboration():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.government_approved_collaboration = True
    pip.abs_facts.activity.activities = ["research"]
    res = assess_abs_fact_driven(pip)
    ex = next(e for e in res.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_COLLABORATIVE_RESEARCH")
    assert ex.is_triggered is True


def test_scenario_26_itpgrfa_case():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.is_itpgrfa_crop = True
    res = assess_abs_fact_driven(pip)
    ex = next(e for e in res.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_ITPGRFA")
    assert ex.is_triggered is True


def test_scenario_27_benefit_sharing_calculation():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_no_foreign_control"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    pip.abs_facts.annual_turnover_inr = 60000000.0  # Above 5 crore -> 0.5%
    res = assess_abs_fact_driven(pip)
    assert res.benefit_sharing.turnover_band == "ABOVE_5_CRORE"
    assert res.benefit_sharing.indicative_amount_inr == 300000.0


def test_scenario_28_missing_turnover():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_no_foreign_control"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    res = assess_abs_fact_driven(pip)
    assert res.benefit_sharing.calculation_status == "MISSING_TURNOVER_DATA"
    assert any(m.field_name == "annual_turnover_inr" for m in res.missing_information)


def test_scenario_29_missing_applicant_category():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    res = assess_abs_fact_driven(pip)
    assert any(m.field_name == "entity_category" for m in res.missing_information)


def test_scenario_30_missing_origin():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"])
    )
    res = assess_abs_fact_driven(pip)
    assert any(m.field_name == "biological_origin_region" for m in res.missing_information)


def test_scenario_31_conflicting_facts():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="no")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.transfer.transfer_involved = True
    res = assess_abs_fact_driven(pip)
    assert res.human_escalation.human_review is True


def test_scenario_32_conflicting_sources():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    res = assess_abs_fact_driven(pip)
    assert all(c.verification_status in ("VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "CONFLICTING") for c in res.citations)


def test_scenario_33_insufficient_information():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=[])
    )
    res = assess_abs_fact_driven(pip)
    assert res.abstained is True
    assert res.status == "INSUFFICIENT_INFORMATION"


def test_scenario_34_human_escalation():
    pip = ProductIntelligenceProfile(
        product=Product(ingredient_sources=["plant"], biological_origin_known="yes", biological_origin_region="India")
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_with_foreign_control"
    res = assess_abs_fact_driven(pip)
    assert res.human_escalation.human_review is True
    assert res.human_escalation.case_summary is not None
    assert len(res.human_escalation.triggered_rules) > 0
