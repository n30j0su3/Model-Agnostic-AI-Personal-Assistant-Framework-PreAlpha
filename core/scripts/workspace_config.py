#!/usr/bin/env python3
"""workspace_config.py — stdlib authority for semantic workspaces.

Responsibilities (single source of truth for install.py, detect_workspace.py,
session_start.py and any agent needing workspace routing):

- Safe name validation for workspace/project directory names that must work on
  Windows/Linux/macOS (reserved device names, trailing dot/space, separators).
  Trailing dot/space is REJECTED, never silently trimmed.
- Load/save the per-install selection from ``data/user/workspaces.json``
  (untracked, 0600, atomic) with a strict distinction between "missing" and
  "present but empty" configs. Corrupt files count as empty.
- Resolve which workspace applies: cwd inside a configured workspace wins,
  then an explicit semantic key; a legacy ``workspaces/content`` fallback is
  allowed ONLY when the user config file does not exist. Present/empty
  configs fail closed instead of silently routing to content.
- All path calculation honors an explicit ``repo_root`` argument (falling back
  to the module root only when omitted) so tests and embedders can operate on
  any install root. Project paths are containment-checked and fail closed on
  unsafe input instead of silently normalizing traversal.

Creator: FreakingJSON (instagram.com/freakingjson, freakingjson.com)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ensure_data_dirs import atomic_write_json, ensure_data_dirs  # noqa: E402
else:  # pragma: no cover
    from .ensure_data_dirs import atomic_write_json, ensure_data_dirs  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_DEFINITIONS_PATH = ROOT / "config" / "workspaces.json"
USER_CONFIG_PATH = ROOT / "data" / "user" / "workspaces.json"

WORKSPACES_DIRNAME = "workspaces"
PROJECTS_DIRNAME = "projects"
LEGACY_WORKSPACE_KEY = "content"
LEGACY_WORKSPACE_DIR = "content"

SEMANTIC_KEYS = frozenset(
    {"personal", "professional", "research", "content", "development", "homelab"}
)

# Common synonyms users (or older docs) may use for the semantic keys.
KEY_ALIASES = {
    "trabajo": "professional",
    "job": "professional",
    "work": "professional",
    "research": "research",
    "dev": "development",
    "develop": "development",
    "contenido": "content",
    "casa": "homelab",
    "lab": "homelab",
    "hogar": "homelab",
}

_MISSING = "missing"
_EMPTY = "empty"
_PRESENT = "present"

# Matches names that are not one clean "word": separators, control chars,
# path traversal, hidden names (leading dot), etc.
_UNSAFE_NAME_RE = re.compile(r"[\\/:*?\"<>|\x00-\x1f]")
_WINDOWS_RESERVED_RE = re.compile(
    r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\..*)?$", re.IGNORECASE
)

# Config schema version, bump only on a format change.
CONFIG_SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------


def safe_name(value: Any) -> Optional[str]:
    """Return ``value`` if it is a safe single directory name, else None.

    Safe means: valid on Windows, Linux and macOS; no path separators, no
    traversal, no Windows reserved device names, no hidden names, no control
    characters, 1..100 chars. A trailing literal dot or space (or any other
    trailing whitespace) is rejected, never trimmed away.
    """
    if not isinstance(value, str):
        return None
    if not value or len(value) > 100:
        return None
    # Trailing dot/space/whitespace must fail validation, not be stripped.
    if value[-1] in {".", " ", "\t", "\n", "\r", "\v", "\f"}:
        return None
    candidate = value.strip()  # leading whitespace only (trailing rejected above)
    if not candidate or len(candidate) > 100:
        return None
    if candidate in {".", ".."} or candidate.startswith("."):
        return None
    if _UNSAFE_NAME_RE.search(candidate):
        return None
    if _WINDOWS_RESERVED_RE.match(candidate):
        return None
    return candidate


# ---------------------------------------------------------------------------
# Canonical + user configuration
# ---------------------------------------------------------------------------


def load_canonical_definitions(path: Path | None = None) -> dict[str, dict[str, str]]:
    """Return canonical semantic workspace definitions from tracked config."""
    source = path if path is not None else CANONICAL_DEFINITIONS_PATH
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raw = {}
    definitions: dict[str, dict[str, str]] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            if key.startswith("_"):
                continue
            if key in SEMANTIC_KEYS and isinstance(value, dict):
                display = value.get("display")
                if isinstance(display, str) and safe_name(display):
                    definitions[key] = {"display": display}
                else:
                    definitions[key] = {"display": key.capitalize()}
            elif key in SEMANTIC_KEYS:
                definitions[key] = {"display": key.capitalize()}
    return definitions


def canonical_display(key: str) -> str:
    """Default display name for a semantic key (canonical config wins)."""
    definitions = load_canonical_definitions()
    entry = definitions.get(key)
    if entry and entry.get("display"):
        return str(entry["display"])
    return key.capitalize()


def normalize_key(value: Any) -> str:
    """Map free-form input to a semantic key when possible, else lowercased."""
    text = str(value or "").strip().lower()
    return KEY_ALIASES.get(text, text)


def is_semantic_key(key: str) -> bool:
    return normalize_key(key) in SEMANTIC_KEYS


def load_user_config(
    repo_root: Path | None = None,
) -> tuple[str, dict[str, dict[str, str]]]:
    """Load the per-install selection.

    Returns ``(status, entries)`` where status distinguishes:
    - "missing": no config file (legacy install, legacy fallback allowed);
    - "empty": file exists but holds no workspaces (corrupt or present-empty);
    - "present": at least one workspace entry.
    Entries are normalized: keys are semantic-normalized, values become
    ``{"dir": <name>, "display": <name>}`` with validated safe names.
    """
    root = Path(repo_root) if repo_root is not None else ROOT
    path = root / "data" / "user" / "workspaces.json"
    if not path.is_file():
        return (_MISSING, {})

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return (_EMPTY, {})

    workspaces = payload.get("workspaces") if isinstance(payload, dict) else None
    if not isinstance(workspaces, dict):
        return (_EMPTY, {})

    entries: dict[str, dict[str, str]] = {}
    for raw_key, raw_value in workspaces.items():
        key = normalize_key(raw_key)
        if not isinstance(raw_key, str) or not key:
            continue
        if isinstance(raw_value, dict):
            directory = raw_value.get("dir")
            display = raw_value.get("display", directory)
        elif isinstance(raw_value, str):
            directory = raw_value
            display = raw_value
        else:
            continue
        directory = safe_name(directory)
        if not directory:
            continue
        display = safe_name(display) or directory
        entries[key] = {"dir": directory, "display": display}
    if not entries:
        return (_EMPTY, {})
    return (_PRESENT, entries)


def config_status(repo_root: Path | None = None) -> str:
    return load_user_config(repo_root)[0]


def normalize_entries(raw: Any) -> dict[str, dict[str, str]]:
    """Validate/normalize {key: name-or-entry} input into canonical entries."""
    if not isinstance(raw, dict) or not raw:
        raise ValueError("workspaces selection must be a non-empty mapping")
    entries: dict[str, dict[str, str]] = {}
    for raw_key, raw_value in raw.items():
        key = normalize_key(raw_key)
        if not key or "/" in key or "\\" in key or not safe_name(key):
            raise ValueError(f"unsafe or invalid workspace key: {raw_key!r}")
        if isinstance(raw_value, dict):
            directory = safe_name(raw_value.get("dir") or "")
            if not directory:
                raise ValueError(f"unsafe directory name for {key!r}")
            display = safe_name(raw_value.get("display") or directory) or directory
        else:
            directory = safe_name(raw_value)
            display = directory
            if not directory:
                raise ValueError(f"unsafe directory name for {key!r}: {raw_value!r}")
        entries[key] = {"dir": directory, "display": display}
    return entries


def save_user_config(entries: Any, repo_root: Path | None = None) -> dict:
    """Atomically persist the normalized selection (0600 via ensure_data_dirs)."""
    root = Path(repo_root) if repo_root is not None else ROOT
    normalized = normalize_entries(entries)
    payload = {
        "schema": CONFIG_SCHEMA_VERSION,
        "workspaces": normalized,
    }
    paths = ensure_data_dirs(root)
    destination = paths["user"] / "workspaces.json"
    atomic_write_json(destination, payload)
    return normalized


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def workspace_dir_for(
    entries: dict[str, dict[str, str]],
    key: str,
    repo_root: Path | str | None = None,
) -> Path:
    """Root path of the configured workspace ``key`` under ``workspaces/``.

    Honors the passed ``repo_root``; only falls back to the module root when
    it is omitted.
    """
    root = Path(repo_root) if repo_root is not None else ROOT
    return root / WORKSPACES_DIRNAME / entries[key]["dir"]


def project_dir_for(
    entries: dict[str, dict[str, str]],
    key: str,
    repo_root: Path | str | None = None,
) -> Path:
    """Projects directory of a configured workspace."""
    return workspace_dir_for(entries, key, repo_root=repo_root) / PROJECTS_DIRNAME


def _cwd_inside_workspace(
    entries: dict[str, dict[str, str]],
    cwd: Path | None,
    repo_root: Path | str | None = None,
) -> Optional[str]:
    if cwd is None:
        return None
    try:
        resolved_cwd = Path(cwd).resolve()
    except OSError:
        return None
    for key, _entry in entries.items():
        root = workspace_dir_for(entries, key, repo_root=repo_root).resolve()
        if resolved_cwd == root or root in resolved_cwd.parents:
            return key
    return None


def resolve_workspace(
    entries: dict[str, dict[str, str]],
    cwd: Path | str | None = None,
    explicit_key: str | None = None,
    status: str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Resolve the active workspace following the contract precedence.

    Precedence:
    1. cwd inside a configured workspace root (source "cwd");
    2. explicit semantic key present in the config (source "explicit-key");
    3. legacy ``workspaces/content`` fallback ONLY when the user config file
       is missing (source "fallback"). Present/empty configs fail closed.

    The result is a receipt dict with ``ok``, and on success ``key``, ``dir``,
    ``name`` (display), ``source``; on failure ``reason`` plus context.
    """
    if status is None:
        # Caller passed entries only: infer status from the mapping itself so
        # resolution stays honest about "no configured workspaces".
        status = _PRESENT if entries else _EMPTY

    if status == _MISSING:
        return {
            "ok": True,
            "key": LEGACY_WORKSPACE_KEY,
            "dir": LEGACY_WORKSPACE_DIR,
            "name": canonical_display(LEGACY_WORKSPACE_KEY),
            "source": "fallback",
        }

    cwd_key = _cwd_inside_workspace(entries, Path(cwd) if cwd else None, repo_root)
    if cwd_key is not None:
        return {
            "ok": True,
            "key": cwd_key,
            "dir": entries[cwd_key]["dir"],
            "name": entries[cwd_key]["display"],
            "source": "cwd",
        }

    if explicit_key:
        key = normalize_key(explicit_key)
        if key in entries:
            return {
                "ok": True,
                "key": key,
                "dir": entries[key]["dir"],
                "name": entries[key]["display"],
                "source": "explicit-key",
            }
        return {
            "ok": False,
            "reason": "workspace-not-configured",
            "key": key,
            "hint": "Configured workspaces: "
            + ", ".join(sorted(entries[k]["dir"] for k in entries)),
        }

    return {
        "ok": False,
        "reason": "workspaces-not-selected",
        "selected": sorted(entries[k]["dir"] for k in entries),
    }


