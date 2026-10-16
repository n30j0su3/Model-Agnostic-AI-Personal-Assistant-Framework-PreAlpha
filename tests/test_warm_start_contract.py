from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "core" / "scripts"


def _load(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


session_start = _load("session_start_warm_contract", SCRIPTS / "session_start.py")
pa = _load("pa_warm_contract", SCRIPTS / "pa.py")


def _receipt_fixture(tmp_path: Path, monkeypatch):
    root = tmp_path / "repo"
    cache_dir = root / "core" / ".context" / ".cache"
    cache_path = cache_dir / "warm-start.json"
    sources = {
        "AGENTS-lite.md": "# Bootstrap\n",
        "core/.context/MASTER.md": "PRIVATE-CONTEXT-MUST-NOT-BE-CACHED\n",
        "core/.context/profile.md": "# Profile\n",
        "core/.context/knowledge/sessions-index.json": '{"sessions": []}\n',
        "VERSION": "0.4.1-beta\n",
    }
    for relative, content in sources.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    monkeypatch.setattr(session_start, "REPO_ROOT", root)
    monkeypatch.setattr(session_start, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(session_start, "WARM_CACHE_PATH", cache_path)

    tier_0 = {
        "content": "PRIVATE-CONTEXT-MUST-NOT-BE-CACHED",
        "tokens": 10,
        "sources": [str(root / "AGENTS-lite.md")],
    }
    tier_1 = {
        "content": "PRIVATE-CONTEXT-MUST-NOT-BE-CACHED",
        "tokens": 20,
        "sources": [str(root / "core/.context/MASTER.md")],
    }
    return root, cache_path, tier_0, tier_1


def test_warm_receipt_contains_hashes_but_no_context_or_absolute_paths(tmp_path, monkeypatch):
    root, cache_path, tier_0, tier_1 = _receipt_fixture(tmp_path, monkeypatch)

    assert session_start.save_warm_cache(tier_0, tier_1) is True

    raw = cache_path.read_text(encoding="utf-8")
    receipt = json.loads(raw)
    assert receipt["schema"] == "pa.warm-start/1"
    assert receipt["source_hashes"]["AGENTS-lite.md"]
    assert receipt["source_hashes"]["core/.context/MASTER.md"]
    assert "content" not in raw
    assert "PRIVATE-CONTEXT-MUST-NOT-BE-CACHED" not in raw
    assert str(root) not in raw


def test_warm_receipt_invalidates_when_a_source_changes(tmp_path, monkeypatch):
    root, _cache_path, tier_0, tier_1 = _receipt_fixture(tmp_path, monkeypatch)
    assert session_start.save_warm_cache(tier_0, tier_1) is True
    assert session_start.check_warm_start_cache() is not None

    (root / "AGENTS-lite.md").write_text("# Changed bootstrap\n", encoding="utf-8")

    assert session_start.check_warm_start_cache() is None


def test_magic_prompt_consumes_receipt_without_repeating_bootstrap():
    prompt = pa.get_magic_prompt()
    assert "core/.context/.cache/warm-start.json" in prompt
    assert "quick-start.md" not in prompt
    assert "session_start" not in prompt
    assert "persistent_storage_discover" not in prompt
    assert len(prompt.encode("utf-8")) <= 320


def test_quick_start_is_compact_and_does_not_order_duplicate_bootstrap():
    text = (ROOT / "core/.context/quick-start.md").read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) <= 1200
    assert "persistent_storage_discover.py --integration" not in text
    assert "python core/scripts/session_start.py" not in text
    assert "0.4.1-beta" in text


def test_pa_bootstrap_uses_single_bootstrap_only_process(tmp_path, monkeypatch):
    scripts = tmp_path / "core" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "session_start.py").write_text("# fixture\n", encoding="utf-8")
    seen = []

    def fake_run(argv, **kwargs):
        seen.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(pa, "SCRIPT_DIR", scripts)
    monkeypatch.setattr(pa, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(pa, "get_python", lambda: sys.executable)
    monkeypatch.setattr(pa.subprocess, "run", fake_run)
    monkeypatch.setattr(
        pa, "_run_skills_indexer", lambda: (_ for _ in ()).throw(AssertionError("duplicate indexer"))
    )
    monkeypatch.setattr(
        pa,
        "_rebuild_interactions_index",
        lambda: (_ for _ in ()).throw(AssertionError("duplicate interactions index")),
    )

    assert pa._framework_bootstrap() is True
    assert len(seen) == 1
    assert "--bootstrap-only" in seen[0][0]


def test_warm_bootstrap_only_opens_no_coordinator_or_sqlite(monkeypatch):
    receipt = {
        "schema": "pa.warm-start/1",
        "timestamp": 1,
        "tiers": {"tier_0": {"tokens": 1}, "tier_1": {"tokens": 1}},
        "source_hashes": {},
    }
    monkeypatch.setattr(sys, "argv", ["session_start.py", "--bootstrap-only"])
    monkeypatch.setattr(session_start, "check_warm_start_cache", lambda: receipt)
    monkeypatch.setattr(
        session_start, "_refresh_bootstrap_indexes", lambda: True, raising=False
    )
    monkeypatch.setattr(
        session_start,
        "init_multi_cli_coordinator",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("coordinator started")),
    )
    monkeypatch.setattr(
        session_start,
        "run_parallel_checks",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("context reloaded")),
    )

    class _ForbiddenBridge:
        def __init__(self, *args, **kwargs):
            raise AssertionError("SQLite SessionBridge opened")

    monkeypatch.setattr(session_start, "SessionBridge", _ForbiddenBridge)
    monkeypatch.setattr(session_start, "MEMORY_BRIDGE_AVAILABLE", True)

    assert session_start.main() == 0


