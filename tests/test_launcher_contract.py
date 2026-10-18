"""W6.1 contract: the POSIX launcher must be LF-only, executable and runnable.

The release ZIP preserves Git modes. A `pa.sh` tracked as 100644 with CRLF
therefore ships as a non-executable script that fails before Python starts.
"""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PA_SH = ROOT / "pa.sh"

pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX launcher contract is not applicable on native Windows",
)


def test_pa_sh_has_no_carriage_returns():
    payload = PA_SH.read_bytes()
    assert b"\r" not in payload, "pa.sh must use LF line endings (no CRLF)"


def test_pa_sh_is_executable():
    mode = stat.S_IMODE(PA_SH.stat().st_mode)
    assert mode & 0o111, f"pa.sh must be executable, got {oct(mode)}"


def test_pa_sh_parses_with_bash():
    result = subprocess.run(
        ["bash", "-n", str(PA_SH)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_pa_sh_help_smoke():
    result = subprocess.run(
        [str(PA_SH), "--help"],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PA Framework Control Panel" in result.stdout


def test_pa_sh_version_smoke():
    result = subprocess.run(
        [str(PA_SH), "--version"],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0.4.1-beta" in result.stdout