# ---------------------------------------------------------------------------
# Project paths (containment-checked, fail closed)
# ---------------------------------------------------------------------------


def project_path(
    entries: dict[str, dict[str, str]],
    key: str,
    workdir: Any,
    repo_root: Path | str | None = None,
) -> Path:
    """Path of a project under ``<workspace dir>/projects/<name>``.

    ``workdir`` must be a safe single directory name (see ``safe_name``);
    anything else — traversal, absolute paths, separators, reserved names —
    raises ``ValueError`` instead of being silently normalized. The result is
    containment-checked with resolve/is_relative_to.
    """
    if key not in entries:
        raise KeyError(f"workspace not configured: {key!r}")
    name = safe_name(workdir)
    if not name:
        raise ValueError(f"unsafe project name: {workdir!r}")
    root = Path(repo_root) if repo_root is not None else ROOT
    projects_root = root / WORKSPACES_DIRNAME / entries[key]["dir"] / PROJECTS_DIRNAME
    candidate = (projects_root / name).resolve()
    projects_resolved = projects_root.resolve()
    if not candidate.is_relative_to(projects_resolved):
        raise ValueError(f"project path escapes workspace projects dir: {candidate}")
    return candidate


# ---------------------------------------------------------------------------
# Master-context rendering helper
# ---------------------------------------------------------------------------


