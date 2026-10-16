"""Fresh-install reference integrity contract."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def install_fresh(root: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    home = tmp_path / "install-home"
    home.mkdir(exist_ok=True)
    env = {
        "HOME": str(home),
        "USERPROFILE": str(home),
        "PATH": str(Path(sys.executable).parent),
        "PYTHONDONTWRITEBYTECODE": "1",
        "LANG": "C.UTF-8",
    }
    return subprocess.run(
        [sys.executable, "core/scripts/install.py", "--no-browser"],
        cwd=root,
        env=env,
        input="\n" * 32,
        capture_output=True,
        text=True,
        timeout=180,
        check=True,
    )


def test_reference_integrity_after_install(repo_extract, tmp_path):
    install = install_fresh(repo_extract, tmp_path)

    assert "v0.4.1-beta" in install.stdout
    assert "v0.3.8-alpha" not in install.stdout
    assert (repo_extract / "workspaces/content/projects").is_dir()

    result = subprocess.run(
        [sys.executable, "core/scripts/reference_integrity_check.py"],
        cwd=repo_extract,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_backlog_has_one_canonical_post_install_path(repo_extract, tmp_path):
    assert (repo_extract / "core/.context/codebase/backlog.seed.md").is_file()
    assert not (repo_extract / "core/.context/codebase/backlog.md").exists()

    install_fresh(repo_extract, tmp_path)

    assert (repo_extract / "core/.context/codebase/backlog.md").is_file()
    assert not (repo_extract / "core/.context/knowledge/backlog.md").exists()


def test_dashboard_check_only_requires_the_served_html(repo_extract):
    module_path = repo_extract / "core/scripts/system_check.py"
    scripts = str(module_path.parent)
    sys.path.insert(0, scripts)
    try:
        spec = importlib.util.spec_from_file_location("post_install_system_check", module_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(scripts)

    setattr(module, "REPO_ROOT", repo_extract)
    ok, detail = module.check_dashboard()

    assert ok is True, detail
    assert detail == "dashboard.html OK"
