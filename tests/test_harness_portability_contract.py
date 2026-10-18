"""W4 contracts: test harness portability and fail-closed fixtures.

- Symlink creation is a host capability: probe it, skip with a reason only when
  the host cannot create symlinks, and never leave probe files behind.
- The no-git fallback must not silently copy or ignore runtime residue from a
  contaminated source tree.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from conftest import RUNTIME_RESIDUE, find_runtime_residue, symlinks_supported

ROOT = Path(__file__).resolve().parents[1]


def test_symlink_probe_detects_capable_host(tmp_path):
    if not hasattr(os, "symlink"):
        pytest.skip("platform has no symlink API")
    if not symlinks_supported(tmp_path):
        # Non-developer Windows hosts cannot create symlinks without Developer
        # Mode or elevation; that is an expected user configuration, not a
        # framework defect. The fail-closed denial path remains covered by
        # test_symlink_probe_reports_denial_and_leaves_no_files.
        pytest.skip(
            "host cannot create symlinks (Windows needs Developer Mode or elevation)"
        )
    assert symlinks_supported(tmp_path) is True


def test_symlink_capability_is_required_in_ci(tmp_path):
    """CI must exercise the positive symlink path; local hosts may skip it."""
    if not os.environ.get("CI"):
        pytest.skip("local host may lack the symlink privilege")
    assert symlinks_supported(tmp_path) is True, (
        "CI runner must support symlinks for the security lane"
    )


def test_symlink_probe_reports_denial_and_leaves_no_files(tmp_path, monkeypatch):
    def denied(self, target, target_is_directory=False):
        raise OSError(1314, "A required privilege is not held by the client")

    monkeypatch.setattr(Path, "symlink_to", denied)

    assert symlinks_supported(tmp_path) is False
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".symlink-probe")]
    assert leftovers == []


def test_residue_detector_flags_runtime_state(tmp_path):
    assert find_runtime_residue(tmp_path) == []

    (tmp_path / "data").mkdir()
    assert "data" in find_runtime_residue(tmp_path)


def test_residue_list_covers_user_and_cache_state():
    assert "data" in RUNTIME_RESIDUE
    assert "core/.context/knowledge/errors" in RUNTIME_RESIDUE
    assert "core/.context/.cache" in RUNTIME_RESIDUE


def test_pytest_cache_is_tool_scratch_not_runtime_residue():
    assert ".pytest_cache" not in RUNTIME_RESIDUE


def test_residue_list_covers_workspaces_and_backlog():
    assert "workspaces" in RUNTIME_RESIDUE
    assert "core/.context/codebase/backlog.md" in RUNTIME_RESIDUE


ERROR_LOGGER_TEST = ROOT / "core" / "scripts" / "tests" / "error_logger_test.py"


def test_error_logger_tests_isolate_default_errors_dir():
    """Default ErrorLogger() writes into the source tree; tests must redirect it."""
    text = ERROR_LOGGER_TEST.read_text(encoding="utf-8")
    assert 'setattr(_el, "ERRORS_DIR"' in text
