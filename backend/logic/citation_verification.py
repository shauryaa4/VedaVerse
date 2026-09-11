"""
Citation verification pipeline (CITE-01 -> CITE-08).
 
This module checks whether every claim in a generated answer is actually
backed by the retrieved legal text it cites, per build spec §8.
 
Pipeline (built incrementally, task by task):
  CITE-01  extract_claim_citation_pairs()   <- done
  CITE-02  get_chunk_text()                 <- done (reads real RagResponse.used_chunks)
  CITE-03  score_overlap()                  <- done (keyword overlap, placeholder threshold)
  CITE-04  (SUPPORTED / UNSUPPORTED / UNCITED classification) <- not yet implemented
  CITE-05  (aggregate support score)        <- not yet implemented
  CITE-06  (strip unsupported sentences)    <- not yet implemented
  CITE-07  (GET /citation/{doc_id}/{section})  <- lives in routes/, not here
  CITE-08  (injected unsupported-claim test)   <- lives in tests/
"""
 
import re
from typing import List, Optional, Tuple
 
from backend.rag.generation import RetrievedChunkRef
 
# Matches citation markers in the format [doc_id:section], e.g.
# [IN-1:3(p)] or [INT-4:Article 27]. doc_id is alphanumeric + hyphens;
# section can contain spaces/parens/periods, so it's captured greedily
# up to the closing bracket.
_MARKER_PATTERN = re.compile(r"\[([A-Za-z0-9\-]+):([^\]]+)\]")
 
# Splits text into sentences on '.', '!', or '?' followed by whitespace
# and then a capital letter or an opening citation bracket. This is a
# lightweight heuristic tuned for this system's answer style (short,
# citation-marker-terminated claims) -- not a general NLP sentence
# tokenizer, and it will mis-split on abbreviations like "Dr." or
# "e.g." if those ever show up in generated answers.
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[])")
 
 
def _split_sentences(text: str) -> List[str]:
    """Split answer text into sentences, keeping any inline markers."""
    text = text.strip()
    if not text:
        return []
    sentences = _SENTENCE_SPLIT_PATTERN.split(text)
    return [s.strip() for s in sentences if s.strip()]
 
 
def extract_claim_citation_pairs(
    answer_text: str,
) -> List[Tuple[str, Optional[str]]]:
    """
    CITE-01: split an LLM-generated answer into sentences and pair each
    one with the citation marker it contains, if any.
 
    A marker belongs to a sentence if it appears within that sentence's
    own text span (a sentence with no marker is genuinely uncited, per
    CITE-04's UNCITED classification -- we do not carry forward a
    marker from an earlier sentence). If a sentence contains more than
    one marker, the last one is used, on the assumption that a claim
    citing two sources places both markers together at the end of the
    sentence and the final one is closest to the claim it's citing.
 
    Returns a list of (sentence_text, chunk_id) pairs, one per sentence,
    covering 100% of the input's sentences in order. chunk_id is in the
    same "doc_id:section" format used throughout the corpus (e.g.
    "IN-1:3(p)", confirmed against the real chunking.py's _build_chunk()),
    or None if the sentence has no marker.
 
    ASSUMPTION STILL UNCONFIRMED: this assumes RAG-01's prompt instructs
    the LLM to emit these [doc_id:section] markers inline in answer_text.
    backend/rag/generation.py's real RagResponse.answer_text is typed as
    a plain str with no marker-format guarantee in its own docstring, and
    the actual prompt template (RAG-01) hasn't been reviewed yet. If it
    turns out markers aren't emitted this way, only this function's
    internals need to change -- its signature and return shape are what
    CITE-02 onward is built against, so downstream code is insulated
    either way.
 
    NOTE (temporary): per the build spec, this logic belongs in a
    shared utility owned by RAG-04 (backend/services/citation_parser.py)
    that both RAG-03's response formatting and this CITE-01 step are
    supposed to reuse, so the two don't drift out of sync on what
    counts as a "sentence" or a "marker". RAG-04 doesn't exist in this
    repo yet, so this function currently duplicates that logic locally.
    Once RAG-04 lands: replace this function's body with a call into
    it, but keep the signature and return shape exactly as they are.
    """
    pairs: List[Tuple[str, Optional[str]]] = []
    for sentence in _split_sentences(answer_text):
        markers = _MARKER_PATTERN.findall(sentence)
        if markers:
            doc_id, section = markers[-1]
            chunk_id = f"{doc_id}:{section}"
        else:
            chunk_id = None
        pairs.append((sentence, chunk_id))
    return pairs
 
 
# ---------------------------------------------------------------------------
# CITE-02 -- evidence chunk lookup
# ---------------------------------------------------------------------------
 
 
def get_chunk_text(chunk_id: str, used_chunks: List[RetrievedChunkRef]) -> Optional[str]:
    """
    CITE-02: look up the full text of a cited chunk.
 
    Reads from RagResponse.used_chunks (backend/rag/generation.py) --
    the actual chunks RAG-03 retrieved and passed into the prompt for
    that specific answer. This is deliberately NOT a separate database
    or vector-store lookup: used_chunks already carries each chunk's
    full, untruncated text, so a citation gets checked against exactly
    what the LLM saw for that query, not a possibly-different or
    since-updated copy fetched independently.
 
    This also naturally handles a hallucinated citation: if chunk_id
    doesn't match any chunk actually passed into the prompt, it simply
    isn't in used_chunks, and this returns None (not an exception) --
    CITE-04 classifies that as UNSUPPORTED rather than crashing the
    pipeline.
    """
    for chunk in used_chunks:
        if chunk.chunk_id == chunk_id:
            return chunk.text
    return None
 
