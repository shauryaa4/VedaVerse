# Backend checklist audit: phases 0–14

This status uses the user's checklist definitions. “Implemented” means the
repository has a concrete code path and local tests; live third-party services
and production deployment still need separate verification.

| Phase | Checklist area | Current status | Evidence / remaining work |
|---|---|---|---|
| 0 | Backend repository audit | Implemented | `backend/ARCHITECTURE.md` maps the actual modules and traces `POST /query`; remaining operational limits are listed there. |
| 1 | PIP / product intake | Implemented | `/intake` merges explicit validated fields and preserves omitted values; `tests/test_intake.py`. |
| 2 | Classification | Implemented | Deterministic classifier; `tests/test_classification.py`. The PIP adapter still lacks a clinical-safety evidence input. |
| 3 | Routing | Implemented | Deterministic jurisdiction/category/objective routing; `tests/test_routing.py`. |
| 4 | PIP → ABS | Implemented | Unified assessment calls the ABS endpoint with saved PIP facts; ABS suite covers rules and scenarios. |
| 5 | PIP → TKDL | Implemented | Independent TKDL endpoint and source-derived offline archive; `tests/test_tkdl.py`. |
| 6 | Unified legal RAG | Implemented locally | Shared Chroma collection has legal source chunks and query retrieval passes retrieved text plus metadata to Gemini. Deployment still needs persistent Chroma storage and ingestion. |
| 7 | Citation verification | Partial | Cited/uncited/unsupported claims are classified and unsupported sentences are removed. The score is lexical; semantic entailment and conflicting-authority resolution remain unimplemented. |
| 8 | Evidence engine | Implemented for returned modules | `/assessment` now includes a shared `evidence` array for legal claims, ABS citations, and TKDL candidate matches, with source fields and explicit verification status. TKDL matches remain `UNVERIFIED` candidates. |
| 9 | Abstention | Partial | Missing biological origin/ingredient inputs produce `INSUFFICIENT_INFORMATION`; contradictory questionnaire/ABS origin inputs and explicitly `CONFLICTING` ABS fact profiles produce `CONFLICTING` and escalation. Contradictions that were not marked or represented in input fields cannot be inferred reliably. |
| 10 | Human escalation | Implemented for ABS cases | Structured ABS escalation carries reasons, facts, missing facts, conflicts, rules, and sources; unified response exposes `human_review_required`. |
| 11 | Unified final answer | Implemented | `POST /assessment` returns classification, routing, optional legal answer, separate ABS/TKDL outputs, and labelled final text. |
| 12 | Unified API | Implemented | `POST /assessment` validates session/jurisdiction and runs the applicable modules. |
| 13 | Backend end-to-end scenarios | Implemented and passing locally | `tests/test_assessment_scenarios.py` exercises the eight requested local scenarios through `/assessment`. It avoids live Gemini/Bhashini calls by design. |
| 14 | ABS regression / 34 scenarios | Implemented and passing locally | `tests/test_abs_34_scenarios.py` contains scenarios 1–34; ABS, grounding, citation, confidence, assessment, and full suite passed after this change. |

## Deployment checks still required

- Set Gemini and Bhashini credentials in the backend host's secret settings.
- Set `CORS_ALLOW_ORIGINS` to the exact deployed frontend origin(s).
- Keep Chroma on persistent storage and run `python scripts/ingest_corpus.py` during deployment.
- Use shared persistence for sessions/citation cache before running multiple backend workers or relying on process restarts.
- Verify deployed frontend API URL, audio transcoding dependencies, and live provider pipelines in the target environment.

## Checklist items beyond phase 14

The supplied document also lists a separate security/data-quality phase and a
later cleanup phase. Those are outside this 0–14 matrix; dedicated adversarial
input/citation tests and repository cleanup have not been completed here.
