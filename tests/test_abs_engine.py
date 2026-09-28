"""
Comprehensive Unit & Pathway Tests for the Fact-Driven Traceable ABS Engine (backend/logic/abs_engine.py).
"""

from backend.logic.abs_engine import assess_abs_fact_driven, build_fact_profile_from_pip
from backend.models.abs_models import ABSFactProfile
from backend.models.pip import ProductIntelligenceProfile, Product


def test_cultivated_plant_exemption_with_certificate():
    pip = ProductIntelligenceProfile(
        product=Product(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Kerala, India",
        )
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.access.cultivated = True
    pip.abs_facts.access.source_type = "cultivated"
    pip.abs_facts.certificate_of_origin.certificate_available = True

    result = assess_abs_fact_driven(pip)

    assert result.relevance == "likely"
    assert result.certificate_of_origin.certificate_status == "PROVIDED"
    ex_cult = next((e for e in result.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_CULTIVATED_PLANTS"), None)
    assert ex_cult is not None
    assert ex_cult.is_triggered is True


def test_normally_traded_commodity_override_on_ipr():
    pip = ProductIntelligenceProfile(
        product=Product(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Himalayas, India",
        ),
        objective=["patentability"],
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.access.source_type = "market_or_trader"

    result = assess_abs_fact_driven(pip)

    ex_ntc = next((e for e in result.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_NORMALLY_TRADED_COMMODITIES"), None)
    assert ex_ntc is not None
    assert ex_ntc.is_triggered is False  # Overridden by IPR / patentability objective!
    assert result.ip_filing_flag is True


def test_foreign_entity_section3_pathway():
    pip = ProductIntelligenceProfile(
        product=Product(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Western Ghats, India",
        )
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "foreign_entity_or_individual"

    result = assess_abs_fact_driven(pip)

    assert result.pathway == "SECTION_3_NBA_APPROVAL"
    assert result.authority_routing.authority_name == "National Biodiversity Authority (NBA)"
    assert any(f.form_id == "FORM_1" for f in result.form_requirements)


def test_indian_entity_section7_pathway():
    pip = ProductIntelligenceProfile(
        product=Product(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Assam, India",
        )
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_no_foreign_control"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]

    result = assess_abs_fact_driven(pip)

    assert result.pathway == "SECTION_7_SBB_INTIMATION"
    assert result.authority_routing.authority_name == "State Biodiversity Board (SBB)"
    assert any(f.form_id == "FORM_B_SBB" for f in result.form_requirements)


def test_benefit_sharing_slabs_calculation():
    pip = ProductIntelligenceProfile(
        product=Product(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Madhya Pradesh, India",
        )
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_no_foreign_control"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    pip.abs_facts.annual_turnover_inr = 20000000.0  # 2 Crore INR -> 0.2%

    result = assess_abs_fact_driven(pip)

    assert result.benefit_sharing.applicable is True
    assert result.benefit_sharing.turnover_band == "1_TO_5_CRORE"
    assert result.benefit_sharing.rate_or_slab == "0.2% of turnover"
    assert result.benefit_sharing.indicative_amount_inr == 40000.0  # 20,000,000 * 0.002 = 40,000
    assert result.benefit_sharing.calculation_status == "INDICATIVE_CALCULATED"


def test_foreign_biological_resource_exemption():
    pip = ProductIntelligenceProfile(
        product=Product(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Amazon Rainforest, Brazil",
        )
    )

    result = assess_abs_fact_driven(pip)

    assert result.relevance == "unlikely"
    ex_foreign = next((e for e in result.exemptions_evaluated if e.exemption_id == "ABS_EXEMPTION_FOREIGN_BIOLOGICAL_RESOURCE"), None)
    assert ex_foreign is not None
    assert ex_foreign.is_triggered is True


def test_human_escalation_for_foreign_controlled_indian_company():
    pip = ProductIntelligenceProfile(
        product=Product(
            ingredient_sources=["plant"],
            biological_origin_known="yes",
            biological_origin_region="Karnataka, India",
        )
    )
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.applicant.entity_category = "indian_company_with_foreign_control"

    result = assess_abs_fact_driven(pip)

    assert result.human_escalation.human_review is True
    assert "Foreign participation" in result.human_escalation.case_summary
