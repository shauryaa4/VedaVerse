from backend.rag.generation import RetrievedChunkRef
from backend.logic.citation_verification import (
    extract_claim_citation_pairs,
    get_chunk_text,
    score_overlap,
    OVERLAP_SUPPORT_THRESHOLD,
    classify_citation_support,
    calculate_support_score,
    strip_unsupported_sentences,
)

# ---------------------------------------------------------------------------
# CITE-01 tests
# ---------------------------------------------------------------------------


def test_single_cited_sentence():
    text = "Classical Ayurvedic formulations are excluded from patentability [IN-1:3(p)]."
    pairs = extract_claim_citation_pairs(text)
    assert len(pairs) == 1
    sentence, chunk_id = pairs[0]
    assert chunk_id == "IN-1:3(p)"
    assert "[IN-1:3(p)]" in sentence


def test_uncited_sentence_gets_null_chunk_id():
    text = "You should still consult a registered patent agent before filing."
    pairs = extract_claim_citation_pairs(text)
    assert len(pairs) == 1
    _, chunk_id = pairs[0]
    assert chunk_id is None


def test_mixed_multi_sentence_answer():
    text = (
        "Classical Ayurvedic formulations are excluded from patentability [IN-1:3(p)]. "
        "This exclusion does not apply to novel combinations with demonstrated efficacy [IN-1:3(d)]. "
        "You should still consult a registered patent agent before filing."
    )
    pairs = extract_claim_citation_pairs(text)
    assert len(pairs) == 3
    assert pairs[0][1] == "IN-1:3(p)"
    assert pairs[1][1] == "IN-1:3(d)"
    assert pairs[2][1] is None  # genuinely uncited, not borrowed from sentence 2


def test_covers_100_percent_of_sentences():
    text = (
        "First claim here [IN-1:10]. "
        "Second claim, no citation. "
        "Third claim [INT-2:Article 5]."
    )
    pairs = extract_claim_citation_pairs(text)
    assert len(pairs) == 3


def test_international_doc_id_and_multiword_section():
    text = "The Nagoya Protocol requires prior informed consent [INT-2:Article 6]."
    pairs = extract_claim_citation_pairs(text)
    assert pairs[0][1] == "INT-2:Article 6"


def test_empty_answer_returns_empty_list():
    assert extract_claim_citation_pairs("") == []


def test_whitespace_only_answer_returns_empty_list():
    assert extract_claim_citation_pairs("   \n  ") == []


# ---------------------------------------------------------------------------
# CITE-02 tests
# ---------------------------------------------------------------------------


def _make_chunk(chunk_id: str, text: str) -> RetrievedChunkRef:
    return RetrievedChunkRef(
        chunk_id=chunk_id,
        text=text,
        source_url=None,
        doc_id=chunk_id.split(":")[0],
        section_or_article=chunk_id.split(":", 1)[1] if ":" in chunk_id else None,
    )


def test_get_chunk_text_finds_matching_chunk():
    used_chunks = [
        _make_chunk("IN-1:3(p)", "traditional knowledge exclusion text"),
        _make_chunk("IN-1:3(d)", "known substance efficacy text"),
    ]
    text = get_chunk_text("IN-1:3(p)", used_chunks)
    assert text == "traditional knowledge exclusion text"


def test_get_chunk_text_hallucinated_chunk_id_returns_none_not_exception():
    # LLM cited a chunk_id that was never actually retrieved/passed into
    # the prompt -- must not raise, CITE-04 needs to mark this UNSUPPORTED.
    used_chunks = [_make_chunk("IN-1:3(p)", "some real text")]
    result = get_chunk_text("IN-999:not-a-real-section", used_chunks)
    assert result is None


def test_get_chunk_text_empty_used_chunks_returns_none():
    assert get_chunk_text("IN-1:3(p)", []) is None


def test_get_chunk_text_returns_full_untruncated_text():
    long_text = "word " * 500
    used_chunks = [_make_chunk("IN-1:10", long_text)]
    assert get_chunk_text("IN-1:10", used_chunks) == long_text


# ---------------------------------------------------------------------------
# CITE-03 tests
# ---------------------------------------------------------------------------


def test_score_overlap_full_match():
    sentence = "The patent excludes traditional knowledge claims [IN-1:3(p)]."
    chunk_text = "This patent excludes traditional knowledge claims explicitly."
    assert score_overlap(sentence, chunk_text) == 1.0


def test_score_overlap_no_match():
    sentence = "Trademarks require distinctive branding elements [IN-2:5]."
    chunk_text = "Biological diversity access requires prior consent from state boards."
    assert score_overlap(sentence, chunk_text) == 0.0


def test_score_overlap_partial_match():
    sentence = "Novel compositions with demonstrated efficacy are patentable [IN-1:3(d)]."
    chunk_text = "A novel composition showing efficacy may qualify for patent protection."
    # claim keywords: novel, compositions, demonstrated, efficacy, patentable (5)
    # matches in chunk: novel, efficacy (2)
    assert score_overlap(sentence, chunk_text) == 2 / 5


def test_score_overlap_strips_citation_marker_before_scoring():
    # Regression test: if the marker weren't stripped, "int" and "article"
    # from "[INT-2:Article 6]" would leak in as claim keywords and produce
    # a false positive overlap against this specific chunk_text.
    sentence = "The Nagoya Protocol requires prior informed consent [INT-2:Article 6]."
    chunk_text = "int article"
    assert score_overlap(sentence, chunk_text) == 0.0


