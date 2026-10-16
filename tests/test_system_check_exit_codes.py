"""Exit-code contract tests for system_check."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "core/scripts/system_check.py"
SPEC = importlib.util.spec_from_file_location("system_check_under_test", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError("cannot load system_check")
system_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(system_check)


def result(status, *, critical=True):
    return {
        "name": "fixture",
        "description": "fixture",
        "critical": critical,
        "status": status,
        "detail": "fixture",
        "duration_ms": 0,
    }


def test_json_mode_fails_on_critical_error(monkeypatch, capsys):
    monkeypatch.setattr(
        system_check, "run_all_checks", lambda quick=False: ([result(False)], 0.01)
    )
    assert system_check.main(["--quick", "--json"]) == 1
    assert '"critical_errors": 1' in capsys.readouterr().out


def test_human_mode_fails_on_critical_error(monkeypatch):
    monkeypatch.setattr(
        system_check, "run_all_checks", lambda quick=False: ([result(False)], 0.01)
    )
    assert system_check.main(["--quick"]) == 1


def test_warning_only_is_success_in_both_modes(monkeypatch):
    monkeypatch.setattr(
        system_check,
        "run_all_checks",
        lambda quick=False: ([result("warn", critical=False)], 0.01),
    )
    assert system_check.main(["--quick", "--json"]) == 0
    assert system_check.main(["--quick"]) == 0
