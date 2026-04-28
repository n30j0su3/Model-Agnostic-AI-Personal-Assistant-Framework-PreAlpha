# ContextLoader API Reference

**Module**: `core/scripts/context_loader.py`  
**Version**: v1.0.0  
**Status**: ✅ Frozen (v0.3.8-alpha)  

---

## Overview

ContextLoader implements ADR-001 lazy loading strategy with tiered context loading for the PA Framework. It provides efficient, budget-controlled loading of context data across 5 tiers.

### Key Features

- **Tier-based loading**: 5 tiers (0-4) with increasing scope
- **Token budget tracking**: Enforces per-tier token limits
- **Lazy loading**: Tiers 2-4 load only when accessed
- **Parallel loading**: Support for concurrent tier loading
- **Caching**: Automatic caching of lazy-loaded tiers

---

## Token Budget Configuration

| Tier | Name | Max Tokens | Description |
|------|------|------------|-------------|
| 0 | Bootstrap | 500 | AGENTS-lite.md, essential bootstrap |
| 1 | Essential | 1,000 | Config, session.json, profile |
| 2 | Context | 2,000 | PRPs, recent logs, sessions |
| 3 | Reference | 5,000 | Templates, examples, navigation |
| 4 | Historical | 10,000 | Archive, old sessions, backups |

---

## Classes

### TokenBudget

Dataclass representing token budget configuration for a tier.

```python
@dataclass
class TokenBudget:
    tier: int           # Tier number (0-4)
    max_tokens: int     # Maximum tokens allowed
    description: str    # Human-readable description
```

---

### TokenBudgetTracker

Tracks token usage across tiers with budget enforcement.

#### Constructor

```python
def __init__(self) -> None
```

#### Methods

##### `track(tier: int, tokens: int) -> bool`

Track token usage for a tier.

**Parameters:**
- `tier` (int): Tier number (0-4)
- `tokens` (int): Number of tokens to track

**Returns:**
- `bool`: True if within budget, False if exceeded

**Raises:**
- `ValueError`: If tier is not 0-4

**Example:**
```python
tracker = TokenBudgetTracker()
within_budget = tracker.track(0, 450)  # True
```

---

##### `check_budget(tier: int, additional_tokens: int = 0) -> bool`

Check if tier has budget remaining for additional tokens.

**Parameters:**
- `tier` (int): Tier number to check
- `additional_tokens` (int): Additional tokens to account for

**Returns:**
- `bool`: True if budget available, False otherwise

**Example:**
```python
if tracker.check_budget(2, 500):
    content = loader.load_tier(2)
```

---

##### `get_remaining(tier: int) -> int`

Get remaining token budget for a tier.

**Parameters:**
- `tier` (int): Tier number

**Returns:**
- `int`: Remaining tokens available

---

##### `record_load_time(tier: int, duration: float) -> None`

Record load time for a tier.

**Parameters:**
- `tier` (int): Tier number
- `duration` (float): Load time in seconds

---

##### `get_stats() -> Dict[str, Any]`

Get usage statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary with keys:
  - `usage`: Dict mapping tier to tokens used
  - `budgets`: Dict mapping tier to max tokens
  - `remaining`: Dict mapping tier to remaining tokens
  - `load_times`: Dict mapping tier to load time

**Example:**
```python
stats = tracker.get_stats()
print(f"Tier 0 usage: {stats['usage'][0]}/{stats['budgets'][0]}")
```

---

### ContextLoader

Lazy tier-based context loader for PA Framework.

#### Constructor

```python
def __init__(
    self,
    repo_root: Optional[Path] = None,
    tracker: Optional[TokenBudgetTracker] = None
) -> None
```

**Parameters:**
- `repo_root` (Optional[Path]): Repository root path (auto-detected if None)
- `tracker` (Optional[TokenBudgetTracker]): TokenBudgetTracker instance (created if None)

**Example:**
```python
from context_loader import ContextLoader

loader = ContextLoader()
# Or with custom paths:
loader = ContextLoader(repo_root=Path("/path/to/repo"))
```

#### Methods

##### `load_tier(tier: int) -> Dict[str, Any]`

Load context for a specific tier.

**Parameters:**
- `tier` (int): Tier number (0-4)

**Returns:**
- `Dict[str, Any]`: Dictionary with keys:
  - `tier` (int): The tier number
  - `description` (str): Tier description
  - `content` (str): Loaded content
  - `tokens` (int): Estimated token count
  - `load_time` (float): Load time in seconds
  - `sources` (List[str]): List of source file paths

**Raises:**
- `ValueError`: If tier is not 0-4

**Example:**
```python
bootstrap = loader.load_tier(0)
print(f"Loaded {bootstrap['tokens']} tokens from {len(bootstrap['sources'])} sources")
```

---

##### `load_all() -> Dict[int, Dict[str, Any]]`

Load all tiers (use sparingly — loads everything).

**Returns:**
- `Dict[int, Dict[str, Any]]`: Dict mapping tier number to content dict

**Example:**
```python
all_context = loader.load_all()
for tier, data in all_context.items():
    print(f"Tier {tier}: {data['tokens']} tokens")
```

---

##### `load_essential() -> Dict[str, Any]`

Load only essential tiers (0 and 1). Recommended for quick startup.

**Returns:**
- `Dict[str, Any]`: Dict with tiers 0 and 1

