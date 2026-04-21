"""
PA Framework - Error Trigger Detection
=======================================

Provides error classification using the ADR-004 taxonomy and
recovery trigger logic for the Self-Healing Engine.

ADR-004 Taxonomy Categories:
    network          - Connection, timeout, DNS errors
    api              - HTTP status, rate-limit, auth errors
    file_system      - File I/O, permissions, paths
    authentication   - Credential, token, session errors
    configuration    - Config, environment, YAML/JSON parse errors
    data_integrity   - Encoding, parsing, schema validation errors
    resource         - Memory, subprocess, system resource errors
"""

from typing import Optional
import logging

# ---------------------------------------------------------------------------# Logging setup for error classification
# ---------------------------------------------------------------------------
_logger = logging.getLogger("pa_framework.recovery.triggers")
_logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# ADR-004 Error Taxonomy Mapping
# ---------------------------------------------------------------------------

# Maps Python exception class names → ADR-004 taxonomy categories
TAXONOMY_MAP: dict[str, str] = {
    # -- network --
    "ConnectionError": "network",
    "ConnectionResetError": "network",
    "ConnectionAbortedError": "network",
    "ConnectionRefusedError": "network",
    "BrokenPipeError": "network",
    "TimeoutError": "network",
    "socket.timeout": "network",
    "urllib.error.URLError": "network",
    "http.client.HTTPException": "api",

    # -- api --
    "HTTPError": "api",
    "RateLimitError": "api",
    "APIError": "api",

    # -- file_system --
    "FileNotFoundError": "file_system",
    "PermissionError": "file_system",
    "IsADirectoryError": "file_system",
    "NotADirectoryError": "file_system",
    "FileExistsError": "file_system",
    "OSError": "file_system",
    "IOError": "file_system",

    # -- authentication --
    "AuthenticationError": "authentication",
    "PermissionDenied": "authentication",
    "UnauthorizedError": "authentication",
    "TokenExpiredError": "authentication",

    # -- configuration --
    "ConfigParserError": "configuration",
    "EnvironmentError": "configuration",

    # -- data_integrity --
    "UnicodeEncodeError": "data_integrity",
    "UnicodeDecodeError": "data_integrity",
    "JSONDecodeError": "data_integrity",
    "yaml.YAMLError": "data_integrity",
    "ValueError": "data_integrity",
    "TypeError": "data_integrity",
    "SerializationError": "data_integrity",

    # -- resource --
    "MemoryError": "resource",
    "SubprocessError": "resource",
    "TimeoutExpired": "resource",
    "RecursionError": "resource",
    "RuntimeError": "resource",
    "ImportError": "resource",
    "ModuleNotFoundError": "resource",
}

# Keyword patterns in error messages for fuzzy classification
KEYWORD_PATTERNS: dict[str, list[str]] = {
    "network": [
        "connection refused", "connection reset", "timed out", "timeout",
        "network is unreachable", "name resolution", "dns",
        "connection aborted", "broken pipe",
    ],
    "api": [
        "status 4", "status 5", "rate limit", "too many requests",
        "api key", "unauthorized", "forbidden",
    ],
    "file_system": [
        "no such file", "not found", "permission denied",
        "is a directory", "not a directory", "disk full",
        "read-only", "cannot access",
    ],
    "authentication": [
        "authentication", "unauthorized", "invalid token",
        "expired token", "invalid credentials", "login failed",
        "access denied",
    ],
    "configuration": [
        "config", "configuration", "environment variable",
        "missing required", "invalid setting", "yaml",
    ],
    "data_integrity": [
        "encode", "decode", "codec", "utf-8", "charmap",
        "json", "parse", "malformed", "schema", "invalid literal",
    ],
    "resource": [
        "memory", "subprocess", "cannot allocate",
        "too many open", "resource temporarily unavailable",
        "module not found", "no module named",
    ],
}

# Exception types that should *not* trigger recovery (too trivial / dev errors)
SKIP_RECOVERY_TYPES: set[str] = {
    "KeyboardInterrupt",
    "SystemExit",
    "GeneratorExit",
    "StopIteration",
    "StopAsyncIteration",
    "NotImplementedError",
    "AssertionError",
    "SyntaxError",
    "IndentationError",
    "TabError",
}


def detect_error_type(error: BaseException | dict | str) -> str:
    """Classify an error into an ADR-004 taxonomy category.

    Args:
        error: An exception instance, a dict with ``type``/``message`` keys,
               or a raw error message string.

    Returns:
        One of the 7 ADR-004 taxonomy categories, or ``"unknown"``.
    """
    # --- Normalize input to (exc_type_name, message) ---
    exc_type_name: Optional[str] = None
    message: str = ""

    if isinstance(error, BaseException):
        exc_type_name = type(error).__name__
        message = str(error)
    elif isinstance(error, dict):
        exc_type_name = error.get("type")
        message = error.get("message", "")
    elif isinstance(error, str):
        message = error

    # --- 1. Exact exception-class match ---
    if exc_type_name and exc_type_name in TAXONOMY_MAP:
        return TAXONOMY_MAP[exc_type_name]

    # --- 2. Keyword fuzzy match on message ---
    msg_lower = message.lower()
    for category, keywords in KEYWORD_PATTERNS.items():
        for kw in keywords:
            if kw in msg_lower:
                return category

    # --- 3. Unknown classification - log for debugging ---
    _logger.debug(
        "Unclassified error | type=%s | message=%s",
        exc_type_name or "none",
        message[:100] if message else "empty",
    )
    return "unknown"


def should_trigger_recovery(error: BaseException | dict | str) -> bool:
    """Decide whether automated recovery should be attempted.

    Returns ``False`` for:
    * skip-list exception types (KeyboardInterrupt, SyntaxError, …)
    * dict/string errors with no recoverable information

    Returns ``True`` for all other errors (best-effort recovery).
    """
    exc_type_name: Optional[str] = None
    message: str = ""

    if isinstance(error, BaseException):
        exc_type_name = type(error).__name__
        message = str(error)
    elif isinstance(error, dict):
        exc_type_name = error.get("type")
        message = error.get("message", "")
    elif isinstance(error, str):
        message = error

    # Never recover from programmer-control-flow or syntax errors
    if exc_type_name and exc_type_name in SKIP_RECOVERY_TYPES:
        return False

    # Empty / whitespace-only message → nothing to act on
    if not message.strip():
        return False

    return True
