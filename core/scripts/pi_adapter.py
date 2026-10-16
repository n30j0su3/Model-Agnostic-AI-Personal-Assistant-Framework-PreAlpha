#!/usr/bin/env python3
"""Opt-in Pi runtime adapter and wizard settings persistence."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ensure_data_dirs import atomic_write_json, ensure_data_dirs
from runtime_adapter import RuntimeAdapter


INSTALL_COMMAND = (
    "npm install -g --ignore-scripts @earendil-works/pi-coding-agent"
)
_AUTO = object()
_VALID_AUTH_STATES = {"ready", "not_ready", "invalid"}
_VALID_RUNTIMES = {"opencode", "pi"}


class PiAdapter(RuntimeAdapter):
    """One-shot Pi adapter; never changes the default runtime by itself."""

    def __init__(self, pi_path: str | Path | None | object = _AUTO):
        if pi_path is _AUTO:
            detected = shutil.which("pi")
            self.pi_path = detected
        elif pi_path is None:
            self.pi_path = None
        else:
            self.pi_path = str(pi_path)

    def detect(self) -> dict[str, Any]:
        if not self.pi_path:
            return {"installed": False, "install_cmd": INSTALL_COMMAND}
        return {"installed": True, "path": self.pi_path}

    def suggested_runtime_change(self) -> bool:
        """Detection must never silently opt the user into Pi."""
        return False

    @staticmethod
    def parse_auth_check(raw: Any) -> str:
        if not isinstance(raw, dict):
            return "invalid"
        state = raw.get("state")
        return state if state in _VALID_AUTH_STATES else "invalid"

    def credential_status(self) -> str:
        if not self.pi_path:
            return "not_ready"
        command = [
            self.pi_path,
            "auth",
            "check",
            "--provider",
            "opencode",
            "--json",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
                check=False,
            )
            raw = json.loads(result.stdout or "{}")
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return "invalid"
        state = self.parse_auth_check(raw)
        if state != "invalid":
            return state
        return {0: "ready", 1: "not_ready", 2: "invalid"}.get(
            result.returncode, "invalid"
        )

    def spawn_chat(
        self,
        prompt: str,
        *,
        model: str,
        opencode_api_key: str | None = None,
        **_: Any,
    ) -> subprocess.Popen:
        if not self.pi_path:
            raise FileNotFoundError("Pi runtime is not installed")
        if not model.startswith("opencode/"):
            raise ValueError("Pi OpenCode model must use provider/id format")
        environment = os.environ.copy()
        if opencode_api_key is not None:
            environment["OPENCODE_API_KEY"] = opencode_api_key
        return subprocess.Popen(
            [self.pi_path, "--print", prompt, "--model", model],
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )


class WizardSettings:
    """Generated wizard state; OpenCode stays implicit until explicit choice."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.path = ensure_data_dirs(self.repo_root)["wizard"] / "runtime-settings.json"

    def _read(self) -> dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._read().get(key, default)

    def effective_runtime(self) -> str:
        runtime = self.get("runtime")
        return runtime if runtime in _VALID_RUNTIMES else "opencode"

    def choose_runtime(self, runtime: str, *, confirm: bool) -> dict[str, Any]:
        if runtime not in _VALID_RUNTIMES:
            raise ValueError(f"unsupported runtime: {runtime}")
        if not confirm:
            raise ValueError("explicit confirmation is required")
        state = self._read()
        state["previous"] = self.effective_runtime()
        state["runtime"] = runtime
        atomic_write_json(self.path, state)
        return state

    def backup(self) -> dict[str, Any]:
        state = self._read()
        return {"previous": state.get("previous", "opencode")}
