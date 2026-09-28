"""
Tests for VEC-01. Run with: pytest -v tests/test_vector_store.py

Split into three groups:
  - where-clause tests: pure logic, no Chroma needed, fast.
  - dummy Chroma round-trip tests: prove local vector-store mechanics.
  - authoritative-corpus tests: prove ROUTE-01 -> Chroma -> real legal
    chunk -> preserved source metadata works against the actual legal corpus.
"""

from pathlib import Path

from backend.logic.routing import RoutingResult, RegimeFilter, route
from backend.services.vector_store import (
    build_where_clause,
    get_client,
    get_or_create_collection,
    add_chunks,
    query,
)
from backend.rag.chunking import Chunk, load_chunks_from_directory


# --- build_where_clause: pure logic ---

def test_where_clause_single_unrestricted_regime():
    routing = RoutingResult(
        jurisdiction="india",
        regime_filters=[RegimeFilter(legal_regime="patent_law", document_types=None)],
        legal_regimes=["patent_law"],
        matched_rows=["test"],
    )
    where = build_where_clause(routing)
    assert where == {"$and": [{"jurisdiction": "india"}, {"legal_regime": "patent_law"}]}


def test_where_clause_restricted_regime_adds_document_type_and():
    routing = RoutingResult(
        jurisdiction="india",
        regime_filters=[
            RegimeFilter(
                legal_regime="patent_law",
                document_types=["act"],
            )
        ],
        legal_regimes=["patent_law"],
        matched_rows=["test"],
    )

    where = build_where_clause(routing)

    assert where == {
        "$and": [
            {"jurisdiction": "india"},
            {
                "$and": [
                    {"legal_regime": "patent_law"},
                    {"document_type": {"$in": ["act"]}},
                ]
            },
        ]
    }


def test_where_clause_multiple_regimes_becomes_or():
    routing = RoutingResult(
        jurisdiction="india",
        regime_filters=[
            RegimeFilter(legal_regime="patent_law", document_types=None),
            RegimeFilter(legal_regime="biodiversity_abs", document_types=None),
        ],
        legal_regimes=["patent_law", "biodiversity_abs"],
        matched_rows=["test"],
    )
    where = build_where_clause(routing)
    assert where["$and"][1] == {
        "$or": [
            {"legal_regime": "patent_law"},
            {"legal_regime": "biodiversity_abs"},
        ]
    }


def test_where_clause_no_regime_filters_falls_back_to_jurisdiction_only():
    routing = RoutingResult(
        jurisdiction="india",
        regime_filters=[],
        legal_regimes=[],
        matched_rows=[],
    )
    where = build_where_clause(routing)
    assert where == {"jurisdiction": "india"}


def test_where_clause_directly_from_real_route_output():
    """End-to-end proof that ROUTE-01's actual output plugs straight in."""
    routing = route("india", "classical_generic", ["patentability"])
    where = build_where_clause(routing)

    # classical_generic must restrict patent_law to ["act"] per the v2 fix
    patent_clause = next(
        c
        for c in where["$and"][1]["$or"]
        if c.get("$and", [{}])[0].get("legal_regime") == "patent_law"
    )

    assert patent_clause == {
        "$and": [
            {"legal_regime": "patent_law"},
            {"document_type": {"$in": ["act"]}},
        ]
    }


# --- Real Chroma round-trip ---

def test_insert_and_query_dummy_vector_locally(tmp_path):
    client = get_client(persist_directory=str(tmp_path / "chroma_data"))
    collection = get_or_create_collection(client, name="test_collection")

    chunks = [
        Chunk(
            chunk_id="TEST-1:1",
            doc_id="TEST-1",
            jurisdiction="india",
            legal_regime="patent_law",
            document_type="act",
            section_or_article="1",
            text="Ashwagandha is a classical Ayurvedic herb used for centuries.",
            source_file="fake.md",
            metadata_source="frontmatter",
            approx_token_count=10,
        ),
        Chunk(
            chunk_id="TEST-1:2",
            doc_id="TEST-1",
            jurisdiction="india",
            legal_regime="patent_law",
            document_type="rule",
            section_or_article="2",
            text="Form 1 requires disclosure of biological material source.",
            source_file="fake.md",
            metadata_source="frontmatter",
            approx_token_count=10,
        ),
    ]

    inserted = add_chunks(collection, chunks)
    assert inserted == 2

    results = query(collection, "Ashwagandha herb", top_k=1)

    assert len(results["ids"][0]) == 1
    assert results["ids"][0][0] == "TEST-1:1"


def test_where_filter_actually_excludes_rules_in_real_query(tmp_path):
    """Proves the classical_generic 'act only' restriction actually holds back
    a Rules chunk during a real Chroma query, not just in the where-dict shape."""
    client = get_client(persist_directory=str(tmp_path / "chroma_data"))
    collection = get_or_create_collection(client, name="test_collection_2")

    chunks = [
        Chunk(
            chunk_id="TEST-1:act",
            doc_id="TEST-1",
            jurisdiction="india",
            legal_regime="patent_law",
            document_type="act",
            section_or_article="1",
            text="Traditional knowledge cannot be patented under this Act.",
            source_file="fake.md",
            metadata_source="frontmatter",
            approx_token_count=10,
        ),
        Chunk(
            chunk_id="TEST-1:rule",
            doc_id="TEST-1",
            jurisdiction="india",
            legal_regime="patent_law",
            document_type="rule",
            section_or_article="2",
            text="Traditional knowledge disclosure form must be filed.",
            source_file="fake.md",
            metadata_source="frontmatter",
            approx_token_count=10,
        ),
    ]

    add_chunks(collection, chunks)

    routing = route("india", "classical_generic", ["patentability"])
    where = build_where_clause(routing)

    results = collection.query(
        query_texts=["traditional knowledge"],
        n_results=5,
        where=where,
    )

    returned_ids = results["ids"][0]

    assert "TEST-1:act" in returned_ids
    assert "TEST-1:rule" not in returned_ids


