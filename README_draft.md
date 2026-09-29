# VedaVerse / IP-SAKTI Sahayak

**Documentation draft — not yet a replacement for `README.md`.** This file reflects the repository inspected at `main` commit `6e3d0b4`. The action plan and team checklists named in the handoff prompt were not found in this checkout. Unknown deployment and product decisions are called out rather than assumed.

## 1. Project overview

VedaVerse is a prototype decision-support application for Ayurvedic and traditional-health product IP/regulatory exploration. It collects structured product facts, applies deterministic classification/routing logic, offers separate ABS and offline TKDL tools, and supports legal questions using a local legal corpus, Chroma retrieval, generated explanations, citation checks, and abstention behavior.

It is not a legal filing service or a substitute for qualified legal review. The repository does not establish a fully orchestrated end-to-end pipeline; the modules are connected through separate screens and API calls.

## 2. Architecture overview

```text
React + Vite intake
  → FastAPI session and intake endpoints
  → ProductIntelligenceProfile
  → deterministic classification
  → query route: routing → Chroma retrieval → answer generation
                           → citation overlap checks → confidence/abstention
  → separate ABS assessment and TKDL search endpoints/screens
```

Backend routes live in `backend/routes/`; deterministic rules in `backend/logic/`; RAG in `backend/rag/`; Chroma and SQLite services in `backend/services/` and `backend/db/`. The legal source files are under `legal-corpus/`; TKDL source-derived data is in `backend/data/`.

The ABS engine consumes PIP facts, but applicant/source/transfer details are not all collected by the current frontend intake. TKDL results remain in their own screen. Neither module is automatically combined with the final RAG answer.

## 3. Backend setup

Repository runtime target: Python 3.11.9 (`runtime.txt`). Verification on 2026-09-30 used Python 3.13.0; compatibility under 3.11.9 remains unverified.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally with the keys needed for the features being demonstrated. Do not commit real keys.

## 4. Frontend setup

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Vite prints the local URL. `VITE_API_BASE` defaults to `http://127.0.0.1:8000`. The frontend package defines `npm run build`; a production build passed on 2026-09-30 after `npm ci` (Vite 5.4.21; 78 modules).

## 5. Environment variables

| Variable | Used for | State |
|---|---|---|
| `GEMINI_API_KEY` | Legal answer generation (`/query`). | In `.env.example`; provide server-side. |
| `BHASHINI_INFERENCE_KEY` | Translation and speech API calls. | In `.env.example`; provide server-side for those features. |
| `BHASHINI_UDYAT_KEY` | Speech service identity/configuration. | In `.env.example`; provide server-side for speech. |
| `VEDAVERSE_DB_PATH` | Accounts/cases SQLite path; defaults to `./vedaverse_accounts.sqlite3`. | In `.env.example`; use persistent writable storage if data must persist. |
| `VITE_API_BASE` | Frontend API base URL; defaults to localhost in `frontend/src/api/client.js`. | In `frontend/.env.example`; set to the deployed backend origin before a production build. |

No deployed environment or production values are established by this repository.

## 6. Running the backend

From the repository root:

```powershell
uvicorn backend.main:app --reload --port 8000
```

Health: `http://127.0.0.1:8000/health` (expected JSON: `{"status":"ok"}`). Interactive API docs: `http://127.0.0.1:8000/docs`.

## 7. Running the frontend

In a second terminal:

```powershell
cd frontend
npm run dev
```

Use the URL printed by Vite. Ensure `VITE_API_BASE` points to the backend, normally `http://127.0.0.1:8000` locally.

## 8. Testing and verification

Run backend tests from the repository root:

```powershell
python -m pytest -q
```

Verified 2026-09-30 on Python 3.13.0: 260 passed, 1 failed. The failure was `tests/test_confidence.py::test_abstention_is_not_overridden_by_high_numeric_score` (expected confidence score 1.0, received 0.8). Separate runs passed ABS tests 16/16, ABS grounding 6/6, the 34-scenario ABS suite 34/34, and the PIP/classify/route plus app-wiring integration tests 2/2. The suite still needs to be run on the declared Python 3.11.9 runtime.

