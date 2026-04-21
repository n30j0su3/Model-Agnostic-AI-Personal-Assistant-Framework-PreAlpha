#!/usr/bin/env python3
"""Unit tests for error_logger.py v2.0.0."""

import json
import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib
from unittest.mock import patch

import pytest

_el = importlib.import_module("error_logger")
ErrorLogger = _el.ErrorLogger


@pytest.fixture
def logger(tmp_path):
    return ErrorLogger(errors_dir=tmp_path / "errors")


def _make_error(error_type, minutes_ago=0, file_name="app.py", **extra):
    timestamp = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
    error = {
        "type": error_type,
        "message": f"{error_type} happened",
        "file": file_name,
        "line": 10,
        "timestamp": timestamp,
    }
    error.update(extra)
    return error


class TestHelpersAndInitialization:
    def test_initialization_creates_expected_files(self, tmp_path):
        log = ErrorLogger(errors_dir=tmp_path / "custom-errors")

        assert log.errors_dir.exists()
        assert log.index_file.exists()
        assert log.log_file.exists()
        assert json.loads(log.index_file.read_text(encoding="utf-8")) == {
            "errors": [],
            "last_updated": None,
        }
        assert "# Error Log" in log.log_file.read_text(encoding="utf-8")

    def test_color_helper_wraps_text(self):
        assert _el.c("x", _el.Colors.GREEN) == f"{_el.Colors.GREEN}x{_el.Colors.END}"

    def test_safe_print_falls_back_after_unicode_encode_error(self, monkeypatch):
        calls = []
        state = {"count": 0}

        class FakeStdout:
            encoding = "ascii"

        def fake_print(text, **kwargs):
            state["count"] += 1
            if state["count"] == 1:
                raise UnicodeEncodeError("ascii", "ñ", 0, 1, "boom")
            calls.append((text, kwargs))

        monkeypatch.setattr(_el.sys, "stdout", FakeStdout())
        monkeypatch.setattr("builtins.print", fake_print)

        _el.safe_print("España")

        assert calls == [("Espa?a", {})]

    def test_read_index_returns_empty_for_missing_or_invalid_json(self, logger):
        logger.index_file.unlink()
        assert logger._read_index() == {"errors": [], "last_updated": None}

        logger.index_file.write_text("{bad json", encoding="utf-8")
        assert logger._read_index() == {"errors": [], "last_updated": None}

    def test_write_and_append_failures_are_reported(self, logger, monkeypatch):
        messages = []

        def fake_safe_print(message, **kwargs):
            messages.append(message)

        def raising_open(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr(_el, "safe_print", fake_safe_print)
        monkeypatch.setattr("builtins.open", raising_open)

        logger._write_index({"errors": []})
        logger._write_log_header()
        logger._append_to_log({"id": "ERR-1", "type": "TypeError"})

        assert any("Failed to write index" in m for m in messages)
        assert any("Failed to write log header" in m for m in messages)
        assert any("Failed to append to log" in m for m in messages)


class TestLoggingAndResolveFlows:
    def test_log_error_writes_json_and_markdown(self, logger):
        error_id = logger.log_error(
            {
                "type": "FileNotFoundError",
                "message": "config.json missing",
                "file": "loader.py",
                "line": 22,
                "context": "startup",
            }
        )

        saved = logger.get_error_by_id(error_id)
        assert error_id.startswith("ERR-")
        assert saved["playbook_suggestion"] == "PB-002"
        assert saved["resolved"] is False

        log_text = logger.log_file.read_text(encoding="utf-8")
        assert f"[!] {error_id}" in log_text
        assert "config.json missing" in log_text
        assert "| **Status** | Open |" in log_text

    def test_format_md_entry_handles_resolved_branch(self, logger):
        entry = logger._format_md_entry(
            {
                "id": "ERR-1",
                "timestamp": "2026-01-01T00:00:00",
                "type": "RuntimeError",
                "message": "boom",
                "resolved": True,
                "playbook_suggestion": "PB-015",
            }
        )
        assert "[OK] ERR-1" in entry
        assert "| **Status** | Resolved |" in entry

    def test_resolve_error_updates_index_and_markdown(self, logger):
        error_id = logger.log_error({"type": "ValueError", "message": "bad", "file": "a.py", "line": 1})

        assert logger.resolve_error(error_id) is True

        saved = logger.get_error_by_id(error_id)
        assert saved["resolved"] is True
        assert saved["resolved_at"] is not None

        log_text = logger.log_file.read_text(encoding="utf-8")
        assert f"[OK] {error_id}" in log_text
        assert "| **Status** | Resolved |" in log_text

    def test_resolve_error_returns_false_when_missing(self, logger):
        assert logger.resolve_error("ERR-DOES-NOT-EXIST") is False

    def test_update_md_entry_warns_when_file_update_fails(self, logger, monkeypatch):
        warnings = []

        def fake_safe_print(message, **kwargs):
            warnings.append(message)

        def raising_read_text(self, **kwargs):
            raise OSError("locked")

        monkeypatch.setattr(_el, "safe_print", fake_safe_print)
        monkeypatch.setattr(Path, "read_text", raising_read_text)

        logger._update_md_entry("ERR-1", True, "2026-01-01T00:00:00")

        assert any("Could not update MD entry" in msg for msg in warnings)


class TestGettersStatsAndHints:
    def test_getters_and_stats_reflect_resolved_state(self, logger):
        id_one = logger.log_error({"type": "ConnectionError", "message": "timeout", "file": "n.py", "line": 5})
        id_two = logger.log_error({"type": "ConnectionError", "message": "refused", "file": "n.py", "line": 8})
        id_three = logger.log_error({"type": "KeyError", "message": "missing", "file": "cfg.py", "line": 3})
        logger.resolve_error(id_two)

        unresolved = logger.get_unresolved_errors()
        all_errors = logger.get_all_errors()
        stats = logger.get_error_stats()

        assert {e["id"] for e in unresolved} == {id_one, id_three}
        assert len(all_errors) == 3
        assert logger.get_error_by_id(id_one)["type"] == "ConnectionError"
        assert logger.get_error_by_id("ERR-none") is None
        assert stats["total"] == 3
        assert stats["resolved"] == 1
        assert stats["unresolved"] == 2
        assert stats["by_type"]["ConnectionError"] == 2
        assert stats["most_common"][0] == ("ConnectionError", 2)

    def test_generate_playbook_hint_known_and_unknown(self, logger):
        assert "PB-001" in logger.generate_playbook_hint({"type": "UnicodeDecodeError"})
        assert "Manual investigation required" in logger.generate_playbook_hint({"type": "OddError"})


class TestClassifyError:
    def setup_method(self):
        self.logger = ErrorLogger()

    def test_classify_connection_error(self):
        assert self.logger.classify_error(ConnectionError("timeout")) == "network"

    def test_classify_file_not_found(self):
        assert self.logger.classify_error(FileNotFoundError("missing.py")) == "file_system"

    def test_classify_permission_error(self):
        assert self.logger.classify_error(PermissionError("denied")) == "file_system"

    def test_classify_json_decode_error(self):
        import json

        result = self.logger.classify_error(json.JSONDecodeError("bad", "", 0))
        assert result in ("data_integrity", "file_system")

    def test_classify_timeout_error(self):
        assert self.logger.classify_error(TimeoutError("slow")) == "network"

    def test_classify_key_error(self):
        assert self.logger.classify_error(KeyError("missing_key")) in ("data_integrity", "configuration")

    def test_classify_import_error(self):
        assert self.logger.classify_error(ImportError("no module")) == "configuration"

    def test_classify_unicode_error(self):
        result = self.logger.classify_error(UnicodeDecodeError("utf-8", b"", 0, 1, "bad"))
        assert result in ("data_integrity", "file_system")

    def test_classify_dict_with_type(self):
        result = self.logger.classify_error({"type": "ConnectionError", "message": "refused"})
        assert result == "network"

    def test_classify_string_message(self):
        result = self.logger.classify_error("network timeout occurred")
        assert result == "network"

    def test_classify_string_auth(self):
        result = self.logger.classify_error("authentication failed: 401")
        assert result in ("authentication", "unknown")

    def test_classify_unknown(self):
        assert self.logger.classify_error("something completely weird") == "unknown"

    def test_classify_non_standard_object_uses_string_conversion(self):
        class WeirdObject:
            def __str__(self):
                return ""

        assert self.logger.classify_error(WeirdObject()) == "unknown"


class TestSuggestRecovery:
    def setup_method(self):
        self.logger = ErrorLogger()

    def test_suggest_network(self):
        result = self.logger.suggest_recovery("network")
        assert result["playbook_id"] == "PB-NET-RETRY"
        assert result["category"] == "network"

    def test_suggest_file_system(self):
        result = self.logger.suggest_recovery("file_system")
        assert result["severity"] == "high"

    def test_suggest_data_integrity(self):
        result = self.logger.suggest_recovery("data_integrity")
        assert result["playbook_id"] == "PB-DATA-VALIDATE"

    def test_suggest_unknown_category(self):
        result = self.logger.suggest_recovery("unknown_category")
        assert result["playbook_id"] is None
        assert result["severity"] == "unknown"


class TestTriggerPlaybook:
    def test_trigger_playbook_via_orchestrator(self, logger, monkeypatch):
        class FakeOrchestrator:
            def execute_playbook(self, playbook_id):
                return {"ok": True, "playbook_id": playbook_id}

        fake_module = types.SimpleNamespace(RecoveryOrchestrator=FakeOrchestrator)
        monkeypatch.setitem(sys.modules, "recovery_orchestrator", fake_module)

        result = logger.trigger_playbook("PB-NET-RETRY")

        assert result["triggered"] is True
        assert result["status"] == "executed"
        assert result["details"]["ok"] is True

    def test_trigger_playbook_script_fallback(self, logger, tmp_path, monkeypatch):
        recovery_dir = tmp_path / "recovery"
        recovery_dir.mkdir()
        script = recovery_dir / "pb-net-retry.py"
        script.write_text("# test script\n", encoding="utf-8")

        monkeypatch.delitem(sys.modules, "recovery_orchestrator", raising=False)
        monkeypatch.setattr(_el, "SCRIPT_DIR", tmp_path)

        result = logger.trigger_playbook("PB-NET-RETRY")

        assert result["triggered"] is True
        assert result["status"] == "pending"
        assert result["script_path"] == str(script)

    def test_trigger_playbook_manual_fallback_after_orchestrator_error(self, logger, monkeypatch):
        class BrokenOrchestrator:
            def execute_playbook(self, playbook_id):
                raise RuntimeError("orchestrator boom")

        fake_module = types.SimpleNamespace(RecoveryOrchestrator=BrokenOrchestrator)
        monkeypatch.setitem(sys.modules, "recovery_orchestrator", fake_module)
        monkeypatch.setattr(_el, "SCRIPT_DIR", Path(logger.errors_dir.parent))

        result = logger.trigger_playbook("PB-ANY")

        assert result["triggered"] is False
        assert result["status"] == "pending"
        assert "queued for manual execution" in result["message"]


class TestDetectPattern:
    def setup_method(self):
        self.logger = ErrorLogger()

    def test_detect_with_empty_history(self):
        result = self.logger.detect_pattern([])
        assert result["risk_level"] == "low"
        assert result["total_analyzed"] == 0

    def test_detect_recurring_error_type(self):
        errors = [
            {"type": "ConnectionError", "message": "timeout"},
            {"type": "ConnectionError", "message": "refused"},
            {"type": "ConnectionError", "message": "reset"},
        ]
        result = self.logger.detect_pattern(errors)
        assert result["risk_level"] == "medium"
        assert any(item["type"] == "ConnectionError" for item in result["recurring_types"])

    def test_detect_with_none_uses_index(self, logger):
        for i in range(3):
            logger.log_error({"type": "ConnectionError", "message": f"timeout {i}", "file": "net.py", "line": i})
        result = logger.detect_pattern(None)
        assert result["total_analyzed"] == 3
        assert result["dominant_category"] == "network"

    def test_detect_mixed_errors(self):
        errors = [
            {"type": "FileNotFoundError", "message": "config.yaml"},
            {"type": "ConnectionError", "message": "timeout"},
            {"type": "FileNotFoundError", "message": "data.json"},
        ]
        result = self.logger.detect_pattern(errors)
        assert isinstance(result, dict)
        assert result["total_analyzed"] == 3

    def test_detect_pattern_burst_and_critical_risk(self):
        errors = [
            _make_error("ConnectionError", minutes_ago=25, file_name="net.py"),
            _make_error("ConnectionError", minutes_ago=20, file_name="net.py"),
            _make_error("ConnectionError", minutes_ago=15, file_name="net.py"),
            _make_error("TimeoutError", minutes_ago=10, file_name="net.py"),
            _make_error("ConnectionError", minutes_ago=5, file_name="net.py"),
        ]
        result = self.logger.detect_pattern(errors)

        assert result["bursts"]
        assert result["risk_level"] == "critical"
        assert any("Error burst" in pattern for pattern in result["patterns_found"])
        assert any("Hot file: net.py" in pattern for pattern in result["patterns_found"])

    def test_detect_pattern_ignores_invalid_timestamps(self):
        errors = [
            {"type": "ValueError", "message": "bad input", "timestamp": "not-a-date", "file": "main.py"},
            {"type": "TypeError", "message": "wrong type", "timestamp": None, "file": "util.py"},
        ]
        result = self.logger.detect_pattern(errors)

        assert result["bursts"] == []
        assert result["risk_level"] == "low"
        assert result["patterns_found"] == ["No significant patterns detected"]


class TestClearResolvedAndConvenienceFunctions:
    def test_clear_resolved_removes_only_old_entries(self, logger):
        old_time = (datetime.now() - timedelta(days=40)).isoformat()
        new_time = (datetime.now() - timedelta(days=2)).isoformat()
        logger._write_index(
            {
                "errors": [
                    {"id": "ERR-old", "type": "ValueError", "resolved": True, "resolved_at": old_time},
                    {"id": "ERR-new", "type": "ValueError", "resolved": True, "resolved_at": new_time},
                    {"id": "ERR-bad", "type": "ValueError", "resolved": True, "resolved_at": "bad-date"},
                    {"id": "ERR-open", "type": "ValueError", "resolved": False, "resolved_at": None},
                ],
                "last_updated": None,
            }
        )

        removed = logger.clear_resolved(days_old=30)
        remaining_ids = {e["id"] for e in logger.get_all_errors()}

        assert removed == 1
        assert remaining_ids == {"ERR-new", "ERR-bad", "ERR-open"}

    def test_clear_resolved_returns_zero_when_nothing_removed(self, logger):
        logger._write_index(
            {
                "errors": [{"id": "ERR-open", "type": "ValueError", "resolved": False, "resolved_at": None}],
                "last_updated": None,
            }
        )
        assert logger.clear_resolved(days_old=30) == 0

    def test_convenience_functions_delegate_to_error_logger(self, monkeypatch):
        calls = []

        class DummyLogger:
            def log_error(self, error_data):
                calls.append(("log_error", error_data))
                return "ERR-dummy"

            def resolve_error(self, error_id):
                calls.append(("resolve_error", error_id))
                return True

            def get_unresolved_errors(self):
                calls.append(("get_unresolved_errors", None))
                return [{"id": "ERR-dummy"}]

            def generate_playbook_hint(self, error_data):
                calls.append(("generate_playbook_hint", error_data))
                return "PB-hint"

            def classify_error(self, error):
                calls.append(("classify_error", error))
                return "network"

            def suggest_recovery(self, error_class):
                calls.append(("suggest_recovery", error_class))
                return {"category": error_class}

            def trigger_playbook(self, playbook_id):
                calls.append(("trigger_playbook", playbook_id))
                return {"playbook_id": playbook_id}

            def detect_pattern(self, error_history=None):
                calls.append(("detect_pattern", error_history))
                return {"total_analyzed": len(error_history or [])}

        monkeypatch.setattr(_el, "ErrorLogger", DummyLogger)

        assert _el.log_error({"type": "X"}) == "ERR-dummy"
        assert _el.resolve_error("ERR-dummy") is True
        assert _el.get_unresolved_errors() == [{"id": "ERR-dummy"}]
        assert _el.generate_playbook_hint({"type": "X"}) == "PB-hint"
        assert _el.classify_error("timeout") == "network"
        assert _el.suggest_recovery("network") == {"category": "network"}
        assert _el.trigger_playbook("PB-1") == {"playbook_id": "PB-1"}
        assert _el.detect_pattern([{"type": "X"}]) == {"total_analyzed": 1}

        assert [name for name, _ in calls] == [
            "log_error",
            "resolve_error",
            "get_unresolved_errors",
            "generate_playbook_hint",
            "classify_error",
            "suggest_recovery",
            "trigger_playbook",
            "detect_pattern",
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])