def test_score_overlap_empty_chunk_text():
    sentence = "Classical formulations are excluded from patentability [IN-1:3(p)]."
    assert score_overlap(sentence, "") == 0.0


def test_score_overlap_sentence_with_only_stopwords():
    sentence = "This is not that."
    assert score_overlap(sentence, "some chunk text with real words") == 0.0


def test_overlap_support_threshold_is_a_float_between_0_and_1():
    assert 0.0 <= OVERLAP_SUPPORT_THRESHOLD <= 1.0


def test_clearly_supported_claim_is_above_threshold():
    sentence = (
        "A phytopharmaceutical must satisfy quality requirements [IN-1:3]"
    )
    chunk = (
        "A phytopharmaceutical must satisfy quality requirements "
        "before approval."
    )

    score = score_overlap(sentence, chunk)

    assert score >= OVERLAP_SUPPORT_THRESHOLD


def test_unrelated_claim_is_below_threshold():
    sentence = (
        "A phytopharmaceutical is exempt from patent registration [IN-1:3]"
    )
    chunk = (
        "A phytopharmaceutical must satisfy quality requirements "
        "before approval."
    )

    score = score_overlap(sentence, chunk)

    assert score < OVERLAP_SUPPORT_THRESHOLD

    # ---------------------------------------------------------------------------
# CITE-04 tests
# ---------------------------------------------------------------------------


def test_cited_sentence_with_high_score_is_supported():
    sentence = (
        "A phytopharmaceutical must satisfy quality requirements [IN-1:3]"
    )
    chunk = (
        "A phytopharmaceutical must satisfy quality requirements "
        "before approval."
    )

    score = score_overlap(sentence, chunk)

    assert classify_citation_support(sentence, chunk, score) == "SUPPORTED"


def test_cited_sentence_with_low_score_is_unsupported():
    sentence = (
        "A phytopharmaceutical is exempt from patent registration [IN-1:3]"
    )
    chunk = (
        "A phytopharmaceutical must satisfy quality requirements "
        "before approval."
    )

    score = score_overlap(sentence, chunk)

    assert classify_citation_support(sentence, chunk, score) == "UNSUPPORTED"


def test_uncited_sentence_is_uncited():
    sentence = (
        "You should consult a registered patent agent before filing."
    )

    assert classify_citation_support(sentence, None, 0.0) == "UNCITED"

    # ---------------------------------------------------------------------------
# CITE-05 tests
# ---------------------------------------------------------------------------


def test_calculate_support_score_three_of_five_supported():
    classifications = [
        "SUPPORTED",
        "SUPPORTED",
        "UNSUPPORTED",
        "SUPPORTED",
        "UNCITED",
    ]

    assert calculate_support_score(classifications) == 0.6


def test_calculate_support_score_all_supported():
    classifications = [
        "SUPPORTED",
        "SUPPORTED",
        "SUPPORTED",
    ]

    assert calculate_support_score(classifications) == 1.0


def test_calculate_support_score_none_supported():
    classifications = [
        "UNSUPPORTED",
        "UNCITED",
        "UNSUPPORTED",
    ]

    assert calculate_support_score(classifications) == 0.0


def test_calculate_support_score_empty_list():
    assert calculate_support_score([]) == 0.0

    # ---------------------------------------------------------------------------
# CITE-06 tests
# ---------------------------------------------------------------------------


def test_strip_unsupported_sentence_and_keep_supported_sentences():
    answer = (
        "This product satisfies the required quality standards [IN-1:3]. "
        "This product is automatically exempt from patent law [IN-1:4]. "
        "The required documentation must also be maintained [IN-1:5]."
    )

    classifications = [
        "SUPPORTED",
        "UNSUPPORTED",
        "SUPPORTED",
    ]

    filtered_answer, should_abstain = strip_unsupported_sentences(
        answer,
        classifications,
    )

    assert (
        filtered_answer
        == "This product satisfies the required quality standards [IN-1:3]. "
        "The required documentation must also be maintained [IN-1:5]."
    )
    assert should_abstain is False


def test_strip_uncited_sentence():
    answer = (
        "This product satisfies the required quality standards [IN-1:3]. "
        "You should consult a patent agent before filing."
    )

    classifications = [
        "SUPPORTED",
        "UNCITED",
    ]

    filtered_answer, should_abstain = strip_unsupported_sentences(
        answer,
        classifications,
    )

    assert (
        filtered_answer
        == "This product satisfies the required quality standards [IN-1:3]."
    )
    assert should_abstain is False


def test_strip_all_unsupported_sentences_triggers_abstention():
    answer = (
        "This product is exempt from patent law [IN-1:3]. "
        "This product requires no regulatory approval [IN-1:4]."
    )

    classifications = [
        "UNSUPPORTED",
        "UNSUPPORTED",
    ]

    filtered_answer, should_abstain = strip_unsupported_sentences(
        answer,
        classifications,
    )

    assert filtered_answer == ""
    assert should_abstain is True


def test_near_empty_remaining_answer_triggers_abstention():
    answer = (
        "Yes [IN-1:3]. "
        "This second sentence contains an unsupported claim [IN-1:4]."
    )

    classifications = [
        "SUPPORTED",
        "UNSUPPORTED",
    ]

    filtered_answer, should_abstain = strip_unsupported_sentences(
        answer,
        classifications,
    )

    assert filtered_answer == "Yes [IN-1:3]."
    assert should_abstain is True

    