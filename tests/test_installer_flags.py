"""Installer flags must support automation without hidden writes or prompts."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import subprocess_text_encoding


def file_hashes(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            relative = str(path.relative_to(root))
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def run_installer(root: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    home = root.parent / "installer-home"
    home.mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, "core/scripts/install.py", *flags],
        cwd=root,
        env={
            **os.environ,
            "HOME": str(home),
            "USERPROFILE": str(home),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding=subprocess_text_encoding(),
        timeout=180,
    )


def test_non_interactive_dry_run_json_has_zero_writes(repo_extract):
    before = file_hashes(repo_extract)

    result = run_installer(
        repo_extract,
        "--no-browser",
        "--non-interactive",
        "--dry-run",
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["mode"] == "dry-run"
    assert receipt["version"] == "0.4.1-beta"
    assert receipt["writes"] == []
    assert file_hashes(repo_extract) == before
    assert not (repo_extract / "data").exists()
    assert not (repo_extract / "workspaces").exists()


def test_non_interactive_json_install_never_prompts(repo_extract):
    result = run_installer(
        repo_extract,
        "--no-browser",
        "--non-interactive",
        "--json",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["mode"] == "installed"
    assert receipt["default_cli"] == "opencode"
    assert receipt["version"] == "0.4.1-beta"
    assert (repo_extract / "core/.context/profile.md").is_file()
    assert (repo_extract / "workspaces/content/projects").is_dir()


def test_help_is_side_effect_free(repo_extract):
    before = file_hashes(repo_extract)

    result = run_installer(repo_extract, "--help")

    assert result.returncode == 0
    assert "--non-interactive" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--json" in result.stdout
    assert file_hashes(repo_extract) == before
