# Import Hyphens Problem

> **Error**: `ModuleNotFoundError` | **Cause**: Python can't import files with `-` in names

---

## 🔴 Problem

Python module names must use underscores (`_`), not hyphens (`-`). Files like:

- `session-start.py` → Cannot be imported
- `context-loader.py` → Cannot be imported
- `knowledge-extractor.py` → Cannot be imported

**Error**:
```python
import session-start  # SyntaxError: invalid syntax
from context-loader import ContextLoader  # ModuleNotFoundError
```

---

## ✅ Solution

### Rename Pattern

| Old Name (❌) | New Name (✅) |
|---------------|---------------|
| `session-start.py` | `session_start.py` |
| `session-end.py` | `session_end.py` |
| `context-loader.py` | `context_loader.py` |
| `knowledge-pattern-detector.py` | `knowledge_pattern_detector.py` |
| `knowledge-extractor.py` | `knowledge_extractor.py` |
| `interaction-logger.py` | `interaction_logger.py` |
| `error-logger.py` | `error_logger.py` |
| `framework-guardian.py` | `framework_guardian.py` |

### Import Fix

```python
# Before (fails):
from session-start import main

# After (works):
from session_start import main
```

### Reference Fix

```python
# In other scripts, update subprocess calls:
# Before:
subprocess.run(["python", "session-start.py"])

# After:
subprocess.run(["python", "session_start.py"])
```

---

## 📋 Scripts Renamed (FASE 1)

**Total**: 34 scripts renamed in core/scripts/

```
session_start.py ✓
session_end.py ✓
session_autosave.py ✓
session_indexer.py ✓
context_loader.py ✓
knowledge_pattern_detector.py ✓
knowledge_extractor.py ✓
interaction_logger.py ✓
error_logger.py ✓
framework_guardian.py ✓
phase4_metrics.py ✓
kb_init.py ✓
...
```

---

## 🧪 Validation

```bash
# Python syntax check
python3 -m py_compile core/scripts/session_start.py
# Expected: No errors

# Import test
python3 -c "from session_start import main; print('OK')"
# Expected: OK
```

---

## 📁 Related Files

| File | Status |
|------|--------|
| All `core/scripts/*.py` | Renamed to underscores |
| `core/scripts/tests/*.py` | Imports updated |
| `AGENTS.md` | References updated |

---

*See also: [Windows I/O Errors](windows-io-errors.md), [Cross-Platform Paths](../patterns/cross-platform.md)*