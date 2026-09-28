"""
Tests for Phase 1 — Product Intake / /intake endpoint.

Run with:

    python -m pytest tests/test_intake.py -v
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.pip_session_store import (
    clear_sessions,
    create_session,
)


@pytest.fixture(autouse=True)
def clean_sessions():
    """
    Give every test a clean in-memory session store.
    """
    clear_sessions()
    yield
    clear_sessions()


@pytest.fixture
def client():
    return TestClient(app)


def test_valid_intake_returns_structured_pip(client):
    """
    A valid intake request should return a complete structured PIP.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "jurisdiction": "india",
            "language": "en",
            "protection_target": "formulation",
            "objective": [
                "patentability",
                "abs_relevance",
            ],
            "product_name": "Ashwagandha Herbal Formulation",
            "composition": [
                {
                    "ingredient": "Ashwagandha extract",
                    "quantity": "500",
                    "unit": "mg",
                    "is_active": True,
                }
            ],
            "intended_use": "therapeutic",
            "classical_basis": "partial",
            "classical_reference": "Ashwagandha Churna",
            "novelty": "modified",
            "ingredient_sources": ["plant"],
            "biological_origin_known": "yes",
            "biological_origin_region": "Rajasthan, India",
            "development_status": "prototype",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == pip.session_id

    assert data["jurisdiction"] == "india"
    assert data["language"] == "en"
    assert data["protection_target"] == "formulation"

    assert data["objective"] == [
        "patentability",
        "abs_relevance",
    ]

    assert data["product"]["name"] == "Ashwagandha Herbal Formulation"

    assert len(data["product"]["composition"]) == 1

    assert (
        data["product"]["composition"][0]["ingredient"]
        == "Ashwagandha extract"
    )

    assert (
        data["product"]["composition"][0]["quantity"]
        == "500"
    )

    assert (
        data["product"]["composition"][0]["unit"]
        == "mg"
    )

    assert (
        data["product"]["composition"][0]["is_active"]
        is True
    )

    assert data["product"]["intended_use"] == "therapeutic"
    assert data["product"]["classical_basis"] == "partial"
    assert data["product"]["classical_reference"] == "Ashwagandha Churna"
    assert data["product"]["novelty"] == "modified"
    assert data["product"]["ingredient_sources"] == ["plant"]
    assert data["product"]["biological_origin_known"] == "yes"
    assert (
        data["product"]["biological_origin_region"]
        == "Rajasthan, India"
    )
    assert data["product"]["development_status"] == "prototype"


def test_partial_intake_preserves_missing_information(client):
    """
    Missing questionnaire answers must remain missing.

    The intake layer must not invent defaults for fields that the user
    did not provide.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "jurisdiction": "india",
            "product_name": "Test Product",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["jurisdiction"] == "india"
    assert data["product"]["name"] == "Test Product"

    # Information not supplied by the user remains unknown.
    assert data["protection_target"] is None
    assert data["objective"] == []

    assert data["product"]["composition"] == []
    assert data["product"]["intended_use"] is None
    assert data["product"]["classical_basis"] is None
    assert data["product"]["classical_reference"] is None
    assert data["product"]["novelty"] is None
    assert data["product"]["ingredient_sources"] == []
    assert data["product"]["biological_origin_known"] is None
    assert data["product"]["biological_origin_region"] is None
    assert data["product"]["development_status"] is None

    # Existing PIP default remains unchanged.
    assert data["language"] == "en"


def test_second_intake_does_not_overwrite_omitted_fields(client):
    """
    A later partial intake request should only modify fields that were
    explicitly supplied.

    This verifies the model_fields_set merge behavior.
    """

    pip = create_session()

    first_response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "jurisdiction": "india",
            "product_name": "Original Product",
            "intended_use": "therapeutic",
            "objective": ["patentability"],
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "product_name": "Updated Product",
        },
    )

    assert second_response.status_code == 200

    data = second_response.json()

    # Explicitly changed field.
    assert data["product"]["name"] == "Updated Product"

    # Previously supplied fields remain unchanged because they were
    # omitted from the second request.
    assert data["jurisdiction"] == "india"
    assert data["product"]["intended_use"] == "therapeutic"
    assert data["objective"] == ["patentability"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("jurisdiction", "mars"),
        ("language", "fr"),
        ("intended_use", "unknown_use"),
        ("classical_basis", "maybe"),
        ("novelty", "probably_new"),
        ("biological_origin_known", "maybe"),
        ("development_status", "finished"),
    ],
)
def test_invalid_enum_values_are_rejected(
    client,
    field,
    value,
):
    """
    Invalid enum-like intake values must be rejected with HTTP 422.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            field: value,
        },
    )

    assert response.status_code == 422


def test_invalid_ingredient_source_is_rejected(client):
    """
    Ingredient sources use the existing IngredientSource model constraint.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "ingredient_sources": ["imaginary_source"],
        },
    )

    assert response.status_code == 422


def test_invalid_objective_is_rejected(client):
    """
    Objective values are validated using the existing Objective type.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "objective": ["make_it_go_viral"],
        },
    )

    assert response.status_code == 422


def test_invalid_protection_target_is_rejected(client):
    """
    Protection target is validated using the existing ProtectionTarget type.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "protection_target": "magic_protection",
        },
    )

    assert response.status_code == 422


def test_unknown_session_returns_404(client):
    """
    /intake must reject a session_id that does not exist.
    """

    response = client.post(
        "/intake",
        json={
            "session_id": "this-session-does-not-exist",
            "jurisdiction": "india",
        },
    )

    assert response.status_code == 404


def test_empty_intake_returns_existing_pip_unchanged(client):
    """
    An intake request containing only session_id should be valid.

    This is important because the user may not yet know any product facts.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == pip.session_id

    assert data["jurisdiction"] is None
    assert data["protection_target"] is None
    assert data["objective"] == []

    assert data["product"]["name"] is None
    assert data["product"]["composition"] == []
    assert data["product"]["intended_use"] is None
    assert data["product"]["classical_basis"] is None
    assert data["product"]["novelty"] is None


def test_intake_output_can_be_consumed_by_classification(client):
    """
    The PIP returned by intake should contain the information required
    by the existing PIP -> Classification adapter.
    """

    pip = create_session()

    response = client.post(
        "/intake",
        json={
            "session_id": pip.session_id,
            "jurisdiction": "india",
            "objective": ["patentability"],
            "product_name": "Ashwagandha Formulation",
            "composition": [
                {
                    "ingredient": "Ashwagandha extract",
                    "quantity": "500",
                    "unit": "mg",
                    "is_active": True,
                }
            ],
            "intended_use": "therapeutic",
            "classical_basis": "partial",
            "novelty": "modified",
            "development_status": "prototype",
        },
    )

    assert response.status_code == 200

    data = response.json()

    # These are the exact PIP fields consumed by the existing
    # extract_classification_input() adapter.
    assert data["product"]["composition"][0]["ingredient"] == (
        "Ashwagandha extract"
    )

    assert data["product"]["intended_use"] == "therapeutic"
    assert data["product"]["classical_basis"] == "partial"
    assert data["product"]["novelty"] == "modified"
    assert data["product"]["development_status"] == "prototype"

    assert data["objective"] == ["patentability"]