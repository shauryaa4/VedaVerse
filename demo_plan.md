# VedaVerse demo preparation

**Purpose:** demonstrate the current repository behavior without presenting a prototype signal as a legal conclusion. The product journey is not fully orchestrated: classification, ABS, TKDL, and legal RAG are separate steps/screens.

## Verification run on 2026-09-30

Using the live local FastAPI app, I submitted a synthetic Ashwagandha/Shatavari PIP through `/session`, `/intake`, `/classify`, `/abs/assess`, `/tkdl/search`, and `/query`:

| Step | Observed result |
|---|---|
| Classification | `proprietary`, confidence `high`. |
| ABS | `CONDITIONAL`, pathway `UNRESOLVED`, one missing-information entry. |
| TKDL | 0 matches for this composition in the local archive. |
| Legal query | HTTP 200 with `abstained=true`, confidence `abstain`, zero retrieved chunks, no answer text. The local Chroma directory had only just been created and corpus ingestion was not run. |

This proves the endpoints can be called in sequence locally, not a complete user-facing pipeline: the UI did not combine their outputs, and this run produced no RAG source/citation to inspect.

## Primary scenario — Ashwagandha + Shatavari formulation

This reuses the product facts from `tests/test_integration_slice.py::test_full_slice_ashwagandha_shatavari_example`, which verifies deterministic classification as `proprietary` and a direct route containing `patent_law` and `biodiversity_abs`. The frontend journey itself has not been end-to-end verified.

### Exact intake fields

1. Jurisdiction: `india` (jurisdiction selection screen).
2. Product name: `Ashwagandha+Shatavari Complex`.
3. Protection target: `formulation`.
4. Objectives: `patentability`.
5. Composition:
   - `Ashwagandha extract`, quantity `500`, unit `mg`, active `true`.
   - `Shatavari extract`, quantity `250`, unit `mg`, active `true`.
6. Intended use: `therapeutic`.
7. Classical basis: `partial`.
8. Novelty: `modified`.
9. Ingredient source: `plant` (explicit demo fact; the existing test fixture does not set this field).
10. Development status: `prototype`.
11. Biological origin: leave unanswered/unknown unless the presenter has a real, documented source fact. Do not infer it from the ingredient name.

### Expected state and presenter actions

- **Verified test boundary:** the integration test expects classification `proprietary` and routing regimes including `patent_law` and `biodiversity_abs` for the tested PIP. It does not verify the UI, ABS result, vector retrieval, or final answer for this profile.
- Show the classification screen, then query workspace. Open ABS and TKDL as separate tabs if the environment is prepared. In Ask & Explore, ask a narrow question supported by the ingested corpus, then open a citation chip to show the retrieved excerpt.
- Evidence/source to open: a citation detail returned from a real `/query` response. If no citation appears or retrieval is empty, stop and use the local-recorded fallback; do not fabricate a source.
- ABS source detail comes from `ABSAssessment` and the optional Chroma grounding call; the current ABS screen shows only selected summary fields. Do not claim every ABS citation is verified by the same `/query` verification pipeline.
- **Do not claim:** patentability, regulatory approval, ABS exemption/requirement, benefit-sharing amount, or that the product is safe/effective. The test only proves the named classification/routing assertions.

## Backup 1 — Missing/unknown origin

**Existing test:** `tests/test_abs_34_scenarios.py::test_scenario_04_unknown_origin` uses a plant source and `biological_origin_known="no"`; it asserts that the ABS assessment includes missing `biological_origin_region` information.

- **Input:** PIP product `ingredient_sources=["plant"]`, `biological_origin_known="no"`; do not provide `biological_origin_region`. Other product facts may be the primary scenario values.
- **Expected tested state:** missing-information entry for `biological_origin_region`. The test does not assert an exact final status label, so do not promise one.
- **Observed API behavior in the live local run:** ABS returned `CONDITIONAL`, listed `biological_origin_region` as missing, set `human_review=true`, and did **not** set `abstained=true`. Do not describe this as ABS abstention.
- **Show:** intake's origin answer and, if available, the ABS API response. The current ABS UI does not render the structured `missing_information` list, so this gap must be disclosed.
- **Evidence to open:** ABS response citations/reasoning if present; there may be no source-specific evidence for the missing product fact.
- **Do not claim:** that the product origin is India, foreign, or legally exempt.

## Backup 2 — Conflicting facts

