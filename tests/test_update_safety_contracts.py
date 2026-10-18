"""RC5 update safety and data-preservation contracts."""
from __future__ import annotations

import builtins
import hashlib
import importlib.util
import inspect
import json
import stat
import sys
import zipfile

import pytest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixed_tempdir(path: Path):
    class FixedTempdir:
        def __enter__(self):
            path.mkdir(parents=True, exist_ok=True)
            return str(path)

        def __exit__(self, exc_type, exc, tb):
            return False

    return FixedTempdir()


def test_root_sqlite_files_are_update_protected(monkeypatch):
    update = load_module("update_rc5_registry", SCRIPTS / "update.py")
    protected_file = ROOT / "config" / "update-protected-paths.txt"
    protected = protected_file.read_text(encoding="utf-8").splitlines()
    assert "data/sessions.db" in protected
    assert "data/user_memory.db" in protected

    monkeypatch.setattr(update, "UPDATE_PROTECTED_PATHS_FILE", Path("/missing"))
    defaults = update.load_update_protected_paths()
    assert "data/sessions.db" in defaults
    assert "data/user_memory.db" in defaults


def test_overlay_preserves_root_sqlite_hashes(tmp_path):
    update = load_module("update_rc5_copy", SCRIPTS / "update.py")
    source = tmp_path / "source"
    target = tmp_path / "target"
    for root, sessions, memory in (
        (source, b"replacement-sessions", b"replacement-memory"),
        (target, b"user-sessions", b"user-memory"),
    ):
        (root / "data").mkdir(parents=True)
        (root / "data/sessions.db").write_bytes(sessions)
        (root / "data/user_memory.db").write_bytes(memory)
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (target / "data/sessions.db", target / "data/user_memory.db")
    }

    update.copy_tree(
        source,
        target,
        protected_paths=["data/sessions.db", "data/user_memory.db"],
    )

    after = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (target / "data/sessions.db", target / "data/user_memory.db")
    }
    assert after == before


def test_create_snapshot_produces_rollback_manifest(tmp_path, monkeypatch):
    update = load_module("update_rc5_snapshot", SCRIPTS / "update.py")
    root = tmp_path / "repo"
    (root / "core/.context").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "config/settings.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(update, "REPO_ROOT", root)
    monkeypatch.setattr(update, "CORE_DIR", root / "core")

    snapshot = update.create_snapshot()

    assert isinstance(snapshot, Path)
    assert snapshot.is_dir()
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == 1
    assert isinstance(manifest["roots"], list)


def test_kb_init_uses_canonical_script(tmp_path, monkeypatch):
    update = load_module("update_rc5_kb", SCRIPTS / "update.py")
    root = tmp_path / "repo"
    script = root / "core/scripts/kb_init.py"
    script.parent.mkdir(parents=True)
    script.write_text("# fixture\n", encoding="utf-8")
    calls = []
    monkeypatch.setattr(update, "REPO_ROOT", root)
    monkeypatch.setattr(update, "CORE_DIR", root / "core")
    monkeypatch.setattr(
        update.subprocess,
        "run",
        lambda command, **kwargs: calls.append(command) or SimpleNamespace(returncode=0),
    )

    assert update.run_kb_init() is True
    assert calls == [[sys.executable, str(script), "--force"]]


def test_kb_init_missing_is_not_success(tmp_path, monkeypatch):
    update = load_module("update_rc5_kb_missing", SCRIPTS / "update.py")
    root = tmp_path / "repo"
    monkeypatch.setattr(update, "REPO_ROOT", root)
    monkeypatch.setattr(update, "CORE_DIR", root / "core")
    assert update.run_kb_init() is False


def test_migration_runner_missing_is_not_success(tmp_path, monkeypatch):
    update = load_module("update_rc5_migrate_missing", SCRIPTS / "update.py")
    root = tmp_path / "repo"
    monkeypatch.setattr(update, "REPO_ROOT", root)
    monkeypatch.setattr(update, "CORE_DIR", root / "core")
    assert update.run_migrations() is False


def test_force_update_still_fails_closed_without_snapshot(tmp_path, monkeypatch):
    update = load_module("update_rc5_force_snapshot", SCRIPTS / "update.py")
    backup_calls = []
    monkeypatch.setattr(update, "REPO_ROOT", tmp_path / "repo")
    monkeypatch.setattr(update, "detect_repo_url", lambda: update.DEFAULT_REPO)
    monkeypatch.setattr(
        update,
        "read_local_version",
        lambda: update.parse_version("v0.4.1-beta"),
    )
    monkeypatch.setattr(
        update,
        "fetch_remote_version_via_git",
        lambda: update.parse_version("v0.4.1-beta"),
    )
    monkeypatch.setattr(update, "create_snapshot", lambda: None)
    monkeypatch.setattr(update, "load_update_protected_paths", lambda: [])
    monkeypatch.setattr(
        update,
        "backup_protected_update_paths",
        lambda _paths: backup_calls.append(True) or tmp_path / "backup",
    )
    monkeypatch.setattr(update, "update_with_zip", lambda *_args: False)

    assert update.run_update(force=True) == update.STATUS_ERROR
    assert backup_calls == []


