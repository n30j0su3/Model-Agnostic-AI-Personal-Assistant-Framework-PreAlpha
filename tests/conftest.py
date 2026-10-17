"""Shared hermetic fixtures for the PA Framework test suite."""

from __future__ import annotations

import io
import locale
import os
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _sandbox_ignore(directory: str, names: list[str]) -> set[str]:
    """Ignore root runtime data without dropping nested skill assets."""
    ignored = set(
        shutil.ignore_patterns(
            ".git", ".pytest_cache", "__pycache__", "*.pyc"
        )(directory, names)
    )
    if Path(directory).resolve() == ROOT.resolve() and "data" in names:
        ignored.add("data")
    return ignored


def subprocess_text_encoding() -> str:
    """Decode captured child output with the encoding requested for that child."""
    requested = os.environ.get("PYTHONIOENCODING", "").partition(":")[0]
    return requested or locale.getpreferredencoding(False)


def assert_private_file(path: Path, *, platform: str | None = None) -> None:
    """Assert POSIX mode locally; native Windows ACL has a separate gate."""
    assert path.is_file()
    if (platform or os.name) == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


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
    git_executable = shutil.which("git")
    if git_executable is None:
        shutil.copytree(
            ROOT,
            destination,
            dirs_exist_ok=True,
            ignore=_sandbox_ignore,
        )
        return destination
    in_git = subprocess.run(
        [git_executable, "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding=subprocess_text_encoding(),
    )
    if in_git.returncode != 0:
        shutil.copytree(
            ROOT,
            destination,
            dirs_exist_ok=True,
            ignore=_sandbox_ignore,
        )
        return destination

    tree = subprocess.run(
        [git_executable, "write-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding=subprocess_text_encoding(),
        check=True,
    ).stdout.strip()
    archive = subprocess.run(
        [git_executable, "archive", tree],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        bundle.extractall(destination)
    return destination
