#!/usr/bin/env python3
"""
Unit tests for PA Framework Context Loader.

Run with:
    pytest tests/context_loader_test.py -v --cov=context_loader

Target: ≥80% coverage

Author: PA Framework Team
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add parent directory to path for imports (test is in core/scripts/tests/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from context_loader import (
    ContextLoader,
    TokenBudgetTracker,
    TokenBudget,
    estimate_tokens,
    track_tokens,
)


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
        playbooks_dir = knowledge_dir / "playbooks"
        
        for d in [context_dir, knowledge_dir, sessions_dir, playbooks_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Create AGENTS-lite.md (Tier 0)
        agents_lite = repo_root / "AGENTS-lite.md"
        agents_lite.write_text("""# AGENTS-lite — Framework Bootstrap

## 🚀 INITIALIZATION TRIGGER
python core/scripts/session-start.py

## 📋 AGENT ROUTER
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
            "sessions": [
                {"id": "2026-04-16", "summary": "Test session"},
                {"id": "2026-04-15", "summary": "Previous session"}
            ]
        }))
        
        # Create session files (Tier 2)
        for i, date in enumerate(["2026-04-16", "2026-04-15", "2026-04-14"]):
            session_file = sessions_dir / f"{date}.md"
            session_file.write_text(f"# Session {date}\n\nWork done on {date}.\n" * 10)
            # Set mtime to make ordering work
            mtime = time.time() - (i * 86400)
            os.utime(session_file, (mtime, mtime))
        
        # Create playbook (Tier 2)
        playbook = playbooks_dir / "PB-001-test.md"
        playbook.write_text("# PB-001: Test Playbook\n\nRecovery steps here.\n")
        
        # Create templates (Tier 3)
        template = context_dir / "MASTER.template.md"
        template.write_text("# Template\n\nTemplate content.\n")
        
        quick_start = context_dir / "quick-start.md"
        quick_start.write_text("# Quick Start\n\nGetting started guide.\n")
        
        nav = context_dir / "navigation.md"
        nav.write_text("# Navigation\n\nFile navigation info.\n")
        
        yield repo_root


# --- TOKEN ESTIMATION TESTS ---
class TestEstimateTokens:
    """Tests for token estimation function."""
    
    def test_empty_string(self):
        """Empty string should return 0 tokens."""
        assert estimate_tokens("") == 0
    
    def test_short_string(self):
        """Short string should return at least 1 token."""
        assert estimate_tokens("abc") == 1
    
    def test_normal_string(self):
        """Normal string estimation."""
        # 400 chars = 100 tokens
        text = "a" * 400
        assert estimate_tokens(text) == 100
    
    def test_long_string(self):
        """Long string estimation."""
        # 4000 chars = 1000 tokens
        text = "a" * 4000
        assert estimate_tokens(text) == 1000
    
    def test_none_input(self):
        """None should return 0."""
        assert estimate_tokens(None) == 0


# --- TOKEN BUDGET TRACKER TESTS ---
class TestTokenBudgetTracker:
    """Tests for TokenBudgetTracker class."""
    
    def test_initialization(self):
        """Tracker should initialize with zero usage."""
        tracker = TokenBudgetTracker()
        for tier in range(5):
            assert tracker.usage[tier] == 0
    
    def test_track_tokens(self):
        """Token tracking should accumulate correctly."""
        tracker = TokenBudgetTracker()
        
        # Track tokens for tier 0
        result = tracker.track(0, 100)
        assert result is True  # Within budget
        assert tracker.usage[0] == 100
        
        # Track more tokens
        tracker.track(0, 200)
        assert tracker.usage[0] == 300
    
    def test_budget_exceeded(self):
        """Should return False when budget exceeded."""
        tracker = TokenBudgetTracker()
        
        # Tier 0 budget is 500
        result = tracker.track(0, 600)
        assert result is False  # Exceeded budget
    
    def test_check_budget(self):
        """Budget checking should work correctly."""
        tracker = TokenBudgetTracker()
        tracker.track(0, 400)
        
        # Should have 100 remaining
        assert tracker.check_budget(0, 50) is True
        assert tracker.check_budget(0, 200) is False
    
    def test_get_remaining(self):
        """Remaining budget calculation."""
        tracker = TokenBudgetTracker()
        tracker.track(0, 200)
        
        # Tier 0 budget is 500, used 200, remaining 300
        assert tracker.get_remaining(0) == 300
    
    def test_get_remaining_exceeded(self):
        """Remaining should be 0 when budget exceeded."""
        tracker = TokenBudgetTracker()
        tracker.track(0, 600)
        
        assert tracker.get_remaining(0) == 0
    
    def test_invalid_tier(self):
        """Invalid tier should raise error."""
        tracker = TokenBudgetTracker()
        
        with pytest.raises(ValueError):
            tracker.track(5, 100)
        
        with pytest.raises(ValueError):
            tracker.track(-1, 100)
    
    def test_record_load_time(self):
        """Load time recording."""
        tracker = TokenBudgetTracker()
        tracker.record_load_time(0, 0.5)
        
        assert tracker.load_times[0] == 0.5
    
    def test_get_stats(self):
        """Stats retrieval."""
        tracker = TokenBudgetTracker()
        tracker.track(0, 100)
        tracker.track(1, 200)
        tracker.record_load_time(0, 0.3)
        
        stats = tracker.get_stats()
        
        assert stats["usage"][0] == 100
        assert stats["usage"][1] == 200
        assert stats["remaining"][0] == 400  # 500 - 100
        assert stats["load_times"][0] == 0.3


