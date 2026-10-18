"""W7.4 contract: storage discovery reports capability without creating SQLite."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def _load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "persistent_storage_discover_w74", SCRIPTS / "persistent_storage_discover.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_absent_db_is_available_when_parent_is_writable(tmp_path):
    module = _load()
    db_path = tmp_path / "data" / "sessions.db"
    db_path.parent.mkdir()

    result = module.check_sqlite(db_path)

    assert result["exists"] is False
    assert result["available"] is True
    assert result["tables"] == []
    assert not db_path.exists(), "discovery must not create the database"


def test_absent_db_is_unavailable_when_parent_is_not_writable(tmp_path, monkeypatch):
    module = _load()
    db_path = tmp_path / "data" / "sessions.db"
    db_path.parent.mkdir()
    real_access = os.access

    def fake_access(path, mode):
        if Path(path) == db_path.parent and mode == os.W_OK:
            return False
        return real_access(path, mode)

    monkeypatch.setattr(module.os, "access", fake_access)

    result = module.check_sqlite(db_path)

    assert result["available"] is False
    assert "not writable" in result.get("error", "")
    assert not db_path.exists()


def test_corrupt_existing_db_is_unavailable(tmp_path):
    module = _load()
    db_path = tmp_path / "data" / "sessions.db"
    db_path.parent.mkdir()
    db_path.write_bytes(b"this is not a sqlite database")

    result = module.check_sqlite(db_path)

    assert result["exists"] is True
    assert result["available"] is False
    assert result.get("error")
