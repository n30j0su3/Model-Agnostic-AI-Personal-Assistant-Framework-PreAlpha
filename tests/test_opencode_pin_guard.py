"""W8 guard: OpenCode CLI gate and plugin contract must stay coherent.

The old exact 1.4.6 pin was incompatible with ``OPCODE_MIN_VERSION=(1, 18, 0)``:
an accepted CLI rewrote ``package.json``/``package-lock.json`` and the guard
failed. Those two files are now runtime-managed; this test checks the semver
contract instead of freezing their bytes.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MINIMUM = "1.18.0"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _version(value: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", value or "")
    assert match is not None, f"not a semver: {value!r}"
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


sfm = _load("sfm_pin_guard", ROOT / "core" / "scripts" / "select_free_model.py")
builder = _load("builder_pin_guard", ROOT / "core" / "scripts" / "build_release.py")
GATE = sfm.OPCODE_MIN_VERSION


def test_runtime_gate_is_the_documented_minimum():
    assert ".".join(map(str, GATE)) == MINIMUM


def test_plugin_contract_meets_runtime_gate():
    package = json.loads((ROOT / ".opencode" / "package.json").read_text(encoding="utf-8"))
    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    assert _version(deps.get("@opencode-ai/plugin", "")) >= GATE


def test_lock_contract_meets_runtime_gate():
    lock = json.loads((ROOT / ".opencode" / "package-lock.json").read_text(encoding="utf-8"))
    packages = lock["packages"]
    for name in ("@opencode-ai/plugin", "@opencode-ai/sdk"):
        entry = packages[f"node_modules/{name}"]
        assert _version(entry["version"]) >= GATE


def test_readme_documents_runtime_managed_opencode():
    readme = (ROOT / ".opencode" / "README.md").read_text(encoding="utf-8")
    assert MINIMUM in readme
    assert "runtime-managed" in readme.lower()


def test_builder_contract_matches_runtime_gate():
    assert builder.OPENCODE_MIN_VERSION == GATE
    assert builder.VOLATILE_RUNTIME_PATHS == {
        ".opencode/package.json",
        ".opencode/package-lock.json",
    }
