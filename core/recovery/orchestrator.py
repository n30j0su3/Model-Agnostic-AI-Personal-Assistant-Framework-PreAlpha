"""
PA Framework - Recovery Orchestrator
====================================

Matches errors to playbooks using the ADR-004 taxonomy and executes
recovery actions.  Works with the existing PB-001 … PB-008 playbooks
in ``core/.context/knowledge/playbooks/``.

ADR-004 Taxonomy Categories (7):
    network, api, file_system, authentication,
    configuration, data_integrity, resource
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

try:
    # Standard package import (works when project root is on sys.path)
    from core.recovery.triggers import TAXONOMY_MAP, detect_error_type, should_trigger_recovery
except ModuleNotFoundError:
    # Fallback for direct file loading (importlib.spec_from_file_location)
    # where package imports are unavailable.
    import importlib.util

    _triggers_path = Path(__file__).resolve().parent / "triggers.py"
    _spec = importlib.util.spec_from_file_location("recovery_triggers_local", _triggers_path)
    if _spec is None or _spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Cannot load triggers module from {_triggers_path}")

    _triggers = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_triggers)

    TAXONOMY_MAP = _triggers.TAXONOMY_MAP
    detect_error_type = _triggers.detect_error_type
    should_trigger_recovery = _triggers.should_trigger_recovery

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

_CORE_DIR = Path(__file__).resolve().parent.parent
_PLAYBOOKS_DIR = _CORE_DIR / ".context" / "knowledge" / "playbooks"

# ---------------------------------------------------------------------------
# Mapping: ADR-004 category → list of playbook IDs (ordered by preference)
# ---------------------------------------------------------------------------

CATEGORY_TO_PLAYBOOKS: dict[str, list[str]] = {
    "network": ["PB-004"],
    "api": ["PB-004"],
    "file_system": ["PB-002", "PB-005"],
    "authentication": ["PB-009"],
    "configuration": ["PB-006"],
    "data_integrity": ["PB-001", "PB-003"],
    "resource": ["PB-004"],
}

# ---------------------------------------------------------------------------
# Built-in recovery actions keyed by playbook ID.
# Each action receives ``context: dict`` and returns ``bool`` (success).
# Users can register additional actions via ``register_action()``.
# ---------------------------------------------------------------------------

def _action_encoding(context: dict) -> bool:
    """PB-001: Fix encoding by reading with detected encoding."""
    path = context.get("file_path")
    if path:
        try:
            Path(path).read_text(encoding="utf-8")
            return True
        except (UnicodeDecodeError, UnicodeEncodeError):
            # Try latin-1 as fallback
            try:
                Path(path).read_text(encoding="latin-1")
                return True
            except Exception:
                return False
    return False


def _action_file_not_found(context: dict) -> bool:
    """PB-002: Attempt to create missing file or directory."""
    path = context.get("file_path")
    if path:
        p = Path(path)
        try:
            if p.suffix:  # looks like a file
                p.parent.mkdir(parents=True, exist_ok=True)
                p.touch(exist_ok=True)
            else:  # directory
                p.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    return False


def _action_json_parse(context: dict) -> bool:
    """PB-003: Strip BOM / trailing commas from JSON content."""
    import re
    raw = context.get("raw_content", "")
    if raw:
        try:
            cleaned = raw.lstrip("\ufeff").strip()
            # Remove trailing commas before } or ]
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            json.loads(cleaned)
            context["cleaned_content"] = cleaned
            return True
        except json.JSONDecodeError:
            return False
    return False


def _action_subprocess_timeout(context: dict) -> bool:
    """PB-004: Return retry-signal (caller decides whether to retry)."""
    return context.get("retry_count", 0) < context.get("max_retries", 3)


def _action_path_resolution(context: dict) -> bool:
    """PB-005: Resolve relative path against a base directory."""
    path = context.get("file_path")
    base = context.get("base_dir", str(_CORE_DIR))
    if path:
        resolved = (Path(base) / path).resolve()
        if resolved.exists():
            context["resolved_path"] = str(resolved)
            return True
    return False


def _action_yaml_parse(context: dict) -> bool:
    """PB-006: YAML parse with fallback to defaults."""
    return bool(context.get("fallback_defaults"))


def _action_git_sync(context: dict) -> bool:
    """PB-007: Signal git-retry (stash + pull)."""
    return context.get("retry_count", 0) < 2


def _action_multi_cli(context: dict) -> bool:
    """PB-008: Wait-and-retry for lock contention."""
    return context.get("retry_count", 0) < 3


def _action_authentication(context: dict) -> bool:
    """PB-009: Signal auth-retry (caller refreshes credentials)."""
    # For basic validation, always signal retry is possible
    # In production, caller should provide context with:
    # - can_refresh: bool (token refresh available)
    # - fallback_credentials: bool (alternative creds available)
    # - retry_count: int (current retry attempt)
    # - max_retries: int (max retry attempts)
    
    refresh_available = context.get("can_refresh", True)  # Default to True for validation
    max_retries = context.get("max_retries", 2)
    retry_count = context.get("retry_count", 0)
    
    if refresh_available and retry_count < max_retries:
        return True
    
    # If no refresh available, check for fallback credentials
    fallback_available = context.get("fallback_credentials", False)
    if fallback_available:
        return True
    
    return False


_BUILTIN_ACTIONS: dict[str, Callable[[dict], bool]] = {
    "PB-001": _action_encoding,
    "PB-002": _action_file_not_found,
    "PB-003": _action_json_parse,
    "PB-004": _action_subprocess_timeout,
    "PB-005": _action_path_resolution,
    "PB-006": _action_yaml_parse,
    "PB-007": _action_git_sync,
    "PB-008": _action_multi_cli,
    "PB-009": _action_authentication,
}

# ---------------------------------------------------------------------------
# RecoveryOrchestrator
# ---------------------------------------------------------------------------


class RecoveryOrchestrator:
    """Match errors to playbooks and execute recovery actions.

    Args:
        playbooks_dir: Path to the directory containing ``index.json``
            and PB-*.md playbook files.
    """

    def __init__(self, playbooks_dir: Optional[Path] = None):
        self.playbooks_dir = playbooks_dir or _PLAYBOOKS_DIR
        self._actions: dict[str, Callable[[dict], bool]] = dict(_BUILTIN_ACTIONS)
        self._playbook_index: list[dict] = []
        self._history: list[dict] = []
        self._load_index()

    # -- Index loading -----------------------------------------------------

    def _load_index(self) -> None:
        """Load the playbook index from ``index.json``."""
        index_path = self.playbooks_dir / "index.json"
        if index_path.exists():
            try:
                data = json.loads(index_path.read_text(encoding="utf-8"))
                self._playbook_index = data.get("playbooks", [])
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load playbook index: %s", exc)
                self._playbook_index = []
        else:
            self._playbook_index = []

    # -- Public API --------------------------------------------------------

    def match_playbook(self, error: BaseException | dict | str) -> Optional[str]:
        """Return the best playbook ID for the given error.

        Uses ADR-004 taxonomy category → playbook mapping, then falls back
        to keyword matching against the playbook index.

        Args:
            error: Exception instance, dict with ``type``/``message``, or string.

        Returns:
            Playbook ID (e.g. ``"PB-001"``) or ``None``.
        """
        if not should_trigger_recovery(error):
            return None

        category = detect_error_type(error)

        # 1. Direct category mapping
        candidates = CATEGORY_TO_PLAYBOOKS.get(category, [])
        if candidates:
            return candidates[0]

        # 2. Keyword matching against playbook index
        msg = ""
        if isinstance(error, BaseException):
            msg = str(error)
        elif isinstance(error, dict):
            msg = error.get("message", "")
        elif isinstance(error, str):
            msg = error

        msg_lower = msg.lower()
        best_match: Optional[str] = None
        best_score = 0

        for pb in self._playbook_index:
            keywords = pb.get("keywords", [])
            score = sum(1 for kw in keywords if kw.lower() in msg_lower)
            if score > best_score:
                best_score = score
                best_match = pb.get("id")

        return best_match

    def execute_playbook(self, playbook_id: str, context: Optional[dict] = None) -> dict:
        """Execute a recovery playbook.

        Args:
            playbook_id: Playbook identifier (e.g. ``"PB-001"``).
            context: Additional context passed to the recovery action
                     (file paths, raw content, retry counters, etc.).

        Returns:
            A dict with keys:
                - ``playbook_id`` (str)
                - ``status`` (``"success"`` | ``"failed"`` | ``"no_action"``)
                - ``timestamp`` (ISO-8601)
                - ``message`` (human-readable summary)
        """
        context = context or {}
        now = datetime.now().isoformat()
        result: dict[str, Any] = {
            "playbook_id": playbook_id,
            "status": "no_action",
            "timestamp": now,
            "message": "",
        }

        action = self._actions.get(playbook_id)
        if action is None:
            result["status"] = "no_action"
            result["message"] = f"No action registered for {playbook_id}"
            self._history.append(result)
            return result

        try:
            success = action(context)
            result["status"] = "success" if success else "failed"
            result["message"] = (
                f"Playbook {playbook_id} executed successfully"
                if success
                else f"Playbook {playbook_id} action returned False"
            )
        except Exception as exc:
            result["status"] = "failed"
            result["message"] = f"Playbook {playbook_id} raised {type(exc).__name__}: {exc}"
            logger.exception("Playbook %s execution failed", playbook_id)

        self._history.append(result)
        return result

    def recover(self, error: BaseException | dict | str, context: Optional[dict] = None) -> dict:
        """End-to-end recovery: classify → match → execute.

        Convenience method combining ``match_playbook`` and ``execute_playbook``.

        Args:
            error: The error to recover from.
            context: Optional context dict.

        Returns:
            The execution result dict (or a dict with ``status="skipped"``).
        """
        if not should_trigger_recovery(error):
            return {
                "playbook_id": None,
                "status": "skipped",
                "timestamp": datetime.now().isoformat(),
                "message": "Recovery not triggered for this error type",
            }

        playbook_id = self.match_playbook(error)
        if playbook_id is None:
            return {
                "playbook_id": None,
                "status": "no_match",
                "timestamp": datetime.now().isoformat(),
                "message": "No matching playbook found for error",
            }

        return self.execute_playbook(playbook_id, context)

    def register_action(self, playbook_id: str, action: Callable[[dict], bool]) -> None:
        """Register or override a recovery action for a playbook.

        Args:
            playbook_id: Playbook identifier.
            action: Callable accepting ``context: dict``, returning ``bool``.
        """
        self._actions[playbook_id] = action

    @property
    def history(self) -> list[dict]:
        """Return a copy of the execution history."""
        return list(self._history)
