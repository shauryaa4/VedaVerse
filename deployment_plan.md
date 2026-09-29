# VedaVerse deployment plan

**Status:** planning draft. No hosting provider, deployed environment, or production data store is configured in this repository. Items marked **UNKNOWN / TEAM DECISION REQUIRED** must be decided before deployment.

`vedaverse_my_action_plan`, the final project checklist, and the backend checklist were not found in this repository checkout. Confirm whether they live elsewhere and reconcile this draft against them before treating it as the team's final plan.

## Current repository facts

| Area | Verified state |
|---|---|
| Backend runtime | `runtime.txt` specifies `python-3.11.9`. `requirements.txt` lists packages without version pins. This machine's `python --version` reports 3.13.0; the earlier full test run used Python 3.13.0. |
| Backend command | README documents `uvicorn backend.main:app --reload`; frontend client documentation also gives `uvicorn backend.main:app --reload --port 8000`. Use port 8000 for local frontend connectivity. |
| Health check | `GET /health`; local URL `http://127.0.0.1:8000/health`. |
| Frontend | Vite + React. `frontend/package.json` defines `npm run dev`, `npm run build`, and `npm run preview`. `vite.config.js` has no deployment-specific configuration. |
| Frontend API URL | `VITE_API_BASE` is read at build/runtime from Vite env and defaults in `frontend/src/api/client.js` to `http://127.0.0.1:8000`. A production build must set it to the deployed API origin before building. |
| Hosts / deploy config | No host is established by a deployment config in this repo. **UNKNOWN / TEAM DECISION REQUIRED** for backend and frontend hosts. |

## Backend deployment

- **Chosen host:** **UNKNOWN / TEAM DECISION REQUIRED.** No Render, Railway, Fly.io, Heroku, or other service configuration was found.
- **Python:** repository target is Python 3.11.9. Confirm with the backend team that this is the deployment version and run the suite under 3.11.9. The actual test evidence is from Python 3.13.0, so compatibility on the declared runtime is not yet verified.
- **Start command:** `uvicorn backend.main:app --host 0.0.0.0 --port 8000` is the expected production form of the repository's Uvicorn command. Host binding and command must be checked against the selected provider's process model before launch. The documented local command remains `uvicorn backend.main:app --reload`.
- **Health check:** configure the provider to check `GET /health` at the deployed API origin plus `/health`. This route only reports process health; it does not verify Chroma data, credentials, or external APIs.
- **Backend environment variables:**

| Variable | Repository use | Deployment note |
|---|---|---|
| `GEMINI_API_KEY` | Used by legal answer generation in `backend/rag/generation.py`. | Needed for LLM-backed `/query` answers. Store as a backend secret. |
| `BHASHINI_INFERENCE_KEY` | Used by translation and speech services. | Needed for the corresponding language/speech features; confirm which are in the demo scope. |
| `BHASHINI_UDYAT_KEY` | Used by `backend/logic/speech.py`. | Needed for speech features; keep backend-side. |
| `VEDAVERSE_DB_PATH` | Selects the accounts/cases SQLite file; default is `./vedaverse_accounts.sqlite3`. | Set to a writable path on persistent storage if account data must survive instance replacement. |

The repo's `.env.example` contains placeholders, not deployment values. Do not put secrets in frontend build variables, documentation, or Git.

## Frontend deployment

- **Chosen host:** **UNKNOWN / TEAM DECISION REQUIRED.** No static hosting config was found.
- **Build command:** from `frontend/`, `npm run build` (defined in `frontend/package.json`). On 2026-09-30, after `npm ci` from the lockfile, Vite 5.4.21 built successfully. `npm audit` reported one high and one moderate advisory in dev/build dependencies (`vite` and transitive `esbuild`); review the Vite 8 major upgrade recommendation before public exposure.
- **API origin:** set `VITE_API_BASE` to the HTTPS origin of the deployed backend before building. It is a frontend build-time setting in `frontend/src/api/client.js`; the current fallback points to localhost and is not suitable for a deployed frontend.
- The API currently allows all CORS origins in `backend/main.py`, with a code comment that this is local-development-only and should be tightened before deployment. Configure an explicit frontend origin before a public demo.

## Vector store and corpus

