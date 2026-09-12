"""
Tests for RAG-03. Run with: pytest -v tests/test_rag.py

None of these tests call the real Gemini API — the LLM client and the
Chroma query() call are both mocked, so this suite runs instantly, offline,
and free. Only scripts/test_llm_connection.py and manual runs of
scripts/ingest_corpus.py touch the real network.
"""

from unittest.mock import MagicMock

import backend.rag.generation as generation
from backend.rag.generation import RetrievedChunkRef, _build_prompt, _results_to_chunk_refs, answer_query
from backend.models.pip import ProductIntelligenceProfile


def _fake_chroma_results(ids, docs, metas):
    """Chroma's real query() return shape: one query batch, so everything is
    wrapped in an extra outer list — [ids_for_query_1], not just ids."""
    return {"ids": [ids], "documents": [docs], "metadatas": [metas]}


# --- _results_to_chunk_refs: pure conversion logic ---

def test_results_to_chunk_refs_converts_chroma_shape():
    results = _fake_chroma_results(
        ["IN-1:3(p)"],
        ["Traditional knowledge cannot be patented."],
        [{"doc_id": "IN-1", "section_or_article": "3(p)", "source_url": "https://example.com"}],
    )
    refs = _results_to_chunk_refs(results)
    assert len(refs) == 1
    assert refs[0].chunk_id == "IN-1:3(p)"
    assert refs[0].doc_id == "IN-1"
    assert refs[0].source_url == "https://example.com"


def test_results_to_chunk_refs_handles_empty_results():
    assert _results_to_chunk_refs(_fake_chroma_results([], [], [])) == []


def test_results_to_chunk_refs_blank_source_url_becomes_none():
    """Chroma metadata can't store None, so vector_store.py stores '' instead —
    confirm we translate that back to a real None, not leave it as ''."""
    results = _fake_chroma_results(
        ["X:1"], ["text"], [{"doc_id": "X", "section_or_article": "1", "source_url": ""}],
    )
    refs = _results_to_chunk_refs(results)
    assert refs[0].source_url is None


# --- _build_prompt: pure string assembly ---

def test_build_prompt_includes_question_and_chunk_labels():
    chunks = [RetrievedChunkRef(
        chunk_id="IN-1:3(p)", text="TK cannot be patented.",
        source_url=None, doc_id="IN-1", section_or_article="3(p)",
    )]
    prompt = _build_prompt("Can I patent this?", chunks)
    assert "Can I patent this?" in prompt
    assert "[IN-1:3(p)]" in prompt
    assert "TK cannot be patented." in prompt


def test_build_prompt_tells_model_not_to_invent_law():
    """Not a style nitpick -- this is the actual safety property CITE-01->08
    will later check the model honored. Confirm the instruction is really there."""
    prompt = _build_prompt("question", [])
    assert "do not invent" in prompt.lower() or "only" in prompt.lower()


def test_build_prompt_groups_chunks_by_regime():
    """RAG-05: a query returning both patent_law and biodiversity_abs chunks
    must show them under separate, clearly labeled sections -- not flattened
    together as if they were one legal domain."""
    chunks = [
        RetrievedChunkRef(
            chunk_id="IN-1:3(p)", text="TK cannot be patented.",
            source_url=None, doc_id="IN-1", section_or_article="3(p)",
            legal_regime="patent_law",
        ),
        RetrievedChunkRef(
            chunk_id="IN-3:3-7", text="ABS approval is required for biological resources.",
            source_url=None, doc_id="IN-3", section_or_article="3-7",
            legal_regime="biodiversity_abs",
        ),
    ]
    prompt = _build_prompt("Can I patent this?", chunks)

    assert "patent_law" in prompt
    assert "biodiversity_abs" in prompt
    # The patent_law heading must appear before its own chunk text, and the
    # biodiversity_abs heading before ITS chunk text -- proving they're in
    # separate labeled sections, not just both mentioned somewhere.
    patent_idx = prompt.index("patent_law")
    tk_text_idx = prompt.index("TK cannot be patented.")
    bio_idx = prompt.index("biodiversity_abs")
    abs_text_idx = prompt.index("ABS approval is required")
    assert patent_idx < tk_text_idx
    assert bio_idx < abs_text_idx


def test_build_prompt_single_regime_still_works():
    """Not a regression from the grouping change -- a single-regime result
    (the common case) should still produce a normal, readable prompt."""
    chunks = [RetrievedChunkRef(
        chunk_id="IN-1:3(p)", text="TK cannot be patented.",
        source_url=None, doc_id="IN-1", section_or_article="3(p)",
        legal_regime="patent_law",
    )]
    prompt = _build_prompt("question", chunks)
    assert "TK cannot be patented." in prompt
    assert prompt.count("patent_law") == 1  # one heading, not duplicated


# --- answer_query(): the full chain, LLM and retrieval both mocked ---

def _classical_pip():
    return ProductIntelligenceProfile(
        jurisdiction="india",
        objective=["patentability"],
        product={"classical_basis": "yes", "intended_use": "therapeutic", "novelty": "existing"},
    )


