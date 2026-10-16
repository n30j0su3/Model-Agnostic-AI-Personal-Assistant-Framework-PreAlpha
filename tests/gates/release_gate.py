#!/usr/bin/env python3
"""Fail-fast executable release gate R1–R12 for PA Framework v0.4.1."""

from __future__ import annotations

import argparse
import io
import json
import os
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


class GateFailure(RuntimeError):
    pass


def run(
    name: str,
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path = ROOT,
) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    output_lines = [line for line in result.stdout.splitlines() if line.strip()]
    receipt = {
        "gate": name,
        "command": command,
        "returncode": result.returncode,
        "summary": output_lines[-1] if output_lines else "",
    }
    if result.returncode != 0:
        raise GateFailure(
            json.dumps({**receipt, "stdout": result.stdout[-8000:], "stderr": result.stderr[-8000:]})
        )
    return receipt


def pytest_gate(
    name: str,
    *paths: str,
    env: dict[str, str] | None = None,
    cwd: Path = ROOT,
) -> dict[str, Any]:
    return run(name, [PYTHON, "-m", "pytest", *paths, "-q"], env=env, cwd=cwd)


def fresh_extract_gate() -> dict[str, Any]:
    """R1: run the complete suite from the exact staged Git tree."""
    tree = subprocess.run(
        ["git", "write-tree"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    archive = subprocess.run(
        ["git", "archive", tree], cwd=ROOT, capture_output=True, check=True
    ).stdout
    with tempfile.TemporaryDirectory(prefix="pa-release-r1-") as temp:
        extracted = Path(temp) / "candidate"
        home = Path(temp) / "home"
        extracted.mkdir()
        home.mkdir()
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
            bundle.extractall(extracted)
        env = {
            **os.environ,
            "HOME": str(home),
            "USERPROFILE": str(home),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        receipt = pytest_gate("R1", "tests", env=env, cwd=extracted)
    receipt["tree"] = tree
    receipt["source"] = "git archive"
    return receipt


def migration_gate() -> dict[str, Any]:
    """R11: require the historical v0.4.0 tag and execute the real roundtrip."""
    baseline = subprocess.run(
        ["git", "rev-parse", "--verify", "v0.4.0-beta^{commit}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if baseline.returncode != 0:
        raise GateFailure("R11 requires local tag v0.4.0-beta (fetch-depth: 0 in CI)")
    receipt = pytest_gate("R11", "tests/test_migration_040_to_041.py")
    receipt["baseline_tag"] = "v0.4.0-beta"
    receipt["baseline_commit"] = baseline.stdout.strip()
    return receipt


def port_open(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def browser_gate(port: int, browser_home: Path) -> dict[str, Any]:
    if not port_open(9222):
        raise GateFailure("R12 requires local CDP on 127.0.0.1:9222")
    home = Path(tempfile.mkdtemp(prefix="pa-release-gate-home-"))
    server = subprocess.Popen(
        [PYTHON, "-u", "core/scripts/dashboard_server.py", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env={**os.environ, "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        url = f"http://127.0.0.1:{port}/api/status"
        for _ in range(50):
            try:
                with urllib.request.urlopen(url, timeout=0.5) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(0.1)
        else:
            raise GateFailure("R12 dashboard server did not become ready")
        env = {
            **os.environ,
            "HOME": str(home),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PA_BROWSER_HOME": str(browser_home),
            "PA_DASHBOARD_URL": f"http://127.0.0.1:{port}/",
            "PA_CDP_PORT": "9222",
        }
        return pytest_gate("R12", "tests/ui/test_dashboard_dom.py", env=env)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser-port", type=int, default=48764)
    parser.add_argument("--browser-home", type=Path, default=Path.home())
    args = parser.parse_args(argv)
    receipts: list[dict[str, Any]] = []
    try:
        receipts.append(fresh_extract_gate())
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if status:
            raise GateFailure(f"R2 dirty checkout:\n{status}")
        receipts.append({"gate": "R2", "returncode": 0})
        receipts.append(pytest_gate("R3", "tests/test_csrf_guard.py"))
        receipts.append(pytest_gate("R4", "tests/test_get_side_effects.py"))
        receipts.append(pytest_gate("R5", "tests/test_system_check_exit_codes.py"))
        receipts.append(pytest_gate("R6", "tests/test_version_contract.py", "tests/test_installer_flags.py", "tests/test_dashboard_version_dom.py"))
        receipts.append(pytest_gate("R7", "tests/test_post_install_integrity.py"))
        receipts.append(pytest_gate("R8", "tests/test_public_package.py"))
        receipts.append(pytest_gate("R9", "tests/test_model_selection_state.py"))
        receipts.append(pytest_gate("R10", "tests/test_pi_adapter.py"))
        receipts.append(migration_gate())
        receipts.append(browser_gate(args.browser_port, args.browser_home))
    except (GateFailure, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "NO-GO", "passed": receipts, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"status": "PASS", "gates": receipts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
