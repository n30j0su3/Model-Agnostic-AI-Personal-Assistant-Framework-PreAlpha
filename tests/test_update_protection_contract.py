"""W1 contracts: update-protected paths are add-only, parity-checked, and never
overwritten by migrations.

Reference of truth for the protected set is config/update-protected-paths.txt.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

ACTIVE = ROOT / "config" / "update-protected-paths.txt"
SEED = ROOT / "config" / "update-protected-paths.txt.seed"
MANDATORY_DATA = ("data/user", "data/sessions.db", "data/user_memory.db")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _entries(text: str) -> list[str]:
    return [
        line.strip().rstrip("/")
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _active_set() -> set[str]:
    return set(_entries(ACTIVE.read_text(encoding="utf-8")))


@pytest.fixture
def update():
    return _load("update_w1_contract", SCRIPTS / "update.py")


def test_truncated_protected_file_keeps_every_active_default(tmp_path, update, monkeypatch):
    """A user file that lists only extra paths must not drop mandatory defaults."""
    trimmed = tmp_path / "update-protected-paths.txt"
    trimmed.write_text("workspaces\n", encoding="utf-8")
    monkeypatch.setattr(update, "UPDATE_PROTECTED_PATHS_FILE", trimmed)

    result = set(update.load_update_protected_paths())

    assert _active_set() <= result
    for path in MANDATORY_DATA:
        assert path in result


def test_missing_protected_file_uses_full_canonical_defaults(update, monkeypatch):
    monkeypatch.setattr(update, "UPDATE_PROTECTED_PATHS_FILE", Path("/nonexistent/paths.txt"))

    result = set(update.load_update_protected_paths())

    assert result == _active_set()


def test_comment_only_file_falls_back_to_full_defaults(tmp_path, update, monkeypatch):
    commented = tmp_path / "update-protected-paths.txt"
    commented.write_text("# nothing here\n\n", encoding="utf-8")
    monkeypatch.setattr(update, "UPDATE_PROTECTED_PATHS_FILE", commented)

    assert _active_set() <= set(update.load_update_protected_paths())


def test_user_extension_is_added_without_duplicates(tmp_path, update, monkeypatch):
    extended = tmp_path / "update-protected-paths.txt"
    extended.write_text("custom/keep/\nworkspaces\ncustom/keep\n", encoding="utf-8")
    monkeypatch.setattr(update, "UPDATE_PROTECTED_PATHS_FILE", extended)

    result = update.load_update_protected_paths()

    assert "custom/keep" in result
    assert len(result) == len(set(result))
    assert _active_set() <= set(result)


def test_seed_matches_active_protected_set():
    """migrate.py recreates the active file from the seed when it is missing."""
    assert set(_entries(SEED.read_text(encoding="utf-8"))) == _active_set()


def test_regenerated_file_from_seed_keeps_mandatory_data_protection(tmp_path, update, monkeypatch):
    regenerated = tmp_path / "update-protected-paths.txt"
    shutil.copyfile(SEED, regenerated)
    monkeypatch.setattr(update, "UPDATE_PROTECTED_PATHS_FILE", regenerated)

    result = set(update.load_update_protected_paths())

    for path in MANDATORY_DATA:
        assert path in result


def test_migration_never_overwrites_existing_user_files(tmp_path, monkeypatch):
    """apply_migration must create missing files only; existing user state is sacred."""
    migrate = _load("migrate_w1_contract", SCRIPTS / "migrate.py")
    monkeypatch.setattr(migrate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(migrate, "MIGRATION_STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(migrate, "run_migration_script", lambda name: True)

    config = tmp_path / "config"
    config.mkdir()
    shutil.copyfile(SEED, config / "update-protected-paths.txt.seed")
    user_paths = config / "update-protected-paths.txt"
    user_paths.write_text("workspaces\ncustom/keep/\n", encoding="utf-8")

    backlog = tmp_path / "core" / ".context" / "codebase" / "backlog.md"
    backlog.parent.mkdir(parents=True)
    backlog.write_text("# my real backlog\n", encoding="utf-8")

    assert migrate.apply_migration("v0.2.1") is True

    assert user_paths.read_text(encoding="utf-8") == "workspaces\ncustom/keep/\n"
    assert backlog.read_text(encoding="utf-8") == "# my real backlog\n"
