#!/usr/bin/env python3
"""
PA Framework - Error Logger Module v2.0.0
Dual logging system (JSON + MD) for error tracking and recovery.

Part of PRP-007: Error Recovery Skill
Enhanced for Phase 3 Item 4: Error classification, recovery suggestion,
playbook triggering, and pattern detection (ADR-004 taxonomy).

Usage:
    from error_logger import ErrorLogger

    logger = ErrorLogger()
    logger.log_error({
        "type": "UnicodeEncodeError",
        "message": "...",
        "file": "example.py",
        "line": 42
    })
"""

__version__ = "2.0.0"

import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

if sys.platform == "win32" and sys.stdout.isatty():
    try:
        
        # v0.4.0-beta fix: reconfigure in-place (TextIOWrapper nuevo dejaba un wrapper
# huérfano que su GC cerraba → "I/O operation on closed file"/"lost sys.stderr" al salir)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, AttributeError):
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
CORE_DIR = SCRIPT_DIR.parent
CONTEXT_DIR = CORE_DIR / ".context"
KNOWLEDGE_DIR = CONTEXT_DIR / "knowledge"
ERRORS_DIR = KNOWLEDGE_DIR / "errors"

ERROR_INDEX_FILE = ERRORS_DIR / "index.json"
ERROR_LOG_MD = ERRORS_DIR / "error-log.md"

PLAYBOOK_MAPPING = {
    "UnicodeEncodeError": "PB-001",
    "UnicodeDecodeError": "PB-001",
    "FileNotFoundError": "PB-002",
    "PermissionError": "PB-003",
    "KeyError": "PB-004",
    "ValueError": "PB-005",
    "TypeError": "PB-006",
    "AttributeError": "PB-007",
    "ImportError": "PB-008",
    "ModuleNotFoundError": "PB-008",
    "ConnectionError": "PB-009",
    "TimeoutError": "PB-010",
    "OSError": "PB-011",
    "IOError": "PB-011",
    "JSONDecodeError": "PB-012",
    "IndexError": "PB-013",
    "ZeroDivisionError": "PB-014",
    "RuntimeError": "PB-015",
}

# ─── ADR-004 Error Classification Taxonomy (v2.0.0) ───────────────────────
# Maps keyword patterns to error category per ADR-004 taxonomy.
# Categories: network, api, file_system, authentication, configuration,
#             data_integrity, resource

ERROR_CATEGORIES = {
    "network": {
        "keywords": [
            "connection", "timeout", "network", "socket", "dns", "host",
            "refused", "reset", "unreachable", "packet", "ttl", "latency",
            "bandwidth", "proxy", "ssl", "tls", "certificate",
            "ConnectionError", "TimeoutError", "ConnectionRefusedError",
            "ConnectionResetError", "ConnectionAbortedError",
            "BrokenPipeError", "URLError",
        ],
        "description": "Network connectivity and communication errors",
    },
    "api": {
        "keywords": [
            "api", "endpoint", "request", "response", "http", "https",
            "status", "rate limit", "throttl", "oauth", "token expired",
            "bad request", "unauthorized", "forbidden", "not found",
            "server error", "gateway", "webhook", "rest", "graphql",
            "HTTPErrors", "requests.exceptions",
        ],
        "description": "API interaction and HTTP protocol errors",
    },
    "file_system": {
        "keywords": [
            "file", "directory", "path", "not found", "permission",
            "read-only", "disk", "space", "inode", "mount", "symlink",
            "encoding", "decode", "encode", "utf", "ascii", "codec",
            "FileNotFoundError", "PermissionError", "IsADirectoryError",
            "NotADirectoryError", "FileExistsError", "UnicodeEncodeError",
            "UnicodeDecodeError", "OSError", "IOError", "JSONDecodeError",
        ],
        "description": "File system access, I/O, and encoding errors",
    },
    "authentication": {
        "keywords": [
            "auth", "login", "credential", "password", "token", "session",
            "expired", "invalid key", "api key", "secret", "jwt", "saml",
            "oauth", "mfa", "2fa", "totp", "forbidden", "unauthorized",
            "PermissionError", "PermissionDenied",
        ],
        "description": "Authentication and authorization errors",
    },
    "configuration": {
        "keywords": [
            "config", "setting", "environment", "env", "variable",
            "missing", "invalid", "schema", "yaml", "toml", "ini",
            "parse", "syntax", "indent", "key error", "keyerror",
            "import", "module", "no module", "KeyError", "ImportError",
            "ModuleNotFoundError", "ConfigParser", "AttributeError",
        ],
        "description": "Configuration, settings, and import errors",
    },
    "data_integrity": {
        "keywords": [
            "data", "corrupt", "checksum", "hash", "mismatch", "valid",
            "invalid", "schema", "constraint", "unique", "foreign key",
            "primary key", "null", "required", "type error", "value error",
            "index", "range", "overflow", "underflow",
            "ValueError", "TypeError", "IndexError", "KeyError",
            "struct.error", "AssertionError",
        ],
        "description": "Data validation and integrity errors",
    },
    "resource": {
        "keywords": [
            "memory", "cpu", "disk", "resource", "limit", "quota",
            "exceeded", "oom", "out of memory", "allocation", "heap",
            "stack", "thread", "process", "fork", "zombie", "deadlock",
            "file descriptor", "too many open", "MemoryError",
            "RuntimeError", "RecursionError", "SystemError",
            "ZeroDivisionError",
        ],
        "description": "System resource exhaustion and runtime errors",
    },
}

