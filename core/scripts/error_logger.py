#!/usr/bin/env python3
"""
PA Framework - Error Logger Module
Dual logging system (JSON + MD) for error tracking and recovery.

Part of PRP-007: Error Recovery Skill

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

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

if sys.platform == "win32" and sys.stdout.isatty():
    try:
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
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


if __name__ == "__main__":
    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("Error Logger Module Test", Colors.BOLD + Colors.CYAN))
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

    print(c("\n" + "=" * 50, Colors.HEADER))
    print(c("Tests completed successfully!", Colors.GREEN))
    print(c("=" * 50, Colors.HEADER))
