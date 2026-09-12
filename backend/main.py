"""
Folder structure + health check, wired to the session/intake/classify/query
routers implemented in backend/routes/. All routers are thin — the real
logic lives in backend/logic, backend/rag, and backend/services.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.routes.query import router as query_router
from backend.routes.citation import router as citation_router
from backend.routes.session import router as session_router
from backend.routes.intake import router as intake_router
from backend.routes.classify import router as classify_router

app = FastAPI(title="IP-SAKTI Sahayak API", version="0.1.0")

# Wide-open CORS for local dev only. Tighten before any real deployment (API-05).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)
app.include_router(citation_router)
app.include_router(session_router)
app.include_router(intake_router)
app.include_router(classify_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}