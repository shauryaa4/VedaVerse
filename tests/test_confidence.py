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
    decision, _ = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=1.0,
        citation_forced_abstain=True,
        status_notes=[],
    )
    assert decision == "abstain"


def test_low_confidence_and_low_support_aborts():
    decision, reason = compute_confidence_decision(
        classification_confidence="low",
        citation_support_score=0.2,
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "abstain"
    assert "low" in reason.lower()


def test_low_confidence_alone_hedges_not_aborts():
    decision, _ = compute_confidence_decision(
        classification_confidence="low",
        citation_support_score=0.9,  # high support offsets low confidence into a hedge, not abstain
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "hedge"


def test_moderate_support_alone_hedges():
    decision, _ = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=0.6,  # below hedge threshold but above abstain threshold
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "hedge"


def test_status_notes_alone_forces_hedge():
    decision, reason = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=1.0,
        citation_forced_abstain=False,
        status_notes=["WIPO GRATK Treaty adopted but NOT YET IN FORCE"],
    )
    assert decision == "hedge"
    assert "status caveat" in reason


def test_high_confidence_and_high_support_answers_cleanly():
    decision, _ = compute_confidence_decision(
        classification_confidence="high",
        citation_support_score=1.0,
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "answer"


def test_missing_confidence_is_treated_as_low():
    decision, _ = compute_confidence_decision(
        classification_confidence=None,
        citation_support_score=0.3,
        citation_forced_abstain=False,
        status_notes=[],
    )
    assert decision == "abstain"  # same as explicit "low" + low support


# ---------------------------------------------------------------------------
# CONF-03 -- applying the decision
# ---------------------------------------------------------------------------


def test_apply_abstain_clears_answer_and_sets_reason():
    response = _make_response()
    apply_confidence_decision(response, "abstain", "too uncertain")
    assert response.abstained is True
    assert response.abstain_reason == "too uncertain"
    assert response.answer_text == ""


def test_apply_hedge_appends_disclaimer_once():
    response = _make_response()
    apply_confidence_decision(response, "hedge", "low support")
    assert response.answer_text.endswith(HEDGE_DISCLAIMER)
    assert response.abstained is False

    # Applying again shouldn't double the disclaimer.
    apply_confidence_decision(response, "hedge", "low support")
    assert response.answer_text.count(HEDGE_DISCLAIMER) == 1


def test_apply_answer_leaves_response_untouched():
    response = _make_response()
    original_text = response.answer_text
    apply_confidence_decision(response, "answer", "fine")
    assert response.answer_text == original_text
    assert response.abstained is False


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