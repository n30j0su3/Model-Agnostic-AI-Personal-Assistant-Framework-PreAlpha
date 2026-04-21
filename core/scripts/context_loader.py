#!/usr/bin/env python3
"""
PA Framework — Context Loader
Lazy tier-based context loading with token budget tracking.

Implements ADR-001 lazy loading strategy with tiered context loading:
- Tier 0: Bootstrap (AGENTS-lite.md) ~500 tokens
- Tier 1: Essential (config, session.json) ~1000 tokens
- Tier 2: Context (PRPs, recent logs) ~2000 tokens [LAZY]
- Tier 3: Reference (templates) [LAZY]
- Tier 4: Historical (archive) [LAZY]

Usage:
    from context_loader import ContextLoader, TokenBudgetTracker
    
    loader = ContextLoader()
    bootstrap = loader.load_tier(0)  # Loads immediately
    context = loader.load_tier(2)    # Lazy loaded when accessed

Version: 1.0.0
Author: PA Framework Team
"""

import json
import os
import time
from pathlib import Path
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field


# --- PATHS ---
SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
REPO_ROOT = CORE_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
SESSIONS_DIR = CONTEXT_DIR / "sessions"


# --- TOKEN ESTIMATION ---
def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    Uses ~4 chars per token as approximation (GPT-style).
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


# --- TOKEN BUDGET TRACKER ---
@dataclass
class TokenBudget:
    """Token budget configuration for a tier."""
    tier: int
    max_tokens: int
    description: str


class TokenBudgetTracker:
    """
    Tracks token usage across tiers with budget enforcement.
    
    Usage:
        tracker = TokenBudgetTracker()
        tracker.track("tier_0", 450)
        if tracker.check_budget("tier_0", 100):
            # Load more content
            pass
    """
    
    # Tier token budgets per ADR-001
    TIER_BUDGETS = {
        0: TokenBudget(tier=0, max_tokens=500, description="Bootstrap"),
        1: TokenBudget(tier=1, max_tokens=1000, description="Essential"),
        2: TokenBudget(tier=2, max_tokens=2000, description="Context"),
        3: TokenBudget(tier=3, max_tokens=5000, description="Reference"),
        4: TokenBudget(tier=4, max_tokens=10000, description="Historical"),
    }
    
    def __init__(self):
        self.usage: Dict[int, int] = {tier: 0 for tier in self.TIER_BUDGETS}
        self.load_times: Dict[int, float] = {}
    
    def track(self, tier: int, tokens: int) -> bool:
        """
        Track token usage for a tier.
        Returns True if within budget, False if exceeded.
        """
        if tier not in self.TIER_BUDGETS:
            raise ValueError(f"Invalid tier: {tier}")
        
        budget = self.TIER_BUDGETS[tier]
        self.usage[tier] += tokens
        return self.usage[tier] <= budget.max_tokens
    
    def check_budget(self, tier: int, additional_tokens: int = 0) -> bool:
        """Check if tier has budget remaining for additional tokens."""
        if tier not in self.TIER_BUDGETS:
            return False
        budget = self.TIER_BUDGETS[tier]
        return (self.usage[tier] + additional_tokens) <= budget.max_tokens
    
    def get_remaining(self, tier: int) -> int:
        """Get remaining token budget for a tier."""
        if tier not in self.TIER_BUDGETS:
            return 0
        budget = self.TIER_BUDGETS[tier]
        return max(0, budget.max_tokens - self.usage[tier])
    
    def record_load_time(self, tier: int, duration: float) -> None:
        """Record load time for a tier."""
        self.load_times[tier] = duration
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "usage": dict(self.usage),
            "budgets": {t: b.max_tokens for t, b in self.TIER_BUDGETS.items()},
            "remaining": {t: self.get_remaining(t) for t in self.TIER_BUDGETS},
            "load_times": dict(self.load_times),
        }


