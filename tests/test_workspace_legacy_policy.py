"""Workspace legacy policy (decision A): a legacy workspaces/content directory is
never deleted when the selection changes; it is reported with its path.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def _load(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


workspace_cfg = _load("workspace_config_policy", SCRIPTS / "workspace_config.py")


def _legacy_tree(root: Path) -> Path:
    project = root / "workspaces" / "content" / "projects" / "keep.md"
    project.parent.mkdir(parents=True)
    project.write_text("user work\n", encoding="utf-8")
    return project


def test_unselected_legacy_content_is_reported_and_kept(tmp_path):
    kept = _legacy_tree(tmp_path)
    entries = {"research": {"dir": "Research", "display": "Research"}}

    assert workspace_cfg.preserved_legacy_workspaces(tmp_path, entries) == ["workspaces/content"]
    assert kept.read_text(encoding="utf-8") == "user work\n"


def test_selected_content_is_not_reported(tmp_path):
    _legacy_tree(tmp_path)
    entries = {"content": {"dir": "content", "display": "Content"}}

    assert workspace_cfg.preserved_legacy_workspaces(tmp_path, entries) == []


def test_no_legacy_directory_means_no_notice(tmp_path):
    entries = {"research": {"dir": "Research", "display": "Research"}}

    assert workspace_cfg.preserved_legacy_workspaces(tmp_path, entries) == []


def test_installer_dry_run_receipt_lists_preserved_legacy(repo_extract):
    _legacy_tree(repo_extract)
    result = subprocess.run(
        [
            sys.executable,
            str(repo_extract / "core" / "scripts" / "install.py"),
            "--non-interactive",
            "--dry-run",
            "--json",
            "--no-browser",
            "--workspaces",
            "research,trabajo",
        ],
        cwd=repo_extract,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["preserved_legacy_workspaces"] == ["workspaces/content"]
    assert (repo_extract / "workspaces" / "content" / "projects" / "keep.md").exists()