- **Prepared input:** PIP reports `biological_origin_known="yes"` and region `India`; a separate ABS fact submission reports country of origin `Brazil` and marks the resource fact `CONFLICTING`.
- **Expected state:** desired behavior is `CONFLICTING` / human review, but **this cross-source conflict is not verified**. The current PIP-to-ABS adapter maps PIP origin facts into the ABS resource profile and may overwrite a conflicting ABS resource value. The current frontend also does not provide a separate ABS-facts editor.
- **Observed API behavior:** posting PIP origin `India` together with ABS origin `Brazil`/`CONFLICTING` returned `origin_status=india`, `country_of_origin=India`, `status=CONDITIONAL`, and `human_review=false`. This scenario **failed** the expected conflict-preservation behavior in the local API check.
- **Show:** only as a documented test case after the backend team verifies merge precedence and confirms the response. Until then, label this scenario **NEEDS TESTING — DO NOT LIVE DEMO AS A WORKING CONFLICT FLOW**.
- **Evidence to open:** the response's fact breakdown and status only after verified behavior exists.
- **Do not claim:** conflict preservation until the API test proves the conflict remains unresolved.

## Backup 3 — TKDL-focused formulation

**Existing test input:** the TKDL tests search the offline source-derived archive with composition `Mercury`, `Sulphur` and assert real records are returned. Use only as a database-match demo, not as a product recommendation.

- **Input:** product name `TKDL archive search demonstration`; composition `Mercury` and `Sulphur`; objective `prior_art`; protection target `formulation`. Set fields only as required by the UI. Do not add use, dosage, provenance, or safety claims.
- **Expected tested state:** the offline search returns matches to real record IDs. The results indicate ingredient overlap only; they do not decide patentability or medical suitability.
- **Show:** the TKDL Match tab, the record identifier/source fields, and overlap/matched ingredients if returned.
- **Evidence to open:** source text and record metadata exposed in the TKDL result. The frontend banner says the archive is offline and not the live TKDL service.
- **Do not claim:** live TKDL access, a patent rejection, a confirmed legal prior-art conclusion, or that Mercury/Sulphur is safe for use.

## Backup 4 — Human escalation / foreign-control case

**Existing tests:** ABS scenarios 07 and 34 use plant resource with known Indian origin and applicant `indian_company_with_foreign_control`; they assert human review is required.

- **Input:** `ingredient_sources=["plant"]`; `biological_origin_known="yes"`; `biological_origin_region="India"`; ABS `applicant.entity_category="indian_company_with_foreign_control"`.
- **Expected tested state:** `human_escalation.human_review == true` in the deterministic engine test. No conclusion is made about any particular real company's status.
- **Observed API behavior:** the structured ABS response returned `status=ESCALATION_RECOMMENDED`, `human_review=true`, and a Section 3(2) foreign-participation/control review reason for the synthetic input.
- **Show:** this scenario can be submitted through the ABS API with structured `abs_facts`, or reproduced in the test harness. The current frontend ABS request sends only a session ID and the current ABS screen does not display the structured escalation object; therefore it is not currently a complete UI demo.
- **Evidence to open:** ABS response `human_escalation` fields and related triggered-rule/source references when available.
- **Do not claim:** that an actual company is foreign-controlled or that a specific statutory filing is legally required without verified facts and expert review.

## Demo readiness checklist

- [ ] Choose host(s), configure the production API URL, and verify CORS for the frontend origin.
- [ ] Verify Python 3.11.9 deployment; current test evidence is Python 3.13.0. Frontend build now passes after `npm ci`.
- [ ] Ingest `legal-corpus/` into the deployed `./chroma_data` store and verify retrieval. On this Windows machine use `python -X utf8 scripts/ingest_corpus.py`; local ingestion created 23 chunks.
- [ ] Confirm only necessary API keys are configured, without showing them.
- [ ] Run `/health`, create a session, classify, perform a real `/query`, open citation details, then separately open ABS/TKDL.
- [ ] Verify missing-information and escalation presentation limitations are explained.
- [ ] Record a clean local browser walkthrough and keep it available offline.


## Current live-query caveat (2026-09-30)

The post-ingestion /query call returned HTTP 500 after Gemini responded 503, then 429 quota exceeded on one retry. The local UI journey was observed through intake only; do not promise a working generated-answer/citation demo unless the provider is confirmed healthy and a fresh query succeeds beforehand. Prepare a recording in advance. ABS, TKDL, classification, and corpus retrieval can be shown as separate flows; cross-source conflict behavior failed verification.

