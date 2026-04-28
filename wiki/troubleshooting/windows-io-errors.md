# Windows I/O Errors

> **Error**: `ValueError: I/O operation on closed file` | **Platform**: Windows 11

---

## 🔴 Problem

On Windows, when Python scripts run in non-interactive environments (CLI tools, subprocess calls), stdout/stderr file descriptors can be closed prematurely by the OS. This causes:

```
ValueError: I/O operation on closed file
OSError: [Errno 9] Bad file descriptor
```

---

## ✅ Solution

### Pattern: Capture Output + Targeted Exceptions

```python
import subprocess
import sys

def run_script_safe(script_path):
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--silent"],
            capture_output=True,  # CRITICAL: prevents I/O errors
            timeout=30
        )
        return result.returncode == 0
    except (ValueError, OSError, subprocess.TimeoutExpired):
        # Windows shutdown-only I/O issues
        return False
```

### Applied in session_start.py

```python
# session_shutdown() pattern (v0.3.3-alpha audit fix)
def session_shutdown():
    try:
        # Print statements wrapped
        try:
            print("🛡️ Session shutdown initiated...")
        except (ValueError, OSError):
            pass  # Windows may close stdout
        
        # Autosave with timeout
        subprocess.run([...], capture_output=True, timeout=10)
        
        # Session end with silent mode
        subprocess.run([...], capture_output=True, timeout=30)
    except (ValueError, OSError, subprocess.TimeoutExpired):
        pass  # Graceful degradation
```

---

## 📋 Root Cause Analysis

| Factor | Windows | Linux/macOS |
|--------|---------|-------------|
| Stdout behavior | Can close early | Stable |
| Stderr behavior | Can close early | Stable |
| atexit handlers | May hit closed FD | Normal execution |
| Subprocess I/O | Needs capture_output | Optional |

---

## 🧪 Test Validation

```bash
# Windows test command
python core/scripts/session_start.py

# Expected: No ValueError
# If fails: Check capture_output=True in subprocess calls
```

---

## 📁 Related Files

| File | Fix Location |
|------|--------------|
| `session_start.py` | Lines 122-136, 138-153 |
| `session_end.py` | `--silent` flag handling |
| `session_autosave.py` | Safe I/O throughout |

---

*See also: [Session Flow](../architecture/session-flow.md), [Import Hyphens](import-hyphens.md)*