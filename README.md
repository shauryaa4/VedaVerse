# IP-SAKTI Sahayak

Ayurveda IP/regulatory classification + citation-grounded RAG assistant.
See `legal-corpus/README.md` for corpus structure specifically.

## Running the backend

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run the API:
```bash
uvicorn backend.main:app --reload
```
Then check `http://127.0.0.1:8000/health` — should return `{"status": "ok"}`.
Interactive API docs (auto-generated once real endpoints exist): `http://127.0.0.1:8000/docs`.

Run tests:
```bash
# Mac/Linux
PYTHONPATH=. pytest tests/ -v

# Windows PowerShell
$env:PYTHONPATH = "."
python -m pytest tests/ -v
```

## Backend structure

```
backend/
  main.py       # FastAPI app + health check (API-01)
  routes/       # HTTP endpoints (empty scaffold — populated as PIP-02/03, CLS-05, RAG-03 land)
  logic/        # deterministic rule engines — classification.py (CLS-01), routing.py (ROUTE-01)
  models/       # data models — pip.py (PIP-01), classification_input.py
  db/           # DB schema/migrations (empty scaffold — API-02)
  services/     # external service wrappers, e.g. vector store (empty scaffold — VEC-01)
tests/
```

## Status

- ✅ CLS-01 — classification decision tree
- ✅ ROUTE-01 — routing engine
- ✅ PIP-01 — Product Intelligence Profile model
- ✅ API-01 — FastAPI scaffold + health check
- ⬜ Everything else — see `EXECUTION-BOARD.md`
