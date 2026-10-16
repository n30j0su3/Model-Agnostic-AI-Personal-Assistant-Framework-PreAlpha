from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def _load_module(name: str, path: Path):
    assert path.exists(), f"missing module: {path.name}"
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_startup_scripts_do_not_gate_utf8_on_isatty():
    offenders = []
    forbidden = 'sys.platform == "win32" and sys.stdout.isatty()'
    for path in sorted(SCRIPTS.glob("*.py")):
        if forbidden in path.read_text(encoding="utf-8"):
            offenders.append(path.name)

    assert offenders == []


def test_session_start_prints_24_hour_time(monkeypatch, capsys):
    session_start = _load_module("session_start_time_test", SCRIPTS / "session_start.py")

    class _FrozenDateTime:
        @classmethod
        def now(cls):
            return datetime(2026, 10, 16, 16, 27)

    monkeypatch.setattr(session_start, "datetime", _FrozenDateTime)
    session_start.print_session_start(
        {
            "cli_summary": (0, []),
            "all_skills": [],
            "kb_summary": {"available": False},
            "pending_count": 0,
            "last_session": "Sin sesión anterior",
            "_parallel_time": 0,
        }
    )

    output = capsys.readouterr().out
    assert "[TIME] 16:27" in output
    assert "[TIME] H:27" not in output
