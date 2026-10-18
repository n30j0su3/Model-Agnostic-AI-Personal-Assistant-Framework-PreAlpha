"""W0 guard: the OpenCode plugin pin is frozen for this release.

The upgrade to a newer @opencode-ai/plugin is a separate task. Any change to
this pin must be a deliberate, reviewed change that updates this test.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = "1.4.6"


def test_opencode_plugin_pin_is_frozen():
    package = json.loads((ROOT / ".opencode" / "package.json").read_text(encoding="utf-8"))
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    assert deps.get("@opencode-ai/plugin") == PIN