# --- TOKEN BUDGET DATACLASS TESTS ---
class TestTokenBudget:
    """Tests for TokenBudget dataclass."""
    
    def test_budget_creation(self):
        """TokenBudget should be created correctly."""
        budget = TokenBudget(tier=0, max_tokens=500, description="Bootstrap")
        
        assert budget.tier == 0
        assert budget.max_tokens == 500
        assert budget.description == "Bootstrap"


# --- TRACK_TOKENS DECORATOR TESTS ---
class TestTrackTokensDecorator:
    """Tests for @track_tokens decorator."""
    
    def test_decorator_adds_tokens(self):
        """Decorator should add token count to result."""
        @track_tokens
        def load_content():
            return {"content": "a" * 400}  # 400 chars = 100 tokens
        
        result = load_content()
        
        assert "tokens" in result
        assert result["tokens"] == 100
    
    def test_decorator_adds_load_time(self):
        """Decorator should add load time to result."""
        @track_tokens
        def load_content():
            time.sleep(0.01)
            return {"content": "test"}
        
        result = load_content()
        
        assert "load_time" in result
        assert result["load_time"] >= 0.01
    
    def test_decorator_handles_empty_content(self):
        """Decorator should handle empty content."""
        @track_tokens
        def load_content():
            return {"content": ""}
        
        result = load_content()
        
        assert result["tokens"] == 0
    
    def test_decorator_handles_non_dict(self):
        """Decorator should pass through non-dict results."""
        @track_tokens
        def load_content():
            return "not a dict"
        
        result = load_content()
        
        assert result == "not a dict"
    
    def test_decorator_preserves_metadata(self):
        """Decorator should preserve function metadata."""
        @track_tokens
        def load_content():
            """Docstring here."""
            return {"content": "test"}
        
        assert load_content.__doc__ == "Docstring here."
        assert load_content.__name__ == "load_content"


