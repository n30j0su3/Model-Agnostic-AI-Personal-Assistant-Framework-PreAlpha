"""Shared hermetic fixtures for the PA Framework test suite."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def hermetic_env(tmp_path, monkeypatch):
    """Isolate user-level state without changing the process cwd."""
    home = tmp_path / "home"
    state_root = tmp_path / "repo-state"
    home.mkdir()
    state_root.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("PA_TEST_REPO_ROOT", str(state_root))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    yield


@pytest.fixture
def repo_extract(tmp_path):
    """Extract the current staged tree into a writable temporary directory."""
    destination = tmp_path / "repo-extract"
    destination.mkdir()
    in_git = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if in_git.returncode != 0:
        shutil.copytree(
            ROOT,
            destination,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns(
                ".git", ".pytest_cache", "__pycache__", "*.pyc", "data"
            ),
        )
        return destination

    tree = subprocess.run(
        ["git", "write-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    archive = subprocess.run(
        ["git", "archive", tree],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        bundle.extractall(destination)
    return destination
