"""Validation and search-compatibility tests for the real offline TKDL archive."""

import importlib
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.data.tkdl_possible_duplicates import POSSIBLE_DUPLICATES
from backend.data.tkdl_real_records import TKDL_REAL_RECORDS
from backend.logic import tkdl_search
from backend.logic.tkdl_search import assess_prior_art, search_tkdl
from backend.models.pip import CompositionItem, Product, ProductIntelligenceProfile
from backend.models.tkdl import PriorArtAssessment, TKDLIngredient, TKDLRecord
from backend.routes.tkdl_routes import router as tkdl_router
from backend.services.pip_session_store import clear_sessions, save_session
from scripts.ingest_tkdl import exact_record_signature
from scripts.validate_tkdl_data import validate


def _composition(names: list[str]) -> list[CompositionItem]:
    return [CompositionItem(ingredient=name, is_active=True) for name in names]


def _pip(names: list[str], novelty: str | None = None) -> ProductIntelligenceProfile:
    return ProductIntelligenceProfile(
        product=Product(composition=_composition(names), novelty=novelty)
    )


def test_real_dataset_import_and_models_validate():
    assert TKDL_REAL_RECORDS
    assert all(isinstance(record, TKDLRecord) for record in TKDL_REAL_RECORDS)
    for record in TKDL_REAL_RECORDS:
        TKDLRecord.model_validate(record)
        assert all(isinstance(ingredient, TKDLIngredient) for ingredient in record.ingredients)


def test_record_ids_are_unique():
    ids = [record.record_id for record in TKDL_REAL_RECORDS]
    assert len(ids) == len(set(ids))


def test_no_exact_duplicate_formulations_remain():
    signatures = [exact_record_signature(record.model_dump(mode="json")) for record in TKDL_REAL_RECORDS]
    assert len(signatures) == len(set(signatures))


def test_runtime_search_uses_only_authoritative_real_dataset():
    assert tkdl_search.TKDL_REAL_RECORDS is TKDL_REAL_RECORDS
    assert len(tkdl_search.TKDL_REAL_RECORDS) == len(TKDL_REAL_RECORDS)
    matches = search_tkdl(_composition(["Mercury", "Sulphur"]))
    assert matches
    assert all(match.record.record_id in {record.record_id for record in TKDL_REAL_RECORDS} for match in matches)


def test_tkdl_api_returns_only_real_records_without_mock_flags():
    pip = _pip(["Mercury", "Sulphur"])
    save_session(pip)
    app = FastAPI()
    app.include_router(tkdl_router)
    try:
        response = TestClient(app).post("/tkdl/search", json={"session_id": pip.session_id})
    finally:
        clear_sessions()
    assert response.status_code == 200
    payload = response.json()
    ids = {record.record_id for record in TKDL_REAL_RECORDS}
    assert "mock" not in payload
    assert "mock" not in payload["assessment"]
    assert all("is_mock" not in match["record"] for match in payload["matches"])
    assert all(match["record"]["record_id"] in ids for match in payload["matches"])


def test_mock_records_cannot_return_to_runtime_dataset():
    fabricated_demo_ids = {
        "TKDL-BP-1025", "TKDL-AS-0007", "TKDL-TR-0014",
        "TKDL-CH-0031", "TKDL-SR-0042", "TKDL-NP-0058",
    }
    assert fabricated_demo_ids.isdisjoint(record.record_id for record in TKDL_REAL_RECORDS)
    assert all(not hasattr(record, "is_mock") for record in TKDL_REAL_RECORDS)
    assert "mock" not in PriorArtAssessment.model_fields
    route_source = (Path(__file__).resolve().parents[1] / "backend/routes/tkdl_routes.py").read_text(encoding="utf-8")
    assert "mock: bool" not in route_source


def test_provenance_covers_every_accepted_record_and_no_accepted_orphans():
    provenance_path = Path(__file__).resolve().parents[1] / "backend/data/tkdl_real_record_sources.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    entries = provenance["records"]
    record_ids = {record.record_id for record in TKDL_REAL_RECORDS}
    accepted_ids = {record_id for record_id, entry in entries.items() if entry.get("status") == "accepted"}
    assert accepted_ids == record_ids
    assert all(entry.get("final_record_id") == record_id for record_id, entry in entries.items())
    assert all(entry.get("source_pages") is not None for entry in entries.values())
    assert all(
        entry.get("source_pages")
        for entry in entries.values()
        if entry.get("record_origin") == "saved source page"
    )
    assert all(
        page.get("path") and len(page.get("sha256", "")) == 64
        for entry in entries.values()
        if entry.get("record_origin") == "saved source page"
        for page in entry["source_pages"]
    )
    assert not any(entry.get("status") == "accepted" and entry.get("final_record_id") not in record_ids for entry in entries.values())


def test_project_generated_ids_are_explicit_in_provenance():
    provenance_path = Path(__file__).resolve().parents[1] / "backend/data/tkdl_real_record_sources.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    for record_id, entry in provenance["records"].items():
        if entry.get("project_generated_id"):
            assert record_id.startswith("SOURCE-TKDL-")
            assert entry.get("source_record_id") is not None or entry.get("record_origin") == "saved source page"


def test_review_groups_reference_existing_real_records():
    ids = {record.record_id for record in TKDL_REAL_RECORDS}
    assert all(set(group.get("records", [])).issubset(ids) for group in POSSIBLE_DUPLICATES)


def test_searches_for_archive_terms_are_sensible():
    ids = {record.record_id for record in TKDL_REAL_RECORDS}
    triphala = search_tkdl(_composition(["Triphala"]))
    mercury_sulphur = search_tkdl(_composition(["Mercury", "Sulphur"]))
    ashwagandha = search_tkdl(_composition(["Ashwagandha"]))

    assert triphala
    assert mercury_sulphur
    assert mercury_sulphur[0].matched_ingredient_names
    assert all(item.record.record_id in ids for item in triphala + mercury_sulphur + ashwagandha)
    # Ashwagandha is absent from this supplied source snapshot; it must not be
    # fabricated from the former demo fixture just to force a search hit.
    assert not ashwagandha


def test_ingredient_risk_and_declared_novelty_remain_separate():
    record = next(
        record for record in TKDL_REAL_RECORDS
        if len(record.ingredients) > 0 and any("mercury" in item.name.lower() for item in record.ingredients)
    )
    pip = _pip([item.name for item in record.ingredients], novelty="modified")
    matches = search_tkdl(pip.product.composition)
    assert any(match.record.record_id == record.record_id for match in matches)
    assessment = assess_prior_art(pip, matches)
    assert assessment.risk_level in {"high", "medium", "low"}
    assert any("modified" in feature for feature in assessment.potential_novel_features)


def test_import_does_not_append_or_duplicate_records():
    before_ids = [record.record_id for record in TKDL_REAL_RECORDS]
    reimported = importlib.import_module("backend.data.tkdl_real_records")
    assert reimported.TKDL_REAL_RECORDS is TKDL_REAL_RECORDS
    assert [record.record_id for record in TKDL_REAL_RECORDS] == before_ids


def test_full_tkdl_data_validator_passes():
    report = validate()
    assert report["final_real_formulations"] == report["runtime_tkdl_count"]
    assert report["mock_records"] == 0
