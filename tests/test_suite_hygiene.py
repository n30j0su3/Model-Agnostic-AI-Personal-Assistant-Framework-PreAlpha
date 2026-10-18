"""Hermetic full-suite gate: subprocess tests must not mutate the checkout."""

from __future__ import annotations

import os
import hashlib
import subprocess
import sys
from pathlib import Path

from conftest import copy_source_sandbox, subprocess_text_encoding


ROOT = Path(__file__).resolve().parents[1]
SESSIONS_INDEX = ROOT / "core/.context/knowledge/sessions-index.json"


def _sessions_index_bytes():
    """RC6: runtime state is untracked+ignored; guard only what exists."""
    if SESSIONS_INDEX.exists():
        return SESSIONS_INDEX.read_bytes()
    return None


def checkout_state():
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding=subprocess_text_encoding(),
        errors="replace",
    )
    if status.returncode == 0:
        return ("git", status.stdout.strip())

    excluded_parts = {".pytest_cache", "__pycache__", "data"}
    snapshot = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or excluded_parts.intersection(path.relative_to(ROOT).parts):
            continue
        if path.suffix == ".pyc":
            continue
        snapshot[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return ("snapshot", snapshot)


def test_full_suite_green_and_does_not_mutate_checkout(tmp_path):
    before_status = checkout_state()
    before_index = _sessions_index_bytes()
    sandbox = copy_source_sandbox(tmp_path / "sandbox")
    home = tmp_path / "nested-home"
    home.mkdir()
    nested_state = tmp_path / "nested-state"
    nested_state.mkdir()
    nested_data = nested_state / "data"
    nested_data.mkdir()
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(home),
        "PA_FRAMEWORK_DATA": str(nested_data),
        "PA_TEST_REPO_ROOT": str(nested_state),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
            "--ignore=tests/test_suite_hygiene.py",
        ],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        encoding=subprocess_text_encoding(),
        errors="replace",
        timeout=600,
    )
    after_status = checkout_state()
    after_index = _sessions_index_bytes()

    assert result.returncode == 0, (result.stdout + result.stderr)[-4000:]
    assert after_index == before_index, "suite mutated tracked sessions-index.json"
    assert after_status == before_status, (
        f"suite changed checkout state\nbefore={before_status!r}\nafter={after_status!r}"
    )