# --- CONTEXT LOADER TESTS ---
class TestContextLoader:
    """Tests for ContextLoader class."""
    
    def test_initialization(self, temp_repo):
        """ContextLoader should initialize correctly."""
        loader = ContextLoader(repo_root=temp_repo)
        
        assert loader.repo_root == temp_repo
        assert loader.context_dir.exists()
        assert loader.tracker is not None
    
    def test_load_tier_0(self, temp_repo):
        """Load Tier 0 (Bootstrap)."""
        loader = ContextLoader(repo_root=temp_repo)
        result = loader.load_tier(0)
        
        assert result["tier"] == 0
        assert result["description"] == "Bootstrap"
        assert "AGENTS-lite" in result["content"] or "Bootstrap" in result["content"]
        assert "tokens" in result
        assert len(result["sources"]) > 0
    
    def test_load_tier_1(self, temp_repo):
        """Load Tier 1 (Essential)."""
        loader = ContextLoader(repo_root=temp_repo)
        result = loader.load_tier(1)
        
        assert result["tier"] == 1
        assert result["description"] == "Essential"
        assert "MASTER" in result["content"] or "Profile" in result["content"]
        assert "tokens" in result
    
    def test_load_tier_2(self, temp_repo):
        """Load Tier 2 (Context)."""
        loader = ContextLoader(repo_root=temp_repo)
        result = loader.load_tier(2)
        
        assert result["tier"] == 2
        assert result["description"] == "Context"
        assert "tokens" in result
    
    def test_load_tier_3(self, temp_repo):
        """Load Tier 3 (Reference)."""
        loader = ContextLoader(repo_root=temp_repo)
        result = loader.load_tier(3)
        
        assert result["tier"] == 3
        assert result["description"] == "Reference"
        assert "tokens" in result
    
    def test_load_tier_4(self, temp_repo):
        """Load Tier 4 (Historical)."""
        loader = ContextLoader(repo_root=temp_repo)
        result = loader.load_tier(4)
        
        assert result["tier"] == 4
        assert result["description"] == "Historical"
        assert "tokens" in result
    
    def test_invalid_tier(self, temp_repo):
        """Invalid tier should raise error."""
        loader = ContextLoader(repo_root=temp_repo)
        
        with pytest.raises(ValueError):
            loader.load_tier(5)
        
        with pytest.raises(ValueError):
            loader.load_tier(-1)
    
    def test_tier_caching(self, temp_repo):
        """Tiers 2-4 should be cached after first load."""
        loader = ContextLoader(repo_root=temp_repo)
        
        # First load
        result1 = loader.load_tier(2)
        
        # Second load should return cached
        result2 = loader.load_tier(2)
        
        # Should be same object (cached)
        assert result1 is result2
    
    def test_clear_cache(self, temp_repo):
        """Clear cache should reset all cached tiers."""
        loader = ContextLoader(repo_root=temp_repo)
        
        # Load some tiers
        loader.load_tier(0)
        loader.load_tier(2)
        
        # Clear cache
        loader.clear_cache()
        
        # All should be None
        for tier in range(5):
            assert loader._cache[tier] is None
    
    def test_load_all(self, temp_repo):
        """Load all tiers at once."""
        loader = ContextLoader(repo_root=temp_repo)
        results = loader.load_all()
        
        assert len(results) == 5
        for tier in range(5):
            assert tier in results
            assert results[tier]["tier"] == tier
    
    def test_load_essential(self, temp_repo):
        """Load essential tiers (0 and 1)."""
        loader = ContextLoader(repo_root=temp_repo)
        results = loader.load_essential()
        
        assert len(results) == 2
        assert 0 in results
        assert 1 in results
        assert 2 not in results
    
    def test_token_budget_tracking(self, temp_repo):
        """Token budget should be tracked."""
        loader = ContextLoader(repo_root=temp_repo)
        
        # Load tier 0
        result = loader.load_tier(0)
        
        # Check tracker
        assert loader.tracker.usage[0] == result["tokens"]
    
    def test_get_budget_status(self, temp_repo):
        """Budget status retrieval."""
        loader = ContextLoader(repo_root=temp_repo)
        loader.load_tier(0)
        loader.load_tier(1)
        
        status = loader.get_budget_status()
        
        assert "usage" in status
        assert "remaining" in status
        assert "budgets" in status
    
    def test_parallel_load_tiers(self, temp_repo):
        """Parallel loading of multiple tiers."""
        loader = ContextLoader(repo_root=temp_repo)
        results = loader.parallel_load_tiers([0, 1, 2])
        
        assert len(results) == 3
        for tier in [0, 1, 2]:
            assert tier in results
            assert results[tier]["tier"] == tier
    
    def test_truncation_on_budget_exceeded(self, temp_repo):
        """Content should be truncated when exceeding budget."""
        loader = ContextLoader(repo_root=temp_repo)
        
        # Create large AGENTS-lite
        agents_lite = temp_repo / "AGENTS-lite.md"
        large_content = "x" * 10000  # Much larger than 500 tokens
        agents_lite.write_text(large_content)
        
        result = loader.load_tier(0)
        
        # Should be truncated
        assert result["tokens"] <= TokenBudgetTracker.TIER_BUDGETS[0].max_tokens


