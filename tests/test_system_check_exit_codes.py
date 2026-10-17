"""Exit-code contract tests for system_check."""

from __future__ import annotations

import importlib.util
import json
import time
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


def check(name, func, *, quick, critical=True):
    return {
        "name": name,
        "description": name,
        "critical": critical,
        "quick": quick,
        "func": func,
    }


def test_quick_mode_runs_only_explicit_quick_subset(monkeypatch):
    seen = []

    def run(name):
        seen.append(name)
        return True, name

    monkeypatch.setattr(
        system_check,
        "checks",
        [
            check("fast", lambda: run("fast"), quick=True),
            check("heavy", lambda: run("heavy"), quick=False),
        ],
    )

    results, _ = system_check.run_all_checks(quick=True)
    assert [item["name"] for item in results] == ["fast"]
    assert seen == ["fast"]


def test_results_keep_registration_order(monkeypatch):
    def slow():
        time.sleep(0.03)
        return True, "slow"

    monkeypatch.setattr(
        system_check,
        "checks",
        [
            check("slow", slow, quick=True),
            check("fast", lambda: (True, "fast"), quick=True),
        ],
    )

    results, _ = system_check.run_all_checks()
    assert [item["name"] for item in results] == ["slow", "fast"]


def test_timed_out_check_is_reported_without_aborting_report(monkeypatch):
    def slow():
        time.sleep(0.05)
        return True, "late"

    monkeypatch.setattr(
        system_check,
        "checks",
        [check("slow", slow, quick=True)],
    )

    results, _ = system_check.run_all_checks(quick=True, timeout_seconds=0.005)
    assert results[0]["name"] == "slow"
    assert results[0]["status"] is False
    assert results[0]["detail"] == "Timeout after 0.005s"


def test_fix_mode_propagates_auto_fix_failure(monkeypatch):
    monkeypatch.setattr(system_check, "auto_fix", lambda: False)
    assert system_check.main(["--fix"]) == 1
    monkeypatch.setattr(system_check, "auto_fix", lambda: True)
    assert system_check.main(["--fix"]) == 0


def test_json_output_is_stably_sorted_and_codepage_safe(monkeypatch, capsys):
    unicode_result = result(True)
    unicode_result["detail"] = "status: ✅"
    monkeypatch.setattr(
        system_check,
        "run_all_checks",
        lambda quick=False: ([unicode_result], 0.01),
    )

    assert system_check.main(["--json"]) == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert list(payload) == sorted(payload)
    assert "\\u2705" in output
