"""W2 contract: the cold start path persists the real storage discovery.

Before the fix, run_parallel_checks() called save_warm_cache() without
storage_status, so every storage flag in the receipt was written as False.
"""
from __future__ import annotations

import importlib.util
import json
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


session_start = _load("session_start_cold_contract", SCRIPTS / "session_start.py")


class _StubLoader:
    def __init__(self, *args, **kwargs):
        pass

    def load_tier(self, tier: int) -> dict:
        return {"content": "", "tokens": 1, "sources": []}


def test_cold_start_receipt_reflects_real_storage_discovery(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_path = cache_dir / "warm-start.json"
    monkeypatch.setattr(session_start, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(session_start, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(session_start, "WARM_CACHE_PATH", cache_path)

    keys = session_start.STORAGE_RECEIPT_KEYS
    discovered = {key: index % 2 == 0 for index, key in enumerate(keys)}
    assert True in discovered.values() and False in discovered.values()

    monkeypatch.setattr(session_start, "check_warm_start_cache", lambda: None)
    monkeypatch.setattr(session_start, "ContextLoader", _StubLoader)
    monkeypatch.setattr(session_start, "_discover_storage_status", lambda: dict(discovered))
    monkeypatch.setattr(session_start, "defer_loading", lambda loader: {})
    monkeypatch.setattr(session_start, "extract_kb_summary_from_tier", lambda tier: {})
    monkeypatch.setattr(session_start, "extract_last_session_from_tier", lambda tier: None)
    for name in (
        "get_active_clis_summary",
        "get_all_skills",
        "count_pending",
        "check_vitals_integrity",
        "sync_workspaces_status",
    ):
        monkeypatch.setattr(session_start, name, lambda *a, **k: None)

    session_start.run_parallel_checks(coord=None, skip_context=False)

    receipt = json.loads(cache_path.read_text(encoding="utf-8"))
    assert receipt["storage"] == discovered
