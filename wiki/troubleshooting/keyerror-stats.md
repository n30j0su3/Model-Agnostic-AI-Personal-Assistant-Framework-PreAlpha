# KeyError Stats Problem

> **Error**: `KeyError: 'agents'` | **Location**: interaction_logger.py

---

## 🔴 Problem

When `interaction_logger.py` tried to access nested dictionary keys without defaults:

```python
# WRONG (causes KeyError)
stats = session_data["stats"]
agents = stats["agents"]  # KeyError if 'agents' missing
```

**Scenario**: Session data from autosave or older sessions may have incomplete stats structure.

---

## ✅ Solution

### Pattern: `.get()` with Defaults

```python
# CORRECT (FASE 2 fix)
stats = session_data.get("stats", {})
agents = stats.get("agents", [])
total = stats.get("total", 0)

# Chain of .get() calls
user_msgs = session_data.get("stats", {}).get("user_messages", 0)
```

### Applied in interaction_logger.py

```python
# Lines 45-52 (FASE 2 fix)
def log_interaction(self, session_data: dict):
    # Safe dictionary access
    stats = session_data.get("stats", {})
    agents = stats.get("agents", [])
    user_msgs = stats.get("user_messages", 0)
    assistant_msgs = stats.get("assistant_messages", 0)
    
    # No KeyError possible now
    total_interactions = user_msgs + assistant_msgs
```

---

## 📋 Dictionary Access Patterns

| Pattern | Risk | Recommendation |
|---------|------|----------------|
| `data["key"]` | KeyError | ❌ Avoid |
| `data.get("key")` | None return | ⚠️ Use with None check |
| `data.get("key", default)` | Safe | ✅ Recommended |
| `data.get("nested", {}).get("key")` | Safe | ✅ For nested |

---

## 🧪 Test Validation

```python
# Test edge cases
empty_session = {}
incomplete_session = {"stats": {}}
full_session = {"stats": {"agents": ["claude", "gemini"]}}

# All should work without KeyError
logger.log_interaction(empty_session)  # Uses defaults
logger.log_interaction(incomplete_session)  # Uses defaults
logger.log_interaction(full_session)  # Uses actual data
```

---

## 📁 Related Files

| File | Fix Location |
|------|--------------|
| `interaction_logger.py` | Lines 45-52, 78-85 |
| `session_autosave.py` | Safe dictionary building |
| `session_indexer.py` | Safe JSON parsing |

---

*See also: [Windows I/O Errors](windows-io-errors.md), [Memory System](../architecture/memory-system.md)*