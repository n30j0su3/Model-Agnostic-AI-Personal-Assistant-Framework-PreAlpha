"""Deterministic ID contracts across Python hash seeds."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def ids_for_seed(seed: str) -> dict:
    program = r'''
import json
import sys
sys.path.insert(0, sys.argv[1])
from knowledge_pattern_detector import PatternDetector
from message_hook import MessageHook

detector = PatternDetector()
prompts = [
    detector._code_block_prompt([content], 0)["id"].rsplit("-", 1)[-1]
    for content in ("alpha", "beta", "gamma")
]
tagged_prompt = detector._parse_tagged_prompt(
    ["#prompt-success stable tagged prompt"], 0, "#prompt-success"
)["id"].rsplit("-", 1)[-1]

class Bridge:
    def set_user_fact(self, **kwargs):
        self.key = kwargs["key"]

bridge = Bridge()
hook = object.__new__(MessageHook)
hook.bridge = bridge
hook._log = lambda *args, **kwargs: None
hook._store_user_fact("The release gate stays fail-closed")
print(json.dumps({"prompts": prompts, "tagged_prompt": tagged_prompt, "fact_key": bridge.key}, sort_keys=True))
'''
    completed = subprocess.run(
        [sys.executable, "-c", program, str(SCRIPTS)],
        cwd=ROOT,
        env={**os.environ, "PYTHONHASHSEED": seed, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_prompt_and_fact_ids_are_stable_across_hash_seeds():
    assert ids_for_seed("1") == ids_for_seed("2")
