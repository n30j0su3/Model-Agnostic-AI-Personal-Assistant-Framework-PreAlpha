"""Canonical recovery registry and honest capability contracts."""

from __future__ import annotations

import importlib
from pathlib import Path

from core.recovery import orchestrator as recovery
from core.scripts.error_logger import ErrorLogger


EXPECTED_IDS = {f"PB-{number:03d}" for number in range(1, 10)}


def test_canonical_registry_exists_and_validates_all_builtin_actions():
    assert hasattr(recovery, "PLAYBOOK_REGISTRY")
    assert hasattr(recovery, "validate_playbook_registry")
    assert set(recovery.PLAYBOOK_REGISTRY) == EXPECTED_IDS
    assert recovery.validate_playbook_registry() == []


def test_registry_error_mappings_match_action_meaning():
    resolve = getattr(recovery, "resolve_playbook_for_error_type", None)
    assert callable(resolve)
    assert resolve("UnicodeDecodeError") == "PB-001"
    assert resolve("FileNotFoundError") == "PB-002"
    assert resolve("JSONDecodeError") == "PB-003"
    assert resolve("TimeoutError") == "PB-004"
    assert resolve("YAMLError") == "PB-006"
    assert resolve("OSError") is None
    assert resolve("PermissionError") is None
    assert resolve("RuntimeError") is None

    orchestrator = recovery.RecoveryOrchestrator()
    implicit_auth = orchestrator.execute_playbook("PB-009")
    assert implicit_auth["status"] == "failed"
    explicit_auth = orchestrator.execute_playbook(
        "PB-009",
        {"can_refresh": True, "retry_count": 0, "max_retries": 1},
    )
    assert explicit_auth["status"] == "success"


def test_error_logger_uses_registry_hints_and_real_orchestrator(tmp_path):
    logger = ErrorLogger(errors_dir=tmp_path / "errors")

    assert logger._get_playbook_suggestion("JSONDecodeError") == "PB-003"
    assert logger._get_playbook_suggestion("PermissionError") is None
    assert "JSON" in logger.generate_playbook_hint({"type": "JSONDecodeError"})

    executed = logger.trigger_playbook(
        "PB-004",
        {"retry_count": 0, "max_retries": 1},
    )
    assert executed["triggered"] is True
    assert executed["status"] == "success"
    assert executed["details"]["status"] == "success"

    unknown = logger.trigger_playbook("PB-015")
    assert unknown["triggered"] is False
    assert unknown["status"] == "no_action"
    assert unknown["details"]["status"] == "no_action"

    network = logger.suggest_recovery("network")
    assert network["playbook_id"] == "PB-004"
    ambiguous = logger.suggest_recovery("data_integrity")
    assert ambiguous["playbook_id"] is None
    assert "Manual investigation" in ambiguous["strategy"]


def test_self_healing_check_consumes_canonical_mapping(monkeypatch, tmp_path):
    module = importlib.import_module("core.scripts.self_healing_check")
    assert module.PLAYBOOK_MAP == recovery.ERROR_TYPE_TO_PLAYBOOK
    assert set(module.PLAYBOOK_MAP.values()).issubset(EXPECTED_IDS)

    error_log = tmp_path / "errors" / "error-log.json"
    monkeypatch.setattr(module, "ERROR_LOG_PATH", error_log)
    healing = module.SelfHealingCheck()

    executed = healing._trigger_playbook({"id": "ERR-1", "type": "TimeoutError"})
    assert executed["playbook_id"] == "PB-004"
    assert executed["status"] == "success"

    unavailable = healing._trigger_playbook({"id": "ERR-2", "type": "RuntimeError"})
    assert unavailable["playbook_id"] is None
    assert unavailable["status"] == "unavailable"


def test_missing_vitals_guardian_is_reported_unavailable(monkeypatch, tmp_path):
    scripts_dir = Path(__file__).resolve().parents[1] / "core" / "scripts"
    monkeypatch.syspath_prepend(str(scripts_dir))
    module = importlib.import_module("session_start")
    monkeypatch.setattr(module, "SCRIPT_DIR", tmp_path)

    available, issues = module.check_vitals_integrity()

    assert available is False
    assert issues == ["Vitals Guardian unavailable"]
    status_fn = getattr(module, "framework_enforcement_status", None)
    assert callable(status_fn)
    status = status_fn()
    assert isinstance(status, dict)
    assert status["status"] == "unavailable"


def test_missing_framework_guardian_has_queryable_status():
    module = importlib.import_module("core.scripts.session_end")
    status_fn = getattr(module, "framework_enforcement_status", None)
    assert callable(status_fn)
    assert status_fn() == {
        "available": False,
        "status": "unavailable",
        "reason": "Framework Guardian is not installed",
    }
