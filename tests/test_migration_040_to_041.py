"""Round-trip migration contract from the public v0.4.0 baseline."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def extract_archive(ref: str, destination: Path) -> None:
    archive = destination.parent / f"{ref.replace('/', '-')}.tar"
    with archive.open("wb") as handle:
        subprocess.run(
            ["git", "archive", ref],
            cwd=ROOT,
            stdout=handle,
            check=True,
        )
    with tarfile.open(archive) as bundle:
        bundle.extractall(destination, filter="data")


def make_candidate_from_040(tmp_path: Path) -> Path:
    root = tmp_path / "candidate"
    root.mkdir()
    extract_archive("v0.4.0-beta", root)
    tree = subprocess.run(
        ["git", "write-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    extract_archive(tree, root)
    return root


def hash_tree(root: Path) -> dict[str, str]:
    ignored_parts = {"__pycache__", ".pytest_cache"}
    result = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parts[:2] == ("data", "backups"):
            continue
        if ignored_parts.intersection(relative.parts) or path.suffix == ".pyc":
            continue
        result[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def run(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    home = root.parent / "home"
    home.mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=root,
        env={
            **os.environ,
            "HOME": str(home),
            "USERPROFILE": str(home),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        text=True,
        timeout=180,
    )


def snapshot_from_output(root: Path, output: str) -> Path:
    line = next(line for line in output.splitlines() if line.startswith("SNAPSHOT_DIR="))
    return root / line.partition("=")[2]


def test_migrate_full_roundtrip_is_idempotent(tmp_path):
    root = make_candidate_from_040(tmp_path)
    assert (root / "core/scripts/rollback.py").is_file()
    session = root / "core/.context/sessions/current.json"
    memory = root / "core/.context/memory/user-note.md"
    session.parent.mkdir(parents=True, exist_ok=True)
    memory.parent.mkdir(parents=True, exist_ok=True)
    session.write_text("USER_SESSION_KEEP", encoding="utf-8")
    memory.write_text("USER_MEMORY_KEEP", encoding="utf-8")
    before = hash_tree(root)

    first = run(root, "core/scripts/migrate.py", "--apply")
    assert first.returncode == 0, first.stdout + first.stderr
    snapshot = snapshot_from_output(root, first.stdout)
    assert (snapshot / "manifest.json").is_file()
    snapshots_before = sorted((root / "data/backups").glob("pre-migration-*"))

    second = run(root, "core/scripts/migrate.py", "--apply")
    assert second.returncode == 0, second.stdout + second.stderr
    assert "APPLIED=[]" in second.stdout
    assert sorted((root / "data/backups").glob("pre-migration-*")) == snapshots_before

    rollback = run(
        root,
        "core/scripts/rollback.py",
        "--snapshot",
        str(snapshot),
        "--json",
    )
    assert rollback.returncode == 0, rollback.stdout + rollback.stderr
    receipt = json.loads(rollback.stdout)
    assert receipt["ok"] is True
    assert hash_tree(root) == before
    assert session.read_text(encoding="utf-8") == "USER_SESSION_KEEP"
    assert memory.read_text(encoding="utf-8") == "USER_MEMORY_KEEP"


def test_migration_script_propagates_nonzero_exit(monkeypatch):
    path = ROOT / "core/scripts/migrate.py"
    spec = importlib.util.spec_from_file_location("migrate_exit_test", path)
    assert spec is not None and spec.loader is not None
    migrate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migrate)

    monkeypatch.setattr(
        migrate.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 7, "", "boom"),
    )

    assert migrate.run_migration_script("kb_init.py") is False
