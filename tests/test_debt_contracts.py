"""W5 contracts: small debt items that must not regress silently."""
from __future__ import annotations

import ast
import importlib.util
import re
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


def test_navigation_footer_matches_canonical_version():
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    navigation = (ROOT / "core" / ".context" / "navigation.md").read_text(encoding="utf-8")
    footer = re.findall(r"Framework v([0-9][^\s|*]*)", navigation)
    assert footer, "navigation.md footer has no framework version"
    assert footer[-1] == version


def test_cron_setup_has_single_module_docstring():
    tree = ast.parse((SCRIPTS / "cron_setup.py").read_text(encoding="utf-8"))
    leading = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            leading.append(node)
        else:
            break
    assert len(leading) == 1


def test_scripts_do_not_use_deprecated_utcnow():
    offenders = [
        path.name
        for path in SCRIPTS.glob("*.py")
        if "utcnow(" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_small_sqlite_file_never_reports_zero_kb(tmp_path, monkeypatch):
    system_check = _load("system_check_w5", SCRIPTS / "system_check.py")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "sessions.db").write_bytes(b"x" * 300)
    monkeypatch.setattr(system_check, "DATA_DIR", data_dir)

    ok, message = system_check.check_sqlite()

    assert ok is True
    assert "0 KB" not in message


def test_changelog_allowlist_count_matches_release_builder():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    build_release = _load("build_release_w5", SCRIPTS / "build_release.py")
    count = len(build_release.CONTEXT_PUBLIC_PATHS)
    assert f"{count}-member" in text
    assert "22-member" not in text
