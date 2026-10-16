#!/usr/bin/env python3
"""
QAWIN-RUNTIME: contratos de hardening de runtime OpenCode basados en QA
Windows 10/11 (feedback N30). Tests de contrato simulados en Linux — NO
prueban ejecución nativa de Windows.

Cubre:
  1. Gate de versión >= 1.18.0 (fail-closed) para todo launch PA-owned.
  2. data/user/model-selection.json como fuente canónica en los launch/
     preflight paths (fallback legacy .opencode/config.json).
  3. Superficies PA (menú M del panel + /api/models/free) solo modelos free.
  4. Windows/manual: subprocess argv, sin shell=True, returncode → menú.
Run: pytest tests/test_windows_qa_runtime.py -v
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {name}")
    mod = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return mod


sfm = _load("sfm_qawin", SCRIPTS / "select_free_model.py")
pa = _load("pa_qawin", SCRIPTS / "pa.py")


def _write_selection(root: Path, model: str) -> None:
    (root / "data" / "user").mkdir(parents=True, exist_ok=True)
    (root / "data" / "user" / "model-selection.json").write_text(
        json.dumps({"model": model}), encoding="utf-8"
    )


def _write_legacy(root: Path, model: str, agent: str = "FreakingJSON") -> None:
    (root / ".opencode").mkdir(parents=True, exist_ok=True)
    (root / ".opencode" / "config.json").write_text(
        json.dumps({"agent": agent, "model": model}), encoding="utf-8"
    )


def _fake_opencode(monkeypatch, output: str, code: int = 0, tag: str = "base"):
    """Script ejecutable 'opencode' falso: imprime output y sale con code."""
    base = Path(f"/tmp/qawin-{tag}")
    fake = base / "opencode"
    base.mkdir(parents=True, exist_ok=True)
    script = f"#!/usr/bin/env python3\nimport sys\nprint({output!r})\nsys.exit({code})\n"
    fake.write_text(script, encoding="utf-8")
    fake.chmod(0o755)
    return fake


# ------------------------------------------------------- version gate -------

def test_version_1_17_9_rejected(monkeypatch):
    fake = _fake_opencode(monkeypatch, "opencode 1.17.9 (build xyz)")
    ok, msg = sfm.enforce_opencode_version(exe=str(fake))
    assert ok is False
    assert "npm install -g opencode-ai@latest" in msg


def test_version_1_18_0_accepted(monkeypatch):
    fake = _fake_opencode(monkeypatch, "opencode 1.18.0")
    ok, msg = sfm.enforce_opencode_version(exe=str(fake))
    assert ok is True, msg


def test_version_newer_accepted(monkeypatch):
    fake = _fake_opencode(monkeypatch, "opencode 1.20.3 (build ok)")
    ok, msg = sfm.enforce_opencode_version(exe=str(fake))
    assert ok is True, msg


def test_version_malformed_rejected(monkeypatch):
    fake = _fake_opencode(monkeypatch, "opencode version unknown??")
    ok, msg = sfm.enforce_opencode_version(exe=str(fake))
    assert ok is False
    assert "npm install -g opencode-ai@latest" in msg


def test_version_nonzero_exit_rejected(monkeypatch):
    fake = _fake_opencode(monkeypatch, "1.18.0", code=1, tag="fail")
    ok, msg = sfm.enforce_opencode_version(exe=str(fake))
    assert ok is False
    assert "npm install -g opencode-ai@latest" in msg


def test_outdated_gate_spawns_no_serve(monkeypatch):
    fake = _fake_opencode(monkeypatch, "1.17.9", tag="oldsrv")

    def _no_popen(*a, **k):
        raise AssertionError("gate debe fallar antes de spawn")

    monkeypatch.setattr(sfm.subprocess, "Popen", _no_popen)
    monkeypatch.setattr(sfm.shutil, "which",
                        lambda n: str(fake) if n == "opencode" else None)
    assert sfm.ensure_opencode_serve() is None


# ------------------------------------------------ selection resolution ------

def test_build_cli_command_prefers_data_selection_over_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    _write_legacy(tmp_path, "opencode/big-pickle")
    _write_selection(tmp_path, "opencode/glm-5.3-free")
    cmd, inject = pa.build_cli_command("opencode", "hola", tmp_path)
    assert inject is True
    assert cmd[cmd.index("--model") + 1] == "opencode/glm-5.3-free"
    assert "big-pickle" not in cmd
    assert cmd[cmd.index("--agent") + 1] == "FreakingJSON"


def test_build_cli_command_falls_back_to_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    _write_legacy(tmp_path, "opencode/big-pickle")
    cmd, _ = pa.build_cli_command("opencode", "hola", tmp_path)
    assert cmd[cmd.index("--model") + 1] == "opencode/big-pickle"


def test_preflight_uses_data_selection_model(tmp_path, monkeypatch):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    _write_legacy(tmp_path, "opencode/big-pickle")
    _write_selection(tmp_path, "opencode/glm-5.3-free")
    seen = {}

    def fake_run(argv, **k):
        seen["argv"] = argv

        class R:
            returncode = 0
            stdout = "VERIFY_OK: ok"
            stderr = ""
        return R()

    monkeypatch.setattr(pa.subprocess, "run", fake_run)
    pa._preflight_model_check()
    joined = " ".join(seen["argv"])
    assert "--verify" in joined
    assert "opencode/glm-5.3-free" in joined
    assert "big-pickle" not in joined


def test_submenu_display_reads_selection_first(tmp_path, monkeypatch):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    _write_legacy(tmp_path, "opencode/big-pickle")
    _write_selection(tmp_path, "opencode/glm-5.3-free")
    assert pa._current_selected_model_display(tmp_path) == "opencode/glm-5.3-free"


# ------------------------------------------------- free-only PA surfaces ----

def test_pa_menu_uses_free_only_list(monkeypatch, tmp_path):
    recorded = {}

    class _FakeSfm:
        @staticmethod
        def get_free_models(port, timeout=25):
            recorded["fn"] = "free"
            return [{"id": "opencode/glm-5.3-free", "status": "anon", "free": True}]

        @staticmethod
        def get_usable_models(port, timeout=25):
            recorded["fn"] = "usable"
            return [{"id": "zai-coding-plan/glm-5.3", "status": "authed_file",
                     "free": False}]

        @staticmethod
        def ensure_opencode_serve():
            return 47017

        @staticmethod
        def save_selection(mid, *a, **k):
            recorded["saved"] = mid

    monkeypatch.setitem(sys.modules, "select_free_model", _FakeSfm)
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    pa._select_free_model()
    assert recorded["fn"] == "free", recorded
    assert recorded["saved"] == "opencode/glm-5.3-free"


def test_api_models_free_endpoint_uses_free_only(tmp_path, monkeypatch):
    import dashboard_server as ds
    calls = {}

    def fake_free(port, *a, **k):
        calls["fn"] = "free"
        return [{"id": "opencode/glm-5.3-free", "status": "anon", "free": True}]

    def fake_usable(*a, **k):
        calls["fn"] = "usable"
        return []

    monkeypatch.setattr(ds.sfm, "get_free_models", fake_free)
    monkeypatch.setattr(ds.sfm, "get_usable_models", fake_usable)
    (tmp_path / "dashboard.html").write_text("<html>ok</html>", encoding="utf-8")
    handler = object.__new__(ds.Handler)
    handler.path = "/api/models/free"

    class FakeServer:
        repo_root = tmp_path
        token_required = False
        server_address = ("127.0.0.1", 0)

        def current_token(self):
            return "tok"

    handler.server = FakeServer()
    sent = {}
    handler._json = lambda obj, status=200: sent.update(obj=obj, status=status)
    handler.do_GET()
    assert calls["fn"] == "free", calls
    assert sent["obj"][0]["id"] == "opencode/glm-5.3-free"


# ---------------------------------------------- windows / manual launches ---

def test_manual_opencode_uses_argv_no_shell(tmp_path, monkeypatch):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    fake = _fake_opencode(monkeypatch, "1.20.3", tag="manual")
    seen = {}

    def fake_run(argv, cwd=None, check=False, **k):
        seen["argv"] = argv
        seen["shell"] = k.get("shell", False)

        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(pa.subprocess, "run", fake_run)
    # Este contrato prueba argv/returncode; el gate tiene pruebas propias.
    # subprocess es compartido y parchear run también afectaría sfm.
    monkeypatch.setattr(pa, "_enforce_opencode_gate", lambda _exe: True)
    monkeypatch.setattr(pa.shutil, "which",
                        lambda n: str(fake) if n == "opencode" else None)
    code = pa._run_cli_interactive("opencode")
    assert seen["shell"] is False
    assert isinstance(seen["argv"], list)
    assert seen["argv"][0] == str(fake)
    assert code == 0


def test_manual_opencode_nonzero_returns_to_menu(tmp_path, monkeypatch):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    fake = _fake_opencode(monkeypatch, "1.20.3", tag="crash")
    printed = []
    monkeypatch.setattr(pa, "print_warn", lambda m: printed.append(m))
    monkeypatch.setattr(pa.shutil, "which",
                        lambda n: str(fake) if n == "opencode" else None)

    def fake_run(argv, cwd=None, check=False, **k):
        class R:
            returncode = 4294967295
        return R()

    monkeypatch.setattr(pa.subprocess, "run", fake_run)
    monkeypatch.setattr(pa, "_enforce_opencode_gate", lambda _exe: True)
    code = pa._run_cli_interactive("opencode")
    assert code == 4294967295
    joined = " ".join(printed).lower()
    assert "4294967295" in joined or "0xffffffff" in joined


def test_manual_opencode_outdated_gate_blocks_launch(tmp_path, monkeypatch):
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    fake = _fake_opencode(monkeypatch, "1.17.9", tag="old")

    def no_spawn(*a, **k):
        raise AssertionError("no debe spawnear con gate desactualizado")

    monkeypatch.setattr(pa.subprocess, "run", no_spawn)
    monkeypatch.setattr(pa.subprocess, "Popen", no_spawn)
    monkeypatch.setattr(pa.shutil, "which",
                        lambda n: str(fake) if n == "opencode" else None)
    assert pa._run_cli_interactive("opencode") is None


def test_auto_opencode_outdated_gate_blocks_launch(tmp_path, monkeypatch):
    fake = _fake_opencode(monkeypatch, "1.17.9", tag="old-auto")
    monkeypatch.setattr(pa.shutil, "which",
                        lambda n: str(fake) if n == "opencode" else None)
    calls = {"gate": 0, "spawn": 0}

    def reject_gate(_exe):
        calls["gate"] += 1
        return False

    def record_spawn(*a, **k):
        calls["spawn"] += 1
        raise AssertionError("auto-launch no debe ejecutar OpenCode desactualizado")

    monkeypatch.setattr(pa, "_enforce_opencode_gate", reject_gate)
    monkeypatch.setattr(pa, "_preflight_model_check", lambda: None)
    monkeypatch.setattr(pa.subprocess, "run", record_spawn)
    assert pa.try_auto_launch_cli("opencode", "hola", tmp_path) is False
    assert calls == {"gate": 1, "spawn": 0}


def test_launch_tui_uses_selection_not_legacy(tmp_path, monkeypatch):
    import dashboard_server as ds
    monkeypatch.setattr(ds, "REPO_ROOT", tmp_path)
    _write_legacy(tmp_path, "opencode/big-pickle")
    _write_selection(tmp_path, "opencode/glm-5.3-free")
    fake = _fake_opencode(monkeypatch, "1.20.3", tag="tui")
    spawned = {}

    def fake_popen(argv, **k):
        spawned["argv"] = argv
        spawned["shell"] = k.get("shell", False)

        class R:
            pid = 1
        return R()

    monkeypatch.setattr(ds.subprocess, "Popen", fake_popen)
    # Popen es compartido por subprocess.run; aislar el gate en este contrato.
    monkeypatch.setattr(ds.sfm, "enforce_opencode_version",
                        lambda _exe: (True, "OpenCode OK"))
    monkeypatch.setattr(
        ds.shutil, "which",
        lambda n: n if n == "x-terminal-emulator" else None)
    monkeypatch.setattr(ds.sys, "platform", "linux")
    monkeypatch.setattr(ds, "opencode_installed", lambda: str(fake))
    result = ds.launch_opencode_tui()
    assert result["ok"] is True, result
    argv_str = " ".join(spawned["argv"])
    assert "big-pickle" not in argv_str
    assert "--agent" in argv_str
    assert "FreakingJSON" in argv_str
    if "--model" in argv_str:
        assert "glm-5.3-free" in argv_str


def test_dashboard_opencode_ensure_gate_blocks_serve(tmp_path, monkeypatch):
    import dashboard_server as ds
    fake = _fake_opencode(monkeypatch, "1.17.9", tag="ensure")
    monkeypatch.setattr(ds, "opencode_installed", lambda: str(fake))

    def no_spawn(*a, **k):
        raise AssertionError("gate desactualizado debe bloquear Popen")

    monkeypatch.setattr(ds.subprocess, "Popen", no_spawn)
    monkeypatch.setattr(ds.time, "sleep", lambda *_: None)
    with patch.object(ds, "opencode_serving", side_effect=[False] * 40):
        result = ds.opencode_ensure()
    assert result["ok"] is False
    assert "npm install -g opencode-ai@latest" in result["error"]


def test_select_free_model_ensure_gate_blocks_serve(monkeypatch):
    fake = _fake_opencode(monkeypatch, "1.17.9", tag="sfm")
    monkeypatch.setattr(sfm.shutil, "which",
                        lambda n: str(fake) if n == "opencode" else None)

    def no_spawn(*a, **k):
        raise AssertionError("gate desactualizado debe bloquear Popen")

    monkeypatch.setattr(sfm.subprocess, "Popen", no_spawn)
    assert sfm.ensure_opencode_serve() is None
