"""Prototype account endpoints backed by the local SQLite account store."""

from __future__ import annotations

import hashlib
import hmac
import re
import sqlite3

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from backend.services.account_store import (
    complete_account_case, create_user, delete_account_case, get_account_assessments, get_active_case, get_case_owner, get_case_stage, get_saved_case, get_user_by_email, list_saved_case_ids,
    get_user_for_token, issue_token, list_saved_cases, revoke_token,
    set_case_stage,
)
from backend.db.query_log import delete_queries_for_session, get_activity_for_sessions, get_queries_for_session

router = APIRouter(prefix="/auth", tags=["Accounts"])


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=256)


class SignupRequest(Credentials):
    name: str = Field(min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    profession: str | None = Field(default=None, max_length=120)


class AccountResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None = None
    profession: str | None = None
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AccountResponse


def optional_current_user(authorization: str | None = Header(default=None)) -> dict | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return get_user_for_token(token)


def require_current_user(user: dict | None = Depends(optional_current_user)) -> dict:
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in to access this account.")
    return user


def ensure_session_access(session_id: str, user: dict | None) -> None:
    if not isinstance(user, dict):
        user = None
    owner_id = get_case_owner(session_id)
    if owner_id and (user is None or owner_id != user["id"]):
        raise HTTPException(status_code=404, detail="Session not found.")


def _validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if len(normalized) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    return normalized


def _auth_response(user: dict) -> AuthResponse:
    return AuthResponse(access_token=issue_token(user["id"]), user=AccountResponse(**user))


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(body: SignupRequest):
    email = _validate_email(body.email)
    if not body.name.strip():
        raise HTTPException(status_code=422, detail="Name cannot be blank.")
    try:
        user = create_user(name=body.name, email=email, phone=body.phone, profession=body.profession, password=body.password)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(body: Credentials):
    email = _validate_email(body.email)
    record = get_user_by_email(email)
    if record is None:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    user, salt_hex, expected_hash = record
    actual_hash = hashlib.scrypt(body.password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1).hex()
    if not hmac.compare_digest(actual_hash, expected_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    return _auth_response(user)


@router.get("/me", response_model=AccountResponse)
def me(user: dict = Depends(require_current_user)):
    return user


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), user: dict = Depends(require_current_user)):
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() == "bearer" and token:
        revoke_token(token)
    return {"status": "ok"}


@router.get("/cases")
def saved_cases(user: dict = Depends(require_current_user)):
    cases = list_saved_cases(user["id"])
    return [
        {
            "session_id": case.session_id,
            "product_name": case.product.name,
            "jurisdiction": case.jurisdiction,
            "category": case.classification.category,
            "updated_at": case.updated_at,
            "created_at": case.created_at,
            "has_product_details": bool(case.product.name or case.product.composition),
        }
        for case in cases
    ]


@router.get("/activity")
def account_activity(user: dict = Depends(require_current_user)):
    return get_activity_for_sessions(list_saved_case_ids(user["id"]))


@router.get("/active-case")
def active_case(user: dict = Depends(require_current_user)):
    case = get_active_case(user["id"])
    if case is None:
        return None
    return {
        "session_id": case.session_id,
        "product_name": case.product.name,
        "jurisdiction": case.jurisdiction,
        "category": case.classification.category,
        "updated_at": case.updated_at,
        "created_at": case.created_at,
        "has_product_details": bool(case.product.name or case.product.composition),
        "stage": get_case_stage(user["id"], case.session_id) or "jurisdiction",
    }


class CaseStageRequest(BaseModel):
    stage: str = Field(pattern="^(jurisdiction|questionnaire|classification|workspace)$")


@router.patch("/cases/{session_id}/stage")
def update_case_stage(session_id: str, body: CaseStageRequest, user: dict = Depends(require_current_user)):
    if not set_case_stage(user["id"], session_id, body.stage):
        raise HTTPException(status_code=404, detail="Active case not found.")
    return {"status": "saved", "stage": body.stage}


@router.post("/cases/{session_id}/complete")
def complete_case(session_id: str, user: dict = Depends(require_current_user)):
    if not complete_account_case(user["id"], session_id):
        raise HTTPException(status_code=404, detail="Active case not found.")
    return {"status": "completed", "session_id": session_id}


@router.get("/cases/{session_id}")
def saved_case(session_id: str, user: dict = Depends(require_current_user)):
    if get_case_owner(session_id) != user["id"]:
        raise HTTPException(status_code=404, detail="Saved case not found.")
    case = get_saved_case(session_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Saved case not found.")
    return case


@router.get("/cases/{session_id}/details")
def saved_case_details(session_id: str, user: dict = Depends(require_current_user)):
    if get_case_owner(session_id) != user["id"]:
        raise HTTPException(status_code=404, detail="Saved case not found.")
    case = get_saved_case(session_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Saved case not found.")
    return {"profile": case.model_dump(mode="json"), "queries": get_queries_for_session(session_id), "assessments": get_account_assessments(session_id)}


@router.delete("/cases/{session_id}", status_code=204)
def delete_case_history(session_id: str, user: dict = Depends(require_current_user)):
    if not delete_account_case(user["id"], session_id):
        raise HTTPException(status_code=404, detail="Completed case not found.")
    delete_queries_for_session(session_id)
