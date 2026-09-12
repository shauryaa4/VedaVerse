"""
Confidence / abstention gate (CONF-01 -> CONF-05).

This is the final gate before an answer reaches the user, per the team
workflow doc's own description: "combine pip.classification.confidence
with the citation verification result to decide whether to answer
normally, hedge, or abstain/escalate to a human."

Pipeline:
  CONF-01  ConfidenceDecision type + operating thresholds      <- this file
  CONF-02  compute_confidence_decision()                       <- this file
  CONF-03  apply_confidence_decision() (mutate the RagResponse) <- this file
  CONF-04  escalation/hedge reason text                        <- folded into
           CONF-02/03 above (kept together since the reason a decision was
           made and the decision itself should never drift out of sync)
  CONF-05  evaluate_confidence() -- the actual integration entrypoint
           routes/query.py calls; ties CLS confidence + CITE support score
           + routing status_notes into one decision, applied to the
           RagResponse before it's returned to the user.

Inputs consumed (all already real, nothing here invents a new signal):
  - pip.classification.confidence  (CLS-01, backend/models/pip.py)
  - calculate_support_score(classifications)  (CITE-05)
  - the should_abstain flag from strip_unsupported_sentences() (CITE-06)
  - RagResponse.status_notes  (routing.py's status_notes, surfaced through
    RAG-03's contract as of this task -- see generation.py)
"""

from typing import Literal, Optional

from backend.logic.classification import Confidence
from backend.rag.generation import RagResponse

# ---------------------------------------------------------------------------
# CONF-01 -- decision type + thresholds
# ---------------------------------------------------------------------------

ConfidenceDecision = Literal["answer", "hedge", "abstain"]

# Citation support score (CITE-05, a float in [0.0, 1.0]) operating points.
# Same spirit as CITE-03's OVERLAP_SUPPORT_THRESHOLD: simple, explainable
# numbers for the hackathon, tunable later against real examples.
SUPPORT_SCORE_ABSTAIN_BELOW = 0.50  # combined with low classification confidence -> abstain
SUPPORT_SCORE_HEDGE_BELOW = 0.75    # below this alone -> hedge, even with high classification confidence

HEDGE_DISCLAIMER = (
    "\n\n---\n"
    "Note: parts of this answer could not be fully verified against the "
    "retrieved legal text, or the underlying classification was uncertain. "
    "Treat this as a starting point, not a final legal conclusion -- verify "
    "against the cited sections or consult a professional before relying on it."
)


# ---------------------------------------------------------------------------
# CONF-02 / CONF-04 -- combine signals into a decision + reason
# ---------------------------------------------------------------------------


def compute_confidence_decision(
    classification_confidence: Optional[Confidence],
    citation_support_score: float,
    citation_forced_abstain: bool,
    status_notes: list[str],
) -> tuple[ConfidenceDecision, str]:
    """
    CONF-02: decide whether the final answer should be returned as-is,
    hedged, or abstained/escalated, and CONF-04: produce the human-readable
    reason for that decision (kept together so the two can never drift).

    Precedence (checked in this order; first match wins):
      1. citation_forced_abstain (CITE-06's near-empty-after-stripping
         signal) -> ABSTAIN. If citation verification already stripped the
         answer down to nothing, no classification confidence can rescue it.
      2. Low classification confidence AND low citation support -> ABSTAIN.
         Two independently weak signals compounding is treated as "the
         system doesn't actually know", not averaged into a medium answer.
      3. Low classification confidence, OR citation support below the hedge
         threshold, OR any routing status_notes present (e.g. a treaty
         that's signed but not yet in force) -> HEDGE. Any one of these
         alone is a reason to add a visible caveat, not to block the answer.
      4. Otherwise -> ANSWER as generated.

    A missing classification_confidence (None) is treated as "low" -- the
    absence of a confidence signal is itself a reason for caution, not a
    free pass.
    """
    confidence = classification_confidence or "low"

    if citation_forced_abstain:
        return "abstain", (
            "The generated answer had too little citation-supported content "
            "remaining after verification to return safely."
        )

    if confidence == "low" and citation_support_score < SUPPORT_SCORE_ABSTAIN_BELOW:
        return "abstain", (
            f"Classification confidence was low and only "
            f"{citation_support_score:.0%} of the answer's claims were "
            f"citation-supported -- too uncertain on both counts to answer safely."
        )

    reasons = []
    if confidence == "low":
        reasons.append("classification confidence was low")
    if citation_support_score < SUPPORT_SCORE_HEDGE_BELOW:
        reasons.append(f"only {citation_support_score:.0%} of claims were citation-supported")
    if status_notes:
        reasons.append("the matched law includes a status caveat (see notes)")

    if reasons:
        return "hedge", "; ".join(reasons) + "."

    return "answer", "Classification confidence and citation support were both sufficient."


# ---------------------------------------------------------------------------
# CONF-03 -- apply the decision to a RagResponse
# ---------------------------------------------------------------------------


def apply_confidence_decision(
    rag_response: RagResponse,
    decision: ConfidenceDecision,
    reason: str,
) -> RagResponse:
    """
    CONF-03: mutates rag_response in place to reflect the decision, and
    returns it (for convenient chaining). Does not recompute anything --
    pure application of a decision already made by compute_confidence_decision().
    """
    if decision == "abstain":
        rag_response.abstained = True
        rag_response.abstain_reason = reason
        rag_response.answer_text = ""
    elif decision == "hedge":
        if not rag_response.answer_text.endswith(HEDGE_DISCLAIMER):
            rag_response.answer_text = rag_response.answer_text.rstrip() + HEDGE_DISCLAIMER
    # decision == "answer": no change.

    return rag_response


# ---------------------------------------------------------------------------
# CONF-05 -- integration entrypoint (called from routes/query.py)
# ---------------------------------------------------------------------------


def evaluate_confidence(
    classification_confidence: Optional[Confidence],
    citation_support_score: float,
    citation_forced_abstain: bool,
    rag_response: RagResponse,
) -> RagResponse:
    """
    CONF-05: the single call site query.py needs. Reads
    rag_response.status_notes directly (already on the contract as of this
    task) so callers only need to pass the CLS/CITE signals that live
    outside RagResponse.
    """
    decision, reason = compute_confidence_decision(
        classification_confidence,
        citation_support_score,
        citation_forced_abstain,
        rag_response.status_notes,
    )
    return apply_confidence_decision(rag_response, decision, reason)