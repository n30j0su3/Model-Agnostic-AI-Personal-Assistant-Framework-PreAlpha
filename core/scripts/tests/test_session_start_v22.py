#!/usr/bin/env python3
"""
Unit tests for session-start.py v2.2.0 — ContextLoader Integration.

Tests cover:
- Warm start cache (check/save/invalidate)
- defer_loading() for lazy tiers 2-4
- extract_kb_summary_from_tier() replacing load_knowledge_base_summary
- extract_last_session_from_tier() replacing get_last_session_summary
- run_parallel_checks() with ContextLoader integration
- --skip-context CLI flag behavior
- Backward compatibility with legacy mode

Run with:
    pytest core/scripts/tests/test_session_start_v22.py -v --tb=short

Author: PA Framework Team
"""

import importlib
import importlib.util
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path for imports (same dir as session-start.py)
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from context_loader import ContextLoader, TokenBudgetTracker


# --- IMPORT session-start.py via importlib (hyphen in name) ---
_spec = importlib.util.spec_from_file_location(
    "session_start",
    str(SCRIPTS_DIR / "session_start.py"),
)
session_start = importlib.util.module_from_spec(_spec)
# Prevent main() from running on import
sys.modules["session_start"] = session_start
_spec.loader.exec_module(session_start)


# Shorthand aliases for test readability
check_warm_start_cache = session_start.check_warm_start_cache
save_warm_cache = session_start.save_warm_cache
defer_loading = session_start.defer_loading
extract_kb_summary_from_tier = session_start.extract_kb_summary_from_tier
extract_last_session_from_tier = session_start.extract_last_session_from_tier
run_parallel_checks = session_start.run_parallel_checks
print_session_start = session_start.print_session_start


