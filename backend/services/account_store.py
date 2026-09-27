"""SQLite storage for prototype accounts, bearer tokens, and saved cases."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.models.pip import ProductIntelligenceProfile


def _db_path() -> str:
    return os.getenv("VEDAVERSE_DB_PATH", "./vedaverse_accounts.sqlite3")


@contextmanager
def _connect():
    path = _db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            phone TEXT,
            profession TEXT,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS auth_tokens (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS saved_cases (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            pip_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            case_status TEXT NOT NULL DEFAULT 'in_progress'
        );
        CREATE TABLE IF NOT EXISTS case_assessments (
            session_id TEXT NOT NULL REFERENCES saved_cases(session_id) ON DELETE CASCADE,
            assessment_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (session_id, assessment_type)
        );
        CREATE INDEX IF NOT EXISTS saved_cases_user_updated
            ON saved_cases(user_id, updated_at DESC);
        """
    )
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(saved_cases)").fetchall()}
    if "case_status" not in columns:
        # Older prototype databases did not distinguish active from completed
        # cases. Preserve the latest saved case as resumable; treat older rows
        # as history so they do not all appear as unfinished work.
        conn.execute("ALTER TABLE saved_cases ADD COLUMN case_status TEXT NOT NULL DEFAULT 'completed'")
        latest_by_user = conn.execute(
            "SELECT user_id, session_id FROM saved_cases "
            "WHERE (user_id, updated_at) IN (SELECT user_id, MAX(updated_at) FROM saved_cases GROUP BY user_id)"
        ).fetchall()
        for row in latest_by_user:
            conn.execute("UPDATE saved_cases SET case_status='in_progress' WHERE session_id=?", (row["session_id"],))
    if "stage" not in columns:
        conn.execute("ALTER TABLE saved_cases ADD COLUMN stage TEXT NOT NULL DEFAULT 'jurisdiction'")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _user_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"], "name": row["name"], "email": row["email"],
        "phone": row["phone"], "profession": row["profession"],
        "created_at": row["created_at"],
    }


def create_user(*, name: str, email: str, phone: str | None, profession: str | None, password: str) -> dict:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()
    created_at = datetime.now(timezone.utc).isoformat()
    user_id = secrets.token_urlsafe(18)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO users(id,name,email,phone,profession,password_salt,password_hash,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (user_id, name.strip(), email.strip().lower(), phone, profession, salt.hex(), password_hash, created_at),
        )
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return _user_dict(row)


def get_user_by_email(email: str) -> tuple[dict, str, str] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email=? COLLATE NOCASE", (email.strip(),)).fetchone()
    if row is None:
        return None
    return _user_dict(row), row["password_salt"], row["password_hash"]


def get_user(user_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return _user_dict(row) if row else None


def issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    with _connect() as conn:
        conn.execute("INSERT INTO auth_tokens(token_hash,user_id,expires_at) VALUES(?,?,?)",
                     (hashlib.sha256(token.encode()).hexdigest(), user_id, expires))
    return token


def get_user_for_token(token: str) -> dict | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with _connect() as conn:
        row = conn.execute(
            "SELECT users.* FROM auth_tokens JOIN users ON users.id=auth_tokens.user_id "
            "WHERE auth_tokens.token_hash=? AND auth_tokens.expires_at>?",
            (token_hash, datetime.now(timezone.utc).isoformat()),
        ).fetchone()
    return _user_dict(row) if row else None


def revoke_token(token: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM auth_tokens WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))


def save_account_case(user_id: str, pip: ProductIntelligenceProfile) -> None:
    payload = json.dumps(pip.model_dump(mode="json"), ensure_ascii=False)
    created_at = pip.created_at.isoformat()
    updated_at = pip.updated_at.isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO saved_cases(session_id,user_id,pip_json,created_at,updated_at,case_status,stage) VALUES(?,?,?,?,?,'in_progress','jurisdiction') "
            "ON CONFLICT(session_id) DO UPDATE SET pip_json=excluded.pip_json,updated_at=excluded.updated_at "
            "WHERE saved_cases.user_id=excluded.user_id",
            (pip.session_id, user_id, payload, created_at, updated_at),
        )


def get_saved_case(session_id: str) -> ProductIntelligenceProfile | None:
    with _connect() as conn:
        row = conn.execute("SELECT pip_json FROM saved_cases WHERE session_id=?", (session_id,)).fetchone()
    return ProductIntelligenceProfile.model_validate(json.loads(row["pip_json"])) if row else None


