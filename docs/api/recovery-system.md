# Recovery System API Reference

**Modules**: 
- `core/recovery/orchestrator.py` (RecoveryOrchestrator)
- `core/recovery/triggers.py` (Error detection and triggers)

**Version**: v1.0.0  
**Status**: ✅ Frozen (v0.3.8-alpha)  

---

## Overview

The Recovery System provides automated error classification and recovery orchestration using the ADR-004 taxonomy. It matches errors to playbooks (PB-001 through PB-009) and executes recovery actions.

### ADR-004 Taxonomy Categories

| Category | Description | Example Errors |
|----------|-------------|----------------|
| `network` | Connection, timeout, DNS errors | ConnectionError, TimeoutError |
| `api` | HTTP status, rate-limit, auth errors | HTTPError, RateLimitError |
| `file_system` | File I/O, permissions, paths | FileNotFoundError, PermissionError |
| `authentication` | Credential, token, session errors | AuthenticationError, TokenExpiredError |
| `configuration` | Config, environment, parse errors | ConfigParserError, EnvironmentError |
| `data_integrity` | Encoding, parsing, schema errors | UnicodeDecodeError, JSONDecodeError |
| `resource` | Memory, subprocess, system errors | MemoryError, SubprocessError |

---

## Module: triggers.py

Error classification and recovery trigger logic.

### Constants

#### `TAXONOMY_MAP: Dict[str, str]`

Maps Python exception class names to ADR-004 taxonomy categories.

```python
{
    "ConnectionError": "network",
    "FileNotFoundError": "file_system",
    "JSONDecodeError": "data_integrity",
    "MemoryError": "resource",
    # ... (full mapping in module)
}
```

---

#### `KEYWORD_PATTERNS: Dict[str, List[str]]`

Keyword patterns for fuzzy error classification by category.

```python
{
    "network": ["connection refused", "timed out", "dns", ...],
    "api": ["status 4", "rate limit", "unauthorized", ...],
    "file_system": ["no such file", "permission denied", ...],
    # ... (full patterns in module)
}
```

---

#### `SKIP_RECOVERY_TYPES: Set[str]`

Exception types that should NOT trigger recovery (too trivial / dev errors).

```python
{
    "KeyboardInterrupt",
    "SystemExit",
    "GeneratorExit",
    "StopIteration",
    "AssertionError",
    "SyntaxError",
    # ... (full list in module)
}
```

---

### Functions

#### `detect_error_type(error: BaseException | Dict | str) -> str`

Classify an error into an ADR-004 taxonomy category.

**Parameters:**
- `error`: An exception instance, dict with `type`/`message` keys, or raw error message string

**Returns:**
- `str`: One of the 7 ADR-004 categories, or `"unknown"`

**Example:**
```python
from recovery.triggers import detect_error_type

category = detect_error_type(FileNotFoundError("config.yaml"))
# Returns: "file_system"

category = detect_error_type({"type": "ConnectionError", "message": "refused"})
# Returns: "network"

category = detect_error_type("out of memory")
# Returns: "resource"
```

---

#### `should_trigger_recovery(error: BaseException | Dict | str) -> bool`

Decide whether automated recovery should be attempted.

**Parameters:**
- `error`: Error to evaluate

**Returns:**
- `bool`: True if recovery should be attempted, False otherwise

**Behavior:**
Returns `False` for:
- Skip-list exception types (KeyboardInterrupt, SyntaxError, etc.)
- Dict/string errors with no recoverable information

Returns `True` for all other errors (best-effort recovery).

**Example:**
```python
from recovery.triggers import should_trigger_recovery

should_trigger_recovery(FileNotFoundError("x"))  # True
should_trigger_recovery(KeyboardInterrupt())     # False
should_trigger_recovery(SyntaxError("invalid"))  # False
```

---

## Module: orchestrator.py

Error-to-playbook matching and recovery execution.

### Class: RecoveryOrchestrator

Match errors to playbooks and execute recovery actions.

#### Constructor

```python
def __init__(self, playbooks_dir: Optional[Path] = None) -> None
```

**Parameters:**
- `playbooks_dir` (Optional[Path]): Path to directory containing `index.json` and PB-*.md playbook files. Defaults to `core/.context/knowledge/playbooks/`

**Example:**
```python
from recovery.orchestrator import RecoveryOrchestrator

orchestrator = RecoveryOrchestrator()
# Or with custom playbooks directory:
orchestrator = RecoveryOrchestrator(playbooks_dir=Path("/custom/playbooks"))
```

---

#### Methods