- `chroma_data/` is ignored by `.gitignore`, is not tracked by Git, and was absent from the checkout when inspected. It is generated locally by Chroma; it is not committed application data. During verification, Windows ingestion required `python -X utf8 scripts/ingest_corpus.py`; it completed with 23 chunks, 10 flagged oversized.
- The legal Markdown corpus under `legal-corpus/` is in the repository. The ingestion script is `python scripts/ingest_corpus.py` from the repository root. It chunks the corpus and upserts it into the `legal_corpus` collection in a persistent Chroma client under `./chroma_data`.
- The API opens that same relative path in `backend/routes/query.py` and `backend/services/vector_store.py`. There is no configured environment variable for the Chroma path.
- A fresh deployment therefore needs an ingestion step or a provided compatible vector-store volume. The repository does not define a deployment ingestion job or provide a prebuilt Chroma volume. After local ingestion, the retrieval script returned relevant corpus records; the real `/query` generation could not be confirmed because Gemini returned 503 then 429 and the API returned HTTP 500. **UNKNOWN / TEAM DECISION REQUIRED:** decide how the provider will receive or generate the index.
- Recommended timing: run ingestion after dependencies and corpus are available, before serving demo traffic, and store the generated index on the same durable filesystem path used by the backend. Do not run ingestion on every application start without measuring startup time and ensuring idempotent operational behavior.
- Confirm Chroma's embedding-model initialization requirements, network access, and disk size in the selected deployment environment. These are not established by a host configuration here.

## SQLite and persistence

| File | Purpose and creation | Git status / restart behavior |
|---|---|---|
| `vedaverse_accounts.sqlite3` | Accounts, auth tokens, saved cases, and assessments; default path from `backend/services/account_store.py`, override with `VEDAVERSE_DB_PATH`. The store creates parent directories and SQLite tables on connection. | Ignored by `.gitignore`; not tracked. It was not present in the inspected checkout. A fresh instance starts without account data and creates the DB when the store is used. It survives process restart only if the file remains on the same filesystem. |
| `query_log.sqlite3` | Query activity log; `backend/db/query_log.py` uses `./query_log.sqlite3` by default. | Ignored by `.gitignore`; present locally but not tracked. Its path is not configured through `VEDAVERSE_DB_PATH`. The code creates the table on a DB connection/write. |

Whether either database survives redeploys depends on the selected host's disk semantics, which are **UNKNOWN / TEAM DECISION REQUIRED**. If the host uses ephemeral storage, assume these files can be lost on instance replacement until persistent storage is configured and tested. Anonymous PIP sessions and citation cache are in memory and do not survive backend process restart.

## Cold starts and demo readiness

The repository does not identify a provider or plan, so free-tier sleep behavior and exact cold-start times are **UNKNOWN / TEAM DECISION REQUIRED**. If the chosen plan sleeps or scales to zero, allow for a slow first request. Before presenting:

1. Start the frontend and backend on the target deployment and check `/health`.
2. Confirm the deployed Chroma collection has been ingested and can return a source chunk.
3. Confirm required backend secrets are configured without displaying them.
4. Make one low-risk query and verify citations, translation if in scope, and the frontend connection.
5. Keep a local fallback and a screen recording ready (see `demo_plan.md`).

## Local fallback procedure

From the repository root, with Python 3.11.9 selected:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `.env` locally with the appropriate keys; never commit it. `VEDAVERSE_DB_PATH` may use the example default. Start the backend in one terminal:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Check `http://127.0.0.1:8000/health` returns `{"status":"ok"}`. If the Chroma index is absent, run this once from the repo root before a legal-RAG demo:

```powershell
python scripts/ingest_corpus.py
```

In a second terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

The Vite terminal prints the actual frontend URL. `VITE_API_BASE` defaults to `http://127.0.0.1:8000`; verify the health check and then create a session in the frontend. If it cannot reach the API, verify the backend is listening on port 8000 and `VITE_API_BASE` matches it. `npm ci` is the standard lockfile-based installation step; a clean install/build has not yet been verified in this checkout.

## Demo recording fallback

Record one clean browser session showing: product intake, deterministic classification, the separate ABS and TKDL tabs, one grounded legal query, opening a citation detail, and the visible abstention/uncertainty state if it occurs. Avoid entering secrets or personal account information. Do not narrate ABS/TKDL screens as an integrated final legal determination; the current UI presents them as separate tools.

