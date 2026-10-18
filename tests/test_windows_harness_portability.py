"""RC5 Windows/native test-harness portability contracts."""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import pytest

import conftest as suite_conftest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def _load(name: str, path: Path):
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


def test_subprocess_text_encoding_matches_utf8_children(monkeypatch):
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252:replace")
    helper = getattr(suite_conftest, "subprocess_text_encoding", None)
    assert callable(helper)
    assert helper() == "utf-8"


def test_captured_child_utf8_survives_cp1252_parent_request(monkeypatch):
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")
    monkeypatch.setenv("PYTHONUTF8", "0")
    child = (
        "import sys; "
        "sys.stdout.reconfigure(encoding='utf-8', errors='replace'); "
        "print('══ v0.4.1-beta ✓')"
    )

    result = subprocess.run(
        [sys.executable, "-c", child],
        capture_output=True,
        text=True,
        encoding=suite_conftest.subprocess_text_encoding(),
        errors="replace",
        check=True,
    )

    assert result.stdout == "══ v0.4.1-beta ✓\n"


def test_repo_extract_does_not_invoke_missing_git(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "sample.txt").write_text("portable\n", encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(suite_conftest, "ROOT", source)
    monkeypatch.setattr(suite_conftest.shutil, "which", lambda _name: None)

    def record_run(argv, **_kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 1, "", "")

    monkeypatch.setattr(suite_conftest.subprocess, "run", record_run)
    fixture_body = getattr(suite_conftest.repo_extract, "__wrapped__")
    extracted = fixture_body(tmp_path)

    assert calls == []
    assert (extracted / "sample.txt").read_text(encoding="utf-8") == "portable\n"


def test_windows_relative_paths_are_serialized_with_forward_slashes():
    detect = _load("detect_workspace_portability", SCRIPTS / "detect_workspace.py")
    helper = getattr(detect, "_relative_posix", None)
    assert callable(helper)
    root = PureWindowsPath("C:/repo")
    target = PureWindowsPath("C:/repo/workspaces/Trabajo/projects/informe")
    assert helper(target, root) == "workspaces/Trabajo/projects/informe"


def test_core_fixture_write_text_calls_declare_encoding():
    missing: list[str] = []
    for path in sorted((ROOT / "core/scripts/tests").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "write_text":
                continue
            keywords = {keyword.arg for keyword in node.keywords if keyword.arg}
            if "encoding" not in keywords:
                missing.append(f"{path.relative_to(ROOT).as_posix()}:{node.lineno}")
    assert missing == []


def test_opencode_runtime_contracts_do_not_build_posix_executables():
    source = (ROOT / "tests/test_windows_qa_runtime.py").read_text(encoding="utf-8")
    assert 'script = f"#!/usr/bin/env python3' not in source
    assert ".chmod(0o755)" not in source


def test_release_ci_runs_cp1252_gate_on_windows():
    workflow = (ROOT / ".github/workflows/release-gates.yml").read_text(encoding="utf-8")
    assert "Windows cp1252 compatibility" in workflow
    assert "if: runner.os == 'Windows'" in workflow
    assert "PYTHONIOENCODING: cp1252" in workflow
    assert 'PYTHONUTF8: "0"' in workflow


def test_private_file_helper_enforces_posix_mode(tmp_path):
    helper = getattr(suite_conftest, "assert_private_file", None)
    assert callable(helper)
    target = tmp_path / "private.json"
    target.write_text("{}\n", encoding="utf-8")
    if os.name == "posix":
        os.chmod(target, 0o644)
        with pytest.raises(AssertionError):
            helper(target, platform="posix")
        os.chmod(target, 0o600)
        helper(target, platform="posix")
    else:
        # Windows synthesizes writable/read-only mode bits as 0666/0444;
        # neither can prove the POSIX 0600 privacy contract.
        for mode in (0o644, 0o400):
            os.chmod(target, mode)
            with pytest.raises(AssertionError):
                helper(target, platform="posix")


def test_private_file_helper_rejects_unknown_platform(tmp_path):
    helper = getattr(suite_conftest, "assert_private_file", None)
    assert callable(helper)
    target = tmp_path / "private.json"
    target.write_text("{}\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="unknown platform"):
        helper(target, platform="plan9")


def test_private_file_helper_defers_windows_mode_bits_to_acl_gate(tmp_path):
    helper = getattr(suite_conftest, "assert_private_file", None)
    assert callable(helper)
    target = tmp_path / "private.json"
    target.write_text("{}\n", encoding="utf-8")
    os.chmod(target, 0o644)
    helper(target, platform="nt")


@pytest.mark.skipif(os.name != "nt", reason="native Windows ACL gate")
def test_windows_private_file_acl_excludes_broad_readers(tmp_path):
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    workspace_config = _load("workspace_config_acl_gate", SCRIPTS / "workspace_config.py")
    workspace_config.save_user_config({"professional": "Trabajo"}, repo_root=tmp_path)
    target = tmp_path / "data/user/workspaces.json"
    script = r"""
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$rows = @((Get-Acl -LiteralPath $args[0]).Access | ForEach-Object {
  try {
    $sid = $_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value
  } catch {
    $sid = $_.IdentityReference.Value
  }
  [PSCustomObject]@{sid=$sid; type=[string]$_.AccessControlType}
})
ConvertTo-Json -Compress -InputObject $rows
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script, str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, f"PowerShell ACL probe exit={result.returncode}"
    rows = json.loads(result.stdout or "[]")
    if isinstance(rows, dict):
        rows = [rows]
    broad_sids = {"S-1-1-0", "S-1-5-11", "S-1-5-32-545"}
    unsafe = sorted(
        row["sid"] for row in rows
        if row.get("type") == "Allow" and row.get("sid") in broad_sids
    )
    assert unsafe == []
