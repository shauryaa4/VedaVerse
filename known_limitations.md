# VedaVerse known limitations

**Scope:** findings from the repository at `main` commit `6e3d0b4` and local verification during this documentation pass. This is not a production security review.

## Verified limitations

- **Broad CORS:** `backend/main.py` allows all origins, methods, and headers. Its comment says to tighten this before real deployment.
- **Host/deployment configuration:** no provider-specific backend/frontend deployment configuration is present. Hosts, URLs, process settings, and plan are not established.
- **Python mismatch:** `runtime.txt` specifies Python 3.11.9; the available interpreter and earlier test run used Python 3.13.0. Runtime parity is unverified.
- **Test failure:** last full suite run on Python 3.13.0 had 260 passed and one failed confidence assertion (`test_abstention_is_not_overridden_by_high_numeric_score`: expected `1.0`, got `0.8`). Dedicated ABS scenario cases passed in that run. Verify again on Python 3.11.9.
- **Frontend dependency audit:** after installing from `package-lock.json`, `npm run build` passed on 2026-09-30 (Vite 5.4.21). `npm audit` reported one high and one moderate advisory in dev/build dependencies (`vite` and transitive `esbuild`) and recommends a Vite 8 major upgrade. No dependency changes were made.
- **Split pipeline:** classification, query/RAG, ABS, and TKDL are separate frontend/API calls. No single router orchestrates them into one answer.
- **ABS UI coverage:** backend returns structured missing-information, citation, benefit-sharing, form, and escalation fields, but `ABSHelper` renders only a subset. The current UI does not show all decision evidence or escalation details. API checks confirmed missing-information data can be returned; it was not displayed in the UI.
- **Conflict merge:** a tested cross-source PIP-versus-ABS origin conflict is not established. The PIP adapter maps origin facts into ABS facts; a local API check showed the PIP adapter overwrote a conflicting ABS origin (India retained over Brazil; status CONDITIONAL, human_review false). Treat conflict handling as a defect to resolve before claiming conflict safety.
- **TKDL scope:** current tool uses an offline source-derived archive, not the live TKDL system. Matches are overlap signals, not legal conclusions.
- **Citation support:** `/query` uses keyword/lexical overlap heuristics for sentence-to-chunk support. It is not semantic/legal correctness review. ABS grounding is a separate optional pass and uses a separate assessment structure.
- **Landing-page claim:** the landing page says every claim traces to an actual statute/rule/treaty. The verified runtime uses lexical overlap against retrieved chunks; do not present this as proof that every legal claim is correct.
- **No export/share:** no structured assessment export or sharing endpoint/UI was found.
- **PIP session persistence:** PIP sessions are stored in process memory; anonymous sessions are lost on backend restart. Authenticated cases can be reloaded from the account SQLite store.
- **SQLite:** account/case data use `VEDAVERSE_DB_PATH` (default `./vedaverse_accounts.sqlite3`); query logs default to `./query_log.sqlite3`. No deployment volume or backup policy is configured.
- **Vector store:** `chroma_data/` is ignored and not tracked. Ingestion must populate a local persistent Chroma index, but no deployment ingestion job or data volume is configured.
- **Health endpoint scope:** `/health` confirms only that the API returns a response; it does not check keys, corpus, Chroma retrieval, or Bhashini/Gemini connectivity.
- **Cold start:** free-tier behavior cannot be stated without a selected provider/plan. If the provider sleeps or uses ephemeral storage, wake-up and data-loss behavior must be tested.

## Pending team decision

- Select backend and frontend hosts, demo URLs, and deployment owner.
- Confirm Python 3.11.9 as the release runtime and make dependency versions reproducible.
- Decide whether the demo requires Gemini, Bhashini translation, Bhashini speech, or only a subset; provide secrets through host secret storage.
- Decide how `chroma_data/` is populated and persisted (prebuilt compatible index vs. ingestion job), and who verifies it.
- Decide whether accounts/query logs must persist beyond a demo session and configure a persistent volume/backup or explicitly accept resets.
- Confirm CORS allowlist and allowed origins before exposing the API.
- Decide how to handle the existing confidence-test failure before calling verification complete.
- Confirm whether the project requires export/share for the demo or can clearly state it is not implemented.
- Locate `vedaverse_my_action_plan`, final project checklist, and backend checklist; they were not found in this checkout.

## Needs testing

- Full backend test suite on Python 3.11.9. The latest Python 3.13 run was 260 passed, 1 failed.
- Decide whether and when to update Vite/esbuild to address the npm audit findings; the suggested Vite 8 upgrade is a major-version change and was not applied during verification.
- Fresh deployment startup, health check, Chroma retrieval, real query, citation detail, and selected language/speech features.
- Persistence across process restart and host redeploy for both SQLite files and Chroma; confirm anonymous session loss is acceptable.
- Cross-source conflict handling, missing-information UI, and structured escalation display.
- Browser-to-backend calls against the selected production CORS/API configuration.
- Free-tier cold start and fallback recording on the actual demo network/device.


## Latest end-to-end provider limitation (2026-09-30)

After corpus ingestion, a real local /query request reached Gemini but received HTTP 503 (high demand) and on a single retry HTTP 429 (free-tier quota exhausted); the API surfaced HTTP 500 both times. No generated answer, citation display, or end-to-end answer abstention was therefore verified. Do not keep retrying this key during the demo; use the documented non-LLM screens or a recording made when service is available.