def test_update_zip_rejects_parent_traversal(tmp_path, monkeypatch):
    update = load_module("update_rc5_traversal", SCRIPTS / "update.py")
    target = tmp_path / "target"
    target.mkdir()
    staging = tmp_path / "staging"
    escaped = tmp_path / "escape.txt"
    monkeypatch.setattr(update, "REPO_ROOT", target)
    monkeypatch.setattr(
        update.tempfile,
        "TemporaryDirectory",
        lambda: _fixed_tempdir(staging),
    )

    def malicious_download(_url, zip_path):
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("repo/file.txt", "safe")
            archive.writestr("../escape.txt", "escaped")
        return True

    monkeypatch.setattr(update, "try_requests_download", malicious_download)

    assert update.update_with_zip("https://example.invalid/update.zip", []) is False
    assert not escaped.exists()
    assert not (target / "file.txt").exists()


@pytest.mark.usefixtures("require_symlinks")
def test_update_zip_rejects_symlink_member(tmp_path, monkeypatch):
    update = load_module("update_rc5_symlink", SCRIPTS / "update.py")
    target = tmp_path / "target"
    target.mkdir()
    staging = tmp_path / "staging"
    monkeypatch.setattr(update, "REPO_ROOT", target)
    monkeypatch.setattr(
        update.tempfile,
        "TemporaryDirectory",
        lambda: _fixed_tempdir(staging),
    )

    def symlink_download(_url, zip_path):
        link = zipfile.ZipInfo("repo/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("repo/file.txt", "safe")
            archive.writestr(link, "../outside")
        return True

    monkeypatch.setattr(update, "try_requests_download", symlink_download)

    assert update.update_with_zip("https://example.invalid/update.zip", []) is False
    assert not (target / "link").exists()


def test_update_zip_rejects_multiple_roots(tmp_path, monkeypatch):
    update = load_module("update_rc5_roots", SCRIPTS / "update.py")
    target = tmp_path / "target"
    target.mkdir()
    staging = tmp_path / "staging"
    monkeypatch.setattr(update, "REPO_ROOT", target)
    monkeypatch.setattr(
        update.tempfile,
        "TemporaryDirectory",
        lambda: _fixed_tempdir(staging),
    )

    def multi_root_download(_url, zip_path):
        with zipfile.ZipFile(zip_path, "w") as archive:
            archive.writestr("repo-a/file.txt", "a")
            archive.writestr("repo-b/file.txt", "b")
        return True

    monkeypatch.setattr(update, "try_requests_download", multi_root_download)

    assert update.update_with_zip("https://example.invalid/update.zip", []) is False
    assert not (target / "file.txt").exists()


def test_download_failure_aborts_without_prompt_or_tls_bypass(monkeypatch):
    update = load_module("update_rc5_download_abort", SCRIPTS / "update.py")
    urllib_calls = []
    prompted = []
    monkeypatch.setattr(update, "try_requests_download", lambda *_args, **_kwargs: False)

    def failed_urllib(*args, **kwargs):
        urllib_calls.append((args, kwargs))
        return False

    monkeypatch.setattr(update, "try_urllib_download", failed_urllib)
    monkeypatch.setattr(
        builtins,
        "input",
        lambda _message: prompted.append(True) or "c",
    )

    assert update.update_with_zip("https://example.invalid/update.zip", []) is False
    assert len(urllib_calls) == 1
    assert urllib_calls[0][1].get("verify_ssl", True) is not False
    assert prompted == []


def test_updater_source_has_no_tls_bypass_or_auto_pip():
    source = (SCRIPTS / "update.py").read_text(encoding="utf-8")
    assert "CERT_NONE" not in source
    assert "verify_ssl=False" not in source
    assert "pip\", \"install\"" not in source
    assert "def install_certifi" not in source


def test_dead_optional_update_hooks_are_removed():
    update = load_module("update_rc5_dead_hooks", SCRIPTS / "update.py")
    assert not hasattr(update, "run_vendor_assets")
    assert not hasattr(update, "run_docs_manifest")
    source = inspect.getsource(update.run_update)
    assert "run_vendor_assets" not in source
    assert "run_docs_manifest" not in source


def test_successful_migration_receipt_tracks_framework_version(tmp_path, monkeypatch):
    migrate = load_module("migrate_rc5_receipt", SCRIPTS / "migrate.py")
    root = tmp_path / "repo"
    state_file = root / "core/.context/.migration_state.json"
    version_file = root / "VERSION"
    state_file.parent.mkdir(parents=True)
    state_file.write_text(
        json.dumps({
            "framework_version": "v0.4.0-beta",
            "migrations_applied": [],
            "last_migration": None,
            "migrations_log": [],
        }),
        encoding="utf-8",
    )
    version_file.write_text("v0.4.1-beta\n", encoding="utf-8")
    monkeypatch.setattr(migrate, "REPO_ROOT", root)
    monkeypatch.setattr(migrate, "MIGRATION_STATE_FILE", state_file)
    monkeypatch.setattr(migrate, "VERSION_FILE", version_file)
    monkeypatch.setattr(
        migrate,
        "MIGRATIONS",
        {"v0.4.1": {"name": "receipt", "description": "receipt truth"}},
    )

    assert migrate.apply_migration("v0.4.1") is True
    receipt = json.loads(state_file.read_text(encoding="utf-8"))
    assert receipt["framework_version"] == "v0.4.1-beta"