def test_answer_query_abstains_when_no_chunks_found(monkeypatch):
    monkeypatch.setattr(generation, "vector_query", lambda *a, **kw: _fake_chroma_results([], [], []))
    result = answer_query(_classical_pip(), "some question", collection=None)

    assert result.abstained is True
    assert result.used_chunks == []
    assert result.answer_text == ""
    assert result.abstain_reason is not None
    # Abstaining must NOT call the LLM at all -- no _get_client should even run.
    # (implicitly proven here since we never mocked _get_client and it would
    # raise RuntimeError with no GEMINI_API_KEY if it were reached)


def test_answer_query_calls_llm_and_returns_answer(monkeypatch):
    fake_results = _fake_chroma_results(
        ["IN-1:3(p)"], ["Traditional knowledge cannot be patented."],
        [{"doc_id": "IN-1", "section_or_article": "3(p)", "source_url": ""}],
    )
    monkeypatch.setattr(generation, "vector_query", lambda *a, **kw: fake_results)

    fake_response = MagicMock()
    fake_response.text = "Traditional knowledge cannot be patented under 3(p). [IN-1:3(p)]"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response
    monkeypatch.setattr(generation, "_get_client", lambda: fake_client)

    result = answer_query(_classical_pip(), "Can I patent this?", collection=None)

    assert result.abstained is False
    assert "3(p)" in result.answer_text
    assert len(result.used_chunks) == 1
    assert result.used_chunks[0].chunk_id == "IN-1:3(p)"
    fake_client.models.generate_content.assert_called_once()
    # Confirm the actual question and retrieved text made it into what was sent.
    call_kwargs = fake_client.models.generate_content.call_args.kwargs
    assert "Can I patent this?" in call_kwargs["contents"]
    assert "Traditional knowledge cannot be patented." in call_kwargs["contents"]


def test_answer_query_classifies_pip_if_not_already_classified(monkeypatch):
    fake_results = _fake_chroma_results(
        ["IN-1:3(p)"], ["text"], [{"doc_id": "IN-1", "section_or_article": "3(p)", "source_url": ""}],
    )
    monkeypatch.setattr(generation, "vector_query", lambda *a, **kw: fake_results)
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="answer")
    monkeypatch.setattr(generation, "_get_client", lambda: fake_client)

    pip = _classical_pip()
    assert pip.classification.category is None  # confirms it starts unclassified

    answer_query(pip, "question", collection=None)

    assert pip.classification.category is not None  # answer_query classified it in place


def test_answer_query_does_not_reclassify_an_already_classified_pip(monkeypatch):
    """If the caller already ran classification (e.g. earlier in a session),
    answer_query() shouldn't silently overwrite it with a fresh run."""
    fake_results = _fake_chroma_results(
        ["IN-1:3(p)"], ["text"], [{"doc_id": "IN-1", "section_or_article": "3(p)", "source_url": ""}],
    )
    monkeypatch.setattr(generation, "vector_query", lambda *a, **kw: fake_results)
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="answer")
    monkeypatch.setattr(generation, "_get_client", lambda: fake_client)

    pip = _classical_pip()
    pip.classification.category = "proprietary"  # pretend it was already classified differently

    answer_query(pip, "question", collection=None)

    assert pip.classification.category == "proprietary"  # untouched


def test_answer_query_passes_where_clause_through_for_debugging(monkeypatch):
    fake_results = _fake_chroma_results(
        ["IN-1:3(p)"], ["text"], [{"doc_id": "IN-1", "section_or_article": "3(p)", "source_url": ""}],
    )
    monkeypatch.setattr(generation, "vector_query", lambda *a, **kw: fake_results)
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="answer")
    monkeypatch.setattr(generation, "_get_client", lambda: fake_client)

    result = answer_query(_classical_pip(), "question", collection=None)

    assert result.retrieval_where_clause is not None
    assert result.retrieval_where_clause.get("$and") is not None


# --- RAG-06: language handling ---

def test_build_prompt_defaults_to_english():
    prompt = _build_prompt("question", [])
    assert "Write your answer in English." in prompt
    assert "Hindi" not in prompt


def test_build_prompt_switches_to_hindi():
    prompt = _build_prompt("question", [], language="hi")
    assert "Hindi" in prompt
    assert "do not translate" in prompt.lower() or "citation" in prompt.lower()


def test_answer_query_passes_pip_language_to_prompt(monkeypatch):
    """Confirms the wiring end-to-end: pip.language actually reaches the
    prompt sent to the LLM, not just that _build_prompt itself works."""
    fake_results = _fake_chroma_results(
        ["IN-1:3(p)"], ["text"], [{"doc_id": "IN-1", "section_or_article": "3(p)", "source_url": ""}],
    )
    monkeypatch.setattr(generation, "vector_query", lambda *a, **kw: fake_results)
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = MagicMock(text="uttar")
    monkeypatch.setattr(generation, "_get_client", lambda: fake_client)

    pip = _classical_pip()
    pip.language = "hi"

    answer_query(pip, "question", collection=None)

    call_kwargs = fake_client.models.generate_content.call_args.kwargs
    assert "Hindi" in call_kwargs["contents"]