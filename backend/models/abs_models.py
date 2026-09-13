"""
ABS-01 — Data model for the ABS-aware decision support helper.

Per build spec section 20:
    "ABS functionality should be presented as: ABS-aware decision support /
    demo helper. It may use rules and mock/demo information. Do not claim
    live NBA filing, live State Biodiversity Board integration, or live
    government status APIs unless those integrations actually exist."

CLASSIFICATION (build spec section 28): this module is RULE-BASED, not
MOCK. Unlike TKDL-01, there is no simulated external dataset here (no
fake NBA records, no fake SBB database) — it applies a small set of
deterministic rules from India's Biological Diversity Act, 2002 (as
amended by the Biological Diversity (Amendment) Act, 2023, with Rules
notified in 2024) directly to fields already captured in the frozen PIP.
There is nothing for an `is_mock` flag to signal here; `disclaimer` below
does the same "decision support, not a filing determination" job that
TKDL's mock flag does for that module.

SCOPE — read before wiring this into routing:
This models INDIA's domestic ABS regime only. `biological_origin_region`
is a free-text PIP field (not a controlled list), so region-matching
below is a simple keyword heuristic, not a lookup against any government
database. The one thing this module deliberately does NOT gate on is
`pip.jurisdiction` ("india" vs "international") — Section 6 of the BD Act
requires NBA approval before applying for IP rights "in India or outside
India" based on a biological resource obtained from India, so a resource
sourced from India stays relevant even when the user is asking an
"international" legal question. See logic/abs_helper.py's module
docstring for the full reasoning and the (real, current-as-of-drafting)
legal citations behind each rule.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

ABSRelevance = Literal["likely", "possible", "unlikely", "not_applicable"]


class ABSAssessment(BaseModel):
    """The ABS-aware decision-support read-out for one Product Intelligence Profile."""

    relevance: ABSRelevance
    reasoning: list[str] = Field(default_factory=list)

    # Plain-language pointer to WHICH body would typically be approached (NBA vs
    # SBB) — never a claim that either was actually contacted or would approve.
    applicable_authority_guidance: list[str] = Field(default_factory=list)

    # Kept as a separate flag (not folded into `relevance`) for the same reason
    # TKDL-02 keeps ingredient-overlap risk separate from process-novelty signals:
    # a resource can be "unlikely" to need routine access permission and STILL
    # trigger the Section 6 pre-IP-filing approval requirement, or vice versa.
    ip_filing_flag: bool = False
    ip_filing_note: Optional[str] = None

    disclaimer: str = (
        "ABS-aware decision support — DEMO HELPER, not a compliance filing "
        "determination. Based on a simplified, deterministic reading of India's "
        "Biological Diversity Act, 2002 (as amended) applied only to the "
        "information you provided. This tool is NOT connected to the National "
        "Biodiversity Authority, any State Biodiversity Board, or any other "
        "government system, and the underlying law changed materially in "
        "2023/2024 — verify against current NBA-notified guidelines and a "
        "qualified ABS/IP professional before taking any compliance action."
    )
