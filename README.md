# IP-SAKTI Sahayak (VedaVerse)

IP-SAKTI Sahayak is a prototype that helps users organize information about an Ayurvedic product, see an initial IP classification, and explore related legal, access-and-benefit-sharing (ABS), and traditional-knowledge (TKDL) information. It is an information tool, not legal advice.

## Run locally

Use Python 3.11 or newer and Node.js with npm. Open two terminals from the repository folder.

### 1. Start the backend

Create and activate a virtual environment, then install the Python dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add a working `GEMINI_API_KEY` for legal question answering. Other integrations such as Bhashini need their own credentials and are optional for the basic English demo. Never commit `.env` or paste its keys into chat or project files.

Start the API from the repository root:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Confirm it is running at <http://127.0.0.1:8000/health>; the response should be `{"status":"ok"}`. The interactive API reference is at <http://127.0.0.1:8000/docs>.

### 2. Start the frontend

In the second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally <http://localhost:5173/>. The frontend uses `http://127.0.0.1:8000` by default. To use another backend URL, set `VITE_API_BASE` in `frontend/.env.local` before starting Vite; restart Vite after changing it.

## Suggested demo flow

Use fictional product details; do not enter real customer, patient, or business-confidential information.

1. Start a new assessment and choose **India**.
2. Enter a fictional product such as **Ashwagandha + Shatavari Complex**. Use a modified or new combination, a therapeutic intended use, and clearly mark any unknown facts as unknown.
3. Show the classification and its reasons. Explain that it is an initial screening result, not a legal conclusion.
4. In Ask & Explore, show a legal question with the retrieved source citations when the legal-answer service is available. The service calls Gemini; a quota or credentials problem prevents this part from returning an answer.
5. If relevant to the fictional ingredients and origin, show ABS and TKDL as separate checks. Describe their findings as screening signals that need human review.
6. Show an uncertain or incomplete-information case and point out where the app flags missing details or recommends review.

The demo can show deterministic classification and the separate ABS/TKDL screens without making a successful Gemini response look guaranteed. Do not claim that the system grants protection, verifies every law, or replaces an IP professional.

## Checks before sharing the project

Run from the repository root:

```powershell
$env:PYTHONPATH = "."
python -m pytest tests/ -v
```

Build the frontend:

```powershell
cd frontend
npm run build
```

The repository ignores local environment files, keys, SQLite databases, Chroma data, dependency folders, build output, and test artifacts. Before making a submission or commit, check `git status` and make sure no `.env` file, real credentials, or personal test data is included. `.env.example` contains placeholders only.

## Project map

- `frontend/` — React/Vite application.
- `backend/main.py` and `backend/routes/` — FastAPI application and API endpoints.
- `backend/logic/` and `backend/models/` — deterministic classification, routing, assessment logic, and data models.
- `backend/rag/` — legal-corpus retrieval, citation checks, confidence, and Gemini answer generation.
- `legal-corpus/` — curated legal source material and corpus notes; review source status notes before presenting legal claims.
- `tests/` — offline and integration-slice checks. The suite does not validate live provider credentials, quota, or deployed hosting configuration.
