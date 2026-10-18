"""W3 contracts: scheduled and directly invoked scripts must not crash on
Unicode status glyphs when the console uses a legacy code page (cp1252).
"""
from __future__ import annotations

import importlib.util
import io
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


def _cp1252_stream() -> io.TextIOWrapper:
    return io.TextIOWrapper(io.BytesIO(), encoding="cp1252", write_through=True)


def test_helper_switches_legacy_streams_to_utf8_with_replacement(monkeypatch):
    console = _load("console_encoding_w3", SCRIPTS / "console_encoding.py")
    out, err = _cp1252_stream(), _cp1252_stream()
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)

    console.configure_utf8_console()

    assert out.encoding == "utf-8"
    assert err.encoding == "utf-8"
    print("\u2713 check", file=sys.stdout)  # would raise UnicodeEncodeError on cp1252


def test_helper_tolerates_streams_without_reconfigure(monkeypatch):
    console = _load("console_encoding_w3_missing", SCRIPTS / "console_encoding.py")
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", io.StringIO())

    console.configure_utf8_console()  # must not raise


def test_self_healing_run_survives_legacy_code_page(tmp_path, monkeypatch):
    healing = _load("self_healing_w3", SCRIPTS / "self_healing_check.py")
    monkeypatch.setattr(healing, "ERROR_LOG_PATH", tmp_path / "error-log.json")
    monkeypatch.setattr(sys, "stdout", _cp1252_stream())
    monkeypatch.setattr(sys, "stderr", _cp1252_stream())
    monkeypatch.setattr(sys, "argv", ["self_healing_check.py", "--run"])

    healing.main()  # RED on baseline: UnicodeEncodeError on '\u2713'
