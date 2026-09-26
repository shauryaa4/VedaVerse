"""Validate the authoritative TKDL records, provenance, and runtime index."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.data.tkdl_possible_duplicates import POSSIBLE_DUPLICATES
from backend.data.tkdl_real_records import TKDL_REAL_RECORDS
from backend.logic import tkdl_search
from backend.models.tkdl import TKDLIngredient, TKDLRecord
from backend.models.tkdl import PriorArtAssessment
from scripts.ingest_tkdl import exact_record_signature


def validate() -> dict[str, int]:
    provenance_path = PROJECT_ROOT / "backend" / "data" / "tkdl_real_record_sources.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance_records = provenance["records"]
    record_ids = [record.record_id for record in TKDL_REAL_RECORDS]
    record_id_set = set(record_ids)
    accepted_ids = {
        record_id
        for record_id, entry in provenance_records.items()
        if entry.get("status") == "accepted"
    }
    orphan_accepted = sum(
        entry.get("status") == "accepted"
        and entry.get("final_record_id") not in record_id_set
        for entry in provenance_records.values()
    )
    missing_provenance = len(record_id_set - accepted_ids)
    exact_signatures = [exact_record_signature(record.model_dump(mode="json")) for record in TKDL_REAL_RECORDS]
    exact_duplicates = len(exact_signatures) - len(set(exact_signatures))
    mock_count = sum(
        hasattr(record, "is_mock")
        or record.record_id in {
            "TKDL-BP-1025", "TKDL-AS-0007", "TKDL-TR-0014",
            "TKDL-CH-0031", "TKDL-SR-0042", "TKDL-NP-0058",
        }
        for record in TKDL_REAL_RECORDS
    )
    runtime_count = len(tkdl_search.TKDL_REAL_RECORDS)
    generated_id_errors = sum(
        entry.get("project_generated_id")
        and not record_id.startswith("SOURCE-TKDL-")
        for record_id, entry in provenance_records.items()
        if entry.get("status") == "accepted"
    )
    duplicate_review_orphans = sum(
        record_id not in record_id_set
        for group in POSSIBLE_DUPLICATES
        for record_id in group.get("records", [])
    )
    invalid_records = 0
    for record in TKDL_REAL_RECORDS:
        try:
            TKDLRecord.model_validate(record)
            invalid_records += sum(not isinstance(item, TKDLIngredient) for item in record.ingredients)
        except Exception:
            invalid_records += 1
    source_page_gaps = sum(
        entry.get("status") == "accepted"
        and entry.get("record_origin") == "saved source page"
        and not entry.get("source_pages")
        for entry in provenance_records.values()
    )
    legacy_entries = [
        entry for entry in provenance_records.values()
        if entry.get("record_origin") == "preserved existing real-record dataset"
    ]
    source_root = Path(provenance.get("extraction_root") or "")
    source_page_hash_errors = 0
    verified_source_pages = 0
    if source_root.exists():
        page_rows = []
        for entry in provenance_records.values():
            page_rows.extend(entry.get("source_pages", []))
            page_rows.extend(entry.get("related_source_pages", []))
        for entry in provenance.get("excluded_sources", []):
            page_rows.extend(entry.get("source_pages", []))
            if entry.get("source_path"):
                page_rows.append({"path": entry["source_path"], "sha256": entry.get("sha256")})
        for page in page_rows:
            page_path = source_root / str(page.get("path") or "")
            if not page_path.is_file() or hashlib.sha256(page_path.read_bytes()).hexdigest() != page.get("sha256"):
                source_page_hash_errors += 1
            else:
                verified_source_pages += 1

    report = {
        "final_real_formulations": len(TKDL_REAL_RECORDS),
        "accepted_provenance_entries": len(accepted_ids),
        "total_provenance_entries_including_exclusions": len(provenance_records) + len(provenance.get("excluded_sources", [])),
        "runtime_tkdl_count": runtime_count,
        "unique_record_ids": len(record_id_set),
        "duplicate_ids": len(record_ids) - len(record_id_set),
        "exact_duplicate_formulations": exact_duplicates,
        "exact_duplicate_source_exclusions": sum(item.get("status") == "duplicate_excluded" for item in provenance.get("excluded_sources", [])),
        "possible_duplicate_review_groups": len(POSSIBLE_DUPLICATES),
        "project_generated_record_ids": sum(bool(entry.get("project_generated_id")) for entry in provenance_records.values()),
        "source_derived_records_without_page_provenance": source_page_gaps,
        "legacy_records_with_related_source_pages": sum(bool(entry.get("related_source_pages")) for entry in legacy_entries),
        "legacy_records_without_related_source_pages": sum(not entry.get("related_source_pages") for entry in legacy_entries),
        "source_pages_with_captured_url": sum(
            bool(page.get("source_urls"))
            for entry in provenance_records.values()
            for page in entry.get("source_pages", []) + entry.get("related_source_pages", [])
        ),
        "verified_source_page_hashes": verified_source_pages,
        "source_page_hash_errors": source_page_hash_errors,
        "orphan_accepted_provenance_entries": orphan_accepted,
        "real_records_without_provenance": missing_provenance,
        "mock_records": mock_count,
        "generated_id_errors": generated_id_errors,
        "duplicate_review_orphans": duplicate_review_orphans,
        "invalid_records_or_ingredients": invalid_records,
        "assessment_mock_fields": int("mock" in PriorArtAssessment.model_fields),
        "api_response_mock_fields": int(
            "mock: bool" in (PROJECT_ROOT / "backend" / "routes" / "tkdl_routes.py").read_text(encoding="utf-8")
        ),
    }
    errors = [key for key in (
        "duplicate_ids", "exact_duplicate_formulations", "orphan_accepted_provenance_entries",
        "real_records_without_provenance", "mock_records", "generated_id_errors",
        "duplicate_review_orphans", "invalid_records_or_ingredients", "source_derived_records_without_page_provenance",
        "source_page_hash_errors",
        "assessment_mock_fields", "api_response_mock_fields",
    ) if report[key]]
    if runtime_count != len(TKDL_REAL_RECORDS) or accepted_ids != record_id_set:
        errors.append("dataset_runtime_provenance_count_mismatch")
    if errors:
        raise AssertionError(f"TKDL validation failed: {errors}; report={report}")
    return report


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2))