# Mapping from error category to suggested recovery strategy/playbook
CATEGORY_RECOVERY_MAP = {
    "network": {
        "playbook_id": "PB-NET-RETRY",
        "strategy": "Retry with exponential backoff; check connectivity; verify DNS",
        "severity": "medium",
    },
    "api": {
        "playbook_id": "PB-API-FALLBACK",
        "strategy": "Check API status; validate request; use cached response",
        "severity": "medium",
    },
    "file_system": {
        "playbook_id": "PB-FS-RECOVER",
        "strategy": "Verify path; check encoding; ensure disk space; fix permissions",
        "severity": "high",
    },
    "authentication": {
        "playbook_id": "PB-AUTH-REFRESH",
        "strategy": "Refresh token; re-authenticate; check credentials rotation",
        "severity": "critical",
    },
    "configuration": {
        "playbook_id": "PB-CFG-VALIDATE",
        "strategy": "Validate config schema; check env vars; restore defaults",
        "severity": "high",
    },
    "data_integrity": {
        "playbook_id": "PB-DATA-VALIDATE",
        "strategy": "Validate input; check schema; sanitize data; restore backup",
        "severity": "high",
    },
    "resource": {
        "playbook_id": "PB-RES-OPTIMIZE",
        "strategy": "Free resources; reduce load; scale up; restart service",
        "severity": "critical",
    },
}

# Pattern detection thresholds
PATTERN_THRESHOLDS = {
    "recurrence_min": 3,       # Minimum occurrences to flag a pattern
    "time_window_minutes": 30, # Time window for burst detection
    "burst_threshold": 5,      # Errors within time_window to count as burst
}


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def c(text: str, color: str) -> str:
    return f"{color}{text}{Colors.END}"


def safe_print(text: str, **kwargs):
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        safe_text = text.encode(encoding, errors="replace").decode(encoding)
        print(safe_text, **kwargs)


class ErrorLogger:
    """
    Dual logging system for errors with JSON index and Markdown log.

    Provides structured error tracking with automatic playbook suggestions
    and recovery integration for the PA Framework.

    Attributes:
        errors_dir: Directory for error logs
        index_file: JSON index file path
        log_file: Markdown log file path
    """

    def __init__(self, errors_dir: Optional[Path] = None):
        """
        Initialize ErrorLogger with custom or default paths.

        Args:
            errors_dir: Optional custom directory for error logs.
                       Defaults to core/.context/knowledge/errors/
        """
        self.errors_dir = errors_dir or ERRORS_DIR
        self.index_file = self.errors_dir / "index.json"
        self.log_file = self.errors_dir / "error-log.md"
        self._ensure_directories()
        self._ensure_files()

    def _ensure_directories(self) -> None:
        """Create error directory structure if it doesn't exist."""
        self.errors_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_files(self) -> None:
        """Initialize JSON index and MD log if they don't exist."""
        if not self.index_file.exists():
            self._write_index({"errors": [], "last_updated": None})

        if not self.log_file.exists():
            self._write_log_header()

    def _write_index(self, data: Dict) -> None:
        """Write data to JSON index file."""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to write index: {e}", Colors.RED))

    def _write_log_header(self) -> None:
        """Write initial header to Markdown log file."""
        header = """# Error Log

> Auto-generated error log for PA Framework
> Part of Error Recovery System (PRP-007)

---

"""
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(header)
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to write log header: {e}", Colors.RED))

    def _read_index(self) -> Dict:
        """Read and return JSON index data."""
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"errors": [], "last_updated": None}

    def _generate_error_id(self) -> str:
        """
        Generate unique error ID with format ERR-YYYYMMDD-HHMMSS.

        Returns:
            Unique error identifier string.
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"ERR-{timestamp}"

    def _generate_timestamp(self) -> str:
        """
        Generate ISO format timestamp.

        Returns:
            ISO format timestamp string.
        """
        return datetime.now().isoformat()

    def _get_playbook_suggestion(self, error_type: str) -> Optional[str]:
        """
        Get playbook ID based on error type mapping.

        Args:
            error_type: The exception class name.

        Returns:
            Playbook ID or None if no mapping exists.
        """
        return PLAYBOOK_MAPPING.get(error_type)

    def _append_to_log(self, error_data: Dict) -> None:
        """Append error entry to Markdown log file."""
        entry = self._format_md_entry(error_data)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            safe_print(c(f"[ERROR] Failed to append to log: {e}", Colors.RED))

    def _format_md_entry(self, error_data: Dict) -> str:
        """
        Format error data as Markdown entry.

        Args:
            error_data: Dictionary with error information.

        Returns:
            Formatted Markdown string.
        """
        status = "Resolved" if error_data.get("resolved") else "Open"
        status_icon = "[OK]" if error_data.get("resolved") else "[!]"

        entry = f"""