def track_tokens(func: Callable) -> Callable:
    """
    Decorator to track token usage for tier loading functions.
    
    Expects function to return dict with 'content' key containing text.
    Adds 'tokens' and 'load_time' to return dict.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        load_time = time.time() - start_time
        
        if isinstance(result, dict):
            if 'content' in result and isinstance(result['content'], str):
                result['tokens'] = estimate_tokens(result['content'])
            result['load_time'] = load_time
        
        return result
    return wrapper


# --- CONTEXT LOADER ---
class ContextLoader:
    """
    Lazy tier-based context loader for PA Framework.
    
    Implements ADR-001 lazy loading strategy:
    - Tiers 0-1 load immediately (bootstrap + essential)
    - Tiers 2-4 load lazily (only when accessed)
    
    Usage:
        loader = ContextLoader()
        
        # Load bootstrap (Tier 0)
        bootstrap = loader.load_tier(0)
        
        # Load essential config (Tier 1)
        config = loader.load_tier(1)
        
        # Lazy load context (Tier 2)
        context = loader.load_tier(2)
    """
    
    def __init__(
        self,
        repo_root: Optional[Path] = None,
        tracker: Optional[TokenBudgetTracker] = None
    ):
        """
        Initialize ContextLoader.
        
        Args:
            repo_root: Repository root path (auto-detected if None)
            tracker: TokenBudgetTracker instance (created if None)
        """
        self.repo_root = repo_root or REPO_ROOT
        self.context_dir = self.repo_root / "core" / ".context"
        self.knowledge_dir = self.context_dir / "knowledge"
        self.sessions_dir = self.context_dir / "sessions"
        
        # Token budget tracker
        self.tracker = tracker or TokenBudgetTracker()
        
        # Lazy-loaded cache for tiers 2-4
        self._cache: Dict[int, Optional[Dict[str, Any]]] = {
            0: None, 1: None, 2: None, 3: None, 4: None
        }
        
        # AGENTS-lite.md path (Tier 0)
        self.agents_lite_path = self.repo_root / "AGENTS-lite.md"
        if not self.agents_lite_path.exists():
            # Try alternate location
            self.agents_lite_path = self.repo_root / "Model-Agnostic-AI-Personal-Assistant-Framework" / "AGENTS-lite.md"
    
    @track_tokens
    def load_tier(self, tier: int) -> Dict[str, Any]:
        """
        Load context for a specific tier.
        
        Args:
            tier: Tier number (0-4)
            
        Returns:
            Dict with 'content', 'tokens', 'load_time', 'tier', 'sources'
        """
        if tier not in range(5):
            raise ValueError(f"Invalid tier: {tier}. Must be 0-4.")
        
        # Check cache for lazy tiers
        if self._cache[tier] is not None:
            return self._cache[tier]
        
        # Load based on tier
        loaders = {
            0: self._load_tier_0,
            1: self._load_tier_1,
            2: self._load_tier_2,
            3: self._load_tier_3,
            4: self._load_tier_4,
        }
        
        result = loaders[tier]()
        
        # Track tokens
        if 'tokens' in result:
            self.tracker.track(tier, result['tokens'])
        
        # Cache result for lazy tiers (2-4)
        if tier >= 2:
            self._cache[tier] = result
        
        return result
    
    def _load_tier_0(self) -> Dict[str, Any]:
        """Load Tier 0: Bootstrap (AGENTS-lite.md)."""
        sources = []
        content_parts = []
        
        # Load AGENTS-lite.md
        if self.agents_lite_path.exists():
            content = self.agents_lite_path.read_text(encoding='utf-8')
            content_parts.append(content)
            sources.append(str(self.agents_lite_path))
        
        combined = "\n\n".join(content_parts)
        tokens = estimate_tokens(combined)
        
        # Check budget (account for truncation marker tokens)
        truncation_marker = "\n... [truncated]"
        marker_tokens = estimate_tokens(truncation_marker)
        if tokens > TokenBudgetTracker.TIER_BUDGETS[0].max_tokens:
            # Truncate to budget minus marker size
            target_tokens = TokenBudgetTracker.TIER_BUDGETS[0].max_tokens - marker_tokens
            max_chars = target_tokens * 4
            combined = combined[:max_chars] + truncation_marker
            tokens = estimate_tokens(combined)
        
        return {
            "tier": 0,
            "description": "Bootstrap",
            "content": combined,
            "tokens": tokens,
            "sources": sources,
        }
    
    def _load_tier_1(self) -> Dict[str, Any]:
        """Load Tier 1: Essential (config, session.json)."""
        sources = []
        content_parts = []
        
        # Load MASTER.md (user config)
        master_path = self.context_dir / "MASTER.md"
        if master_path.exists():
            content = master_path.read_text(encoding='utf-8')
            content_parts.append(f"=== MASTER.md ===\n{content}")
            sources.append(str(master_path))
        
        # Load session index
        sessions_index = self.knowledge_dir / "sessions-index.json"
        if sessions_index.exists():
            try:
                with open(sessions_index, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Summarize recent sessions
                recent = data.get('sessions', [])[:5] if isinstance(data, dict) else []
                content_parts.append(f"=== Recent Sessions ===\n{json.dumps(recent, indent=2)}")
                sources.append(str(sessions_index))
            except (json.JSONDecodeError, IOError):
                pass
        
        # Load profile
        profile_path = self.context_dir / "profile.md"
        if profile_path.exists():
            content = profile_path.read_text(encoding='utf-8')
            content_parts.append(f"=== Profile ===\n{content}")
            sources.append(str(profile_path))
        
        combined = "\n\n".join(content_parts)
        tokens = estimate_tokens(combined)
        
        # Check budget
        if tokens > TokenBudgetTracker.TIER_BUDGETS[1].max_tokens:
            max_chars = TokenBudgetTracker.TIER_BUDGETS[1].max_tokens * 4
            combined = combined[:max_chars] + "\n... [truncated]"
            tokens = estimate_tokens(combined)
        
        return {
            "tier": 1,
            "description": "Essential",
            "content": combined,
            "tokens": tokens,
            "sources": sources,
        }
    
    def _load_tier_2(self) -> Dict[str, Any]:
        """Load Tier 2: Context (PRPs, recent logs)."""
        sources = []
        content_parts = []
        
        # Load recent session files (last 3)
        if self.sessions_dir.exists():
            session_files = sorted(
                self.sessions_dir.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:3]
            
            for sf in session_files:
                try:
                    content = sf.read_text(encoding='utf-8')
                    # Truncate long sessions
                    if len(content) > 2000:
                        content = content[:2000] + "\n... [truncated]"
                    content_parts.append(f"=== Session: {sf.stem} ===\n{content}")
                    sources.append(str(sf))
                except IOError:
                    pass
        
        # Load playbooks summary
        playbooks_dir = self.knowledge_dir / "playbooks"
        if playbooks_dir.exists():
            playbook_files = list(playbooks_dir.glob("*.md"))
            if playbook_files:
                pb_summary = f"=== Playbooks ({len(playbook_files)} available) ===\n"
                pb_summary += "\n".join(f"- {pb.name}" for pb in playbook_files[:10])
                content_parts.append(pb_summary)
                sources.append(str(playbooks_dir))
        
        combined = "\n\n".join(content_parts)
        tokens = estimate_tokens(combined)
        
        if tokens > TokenBudgetTracker.TIER_BUDGETS[2].max_tokens:
            max_chars = TokenBudgetTracker.TIER_BUDGETS[2].max_tokens * 4
            combined = combined[:max_chars] + "\n... [truncated]"
            tokens = estimate_tokens(combined)
        
        return {
            "tier": 2,
            "description": "Context",
            "content": combined,
            "tokens": tokens,
            "sources": sources,
        }
    
    def _load_tier_3(self) -> Dict[str, Any]:
        """Load Tier 3: Reference (templates, examples)."""
        sources = []
        content_parts = []
        
        # Load templates
        templates = [
            self.context_dir / "MASTER.template.md",
            self.context_dir / "quick-start.md",
        ]
        
        for template_path in templates:
            if template_path.exists():
                try:
                    content = template_path.read_text(encoding='utf-8')
                    content_parts.append(f"=== {template_path.name} ===\n{content}")
                    sources.append(str(template_path))
                except IOError:
                    pass
        
        # Load navigation
        nav_path = self.context_dir / "navigation.md"
        if nav_path.exists():
            try:
                content = nav_path.read_text(encoding='utf-8')
                content_parts.append(f"=== Navigation ===\n{content}")
                sources.append(str(nav_path))
            except IOError:
                pass
        
        combined = "\n\n".join(content_parts)
        tokens = estimate_tokens(combined)
        
        return {
            "tier": 3,
            "description": "Reference",
            "content": combined,
            "tokens": tokens,
            "sources": sources,
        }
    
    def _load_tier_4(self) -> Dict[str, Any]:
        """Load Tier 4: Historical (archive, old sessions)."""
        sources = []
        content_parts = []
        
        # Load older sessions (beyond recent 3)
        if self.sessions_dir.exists():
            session_files = sorted(
                self.sessions_dir.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[3:10]  # Sessions 4-10
            
            for sf in session_files:
                try:
                    content = sf.read_text(encoding='utf-8')
                    # Heavily truncate historical
                    if len(content) > 500:
                        content = content[:500] + "\n... [historical excerpt]"
                    content_parts.append(f"=== Historical: {sf.stem} ===\n{content}")
                    sources.append(str(sf))
                except IOError:
                    pass
        
        # Load backups index
        backups_dir = self.context_dir / "backups"
        if backups_dir.exists():
            backup_count = len(list(backups_dir.glob("**/*")))
            content_parts.append(f"=== Backups ===\n{backup_count} backup files available")
            sources.append(str(backups_dir))
        
        combined = "\n\n".join(content_parts)
        tokens = estimate_tokens(combined)
        
        return {
            "tier": 4,
            "description": "Historical",
            "content": combined,
            "tokens": tokens,
            "sources": sources,
        }
    
    def load_all(self) -> Dict[int, Dict[str, Any]]:
        """
        Load all tiers (use sparingly - loads everything).
        
        Returns:
            Dict mapping tier number to content dict
        """
        results = {}
        for tier in range(5):
            results[tier] = self.load_tier(tier)
        return results
    
    def load_essential(self) -> Dict[str, Any]:
        """
        Load only essential tiers (0 and 1).
        Recommended for quick startup.
        """
        return {
            0: self.load_tier(0),
            1: self.load_tier(1),
        }
    
    def clear_cache(self) -> None:
        """Clear cached tier data (useful for refresh)."""
        self._cache = {0: None, 1: None, 2: None, 3: None, 4: None}
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current token budget status."""
        return self.tracker.get_stats()
    
    def parallel_load_tiers(self, tiers: List[int]) -> Dict[int, Dict[str, Any]]:
        """
        Load multiple tiers in parallel using ThreadPoolExecutor.
        
        Args:
            tiers: List of tier numbers to load
            
        Returns:
            Dict mapping tier number to content dict
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=len(tiers)) as executor:
            futures = {executor.submit(self.load_tier, tier): tier for tier in tiers}
            
            for future in as_completed(futures, timeout=30):
                tier = futures[future]
                try:
                    results[tier] = future.result()
                except Exception as e:
                    results[tier] = {
                        "tier": tier,
                        "error": str(e),
                        "content": "",
                        "tokens": 0,
                    }
        
        return results


# --- CLI ENTRY POINT ---
def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="PA Framework Context Loader")
    parser.add_argument("--tier", "-t", type=int, default=0,
                        help="Tier to load (0-4)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Load all tiers")
    parser.add_argument("--essential", "-e", action="store_true",
                        help="Load essential tiers (0-1)")
    parser.add_argument("--stats", "-s", action="store_true",
                        help="Show budget stats after loading")
    
    args = parser.parse_args()
    
    loader = ContextLoader()
    
    if args.all:
        results = loader.load_all()
        for tier, data in results.items():
            print(f"\n=== Tier {tier}: {data.get('description', 'Unknown')} ===")
            print(f"Tokens: {data.get('tokens', 0)}")
            print(f"Sources: {len(data.get('sources', []))}")
    elif args.essential:
        results = loader.load_essential()
        for tier, data in results.items():
            print(f"\n=== Tier {tier}: {data.get('description', 'Unknown')} ===")
            print(f"Tokens: {data.get('tokens', 0)}")
    else:
        result = loader.load_tier(args.tier)
        print(f"\n=== Tier {args.tier}: {result.get('description', 'Unknown')} ===")
        print(f"Tokens: {result.get('tokens', 0)}")
        print(f"Sources: {result.get('sources', [])}")
        print(f"\nContent Preview (first 500 chars):\n")
        print(result.get('content', '')[:500])
    
    if args.stats:
        stats = loader.get_budget_status()
        print("\n=== Token Budget Stats ===")
        print(f"Usage: {stats['usage']}")
        print(f"Remaining: {stats['remaining']}")


if __name__ == "__main__":
    main()