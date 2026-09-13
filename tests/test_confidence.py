from backend.rag.confidence import (
    HEDGE_DISCLAIMER,
    apply_confidence_decision,
    compute_confidence_decision,
    evaluate_confidence,
)
from backend.rag.generation import RagResponse


def _make_response(answer_text="Some answer [IN-1:3(p)].", status_notes=None):
    return RagResponse(
        answer_text=answer_text,
        used_chunks=[],
        retrieval_where_clause=None,
        status_notes=status_notes or [],
    )


# ---------------------------------------------------------------------------
# CONF-02 -- decision matrix
# ---------------------------------------------------------------------------


def test_citation_forced_abstain_always_wins():
    decision, level, _ = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=1.0,
        citation_forced_abstain=True,
        status_notes=[],
    )
    assert decision == "abstain"
    assert level == "low"


def test_low_confidence_and_low_support_aborts():
    decision, level, reason = compute_confidence_decision(
        classification_confidence="low",
        citation_support_score=0.2,
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "abstain"
    assert level == "low"
    assert "low" in reason.lower()


def test_low_confidence_alone_hedges_not_aborts():
    decision, level, _ = compute_confidence_decision(
        classification_confidence="low",
        citation_support_score=0.9,  # high support offsets low confidence into a hedge, not abstain
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "hedge"
    assert (
        level == "medium"
    )  # support is well above the abstain floor, so MEDIUM not LOW


def test_moderate_support_alone_hedges():
    decision, level, _ = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=0.6,  # below hedge threshold but above abstain threshold
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "hedge"
    assert level == "medium"


def test_weak_support_within_hedge_shows_low_not_medium():
    # High classification confidence keeps this out of the ABSTAIN branch,
    # but citation support is the harder signal -- badge should read LOW.
    decision, level, _ = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=0.3,
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "hedge"
    assert level == "low"


def test_status_notes_alone_forces_hedge():
    decision, level, reason = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=1.0,
        citation_forced_abstain=False,
        status_notes=["WIPO GRATK Treaty adopted but NOT YET IN FORCE"],
    )
    assert decision == "hedge"
    assert level == "medium"
    assert "status caveat" in reason


def test_high_confidence_and_high_support_answers_cleanly():
    decision, level, _ = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=1.0,
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "answer"
    assert level == "high"


def test_missing_confidence_is_treated_as_low():
    decision, level, _ = compute_confidence_decision(
        classification_confidence=None,
        citation_support_score=0.3,
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "abstain"  # same as explicit "low" + low support
    assert level == "low"


# ---------------------------------------------------------------------------
# CONF-03 -- applying the decision
# ---------------------------------------------------------------------------


def test_apply_abstain_clears_answer_and_sets_reason():
    response = _make_response()
    apply_confidence_decision(response, "abstain", "low", "too uncertain")
    assert response.abstained is True
    assert response.abstain_reason == "too uncertain"
    assert response.answer_text == ""
    assert response.confidence == "low"
    assert response.confidence_reason == "too uncertain"


def test_apply_hedge_appends_disclaimer_once():
    response = _make_response()
    apply_confidence_decision(response, "hedge", "medium", "low support")
    assert response.answer_text.endswith(HEDGE_DISCLAIMER)
    assert response.abstained is False
    assert response.confidence == "medium"

    # Applying again shouldn't double the disclaimer.
    apply_confidence_decision(response, "hedge", "medium", "low support")
    assert response.answer_text.count(HEDGE_DISCLAIMER) == 1


def test_apply_answer_leaves_response_untouched():
    response = _make_response()
    original_text = response.answer_text
    apply_confidence_decision(response, "answer", "high", "fine")
    assert response.answer_text == original_text
    assert response.abstained is False
    assert response.confidence == "high"


def test_default_confidence_before_evaluation_is_high():
    # A freshly-built RagResponse (pre-CONF-05) shouldn't silently look
    # low-confidence just because the field hasn't been evaluated yet.
    response = _make_response()
    assert response.confidence == "high"
    assert response.confidence_reason is None


# ---------------------------------------------------------------------------
# CONF-05 -- integration entrypoint
# ---------------------------------------------------------------------------


def test_evaluate_confidence_reads_status_notes_from_response():
    response = _make_response(status_notes=["not yet in force"])
    result = evaluate_confidence(
        classification_confidence="high",
        citation_support_score=1.0,
        citation_forced_abstain=False,
        rag_response=response,
    )
    assert result.answer_text.endswith(HEDGE_DISCLAIMER)
    assert result.confidence == "medium"
    assert result.confidence_reason is not None


def test_evaluate_confidence_abstain_path_sets_low_confidence():
    response = _make_response()
    result = evaluate_confidence(
        classification_confidence="low",
        citation_support_score=0.1,
        citation_forced_abstain=False,
        rag_response=response,
    )
    assert result.abstained is True
    assert result.confidence == "low"
