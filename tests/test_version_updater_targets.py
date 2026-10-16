"""Version updater must reference only live public surfaces."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def test_version_updater_targets_all_exist(repo_extract):
    path = repo_extract / "core/scripts/version_updater.py"
    spec = importlib.util.spec_from_file_location("version_updater_targets_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    missing = [relative for relative in module.TARGETS if not (repo_extract / relative).is_file()]

    assert missing == []
    assert "README-technical.md" not in module.TARGETS
    assert "GEMINI.md" not in module.TARGETS
