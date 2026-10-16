#!/usr/bin/env python3
"""Create ignored user-data directories and write private JSON atomically."""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any


_REPO_ROOT = Path(__file__).resolve().parents[2]


def ensure_data_dirs(repo_root: str | Path | None = None) -> dict[str, Path]:
    """Create the local generated-data skeleton and return its named paths."""
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    paths = {
        "user": root / "data" / "user",
        "wizard": root / "data" / "wizard",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            path.chmod(0o700)
        except OSError:
            pass
    return paths


def atomic_write_json(path: str | Path, payload: dict[str, Any]) -> None:
    """Write a private JSON object using a same-directory atomic rename."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = destination.with_name(
        f".{destination.name}.{os.getpid()}.{secrets.token_hex(6)}.tmp"
    )
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        try:
            destination.chmod(0o600)
        except OSError:
            pass
    finally:
        if temporary.exists():
            temporary.unlink()
