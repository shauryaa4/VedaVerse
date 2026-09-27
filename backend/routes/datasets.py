"""Read-only search endpoints for the repository's curated information sources."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query

from backend.data.tkdl_real_records import TKDL_REAL_RECORDS

router = APIRouter(prefix="/datasets", tags=["Datasets"])
_CORPUS_ROOT = Path(__file__).resolve().parents[2] / "legal-corpus"
_MANIFEST = _CORPUS_ROOT / "manifest.json"


def _legal_entries():
    if not _MANIFEST.exists():
        return []
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    entries = []
    for item in manifest.get("documents", []):
        relative_path = item.get("corpus_path")
        if not relative_path:
            continue
        path = (_CORPUS_ROOT / relative_path).resolve()
        if _CORPUS_ROOT.resolve() not in path.parents or not path.is_file():
            continue
        entry = {**item, "text": path.read_text(encoding="utf-8")}
        entries.append(entry)
    return entries


def _page(items: list[dict], limit: int, offset: int, description: str):
    return {
        "items": items[offset:offset + limit],
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "description": description,
    }


def _filter_text(items: list[dict], query: str, fields: tuple[str, ...]):
    terms = [term.casefold() for term in query.split() if term]
    if not terms:
        return items
    return [item for item in items if all(
        term in " ".join(str(item.get(field, "")) for field in fields).casefold()
        for term in terms
    )]


@router.get("/legal")
def search_legal_corpus(
    q: str = Query(default="", max_length=200),
    jurisdiction: str | None = Query(default=None, pattern="^(india|international)$"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    entries = _legal_entries()
    if jurisdiction:
        entries = [item for item in entries if item.get("jurisdiction") == jurisdiction]
    entries = _filter_text(entries, q, ("document_name", "legal_regime", "section_or_article", "corpus_path", "text"))
    entries.sort(key=lambda item: (item.get("jurisdiction", ""), item.get("document_name", ""), item.get("section_or_article", "")))
    return _page(entries, limit, offset, "Curated source text and metadata from this project's legal corpus.")


@router.get("/nba")
def search_nba_abs_sources(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    entries = [item for item in _legal_entries() if item.get("jurisdiction") == "india" and item.get("legal_regime") == "biodiversity_abs"]
    entries = _filter_text(entries, q, ("document_name", "section_or_article", "text"))
    entries.sort(key=lambda item: (item.get("document_name", ""), item.get("section_or_article", "")))
    return _page(entries, limit, offset, "Indian biodiversity and ABS legal sources relevant to the NBA/SBB framework. This is not a live NBA registry, application tracker, or approval database.")


@router.get("/tkdl")
def search_tkdl_archive(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    items = [record.model_dump(mode="json") for record in TKDL_REAL_RECORDS]
    items = _filter_text(items, q, ("record_id", "formulation_name", "source_text", "formulation_type", "therapeutic_use", "ingredients"))
    items.sort(key=lambda item: (item.get("formulation_name", "").casefold(), item.get("record_id", "")))
    return _page(items, limit, offset, "Offline source-derived formulation archive. It is not a live connection to the Traditional Knowledge Digital Library.")
