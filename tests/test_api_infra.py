"""
Tests for API-03 (error middleware) and API-04 (query log).
"""

import os
import tempfile

from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.query_log import get_recent_queries, log_query

client = TestClient(app)


# --- API-03: global error handler ---

def test_health_check_unaffected_by_error_handler():
    """Sanity check: adding a global exception handler must not break the
    normal, no-error path."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_expected_http_exceptions_still_return_their_own_status_code():
    """HTTPException (e.g. 404 unknown session) must NOT be swallowed by the
    global handler and turned into a generic 500 -- only genuinely unexpected
    exceptions should hit that path."""
    resp = client.post("/classify", json={"session_id": "does-not-exist"})
    assert resp.status_code == 404
    assert "Unknown session_id" in resp.json()["detail"]


def test_unhandled_exception_returns_clean_json_not_a_traceback():
    """Directly exercises the exception_handler by adding a throwaway route
    that always raises a plain (non-HTTPException) error.

    Uses raise_server_exceptions=False: TestClient's default behavior is to
    re-raise server-side exceptions in the test process (useful for most
    tests, since it surfaces real bugs immediately) -- but that bypasses the
    exception_handler entirely, which is exactly the thing this test needs
    to exercise."""
    @app.get("/__test_only_raises")
    def _raises():
        raise ValueError("boom")

    no_raise_client = TestClient(app, raise_server_exceptions=False)
    resp = no_raise_client.get("/__test_only_raises")
    assert resp.status_code == 500
    body = resp.json()
    assert body["error_type"] == "ValueError"
    assert "detail" in body
    # Must NOT leak the raw exception message or a stack trace to the client.
    assert "boom" not in str(body)


# --- API-04: query log ---

def test_log_query_writes_a_row_that_can_be_read_back():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test_query_log.sqlite3")

        log_query(
            session_id="sess-123",
            question="Can I patent this?",
            jurisdiction="india",
            category="classical_generic",
            objectives=["patentability"],
            where_clause={"jurisdiction": "india"},
            used_chunk_ids=["IN-1:3(p)"],
            answer_text="No, per 3(p).",
            abstained=False,
            abstain_reason=None,
            db_path=db_path,
        )

        rows = get_recent_queries(db_path=db_path)
        assert len(rows) == 1
        assert rows[0]["question"] == "Can I patent this?"
        assert rows[0]["session_id"] == "sess-123"
        assert rows[0]["abstained"] == 0


def test_log_query_handles_abstained_query():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test_query_log.sqlite3")

        log_query(
            session_id=None,
            question="unanswerable question",
            jurisdiction="india",
            category=None,
            objectives=[],
            where_clause=None,
            used_chunk_ids=[],
            answer_text="",
            abstained=True,
            abstain_reason="No relevant chunks found.",
            db_path=db_path,
        )

        rows = get_recent_queries(db_path=db_path)
        assert rows[0]["abstained"] == 1
        assert rows[0]["abstain_reason"] == "No relevant chunks found."


def test_get_recent_queries_respects_limit_and_order():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test_query_log.sqlite3")

        for i in range(5):
            log_query(
                session_id=None, question=f"question {i}", jurisdiction="india",
                category=None, objectives=[], where_clause=None,
                used_chunk_ids=[], answer_text="", abstained=False,
                abstain_reason=None, db_path=db_path,
            )

        rows = get_recent_queries(limit=2, db_path=db_path)
        assert len(rows) == 2
        # Most recent first.
        assert rows[0]["question"] == "question 4"
        assert rows[1]["question"] == "question 3"