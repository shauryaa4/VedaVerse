"""Convert saved TKDL HTML pages into model-validated offline records."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
import pprint
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.models.tkdl import TKDLRecord


class PageParser(HTMLParser):
    """Collect table rows and the page title without external libraries."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.title_parts: list[str] = []
        self.in_title = False
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(html.unescape(href).strip())
        if tag == "title":
            self.in_title = True
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append(clean_text(" ".join(self.cell)))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.rows.append(self.row)
            self.row = None

    def handle_data(self, data: str) -> None:
        text = clean_text(data)
        if not text:
            return
        if self.cell is not None:
            self.cell.append(text)
        if self.in_title:
            self.title_parts.append(text)


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def normalize(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def generated_id(identity: tuple[str, str, tuple[str, ...]]) -> str:
    encoded = json.dumps(identity, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return f"SOURCE-TKDL-{hashlib.sha256(encoded).hexdigest()[:16].upper()}"


_MINERALS = re.compile(
    r"\b(mercury|sulphur|sulfur|copper|iron|lead|tin|mica|cinnabar|borax|arsenic|orpiment|"
    r"realgar|gold|silver|zinc|rock salt|black salt|sodium|calx|oxide|mineral)\b", re.I
)
_ANIMALS = re.compile(r"\b(milk|honey|ghee|clarified butter|wax|urine|meat|bone|shell|pearl|animal)\b", re.I)
_BOTANICAL = re.compile(r"\b[A-Z][a-z-]+\s+[a-z][a-z-]+\b")
_FORMULA_TYPE = re.compile(r"formulated\s+as\s+(.{2,100}?)(?:\.|<|\n)", re.I)


def classify_ingredient(raw: str) -> str | None:
    if _MINERALS.search(raw):
        return "mineral"
    if _ANIMALS.search(raw):
        return "animal"
    if _BOTANICAL.search(raw):
        return "plant"
    return None


def extract_title(parser: PageParser) -> str | None:
    for index, row in enumerate(parser.rows):
        if "title of traditional knowledge resource" in " ".join(row).lower():
            for candidate in parser.rows[index + 1 : index + 4]:
                for cell in candidate:
                    if cell and not re.search(r"\d+\s*years?", cell, re.I):
                        return cell
    title = clean_text(" ".join(parser.title_parts))
    title = re.sub(r"\s*\(\d+\)\s*$", "", title)
    return title or None


def extract_ingredients(parser: PageParser) -> list[dict[str, Any]]:
    ingredients = []
    for row in parser.rows:
        if len(row) < 3 or not re.fullmatch(r"\d{1,3}", row[0]):
            continue
        raw_name = clean_text(row[1])
        if len(raw_name) <= 3 or re.search(r"^(?:page|vol\.?|ed\.?\s)\b", raw_name, re.I):
            continue
        botanical = _BOTANICAL.search(raw_name)
        ingredients.append({
            "name": raw_name,
            "scientific_name": botanical.group(0) if botanical else None,
            "traditional_name": None,
            "source_category": classify_ingredient(raw_name),
            "part_used": row[2] or None,
            "processing": None,
        })
    return ingredients


def parse_page(path: Path, root: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    raw = path.read_bytes()
    text = raw.decode("cp1252", errors="replace")
    parser = PageParser()
    parser.feed(text)
    parser.close()
    source_urls = [link for link in parser.links if link.lower().startswith(("http://", "https://")) and "highlight.asp" in link.lower()]
    title = extract_title(parser)
    ingredients = extract_ingredients(parser)
    source_match = re.search(r"\b([A-Z]{1,8}/\d{1,6})\b", text)
    source_id = source_match.group(1) if source_match else None
    year_match = re.search(r"Knowledge Known Since.{0,120}?(\d{1,4})\s+years?", text, re.I | re.S)
    type_match = _FORMULA_TYPE.search(text)
    source_ref = next(
        (" ".join(row) for row in parser.rows
         if any(re.search(r"\b(ed\.?|vol\.?|publish|chaukhamba|bhaisajya|samhita)\b", cell, re.I) for cell in row)),
        None,
    )
    relative_path = path.relative_to(root).as_posix()
    issues = []
    if not source_id:
        issues.append("source record ID absent; a project-generated ID will be used")
    if not title:
        issues.append("formulation title missing; page omitted because formulation identity cannot be established")
    elif any(char in title for char in "¢¤¦¹º¾¬�"):
        issues.append("title contains unresolved custom-font/encoding text; raw source wording retained")
    if year_match is None:
        issues.append("knowledge-known-since year absent")
    if not source_ref:
        issues.append("source citation absent")
    elif any(char in source_ref for char in "¢¤¦¹º¾¬�"):
        issues.append("source citation contains unresolved custom-font/encoding text; raw wording retained")
    if not ingredients:
        issues.append("ingredient rows absent; page omitted because composition cannot be established")
    for ingredient in ingredients:
        if ingredient["source_category"] is None:
            issues.append(f"ingredient category unavailable in source and not inferred: {ingredient['name']}")
    issues.append("therapeutic use left empty because page highlighting may be a search term")

    entry = {
        "source_path": relative_path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_urls": source_urls,
        "source_record_id": source_id,
        "formulation_name": title,
        "ingredient_names": [ingredient["name"] for ingredient in ingredients],
        "ingredient_count": len(ingredients),
        "issues": issues,
    }
    if not title or not ingredients:
        return None, entry

    record = {
        "record_id": source_id or "PENDING-GENERATED-ID",
        "formulation_name": title,
        "source_text": source_ref,
        "formulation_type": clean_text(type_match.group(1)) if type_match else None,
        "knowledge_known_since_years": int(year_match.group(1)) if year_match else None,
        "ingredients": ingredients,
        "therapeutic_use": [],
    }
    return record, entry


def exact_record_signature(record: dict[str, Any]) -> tuple[Any, ...]:
    """Normalize all formulation fields except identifiers for exact deduping."""
    compact = lambda value: re.sub(r"[^a-z0-9]", "", normalize(value))
    ingredient_rows = tuple(sorted(
        tuple(compact(ingredient.get(field)) for field in (
            "name", "scientific_name", "traditional_name", "part_used", "processing",
        ))
        for ingredient in record.get("ingredients", [])
    ))
    return (
        compact(record.get("formulation_name", "")),
        ingredient_rows,
        compact(record.get("source_text", "")),
        compact(record.get("formulation_type", "")),
        record.get("knowledge_known_since_years"),
        tuple(sorted(compact(value) for value in record.get("therapeutic_use", []))),
    )


def _legacy_raw_id(record_id: str) -> str:
    value = record_id.strip()
    if value.upper().startswith("TKDL-"):
        value = value[5:]
    return normalize(value)


def _write_authoritative_outputs(
    *,
    candidates: list[dict[str, Any]],
    candidate_provenance: dict[str, Any],
    extraction_report: list[dict[str, Any]],
    output_root: Path,
    project_root: Path,
    source_root: Path,
    source_archive: Path | None,
    deduplicated_input: Path | None,
) -> dict[str, Any]:
    """Preserve the existing 21 rows, append distinct source records, and write all TKDL outputs."""
    from backend.data.tkdl_real_records import TKDL_REAL_RECORDS as existing_records

    # The first 21 entries are the pre-expansion source-derived records. Keeping
    # them first makes repeat ingestion deterministic and preserves their IDs.
    legacy = [record.model_dump(mode="json") for record in existing_records[:21]]
    if len(legacy) != 21:
        raise ValueError("Expected the 21 existing real TKDL records at the head of TKDL_REAL_RECORDS")

    legacy_id_keys = {_legacy_raw_id(record["record_id"]) for record in legacy}
    related_pages_by_legacy_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for metadata in candidate_provenance.values():
        source_id = metadata.get("source_record_id")
        if source_id:
            related_pages_by_legacy_id[normalize(str(source_id))].extend(metadata.get("source_pages", []))
    dedup_records = json.loads(deduplicated_input.read_text(encoding="utf-8")) if deduplicated_input else []
    dedup_by_path: dict[str, list[str]] = defaultdict(list)
    for item in dedup_records:
        source_file = str(item.get("source_file") or "")
        dedup_by_path[source_file.removeprefix("tkdl/")].append(str(item.get("record_id") or ""))

    candidates_with_provenance: list[tuple[dict[str, Any], dict[str, Any], str]] = []
    used_ids = {record["record_id"] for record in legacy}
    for candidate in candidates:
        record = dict(candidate)
        original_candidate_id = str(record["record_id"])
        metadata = dict(candidate_provenance[original_candidate_id])
        source_id = metadata.get("source_record_id")
        generated = bool(metadata.get("project_generated_id"))
        if source_id and not generated and normalize(str(source_id)) in legacy_id_keys:
            ingredient_key = tuple(sorted({normalize(str(i.get("name") or "")) for i in record["ingredients"]}))
            record["record_id"] = generated_id((normalize(str(source_id)), normalize(record["formulation_name"]), ingredient_key))
            metadata["project_generated_id"] = True
            metadata.setdefault("issues", []).append(
                "source ID conflicts with a preserved legacy record; a project-generated ID is used"
            )
        while record["record_id"] in used_ids:
            ingredient_key = tuple(sorted({normalize(str(i.get("name") or "")) for i in record["ingredients"]}))
            collision_counter = 1
            while True:
                identity = (
                    normalize(str(source_id or original_candidate_id)),
                    normalize(record["formulation_name"]),
                    ingredient_key + (normalize(original_candidate_id), str(collision_counter)),
                )
                replacement_id = generated_id(identity)
                if replacement_id not in used_ids:
                    record["record_id"] = replacement_id
                    break
                collision_counter += 1
            metadata["project_generated_id"] = True
        used_ids.add(record["record_id"])
        metadata["status"] = "accepted"
        metadata["final_record_id"] = record["record_id"]
        metadata["record_id"] = record["record_id"]
        metadata["original_extraction_record_id"] = original_candidate_id
        metadata["record_origin"] = "saved source page"
        metadata["original_formulation_name"] = record.get("formulation_name")
        metadata["source_reference"] = record.get("source_text")
        metadata["source_urls"] = sorted({
            url for page in metadata.get("source_pages", []) for url in page.get("source_urls", [])
        })
        metadata["source_url"] = metadata["source_urls"][0] if len(metadata["source_urls"]) == 1 else None
        metadata["source_pages"] = [
            {**page, "filename": Path(str(page.get("path") or "")).name}
            for page in metadata.get("source_pages", [])
        ]
        metadata["supplied_deduplicated_record_ids"] = sorted({
            item_id
            for page in metadata.get("source_pages", [])
            for item_id in dedup_by_path.get(str(page.get("path") or ""), [])
        })
        if metadata.get("project_generated_id") and not str(record["record_id"]).startswith("SOURCE-TKDL-"):
            raise ValueError(f"Generated identifier lacks SOURCE-TKDL prefix: {record['record_id']}")
        candidates_with_provenance.append((record, metadata, original_candidate_id))

    # Group only records whose complete normalized formulation payload agrees.
    by_signature: dict[tuple[Any, ...], list[tuple[dict[str, Any], dict[str, Any], str]]] = defaultdict(list)
    for item in candidates_with_provenance:
        by_signature[exact_record_signature(item[0])].append(item)
    duplicate_exclusions: list[dict[str, Any]] = []
    accepted_source: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for group in by_signature.values():
        group.sort(key=lambda item: (bool(item[1].get("project_generated_id")), item[0]["record_id"]))
        keep_record, keep_metadata, _ = group[0]
        if len(group) > 1:
            by_ingredient: dict[tuple[str, ...], set[str]] = defaultdict(set)
            for duplicate_record, _, _ in group:
                for ingredient in duplicate_record.get("ingredients", []):
                    identity = tuple(normalize(str(ingredient.get(field) or "")) for field in (
                        "name", "scientific_name", "traditional_name", "part_used", "processing",
                    ))
                    if ingredient.get("source_category") is not None:
                        by_ingredient[identity].add(str(ingredient["source_category"]))
            for ingredient in keep_record.get("ingredients", []):
                identity = tuple(normalize(str(ingredient.get(field) or "")) for field in (
                    "name", "scientific_name", "traditional_name", "part_used", "processing",
                ))
                if len(by_ingredient[identity]) > 1:
                    ingredient["source_category"] = None
                    keep_metadata.setdefault("issues", []).append(
                        f"ingredient category conflicted across exact duplicate captures; left unclassified: {ingredient.get('name')}"
                    )
        accepted_source.append((keep_record, keep_metadata))
        for excluded_record, excluded_metadata, _ in group[1:]:
            excluded_urls = sorted({
                url for page in excluded_metadata.get("source_pages", []) for url in page.get("source_urls", [])
            })
            duplicate_exclusions.append({
                "status": "duplicate_excluded",
                "record_id": excluded_record["record_id"],
                "duplicate_of": keep_record["record_id"],
                "source_record_id": excluded_metadata.get("source_record_id"),
                "source_pages": [
                    {**page, "filename": Path(str(page.get("path") or "")).name}
                    for page in excluded_metadata.get("source_pages", [])
                ],
                "original_formulation_name": excluded_record.get("formulation_name"),
                "source_reference": excluded_record.get("source_text"),
                "source_urls": excluded_urls,
                "source_url": excluded_urls[0] if len(excluded_urls) == 1 else None,
                "reason": "all normalized formulation fields match the retained record; source identity differs",
            })

    final_records = legacy + [record for record, _ in accepted_source]
    final_ids = [record["record_id"] for record in final_records]
    if len(final_ids) != len(set(final_ids)):
        raise ValueError("Record ID collision remained after deterministic ID assignment")
    for record in final_records:
        TKDLRecord.model_validate(record)

    provenance_records: dict[str, dict[str, Any]] = {}
    for record in legacy:
        record_id = record["record_id"]
        raw_legacy_id = _legacy_raw_id(record_id)
        related_pages = [
            {**page, "filename": Path(str(page.get("path") or "")).name}
            for page in related_pages_by_legacy_id.get(raw_legacy_id, [])
        ]
        related_urls = sorted({url for page in related_pages for url in page.get("source_urls", [])})
        deduplicated_ids = sorted({
            item_id for page in related_pages
            for item_id in dedup_by_path.get(str(page.get("path") or ""), [])
        })
        provenance_records[record_id] = {
            "status": "accepted",
            "final_record_id": record_id,
            "record_id": record_id,
            "source_record_id": record_id[5:].replace("-", "/", 1) if related_pages and record_id.upper().startswith("TKDL-") else None,
            "legacy_record_id": record_id,
            "project_generated_id": False,
            "record_origin": "preserved existing real-record dataset",
            "identifier_origin": "legacy identifier matched to saved source pages by ID; formulation equivalence was not assumed" if related_pages else "legacy identifier preserved; official status not independently confirmed from supplied source pages",
            "original_formulation_name": record.get("formulation_name"),
            "source_text": record.get("source_text"),
            "source_reference": record.get("source_text"),
            "source_url": related_urls[0] if len(related_urls) == 1 else None,
            "source_urls": related_urls,
            "source_filename": related_pages[0]["filename"] if len(related_pages) == 1 else None,
            "source_pages": [],
            "related_source_pages": related_pages,
            "supplied_deduplicated_record_ids": deduplicated_ids,
            "issues": (
                ["Saved pages share the legacy source ID; their title/composition was not treated as an exact match."]
                if related_pages else
                ["Page-level source file was not present in the supplied archive; the legacy citation was preserved."]
            ),
        }
    for record, metadata in accepted_source:
        provenance_records[record["record_id"]] = metadata

    incomplete_sources = []
    for entry in extraction_report:
        if not entry.get("ingredient_count") or not entry.get("formulation_name"):
            incomplete_sources.append({
                "status": "rejected_incomplete_source",
                "source_path": entry.get("source_path"),
                "source_filename": Path(str(entry.get("source_path") or "")).name,
                "sha256": entry.get("sha256"),
                "source_record_id": entry.get("source_record_id"),
                "formulation_name": entry.get("formulation_name"),
                "source_urls": entry.get("source_urls", []),
                "issues": entry.get("issues", []),
            })
    excluded_sources = duplicate_exclusions + incomplete_sources

    # Review groups remain separate from the accepted data and never cause an automatic merge.
    possible: list[dict[str, Any]] = []
    by_name: dict[str, list[str]] = defaultdict(list)
    by_ingredients: dict[tuple[str, ...], list[str]] = defaultdict(list)
    by_source_id: dict[str, list[str]] = defaultdict(list)
    for record in final_records:
        record_id = record["record_id"]
        by_name[normalize(record.get("formulation_name", ""))].append(record_id)
        by_ingredients[tuple(sorted({normalize(str(i.get("name") or "")) for i in record.get("ingredients", [])}))].append(record_id)
        source_id = provenance_records[record_id].get("source_record_id")
        if source_id:
            by_source_id[normalize(str(source_id))].append(record_id)
        elif provenance_records[record_id].get("legacy_record_id"):
            legacy_key = _legacy_raw_id(record_id)
            if legacy_key:
                by_source_id[legacy_key].append(record_id)
    for name, ids in sorted(by_name.items()):
        if name and len(ids) > 1:
            possible.append({"signal": "same normalized formulation name; compare composition and references", "records": sorted(ids)})
    for ingredients, ids in sorted(by_ingredients.items(), key=lambda item: item[0]):
        if ingredients and len(ids) > 1:
            possible.append({"signal": "same normalized ingredient set; compare names and references; not merged", "records": sorted(ids), "ingredients": list(ingredients)})
    for source_id, ids in sorted(by_source_id.items()):
        if len(ids) > 1:
            possible.append({"signal": "source identifier is shared across distinct retained records; review source pages", "source_record_id": source_id, "records": sorted(ids)})

    # The provenance map is keyed by final record ID so accepted rows cannot become orphans.
    root_data = {
        "source_archive": str(source_archive) if source_archive else None,
        "extraction_root": str(source_root),
        "notes": [
            "Raw source wording and missing fields are preserved. URLs are copied from source-page links when present; none are inferred.",
            "Project-generated IDs begin SOURCE-TKDL- and keep the raw source identifier in provenance.",
            "Possible duplicates are retained and listed for review; only exact normalized payload duplicates are excluded.",
        ],
        "records": provenance_records,
        "excluded_sources": excluded_sources,
        "source_summary": {
            "source_pages": len(extraction_report),
            "source_candidate_formulations": len(candidates),
            "accepted_archive_records": len(accepted_source),
            "preserved_legacy_records": len(legacy),
            "final_real_records": len(final_records),
            "exact_duplicate_formulations_excluded": len(duplicate_exclusions),
            "rejected_incomplete_sources": len(incomplete_sources),
            "possible_duplicate_review_groups": len(possible),
            "supplemental_deduplicated_input_records": len(dedup_records),
            "pages_with_source_url": sum(bool(entry.get("source_urls")) for entry in extraction_report),
        },
    }
    data_dir = project_root / "backend" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        '"""Authoritative real, source-derived TKDL formulation dataset.\n\n'
        'Data fields are preserved from the existing real records or saved source pages.\n'
        'Page-level source traceability is maintained in tkdl_real_record_sources.json.\n'
        'This is an offline archive, not a live TKDL connection.\n'
        '"""',
        "\nfrom backend.models.tkdl import TKDLRecord\n",
        "\nTKDL_REAL_RECORDS: list[TKDLRecord] = [",
    ]
    for record in final_records:
        lines.append("    TKDLRecord.model_validate(" + pprint.pformat(record, width=100, sort_dicts=False) + "),")
    lines.append("]\n")
    (data_dir / "tkdl_real_records.py").write_text("\n".join(lines), encoding="utf-8")
    (data_dir / "tkdl_real_record_sources.json").write_text(json.dumps(root_data, ensure_ascii=False, indent=2), encoding="utf-8")
    duplicate_py = '"""Possible TKDL duplicates retained for human review."""\n\nPOSSIBLE_DUPLICATES: list[dict[str, object]] = ' + pprint.pformat(possible, width=100, sort_dicts=False) + "\n"
    (data_dir / "tkdl_possible_duplicates.py").write_text(duplicate_py, encoding="utf-8")
    return root_data["source_summary"]


def main() -> int:
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--source-root", type=Path, required=True, help="Root containing the saved TKDL HTML pages")
    argp.add_argument("--output-dir", type=Path, required=True, help="Directory for candidate records and review reports")
    argp.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="VedaVerse root for authoritative TKDL outputs")
    argp.add_argument("--source-archive", type=Path, help="Optional path to the supplied archive, recorded verbatim")
    argp.add_argument("--deduplicated-input", type=Path, help="Optional supplied deduplicated JSON used for provenance cross-reference")
    args = argp.parse_args()
    root = args.source_root.resolve()
    output = args.output_dir.resolve()
    pages = sorted(p for p in root.rglob("*.html") if not p.name.startswith("._") and "__MACOSX" not in p.parts)

    page_data = []
    for page in pages:
        record, entry = parse_page(page, root)
        page_data.append({"record": record, "entry": entry})

    # De-duplicate copies with the same official ID, title, and ingredient set.
    # Pages without an ID use title and composition. Conflicting source IDs
    # remain separate records with project IDs while the raw ID stays in provenance.
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in page_data:
        record = item["record"]
        if not record:
            continue
        ingredient_key = tuple(sorted({normalize(i["name"]) for i in record["ingredients"]}))
        id_key = normalize(item["entry"]["source_record_id"] or "")
        groups[(id_key, normalize(record["formulation_name"]), ingredient_key)].append(item)

    id_to_signatures: dict[str, set[tuple[Any, ...]]] = defaultdict(set)
    for key in groups:
        if key[0]:
            id_to_signatures[key[0]].add(key)
    id_conflicts = {key for key, signatures in id_to_signatures.items() if len(signatures) > 1}

    records = []
    provenance: dict[str, Any] = {}
    for key, copies in sorted(groups.items(), key=lambda pair: pair[0]):
        first = copies[0]
        record = dict(first["record"])
        raw_id = first["entry"]["source_record_id"]
        must_generate_id = raw_id is None or normalize(raw_id) in id_conflicts
        if must_generate_id:
            record["record_id"] = generated_id((key[0], key[1], key[2]))
        record = TKDLRecord.model_validate(record).model_dump(mode="json")
        records.append(record)
        provenance[record["record_id"]] = {
            "source_record_id": raw_id,
            "project_generated_id": must_generate_id,
            "source_pages": [
                {
                    "path": copy["entry"]["source_path"],
                    "filename": Path(copy["entry"]["source_path"]).name,
                    "sha256": copy["entry"]["sha256"],
                    "source_urls": copy["entry"].get("source_urls", []),
                }
                for copy in copies
            ],
            "issues": sorted({issue for copy in copies for issue in copy["entry"]["issues"]}),
        }

    # Flag, but do not merge, same-name and same-composition records with
    # different identities or conflicting source IDs.
    possible = []
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_ingredients: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_name[normalize(record["formulation_name"])].append(record)
        by_ingredients[tuple(sorted({normalize(i["name"]) for i in record["ingredients"]}))].append(record)
    for name, group in by_name.items():
        if len(group) > 1:
            possible.append({"signal": "same normalized formulation name; compare composition and references", "records": [r["record_id"] for r in group]})
    for ingredient_set, group in by_ingredients.items():
        if len(group) > 1:
            possible.append({"signal": "same normalized ingredient set; compare names and references; not merged", "records": [r["record_id"] for r in group], "ingredients": list(ingredient_set)})
    for source_id in sorted(id_conflicts):
        conflicting_records = [r["record_id"] for r in records if normalize(provenance[r["record_id"]]["source_record_id"] or "") == source_id]
        possible.append({"signal": "same source ID but title/composition differs; project IDs assigned and records retained", "source_record_id": source_id, "records": conflicting_records})

    output.mkdir(parents=True, exist_ok=True)
    (output / "tkdl_candidate_records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "tkdl_record_provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "tkdl_extraction_report.json").write_text(json.dumps([item["entry"] for item in page_data], ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "tkdl_duplicates.json").write_text(json.dumps(possible, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "source_pages": len(pages),
        "pages_with_formulation_and_ingredients": sum(item["record"] is not None for item in page_data),
        "unique_formulations": len(records),
        "exact_duplicate_pages_collapsed": sum(len(group) - 1 for group in groups.values()),
        "records_without_official_source_id": sum(p.get("project_generated_id", False) for p in provenance.values()),
        "possible_duplicate_review_groups": len(possible),
        "pages_missing_ingredient_rows": sum(not item["entry"]["ingredient_count"] for item in page_data),
        "records_with_missing_known_since_year": sum(r["knowledge_known_since_years"] is None for r in records),
        "records_with_missing_source_citation": sum(r["source_text"] is None for r in records),
        "records_with_unclassified_ingredients": sum(any(i["source_category"] is None for i in r["ingredients"]) for r in records),
        "records_with_unresolved_title_encoding": sum(any(char in r["formulation_name"] for char in "¢¤¦¹º¾¬�") for r in records),
        "output_directory": str(output),
        "note": "Raw source wording and missing values are preserved. Therapeutic use remains empty unless extracted with a reliable source label.",
    }
    (output / "tkdl_conversion_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    final_summary = _write_authoritative_outputs(
        candidates=records,
        candidate_provenance=provenance,
        extraction_report=[item["entry"] for item in page_data],
        output_root=output,
        project_root=args.project_root.resolve(),
        source_root=root,
        source_archive=args.source_archive.resolve() if args.source_archive else None,
        deduplicated_input=args.deduplicated_input.resolve() if args.deduplicated_input else None,
    )
    print(json.dumps({"extraction": summary, "authoritative": final_summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