Frontend build command is `cd frontend; npm run build`. After `npm ci` from the lockfile, the production build passed with Vite 5.4.21 (78 modules). There is no frontend test script or TypeScript check script. Browser observation confirmed landing, jurisdiction, and intake screens; a full journey through classification and result tabs has not been verified.

`npm audit` against the installed lockfile reported one high and one moderate vulnerability, both in development/build dependencies (`vite` and transitive `esbuild`). The registry recommended a Vite 8 major upgrade. Review and plan that upgrade separately; no dependency versions were changed during verification.

## 9. API endpoints

Verified from route decorators registered by `backend/main.py`:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health response. |
| POST | `/session` | Create a PIP session. |
| POST | `/intake` | Update session product facts. |
| POST | `/classify` | Classify a session PIP. |
| POST | `/query` | Retrieve sources and generate a legal response. |
| GET | `/citation/{doc_id}/{section}?session_id=...` | Read cached citation details. |
| POST | `/abs/assess` | Run ABS assessment for a session. |
| POST | `/tkdl/search` | Search the offline source-derived TKDL archive. |
| GET | `/datasets/legal`, `/datasets/nba`, `/datasets/tkdl` | Search datasets. |
| POST | `/auth/signup`, `/auth/login`, `/auth/logout` | Account authentication. |
| GET | `/auth/me`, `/auth/cases`, `/auth/activity`, `/auth/active-case` | Account and case information. |
| GET | `/auth/cases/{session_id}`, `/auth/cases/{session_id}/details` | Saved case details. |
| PATCH | `/auth/cases/{session_id}/stage` | Update case stage. |
| POST | `/auth/cases/{session_id}/complete` | Complete a case. |
| DELETE | `/auth/cases/{session_id}` | Delete saved case history. |
| POST | `/voice/transcribe`, `/voice/tts`, `/voice/chat` | Voice services. |
| POST | `/bhashini/translate`, `/bhashini/translate_batch`, `/bhashini/in`, `/bhashini/out` | Bhashini translation routes. |

The exact contract should be checked at `/docs`; the UI calls PIP, ABS, TKDL, and RAG separately. There is no unified assessment endpoint in the inspected routes.

## 10. Deployment

Backend and frontend hosts are **UNKNOWN / TEAM DECISION REQUIRED**. There are no provider-specific deployment files. `chroma_data/` is ignored and generated locally; verification populated it with `python -X utf8 scripts/ingest_corpus.py` on Windows (23 chunks, 10 flagged oversized). Deploy by ingesting before demo traffic or providing a compatible persistent index. The host must keep that index on the path used by the backend (`./chroma_data`). SQLite persistence also depends on the selected host's disk. See `deployment_plan.md` for the detailed deployment and local fallback plan.

## 11. Known limitations

- Backend CORS currently allows all origins; the code says to tighten it before deployment.
- PIP sessions and citation cache use in-memory stores; anonymous sessions do not persist across backend restarts.
- Accounts/cases and query logs use local SQLite files; durable deployment storage is not configured.
- Chroma data is generated and not in Git; deployment ingestion is not automated.
- ABS and TKDL are separate analyses, not components of one final response. The ABS UI does not display all structured missing-information/escalation fields.
- Citation support uses lexical overlap heuristics and should not be described as proof of legal correctness.
- No export/share flow was found.
- Backend behavior on Python 3.11.9 and deployed cold starts need verification. The local build works after dependency installation, but the dependency audit reported Vite/esbuild advisories.

## 12. Demo assumptions

- Demo product facts are illustrative inputs, not legal conclusions or advice about manufacturing, safety, patentability, or compliance.
- Run corpus ingestion before showing legal RAG retrieval. Configure keys needed for the selected features.
- The synthetic Ashwagandha/Shatavari API journey passed through classification, ABS, and TKDL endpoints; the post-ingestion `/query` answer was not verified because Gemini returned 503 and then 429, surfaced as HTTP 500. This does not establish a complete browser journey.
- Show ABS, TKDL, and legal query as separate tools and describe their current boundaries honestly. Do not promise an integrated one-click report.
- Hosting provider, persistence, warm-up, and exact demo URL remain team decisions.