##### `match_playbook(error: BaseException | Dict | str) -> Optional[str]`

Return the best playbook ID for the given error.

**Parameters:**
- `error`: Exception instance, dict with `type`/`message`, or string

**Returns:**
- `Optional[str]`: Playbook ID (e.g., `"PB-001"`) or `None`

**Behavior:**
1. Uses ADR-004 taxonomy category → playbook mapping
2. Falls back to keyword matching against playbook index

**Example:**
```python
playbook_id = orchestrator.match_playbook(FileNotFoundError("config.json"))
# Returns: "PB-002"

playbook_id = orchestrator.match_playbook(UnicodeDecodeError("utf-8", b"", 0, 1, "error"))
# Returns: "PB-001"
```

---

##### `execute_playbook(playbook_id: str, context: Optional[Dict] = None) -> Dict`

Execute a recovery playbook.

**Parameters:**
- `playbook_id` (str): Playbook identifier (e.g., `"PB-001"`)
- `context` (Optional[Dict]): Additional context (file paths, raw content, retry counters, etc.)

**Returns:**
- `Dict` with keys:
  - `playbook_id` (str): The playbook that was executed
  - `status` (str): `"success"`, `"failed"`, or `"no_action"`
  - `timestamp` (str): ISO-8601 timestamp
  - `message` (str): Human-readable summary

**Example:**
```python
result = orchestrator.execute_playbook("PB-002", {
    "file_path": "/path/to/missing/file.txt"
})
print(result["status"])  # "success" or "failed"
```

---

##### `recover(error: BaseException | Dict | str, context: Optional[Dict] = None) -> Dict`

End-to-end recovery: classify → match → execute.

Convenience method combining `match_playbook` and `execute_playbook`.

**Parameters:**
- `error`: The error to recover from
- `context` (Optional[Dict]): Optional context dict

**Returns:**
- `Dict`: Execution result dict, or dict with `status="skipped"` if recovery not triggered

**Example:**
```python
try:
    risky_operation()
except Exception as e:
    result = orchestrator.recover(e, {"file_path": str(path)})
    if result["status"] == "success":
        print("Recovery successful!")
```

---

##### `register_action(playbook_id: str, action: Callable[[Dict], bool]) -> None`

Register or override a recovery action for a playbook.

**Parameters:**
- `playbook_id` (str): Playbook identifier
- `action` (Callable[[Dict], bool]): Callable accepting `context: Dict`, returning `bool`

**Example:**
```python
def custom_recovery_action(context: Dict) -> bool:
    # Custom recovery logic
    file_path = context.get("file_path")
    # ... recovery logic ...
    return True  # Success

orchestrator.register_action("PB-CUSTOM", custom_recovery_action)
```

---

##### `history: List[Dict]` (Property)

Return a copy of the execution history.

**Returns:**
- `List[Dict]`: List of all execution result dicts

**Example:**
```python
for entry in orchestrator.history:
    print(f"{entry['playbook_id']}: {entry['status']} at {entry['timestamp']}")
```

---

## Built-in Recovery Actions

| Playbook ID | Category | Action Description |
|-------------|----------|-------------------|
| PB-001 | data_integrity | Fix encoding (UTF-8 → Latin-1 fallback) |
| PB-002 | file_system | Create missing file/directory |
| PB-003 | data_integrity | Strip BOM/trailing commas from JSON |
| PB-004 | network/api/resource | Signal retry for subprocess timeout |
| PB-005 | file_system | Resolve relative path against base directory |
| PB-006 | configuration | YAML parse with fallback to defaults |
| PB-007 | network | Signal git-retry (stash + pull) |
| PB-008 | resource | Wait-and-retry for lock contention |
| PB-009 | authentication | Signal auth-retry (refresh credentials) |

---

## Category to Playbook Mapping

```python
CATEGORY_TO_PLAYBOOKS = {
    "network": ["PB-004"],
    "api": ["PB-004"],
    "file_system": ["PB-002", "PB-005"],
    "authentication": ["PB-009"],
    "configuration": ["PB-006"],
    "data_integrity": ["PB-001", "PB-003"],
    "resource": ["PB-004"],
}
```

---

## Usage Examples

### Basic Error Recovery

```python
from recovery.orchestrator import RecoveryOrchestrator

orchestrator = RecoveryOrchestrator()

try:
    with open("config.json", "r") as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    result = orchestrator.recover(e, {"raw_content": str(e)})
    if result["status"] == "success":
        print("JSON recovery successful!")
```

### Manual Playbook Execution

