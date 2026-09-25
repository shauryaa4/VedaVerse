"""
ABS-02 — ABS-aware decision support helper adapter.

Delegates deterministic ABS evaluation to backend.logic.abs_engine's
17-step fact-driven traceable ABS pathway engine, preserving 100% backward
compatibility with existing PIP calls and test contracts.
"""

from backend.logic.abs_engine import assess_abs_fact_driven
from backend.models.abs_models import ABSAssessment
from backend.models.pip import ProductIntelligenceProfile


def assess_abs(pip: ProductIntelligenceProfile) -> ABSAssessment:
    """Entry point for ABS assessment, delegating to the fact-driven ABS engine."""
    return assess_abs_fact_driven(pip)