from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def _load(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migrate = _load("migrate_determinism_test", SCRIPTS / "migrate.py")
session_start = _load("session_start_determinism_test", SCRIPTS / "session_start.py")
wiki = _load("wiki_autopopulate_determinism_test", SCRIPTS / "wiki_autopopulate.py")


def test_migration_check_warns_but_succeeds_for_missing_structures(monkeypatch, capsys):
    monkeypatch.setattr(migrate, "get_pending_migrations", lambda: [])
    monkeypatch.setattr(
        migrate,
        "detect_missing_structures",
        lambda: {"v0.2.0": ["core/.context/projects/"]},
    )
    monkeypatch.setattr(
        migrate,
        "load_migration_state",
        lambda: {"migrations_applied": list(migrate.MIGRATIONS)},
    )

    result = migrate.check_migrations()
    output = capsys.readouterr().out

    assert result == 0
    assert "[WARN]" in output
    assert "Estructuras faltantes" in output
    assert "Ejecuta: python core/scripts/migrate.py --apply" not in output


def test_session_start_migration_check_uses_exit_code_not_output_text(monkeypatch):
    calls = []

    def fake_run(argv, **kwargs):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="all migrations applied", stderr="")

    monkeypatch.setattr(session_start.subprocess, "run", fake_run)

    session_start.check_pending_migrations()

    assert len(calls) == 1
    assert "--check" in calls[0]


def _wiki_dirs(tmp_path: Path, monkeypatch):
    mapping = {
        "WIKI_BASE": tmp_path / "wiki",
        "WIKI_ENTITIES": tmp_path / "wiki/entities",
        "WIKI_CONCEPTS": tmp_path / "wiki/concepts",
        "WIKI_COMPARISONS": tmp_path / "wiki/comparisons",
        "WIKI_QUERIES": tmp_path / "wiki/queries",
        "WIKI_RAW": tmp_path / "wiki/raw",
    }
    for name, path in mapping.items():
        monkeypatch.setattr(wiki, name, path)
        path.mkdir(parents=True, exist_ok=True)
    return mapping


def test_wiki_save_is_idempotent_for_identical_content(tmp_path, monkeypatch):
    dirs = _wiki_dirs(tmp_path, monkeypatch)
    entry = {
        "type": "concept",
        "title": "Pattern: Error",
        "content": "---\ntitle: Pattern: Error\n---\nSame body\n",
    }

    first = wiki.save_wiki_entry(entry)
    second = wiki.save_wiki_entry(entry)

    assert first == second
    assert first is not None
    assert first.read_text(encoding="utf-8") == entry["content"]
    assert list(dirs["WIKI_CONCEPTS"].glob("*.md")) == [first]


def test_wiki_save_updates_same_slug_instead_of_creating_suffix(tmp_path, monkeypatch):
    dirs = _wiki_dirs(tmp_path, monkeypatch)
    original = {
        "type": "concept",
        "title": "Pattern: Error",
        "content": "---\ntitle: Pattern: Error\n---\nOld body\n",
    }
    updated = {**original, "content": "---\ntitle: Pattern: Error\n---\nNew body\n"}

    first = wiki.save_wiki_entry(original)
    second = wiki.save_wiki_entry(updated)

    assert first == second
    assert first is not None
    assert first.read_text(encoding="utf-8") == updated["content"]
    assert list(dirs["WIKI_CONCEPTS"].glob("*.md")) == [first]


def test_wiki_save_preserves_distinct_titles_with_same_sanitized_slug(
    tmp_path, monkeypatch
):
    dirs = _wiki_dirs(tmp_path, monkeypatch)
    first_entry = {
        "type": "concept",
        "title": "A/B",
        "content": "---\ntitle: A/B\n---\nFirst\n",
    }
    collision = {
        "type": "concept",
        "title": "A:B",
        "content": "---\ntitle: A:B\n---\nSecond\n",
    }

    first = wiki.save_wiki_entry(first_entry)
    second = wiki.save_wiki_entry(collision)

    assert first is not None and second is not None
    assert first != second
    assert first.read_text(encoding="utf-8") == first_entry["content"]
    assert second.read_text(encoding="utf-8") == collision["content"]
    assert len(list(dirs["WIKI_CONCEPTS"].glob("*.md"))) == 2
