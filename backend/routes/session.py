"""
NEW FILE — POST /session.

Per API contract (build spec §13): "POST /session → create session, returns
session_id." Implemented here by creating a fresh, empty
ProductIntelligenceProfile (PIP-01) and returning it in full — session_id
is a field on that object, and returning the whole (empty-but-shaped) PIP
lets the frontend see the exact contract it will be filling in via
/intake, rather than inventing a second, narrower response shape.

Deliberately thin, same spirit as routes/citation.py and routes/query.py:
all state lives in backend/services/pip_session_store.py, this file only
turns the HTTP call into a store call and back.
"""

from fastapi import APIRouter

from backend.models.pip import ProductIntelligenceProfile
from backend.services.pip_session_store import create_session

router = APIRouter()


@router.post("/session", response_model=ProductIntelligenceProfile)
def create_session_endpoint() -> ProductIntelligenceProfile:
    return create_session()
