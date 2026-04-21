# Cross-Platform Path Handling

> **Platforms**: Windows, macOS, Linux | **Pattern**: Use pathlib + tempfile

---

## 🎯 Best Practices

### 1. Relative Paths

```python
from pathlib import Path

# CORRECT: Relative to script location
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# WRONG: Hardcoded absolute paths
SCRIPT_DIR = "/home/user/project/core/scripts"  # ❌
```

### 2. Temp Directory

```python
import tempfile

# CORRECT: Platform-agnostic temp
temp_dir = Path(tempfile.gettempdir()) / "pa-framework"

# WRONG: Linux-specific
temp_dir = Path("/tmp/pa-framework")  # ❌ Windows fails
```

### 3. Home Directory

```python
from pathlib import Path

# CORRECT: Platform-agnostic home
home = Path.home()

# WRONG: Hardcoded
home = Path("/home/user")  # ❌ macOS is /Users/, Windows is C:\Users\
```

---

## 📋 Path Resolution Patterns

| Need | Pattern | Cross-Platform |
|------|---------|----------------|
| Script location | `Path(__file__).parent` | ✅ |
| Project root | `SCRIPT_DIR.parent.parent` | ✅ |
| Temp files | `tempfile.gettempdir()` | ✅ |
| User home | `Path.home()` | ✅ |
| Config dir | `PROJECT_ROOT / "config"` | ✅ |

---

## 🔴 Common Pitfalls

### Pitfall 1: Linux-specific `/tmp`

```python
# WRONG
temp_file = Path("/tmp/session.db")

# CORRECT
temp_file = Path(tempfile.gettempdir()) / "session.db"
```

### Pitfall 2: Hardcoded home path

```python
# WRONG
data_dir = Path("/home/freakingjson/.pa-framework")

# CORRECT
data_dir = Path.home() / ".pa-framework"
# OR: Store in project directory
data_dir = PROJECT_ROOT / "core" / ".context" / "sessions"
```

### Pitfall 3: Case sensitivity

```python
# Windows: AGENTS.md = agents.md (same file)
# Git: AGENTS.md ≠ agents.md (different files)

# Use consistent casing
config_file = PROJECT_ROOT / "AGENTS.md"  # Always uppercase
```

---

## 📁 Framework Standard

**Location**: Data persists in framework directory, NOT in user home.

```python
# PA Framework standard
SESSIONS_DIR = PROJECT_ROOT / "core" / ".context" / "sessions"
KNOWLEDGE_DIR = PROJECT_ROOT / "core" / ".context" / "knowledge"
VITALS_DIR = PROJECT_ROOT / "core" / ".context" / "vitals"
```

**Benefit**: Zero-config, portable, fresh ZIP works out of the box.

---

*See also: [Import Hyphens](../troubleshooting/import-hyphens.md)*