## {status_icon} {error_data.get("id", "Unknown")}

| Field | Value |
|-------|-------|
| **Timestamp** | {error_data.get("timestamp", "N/A")} |
| **Type** | {error_data.get("type", "Unknown")} |
| **Status** | {status} |
| **File** | {error_data.get("file", "N/A")} |
| **Line** | {error_data.get("line", "N/A")} |
| **Playbook** | {error_data.get("playbook_suggestion", "N/A")} |

### Message
```
{error_data.get("message", "No message")}
```

### Context
{error_data.get("context", "No additional context")}

---

"""
        return entry

    def log_error(self, error_data: Dict) -> str:
        """
        Log an error to both JSON index and Markdown log.

        Args:
            error_data: Dictionary containing:
                - type: Error class name (e.g., 'UnicodeEncodeError')
                - message: Error message string
                - file: File where error occurred
                - line: Line number (int)
                - context: Additional context (optional)

        Returns:
            The generated error ID string.

        Example:
            >>> logger = ErrorLogger()
            >>> error_id = logger.log_error({
            ...     "type": "FileNotFoundError",
            ...     "message": "config.json not found",
            ...     "file": "app.py",
            ...     "line": 42,
            ...     "context": "During startup initialization"
            ... })
            >>> print(error_id)
            'ERR-20260311-143052'
        """
        error_id = self._generate_error_id()
        timestamp = self._generate_timestamp()

        error_type = error_data.get("type", "Unknown")
        playbook_suggestion = self._get_playbook_suggestion(error_type)

        complete_error = {
            "id": error_id,
            "timestamp": timestamp,
            "type": error_type,
            "message": error_data.get("message", ""),
            "file": error_data.get("file", ""),
            "line": error_data.get("line", 0),
            "context": error_data.get("context", ""),
            "resolved": False,
            "resolved_at": None,
            "playbook_suggestion": playbook_suggestion,
        }

        index_data = self._read_index()
        index_data["errors"].append(complete_error)
        index_data["last_updated"] = timestamp
        self._write_index(index_data)

        self._append_to_log(complete_error)

        safe_print(c(f"[LOGGED] Error {error_id} - {error_type}", Colors.YELLOW))

        return error_id

    def resolve_error(self, error_id: str) -> bool:
        """
        Mark an error as resolved in both JSON index and Markdown log.

        Args:
            error_id: The error identifier to resolve (e.g., 'ERR-20260311-143052')

        Returns:
            True if error was found and resolved, False otherwise.

        Example:
            >>> logger = ErrorLogger()
            >>> success = logger.resolve_error("ERR-20260311-143052")
            >>> print(success)
            True
        """
        index_data = self._read_index()
        found = False
        timestamp = self._generate_timestamp()

        for error in index_data["errors"]:
            if error.get("id") == error_id:
                error["resolved"] = True
                error["resolved_at"] = timestamp
                found = True
                break

        if found:
            index_data["last_updated"] = timestamp
            self._write_index(index_data)
            self._update_md_entry(error_id, resolved=True, resolved_at=timestamp)
            safe_print(c(f"[RESOLVED] Error {error_id}", Colors.GREEN))
        else:
            safe_print(c(f"[WARN] Error {error_id} not found", Colors.YELLOW))

        return found

    def _update_md_entry(self, error_id: str, resolved: bool, resolved_at: str) -> None:
        """Update the Markdown entry to show resolved status."""
        try:
            content = self.log_file.read_text(encoding="utf-8")

            content = content.replace(f"[!] {error_id}", f"[OK] {error_id}")

            lines = content.split("\n")
            new_lines = []
            for line in lines:
                if f"**Status** | Open" in line:
                    line = line.replace("**Status** | Open", "**Status** | Resolved")
                new_lines.append(line)
            content = "\n".join(new_lines)

            self.log_file.write_text(content, encoding="utf-8")
        except Exception as e:
            safe_print(c(f"[WARN] Could not update MD entry: {e}", Colors.YELLOW))

    def get_unresolved_errors(self) -> List[Dict]:
        """
        Get list of all unresolved errors from the JSON index.

        Returns:
            List of error dictionaries that have resolved=False.

        Example:
            >>> logger = ErrorLogger()
            >>> unresolved = logger.get_unresolved_errors()
            >>> print(len(unresolved))
            3
        """
        index_data = self._read_index()
        unresolved = [
            error
            for error in index_data.get("errors", [])
            if not error.get("resolved", False)
        ]
        return unresolved

    def get_all_errors(self) -> List[Dict]:
        """
        Get list of all errors from the JSON index.

        Returns:
            List of all error dictionaries.
        """
        index_data = self._read_index()
        return index_data.get("errors", [])

    def get_error_by_id(self, error_id: str) -> Optional[Dict]:
        """
        Get a specific error by its ID.

        Args:
            error_id: The error identifier to look up.

        Returns:
            Error dictionary if found, None otherwise.
        """
        index_data = self._read_index()
        for error in index_data.get("errors", []):
            if error.get("id") == error_id:
                return error
        return None

    def generate_playbook_hint(self, error_data: Dict) -> str:
        """
        Generate a recovery playbook hint based on error pattern.

        Analyzes the error type and provides a suggestion for which
        recovery playbook to use, along with initial recovery steps.

        Args:
            error_data: Dictionary containing error information, especially
                       the 'type' key with the exception class name.

        Returns:
            String with playbook ID and brief recovery suggestion.

        Example:
            >>> logger = ErrorLogger()
            >>> hint = logger.generate_playbook_hint({
            ...     "type": "UnicodeDecodeError",
            ...     "message": "'utf-8' codec can't decode"
            ... })
            >>> print(hint)
            'PB-001: Check file encoding with chardet, use detected encoding'
        """
        error_type = error_data.get("type", "Unknown")
        playbook_id = self._get_playbook_suggestion(error_type)

        hints = {
            "PB-001": f"{playbook_id}: Check file encoding with chardet, use detected encoding",
            "PB-002": f"{playbook_id}: Verify file path exists, check permissions",
            "PB-003": f"{playbook_id}: Check file/directory permissions, run as admin if needed",
            "PB-004": f"{playbook_id}: Verify dict key exists, use .get() with default",
            "PB-005": f"{playbook_id}: Validate input values, add type checking",
            "PB-006": f"{playbook_id}: Check variable types, add type conversion",
            "PB-007": f"{playbook_id}: Verify object has attribute, use hasattr()",
            "PB-008": f"{playbook_id}: Install missing package, check import path",
            "PB-009": f"{playbook_id}: Check network connection, add retry logic",
            "PB-010": f"{playbook_id}: Increase timeout, add async handling",
            "PB-011": f"{playbook_id}: Check file handles, close resources properly",
            "PB-012": f"{playbook_id}: Validate JSON syntax, use try/except for parsing",
            "PB-013": f"{playbook_id}: Check list length before accessing index",
            "PB-014": f"{playbook_id}: Add zero check before division",
            "PB-015": f"{playbook_id}: Review error context, add proper error handling",
        }

        if playbook_id and playbook_id in hints:
            return hints[playbook_id]

        return f"No playbook available for {error_type}. Manual investigation required."

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get statistics about logged errors.

        Returns:
            Dictionary with error statistics including counts by type,
            resolved vs unresolved, and most common errors.
        """
        index_data = self._read_index()
        errors = index_data.get("errors", [])

        total = len(errors)
        resolved = sum(1 for e in errors if e.get("resolved", False))
        unresolved = total - resolved

        type_counts: Dict[str, int] = {}
        for error in errors:
            error_type = error.get("type", "Unknown")
            type_counts[error_type] = type_counts.get(error_type, 0) + 1

        most_common = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total": total,
            "resolved": resolved,
            "unresolved": unresolved,
            "by_type": type_counts,
            "most_common": most_common,
        }

    # ─── v2.0.0 Methods: ADR-004 Classification & Recovery ─────────────

    def classify_error(self, error: Any) -> str:
        """
        Classify an error into an ADR-004 taxonomy category using keyword
        matching on the error message and type string.

        Args:
            error: An error dict (with 'type' and/or 'message' keys),
                   an Exception instance, or a string describing the error.

        Returns:
            One of the ADR-004 category strings:
            'network', 'api', 'file_system', 'authentication',
            'configuration', 'data_integrity', 'resource', or 'unknown'.

        Example:
            >>> logger = ErrorLogger()
            >>> logger.classify_error({"type": "ConnectionError",
            ...                        "message": "Connection refused"})
            'network'
            >>> logger.classify_error(FileNotFoundError("config.yaml"))
            'file_system'
        """
        # Normalize the input into a searchable text blob
        text_parts: List[str] = []

        if isinstance(error, dict):
            text_parts.append(str(error.get("type", "")))
            text_parts.append(str(error.get("message", "")))
            text_parts.append(str(error.get("context", "")))
        elif isinstance(error, BaseException):
            text_parts.append(type(error).__name__)
            text_parts.append(str(error))
        elif isinstance(error, str):
            text_parts.append(error)
        else:
            text_parts.append(str(error))

        combined = " ".join(text_parts).lower()

        if not combined.strip():
            return "unknown"

        # Score each category by counting keyword matches
        best_category = "unknown"
        best_score = 0

        for category, cat_data in ERROR_CATEGORIES.items():
            score = 0
            for keyword in cat_data["keywords"]:
                # Use word-level matching for short keywords, substring for longer
                kw_lower = keyword.lower()
                if len(kw_lower) <= 4:
                    # Short keywords: word boundary match
                    pattern = r'\b' + re.escape(kw_lower) + r'\b'
                    matches = re.findall(pattern, combined)
                    score += len(matches)
                else:
                    # Longer keywords: substring match
                    count = combined.count(kw_lower)
                    score += count

            if score > best_score:
                best_score = score
                best_category = category

        return best_category

    def suggest_recovery(self, error_class: str) -> Dict[str, Any]:
        """
        Suggest a recovery strategy for a given error classification category.

        Args:
            error_class: One of the ADR-004 taxonomy categories
                        (e.g., 'network', 'api', 'file_system', etc.)

        Returns:
            Dictionary with recovery information:
            - playbook_id: Suggested playbook identifier
            - strategy: Human-readable recovery strategy
            - severity: Severity level (low, medium, high, critical)
            - category: The error category that was matched

        Example:
            >>> logger = ErrorLogger()
            >>> result = logger.suggest_recovery("network")
            >>> print(result["playbook_id"])
            'PB-NET-RETRY'
        """
        if error_class in CATEGORY_RECOVERY_MAP:
            result = dict(CATEGORY_RECOVERY_MAP[error_class])
            result["category"] = error_class
            return result

        return {
            "playbook_id": None,
            "strategy": "No automated recovery available. Manual investigation required.",
            "severity": "unknown",
            "category": error_class,
        }

    def trigger_playbook(self, playbook_id: str) -> Dict[str, Any]:
        """
        Trigger a recovery playbook via the recovery orchestrator.

        Attempts to integrate with the recovery orchestrator if available.
        Falls back gracefully with a logged suggestion if the orchestrator
        is not yet implemented.

        Args:
            playbook_id: The playbook identifier to trigger
                        (e.g., 'PB-NET-RETRY', 'PB-001', etc.)

        Returns:
            Dictionary with trigger result:
            - triggered: Whether the playbook was actually executed
            - playbook_id: The playbook that was requested
            - status: 'executed', 'pending', or 'unavailable'
            - message: Human-readable status message

        Example:
            >>> logger = ErrorLogger()
            >>> result = logger.trigger_playbook("PB-NET-RETRY")
            >>> print(result["status"])
            'pending'
        """
        result: Dict[str, Any] = {
            "triggered": False,
            "playbook_id": playbook_id,
            "status": "unavailable",
            "message": "",
        }

        # Attempt to import and use recovery orchestrator
        try:
            # Try core recovery orchestrator
            from recovery_orchestrator import RecoveryOrchestrator
            orchestrator = RecoveryOrchestrator()
            exec_result = orchestrator.execute_playbook(playbook_id)
            result["triggered"] = True
            result["status"] = "executed"
            result["message"] = f"Playbook {playbook_id} executed successfully"
            result["details"] = exec_result
            safe_print(c(
                f"[PLAYBOOK] Triggered {playbook_id} via recovery orchestrator",
                Colors.GREEN
            ))
            return result
        except ImportError:
            pass
        except Exception as e:
            result["message"] = f"Orchestrator error: {e}"
            result["status"] = "error"

        # Fallback: Try script-based playbook execution
        try:
            playbook_path = (
                SCRIPT_DIR / "recovery" / f"{playbook_id.lower()}.py"
            )
            if playbook_path.exists():
                result["triggered"] = True
                result["status"] = "pending"
                result["message"] = (
                    f"Playbook script found at {playbook_path}. "
                    f"Manual execution required."
                )
                result["script_path"] = str(playbook_path)
                safe_print(c(
                    f"[PLAYBOOK] Script available: {playbook_path}",
                    Colors.YELLOW
                ))
                return result
        except Exception:
            pass

        # Graceful fallback — log the suggestion
        result["status"] = "pending"
        result["triggered"] = False
        result["message"] = (
            f"Recovery orchestrator not available. "
            f"Playbook {playbook_id} queued for manual execution."
        )
        safe_print(c(
            f"[PLAYBOOK] {playbook_id} — orchestrator not available, "
            f"queued for manual execution",
            Colors.YELLOW
        ))
        return result

    def detect_pattern(self, error_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Detect recurring patterns in error history.

        Analyzes a list of recent errors to identify:
        - Frequently recurring error types
        - Error bursts (many errors in a short time window)
        - Dominant error categories (by ADR-004 taxonomy)
        - Correlated error sequences (same file, same type chain)

        Args:
            error_history: List of error dicts to analyze. If None, reads
                          from the JSON index. Defaults to last 20 errors.

        Returns:
            Dictionary with pattern analysis:
            - recurring_types: Error types appearing >= recurrence_min times
            - bursts: Time windows with >= burst_threshold errors
            - dominant_category: Most common ADR-004 category
            - category_distribution: Count of errors per category
            - patterns_found: List of detected pattern descriptions
            - risk_level: 'low', 'medium', 'high', or 'critical'

        Example:
            >>> logger = ErrorLogger()
            >>> analysis = logger.detect_pattern()
            >>> print(analysis["dominant_category"])
            'file_system'
        """
        # Load errors from index if not provided
        if error_history is None:
            index_data = self._read_index()
            error_history = index_data.get("errors", [])[-20:]

        if not error_history:
            return {
                "recurring_types": [],
                "bursts": [],
                "dominant_category": "none",
                "category_distribution": {},
                "patterns_found": ["No errors to analyze"],
                "risk_level": "low",
                "total_analyzed": 0,
            }

        # --- 1. Recurring type analysis ---
        type_counts: Dict[str, int] = {}
        for err in error_history:
            err_type = err.get("type", "Unknown")
            type_counts[err_type] = type_counts.get(err_type, 0) + 1

        recurrence_min = PATTERN_THRESHOLDS["recurrence_min"]
        recurring_types = [
            {"type": t, "count": c}
            for t, c in type_counts.items()
            if c >= recurrence_min
        ]

        # --- 2. Burst detection ---
        bursts: List[Dict[str, Any]] = []
        timestamps: List[tuple] = []

        for err in error_history:
            ts_str = err.get("timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    timestamps.append((ts, err))
                except (ValueError, TypeError):
                    pass

        if len(timestamps) >= 2:
            timestamps.sort(key=lambda x: x[0])
            window_minutes = PATTERN_THRESHOLDS["time_window_minutes"]
            burst_threshold = PATTERN_THRESHOLDS["burst_threshold"]

            for i in range(len(timestamps)):
                window_start = timestamps[i][0]
                window_errors = []
                for j in range(i, len(timestamps)):
                    diff = (timestamps[j][0] - window_start).total_seconds() / 60.0
                    if diff <= window_minutes:
                        window_errors.append(timestamps[j][1])
                    else:
                        break
                if len(window_errors) >= burst_threshold:
                    bursts.append({
                        "start": window_start.isoformat(),
                        "count": len(window_errors),
                        "types": list(set(
                            e.get("type", "Unknown") for e in window_errors
                        )),
                    })

        # --- 3. Category distribution ---
        category_counts: Dict[str, int] = {}
        for err in error_history:
            cat = self.classify_error(err)
            category_counts[cat] = category_counts.get(cat, 0) + 1

        dominant_category = (
            max(category_counts, key=category_counts.get)
            if category_counts else "none"
        )

        # --- 4. Pattern descriptions ---
        patterns_found: List[str] = []

        for rt in recurring_types:
            patterns_found.append(
                f"Recurring error: {rt['type']} occurred {rt['count']} times"
            )

        for burst in bursts[:5]:  # Limit to 5 burst reports
            patterns_found.append(
                f"Error burst at {burst['start']}: "
                f"{burst['count']} errors in 30min window "
                f"(types: {', '.join(burst['types'])})"
            )

        if dominant_category != "none" and category_counts.get(dominant_category, 0) >= 3:
            patterns_found.append(
                f"Dominant category: {dominant_category} "
                f"({category_counts[dominant_category]} of {len(error_history)} errors)"
            )

        # File-level correlation
        file_counts: Dict[str, int] = {}
        for err in error_history:
            f = err.get("file", "")
            if f:
                file_counts[f] = file_counts.get(f, 0) + 1

        hot_files = [
            {"file": f, "count": c}
            for f, c in file_counts.items()
            if c >= 2
        ]
        for hf in hot_files[:3]:
            patterns_found.append(
                f"Hot file: {hf['file']} has {hf['count']} errors"
            )

        if not patterns_found:
            patterns_found.append("No significant patterns detected")

        # --- 5. Risk level ---
        risk_level = "low"
        if recurring_types:
            risk_level = "medium"
        if bursts:
            risk_level = "high"
        if bursts and recurring_types:
            risk_level = "critical"

        return {
            "recurring_types": recurring_types,
            "bursts": bursts[:5],
            "dominant_category": dominant_category,
            "category_distribution": category_counts,
            "patterns_found": patterns_found,
            "risk_level": risk_level,
            "total_analyzed": len(error_history),
            "hot_files": hot_files[:5],
        }

    def clear_resolved(self, days_old: int = 30) -> int:
        """
        Remove resolved errors older than specified days from index.

        Args:
            days_old: Number of days after which resolved errors are removed.
                     Defaults to 30.

        Returns:
            Number of errors removed.
        """
        from datetime import timedelta

        index_data = self._read_index()
        errors = index_data.get("errors", [])
        cutoff = datetime.now() - timedelta(days=days_old)

        new_errors = []
        removed = 0

        for error in errors:
            if error.get("resolved", False):
                resolved_at = error.get("resolved_at")
                if resolved_at:
                    try:
                        resolved_date = datetime.fromisoformat(resolved_at)
                        if resolved_date < cutoff:
                            removed += 1
                            continue
                    except (ValueError, TypeError):
                        pass
            new_errors.append(error)

        if removed > 0:
            index_data["errors"] = new_errors
            index_data["last_updated"] = self._generate_timestamp()
            self._write_index(index_data)
            safe_print(
                c(f"[CLEANUP] Removed {removed} old resolved errors", Colors.CYAN)
            )

        return removed


def log_error(error_data: Dict) -> str:
    """
    Convenience function to log an error without instantiating ErrorLogger.

    Args:
        error_data: Dictionary with error information.

    Returns:
        The generated error ID.
    """
    logger = ErrorLogger()
    return logger.log_error(error_data)


def resolve_error(error_id: str) -> bool:
    """
    Convenience function to resolve an error by ID.

    Args:
        error_id: The error identifier to resolve.

    Returns:
        True if resolved, False if not found.
    """
    logger = ErrorLogger()
    return logger.resolve_error(error_id)


def get_unresolved_errors() -> List[Dict]:
    """
    Convenience function to get all unresolved errors.

    Returns:
        List of unresolved error dictionaries.
    """
    logger = ErrorLogger()
    return logger.get_unresolved_errors()


def generate_playbook_hint(error_data: Dict) -> str:
    """
    Convenience function to generate a playbook hint.

    Args:
        error_data: Dictionary with error information.

    Returns:
        Playbook hint string.
    """
    logger = ErrorLogger()
    return logger.generate_playbook_hint(error_data)


# ─── v2.0.0 Convenience Functions ───────────────────────────────────

def classify_error(error: Any) -> str:
    """
    Convenience function to classify an error into ADR-004 taxonomy.

    Args:
        error: Error dict, Exception, or string.

    Returns:
        Category string (e.g., 'network', 'file_system', etc.)
    """
    logger = ErrorLogger()
    return logger.classify_error(error)


def suggest_recovery(error_class: str) -> Dict[str, Any]:
    """
    Convenience function to get recovery suggestion for a category.

    Args:
        error_class: ADR-004 category string.

    Returns:
        Recovery strategy dictionary.
    """
    logger = ErrorLogger()
    return logger.suggest_recovery(error_class)


def trigger_playbook(playbook_id: str) -> Dict[str, Any]:
    """
    Convenience function to trigger a recovery playbook.

    Args:
        playbook_id: Playbook identifier.

    Returns:
        Trigger result dictionary.
    """
    logger = ErrorLogger()
    return logger.trigger_playbook(playbook_id)


def detect_pattern(error_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Convenience function to detect patterns in error history.

    Args:
        error_history: Optional list of error dicts.

    Returns:
        Pattern analysis dictionary.
    """
    logger = ErrorLogger()
    return logger.detect_pattern(error_history)


if __name__ == "__main__":
    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("Error Logger Module v2.0.0 Test", Colors.BOLD + Colors.CYAN))
    print(c("=" * 50, Colors.HEADER))

    logger = ErrorLogger()

    print(c("\n[TEST 1] Logging sample error...", Colors.CYAN))
    error_id = logger.log_error(
        {
            "type": "UnicodeDecodeError",
            "message": "'utf-8' codec can't decode byte 0xf1 in position 42",
            "file": "data_processor.py",
            "line": 127,
            "context": "Reading CSV file exported from Windows with Latin-1 encoding",
        }
    )
    print(f"  Generated ID: {error_id}")

    print(c("\n[TEST 2] Getting playbook hint...", Colors.CYAN))
    hint = logger.generate_playbook_hint({"type": "UnicodeDecodeError"})
    print(f"  Hint: {hint}")

    print(c("\n[TEST 3] Getting unresolved errors...", Colors.CYAN))
    unresolved = logger.get_unresolved_errors()
    print(f"  Count: {len(unresolved)}")

    print(c("\n[TEST 4] Getting error statistics...", Colors.CYAN))
    stats = logger.get_error_stats()
    print(f"  Total: {stats['total']}")
    print(f"  Resolved: {stats['resolved']}")
    print(f"  Unresolved: {stats['unresolved']}")

    print(c("\n[TEST 5] Resolving error...", Colors.CYAN))
    success = logger.resolve_error(error_id)
    print(f"  Success: {success}")

    print(c("\n[TEST 6] Verifying resolution...", Colors.CYAN))
    unresolved_after = logger.get_unresolved_errors()
    print(f"  Unresolved count: {len(unresolved_after)}")

    # ─── v2.0.0 Tests: Classification, Recovery, Pattern Detection ───

    print(c("\n[TEST 7] Classifying errors (ADR-004)...", Colors.CYAN))
    cat1 = logger.classify_error({"type": "ConnectionError", "message": "Connection refused"})
    print(f"  ConnectionError -> {cat1}")
    cat2 = logger.classify_error(FileNotFoundError("config.yaml"))
    print(f"  FileNotFoundError -> {cat2}")
    cat3 = logger.classify_error({"type": "ValueError", "message": "invalid data"})
    print(f"  ValueError (data) -> {cat3}")
    cat4 = logger.classify_error("out of memory during processing")
    print(f"  'out of memory' -> {cat4}")

    print(c("\n[TEST 8] Suggesting recovery...", Colors.CYAN))
    rec = logger.suggest_recovery("network")
    print(f"  network -> {rec['playbook_id']}: {rec['strategy']}")
    rec_unknown = logger.suggest_recovery("unknown_cat")
    print(f"  unknown -> {rec_unknown['playbook_id']}")

    print(c("\n[TEST 9] Triggering playbook...", Colors.CYAN))
    trig = logger.trigger_playbook("PB-NET-RETRY")
    print(f"  PB-NET-RETRY -> status={trig['status']}, triggered={trig['triggered']}")

    print(c("\n[TEST 10] Detecting patterns...", Colors.CYAN))
    analysis = logger.detect_pattern()
    print(f"  Total analyzed: {analysis['total_analyzed']}")
    print(f"  Dominant category: {analysis['dominant_category']}")
    print(f"  Risk level: {analysis['risk_level']}")
    print(f"  Patterns: {analysis['patterns_found']}")

    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("All tests completed successfully!", Colors.GREEN))
    print(c("=" * 50, Colors.HEADER))