# --- FIXTURES ---
@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create directory structure
        context_dir = repo_root / "core" / ".context"
        knowledge_dir = context_dir / "knowledge"
        sessions_dir = context_dir / "sessions"
        cache_dir = context_dir / ".cache"
        codebase_dir = context_dir / "codebase"

        for d in [context_dir, knowledge_dir, sessions_dir, cache_dir, codebase_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Create AGENTS-lite.md (Tier 0)
        agents_lite = repo_root / "AGENTS-lite.md"
        agents_lite.write_text("""# AGENTS-lite — Framework Bootstrap

## INITIALIZATION TRIGGER
python core/scripts/session-start.py

## AGENT ROUTER
Agent routing info here.
""")

        # Create MASTER.md (Tier 1)
        master = context_dir / "MASTER.md"
        master.write_text("""# MASTER CONTEXT
## Preferences
- Language: es
- Style: concise
""")

        # Create profile.md (Tier 1)
        profile = context_dir / "profile.md"
        profile.write_text("# User Profile\nName: Test User\n")

        # Create sessions-index.json (Tier 1)
        sessions_index = knowledge_dir / "sessions-index.json"
        sessions_index.write_text(json.dumps({
            "total_sessions": 5,
            "sessions": [
                {"id": "2026-04-16", "title": "Today's session", "summary": "Refactored context loader", "topics": ["refactoring", "testing"]},
                {"id": "2026-04-15", "title": "Previous session", "summary": "Implemented ADR-001", "topics": ["ADR", "design"]},
                {"id": "2026-04-14", "title": "Older session", "summary": "Fixed bugs", "topics": ["bugs", "testing"]},
            ]
        }))

        # Create session files (Tier 2)
        for i, date in enumerate(["2026-04-16", "2026-04-15", "2026-04-14"]):
            session_file = sessions_dir / f"{date}.md"
            session_file.write_text(f"# Session {date}\n\nWork done on {date}.\n")
            mtime = time.time() - (i * 86400)
            os.utime(session_file, (mtime, mtime))

        # Create recordatorios.md for pending count
        recordatorios = codebase_dir / "recordatorios.md"
        recordatorios.write_text("- [ ] Task 1\n- [ ] Task 2\n- [x] Done task\n- [ ] Task 3\n")

        yield repo_root


@pytest.fixture
def warm_cache_data():
    """Sample warm cache data for testing."""
    return {
        "timestamp": time.time(),
        "version": "2.2.0",
        "tiers": {
            "tier_0": {
                "content": "# Bootstrap content",
                "tokens": 50,
                "sources": ["/fake/AGENTS-lite.md"],
            },
            "tier_1": {
                "content": "# Essential content\nSessions data here",
                "tokens": 200,
                "sources": ["/fake/MASTER.md", "/fake/sessions-index.json"],
            },
        },
    }


def _patch_paths(temp_repo):
    """Return a list of patch context managers for all session-start paths."""
    context_dir = temp_repo / "core" / ".context"
    cache_dir = context_dir / ".cache"
    cache_path = cache_dir / "warm-start.json"
    return [
        patch.object(session_start, "REPO_ROOT", temp_repo),
        patch.object(session_start, "CONTEXT_DIR", context_dir),
        patch.object(session_start, "SESSIONS_DIR", context_dir / "sessions"),
        patch.object(session_start, "KNOWLEDGE_DIR", context_dir / "knowledge"),
        patch.object(session_start, "CODEBASE_DIR", context_dir / "codebase"),
        patch.object(session_start, "CACHE_DIR", cache_dir),
        patch.object(session_start, "WARM_CACHE_PATH", cache_path),
        patch.object(session_start, "CORE_DIR", temp_repo / "core"),
    ]


from contextlib import ExitStack


# --- WARM START CACHE TESTS ---
class TestWarmStartCache:
    """Tests for warm start cache functionality."""

    def test_check_cache_no_file(self, temp_repo):
        """No cache file should return None (cold start)."""
        cache_dir = temp_repo / "core" / ".context" / ".cache"
        cache_path = cache_dir / "warm-start.json"

        with patch.object(session_start, "WARM_CACHE_PATH", cache_path):
            result = check_warm_start_cache()
            assert result is None

    def test_check_cache_valid(self, temp_repo, warm_cache_data):
        """Valid cache should return cached data."""
        cache_dir = temp_repo / "core" / ".context" / ".cache"
        cache_path = cache_dir / "warm-start.json"
        cache_path.write_text(json.dumps(warm_cache_data), encoding="utf-8")

        with patch.object(session_start, "WARM_CACHE_PATH", cache_path):
            result = check_warm_start_cache()
            assert result is not None
            assert "tiers" in result
            assert "tier_0" in result["tiers"]

    def test_check_cache_stale(self, temp_repo):
        """Stale cache (older than TTL) should return None."""
        stale_data = {
            "timestamp": time.time() - 7201,  # 1 second past TTL
            "version": "2.2.0",
            "tiers": {
                "tier_0": {"content": "old", "tokens": 10, "sources": []},
                "tier_1": {"content": "old", "tokens": 10, "sources": []},
            },
        }
        cache_dir = temp_repo / "core" / ".context" / ".cache"
        cache_path = cache_dir / "warm-start.json"
        cache_path.write_text(json.dumps(stale_data), encoding="utf-8")

        with patch.object(session_start, "WARM_CACHE_PATH", cache_path):
            result = check_warm_start_cache()
            assert result is None

    def test_check_cache_corrupted(self, temp_repo):
        """Corrupted cache file should return None."""
        cache_dir = temp_repo / "core" / ".context" / ".cache"
        cache_path = cache_dir / "warm-start.json"
        cache_path.write_text("not valid json {{{", encoding="utf-8")

        with patch.object(session_start, "WARM_CACHE_PATH", cache_path):
            result = check_warm_start_cache()
            assert result is None

    def test_check_cache_missing_tiers(self, temp_repo):
        """Cache missing tier keys should return None."""
        bad_data = {
            "timestamp": time.time(),
            "version": "2.2.0",
            "tiers": {"tier_0": {"content": "x", "tokens": 1, "sources": []}},
        }
        cache_dir = temp_repo / "core" / ".context" / ".cache"
        cache_path = cache_dir / "warm-start.json"
        cache_path.write_text(json.dumps(bad_data), encoding="utf-8")

        with patch.object(session_start, "WARM_CACHE_PATH", cache_path):
            result = check_warm_start_cache()
            assert result is None

    def test_save_warm_cache(self, temp_repo):
        """save_warm_cache should write valid cache file."""
        cache_dir = temp_repo / "core" / ".context" / ".cache"
        cache_path = cache_dir / "warm-start.json"

        tier_0 = {"content": "bootstrap", "tokens": 50, "sources": ["/a.md"]}
        tier_1 = {"content": "essential", "tokens": 200, "sources": ["/b.md"]}

        with patch.object(session_start, "WARM_CACHE_PATH", cache_path), \
             patch.object(session_start, "CACHE_DIR", cache_dir):
            result = save_warm_cache(tier_0, tier_1)
            assert result is True

        # Verify file was written
        assert cache_path.exists()
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        assert data["version"] == "2.2.0"
        assert "tier_0" in data["tiers"]
        assert "tier_1" in data["tiers"]
        assert data["tiers"]["tier_0"]["tokens"] == 50

    def test_save_and_load_roundtrip(self, temp_repo):
        """Save then load should return equivalent data."""
        cache_dir = temp_repo / "core" / ".context" / ".cache"
        cache_path = cache_dir / "warm-start.json"

        tier_0 = {"content": "hello bootstrap", "tokens": 100, "sources": ["/test.md"]}
        tier_1 = {"content": "essential data", "tokens": 300, "sources": ["/test2.md"]}

        with patch.object(session_start, "WARM_CACHE_PATH", cache_path), \
             patch.object(session_start, "CACHE_DIR", cache_dir):
            save_warm_cache(tier_0, tier_1)
            loaded = check_warm_start_cache()

        assert loaded is not None
        assert loaded["tiers"]["tier_0"]["content"] == "hello bootstrap"
        assert loaded["tiers"]["tier_1"]["tokens"] == 300


# --- DEFER LOADING TESTS ---
class TestDeferLoading:
    """Tests for defer_loading() function."""

    def test_defer_loading_returns_metadata(self, temp_repo):
        """defer_loading should return tier 2-4 metadata."""
        loader = ContextLoader(repo_root=temp_repo)
        result = defer_loading(loader)

        assert result["deferred_tiers"] == [2, 3, 4]
        assert 2 in result["descriptions"]
        assert result["status"] == "deferred"
        assert result["loader_available"] is True

    def test_defer_loading_none_loader(self):
        """defer_loading with None loader should still return metadata."""
        result = defer_loading(None)

        assert result["deferred_tiers"] == [2, 3, 4]
        assert result["loader_available"] is False

    def test_deferred_tiers_not_loaded(self, temp_repo):
        """Deferred tiers should NOT be loaded in cache."""
        loader = ContextLoader(repo_root=temp_repo)
        defer_loading(loader)

        # Tiers 2-4 should be None (not loaded)
        assert loader._cache[2] is None
        assert loader._cache[3] is None
        assert loader._cache[4] is None

    def test_deferred_tiers_can_be_loaded_later(self, temp_repo):
        """Deferred tiers should be loadable on demand after deferring."""
        loader = ContextLoader(repo_root=temp_repo)
        defer_loading(loader)

        # Now explicitly load tier 2 (lazy)
        result = loader.load_tier(2)
        assert result["tier"] == 2
        assert result["description"] == "Context"
        assert "tokens" in result


# --- EXTRACT KB SUMMARY TESTS ---
class TestExtractKBSummary:
    """Tests for extract_kb_summary_from_tier()."""

    def test_extract_from_tier_with_data(self, temp_repo):
        """Should extract structured KB data from tier 1 context."""
        knowledge_dir = temp_repo / "core" / ".context" / "knowledge"
        tier_1_data = {"content": "some content", "tokens": 100, "sources": []}

        with patch.object(session_start, "KNOWLEDGE_DIR", knowledge_dir):
            result = extract_kb_summary_from_tier(tier_1_data)

        assert result["available"] is True
        assert result["total_sessions"] == 5
        assert result["last_session"] is not None
        assert result["last_session"]["id"] == "2026-04-16"

    def test_extract_no_index_file(self, temp_repo):
        """Should return unavailable when no sessions-index.json."""
        knowledge_dir = temp_repo / "core" / ".context" / "knowledge"
        # Remove sessions index
        (knowledge_dir / "sessions-index.json").unlink()

        tier_1_data = {"content": "some content", "tokens": 0, "sources": []}

        with patch.object(session_start, "KNOWLEDGE_DIR", knowledge_dir):
            result = extract_kb_summary_from_tier(tier_1_data)

        assert result["available"] is False
        assert result["total_sessions"] == 0

    def test_extract_topics_frequency(self, temp_repo):
        """Should correctly count topic frequency."""
        knowledge_dir = temp_repo / "core" / ".context" / "knowledge"
        tier_1_data = {"content": "some content", "tokens": 0, "sources": []}

        with patch.object(session_start, "KNOWLEDGE_DIR", knowledge_dir):
            result = extract_kb_summary_from_tier(tier_1_data)

        # Should have topics from sessions-index.json
        assert len(result["recent_topics"]) > 0

    def test_extract_corrupted_index(self, temp_repo):
        """Should handle corrupted sessions-index.json gracefully."""
        knowledge_dir = temp_repo / "core" / ".context" / "knowledge"
        # Corrupt the index
        (knowledge_dir / "sessions-index.json").write_text("not json{{{", encoding="utf-8")

        tier_1_data = {"content": "some content", "tokens": 0, "sources": []}

        with patch.object(session_start, "KNOWLEDGE_DIR", knowledge_dir):
            result = extract_kb_summary_from_tier(tier_1_data)

        # Should not crash, just return available=False or empty
        assert isinstance(result, dict)


# --- EXTRACT LAST SESSION TESTS ---
class TestExtractLastSession:
    """Tests for extract_last_session_from_tier()."""

    def test_extract_with_sessions(self, temp_repo):
        """Should extract last session summary from index."""
        knowledge_dir = temp_repo / "core" / ".context" / "knowledge"
        tier_1_data = {"content": "some content", "tokens": 0, "sources": []}

        with patch.object(session_start, "KNOWLEDGE_DIR", knowledge_dir):
            result = extract_last_session_from_tier(tier_1_data)

        # Should return second session's title/summary (previous session)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_extract_no_index(self, temp_repo):
        """Should return fallback when no index exists."""
        knowledge_dir = temp_repo / "core" / ".context" / "knowledge"
        (knowledge_dir / "sessions-index.json").unlink()

        tier_1_data = {"content": "some content", "tokens": 0, "sources": []}

        with patch.object(session_start, "KNOWLEDGE_DIR", knowledge_dir):
            result = extract_last_session_from_tier(tier_1_data)

        assert result == "Sin sesión anterior"

    def test_extract_single_session(self, temp_repo):
        """With only one session, should return its summary."""
        knowledge_dir = temp_repo / "core" / ".context" / "knowledge"
        (knowledge_dir / "sessions-index.json").write_text(json.dumps({
            "sessions": [
                {"id": "2026-04-16", "summary": "Only session today"}
            ]
        }), encoding="utf-8")

        tier_1_data = {"content": "some content", "tokens": 0, "sources": []}

        with patch.object(session_start, "KNOWLEDGE_DIR", knowledge_dir):
            result = extract_last_session_from_tier(tier_1_data)

        assert "Only session" in result


# --- RUN PARALLEL CHECKS TESTS ---
class TestRunParallelChecks:
    """Tests for run_parallel_checks() with ContextLoader integration."""

    def test_basic_run(self, temp_repo):
        """run_parallel_checks should return results dict."""
        patches = _patch_paths(temp_repo)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = run_parallel_checks(coord=None, skip_context=False)

        assert isinstance(result, dict)
        assert "kb_summary" in result
        assert "last_session" in result
        assert "_context_loaded" in result
        assert "_parallel_time" in result

    def test_skip_context_flag(self, temp_repo):
        """--skip-context should skip ContextLoader entirely."""
        patches = _patch_paths(temp_repo)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = run_parallel_checks(coord=None, skip_context=True)

        assert result["_context_loaded"] is False
        assert result["_warm_start"] is False

    def test_context_loaded(self, temp_repo):
        """Context should be loaded when skip_context=False."""
        patches = _patch_paths(temp_repo)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = run_parallel_checks(coord=None, skip_context=False)

        assert result["_context_loaded"] is True
        assert result["_tier_0_tokens"] > 0 or result["_tier_1_tokens"] > 0

    def test_warm_start_on_second_run(self, temp_repo):
        """Second run should use warm cache (warm start)."""
        patches = _patch_paths(temp_repo)

        # First run (cold start)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result1 = run_parallel_checks(coord=None, skip_context=False)

        assert result1["_context_loaded"] is True
        assert result1["_warm_start"] is False

        # Second run (warm start — cache was saved)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result2 = run_parallel_checks(coord=None, skip_context=False)

        assert result2["_context_loaded"] is True
        assert result2["_warm_start"] is True

    def test_deferred_tiers_present(self, temp_repo):
        """Results should include deferred tier metadata."""
        patches = _patch_paths(temp_repo)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = run_parallel_checks(coord=None, skip_context=False)

        assert "_deferred" in result
        assert result["_deferred"]["deferred_tiers"] == [2, 3, 4]

    def test_operational_checks_still_run(self, temp_repo):
        """Operational checks (skills, pending, vitals) should still execute."""
        # Create skills directory
        skills_dir = temp_repo / "core" / "skills" / "core"
        skills_dir.mkdir(parents=True, exist_ok=True)
        test_skill = skills_dir / "test-skill"
        test_skill.mkdir(exist_ok=True)
        (test_skill / "SKILL.md").write_text("# Test Skill")

        patches = _patch_paths(temp_repo)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = run_parallel_checks(coord=None, skip_context=False)

        # Operational checks should still be in results
        assert "all_skills" in result
        assert "pending_count" in result


# --- BACKWARD COMPATIBILITY TESTS ---
class TestBackwardCompatibility:
    """Tests ensuring v2.2.0 maintains backward compatibility."""

    def test_legacy_data_functions_still_work(self, temp_repo):
        """Original data loading functions should still be importable and work."""
        context_dir = temp_repo / "core" / ".context"

        with patch.object(session_start, "CONTEXT_DIR", context_dir), \
             patch.object(session_start, "SESSIONS_DIR", context_dir / "sessions"), \
             patch.object(session_start, "KNOWLEDGE_DIR", context_dir / "knowledge"), \
             patch.object(session_start, "CODEBASE_DIR", context_dir / "codebase"):

            pending = session_start.count_pending()
            assert isinstance(pending, int)
            assert pending == 3  # 3 unchecked items in fixture

            kb = session_start.load_knowledge_base_summary()
            assert isinstance(kb, dict)
            assert "available" in kb

    def test_parallel_data_format_unchanged(self, temp_repo):
        """run_parallel_checks output format should be backward compatible."""
        patches = _patch_paths(temp_repo)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            result = run_parallel_checks(coord=None, skip_context=False)

        # Original keys should still exist
        assert "cli_summary" in result
        assert "all_skills" in result
        assert "kb_summary" in result
        assert "pending_count" in result
        assert "last_session" in result
        assert "_parallel_time" in result

    def test_print_session_start_no_crash(self, temp_repo):
        """print_session_start should not crash with new data format."""
        patches = _patch_paths(temp_repo)
        with ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            data = run_parallel_checks(coord=None, skip_context=False)
            # Should not raise
            print_session_start(data)

    def test_print_session_start_none_data(self, temp_repo):
        """print_session_start with None should use legacy fallback."""
        context_dir = temp_repo / "core" / ".context"
        with patch.object(session_start, "CONTEXT_DIR", context_dir), \
             patch.object(session_start, "SESSIONS_DIR", context_dir / "sessions"), \
             patch.object(session_start, "KNOWLEDGE_DIR", context_dir / "knowledge"), \
             patch.object(session_start, "CODEBASE_DIR", context_dir / "codebase"):
            print_session_start(None)


# --- VERSION TEST ---
class TestVersion:
    """Tests for version string."""

    def test_version_is_v22(self):
        """Module docstring should indicate v2.2.0."""
        doc = session_start.__doc__
        assert "2.2.0" in doc
        assert "Context Loader" in doc

    def test_imports_work(self):
        """All new functions should be importable."""
        assert callable(session_start.check_warm_start_cache)
        assert callable(session_start.save_warm_cache)
        assert callable(session_start.defer_loading)
        assert callable(session_start.extract_kb_summary_from_tier)
        assert callable(session_start.extract_last_session_from_tier)


# --- MAIN ---
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
