"""
scripts/ingest_corpus.py — run the real chunking -> embedding -> retrieval
pipeline against the actual legal-corpus/ folder, not test fixtures.

Usage (from repo root):
    python scripts/ingest_corpus.py

What it does, in order:
  1. Walks legal-corpus/ and chunks every real .md file.
  2. Prints a summary: how many chunks, broken down by metadata source and by
     legal_regime — this is where corpus gaps (like BDA's missing frontmatter)
     become visible as numbers instead of something you have to remember.
  3. Embeds and loads everything into a local Chroma collection.
  4. Runs two sample queries through the FULL chain (classify -> route ->
     build_where_clause -> Chroma query) to prove it actually works end to
     end against real content, not just unit test fixtures.
"""

import sys
from pathlib import Path
from collections import Counter

# Allow running as `python scripts/ingest_corpus.py` from repo root.
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.chunking import load_chunks_from_directory
from backend.services.vector_store import (
    get_client, get_or_create_collection, add_chunks, build_where_clause, query,
)
from backend.logic.classification import classify
from backend.logic.routing import route
from backend.models.pip import ProductIntelligenceProfile, extract_classification_input

CORPUS_ROOT = Path(__file__).parent.parent / "legal-corpus"
PERSIST_DIR = str(Path(__file__).parent.parent / "chroma_data")


def print_summary(chunks):
    print(f"\n{'='*60}\nCHUNKING SUMMARY\n{'='*60}")
    print(f"Total chunks found: {len(chunks)}")

    by_source = Counter(c.metadata_source for c in chunks)
    print(f"\nBy metadata source:")
    for source, count in by_source.items():
        print(f"  {source:12s}: {count}")

    by_regime = Counter(c.legal_regime or "(none)" for c in chunks)
    print(f"\nBy legal_regime:")
    for regime, count in by_regime.items():
        print(f"  {regime:20s}: {count}")

    missing = [c for c in chunks if c.metadata_source == "missing"]
    if missing:
        print(f"\n⚠️  {len(missing)} chunk(s) with NO metadata — won't be found by any")
        print(f"   regime-filtered route, only by jurisdiction-only fallback:")
        for c in missing:
            print(f"   - {c.source_file}")

    oversized = [c for c in chunks if c.oversized]
    if oversized:
        print(f"\n⚠️  {len(oversized)} chunk(s) flagged oversized (~>450 est. tokens):")
        for c in oversized:
            print(f"   - {c.source_file} (~{c.approx_token_count} tokens)")

    empty = [c for c in chunks if not c.text.strip()]
    if empty:
        print(f"\n⚠️  {len(empty)} chunk(s) are EMPTY (0 bytes) — skipped during embedding:")
        for c in empty:
            print(f"   - {c.source_file}")


def run_sample_query(collection, label, jurisdiction, category, objectives, query_text):
    print(f"\n{'-'*60}\nSAMPLE QUERY: {label}\n{'-'*60}")
    routing = route(jurisdiction, category, objectives)
    print(f"Routing matched: {routing.matched_rows}")
    if routing.status_notes:
        print(f"Status notes: {routing.status_notes}")

    where = build_where_clause(routing)
    print(f"Chroma where-clause: {where}")

    results = query(collection, query_text, where=where, top_k=3)
    ids = results["ids"][0]
    if not ids:
        print("→ NO RESULTS — retriever should fall back to jurisdiction-only or abstain.")
    else:
        print(f"→ Retrieved {len(ids)} chunk(s): {ids}")
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            preview = doc[:80].replace("\n", " ")
            print(f"   [{meta['doc_id']}:{meta['section_or_article']}] {preview}...")


def main():
    if not CORPUS_ROOT.exists():
        print(f"ERROR: {CORPUS_ROOT} does not exist. Run this from the repo root.")
        sys.exit(1)

    chunks = load_chunks_from_directory(CORPUS_ROOT)
    print_summary(chunks)

    client = get_client(PERSIST_DIR)
    collection = get_or_create_collection(client)
    inserted = add_chunks(collection, chunks)
    print(f"\n✅ Inserted {inserted} chunk(s) into Chroma collection at {PERSIST_DIR}")

    # Sample 1: the build spec's own demo example (§18) — Classical/Generic path.
    run_sample_query(
        collection, "Classical/Generic + patentability (should EXCLUDE Patents Rules)",
        "india", "classical_generic", ["patentability"],
        "traditional knowledge cannot be patented",
    )

    # Sample 2: Proprietary path — should INCLUDE Patents Rules this time.
    run_sample_query(
        collection, "Proprietary + patentability (should INCLUDE Patents Rules)",
        "india", "proprietary", ["patentability"],
        "biological material disclosure requirement",
    )


if __name__ == "__main__":
    main()
