"""
Unit tests for core/recovery/ — Self-Healing Engine
====================================================

Covers:
    - triggers.detect_error_type()
    - triggers.should_trigger_recovery()
    - orchestrator.RecoveryOrchestrator.match_playbook()
    - orchestrator.RecoveryOrchestrator.execute_playbook()
    - orchestrator.RecoveryOrchestrator.recover()
    - orchestrator.RecoveryOrchestrator.register_action()
    - orchestrator.RecoveryOrchestrator.history
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so ``core.recovery`` resolves
# ---------------------------------------------------------------------------
import sys

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.recovery.triggers import (
    KEYWORD_PATTERNS,
    SKIP_RECOVERY_TYPES,
    TAXONOMY_MAP,
    detect_error_type,
    should_trigger_recovery,
)
from core.recovery.orchestrator import (
    CATEGORY_TO_PLAYBOOKS,
    RecoveryOrchestrator,
)


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def tmp_playbooks_dir(tmp_path):
    """Create a temporary playbooks directory with a minimal index.json."""
    playbooks = tmp_path / "playbooks"
    playbooks.mkdir()
    index_data = {
        "version": "1.0.0",
        "playbooks": [
            {
                "id": "PB-001",
                "name": "encoding-errors",
                "keywords": ["UnicodeEncodeError", "charmap", "codec", "utf-8", "encoding"],
            },
            {
                "id": "PB-002",
                "name": "file-not-found",
                "keywords": ["FileNotFoundError", "PermissionError", "path", "file"],
            },
            {
                "id": "PB-004",
                "name": "subprocess-timeout",
                "keywords": ["TimeoutExpired", "subprocess", "timeout", "hang"],
            },
        ],
    }
    (playbooks / "index.json").write_text(json.dumps(index_data), encoding="utf-8")
    return playbooks


@pytest.fixture
def orchestrator(tmp_playbooks_dir):
    """Return a RecoveryOrchestrator pointed at the temp playbooks dir."""
    return RecoveryOrchestrator(playbooks_dir=tmp_playbooks_dir)


# ===================================================================
# detect_error_type
# ===================================================================

class TestDetectErrorType:
    """Tests for triggers.detect_error_type()."""

    # --- Exception instance inputs ---

    def test_connection_error_is_network(self):
        assert detect_error_type(ConnectionError("refused")) == "network"

    def test_timeout_error_is_network(self):
        assert detect_error_type(TimeoutError("timed out")) == "network"

    def test_file_not_found_is_file_system(self):
        assert detect_error_type(FileNotFoundError("missing.txt")) == "file_system"

    def test_permission_error_is_file_system(self):
        assert detect_error_type(PermissionError("denied")) == "file_system"

    def test_unicode_encode_is_data_integrity(self):
        assert detect_error_type(UnicodeEncodeError("utf-8", "", 0, 1, "test")) == "data_integrity"

    def test_unicode_decode_is_data_integrity(self):
        assert detect_error_type(UnicodeDecodeError("utf-8", b"", 0, 1, "test")) == "data_integrity"

    def test_json_decode_is_data_integrity(self):
        assert detect_error_type(json.JSONDecodeError("msg", "doc", 0)) == "data_integrity"

    def test_value_error_is_data_integrity(self):
        assert detect_error_type(ValueError("bad value")) == "data_integrity"

    def test_type_error_is_data_integrity(self):
        assert detect_error_type(TypeError("wrong type")) == "data_integrity"

    def test_memory_error_is_resource(self):
        assert detect_error_type(MemoryError()) == "resource"

    def test_import_error_is_resource(self):
        assert detect_error_type(ImportError("no module")) == "resource"

    def test_os_error_is_file_system(self):
        assert detect_error_type(OSError("broken")) == "file_system"

    # --- Dict inputs ---

    def test_dict_with_known_type(self):
        assert detect_error_type({"type": "FileNotFoundError", "message": "nope"}) == "file_system"

    def test_dict_with_unknown_type_keyword_match(self):
        assert detect_error_type({"type": "CustomError", "message": "connection refused"}) == "network"

    # --- String inputs (keyword fallback) ---

    def test_string_network_keyword(self):
        assert detect_error_type("connection timed out") == "network"

    def test_string_api_keyword(self):
        assert detect_error_type("status 404 not found") == "api"

    def test_string_file_system_keyword(self):
        assert detect_error_type("no such file or directory") == "file_system"

    def test_string_authentication_keyword(self):
        assert detect_error_type("invalid credentials provided") == "authentication"

    def test_string_configuration_keyword(self):
        assert detect_error_type("config file is malformed") == "configuration"

    def test_string_data_integrity_keyword(self):
        assert detect_error_type("json parse error near line 5") == "data_integrity"

    def test_string_resource_keyword(self):
        assert detect_error_type("subprocess failed to start") == "resource"

    def test_string_unknown_no_match(self):
        assert detect_error_type("something completely unexpected") == "unknown"

    def test_empty_string_is_unknown(self):
        assert detect_error_type("") == "unknown"


# ===================================================================
# should_trigger_recovery
# ===================================================================

class TestShouldTriggerRecovery:

    def test_connection_error_triggers(self):
        assert should_trigger_recovery(ConnectionError("refused")) is True

    def test_keyboard_interrupt_skipped(self):
        assert should_trigger_recovery(KeyboardInterrupt()) is False

    def test_syntax_error_skipped(self):
        assert should_trigger_recovery(SyntaxError("bad syntax")) is False

    def test_assertion_error_skipped(self):
        assert should_trigger_recovery(AssertionError()) is False

    def test_system_exit_skipped(self):
        assert should_trigger_recovery(SystemExit(1)) is False

    def test_not_implemented_skipped(self):
        assert should_trigger_recovery(NotImplementedError()) is False

    def test_dict_with_skip_type_skipped(self):
        assert should_trigger_recovery({"type": "KeyboardInterrupt", "message": "ctrl+c"}) is False

    def test_dict_normal_triggers(self):
        assert should_trigger_recovery({"type": "ValueError", "message": "bad"}) is True

    def test_empty_string_skipped(self):
        assert should_trigger_recovery("") is False

    def test_whitespace_string_skipped(self):
        assert should_trigger_recovery("   ") is False

    def test_nonempty_string_triggers(self):
        assert should_trigger_recovery("something broke") is True


# ===================================================================
# RecoveryOrchestrator.match_playbook
# ===================================================================

class TestMatchPlaybook:

    def test_unicode_error_matches_pb001(self, orchestrator):
        pb = orchestrator.match_playbook(UnicodeEncodeError("charmap", "", 0, 1, "undef"))
        assert pb == "PB-001"

    def test_file_not_found_matches_pb002(self, orchestrator):
        pb = orchestrator.match_playbook(FileNotFoundError("nope.txt"))
        assert pb == "PB-002"

    def test_timeout_matches_pb004(self, orchestrator):
        pb = orchestrator.match_playbook(TimeoutError("timed out"))
        assert pb == "PB-004"

    def test_keyword_fallback_match(self, orchestrator):
        """An unknown exception type but matching keywords should find a playbook."""
        pb = orchestrator.match_playbook("subprocess hang detected")
        assert pb == "PB-004"

    def test_no_match_returns_none(self, orchestrator):
        pb = orchestrator.match_playbook("everything is fine")
        assert pb is None

    def test_skip_error_returns_none(self, orchestrator):
        pb = orchestrator.match_playbook(KeyboardInterrupt())
        assert pb is None

    def test_dict_error_matches(self, orchestrator):
        pb = orchestrator.match_playbook({"type": "FileNotFoundError", "message": "missing"})
        assert pb == "PB-002"

    def test_category_resource_maps_to_pb004(self, orchestrator):
        """MemoryError maps to resource category → PB-004."""
        # MemoryError() has empty message, so use dict form to bypass trigger check
        pb = orchestrator.match_playbook({"type": "MemoryError", "message": "cannot allocate memory"})
        assert pb == "PB-004"

    def test_category_data_integrity_prefers_pb001(self, orchestrator):
        pb = orchestrator.match_playbook(UnicodeDecodeError("utf-8", b"", 0, 1, "err"))
        assert pb == "PB-001"


# ===================================================================
# RecoveryOrchestrator.execute_playbook
# ===================================================================

class TestExecutePlaybook:

    def test_execute_pb002_creates_file(self, orchestrator, tmp_path):
        target = tmp_path / "subdir" / "newfile.txt"
        result = orchestrator.execute_playbook(
            "PB-002", {"file_path": str(target)}
        )
        assert result["status"] == "success"
        assert target.exists()

    def test_execute_pb003_json_cleanup(self, orchestrator):
        bad_json = '\ufeff{"a": 1,}'
        result = orchestrator.execute_playbook(
            "PB-003", {"raw_content": bad_json}
        )
        assert result["status"] == "success"

    def test_execute_pb004_retry_signal(self, orchestrator):
        result = orchestrator.execute_playbook(
            "PB-004", {"retry_count": 0, "max_retries": 3}
        )
        assert result["status"] == "success"

    def test_execute_pb004_max_retries_exceeded(self, orchestrator):
        result = orchestrator.execute_playbook(
            "PB-004", {"retry_count": 3, "max_retries": 3}
        )
        assert result["status"] == "failed"

    def test_execute_pb005_path_resolution(self, orchestrator, tmp_path):
        real_file = tmp_path / "exists.txt"
        real_file.write_text("hi", encoding="utf-8")
        ctx = {"file_path": "exists.txt", "base_dir": str(tmp_path)}
        result = orchestrator.execute_playbook("PB-005", ctx)
        assert result["status"] == "success"
        # Action stores resolved_path in the context dict by reference
        assert "resolved_path" in ctx

    def test_execute_unknown_playbook(self, orchestrator):
        result = orchestrator.execute_playbook("PB-999")
        assert result["status"] == "no_action"
        assert "PB-999" in result["message"]

    def test_execute_pb001_encoding_success(self, orchestrator, tmp_path):
        good_file = tmp_path / "ok.txt"
        good_file.write_text("hello", encoding="utf-8")
        result = orchestrator.execute_playbook(
            "PB-001", {"file_path": str(good_file)}
        )
        assert result["status"] == "success"

    def test_execute_pb006_yaml_fallback(self, orchestrator):
        result = orchestrator.execute_playbook(
            "PB-006", {"fallback_defaults": {"key": "value"}}
        )
        assert result["status"] == "success"

    def test_execute_pb006_no_fallback(self, orchestrator):
        result = orchestrator.execute_playbook("PB-006", {})
        assert result["status"] == "failed"

    def test_execute_pb007_git_retry(self, orchestrator):
        result = orchestrator.execute_playbook("PB-007", {"retry_count": 0})
        assert result["status"] == "success"

    def test_execute_pb008_multi_cli(self, orchestrator):
        result = orchestrator.execute_playbook("PB-008", {"retry_count": 0})
        assert result["status"] == "success"


# ===================================================================
# RecoveryOrchestrator.recover (end-to-end)
# ===================================================================

class TestRecover:

    def test_recover_file_not_found(self, orchestrator, tmp_path):
        target = tmp_path / "auto_created.txt"
        result = orchestrator.recover(
            FileNotFoundError(str(target)),
            {"file_path": str(target)},
        )
        assert result["status"] == "success"
        assert target.exists()

    def test_recover_skip_error(self, orchestrator):
        result = orchestrator.recover(KeyboardInterrupt())
        assert result["status"] == "skipped"

    def test_recover_no_match(self, orchestrator):
        result = orchestrator.recover("everything is fine")
        assert result["status"] == "no_match"


# ===================================================================
# RecoveryOrchestrator.register_action & history
# ===================================================================

class TestRegisterAction:

    def test_register_custom_action(self, orchestrator):
        called = {"value": False}

        def custom(ctx):
            called["value"] = True
            return True

        orchestrator.register_action("PB-CUSTOM", custom)
        result = orchestrator.execute_playbook("PB-CUSTOM", {})
        assert result["status"] == "success"
        assert called["value"] is True

    def test_override_existing_action(self, orchestrator):
        def always_fail(ctx):
            return False

        orchestrator.register_action("PB-001", always_fail)
        result = orchestrator.execute_playbook("PB-001", {})
        assert result["status"] == "failed"


class TestHistory:

    def test_history_records_executions(self, orchestrator):
        orchestrator.execute_playbook("PB-004", {"retry_count": 0, "max_retries": 3})
        orchestrator.execute_playbook("PB-004", {"retry_count": 3, "max_retries": 3})
        assert len(orchestrator.history) == 2
        assert orchestrator.history[0]["status"] == "success"
        assert orchestrator.history[1]["status"] == "failed"

    def test_history_is_copy(self, orchestrator):
        orchestrator.execute_playbook("PB-004", {"retry_count": 0, "max_retries": 3})
        h = orchestrator.history
        h.clear()
        assert len(orchestrator.history) == 1  # original unchanged


# ===================================================================
# Edge cases
# ===================================================================

class TestEdgeCases:

    def test_no_index_file_does_not_crash(self, tmp_path):
        empty_dir = tmp_path / "empty_playbooks"
        empty_dir.mkdir()
        orch = RecoveryOrchestrator(playbooks_dir=empty_dir)
        # Should still classify via taxonomy even without index
        pb = orch.match_playbook(FileNotFoundError("x"))
        assert pb == "PB-002"

    def test_malformed_index_handled(self, tmp_path):
        bad_dir = tmp_path / "bad_playbooks"
        bad_dir.mkdir()
        (bad_dir / "index.json").write_text("NOT JSON", encoding="utf-8")
        orch = RecoveryOrchestrator(playbooks_dir=bad_dir)
        pb = orch.match_playbook(FileNotFoundError("x"))
        assert pb == "PB-002"

    def test_action_exception_is_caught(self, orchestrator):
        def bad_action(ctx):
            raise RuntimeError("boom")

        orchestrator.register_action("PB-BOOM", bad_action)
        result = orchestrator.execute_playbook("PB-BOOM")
        assert result["status"] == "failed"
        assert "RuntimeError" in result["message"]

    def test_all_taxonomy_categories_mapped(self):
        """Every ADR-004 category has at least an empty list entry."""
        expected = {"network", "api", "file_system", "authentication",
                    "configuration", "data_integrity", "resource"}
        assert set(CATEGORY_TO_PLAYBOOKS.keys()) == expected

    def test_detect_error_type_all_taxonomymap_categories_valid(self):
        """Every value in TAXONOMY_MAP is a valid ADR-004 category."""
        valid = {"network", "api", "file_system", "authentication",
                 "configuration", "data_integrity", "resource", "unknown"}
        for exc_name, category in TAXONOMY_MAP.items():
            assert category in valid, f"{exc_name} maps to invalid category {category}"
