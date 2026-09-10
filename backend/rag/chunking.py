"""
VEC-02 — Chunking pipeline.

Walks a corpus directory tree (matching Shau's actual layout:
legal-corpus/<jurisdiction>/<act-folder>/<section>.md) and produces one Chunk
per file. Each .md file is already split at section boundaries by convention
(Shau's own file-per-section pattern), so this does NOT further split within
a file — it trusts the existing boundaries. It DOES flag (not split) any
chunk whose word count suggests it's too big for good retrieval, per build
spec section 7's ~150-400 token guidance, so the corpus-quality issue is
visible without silently rewriting someone else's content.

HANDLES BOTH REAL METADATA CONVENTIONS FOUND IN THE ACTUAL CORPUS:
1. Inline YAML frontmatter at the top of the .md file (Patents Act style).
2. A per-folder meta.json array with a "file" key pointing at each .md
   (Patents Rules style) — this pattern emerged after CLS-01/ROUTE-01 were
   already built, so this chunker was written to match it, not the other
   way around.
3. Neither present (found in 2 of the Biological Diversity Act files as of
   this writing) — DEGRADES GRACEFULLY: still produces a chunk (never drops
   content silently), tags it metadata_source="missing", and best-effort
   infers jurisdiction from the folder path so it's at least findable by a
   jurisdiction-only fallback retrieval per build spec section 5/9.
"""

import json
import re
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)

# Files that live alongside real corpus docs but are never corpus content themselves.
_SKIP_FILENAMES = {"readme.md", "_template.meta.json", "meta.json", "manifest.json", "corpus_validation.csv"}

# Rough token estimate: ~0.75 words per token is the usual rule of thumb, i.e.
# tokens ≈ words / 0.75. We only need this to flag oversized chunks, not for
# precision, so a simple word count multiplier is fine.
_TOKEN_ESTIMATE_FACTOR = 1.3
_CHUNK_TOKEN_WARNING_THRESHOLD = 450  # spec's ~150-400 guidance, +some slack before flagging


class Chunk(BaseModel):
    chunk_id: str
    doc_id: Optional[str] = None
    jurisdiction: Optional[str] = None
    legal_regime: Optional[str] = None
    document_name: Optional[str] = None
    document_type: Optional[str] = None
    section_or_article: Optional[str] = None
    product_class_tags: list[str] = []
    date_enacted: Optional[str] = None
    last_verified_date: Optional[str] = None
    source_url: Optional[str] = None
    status_note: Optional[str] = None

    text: str
    source_file: str
    metadata_source: str  # "frontmatter" | "meta_json" | "missing"
    approx_token_count: int
    oversized: bool = False


def _estimate_tokens(text: str) -> int:
    return int(len(text.split()) * _TOKEN_ESTIMATE_FACTOR)


def _parse_frontmatter(raw: str) -> tuple[Optional[dict], str]:
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        return None, raw
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return None, raw
    return meta, match.group(2).strip()


def _infer_jurisdiction_from_path(path: Path, corpus_root: Path) -> Optional[str]:
    try:
        rel_parts = path.relative_to(corpus_root).parts
    except ValueError:
        return None
    for part in rel_parts:
        if part.lower() in ("india", "international"):
            return part.lower()
    return None


def _load_meta_json_lookup(folder: Path) -> dict[str, dict]:
    meta_path = folder / "meta.json"
    if not meta_path.exists():
        return {}
    try:
        entries = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(entries, list):
        return {}
    lookup = {}
    for entry in entries:
        if isinstance(entry, dict) and "file" in entry:
            lookup[entry["file"]] = entry
    return lookup


def _build_chunk(meta: dict, text: str, source_file: Path, metadata_source: str) -> Chunk:
    token_count = _estimate_tokens(text)
    doc_id = meta.get("doc_id")
    section = meta.get("section_or_article")
    chunk_id = f"{doc_id}:{section}" if doc_id and section else f"missing:{source_file.name}"
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        jurisdiction=meta.get("jurisdiction"),
        legal_regime=meta.get("legal_regime"),
        document_name=meta.get("document_name"),
        document_type=meta.get("document_type"),
        section_or_article=section,
        product_class_tags=meta.get("product_class_tags") or [],
        date_enacted=meta.get("date_enacted"),
        last_verified_date=meta.get("last_verified_date"),
        source_url=meta.get("source_url"),
        status_note=meta.get("status_note"),
        text=text,
        source_file=str(source_file),
        metadata_source=metadata_source,
        approx_token_count=token_count,
        oversized=token_count > _CHUNK_TOKEN_WARNING_THRESHOLD,
    )


def load_chunks_from_directory(corpus_root: Path) -> list[Chunk]:
    corpus_root = Path(corpus_root)
    chunks: list[Chunk] = []

    for md_file in sorted(corpus_root.rglob("*.md")):
        if md_file.name.lower() in _SKIP_FILENAMES:
            continue

        folder = md_file.parent
        meta_json_lookup = _load_meta_json_lookup(folder)

        raw = md_file.read_text(encoding="utf-8", errors="replace")

        if md_file.name in meta_json_lookup:
            meta = meta_json_lookup[md_file.name]
            text = raw.strip()
            chunks.append(_build_chunk(meta, text, md_file, "meta_json"))
            continue

        frontmatter, body = _parse_frontmatter(raw)
        if frontmatter is not None:
            chunks.append(_build_chunk(frontmatter, body, md_file, "frontmatter"))
            continue

        # Neither meta.json nor inline frontmatter — degrade gracefully, don't drop content.
        inferred_jurisdiction = _infer_jurisdiction_from_path(md_file, corpus_root)
        fallback_meta = {"jurisdiction": inferred_jurisdiction} if inferred_jurisdiction else {}
        chunks.append(_build_chunk(fallback_meta, raw.strip(), md_file, "missing"))

    return chunks