# --- Phase 6: authoritative legal-corpus retrieval ---

def _authoritative_corpus_root() -> Path:
    """Resolve the repository's real legal corpus from this test file."""
    return Path(__file__).resolve().parents[1] / "legal-corpus"


def test_authoritative_corpus_contains_real_legal_chunk_with_source_metadata():
    """
    Phase 6 acceptance check:

    The actual legal corpus must contain a real legal chunk with the
    structured metadata needed downstream for citation/evidence work.
    """
    corpus_root = _authoritative_corpus_root()
    chunks = load_chunks_from_directory(corpus_root)

    target = next(
        (
            chunk
            for chunk in chunks
            if chunk.doc_id == "IN-1"
            and chunk.section_or_article == "3(p)"
        ),
        None,
    )

    assert target is not None
    assert target.text
    assert "traditional knowledge" in target.text.lower()

    assert target.jurisdiction == "india"
    assert target.legal_regime == "patent_law"
    assert target.document_type == "act"
    assert target.document_name == "Patents Act 1970"
    assert target.source_url
    assert target.metadata_source in {"frontmatter", "meta_json"}


def test_route_to_authoritative_corpus_returns_actual_legal_chunk_and_metadata(tmp_path):
    """
    Phase 6 integration:

        routing rule
            -> Chroma where clause
            -> actual legal-corpus chunk
            -> actual source metadata

    This is deliberately not a dummy document. The inserted chunk is loaded
    directly from legal-corpus/.
    """
    corpus_root = _authoritative_corpus_root()
    chunks = load_chunks_from_directory(corpus_root)

    target = next(
        (
            chunk
            for chunk in chunks
            if chunk.doc_id == "IN-1"
            and chunk.section_or_article == "3(p)"
        ),
        None,
    )

    assert target is not None

    client = get_client(persist_directory=str(tmp_path / "chroma_data"))
    collection = get_or_create_collection(
        client,
        name="authoritative_phase6_collection",
    )

    inserted = add_chunks(collection, [target])
    assert inserted == 1

    routing = route(
        "india",
        "classical_generic",
        ["patentability"],
    )
    where = build_where_clause(routing)

    results = query(
        collection,
        "traditional knowledge known properties patentability",
        where=where,
        top_k=5,
    )

    assert results["ids"][0]
    assert target.chunk_id in results["ids"][0]

    returned_index = results["ids"][0].index(target.chunk_id)
    returned_text = results["documents"][0][returned_index]
    returned_metadata = results["metadatas"][0][returned_index]

    assert "traditional knowledge" in returned_text.lower()
    assert returned_metadata["doc_id"] == "IN-1"
    assert returned_metadata["document_name"] == "Patents Act 1970"
    assert returned_metadata["section_or_article"] == "3(p)"
    assert returned_metadata["legal_regime"] == "patent_law"
    assert returned_metadata["document_type"] == "act"
    assert returned_metadata["source_url"]


def test_same_rag_retrieval_can_return_multiple_authoritative_legal_regimes(tmp_path):
    """
    Phase 6 'Unified RAG' check:

    The same routed retrieval path must be able to return actual source
    material from more than one relevant legal regime. This prevents the
    implementation from becoming an ABS-only or patent-only RAG path.
    """
    corpus_root = _authoritative_corpus_root()
    chunks = load_chunks_from_directory(corpus_root)

    targets = [
        chunk
        for chunk in chunks
        if (
            (chunk.doc_id == "IN-1" and chunk.section_or_article == "3(p)")
            or (
                chunk.doc_id == "IN-3"
                and chunk.section_or_article == "3-7 (Access and ABS obligations)"
            )
        )
    ]

    assert len(targets) == 2

    by_id = {chunk.doc_id: chunk for chunk in targets}
    assert "IN-1" in by_id
    assert "IN-3" in by_id

    client = get_client(persist_directory=str(tmp_path / "chroma_data"))
    collection = get_or_create_collection(
        client,
        name="unified_phase6_collection",
    )

    inserted = add_chunks(collection, targets)
    assert inserted == 2

    routing = route(
        "india",
        "classical_generic",
        ["patentability"],
    )
    where = build_where_clause(routing)

    results = query(
        collection,
        "traditional knowledge biological resources India",
        where=where,
        top_k=5,
    )

    returned_ids = set(results["ids"][0])
    returned_metadata = results["metadatas"][0]

    assert "IN-1:3(p)" in returned_ids
    assert "IN-3:3-7 (Access and ABS obligations)" in returned_ids

    returned_regimes = {
        metadata["legal_regime"]
        for metadata in returned_metadata
    }

    assert "patent_law" in returned_regimes
    assert "biodiversity_abs" in returned_regimes

    for metadata in returned_metadata:
        assert metadata["doc_id"]
        assert metadata["document_name"]
        assert metadata["section_or_article"]
        assert metadata["legal_regime"]
        assert metadata["source_url"]