**Example:**
```python
essential = loader.load_essential()
# Returns {0: {...}, 1: {...}}
```

---

##### `clear_cache() -> None`

Clear cached tier data (useful for refresh).

**Example:**
```python
loader.clear_cache()
fresh_context = loader.load_tier(2)  # Re-loads from disk
```

---

##### `get_budget_status() -> Dict[str, Any]`

Get current token budget status.

**Returns:**
- `Dict[str, Any]`: Same as `TokenBudgetTracker.get_stats()`

---

##### `parallel_load_tiers(tiers: List[int]) -> Dict[int, Dict[str, Any]]`

Load multiple tiers in parallel using ThreadPoolExecutor.

**Parameters:**
- `tiers` (List[int]): List of tier numbers to load

**Returns:**
- `Dict[int, Dict[str, Any]]`: Dict mapping tier number to content dict

**Example:**
```python
# Load tiers 2, 3, 4 in parallel
context = loader.parallel_load_tiers([2, 3, 4])
```

---

## Decorators

### `track_tokens(func: Callable) -> Callable`

Decorator to track token usage for tier loading functions.

**Behavior:**
- Expects function to return dict with 'content' key containing text
- Adds 'tokens' and 'load_time' to return dict
- Automatically estimates tokens using 4 chars/token approximation

**Example:**
```python
@track_tokens
def load_custom_tier() -> Dict[str, Any]:
    content = "..."  # Load content
    return {"content": content, "tier": 5}
# Returns: {"content": "...", "tier": 5, "tokens": N, "load_time": X.XX}
```

---

## Utility Functions

### `estimate_tokens(text: str) -> int`

Estimate token count for text using ~4 chars per token approximation.

**Parameters:**
- `text` (str): Text to estimate

**Returns:**
- `int`: Estimated token count

**Example:**
```python
from context_loader import estimate_tokens

tokens = estimate_tokens("Hello, world!")  # ~3-4 tokens
```

---

## Usage Examples

### Basic Usage

```python
from context_loader import ContextLoader

# Initialize loader
loader = ContextLoader()

# Load bootstrap (immediate)
bootstrap = loader.load_tier(0)
print(f"Bootstrap: {bootstrap['tokens']} tokens")

# Load essential config (immediate)
config = loader.load_tier(1)

# Lazy load context (only when needed)
context = loader.load_tier(2)

# Check budget status
stats = loader.get_budget_status()
print(f"Remaining Tier 2: {stats['remaining'][2]} tokens")
```

### Advanced: Custom Token Budget

```python
from context_loader import ContextLoader, TokenBudgetTracker

# Create custom tracker
tracker = TokenBudgetTracker()

# Pre-allocate some tokens
tracker.track(0, 100)  # Reserve 100 tokens

# Create loader with custom tracker
loader = ContextLoader(tracker=tracker)

# Load with remaining budget
if tracker.check_budget(1, 500):
    config = loader.load_tier(1)
```

### Parallel Loading

```python
from context_loader import ContextLoader

loader = ContextLoader()

# Load multiple tiers in parallel
results = loader.parallel_load_tiers([2, 3, 4])

for tier, data in sorted(results.items()):
    if 'error' in data:
        print(f"Tier {tier} failed: {data['error']}")
    else:
        print(f"Tier {tier}: {data['tokens']} tokens in {data['load_time']:.2f}s")
```

---

## Error Handling

### Tier Loading Errors

If a tier fails to load, the error is captured in the result:

```python
result = loader.load_tier(2)
if 'error' in result:
    print(f"Loading failed: {result['error']}")
```

### Parallel Loading Errors

Parallel loading captures errors per-tier:

```python
results = loader.parallel_load_tiers([0, 1, 2])
for tier, data in results.items():
    if 'error' in data:
        print(f"Tier {tier} error: {data['error']}")
```

---

## Performance Considerations

### Cold vs Warm Load

- **Cold load**: First access to lazy tiers reads from disk (~100-500ms per tier)
- **Warm load**: Subsequent access uses cache (<10ms)

### Token Estimation

Token estimation uses a simple 4 chars/token approximation. For more accurate counts, integrate with tiktoken or similar libraries.

### Memory Usage

Lazy tiers (2-4) are cached after first load. Use `clear_cache()` to free memory:

```python
loader.clear_cache()  # Release cached tier data
```

---

## Testing

### Unit Test Example

```python
import pytest
from context_loader import ContextLoader, TokenBudgetTracker

def test_token_budget_tracker():
    tracker = TokenBudgetTracker()
    assert tracker.check_budget(0, 400)  # Within 500 token budget
    tracker.track(0, 450)
    assert not tracker.check_budget(0, 100)  # Exceeds budget

def test_context_loader_tier_0():
    loader = ContextLoader()
    result = loader.load_tier(0)
    assert result['tier'] == 0
    assert 'content' in result
    assert 'tokens' in result
    assert result['tokens'] <= 500  # Within budget
```

---

## Related Documentation

- [ADR-001](../../design/adr-001-lazy-loading.md) — Lazy loading strategy
- [Recovery System API](recovery-system.md) — Error recovery orchestration
- [Knowledge Management API](knowledge-management.md) — Pattern detection

---

*Last updated: April 17, 2026*  
*Phase 5 Workstream 1 — API Stabilization*
