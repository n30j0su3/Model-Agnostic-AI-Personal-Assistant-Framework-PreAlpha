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


def test_symlink_probe_detects_capable_host(tmp_path):
    if not hasattr(os, "symlink"):
        pytest.skip("platform has no symlink API")
    assert symlinks_supported(tmp_path) is True


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
