"""W2 wiring contracts for configurable semantic workspaces."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from conftest import assert_private_file, subprocess_text_encoding


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


def run_installer(root: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    home = root.parent / "workspace-installer-home"
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


def test_installer_dry_run_reports_selected_workspaces_without_writes(repo_extract):
    result = run_installer(
        repo_extract,
        "--non-interactive",
        "--dry-run",
        "--json",
        "--no-browser",
        "--workspaces",
        "research,trabajo",
        "--workspace-name",
        "professional=Trabajo",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["writes"] == []
    assert receipt["planned_workspace_directories"] == [
        "workspaces/Research/projects",
        "workspaces/Trabajo/projects",
    ]
    assert receipt["planned_workspace_config"]["workspaces"] == {
        "professional": {"dir": "Trabajo", "display": "Trabajo"},
        "research": {"dir": "Research", "display": "Research"},
    }
    assert not (repo_extract / "data").exists()
    assert not (repo_extract / "workspaces").exists()


def test_installer_creates_only_selected_and_persists_0600(repo_extract):
    result = run_installer(
        repo_extract,
        "--non-interactive",
        "--json",
        "--no-browser",
        "--workspaces",
        "research,professional",
        "--workspace-name",
        "professional=Trabajo",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (repo_extract / "workspaces/Research/projects").is_dir()
    assert (repo_extract / "workspaces/Trabajo/projects").is_dir()
    for absent in ("Personal", "Content", "Development", "Homelab", "content"):
        assert not (repo_extract / "workspaces" / absent).exists()
    config_path = repo_extract / "data/user/workspaces.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert set(payload["workspaces"]) == {"professional", "research"}
    assert payload["workspaces"]["professional"]["dir"] == "Trabajo"
    assert_private_file(config_path)


def test_installer_default_remains_legacy_content_compatible(repo_extract):
    result = run_installer(
        repo_extract, "--non-interactive", "--json", "--no-browser"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (repo_extract / "workspaces/content/projects").is_dir()
    payload = json.loads(
        (repo_extract / "data/user/workspaces.json").read_text(encoding="utf-8")
    )
    assert payload["workspaces"] == {
        "content": {"dir": "content", "display": "Content"}
    }


def test_installer_supports_custom_workspace_name(repo_extract):
    result = run_installer(
        repo_extract,
        "--non-interactive",
        "--json",
        "--no-browser",
        "--workspaces",
        "custom",
        "--workspace-name",
        "custom=MyLab",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (repo_extract / "workspaces/MyLab/projects").is_dir()
    payload = json.loads(
        (repo_extract / "data/user/workspaces.json").read_text(encoding="utf-8")
    )
    assert payload["workspaces"] == {
        "custom": {"dir": "MyLab", "display": "MyLab"}
    }


def test_installer_json_dry_run_never_prompts(repo_extract):
    result = run_installer(repo_extract, "--dry-run", "--json", "--no-browser")
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["mode"] == "dry-run"
    assert receipt["writes"] == []


def test_installer_rejects_unknown_rename_target(repo_extract):
    result = run_installer(
        repo_extract,
        "--non-interactive",
        "--dry-run",
        "--json",
        "--workspace-name",
        "professional=Trabajo",
    )
    assert result.returncode == 2


def test_detect_workspace_uses_configured_semantic_key(tmp_path, monkeypatch):
    detect = load_module("detect_workspace_w2", SCRIPTS / "detect_workspace.py")
    root = tmp_path / "repo"
    project = root / "workspaces/Trabajo/projects/informe"
    project.mkdir(parents=True)
    cfg = root / "data/user/workspaces.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({
        "schema": 1,
        "workspaces": {
            "professional": {"dir": "Trabajo", "display": "Trabajo"}
        },
    }), encoding="utf-8")

    workspace = detect.detect_workspace(project, "silent", repo_root=root)
    assert workspace is not None
    assert workspace["name"] == "professional"
    assert workspace["directory"] == "Trabajo"
    assert workspace["path"] == "workspaces/Trabajo"


def test_detect_workspace_rejects_prefix_neighbor(tmp_path):
    detect = load_module("detect_workspace_neighbor_w2", SCRIPTS / "detect_workspace.py")
    root = tmp_path / "repo"
    neighbor = root / "workspaces-extra/Trabajo/projects/informe"
    neighbor.mkdir(parents=True)
    assert detect.detect_workspace(neighbor, "silent", repo_root=root) is None


def test_detect_project_uses_renamed_workspace_path(tmp_path):
    detect = load_module("detect_project_w2", SCRIPTS / "detect_workspace.py")
    root = tmp_path / "repo"
    project_dir = root / "workspaces/Trabajo/projects/informe"
    project_dir.mkdir(parents=True)
    workspace = {
        "name": "professional",
        "directory": "Trabajo",
        "path": "workspaces/Trabajo",
    }
    project = detect.detect_project(project_dir, workspace, "silent", repo_root=root)
    assert project is not None
    assert project["path"] == "workspaces/Trabajo/projects/informe"


def test_session_sync_renders_configured_renamed_workspace(tmp_path, monkeypatch):
    # session_start imports create first-run directories at import; redirect all roots.
    session = load_module("session_start_w2", SCRIPTS / "session_start.py")
    root = tmp_path / "repo"
    master = root / "core/.context/MASTER.md"
    master.parent.mkdir(parents=True)
    master.write_text(
        "# MASTER\r\n\r\n## Active Workspaces\r\n\r\n"
        "- [ ] Professional: No configurado.\r\n\r\n## Current Focus\r\nX\r\n",
        encoding="utf-8",
        newline="",
    )
    (root / "workspaces/Trabajo/projects").mkdir(parents=True)
    cfg = root / "data/user/workspaces.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({
        "schema": 1,
        "workspaces": {
            "professional": {"dir": "Trabajo", "display": "Trabajo"}
        },
    }), encoding="utf-8")
    monkeypatch.setattr(session, "REPO_ROOT", root)
    monkeypatch.setattr(session, "CONTEXT_DIR", root / "core/.context")

    session.sync_workspaces_status()

    rendered = master.read_text(encoding="utf-8")
    assert "Trabajo" in rendered
    assert "workspaces/Trabajo" in rendered
    assert "Professional: No configurado" not in rendered


def test_agent_prompts_use_semantic_routing_not_forced_content():
    for relative in (
        ".opencode/agent/FreakingJSON.md",
        "core/agents/pa-assistant.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "data/user/workspaces.json" in text
        assert "professional" in text
        assert "personal" in text
        assert "workspaces/content/projects/<nombre" not in text
        assert "workspaces/content/projects/<nombre-proyecto" not in text


def test_user_workspace_state_and_all_workspaces_are_update_protected():
    protected = (ROOT / "config/update-protected-paths.txt").read_text(encoding="utf-8")
    assert "data/user" in protected.splitlines()
    assert "workspaces" in protected.splitlines()

    update = load_module("update_w2", SCRIPTS / "update.py")
    defaults = update.load_update_protected_paths()
    assert "data/user" in defaults
    assert "workspaces" in defaults

    migrate = load_module("migrate_w2", SCRIPTS / "migrate.py")
    rollback = load_module("rollback_w2", SCRIPTS / "rollback.py")
    assert Path("workspaces") in migrate.PROTECTED_PREFIXES
    assert Path("workspaces") in rollback.MANDATORY_PROTECTED
