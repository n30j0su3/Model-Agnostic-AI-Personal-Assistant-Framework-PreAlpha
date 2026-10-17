"""Pi is an explicit opt-in runtime; OpenCode remains implicit default."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import assert_private_file


SCRIPTS = Path(__file__).resolve().parents[1] / "core/scripts"
sys.path.insert(0, str(SCRIPTS))

from pi_adapter import PiAdapter, WizardSettings  # noqa: E402


INSTALL_COMMAND = (
    "npm install -g --ignore-scripts @earendil-works/pi-coding-agent"
)


def test_detect_pi_missing_does_not_suggest_runtime_change():
    adapter = PiAdapter(pi_path=None)

    assert adapter.detect() == {
        "installed": False,
        "install_cmd": INSTALL_COMMAND,
    }
    assert adapter.suggested_runtime_change() is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"state": "ready"}, "ready"),
        ({"state": "not_ready"}, "not_ready"),
        ({"state": "invalid"}, "invalid"),
        ({"state": "future-value"}, "invalid"),
    ],
)
def test_auth_check_parses_documented_states(raw, expected):
    assert PiAdapter.parse_auth_check(raw) == expected


def test_credential_status_uses_scriptable_auth_contract(monkeypatch):
    recorded = {}

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, json.dumps({"state": "ready"}), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    adapter = PiAdapter(pi_path="/usr/bin/pi")

    assert adapter.credential_status() == "ready"
    assert recorded["command"] == [
        "/usr/bin/pi",
        "auth",
        "check",
        "--provider",
        "opencode",
        "--json",
    ]
    assert recorded["kwargs"]["shell"] is False


def test_spawn_uses_print_mode_model_and_ephemeral_key(monkeypatch):
    recorded = {}

    class FakeProcess:
        pass

    def fake_popen(command, **kwargs):
        recorded["command"] = command
        recorded["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    adapter = PiAdapter(pi_path="/usr/bin/pi")

    process = adapter.spawn_chat(
        "hola",
        model="opencode/test-free",
        opencode_api_key="test-only-key",
    )

    assert isinstance(process, FakeProcess)
    assert recorded["command"] == [
        "/usr/bin/pi",
        "--print",
        "hola",
        "--model",
        "opencode/test-free",
    ]
    assert not any("models.json" in value for value in recorded["command"])
    assert recorded["kwargs"]["env"]["OPENCODE_API_KEY"] == "test-only-key"
    assert recorded["kwargs"]["shell"] is False


def test_wizard_requires_explicit_choice_and_preserves_default(tmp_path):
    settings = WizardSettings(tmp_path)

    assert settings.get("runtime") is None
    assert settings.effective_runtime() == "opencode"
    with pytest.raises(ValueError, match="confirmation"):
        settings.choose_runtime("pi", confirm=False)
    assert not settings.path.exists()

    settings.choose_runtime("pi", confirm=True)

    assert settings.get("runtime") == "pi"
    assert settings.backup()["previous"] == "opencode"
    assert_private_file(settings.path)


def test_wizard_rejects_unknown_runtime(tmp_path):
    settings = WizardSettings(tmp_path)

    with pytest.raises(ValueError, match="unsupported runtime"):
        settings.choose_runtime("unknown", confirm=True)