def master_active_workspaces_block(entries: dict[str, dict[str, str]]) -> str:
    """Render the Active Workspaces section body from configured entries."""
    lines = []
    for key in sorted(entries):
        entry = entries[key]
        path = f"workspaces/{entry['dir']}"
        lines.append(f"- [ ] {entry['display']} (`{path}`)")
    return "\n".join(lines)


def render_master_workspaces(
    master_text: str, entries: dict[str, dict[str, str]]
) -> str:
    """Replace the Active Workspaces section in a MASTER document robustly.

    Line-based (non-brittle): finds the ``## Active Workspaces`` heading and
    swaps the bullet block up to (not including) the next ``## `` heading,
    preserving the document's line endings and its original trailing shape.
    """
    marker = "## Active Workspaces"
    lines = master_text.splitlines(keepends=True)
    heading_index = -1
    for i, line in enumerate(lines):
        if line.rstrip("\r\n").strip() == marker:
            heading_index = i
            break
    if heading_index < 0:
        return master_text

    eol = "\r\n" if "\r\n" in master_text else "\n"
    replacement = master_active_workspaces_block(entries)
    if not replacement:
        replacement = "- (sin workspaces configurados)"

    block_start = heading_index + 1
    while block_start < len(lines) and not lines[block_start].strip("\r\n").strip():
        block_start += 1
    block_end = block_start
    while block_end < len(lines) and not lines[block_end].lstrip().startswith("## "):
        block_end += 1

    tail = "".join(lines[block_end:]).lstrip("\r\n")
    rebuilt = (
        "".join(lines[: heading_index + 1])
        + eol
        + replacement
        + eol
    )
    if tail:
        rebuilt += eol + tail
    return rebuilt


