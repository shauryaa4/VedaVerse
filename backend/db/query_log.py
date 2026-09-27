"""
API-04 — Query log.

Records every /query call: what was asked, what the routing/retrieval
produced, and what the final answer was. This exists for one reason: if the
demo gives a bad or surprising answer live, there needs to be a record to
debug from afterward, rather than trying to reconstruct what happened from
memory.

Deliberately simple (SQLite, one table, no ORM) — this is a debugging log,
not a product feature. Local file, no server to stand up, consistent with
VEC-01's same reasoning for choosing Chroma's local mode.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = "./query_log.sqlite3"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    session_id TEXT,
    question TEXT NOT NULL,
    jurisdiction TEXT,
    category TEXT,
    objectives TEXT,
    where_clause TEXT,
    used_chunk_ids TEXT,
    answer_text TEXT,
    abstained INTEGER NOT NULL,
    abstain_reason TEXT
);
"""


@contextmanager
def _connect(db_path: str = DEFAULT_DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_query(
    *,
    session_id: str | None,
    question: str,
    jurisdiction: str | None,
    category: str | None,
    objectives: list[str],
    where_clause: dict | None,
    used_chunk_ids: list[str],
    answer_text: str,
    abstained: bool,
    abstain_reason: str | None,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    """Writes one row per /query call. Never raises on its own — a logging
    failure must never take down the actual answer being returned to the
    user, so callers should wrap this in a try/except that just logs to
    stderr and moves on (see routes/query.py's usage)."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO query_log (
                timestamp, session_id, question, jurisdiction, category,
                objectives, where_clause, used_chunk_ids, answer_text,
                abstained, abstain_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                session_id,
                question,
                jurisdiction,
                category,
                json.dumps(objectives),
                json.dumps(where_clause) if where_clause else None,
                json.dumps(used_chunk_ids),
                answer_text,
                1 if abstained else 0,
                abstain_reason,
            ),
        )


def get_recent_queries(limit: int = 20, db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    """Convenience read for debugging after a demo — e.g. from a Python shell:
    `from backend.db.query_log import get_recent_queries; get_recent_queries()`"""
    with _connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM query_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def get_activity_for_sessions(session_ids: list[str], limit: int = 10, db_path: str = DEFAULT_DB_PATH) -> dict:
    """Return real aggregate counts and recent question metadata for saved cases."""
    if not session_ids:
        return {"question_count": 0, "abstained_count": 0, "recent": []}
    # Keep the IN clause below SQLite's parameter limit while covering many
    # sessions by querying chunks and combining their persisted rows.
    total_count = 0
    abstained_count = 0
    rows = []
    with _connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for start in range(0, len(session_ids), 400):
            batch = session_ids[start:start + 400]
            placeholders = ",".join("?" for _ in batch)
            counts = conn.execute(
                f"SELECT COUNT(*),COALESCE(SUM(abstained),0) FROM query_log WHERE session_id IN ({placeholders})",
                batch,
            ).fetchone()
            total_count += counts[0]
            abstained_count += counts[1]
            rows.extend(conn.execute(
                f"SELECT timestamp,session_id,question,jurisdiction,category,abstained "
                f"FROM query_log WHERE session_id IN ({placeholders}) ORDER BY id DESC LIMIT ?",
                (*batch, max(1, min(limit, 50))),
            ).fetchall())
    rows.sort(key=lambda row: row["timestamp"], reverse=True)
    return {
        "question_count": total_count,
        "abstained_count": abstained_count,
        "recent": [dict(row) for row in rows[:max(1, min(limit, 50))]],
    }


def get_queries_for_session(session_id: str, db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    with _connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM query_log WHERE session_id=? ORDER BY id", (session_id,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for key in ("objectives", "where_clause", "used_chunk_ids"):
            if item.get(key):
                try:
                    item[key] = json.loads(item[key])
                except (TypeError, json.JSONDecodeError):
                    pass
        item["abstained"] = bool(item["abstained"])
        result.append(item)
    return result


def delete_queries_for_session(session_id: str, db_path: str = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM query_log WHERE session_id=?", (session_id,))
