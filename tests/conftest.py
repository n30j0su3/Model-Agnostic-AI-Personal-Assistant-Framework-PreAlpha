"""Shared hermetic fixtures for the PA Framework test suite."""

from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

# Runtime state that must never be present in a source tree used for tests.
# A clean release package contains none of these paths.
RUNTIME_RESIDUE = (
    "data",
    "core/.context/knowledge/errors",
    "core/.context/codebase/ideas.md",
    "core/.context/codebase/backlog.md",
    "core/.context/.cache",
    "workspaces",
)


def find_runtime_residue(root: Path) -> list[str]:
    """Return residue paths present under root (empty list means clean)."""
    return [rel for rel in RUNTIME_RESIDUE if (root / rel).exists()]


# Residue present before any test runs means the input package is contaminated.
# Residue created later by the suite itself is a hygiene defect, handled by the
# sandboxed nested-suite test, and must not break unrelated tests in the session.
_SESSION_START_RESIDUE = find_runtime_residue(ROOT)


def symlinks_supported(directory: Path) -> bool:
    """Probe whether this host can create symlinks, leaving no files behind."""
    target = directory / ".symlink-probe-target"
    link = directory / ".symlink-probe-link"
    target.write_text("probe", encoding="utf-8")
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        return False
    finally:
        link.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
    return True


def _sandbox_ignore(directory: str, names: list[str]) -> set[str]:
    """Ignore VCS and bytecode noise only; runtime residue is handled fail-closed."""
    return set(
        shutil.ignore_patterns(
            ".git", ".pytest_cache", "__pycache__", "*.pyc"
        )(directory, names)
    )


def _residue_ignore(directory: str, names: list[str]) -> set[str]:
    """Ignore VCS/bytecode noise plus runtime residue at its exact location.

    Mirrors ``git archive`` semantics for VCS-less packages: runtime state that
    a ``.git`` checkout would leave untracked must never reach a test sandbox.
    Nested directories that merely share a name (e.g. a skill's own ``data/``)
    are intentionally preserved.
    """
    ignored = _sandbox_ignore(directory, names)
    base = Path(directory).resolve()
    for rel in RUNTIME_RESIDUE:
        absolute = ROOT / rel
        if absolute.parent.resolve() == base and absolute.name in names:
            ignored.add(absolute.name)
    return ignored


def _copy_source_without_git(destination: Path) -> Path:
    if _SESSION_START_RESIDUE:
        pytest.fail(
            "source tree is not a clean package; runtime residue present at session start: "
            + ", ".join(_SESSION_START_RESIDUE)
            + ". Re-extract a clean candidate before running the suite."
        )
    shutil.copytree(ROOT, destination, dirs_exist_ok=True, ignore=_residue_ignore)
    return destination


def copy_source_sandbox(destination: Path) -> Path:
    """Copy the source tree without VCS, caches or runtime residue (for nested runs)."""
    shutil.copytree(ROOT, destination, dirs_exist_ok=True, ignore=_residue_ignore)
    return destination


@pytest.fixture
def require_symlinks(tmp_path):
    """Skip only when the host cannot create symlinks; security lanes must run elsewhere."""
    if not symlinks_supported(tmp_path):
        pytest.skip(
            "host cannot create symlinks (Windows needs Developer Mode or elevation)"
        )


def subprocess_text_encoding() -> str:
    """Decode captured pipes as UTF-8, matching PA child scripts on Windows."""
    return "utf-8"


def assert_private_file(path: Path, *, platform: str | None = None) -> None:
    """Assert POSIX mode locally; native Windows ACL has a separate gate."""
    assert path.is_file()
    effective = platform or os.name
    if effective == "posix":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
    elif effective != "nt":
        raise AssertionError(f"unknown platform for privacy gate: {effective}")


@pytest.fixture(autouse=True)
def hermetic_env(tmp_path, monkeypatch):
    """Isolate user-level state without changing the process cwd."""
    home = tmp_path / "home"
    state_root = tmp_path / "repo-state"
    home.mkdir()
    state_root.mkdir()
    data_dir = state_root / "data"
    data_dir.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    # PA_FRAMEWORK_DATA is the override the memory layer actually honors;
    # PA_TEST_REPO_ROOT alone lets default data paths write into the checkout.
    monkeypatch.setenv("PA_FRAMEWORK_DATA", str(data_dir))
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
        return _copy_source_without_git(destination)
    in_git = subprocess.run(
        [git_executable, "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding=subprocess_text_encoding(),
        errors="replace",
    )
    if in_git.returncode != 0:
        return _copy_source_without_git(destination)

    tree = subprocess.run(
        [git_executable, "write-tree"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding=subprocess_text_encoding(),
        errors="replace",
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
