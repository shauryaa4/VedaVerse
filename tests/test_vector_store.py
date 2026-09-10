"""
Tests for VEC-01. Run with: pytest -v tests/test_vector_store.py

Split into two groups:
  - where-clause tests: pure logic, no Chroma needed, fast.
  - round-trip test: actually inserts into a real (temp, disposable) Chroma
    collection and queries it back, proving the pipeline mechanics work end
    to end — this is VEC-01's own acceptance criterion ("can insert and
    query a dummy vector locally").
"""

from backend.logic.routing import RoutingResult, RegimeFilter, route
from backend.services.vector_store import (
    build_where_clause, get_client, get_or_create_collection, add_chunks, query,
)
from backend.rag.chunking import Chunk


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
        regime_filters=[RegimeFilter(legal_regime="patent_law", document_types=["act"])],
        legal_regimes=["patent_law"],
        matched_rows=["test"],
    )
    where = build_where_clause(routing)
    assert where == {
        "$and": [
            {"jurisdiction": "india"},
            {"$and": [{"legal_regime": "patent_law"}, {"document_type": {"$in": ["act"]}}]},
        ]
    }


def test_where_clause_multiple_regimes_becomes_or():
    routing = RoutingResult(
        jurisdiction="india",
        regime_filters=[
            RegimeFilter(legal_regime="patent_law", document_types=None),
            RegimeFilter(legal_regime="biodiversity_law", document_types=None),
        ],
        legal_regimes=["patent_law", "biodiversity_law"],
        matched_rows=["test"],
    )
    where = build_where_clause(routing)
    assert where["$and"][1] == {"$or": [{"legal_regime": "patent_law"}, {"legal_regime": "biodiversity_law"}]}


def test_where_clause_no_regime_filters_falls_back_to_jurisdiction_only():
    routing = RoutingResult(jurisdiction="india", regime_filters=[], legal_regimes=[], matched_rows=[])
    where = build_where_clause(routing)
    assert where == {"jurisdiction": "india"}


def test_where_clause_directly_from_real_route_output():
    """End-to-end proof that ROUTE-01's actual output plugs straight in."""
    routing = route("india", "classical_generic", ["patentability"])
    where = build_where_clause(routing)
    # classical_generic must restrict patent_law to ["act"] per the v2 fix
    patent_clause = next(
        c for c in where["$and"][1]["$or"] if c.get("$and", [{}])[0].get("legal_regime") == "patent_law"
    )
    assert patent_clause == {"$and": [{"legal_regime": "patent_law"}, {"document_type": {"$in": ["act"]}}]}


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
            chunk_id="TEST-1:act", doc_id="TEST-1", jurisdiction="india",
            legal_regime="patent_law", document_type="act", section_or_article="1",
            text="Traditional knowledge cannot be patented under this Act.",
            source_file="fake.md", metadata_source="frontmatter", approx_token_count=10,
        ),
        Chunk(
            chunk_id="TEST-1:rule", doc_id="TEST-1", jurisdiction="india",
            legal_regime="patent_law", document_type="rule", section_or_article="2",
            text="Traditional knowledge disclosure form must be filed.",
            source_file="fake.md", metadata_source="frontmatter", approx_token_count=10,
        ),
    ]
    add_chunks(collection, chunks)

    routing = route("india", "classical_generic", ["patentability"])
    where = build_where_clause(routing)
    results = collection.query(query_texts=["traditional knowledge"], n_results=5, where=where)

    returned_ids = results["ids"][0]
    assert "TEST-1:act" in returned_ids
    assert "TEST-1:rule" not in returned_ids
