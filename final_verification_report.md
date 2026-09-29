# VedaVerse / IP-SAKTI Sahayak — final verification

**Verified:** 2026-09-30  
**Repository:** local branch `codex/non-code-completion-docs`, based on merged `main` commit `6e3d0b4` (PR #5 merge).  
**Scope:** verification and documentation only. No application code or tests were changed. These checks establish local repository behavior, not production readiness.

## Executive result

The repository contains functioning components, but the requested end-to-end system is not yet verified as one coherent flow. The local production frontend build passed and the focused ABS suites passed. However, the full backend suite has one failure; a cross-source conflict was overwritten; structured ABS missing-information and escalation results are not surfaced by the current UI; and the post-ingestion live query returned HTTP 500 after Gemini returned 503 and then 429. There is no configured deployment or fresh deployed session.

## Baseline and actual checks

| Check | Actual result | Notes |
|---|---:|---|
| ABS tests (`test_abs.py`, `test_abs_engine.py`) | **16 passed** | Python 3.13.0 |
| ABS grounding | **6 passed** | Python 3.13.0 |
| ABS 34-scenario suite | **34 passed** | Python 3.13.0 |
| Relevant integration (`test_integration_slice.py`, `test_app_wiring.py`) | **2 passed** | Python 3.13.0 |
| Full backend suite | **260 passed, 1 failed** | `tests/test_confidence.py::test_abstention_is_not_overridden_by_high_numeric_score`; expected confidence score `1.0`, received `0.8`. One Starlette/httpx deprecation warning. |
| Frontend automated tests / type check | **Not available** | `frontend/package.json` has no test or type-check script. |
| Frontend production build | **Passed** | `npm ci`, then `npm run build`; Vite 5.4.21, 78 modules. |
| Dependency audit | **Findings** | One high and one moderate advisory in dev/build dependencies (Vite/esbuild); recommended fix entails a Vite 8 major upgrade. No automatic upgrade applied. |
| Legal corpus ingestion | **Passed locally** | Windows required `python -X utf8 scripts/ingest_corpus.py`; generated 23 Chroma chunks, 10 flagged oversized. Retrieval script returned corpus records. |
| Python runtime parity | **Not verified** | `runtime.txt` specifies Python 3.11.9; all recorded tests used Python 3.13.0. |

Historical figures (8 ABS tests, 6 grounding tests, 179 full-suite passes) are not used as current proof. The current focused counts above are the latest observed results.

## End-to-end scenarios A–H

The local API calls used synthetic facts. `/session`, `/intake`, `/classify`, `/abs/assess`, `/tkdl/search`, and `/query` are separate requests; the repository does not orchestrate them into a single unified final assessment. Browser observation reached the landing, jurisdiction, and intake screens but did not complete all result tabs.

| Scenario | Input and route | Backend result | Frontend / evidence / citations | Status and reason |
|---|---|---|---|---|
| **A — ordinary Indian product** | Synthetic Ashwagandha + Shatavari product; session → intake → classify → ABS → TKDL → query. | Classification `proprietary`, confidence high. ABS `CONDITIONAL`, pathway `UNRESOLVED`, one missing-information item. TKDL returned 0 matches. After corpus ingestion, `/query` reached Gemini but returned HTTP 500 after provider 503; one retry returned HTTP 500 after provider 429. | Intake UI observed. Full results UI, generated answer, citation detail, and displayed evidence not verified. Earlier pre-ingestion query abstained with zero chunks; it does not prove post-ingestion answer behavior. | **PARTIAL** — component calls worked except answer generation; user-facing completion not verified. |
| **B — foreign applicant** | Plant product, PIP Indian origin; `/abs/assess` with `applicant.entity_category=foreign_entity_or_individual`. | `STRONG`, pathway `SECTION_3_NBA_APPROVAL`, forms `FORM_1`, `FORM_3`; `human_review=false`. | API only. Frontend does not collect these structured ABS facts or present all response fields. No legal conclusion inferred from the synthetic input. | **PARTIAL** — backend response observed, full UI flow absent. |
| **C — unknown origin** | Plant source with `biological_origin_known=no`; `/abs/assess`. | `CONDITIONAL`; missing `biological_origin_region`; `human_review=true`; `abstained=false`. | Structured missing-information list not shown in current ABS UI. | **PARTIAL** — missing fact is flagged in API, but abstention was not returned and UI visibility is missing. |
| **D — conflicting facts** | PIP origin India; ABS facts report Brazil and `CONFLICTING`; `/abs/assess`. | PIP adapter retained India, returned `CONDITIONAL`, `human_review=false`. | No separate ABS facts editor or conflict presentation in frontend. | **FAIL** — conflict was overwritten instead of preserved/escalated. |
| **E — IPR-related** | Plant origin India; patentability objective; prototype; `/classify` + `/abs/assess`. | Classification `unresolved` / low confidence on minimal facts. ABS `CONDITIONAL`, `CONDITIONAL_ON_ENTITY_STATUS`, `ipr_stage=CONSIDERING_IPR`, rule `ABS_RULE_SEC6_IPR_APPROVAL`, missing `entity_category`. | API only; complete IPR journey and evidence display not verified. | **PARTIAL** — some state returned; material applicant fact missing and UI path not verified. |
| **F — TKDL** | Composition Mercury + Sulphur; `/tkdl/search`. | 108 matches, `risk_level=high`; this measures archive overlap. Existing TKDL suite validates offline source-derived records. | Separate TKDL endpoint/tab; offline archive banner present. No live TKDL connection. | **PASS** for separate offline search behavior; **NOT IN SCOPE** for live TKDL. Matches are not legal/medical determinations. |
| **G — insufficient information** | No ingredient source; `/abs/assess`. | `INSUFFICIENT_INFORMATION`, `abstained=true`, missing `ingredient_sources`. | API only; frontend does not render the complete structured state. | **PARTIAL** — backend abstention observed, user-facing abstention/evidence not verified. |
| **H — human escalation** | Indian-origin plant; Indian company with foreign control; `/abs/assess`. | `ESCALATION_RECOMMENDED`, `human_review=true`, reason includes Section 3(2) foreign participation/control. | API only; ABS screen does not render `human_escalation`. | **PARTIAL** — structured escalation observed from API, not presented through the UI. |

### RAG, sources, and citation behavior

Corpus ingestion and standalone retrieval were verified locally. After ingestion, `/query` attempted generation and failed at the Gemini provider (503; then 429 quota exceeded on one retry), surfaced as HTTP 500. No final answer or citation display could be verified end to end. Citation-related automated tests passed within the test runs, but that is not equivalent to a live sourced answer. The current citation support is lexical overlap, not validation of legal meaning or correctness.

## Frontend and repository checks

- Frontend session/intake interaction was observed in a browser; the full classification and result-tab journey was not completed.
- Code paths include loading/error states and questionnaire validation, but those states were not dynamically exercised in this verification.
- Classification is displayed in the case flow. ABS, TKDL, and legal Q&A are separate requests/tabs. The ABS screen omits some structured missing-information, forms, citation, and escalation fields. No dedicated conflict workflow was found.
- TKDL is labelled as an offline archive. Evidence and citations are not unified across ABS, TKDL, and legal Q&A.
- No export/share endpoint or UI was found. Treat export/share as **NOT IN SCOPE** unless the product owner says otherwise.
- No comprehensive static proof of “no statutory logic in frontend” was conducted; observed architecture places deterministic assessment rules in the backend.
- No deployment host, public URL, or credentials/platform decision was available. No deployment or fresh deployed-browser session was attempted.
- Live local `/health` returned `{"status":"ok"}`. This checks process response only; it does not verify the corpus, external providers, or production configuration.
- `git check-ignore` confirmed that `.env`, frontend `node_modules` and `dist`, Chroma SQLite data, the account database, query log, and `.pytest-tmp` match ignore rules. No tracked `.env`, database, Chroma index, build output, or `node_modules` was found. A repository pattern scan found no matching API-key/private-key patterns in tracked `HEAD` files. This is a scoped check, not a complete secrets audit of every historical object or external archive.
- Legal corpus, TKDL source-derived data, tests, and configuration remain in the repository. Route inspection found 29 unique registered OpenAPI paths and no duplicate path entries.
- The legacy `README.md` remains unchanged and does not match this verification-level documentation. `README_draft.md` is a proposed replacement, not yet the canonical README. The action plan and named team checklists were not present in the checkout.

## Final sign-off matrix

| Area | Status | Evidence | Verified on | Owner |
|---|---|---|---|---|
| Backend pipeline | PARTIAL | Session/intake/classification and separate ABS/TKDL endpoints returned results; no unified journey; `/query` 500; full suite 260/1. | 2026-09-30 | Backend team |
| ABS / TKDL | PARTIAL | Focused ABS suites 16/16, grounding 6/6, scenarios 34/34. API B/C/E/G/H returned structured results; D conflict was overwritten. TKDL offline search returned 108 overlaps. | 2026-09-30 | Backend team |
| RAG / citations / evidence | PARTIAL | Ingested 23 chunks and standalone retrieval succeeded; live generation failed at Gemini (503 then 429), so answer/citation path not verified. | 2026-09-30 | Backend team |
| E2E / regression | FAIL | Full suite has one failing confidence assertion; cross-source conflict behavior failed; live `/query` returned 500. | 2026-09-30 | Backend team |
| Security / data quality | PARTIAL | Ignore rules and tracked-file scans passed; `npm audit` has one high and one moderate dev/build advisory; CORS allows all origins; landing claim overstates citation certainty. | 2026-09-30 | Backend team / frontend team |
| Frontend | PARTIAL | Production build passed; browser observed through intake only; no automated frontend tests; structured ABS states and full result journey not verified. | 2026-09-30 | Frontend team |
| Deployment | BLOCKED | No host, URL, deployment configuration, persistent storage decision, or deployed environment available. | 2026-09-30 | Team decision |
| Documentation / demo | PARTIAL | Draft README, deployment, demo, limitations, navigation, and this report record current evidence; canonical README/action plan/team checklists and demo rehearsal remain unresolved. | 2026-09-30 | Palak / team owner |

## Blockers and follow-ups

### Must fix before demo

- Resolve the failing confidence test without weakening the assertion, then rerun the full backend suite.
- Fix or explicitly contain cross-source ABS fact merging so a conflicting value cannot silently become India with no human review.
- Confirm the live answer-generation provider works and that `/query` returns a sourced answer or honest abstention. Current observed 503/429 became HTTP 500.
- If the demo claims uncertainty/escalation handling, display the structured missing-information and escalation state in the actual frontend or narrow the demo claim to the API-only behavior.
- Do a full browser rehearsal on the actual demo screen/device, including frontend-to-backend connectivity and citations, before presenting it as working.

### Should fix before demo

- Reconcile the landing-page promise that every claim traces to law with the actual lexical citation support.
- Review the Vite/esbuild npm audit advisories and decide on a compatible upgrade; do not apply a major upgrade without validation.
- Restrict CORS to the chosen frontend origin before any public deployment.
- Validate the declared Python 3.11.9 runtime, and pin/reconcile backend dependencies for reproducible setup.
- Fix the Windows ingestion encoding requirement in a documented or robust workflow if Windows is the supported demo environment.

### Can remain as known limitation

- TKDL is an offline source-derived archive, not live TKDL.
- ABS, TKDL, classification, and legal Q&A are separate tools, not a unified automated legal report.
- No export/share flow exists, if the product owner confirms it is outside demo scope.
- Anonymous sessions and citation cache are in memory; local SQLite and Chroma persistence depend on host storage.
- Citation overlap is not legal correctness review. No legal conclusion should be inferred from synthetic examples or overlap counts.

### Requires team decision

- Select backend/frontend hosts, URLs, deployment owner, persistence/backup approach, and corpus ingestion strategy.
- Decide whether demo requires Gemini, Bhashini translation, Bhashini speech, or only a subset; configure secrets server-side.
- Confirm whether export/share is required and what the intended demo scope is.
- Locate and reconcile `vedaverse_my_action_plan`, the final checklist, and the backend checklist; they were not found in this checkout.

### Requires backend team

- Fix conflict precedence/preservation; expose stable conflict and escalation outcomes.
- Resolve the confidence regression and make `/query` surface provider outages as an honest recoverable error/abstention rather than an unhandled 500.
- Verify corpus retrieval plus generated response and source citations under a healthy provider; decide the Chroma deployment path.
- Run full tests under Python 3.11.9 and review dependency reproducibility.

### Requires frontend team

- Complete the browser flow and handle provider/API errors visibly.
- Show ABS missing facts, conflict state, relevant evidence, and escalation in the interface if those are demo promises.
- Verify classification, distinct ABS/TKDL results, legal citations, loading/invalid-input/error states at intended screen sizes.
- Coordinate CORS and production `VITE_API_BASE` with the selected deployment.

### Requires my action

- Confirm whether the zip containing real keys left trusted machines; if exposure is possible, rotate affected keys and record the decision. This verification did not read or reproduce `.env` values.
- Supply/identify the personal action plan and sign-off checklists if they are stored outside this repository.
- Confirm product/demo scope decisions and attend a rehearsal once the technical blockers are cleared.

## Literal demo checklist

### Before opening the demo

- [ ] Confirm the selected deployed URL. **Currently none is configured.**
- [ ] Confirm backend `/health`, then test `/query`; health alone is insufficient.
- [ ] Warm the backend and verify corpus retrieval and provider quota/connectivity.
- [ ] Keep a local backend/frontend fallback ready. From the repo root: `uvicorn backend.main:app --reload --port 8000`; in a second terminal: `cd frontend`, `npm run dev`. Ensure `VITE_API_BASE` points to that backend.
- [ ] If the local corpus is absent, ingest it from repo root using `python -X utf8 scripts/ingest_corpus.py` on Windows.
- [ ] Keep a screen recording available, but only record a successful end-to-end answer/citation run after it works. A recording is the fallback for a provider outage; do not imply a failed live query succeeded.
- [ ] Prepare one ordinary synthetic product input and one backup input. Avoid personal or real applicant data.
- [ ] Have the architecture talking points and known limitations open; label every input as illustrative.

### During demo

- [ ] Start at the landing page, open a case, choose jurisdiction, and enter the prepared synthetic product.
- [ ] Point to the displayed classification and describe it as the prototype's classification result.
- [ ] Open ABS Helper separately; show only fields the UI actually displays. Explain missing structured fields if asked.
- [ ] Open TKDL Match separately; point to source-derived archive matches and state clearly that this is not live TKDL or a legal ruling.
- [ ] Open Ask & Explore only after a preflight query succeeds. Show answer, source excerpt, and citation detail; say citation matching is lexical support, not legal validation.
- [ ] Demonstrate uncertainty with a prepared missing-origin case only if the UI visibly presents it; current API behavior alone is not a UI demo.
- [ ] Demonstrate escalation only after the UI displays the structured result; current verified escalation is API-only.
- [ ] Do not demonstrate the cross-source conflict flow as working; it failed verification.

### If deployment fails

1. Say the deployed service is unavailable and do not claim its behavior was verified.
2. Switch to the local backend command above and local Vite frontend; verify `/health` and the configured API base.
3. If required, populate the local corpus with `python -X utf8 scripts/ingest_corpus.py`.
4. Check `/query` once. If provider returns 503/429 or API 500, stop live retries and use a previously recorded successful answer/citation walkthrough, clearly labelled as a recording.
5. If there is no successful recording, limit the live demo to intake, classification, ABS/TKDL only where those screens work, and explain that generated answer/citation behavior is unavailable. Do not present retrieval-only output as a generated answer.

## FINAL STATUS

# NOT READY

The repository is not ready for an end-to-end demo that promises a coherent legal assessment. A full backend test fails, conflicting ABS facts are overwritten, and live RAG generation returned HTTP 500 under the configured provider's 503/429 responses. The frontend build passes, but only the initial browser journey was observed and key ABS uncertainty/escalation details are not surfaced. Deployment and fresh-session verification are blocked by missing host/platform decisions. A tightly scoped component walkthrough may be possible after a live preflight, but it must not be represented as a verified integrated system.
