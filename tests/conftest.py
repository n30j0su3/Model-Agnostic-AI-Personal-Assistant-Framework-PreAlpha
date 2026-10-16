"""Shared hermetic fixtures for the PA Framework test suite."""

from __future__ import annotations

import io
import os
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
    """Extract tracked HEAD into a writable temporary tree."""
    destination = tmp_path / "repo-extract"
    destination.mkdir()
    archive = subprocess.run(
        ["git", "archive", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        bundle.extractall(destination)
    return destination
