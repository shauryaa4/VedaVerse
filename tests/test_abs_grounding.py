"""
ABS-03 tests — ground_abs_citations() in isolation.

Deliberately does NOT touch the real Chroma collection (no dependency on
chroma_data/ existing, no embedding-model download, no network). A fake
collection stands in for Chroma's .query() — ground_abs_citations() only
ever calls collection.query(...) via backend.services.vector_store.query(),
so a fake with the same return shape is a faithful, fast substitute.

Run with: pytest tests/test_abs_grounding.py -v
"""

from backend.logic.abs_helper import ground_abs_citations
from backend.models.abs_models import ABSAssessment


class _FakeCollection:
    """Mimics chromadb.Collection.query()'s return shape."""

    def __init__(self, ids, documents, metadatas):
        self._ids = ids
        self._documents = documents
        self._metadatas = metadatas

    def query(self, query_texts, n_results, where=None):
        return {
            "ids": [self._ids],
            "documents": [self._documents],
            "metadatas": [self._metadatas],
        }


def _assessment_with(reasoning: list[str]) -> ABSAssessment:
    return ABSAssessment(relevance="likely", reasoning=reasoning)


def test_no_collection_returns_assessment_unchanged():
    """collection=None must be a safe no-op, not an error — routes/abs_routes.py
    relies on this so a Chroma outage never takes down /abs/assess."""
    assessment = _assessment_with(["Some reasoning line."])
    result = ground_abs_citations(assessment, collection=None)
    assert result.citations == []
    assert result is assessment


def test_strong_overlap_marks_citation_verified():
    reasoning = "Biological origin is declared as India-linked."
    fake = _FakeCollection(
        ids=["IN-3:s.3"],
        documents=["A resource is declared as India-linked and biological in origin."],
        metadatas=[{
            "doc_id": "IN-3",
            "document_name": "Biological Diversity Act 2002",
            "section_or_article": "s.3",
            "source_url": "https://example.gov/bda#s3",
        }],
    )
    assessment = _assessment_with([reasoning])

    result = ground_abs_citations(assessment, collection=fake)

    assert len(result.citations) == 1
    citation = result.citations[0]
    assert citation.reasoning_text == reasoning
    assert citation.doc_id == "IN-3"
    assert citation.document_name == "Biological Diversity Act 2002"
    assert citation.verified is True


def test_weak_overlap_marks_citation_unverified_not_dropped():
    """An ungrounded line is still surfaced (verified=False), never silently
    dropped — matching ABSCitation's own docstring."""
    reasoning = "This tool has no data on the NBA's exemption list."
    fake = _FakeCollection(
        ids=["IN-3:s.7"],
        documents=["State Biodiversity Boards receive prior intimation under section 7."],
        metadatas=[{"doc_id": "IN-3", "section_or_article": "s.7"}],
    )
    assessment = _assessment_with([reasoning])

    result = ground_abs_citations(assessment, collection=fake)

    assert len(result.citations) == 1
    assert result.citations[0].verified is False


def test_no_results_leaves_line_ungrounded():
    fake = _FakeCollection(ids=[], documents=[], metadatas=[])
    assessment = _assessment_with(["A reasoning line with nothing to match."])

    result = ground_abs_citations(assessment, collection=fake)

    assert result.citations == []


def test_multiple_reasoning_lines_each_get_their_own_citation():
    reasoning_lines = [
        "Biological origin is declared as India-linked.",
        "Section 6 requires prior NBA approval before filing.",
    ]

    class _RoundRobinCollection:
        def __init__(self):
            self.calls = 0

        def query(self, query_texts, n_results, where=None):
            self.calls += 1
            text = query_texts[0]
            return {
                "ids": [[f"IN-{self.calls}:s.{self.calls}"]],
                "documents": [[text]],  # perfect overlap with itself -> verified
                "metadatas": [[{"doc_id": f"IN-{self.calls}"}]],
            }

    fake = _RoundRobinCollection()
    assessment = _assessment_with(reasoning_lines)

    result = ground_abs_citations(assessment, collection=fake)

    assert fake.calls == 2
    assert len(result.citations) == 2
    assert {c.reasoning_text for c in result.citations} == set(reasoning_lines)
    assert all(c.verified for c in result.citations)


def test_retrieval_exception_is_swallowed_per_line():
    class _ExplodingCollection:
        def query(self, query_texts, n_results, where=None):
            raise RuntimeError("Chroma is down")

    assessment = _assessment_with(["A reasoning line."])
    result = ground_abs_citations(assessment, collection=_ExplodingCollection())

    # Must not raise, and must leave the assessment usable with no citations.
    assert result.citations == []