def get_case_owner(session_id: str) -> str | None:
    with _connect() as conn:
        row = conn.execute("SELECT user_id FROM saved_cases WHERE session_id=?", (session_id,)).fetchone()
    return row["user_id"] if row else None


def list_saved_cases(user_id: str) -> list[ProductIntelligenceProfile]:
    with _connect() as conn:
        rows = conn.execute("SELECT pip_json FROM saved_cases WHERE user_id=? AND case_status='completed' ORDER BY updated_at DESC", (user_id,)).fetchall()
    return [ProductIntelligenceProfile.model_validate(json.loads(row["pip_json"])) for row in rows]


def get_active_case(user_id: str) -> ProductIntelligenceProfile | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT pip_json FROM saved_cases WHERE user_id=? AND case_status='in_progress' ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return ProductIntelligenceProfile.model_validate(json.loads(row["pip_json"])) if row else None


def get_case_stage(user_id: str, session_id: str) -> str | None:
    with _connect() as conn:
        row = conn.execute("SELECT stage FROM saved_cases WHERE user_id=? AND session_id=? AND case_status='in_progress'", (user_id, session_id)).fetchone()
    return row["stage"] if row else None


def set_case_stage(user_id: str, session_id: str, stage: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute("UPDATE saved_cases SET stage=?,updated_at=? WHERE user_id=? AND session_id=? AND case_status='in_progress'", (stage, datetime.now(timezone.utc).isoformat(), user_id, session_id))
    return cursor.rowcount > 0


def discard_active_cases(user_id: str) -> list[str]:
    """Remove any unfinished case when the user explicitly starts another."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT session_id FROM saved_cases WHERE user_id=? AND case_status='in_progress'",
            (user_id,),
        ).fetchall()
        conn.execute("DELETE FROM saved_cases WHERE user_id=? AND case_status='in_progress'", (user_id,))
    return [row["session_id"] for row in rows]


def complete_account_case(user_id: str, session_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT pip_json FROM saved_cases WHERE user_id=? AND session_id=? AND case_status='in_progress'", (user_id, session_id)).fetchone()
        if row is None:
            return False
        payload = json.loads(row["pip_json"])
        if not (payload.get("product", {}).get("name") or "").strip():
            rows = conn.execute("SELECT pip_json FROM saved_cases WHERE user_id=?", (user_id,)).fetchall()
            used = set()
            for saved in rows:
                name = (json.loads(saved["pip_json"]).get("product", {}).get("name") or "").strip()
                match = re.fullmatch(r"Product (\d+)", name, re.IGNORECASE)
                if match:
                    used.add(int(match.group(1)))
            number = 1
            while number in used:
                number += 1
            payload.setdefault("product", {})["name"] = f"Product {number}"
        cursor = conn.execute(
            "UPDATE saved_cases SET pip_json=?,case_status='completed',stage='workspace',updated_at=? WHERE user_id=? AND session_id=?",
            (json.dumps(payload, ensure_ascii=False), datetime.now(timezone.utc).isoformat(), user_id, session_id),
        )
    return cursor.rowcount > 0


def save_account_assessment(session_id: str, assessment_type: str, payload: dict) -> None:
    with _connect() as conn:
        conn.execute("INSERT INTO case_assessments(session_id,assessment_type,payload_json,updated_at) VALUES(?,?,?,?) ON CONFLICT(session_id,assessment_type) DO UPDATE SET payload_json=excluded.payload_json,updated_at=excluded.updated_at", (session_id, assessment_type, json.dumps(payload, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))


def get_account_assessments(session_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT assessment_type,payload_json,updated_at FROM case_assessments WHERE session_id=? ORDER BY assessment_type", (session_id,)).fetchall()
    return [{"type": row["assessment_type"], "data": json.loads(row["payload_json"]), "updated_at": row["updated_at"]} for row in rows]


def delete_account_case(user_id: str, session_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM saved_cases WHERE user_id=? AND session_id=? AND case_status='completed'", (user_id, session_id))
    return cursor.rowcount > 0


def list_saved_case_ids(user_id: str) -> list[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT session_id FROM saved_cases WHERE user_id=? AND case_status='completed'", (user_id,)).fetchall()
    return [row["session_id"] for row in rows]
