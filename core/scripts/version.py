#!/usr/bin/env python3
"""Canonical PA Framework version reader and renderer."""

from __future__ import annotations

import re
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_VERSION_RE = re.compile(
    r"\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?"
)


def normalize(value: str) -> str:
    """Return a validated version without a display prefix."""
    candidate = value.strip()
    if candidate.startswith("v"):
        candidate = candidate[1:]
    if not _VERSION_RE.fullmatch(candidate):
        raise ValueError(f"invalid PA Framework version: {value!r}")
    return candidate


def canonical(repo_root: str | Path | None = None) -> str:
    """Read VERSION from *repo_root* and return its canonical value."""
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    return normalize((root / "VERSION").read_text(encoding="utf-8"))


def render(value: str, surface: str = "plain") -> str:
    """Render a canonical value for a named public surface."""
    canonical_value = normalize(value)
    if surface == "plain":
        return canonical_value
    if surface == "badge":
        return f"v{canonical_value}"
    raise ValueError(f"unknown version surface: {surface!r}")
