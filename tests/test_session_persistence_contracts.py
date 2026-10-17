"""Contract tests for SQLite session persistence and its CLI bridge."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from core.memory.session_memory import SessionStore
from core.scripts import session_bridge


def test_session_store_metadata_and_search_round_trip(tmp_path: Path):
    store = SessionStore(tmp_path / "sessions.db")
    try:
        session = store.get_or_create("synthetic-user", session_id="stable-session")
        created_at = session.created_at
        assert store.update_metadata(
            session.session_id,
            updates={"project_alpha": "/synthetic/project", "status": "active"},
        )
        store.add_message(session.session_id, "user", "needle contract message")

        resumed = store.get_or_create("synthetic-user", session_id="stable-session")
        assert resumed.created_at == created_at
        assert resumed.metadata == {
            "project_alpha": "/synthetic/project",
            "status": "active",
        }
        assert [item["content"] for item in store.search("needle")] == [
            "needle contract message"
        ]
        metadata_hits = store.search("synthetic/project")
        assert metadata_hits == [
            {
                "session_id": "stable-session",
                "type": "metadata",
                "key": "project_alpha",
                "value": "/synthetic/project",
            }
        ]
        with pytest.raises(ValueError, match="different user"):
            store.get_or_create("other-user", session_id="stable-session")
        still_owned = store.get_session("stable-session")
        assert still_owned is not None
        assert still_owned.user_id == "synthetic-user"
    finally:
        store.close()


def test_session_bridge_persists_real_id_metadata_and_close(tmp_path: Path, monkeypatch):
    store = SessionStore(tmp_path / "bridge.db")
    monkeypatch.setattr(session_bridge, "get_default_store", lambda: store)
    monkeypatch.setattr(session_bridge, "USER_MEMORY_AVAILABLE", False)
    monkeypatch.setattr(session_bridge.SessionBridge, "_log_event", lambda *args: None)
    monkeypatch.setattr(
        session_bridge.SessionBridge, "_update_project_registry", lambda *args: None
    )

    bridge = session_bridge.SessionBridge()
    try:
        session_id = bridge.start_session(
            user_input="initial contract message",
            metadata={"source": "contract-test"},
        )
        assert session_id == bridge.current_session
        persisted = store.get_session(session_id)
        assert persisted is not None
        assert persisted.metadata["source"] == "contract-test"
        assert persisted.metadata["init_type"] in {"cold", "warm"}

        assert bridge.register_project("Alpha", "/synthetic/alpha")
        registered = store.get_session(session_id)
        assert registered is not None
        assert registered.metadata["project_alpha"] == "/synthetic/alpha"

        assert bridge.end_session("closed by contract")
        closed = store.get_session(session_id)
        assert closed is not None
        assert closed.metadata["status"] == "closed"
        assert closed.metadata["end_time"]
        assert bridge.current_session is None
        assert any(
            hit.get("content") == "SESSION_SUMMARY: closed by contract"
            for hit in store.search("closed by contract")
        )
    finally:
        store.close()


def test_repair_removes_old_empty_and_orphan_rows(tmp_path: Path):
    store = SessionStore(tmp_path / "repair.db")
    try:
        store._conn.execute(
            "INSERT INTO sessions (session_id, user_id, created_at, last_activity, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            ("old-empty", "synthetic-user", 0.0, 0.0, "{}"),
        )
        store._conn.execute(
            "INSERT INTO session_messages "
            "(session_id, role, content, channel, timestamp, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("missing-session", "user", "orphan", "cli", time.time(), "{}"),
        )
        store._conn.commit()

        report = store.repair()

        assert report == {
            "fixed_orphans": 1,
            "fixed_empty": 1,
            "vacuumed": True,
            "errors": [],
        }
        assert store._conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE session_id = 'old-empty'"
        ).fetchone()[0] == 0
        assert store._conn.execute(
            "SELECT COUNT(*) FROM session_messages WHERE session_id = 'missing-session'"
        ).fetchone()[0] == 0
    finally:
        store.close()


def test_repair_reports_database_errors_instead_of_swallowing(tmp_path: Path):
    store = SessionStore(tmp_path / "closed.db")
    store.close()

    report = store.repair()

    assert report["vacuumed"] is False
    assert report["errors"]
    assert "closed database" in report["errors"][0].lower()
