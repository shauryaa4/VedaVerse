"""Common inspectable evidence records returned by the unified assessment."""

from typing import Literal

from pydantic import BaseModel


EvidenceStatus = Literal[
    "SUPPORTED",
    "UNSUPPORTED",
    "UNCITED",
    "VERIFIED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
    "CONFLICTING",
]


class EvidenceRecord(BaseModel):
    module: Literal["legal_rag", "abs", "tkdl"]
    evidence_type: Literal["claim", "legal_source", "rule", "prior_art_match"]
    claim_or_finding: str
    status: EvidenceStatus
    source_id: str | None = None
    source_title: str | None = None
    document_type: str | None = None
    authority: str | None = None
    provision: str | None = None
    version: str | None = None
    date_enacted: str | None = None
    last_verified_date: str | None = None
    effective_date: str | None = None
    source_url: str | None = None
    excerpt: str | None = None
    overlap_score: float | None = None