# ---------------------------------------------------------------------------
# Prompt snippet for agents
# ---------------------------------------------------------------------------


def agent_workspace_rules(entries: dict[str, dict[str, str]]) -> str:
    """Rules text for agent prompts, driven by configured entries."""
    listing = ", ".join(
        f"{entries[k]['display']} ({entries[k]['dir']})" for k in sorted(entries)
    )
    if listing:
        listing = "Configured: " + listing
    else:
        listing = "No workspaces configured yet."
    return f"""Workspaces y proyectos (rutas configuradas en `data/user/workspaces.json`):

1. **Enrutamiento semántico**: elige el workspace según el dominio de la tarea:
   - Informe laboral / trabajo → professional
   - Organización de vida personal → personal
   - Investigación → research
   - Producción de contenido → content
   - Software/desarrollo → development
   - Laboratorio casero / homelab → homelab
2. **Precedencia**: una ruta explícita del usuario o el cwd dentro de un workspace configurado ganan; si no, aplica el routing semántico. Si la configuración existe y el workspace pedido no está en ella, NO infieras otro workspace: pregunta al usuario (fail closed).
3. **Ubicación de proyectos**: `{WORKSPACES_DIRNAME}/<workspace>/projects/<proyecto>/` — nunca en la raíz de `{WORKSPACES_DIRNAME}/` ni del repo.
{listing}"""


if __name__ == "__main__":
    print(json.dumps({"config_status": config_status()}, indent=2))
