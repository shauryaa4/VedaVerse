"""
API-01 — FastAPI project scaffold.

Deliberately minimal per the task's own scope: folder structure + health
check only. Session/intake/classify/query endpoints are separate tasks
(PIP-02/03, CLS-05, RAG-03) — don't build ahead of them here.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.query import router as query_router

app = FastAPI(title="IP-SAKTI Sahayak API", version="0.1.0")

# Wide-open CORS for local dev only. Tighten before any real deployment (API-05).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}