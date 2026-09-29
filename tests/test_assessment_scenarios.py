"""Real local pipeline scenarios for the unified assessment endpoint.

These exercise intake/session state, classification, routing, ABS and TKDL.
They intentionally omit a legal question so tests do not call Gemini or a
live translation service.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.abs_models import ABSFactProfile
from backend.models.pip import CompositionItem
from backend.services.pip_session_store import clear_sessions, create_session, save_session


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_assessment(monkeypatch):
    from backend.routes import abs_routes

    clear_sessions()
    monkeypatch.setattr(abs_routes, "get_default_collection", lambda: None)
    yield
    clear_sessions()


def _new_indian_plant_session():
    pip = create_session()
    pip.jurisdiction = "india"
    pip.product.ingredient_sources = ["plant"]
    pip.product.biological_origin_known = "yes"
    pip.product.biological_origin_region = "Kerala, India"
    pip.product.composition = [CompositionItem(ingredient="Tulsi", is_active=True)]
    pip.abs_facts = ABSFactProfile()
    pip.abs_facts.resource.biological_resource_involved = True
    pip.abs_facts.resource.origin_status = "india"
    pip.abs_facts.resource.status = "KNOWN"
    pip.abs_facts.applicant.entity_category = "indian_citizen"
    pip.abs_facts.applicant.status = "KNOWN"
    pip.abs_facts.activity.activities = ["commercial_utilisation"]
    save_session(pip)
    return pip


def _assess(pip, **options):
    response = client.post(
        "/assessment",
        json={"session_id": pip.session_id, **options},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_e2e_simple_indian_product_reaches_abs():
    pip = _new_indian_plant_session()
    data = _assess(pip, include_abs=True, include_tkdl=False)
    assert data["classification"]["category"]
    assert data["routing"]["jurisdiction"] == "india"
    assert data["abs_assessment"]["citations"]
    assert any(item["module"] == "abs" for item in data["evidence"])


def test_e2e_foreign_applicant_routes_to_nba():
    pip = _new_indian_plant_session()
    pip.abs_facts.applicant.entity_category = "foreign_entity_or_individual"
    pip.abs_facts.applicant.applicant_type = "individual"
    save_session(pip)
    data = _assess(pip, include_abs=True, include_tkdl=False)
    assessment = data["abs_assessment"]
    assert assessment["authority_routing"]["authority_name"].startswith("National Biodiversity Authority")


def test_e2e_unknown_origin_abstains_with_a_question():
    pip = _new_indian_plant_session()
    pip.product.biological_origin_known = "no"
    pip.product.biological_origin_region = None
    pip.abs_facts.resource.origin_status = "unknown"
    save_session(pip)
    assessment = _assess(pip, include_abs=True, include_tkdl=False)["abs_assessment"]
    assert assessment["status"] == "INSUFFICIENT_INFORMATION"
    assert assessment["abstained"] is True
    assert any(item["field_name"] == "biological_origin_region" for item in assessment["missing_information"])


def test_e2e_conflicting_origin_abstains_and_escalates():
    pip = _new_indian_plant_session()
    pip.abs_facts.resource.origin_status = "foreign"
    save_session(pip)
    data = _assess(pip, include_abs=True, include_tkdl=False)
    assessment = data["abs_assessment"]
    assert assessment["status"] == "CONFLICTING"
    assert assessment["abstained"] is True
    assert data["human_review_required"] is True
    assert assessment["human_escalation"]["conflicts"]


def test_e2e_explicit_abs_conflict_flag_abstains():
    pip = _new_indian_plant_session()
    pip.abs_facts.tk.status = "CONFLICTING"
    save_session(pip)
    assessment = _assess(pip, include_abs=True, include_tkdl=False)["abs_assessment"]
    assert assessment["status"] == "CONFLICTING"
    assert assessment["abstained"] is True
    assert assessment["human_escalation"]["conflicts"]


def test_e2e_ipr_objective_reaches_section_6_rule():
    pip = _new_indian_plant_session()
    pip.objective = ["patentability"]
    save_session(pip)
    assessment = _assess(pip, include_abs=True, include_tkdl=False)["abs_assessment"]
    assert any(rule["rule_id"] == "ABS_RULE_SEC6_IPR_APPROVAL" for rule in assessment["triggered_rules"])


def test_e2e_tkdl_objective_returns_independent_result():
    pip = _new_indian_plant_session()
    pip.objective = ["prior_art"]
    save_session(pip)
    data = _assess(pip, include_abs=False, include_tkdl=True)
    assert data["tkdl_assessment"] is not None
    assert data["abs_assessment"] is None


def test_e2e_missing_ingredient_sources_abstains():
    pip = create_session()
    pip.jurisdiction = "india"
    save_session(pip)
    assessment = _assess(pip, include_abs=True, include_tkdl=False)["abs_assessment"]
    assert assessment["status"] == "INSUFFICIENT_INFORMATION"
    assert assessment["abstained"] is True
    assert any(item["field_name"] == "ingredient_sources" for item in assessment["missing_information"])


def test_e2e_complex_foreign_control_case_requires_human_review():
    pip = _new_indian_plant_session()
    pip.abs_facts.applicant.entity_category = "indian_company_with_foreign_control"
    pip.abs_facts.applicant.foreign_participation_or_control = True
    save_session(pip)
    data = _assess(pip, include_abs=True, include_tkdl=False)
    assert data["human_review_required"] is True
    assert data["abs_assessment"]["human_escalation"]["case_summary"]