def test_cold_bootstrap_only_builds_receipt_without_session(monkeypatch):
    seen_argv: list[list[str]] = []
    saved = {}

    def fake_run(argv, **kwargs):
        seen_argv.append([str(part) for part in argv])
        if "persistent_storage_discover.py" in " ".join(map(str, argv)):
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "sqlite_available": True,
                        "wiki_available": False,
                        "md_memory_available": True,
                        "sessions_md_available": True,
                        "all_available": False,
                        "private_path": "PRIVATE-SENTINEL-MUST-NOT-PERSIST",
                    }
                ),
                stderr="",
            )
        return SimpleNamespace(returncode=0, stdout="0 pending", stderr="")

    class _Loader:
        def __init__(self, repo_root):
            self.repo_root = repo_root

        def load_tier(self, tier):
            return {
                "tier": tier,
                "content": f"private tier {tier}",
                "tokens": tier + 1,
                "sources": [],
            }

    def fake_save(tier_0, tier_1, storage_status=None):
        saved["tier_0"] = tier_0
        saved["tier_1"] = tier_1
        saved["storage"] = storage_status
        return True

    monkeypatch.setattr(sys, "argv", ["session_start.py", "--bootstrap-only"])
    monkeypatch.setattr(session_start, "check_warm_start_cache", lambda: None)
    monkeypatch.setattr(
        session_start, "_refresh_bootstrap_indexes", lambda: True, raising=False
    )
    monkeypatch.setattr(session_start.subprocess, "run", fake_run)
    monkeypatch.setattr(session_start, "ContextLoader", _Loader)
    monkeypatch.setattr(session_start, "save_warm_cache", fake_save)
    monkeypatch.setattr(
        session_start,
        "init_multi_cli_coordinator",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("coordinator started")),
    )

    class _ForbiddenBridge:
        def __init__(self, *args, **kwargs):
            raise AssertionError("SQLite SessionBridge opened")

    monkeypatch.setattr(session_start, "SessionBridge", _ForbiddenBridge)
    monkeypatch.setattr(session_start, "MEMORY_BRIDGE_AVAILABLE", True)

    assert session_start.main() == 0
    assert saved["tier_0"]["tier"] == 0
    assert saved["tier_1"]["tier"] == 1
    assert saved["storage"] == {
        "sqlite_available": True,
        "wiki_available": False,
        "md_memory_available": True,
        "sessions_md_available": True,
        "all_available": False,
    }
    commands = [" ".join(argv) for argv in seen_argv]
    assert any("system_check.py" in command for command in commands)
    assert any("persistent_storage_discover.py" in command for command in commands)
