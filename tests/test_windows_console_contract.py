"""Subprocess contracts for legacy cp1252 console safety."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def test_context_loader_prints_utf8_fixture_under_cp1252(tmp_path):
    fixture = tmp_path / "AGENTS-lite.md"
    fixture.write_bytes(b"# Bootstrap\nstatus: \xe2\x9c\x85\n")
    program = (
        "import sys; "
        "from pathlib import Path; "
        "sys.path.insert(0, sys.argv[1]); "
        "from context_loader import ContextLoader; "
        "print(ContextLoader(repo_root=Path(sys.argv[2])).load_tier(0)['content'])"
    )
    env = os.environ.copy()
    env.update({"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"})

    completed = subprocess.run(
        [sys.executable, "-c", program, str(SCRIPTS), str(tmp_path)],
        capture_output=True,
        env=env,
        timeout=15,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    assert b"UnicodeEncodeError" not in completed.stderr