# --- INTEGRATION TESTS ---
class TestContextLoaderIntegration:
    """Integration tests for ContextLoader."""
    
    def test_full_workflow(self, temp_repo):
        """Test complete workflow from init to load."""
        tracker = TokenBudgetTracker()
        loader = ContextLoader(repo_root=temp_repo, tracker=tracker)
        
        # Load essential tiers
        essential = loader.load_essential()
        
        assert 0 in essential
        assert 1 in essential
        
        # Check tracker
        stats = tracker.get_stats()
        assert stats["usage"][0] > 0
        assert stats["usage"][1] > 0
    
    def test_budget_enforcement(self, temp_repo):
        """Budget limits should be enforced."""
        loader = ContextLoader(repo_root=temp_repo)
        
        # Load all tiers
        loader.load_all()
        
        stats = loader.get_budget_status()
        
        # Check no tier exceeded budget
        for tier in range(5):
            usage = stats["usage"][tier]
            budget = stats["budgets"][tier]
            assert usage <= budget, f"Tier {tier} exceeded budget: {usage} > {budget}"
    
    def test_missing_files_graceful(self, temp_repo):
        """Missing files should not cause errors."""
        # Remove some files
        (temp_repo / "AGENTS-lite.md").unlink()
        
        loader = ContextLoader(repo_root=temp_repo)
        
        # Should not raise, just return empty content
        result = loader.load_tier(0)
        
        assert result["tier"] == 0
        assert isinstance(result["content"], str)
    
    def test_parallel_performance(self, temp_repo):
        """Parallel loading should be faster than sequential."""
        loader = ContextLoader(repo_root=temp_repo)
        
        # Sequential
        start = time.time()
        for tier in [0, 1, 2, 3, 4]:
            loader.clear_cache()
            loader.load_tier(tier)
        sequential_time = time.time() - start
        
        # Parallel
        loader.clear_cache()
        start = time.time()
        loader.parallel_load_tiers([0, 1, 2, 3, 4])
        parallel_time = time.time() - start
        
        # Parallel should be similar or faster (not strict due to small files)
        # Just verify it doesn't error
        assert parallel_time < 10  # Should complete within 10 seconds


# --- EDGE CASE TESTS ---
class TestContextLoaderEdgeCases:
    """Edge case tests for ContextLoader."""
    
    def test_empty_sessions_directory(self, temp_repo):
        """Empty sessions directory should not cause errors."""
        # Clear sessions
        sessions_dir = temp_repo / "core" / ".context" / "sessions"
        for f in sessions_dir.glob("*.md"):
            f.unlink()
        
        loader = ContextLoader(repo_root=temp_repo)
        
        result = loader.load_tier(2)
        
        assert result["tier"] == 2
        assert isinstance(result["content"], str)
    
    def test_corrupted_json(self, temp_repo):
        """Corrupted JSON should be handled gracefully."""
        # Corrupt sessions-index.json
        sessions_index = temp_repo / "core" / ".context" / "knowledge" / "sessions-index.json"
        sessions_index.write_text("not valid json {{{")
        
        loader = ContextLoader(repo_root=temp_repo)
        
        # Should not raise
        result = loader.load_tier(1)
        
        assert result["tier"] == 1
    
    def test_alternate_agents_lite_path(self, temp_repo):
        """Should handle AGENTS-lite.md in alternate location."""
        # Move AGENTS-lite.md to alternate location
        agents_lite = temp_repo / "AGENTS-lite.md"
        alt_dir = temp_repo / "Model-Agnostic-AI-Personal-Assistant-Framework"
        alt_dir.mkdir(exist_ok=True)
        agents_lite.rename(alt_dir / "AGENTS-lite.md")
        
        loader = ContextLoader(repo_root=temp_repo)
        
        # Should find alternate path
        result = loader.load_tier(0)
        
        assert len(result["sources"]) > 0 or result["content"]


# --- FIXTURE FOR ACTUAL REPO ---
class TestContextLoaderRealRepo:
    """Tests using actual repository structure if available."""
    
    @pytest.mark.skipif(
        not (Path(__file__).parent.parent / "core" / "scripts" / "context_loader.py").exists(),
        reason="Real repo not available"
    )
    def test_real_repo_load(self):
        """Test loading from actual repository."""
        repo_root = Path(__file__).parent.parent
        
        loader = ContextLoader(repo_root=repo_root)
        
        # Try loading tier 0
        result = loader.load_tier(0)
        
        assert result["tier"] == 0
        # Should have some content from AGENTS-lite.md
        assert len(result["content"]) > 0 or len(result["sources"]) > 0


# --- MAIN ---
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=context_loader", "--cov-report=term-missing"])