```python
from recovery.orchestrator import RecoveryOrchestrator

orchestrator = RecoveryOrchestrator()

# Match error to playbook
error = FileNotFoundError("missing.txt")
playbook_id = orchestrator.match_playbook(error)
print(f"Matched playbook: {playbook_id}")  # PB-002

# Execute with context
result = orchestrator.execute_playbook(playbook_id, {
    "file_path": "/path/to/missing.txt"
})
print(f"Status: {result['status']}")
```

### Custom Recovery Action

```python
from recovery.orchestrator import RecoveryOrchestrator

orchestrator = RecoveryOrchestrator()

def backup_recovery(context: Dict) -> bool:
    """Restore from backup file."""
    from pathlib import Path
    
    file_path = context.get("file_path")
    if not file_path:
        return False
    
    backup_path = Path(file_path).with_suffix(".bak")
    if backup_path.exists():
        Path(file_path).write_text(backup_path.read_text())
        return True
    return False

orchestrator.register_action("PB-BACKUP", backup_recovery)

# Use custom action
result = orchestrator.execute_playbook("PB-BACKUP", {
    "file_path": "config.json"
})
```

### Recovery History Analysis

```python
from recovery.orchestrator import RecoveryOrchestrator

orchestrator = RecoveryOrchestrator()

# Execute several recoveries...
# orchestrator.recover(...)

# Analyze history
history = orchestrator.history
success_count = sum(1 for h in history if h["status"] == "success")
print(f"Success rate: {success_count}/{len(history)} ({100*success_count/len(history):.1f}%)")
```

---

## Integration with ErrorLogger

The Recovery System integrates with ErrorLogger v2:

```python
from error_logger import ErrorLogger
from recovery.orchestrator import RecoveryOrchestrator

logger = ErrorLogger()
orchestrator = RecoveryOrchestrator()

try:
    operation()
except Exception as e:
    # Log the error
    error_id = logger.log_error({
        "type": type(e).__name__,
        "message": str(e),
        "file": __file__,
        "line": 42
    })
    
    # Attempt recovery
    result = orchestrator.recover(e)
    
    # Mark as resolved if recovery succeeded
    if result["status"] == "success":
        logger.resolve_error(error_id)
```

---

## Testing

### Unit Test Example

```python
import pytest
from recovery.orchestrator import RecoveryOrchestrator
from recovery.triggers import detect_error_type, should_trigger_recovery

def test_detect_error_type():
    assert detect_error_type(FileNotFoundError("x")) == "file_system"
    assert detect_error_type(ConnectionError("x")) == "network"
    assert detect_error_type(MemoryError("x")) == "resource"

def test_should_trigger_recovery():
    assert should_trigger_recovery(FileNotFoundError("x")) is True
    assert should_trigger_recovery(KeyboardInterrupt()) is False
    assert should_trigger_recovery(SyntaxError("x")) is False

def test_orchestrator_match():
    orchestrator = RecoveryOrchestrator()
    playbook_id = orchestrator.match_playbook(FileNotFoundError("x"))
    assert playbook_id == "PB-002"

def test_orchestrator_execute():
    orchestrator = RecoveryOrchestrator()
    result = orchestrator.execute_playbook("PB-002", {
        "file_path": "/tmp/test_file.txt"
    })
    assert result["playbook_id"] == "PB-002"
    assert result["status"] in ("success", "failed")
```

---

## Error Handling

### No Matching Playbook

```python
orchestrator = RecoveryOrchestrator()
result = orchestrator.match_playbook(ValueError("custom error"))
# May return None if no match found
```

### Action Execution Failure

```python
result = orchestrator.execute_playbook("PB-001", {})
# Returns: {"status": "failed", "message": "Playbook PB-001 action returned False"}
```

### Invalid Playbook ID

```python
result = orchestrator.execute_playbook("PB-INVALID", {})
# Returns: {"status": "no_action", "message": "No action registered for PB-INVALID"}
```

---

## Performance Considerations

### Playbook Index Loading

The playbook index (`index.json`) is loaded once at initialization. For large playbook directories, consider lazy loading.

### Recovery Action Timeout

Recovery actions should be fast (<100ms). For long-running recovery, implement async patterns or background execution.

---

## Related Documentation

- [ADR-004](../../design/adr-004-error-taxonomy.md) — Error classification taxonomy
- [ContextLoader API](context-loader.md) — Context loading system
- [ErrorLogger API](knowledge-management.md) — Error logging and pattern detection

---

*Last updated: April 17, 2026*  
*Phase 5 Workstream 1 — API Stabilization*
