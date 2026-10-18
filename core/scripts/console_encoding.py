"""Shared console encoding guard for scripts that print Unicode status glyphs.

Scheduled tasks and direct invocations on Windows can run under a legacy code
page (cp1252). Printing a glyph such as U+2713 there raises UnicodeEncodeError
and aborts the script. configure_utf8_console() switches the standard streams
to UTF-8 with replacement, in place, and never raises.
"""
from __future__ import annotations

import sys


def configure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