# ---------------------------------------------------------------------------
# CITE-03 -- lightweight citation support scoring
# ---------------------------------------------------------------------------

# Initial operating threshold for the keyword-overlap support check.
#
# Interpretation:
#   >= 0.50 -> the cited chunk contains at least half of the meaningful
#              keywords in the claim, so the claim is considered
#              sufficiently supported for the lightweight check.
#
# This is intentionally a simple, explainable heuristic for the hackathon.
# It should be tuned later against real corpus examples if evaluation shows
# false positives or false negatives.
OVERLAP_SUPPORT_THRESHOLD = 0.50

# Small stopword list used to prevent common grammatical words from
# dominating the overlap score.
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "with",
}

_WORD_PATTERN = re.compile(r"[a-zA-Z]+")


def _keywords(text: str) -> set[str]:
    """Extract meaningful, normalized keywords from text."""
    words = _WORD_PATTERN.findall(text.lower())

    return {
        word
        for word in words
        if len(word) > 1 and word not in _STOPWORDS
    }


def score_overlap(sentence: str, chunk_text: Optional[str]) -> float:
    """
    CITE-03: calculate a lightweight keyword-overlap support score.

    The score is:

        number of claim keywords found in the cited chunk
        --------------------------------------------------
                    total claim keywords

    Therefore the result is always in the range [0.0, 1.0].

    Citation markers are removed before scoring so document IDs and
    section names do not artificially increase the score.

    A score of:
        1.0 -> all meaningful claim keywords occur in the chunk
        0.0 -> no meaningful claim keywords occur in the chunk

    This is intentionally a lightweight lexical heuristic rather than
    semantic similarity. CITE-04 will use OVERLAP_SUPPORT_THRESHOLD to
    convert this score into SUPPORTED or UNSUPPORTED.
    """
    if not chunk_text:
        return 0.0

    # Remove citation markers such as [IN-1:3(p)] before extracting
    # keywords from the claim.
    sentence_without_marker = _MARKER_PATTERN.sub("", sentence)

    claim_keywords = _keywords(sentence_without_marker)
    if not claim_keywords:
        return 0.0

    chunk_keywords = _keywords(chunk_text)

    overlap = claim_keywords.intersection(chunk_keywords)

    return len(overlap) / len(claim_keywords)

# ---------------------------------------------------------------------------
# CITE-04 -- citation support classification
# ---------------------------------------------------------------------------


def classify_citation_support(
    sentence: str,
    chunk_text: Optional[str],
    score: float,
) -> str:
    """
    CITE-04: classify a sentence's citation support.

    Rules:
      - No citation marker -> UNCITED
      - Citation marker + score >= threshold -> SUPPORTED
      - Citation marker + score < threshold -> UNSUPPORTED

    UNCITED sentences are intentionally kept as a separate classification.
    CITE-06/downstream logic will treat UNCITED as unsupported when deciding
    what may remain in the final answer.
    """
    markers = _MARKER_PATTERN.findall(sentence)

    if not markers:
        return "UNCITED"

    if score >= OVERLAP_SUPPORT_THRESHOLD:
        return "SUPPORTED"

    return "UNSUPPORTED"

# ---------------------------------------------------------------------------
# CITE-05 -- aggregate citation support score
# ---------------------------------------------------------------------------


def calculate_support_score(classifications: List[str]) -> float:
    """
    CITE-05: calculate the proportion of claim sentences that are supported.

    The score is:

        number of SUPPORTED sentences
        ------------------------------
        total claim sentences

    SUPPORTED contributes to the numerator.

    UNSUPPORTED and UNCITED remain part of the denominator and therefore
    reduce the overall support score.

    Returns 0.0 when there are no claim sentences.
    """
    if not classifications:
        return 0.0

    supported_count = sum(
        classification == "SUPPORTED"
        for classification in classifications
    )

    return supported_count / len(classifications)

# ---------------------------------------------------------------------------
# CITE-06 -- strip unsupported sentences
# ---------------------------------------------------------------------------

# After unsupported/uncited sentences are removed, an answer shorter than
# this is considered "near-empty" and should trigger CONF-02 rather than
# being returned as a useless answer bubble.
#
# This is an initial conservative operating threshold for the hackathon.
MIN_REMAINING_ANSWER_LENGTH = 20


def strip_unsupported_sentences(
    answer_text: str,
    classifications: List[str],
) -> Tuple[str, bool]:
    """
    CITE-06: remove UNSUPPORTED and UNCITED sentences from the final answer.

    The classifications list must correspond to the sentences produced by
    CITE-01, in the same order.

    Only SUPPORTED sentences are retained.

    Returns:
        (filtered_answer, should_abstain)

        filtered_answer:
            The final answer containing only supported sentences.

        should_abstain:
            True when the remaining answer is empty or near-empty, so
            CONF-02 can trigger abstention instead of returning an unusable
            answer.
    """
    sentences = _split_sentences(answer_text)

    # Keep only sentences explicitly classified as SUPPORTED.
    supported_sentences = [
        sentence
        for sentence, classification in zip(sentences, classifications)
        if classification == "SUPPORTED"
    ]

    filtered_answer = " ".join(supported_sentences).strip()

    should_abstain = len(filtered_answer) < MIN_REMAINING_ANSWER_LENGTH

    return filtered_answer, should_abstain